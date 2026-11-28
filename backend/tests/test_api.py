# Python / backend/tests/test_api.py / Python 3.12 + pytest / LearnPlay API behavior
import pytest
from learnplay.app import create_app, db, User, Course, Section, Lesson, Enrollment, LessonCompletion, Assessment, AssessmentQuestion, NotificationOutbox, seed_demo_data


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


def test_catalog_displays_course_specific_demo_instructors(client):
    courses = client.get('/api/v1/courses').json['items']
    assert {row['instructor'] for row in courses} == {
        'Marina Azevedo', 'Elisa Moura', 'Bruno Almeida', 'Camila Nogueira',
    }
    for row in courses:
        detail = client.get(f"/api/v1/courses/{row['id']}").json
        assert detail['instructor'] == row['instructor']
        assert detail['instructor_is_demo'] is True

    with client.application.app_context():
        owner = User(name='Nome da professora', email='docente@example.test', password_hash='not-a-login', role='instructor')
        db.session.add(owner)
        db.session.flush()
        other = Course(title='Design de interfaces digitais', description='Turma de outro docente',
                       category='Design', instructor_id=owner.id, status='published')
        db.session.add(other)
        db.session.commit()
        other_id = other.id
    detail = client.get(f'/api/v1/courses/{other_id}').json
    assert detail['instructor'] == 'Nome da professora'
    assert detail['instructor_is_demo'] is False


def test_catalog_indexes_published_lessons_in_study_order(client):
    with client.application.app_context():
        course = Course.query.filter_by(title='Python do zero ao primeiro projeto').one()
        section = Section.query.filter_by(course_id=course.id).first()
        db.session.add(Lesson(section_id=section.id, title='Aula em preparação', position=5, status='draft'))
        db.session.commit()
        course_id = course.id
    summary = next(row for row in client.get('/api/v1/courses').json['items'] if row['id'] == course_id)
    assert summary['lesson_titles'] == [
        'Primeiros passos com Python', 'Variáveis e tipos de dados',
        'Decisões e repetições', 'Projeto: lista de tarefas',
    ]
    assert len(summary['lesson_titles']) == summary['lesson_count']


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


def test_dashboard_resume_uses_the_students_published_lesson(client):
    token = login(client, 'aluna@learnplay.local', 'Aluno12345!')
    headers = {'X-CSRF-Token': token}
    course = next(row for row in client.get('/api/v1/courses').json['items'] if 'Python' in row['title'])
    course_id = course['id']
    assert client.post(f'/api/v1/courses/{course_id}/enrollments', headers=headers).status_code == 201
    lessons = client.get(f'/api/v1/courses/{course_id}/lessons').json['items'][0]['lessons']

    def target():
        return client.get('/api/v1/me/enrollments').json['items'][0]['resume_lesson']

    assert target() == {'id': lessons[0]['id'], 'title': lessons[0]['title'], 'saved': False}
    client.put(f"/api/v1/lessons/{lessons[0]['id']}/completion", headers=headers)
    assert target()['id'] == lessons[1]['id']
    client.put(f'/api/v1/me/resume/{course_id}', json={'lesson_id': lessons[2]['id']}, headers=headers)
    assert target() == {'id': lessons[2]['id'], 'title': lessons[2]['title'], 'saved': True}

    other = client.application.test_client()
    registration = other.post('/api/v1/auth/register', headers={'X-CSRF-Token': csrf(other)},
                              json={'name': 'Outro aluno', 'email': 'outro@example.test', 'password': 'TesteAluno123!'})
    other.post(f'/api/v1/courses/{course_id}/enrollments', headers={'X-CSRF-Token': registration.json['csrf_token']})
    assert other.get('/api/v1/me/enrollments').json['items'][0]['resume_lesson']['id'] == lessons[0]['id']

    with client.application.app_context():
        db.session.get(Lesson, lessons[2]['id']).status = 'draft'
        db.session.commit()
    assert target()['id'] == lessons[1]['id']
    for lesson in [lessons[1], lessons[3]]:
        client.put(f"/api/v1/lessons/{lesson['id']}/completion", headers=headers)
    assert target()['id'] == lessons[0]['id']
    with client.application.app_context():
        for lesson in lessons:
            db.session.get(Lesson, lesson['id']).status = 'draft'
        db.session.commit()
    assert target() is None


