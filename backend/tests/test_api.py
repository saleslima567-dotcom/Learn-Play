# Python / backend/tests/test_api.py / Python 3.12 + pytest / LearnPlay API behavior
import pytest
import hashlib
import hmac
import json
from learnplay.app import create_app, db, User, Course, Section, Lesson, Enrollment, LessonCompletion, Assessment, AssessmentQuestion, seed_demo_data


@pytest.fixture()
def client(tmp_path):
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': f'sqlite:///{tmp_path / "test.db"}', 'SESSION_COOKIE_SECURE': False})
    with app.app_context():
        db.create_all()
        seed_demo_data()
    yield app.test_client()
    with app.app_context():
        db.drop_all()


def csrf(client):
    return client.get('/api/v1/auth/csrf').json['csrf_token']


def login(client, email, password):
    token = csrf(client)
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password}, headers={'X-CSRF-Token': token})
    assert response.status_code == 200, response.json
    return response.json['csrf_token']


def test_catalog_public_and_contains_seed_courses(client):
    response = client.get('/api/v1/courses')
    assert response.status_code == 200
    assert len(response.json['items']) == 4
    assert response.json['items'][0]['lesson_count'] > 0


def test_csrf_blocks_mutation_without_token(client):
    response = client.post('/api/v1/auth/login', json={'email': 'x', 'password': 'y'})
    assert response.status_code == 403


def test_free_enrollment_and_lesson_progress_are_idempotent(client):
    token = login(client, 'aluna@learnplay.local', 'Aluno12345!')
    course = next(x for x in client.get('/api/v1/courses').json['items'] if x['price'] == 0)
    enrolled = client.post(f"/api/v1/courses/{course['id']}/enrollments", headers={'X-CSRF-Token': token})
    assert enrolled.status_code == 201
    lesson = client.get(f"/api/v1/courses/{course['id']}/lessons")
    assert lesson.status_code == 200
    lesson_id = lesson.json['items'][0]['lessons'][0]['id']
    first = client.put(f'/api/v1/lessons/{lesson_id}/completion', headers={'X-CSRF-Token': token})
    second = client.put(f'/api/v1/lessons/{lesson_id}/completion', headers={'X-CSRF-Token': token})
    expected = round(100 / course['lesson_count'])
    assert first.json['progress_percent'] == second.json['progress_percent'] == expected
    assert len(client.get(f"/api/v1/courses/{course['id']}").json['completed_lesson_ids']) == 1


def test_paid_enrollment_requires_demo_confirmation(client):
    token = login(client, 'aluna@learnplay.local', 'Aluno12345!')
    course = next(x for x in client.get('/api/v1/courses').json['items'] if x['price'] > 0)
    response = client.post(f"/api/v1/courses/{course['id']}/enrollments", headers={'X-CSRF-Token': token})
    assert response.status_code == 202
    assert response.json['status'] == 'pending_payment'
    lesson_response = client.get(f"/api/v1/courses/{course['id']}/lessons")
    assert lesson_response.status_code == 403
    approved = client.post(f"/api/v1/me/enrollments/{response.json['id']}/demo-payment", headers={'X-CSRF-Token': token})
    assert approved.json['status'] == 'active'
    assert client.get(f"/api/v1/courses/{course['id']}/lessons").status_code == 200


def test_instructor_can_create_course_and_student_cannot(client):
    token = login(client, 'professor@learnplay.local', 'Professor123!')
    response = client.post('/api/v1/instructor/courses', json={'title': 'Arquitetura de APIs', 'description': 'Curso de demonstração', 'price': 0}, headers={'X-CSRF-Token': token})
    assert response.status_code == 201
    student_token = login(client, 'aluna@learnplay.local', 'Aluno12345!')
    forbidden = client.post('/api/v1/instructor/courses', json={'title': 'Tentativa', 'description': 'Sem permissão'}, headers={'X-CSRF-Token': student_token})
    assert forbidden.status_code == 403


def test_assessment_attempts_are_limited_and_score_is_computed(client):
    token = login(client, 'aluna@learnplay.local', 'Aluno12345!')
    course = client.get('/api/v1/courses').json['items'][0]
    client.post(f"/api/v1/courses/{course['id']}/enrollments", headers={'X-CSRF-Token': token})
    detail = client.get(f"/api/v1/courses/{course['id']}").json
    assessment = detail['assessment']
    answers = {q['id']: 0 for q in assessment['questions']}
    first = client.post(f"/api/v1/courses/{course['id']}/assessments/{assessment['id']}/attempts", json={'answers': answers}, headers={'X-CSRF-Token': token})
    assert first.status_code == 200 and first.json['score'] == 50
    for _ in range(2):
        client.post(f"/api/v1/courses/{course['id']}/assessments/{assessment['id']}/attempts", json={'answers': answers}, headers={'X-CSRF-Token': token})
    blocked = client.post(f"/api/v1/courses/{course['id']}/assessments/{assessment['id']}/attempts", json={'answers': answers}, headers={'X-CSRF-Token': token})
    assert blocked.status_code == 409



def test_payment_webhook_signature_and_duplicate_event_are_idempotent(client, monkeypatch):
    monkeypatch.setenv('PAYMENT_WEBHOOK_SECRET', 'test-webhook-secret')
    token = login(client, 'aluna@learnplay.local', 'Aluno12345!')
    course = next(x for x in client.get('/api/v1/courses').json['items'] if x['price'] > 0)
    pending = client.post(f"/api/v1/courses/{course['id']}/enrollments", headers={'X-CSRF-Token': token})
    payload = {'event_id': 'evt-test-001', 'enrollment_id': pending.json['id'], 'status': 'approved', 'amount': course['price'], 'currency': 'BRL'}
    body = json.dumps(payload, separators=(',', ':')).encode()
    signature = hmac.new(b'test-webhook-secret', body, hashlib.sha256).hexdigest()
    path = '/api/v1/integrations/payments/webhook'
    first = client.post(path, data=body, content_type='application/json', headers={'X-Webhook-Signature': signature})
    duplicate = client.post(path, data=body, content_type='application/json', headers={'X-Webhook-Signature': signature})
    assert first.status_code == 200 and first.json['status'] == 'active'
    assert duplicate.status_code == 200 and duplicate.json['duplicate'] is True



def test_instructor_can_author_lessons_assessment_and_publish(client):
    token = login(client, 'professor@learnplay.local', 'Professor123!')
    created = client.post('/api/v1/instructor/courses', json={'title': 'Arquitetura de Software', 'description': 'Do requisito à implantação', 'price': 0}, headers={'X-CSRF-Token': token})
    course = created.json['course']
    lesson = client.post(f"/api/v1/instructor/courses/{course['id']}/lessons", json={'title': 'Requisitos e cenários', 'description': 'Identifique as necessidades', 'status': 'published'}, headers={'X-CSRF-Token': token})
    assert lesson.status_code == 201
    quiz = client.put(f"/api/v1/instructor/courses/{course['id']}/assessment", json={'title': 'Revisão', 'max_attempts': 3, 'questions': [{'prompt': 'Qual artefato guia o projeto?', 'options': ['Requisitos', 'Sorteio'], 'correct_option': 0}]}, headers={'X-CSRF-Token': token})
    assert quiz.status_code == 200
    published = client.patch(f"/api/v1/instructor/courses/{course['id']}", json={'status': 'published'}, headers={'X-CSRF-Token': token})
    assert published.status_code == 200
    assert client.get(f"/api/v1/courses/{course['id']}").json['lesson_count'] == 1