@pytest.mark.parametrize('method', ['pix', 'credit', 'debit'])
def test_paid_enrollment_requires_demo_confirmation(client, method):
    token = login(client, 'aluna@learnplay.local', 'Aluno12345!')
    headers = {'X-CSRF-Token': token}
    course = next(x for x in client.get('/api/v1/courses').json['items'] if x['price'] > 0)
    response = client.post(f"/api/v1/courses/{course['id']}/enrollments", headers=headers)
    enrollment_id = response.json['id']
    path = f'/api/v1/me/enrollments/{enrollment_id}'
    assert response.status_code == 202
    assert response.json['status'] == 'pending_payment'
    assert client.get(f'{path}/receipt').status_code == 404
    assert client.get(f"/api/v1/courses/{course['id']}/lessons").status_code == 403
    assert client.post(f'{path}/demo-payment', headers=headers).status_code == 404
    assert client.post('/api/v1/integrations/payments/webhook', headers=headers).status_code == 404

    assert client.post(f'{path}/payment', json={'method': []}, headers=headers).status_code == 422
    first = client.post(f'{path}/payment', json={'method': 'pix'}, headers=headers).json
    assert client.get(first['qr_url']).data.startswith(b'\x89PNG\r\n\x1a\n')
    prepared = client.post(f'{path}/payment', json={'method': method, 'amount': 0}, headers=headers)
    assert prepared.json['method'] == method
    assert prepared.json['amount'] == course['price']
    assert 'reference' in prepared.json
    reference = prepared.json['reference']
    assert client.get(f'{path}/payment').json['reference'] == reference
    assert client.get(f"/api/v1/courses/{course['id']}/lessons").status_code == 403
    if method != 'pix':
        assert client.get(first['qr_url']).status_code == 404
        assert client.post(f'{path}/payment/approve', json={'reference': first['reference']},
                           headers=headers).status_code == 409
    assert client.post(f'{path}/payment/approve', json={'reference': reference}).status_code == 403
    approved = client.post(f'{path}/payment/approve', json={'reference': reference}, headers=headers)
    assert approved.json['enrollment_status'] == 'active'
    assert client.post(f'{path}/payment/approve', json={'reference': reference}, headers=headers).json == approved.json
    assert client.get(f"/api/v1/courses/{course['id']}/lessons").status_code == 200
    assert not approved.json['qr_url']
    receipt = client.get(approved.json['receipt_url'])
    assert receipt.mimetype == 'application/pdf'
    assert 'attachment;' in receipt.headers['Content-Disposition']
    assert receipt.data.startswith(b'%PDF-')
    assert client.get('/api/v1/me/enrollments').json['items'][0]['receipt_url'] == approved.json['receipt_url']
    with client.application.app_context():
        assert NotificationOutbox.query.filter_by(event_key=f'enrollment:{enrollment_id}').count() == 1


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
    assert first.json['incorrect_question_ids'] == [assessment['questions'][1]['id']]
    for _ in range(2):
        client.post(f"/api/v1/courses/{course['id']}/assessments/{assessment['id']}/attempts", json={'answers': answers}, headers={'X-CSRF-Token': token})
    blocked = client.post(f"/api/v1/courses/{course['id']}/assessments/{assessment['id']}/attempts", json={'answers': answers}, headers={'X-CSRF-Token': token})
    assert blocked.status_code == 409



def test_certificate_share_is_opt_in_and_can_be_revoked(client):
    token = login(client, 'aluna@learnplay.local', 'Aluno12345!')
    headers = {'X-CSRF-Token': token}
    course_id = next(row['id'] for row in client.get('/api/v1/courses').json['items'] if 'Python' in row['title'])
    detail = f'/api/v1/courses/{course_id}'
    share = f'/api/v1/me/certificates/{course_id}/share'
    guest = client.application.test_client()
    assert guest.put(share, headers={'X-CSRF-Token': csrf(guest)}).status_code == 401
    assert client.put(share, headers=headers).status_code == 404
    assert client.post(f'{detail}/enrollments', headers=headers).status_code == 201
    assert client.put(share, headers=headers).status_code == 409
    for section in client.get(f'{detail}/lessons').json['items']:
        for lesson in section['lessons']:
            assert client.put(f"/api/v1/lessons/{lesson['id']}/completion", headers=headers).status_code == 200
    assert client.get(detail).json['certificate_verification_url'] is None

    url = client.put(share, headers=headers).json['verification_url']
    assert client.put(share, headers=headers).json['verification_url'] == url
    assert client.get(detail).json['certificate_verification_url'] == url
    assert 'certificate_verification_url' not in guest.get(detail).json
    verification = guest.get(url)
    assert verification.status_code == 200
    assert verification.headers['Cache-Control'] == 'no-store'
    assert 'noindex' in verification.headers['X-Robots-Tag']
    page = verification.get_data(as_text=True)
    assert 'Ana Martins' in page and 'aluna@learnplay.local' not in page
    assert client.delete(share, headers=headers).status_code == 204
    assert guest.get(url).status_code == 404
    new = client.put(share, headers=headers).json['verification_url']
    assert new != url
    assert guest.get(new).status_code == 200

    with client.application.app_context():
        owner_id = User.query.filter_by(email='aluna@learnplay.local').first().id
    admin = login(client, 'admin@learnplay.local', 'Admin123456!')
    assert client.delete(f'/api/v1/admin/users/{owner_id}', headers={'X-CSRF-Token': admin}).status_code == 204
    assert guest.get(new).status_code == 404


def test_project_achievement_requires_completion_and_remains_private(client):
    token = login(client, 'aluna@learnplay.local', 'Aluno12345!')
    headers = {'X-CSRF-Token': token}
    course_id = next(row['id'] for row in client.get('/api/v1/courses').json['items'] if 'Python' in row['title'])
    detail = f'/api/v1/courses/{course_id}'
    path = f'/api/v1/me/projects/{course_id}'
    url = 'https://example.test/student/project'
    assert client.put(path, json={'url': url}, headers=headers).status_code == 403
    assert client.post(f'{detail}/enrollments', headers=headers).status_code == 201
    assert client.put(path, json={'url': url}, headers=headers).status_code == 409
    for section in client.get(f'{detail}/lessons').json['items']:
        for lesson in section['lessons']:
            assert client.put(f"/api/v1/lessons/{lesson['id']}/completion", headers=headers).status_code == 200

    assert client.put(path, json={'url': 'http://example.test'}, headers=headers).status_code == 422
    assert client.put(path, json={'url': url}, headers=headers).json['project_url'] == url
    updated = 'https://example.test/student/final'
    assert client.put(path, json={'url': updated}, headers=headers).json['project_url'] == updated
    assert client.get(detail).json['project_url'] == updated

    other = client.application.test_client()
    assert 'project_url' not in other.get(detail).json
    instructor = login(other, 'professor@learnplay.local', 'Professor123!')
    assert other.put(path, json={'url': url}, headers={'X-CSRF-Token': instructor}).status_code == 403


def test_demo_payment_and_receipt_belong_to_enrolled_student(client):
    token = login(client, 'aluna@learnplay.local', 'Aluno12345!')
    headers = {'X-CSRF-Token': token}
    course = next(x for x in client.get('/api/v1/courses').json['items'] if x['price'] > 0)
    pending = client.post(f"/api/v1/courses/{course['id']}/enrollments", headers=headers)
    path = f"/api/v1/me/enrollments/{pending.json['id']}"
    payment = client.post(f'{path}/payment', json={'method': 'pix'}, headers=headers).json

    other = client.application.test_client()
    registered = other.post('/api/v1/auth/register', headers={'X-CSRF-Token': csrf(other)},
                            json={'name': 'Outro aluno', 'email': 'outro@example.test', 'password': 'Teste12345!'})
    other_headers = {'X-CSRF-Token': registered.json['csrf_token']}
    assert other.get(f'{path}/payment').status_code == 404
    assert other.get(payment['qr_url']).status_code == 404
    assert other.post(f'{path}/payment/approve', json={'reference': payment['reference']},
                      headers=other_headers).status_code == 404

    client.post(f'{path}/payment/approve', json={'reference': payment['reference']}, headers=headers)
    assert other.get(f'{path}/receipt').status_code == 404


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
