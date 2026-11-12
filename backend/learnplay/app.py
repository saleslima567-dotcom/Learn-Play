# Python / backend/learnplay/app.py / Python 3.12 + Flask / LearnPlay REST API
from __future__ import annotations

import hashlib
from html import escape as html_escape
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import wraps

from flask import Flask, g, jsonify, make_response, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, func
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


def now_utc():
    return datetime.now(timezone.utc)


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)

    def public(self):
        return {'id': self.id, 'name': self.name, 'email': self.email, 'role': self.role, 'status': self.status}


class ServerSession(db.Model):
    id = db.Column(db.String(64), primary_key=True)  # SHA-256 digest; raw cookie is never stored.
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)
    csrf_hash = db.Column(db.String(64), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)


class Course(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    instructor_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(60), nullable=False, default='Geral')
    level = db.Column(db.String(30), nullable=False, default='Iniciante')
    price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    status = db.Column(db.String(20), nullable=False, default='published')
    cover_color = db.Column(db.String(20), nullable=False, default='violet')
    instructor = db.relationship('User', foreign_keys=[instructor_id])

    def public(self, details=False):
        lessons = Lesson.query.join(Section).filter(Section.course_id == self.id, Lesson.status == 'published').order_by(Section.position, Lesson.position).all()
        data = {'id': self.id, 'title': self.title, 'description': self.description, 'category': self.category,
                'level': self.level, 'price': float(self.price), 'status': self.status,
                'cover_color': self.cover_color, 'instructor': self.instructor.name,
                'lesson_count': len(lessons), 'duration_minutes': sum(x.duration_seconds for x in lessons) // 60}
        if details:
            data['lessons'] = [x.public() for x in lessons]
            data['assessment'] = Assessment.query.filter_by(course_id=self.id).first().public() if Assessment.query.filter_by(course_id=self.id).first() else None
        return data


class Section(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = db.Column(db.String(36), db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(140), nullable=False)
    position = db.Column(db.Integer, nullable=False)


class Lesson(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    section_id = db.Column(db.String(36), db.ForeignKey('section.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    duration_seconds = db.Column(db.Integer, nullable=False, default=600)
    position = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='published')
    media_key = db.Column(db.String(255), nullable=True)

    def public(self):
        return {'id': self.id, 'title': self.title, 'description': self.description, 'duration_seconds': self.duration_seconds, 'position': self.position}


class Enrollment(db.Model):
    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='uq_enrollment_student_course'),)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.String(36), db.ForeignKey('course.id'), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    activated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    course = db.relationship('Course')

    def public(self):
        return {'id': self.id, 'course_id': self.course_id, 'course': self.course.public(), 'status': self.status,
                'created_at': self.created_at.isoformat(), 'progress_percent': progress_for(self.student_id, self.course_id)}


class Favorite(db.Model):
    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='uq_favorite_student_course'),)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False, index=True)
    course_id = db.Column(db.String(36), db.ForeignKey('course.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    course = db.relationship('Course')


class CourseResume(db.Model):
    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='uq_resume_student_course'),)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False, index=True)
    course_id = db.Column(db.String(36), db.ForeignKey('course.id'), nullable=False, index=True)
    lesson_id = db.Column(db.String(36), db.ForeignKey('lesson.id'), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)


class LessonCompletion(db.Model):
    __table_args__ = (UniqueConstraint('student_id', 'lesson_id', name='uq_completion_student_lesson'),)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.String(36), db.ForeignKey('lesson.id'), nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)


class Assessment(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = db.Column(db.String(36), db.ForeignKey('course.id'), nullable=False, unique=True)
    title = db.Column(db.String(140), nullable=False)
    passing_score = db.Column(db.Integer, nullable=False, default=70)
    max_attempts = db.Column(db.Integer, nullable=False, default=3)

    def public(self):
        qs = AssessmentQuestion.query.filter_by(assessment_id=self.id).order_by(AssessmentQuestion.position).all()
        return {'id': self.id, 'title': self.title, 'passing_score': self.passing_score, 'max_attempts': self.max_attempts,
                'questions': [{'id': q.id, 'prompt': q.prompt, 'options': q.options} for q in qs]}


class AssessmentQuestion(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = db.Column(db.String(36), db.ForeignKey('assessment.id', ondelete='CASCADE'), nullable=False)
    prompt = db.Column(db.String(400), nullable=False)
    options = db.Column(db.JSON, nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)
    position = db.Column(db.Integer, nullable=False)


class AssessmentAttempt(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = db.Column(db.String(36), db.ForeignKey('assessment.id'), nullable=False)
    student_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    attempt_number = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)


class PaymentEvent(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_event_id = db.Column(db.String(160), nullable=False, unique=True)
    enrollment_id = db.Column(db.String(36), db.ForeignKey('enrollment.id'), nullable=False)
    payload_digest = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='received')
    received_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)

class NotificationOutbox(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_key = db.Column(db.String(180), unique=True, nullable=False)
    recipient_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    event_type = db.Column(db.String(60), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    attempts = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)


def progress_for(student_id, course_id):
    total = db.session.query(func.count(Lesson.id)).join(Section).filter(Section.course_id == course_id, Lesson.status == 'published').scalar() or 0
    if not total:
        return 0
    done = db.session.query(func.count(LessonCompletion.id)).join(Lesson).join(Section).filter(
        LessonCompletion.student_id == student_id, Section.course_id == course_id, Lesson.status == 'published').scalar() or 0
    return round(done * 100 / total)


def create_app(test_config=None):
    app = Flask(__name__, static_folder='static/assets', static_url_path='/assets')
    database_url = os.getenv('DATABASE_URL', 'sqlite:///learnplay.db')
    if database_url.startswith('postgres://'):
        database_url = 'postgresql+psycopg://' + database_url[len('postgres://'):]
    elif database_url.startswith('postgresql://'):
        database_url = 'postgresql+psycopg://' + database_url[len('postgresql://'):]
    app.config.update(
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_NAME='learnplay_session',
        SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE', 'false').lower() == 'true',
        SESSION_TTL_HOURS=12,
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    @app.before_request
    def load_session():
        raw = request.cookies.get(app.config['SESSION_COOKIE_NAME'])
        record = db.session.get(ServerSession, token_hash(raw)) if raw else None
        if record and record.revoked_at is None and (record.expires_at.replace(tzinfo=timezone.utc) if record.expires_at.tzinfo is None else record.expires_at) > now_utc():
            g.server_session = record
            g.user = db.session.get(User, record.user_id) if record.user_id else None
        else:
            g.server_session = None
            g.user = None
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and request.path != '/api/v1/integrations/payments/webhook':
            if not g.server_session or not secrets.compare_digest(token_hash(request.headers.get('X-CSRF-Token', '')), g.server_session.csrf_hash):
                return problem(403, 'Token CSRF ausente ou inválido')

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Cache-Control'] = 'no-store' if request.path.startswith('/api/v1/auth') else 'no-cache'
        return response

    @app.get('/')
    def frontend_index():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'index.html')

    def require_user(*roles):
        def decorator(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                if not g.user or g.user.status != 'active':
                    return problem(401, 'Autenticação necessária')
                if roles and g.user.role not in roles:
                    return problem(403, 'Perfil sem permissão para esta operação')
                return fn(*args, **kwargs)
            return wrapped
        return decorator

    def establish_session(user_id=None):
        if g.server_session:
            g.server_session.revoked_at = now_utc()
        raw, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        record = ServerSession(id=token_hash(raw), user_id=user_id, csrf_hash=token_hash(csrf), expires_at=now_utc() + timedelta(hours=app.config['SESSION_TTL_HOURS']))
        db.session.add(record)
        return raw, csrf

    def session_cookie(response, raw, max_age=43200):
        response.set_cookie(app.config['SESSION_COOKIE_NAME'], raw, httponly=True, secure=app.config['SESSION_COOKIE_SECURE'],
                            samesite='Lax', max_age=max_age, path='/')
        return response

    @app.get('/api/v1/health/live')
    def live():
        return jsonify(status='ok')

    @app.get('/api/v1/health/ready')
    def ready():
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify(status='ready', database='ok')
        except Exception:
            return problem(503, 'Banco de dados indisponível')

    @app.get('/api/v1/auth/csrf')
    def csrf():
        if g.server_session:
            raw = request.cookies.get(app.config['SESSION_COOKIE_NAME'])
            csrf_value = getattr(g, '_csrf_value', None)
            if not csrf_value:
                csrf_value = secrets.token_urlsafe(32)
                g.server_session.csrf_hash = token_hash(csrf_value)
                db.session.commit()
        else:
            raw, csrf_value = establish_session()
            db.session.commit()
            response = jsonify(csrf_token=csrf_value)
            return session_cookie(response, raw)
        return jsonify(csrf_token=csrf_value)

    @app.post('/api/v1/auth/register')
    def register():
        data = request.get_json(silent=True) or {}
        name, email, password = str(data.get('name', '')).strip(), str(data.get('email', '')).strip().lower(), str(data.get('password', ''))
        if len(name) < 2 or len(name) > 100 or '@' not in email or len(password) < 10 or len(password) > 128:
            return problem(422, 'Informe nome, e-mail válido e senha entre 10 e 128 caracteres')
        if User.query.filter_by(email=email).first():
            return problem(409, 'Este e-mail já está cadastrado')
        user = User(name=name, email=email, password_hash=generate_password_hash(password, method='scrypt'))
        db.session.add(user)
        db.session.flush()
        raw, csrf_value = establish_session(user.id)
        db.session.commit()
        response = jsonify(user=user.public(), csrf_token=csrf_value)
        response.status_code = 201
        return session_cookie(response, raw)

    @app.post('/api/v1/auth/login')
    def login():
        data = request.get_json(silent=True) or {}
        user = User.query.filter_by(email=str(data.get('email', '')).strip().lower()).first()
        if not user or not check_password_hash(user.password_hash, str(data.get('password', ''))) or user.status != 'active':
            return problem(401, 'E-mail ou senha inválidos')
        raw, csrf_value = establish_session(user.id)
        db.session.commit()
        response = jsonify(user=user.public(), csrf_token=csrf_value)
        return session_cookie(response, raw)

    @app.post('/api/v1/auth/logout')
    @require_user()
    def logout():
        g.server_session.revoked_at = now_utc()
        db.session.commit()
        response = make_response('', 204)
        response.delete_cookie(app.config['SESSION_COOKIE_NAME'], path='/')
        return response

    @app.get('/api/v1/me')
    @require_user()
    def me():
        return jsonify(user=g.user.public())

    @app.get('/api/v1/courses')
    def list_courses():
        query = Course.query.filter_by(status='published')
        search = request.args.get('search', '').strip()
        if search:
            query = query.filter(Course.title.ilike(f'%{search[:100]}%'))
        items = query.order_by(Course.title).limit(min(max(request.args.get('limit', 20, type=int), 1), 100)).all()
        return jsonify(items=[c.public() for c in items], next_cursor=None)

    @app.get('/api/v1/courses/<course_id>')
    def course_detail(course_id):
        course = db.session.get(Course, course_id)
        if not course or course.status != 'published':
            return problem(404, 'Curso não encontrado')
        data = course.public(details=True)
        if g.user:
            enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=course.id).first()
            data['enrollment_status'] = enrollment.status if enrollment else None
            data['completed_lesson_ids'] = [x.lesson_id for x in LessonCompletion.query.join(Lesson).join(Section).filter(LessonCompletion.student_id == g.user.id, Section.course_id == course.id).all()]
        return jsonify(data)

    @app.post('/api/v1/courses/<course_id>/enrollments')
    @require_user('student')
    def enroll(course_id):
        course = db.session.get(Course, course_id)
        if not course or course.status != 'published':
            return problem(404, 'Curso não encontrado')
        existing = Enrollment.query.filter_by(student_id=g.user.id, course_id=course.id).first()
        if existing:
            return jsonify(existing.public()), 200
        status = 'active' if course.price == 0 else 'pending_payment'
        enrollment = Enrollment(student_id=g.user.id, course_id=course.id, status=status, activated_at=now_utc() if status == 'active' else None)
        db.session.add(enrollment)
        db.session.flush()
        if status == 'active':
            db.session.add(NotificationOutbox(event_key=f'enrollment:{enrollment.id}', recipient_id=g.user.id, event_type='enrollment_confirmed', payload={'course_id': course.id}))
        db.session.commit()
        return jsonify(enrollment.public()), (201 if status == 'active' else 202)

    @app.post('/api/v1/me/enrollments/<enrollment_id>/demo-payment')
    @require_user('student')
    def demo_payment(enrollment_id):
        enrollment = db.session.get(Enrollment, enrollment_id)
        if not enrollment or enrollment.student_id != g.user.id:
            return problem(404, 'Matrícula não encontrada')
        if enrollment.status == 'pending_payment':
            enrollment.status, enrollment.activated_at = 'active', now_utc()
            db.session.add(NotificationOutbox(event_key=f'enrollment:{enrollment.id}', recipient_id=g.user.id, event_type='enrollment_confirmed', payload={'course_id': enrollment.course_id, 'demo': True}))
            db.session.commit()
        return jsonify(enrollment.public())

    @app.get('/api/v1/me/enrollments')
    @require_user()
    def my_enrollments():
        items = Enrollment.query.filter_by(student_id=g.user.id).order_by(Enrollment.created_at.desc()).all()
        return jsonify(items=[e.public() for e in items])

    @app.get('/api/v1/me/favorites')
    @require_user('student')
    def my_favorites():
        favorites = Favorite.query.join(Course).filter(
            Favorite.student_id == g.user.id, Course.status == 'published').order_by(Favorite.created_at.desc()).all()
        return jsonify(items=[favorite.course.public() for favorite in favorites])

    @app.post('/api/v1/me/favorites/<course_id>')
    @require_user('student')
    def add_favorite(course_id):
        course = db.session.get(Course, course_id)
        if not course or course.status != 'published':
            return problem(404, 'Curso não encontrado')
        favorite = Favorite.query.filter_by(student_id=g.user.id, course_id=course.id).first()
        if not favorite:
            db.session.add(Favorite(student_id=g.user.id, course_id=course.id))
            db.session.commit()
        return jsonify(course=course.public()), 201

    @app.delete('/api/v1/me/favorites/<course_id>')
    @require_user('student')
    def remove_favorite(course_id):
        favorite = Favorite.query.filter_by(student_id=g.user.id, course_id=course_id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
        return '', 204

    @app.get('/api/v1/me/resume/<course_id>')
    @require_user('student')
    def get_course_resume(course_id):
        enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=course_id, status='active').first()
        if not enrollment:
            return problem(403, 'Matrícula ativa necessária')
        resume = CourseResume.query.filter_by(student_id=g.user.id, course_id=course_id).first()
        return jsonify(course_id=course_id, lesson_id=resume.lesson_id if resume else None,
                       updated_at=resume.updated_at.isoformat() if resume else None)

    @app.put('/api/v1/me/resume/<course_id>')
    @require_user('student')
    def save_course_resume(course_id):
        enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=course_id, status='active').first()
        if not enrollment:
            return problem(403, 'Matrícula ativa necessária')
        lesson_id = str((request.get_json(silent=True) or {}).get('lesson_id', ''))
        lesson = db.session.query(Lesson).join(Section).filter(
            Lesson.id == lesson_id, Section.course_id == course_id, Lesson.status == 'published').first()
        if not lesson:
            return problem(404, 'Aula publicada não encontrada neste curso')
        resume = CourseResume.query.filter_by(student_id=g.user.id, course_id=course_id).first()
        if resume:
            resume.lesson_id = lesson.id
            resume.updated_at = now_utc()
        else:
            resume = CourseResume(student_id=g.user.id, course_id=course_id, lesson_id=lesson.id)
            db.session.add(resume)
        db.session.commit()
        return jsonify(course_id=course_id, lesson_id=resume.lesson_id, updated_at=resume.updated_at.isoformat())

    @app.get('/api/v1/courses/<course_id>/lessons')
    @require_user('student')
    def course_lessons(course_id):
        enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=course_id, status='active').first()
        if not enrollment:
            return problem(403, 'Matrícula ativa necessária')
        course = db.session.get(Course, course_id)
        if not course:
            return problem(404, 'Curso não encontrado')
        rows = db.session.query(Section, Lesson).join(Lesson, Lesson.section_id == Section.id).filter(Section.course_id == course_id, Lesson.status == 'published').order_by(Section.position, Lesson.position).all()
        completed = {x.lesson_id for x in LessonCompletion.query.join(Lesson).join(Section).filter(LessonCompletion.student_id == g.user.id, Section.course_id == course_id).all()}
        sections = {}
        for section, lesson in rows:
            sections.setdefault(section.id, {'id': section.id, 'title': section.title, 'lessons': []})['lessons'].append({**lesson.public(), 'completed': lesson.id in completed})
        return jsonify(items=list(sections.values()), progress_percent=progress_for(g.user.id, course_id))

    @app.put('/api/v1/lessons/<lesson_id>/completion')
    @require_user('student')
    def complete_lesson(lesson_id):
        lesson = db.session.get(Lesson, lesson_id)
        section = db.session.get(Section, lesson.section_id) if lesson else None
        if not lesson or not section or lesson.status != 'published':
            return problem(404, 'Aula não encontrada')
        enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=section.course_id, status='active').first()
        if not enrollment:
            return problem(403, 'Matrícula ativa necessária')
        completion = LessonCompletion.query.filter_by(student_id=g.user.id, lesson_id=lesson.id).first()
        if not completion:
            completion = LessonCompletion(student_id=g.user.id, lesson_id=lesson.id)
            db.session.add(completion)
            db.session.flush()
            pct = progress_for(g.user.id, section.course_id)
            if pct == 100:
                db.session.add(NotificationOutbox(event_key=f'course-complete:{g.user.id}:{section.course_id}', recipient_id=g.user.id, event_type='course_completed', payload={'course_id': section.course_id}))
            db.session.commit()
        return jsonify(lesson_id=lesson.id, completed_at=completion.completed_at.isoformat(), progress_percent=progress_for(g.user.id, section.course_id))

    @app.get('/api/v1/me/progress/<course_id>')
    @require_user('student')
    def my_progress(course_id):
        return jsonify(course_id=course_id, progress_percent=progress_for(g.user.id, course_id))

    @app.get('/api/v1/me/certificates/<course_id>')
    @require_user('student')
    def course_certificate(course_id):
        course = db.session.get(Course, course_id)
        enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=course_id, status='active').first()
        if not course or not enrollment:
            return problem(404, 'Curso ou matrícula ativa não encontrada')
        if progress_for(g.user.id, course_id) < 100:
            return problem(409, 'Conclua todas as aulas antes de emitir o certificado')
        certificate_id = uuid.uuid5(uuid.NAMESPACE_URL, f'learnplay:certificate:{g.user.id}:{course.id}').hex[:16].upper()
        student_name = html_escape(g.user.name)
        course_title = html_escape(course.title)
        issued_on = now_utc().strftime('%d/%m/%Y')
        page = f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Certificado LearnPlay — {course_title}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;padding:32px;background:#f0eef7;color:#242239;font-family:Georgia,"Times New Roman",serif}}
.sheet{{position:relative;display:flex;min-height:calc(100vh - 64px);align-items:center;justify-content:center;border:12px solid #7455e8;background:#fff;padding:8vw;text-align:center}}
.sheet:before{{content:"";position:absolute;inset:12px;border:1px solid #d8d0f4;pointer-events:none}}
.content{{max-width:900px}}.brand{{font:800 16px Arial,sans-serif;letter-spacing:4px;color:#7455e8;text-transform:uppercase}}
h1{{margin:44px 0 12px;font-size:clamp(38px,6vw,66px);font-weight:400}}.intro{{font:18px/1.7 Arial,sans-serif;color:#66647a}}
.name{{margin:30px 0 12px;font-size:clamp(32px,5vw,52px);color:#4e3ba4}}.course{{font-size:clamp(22px,3vw,34px);font-weight:700}}
.date{{margin-top:42px;font:14px Arial,sans-serif;color:#66647a}}.id{{margin-top:12px;font:11px Arial,sans-serif;color:#89879a}}
.print{{position:fixed;right:24px;top:24px;border:0;border-radius:10px;background:#7455e8;color:white;padding:12px 16px;font:700 14px Arial,sans-serif;cursor:pointer}}
@media print{{@page{{size:A4 landscape;margin:0}}body{{padding:0;background:white}}.sheet{{min-height:100vh;border-width:12px}}.print{{display:none}}}}
</style></head><body><button class="print" onclick="window.print()">Imprimir / salvar em PDF</button>
<main class="sheet"><div class="content"><div class="brand">LearnPlay · aprender abre caminhos</div><h1>Certificado de conclusão</h1>
<p class="intro">Certificamos que</p><div class="name">{student_name}</div>
<p class="intro">concluiu todas as aulas do curso</p><div class="course">{course_title}</div>
<p class="date">Emitido em {issued_on}</p><p class="id">Identificador do certificado: LP-{certificate_id}</p></div></main></body></html>'''
        response = make_response(page)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Content-Disposition'] = f'inline; filename="certificado-learnplay-{certificate_id}.html"'
        return response

    @app.post('/api/v1/courses/<course_id>/assessments/<assessment_id>/attempts')
    @require_user('student')
    def submit_assessment(course_id, assessment_id):
        enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=course_id, status='active').first()
        assessment = db.session.get(Assessment, assessment_id)
        if not enrollment or not assessment or assessment.course_id != course_id:
            return problem(403, 'Avaliação indisponível sem matrícula ativa')
        questions = AssessmentQuestion.query.filter_by(assessment_id=assessment_id).all()
        previous = AssessmentAttempt.query.filter_by(student_id=g.user.id, assessment_id=assessment_id).order_by(AssessmentAttempt.attempt_number).all()
        if len(previous) >= assessment.max_attempts:
            return problem(409, 'Limite de tentativas atingido')
        answers = (request.get_json(silent=True) or {}).get('answers', {})
        if len(answers) != len(questions):
            return problem(422, 'Responda todas as questões')
        correct = sum(1 for q in questions if str(answers.get(q.id)) == str(q.correct_option))
        score = round(100 * correct / len(questions)) if questions else 0
        attempt = AssessmentAttempt(assessment_id=assessment_id, student_id=g.user.id, attempt_number=len(previous) + 1, score=score)
        db.session.add(attempt)
        db.session.commit()
        return jsonify(attempt_number=attempt.attempt_number, score=score, passed=score >= assessment.passing_score,
                       best_score=max([x.score for x in previous] + [score]), attempts_remaining=assessment.max_attempts - attempt.attempt_number)

    @app.get('/api/v1/instructor/courses')
    @require_user('instructor', 'admin')
    def instructor_courses():
        q = Course.query if g.user.role == 'admin' else Course.query.filter_by(instructor_id=g.user.id)
        return jsonify(items=[c.public(details=True) for c in q.order_by(Course.title).all()])

    @app.post('/api/v1/instructor/courses')
    @require_user('instructor', 'admin')
    def create_course():
        data = request.get_json(silent=True) or {}
        title, description = str(data.get('title', '')).strip(), str(data.get('description', '')).strip()
        if len(title) < 4 or not description:
            return problem(422, 'Título e descrição são obrigatórios')
        try:
            price = Decimal(str(data.get('price', 0))).quantize(Decimal('0.01'))
            if price < 0:
                raise ValueError()
        except Exception:
            return problem(422, 'Preço inválido')
        course = Course(instructor_id=g.user.id, title=title, description=description, price=price,
                        category=str(data.get('category', 'Geral'))[:60], level=str(data.get('level', 'Iniciante'))[:30], status='draft')
        db.session.add(course)
        db.session.flush()
        section = Section(course_id=course.id, title='Comece por aqui', position=1)
        db.session.add(section)
        db.session.flush()
        db.session.add(Lesson(section_id=section.id, title='Boas-vindas', description='Apresente o objetivo do curso.', position=1, duration_seconds=300, status='draft'))
        db.session.commit()
        return jsonify(course=course.public(details=True)), 201

    @app.patch('/api/v1/instructor/courses/<course_id>')
    @require_user('instructor', 'admin')
    def update_course(course_id):
        course = db.session.get(Course, course_id)
        if not course or (g.user.role != 'admin' and course.instructor_id != g.user.id):
            return problem(404, 'Curso não encontrado')
        data = request.get_json(silent=True) or {}
        for field in ('title', 'description', 'category', 'level'):
            if field in data:
                setattr(course, field, str(data[field]).strip())
        if 'price' in data:
            try:
                course.price = Decimal(str(data['price'])).quantize(Decimal('0.01'))
                if course.price < 0:
                    raise ValueError()
            except Exception:
                return problem(422, 'Preço inválido')
        if 'status' in data:
            if data['status'] not in ('draft', 'published', 'archived'):
                return problem(422, 'Estado inválido')
            if data['status'] == 'published' and (not course.title or not course.description or Lesson.query.join(Section).filter(Section.course_id == course.id, Lesson.status == 'published').count() < 1):
                return problem(422, 'Publique ao menos uma aula antes de publicar o curso')
            course.status = data['status']
        db.session.commit()
        return jsonify(course=course.public(details=True))

    @app.post('/api/v1/instructor/courses/<course_id>/lessons')
    @require_user('instructor', 'admin')
    def create_lesson(course_id):
        course = db.session.get(Course, course_id)
        if not course or (g.user.role != 'admin' and course.instructor_id != g.user.id):
            return problem(404, 'Curso não encontrado')
        data = request.get_json(silent=True) or {}
        title = str(data.get('title', '')).strip()
        if len(title) < 3:
            return problem(422, 'Título da aula obrigatório')
        section = Section.query.filter_by(course_id=course.id).order_by(Section.position).first()
        if not section:
            section = Section(course_id=course.id, title='Conteúdo do curso', position=1)
            db.session.add(section)
            db.session.flush()
        position = (db.session.query(func.max(Lesson.position)).filter_by(section_id=section.id).scalar() or 0) + 1
        lesson = Lesson(section_id=section.id, title=title, description=str(data.get('description', '')).strip(),
                        duration_seconds=max(60, min(int(data.get('duration_seconds', 600)), 14400)), position=position,
                        status='published' if data.get('status') == 'published' else 'draft')
        db.session.add(lesson)
        db.session.commit()
        return jsonify(lesson=lesson.public(), status=lesson.status), 201

    @app.patch('/api/v1/instructor/courses/<course_id>/lessons/<lesson_id>')
    @require_user('instructor', 'admin')
    def update_lesson(course_id, lesson_id):
        course = db.session.get(Course, course_id)
        lesson = db.session.get(Lesson, lesson_id)
        section = db.session.get(Section, lesson.section_id) if lesson else None
        if not course or not lesson or not section or section.course_id != course.id or (g.user.role != 'admin' and course.instructor_id != g.user.id):
            return problem(404, 'Aula não encontrada')
        data = request.get_json(silent=True) or {}
        for field in ('title', 'description'):
            if field in data:
                setattr(lesson, field, str(data[field]).strip())
        if 'status' in data:
            if data['status'] not in ('draft', 'published', 'archived'):
                return problem(422, 'Estado inválido')
            lesson.status = data['status']
        db.session.commit()
        return jsonify(lesson=lesson.public(), status=lesson.status)

    @app.put('/api/v1/instructor/courses/<course_id>/assessment')
    @require_user('instructor', 'admin')
    def save_assessment(course_id):
        course = db.session.get(Course, course_id)
        if not course or (g.user.role != 'admin' and course.instructor_id != g.user.id):
            return problem(404, 'Curso não encontrado')
        data = request.get_json(silent=True) or {}
        questions = data.get('questions', [])
        if not isinstance(questions, list) or not 1 <= len(questions) <= 30:
            return problem(422, 'Informe de 1 a 30 questões')
        assessment = Assessment.query.filter_by(course_id=course.id).first()
        if not assessment:
            assessment = Assessment(course_id=course.id, title=str(data.get('title', 'Avaliação')), max_attempts=3)
            db.session.add(assessment)
            db.session.flush()
        assessment.title = str(data.get('title', assessment.title))[:140]
        assessment.passing_score = max(0, min(int(data.get('passing_score', 70)), 100))
        assessment.max_attempts = max(1, min(int(data.get('max_attempts', 3)), 10))
        AssessmentQuestion.query.filter_by(assessment_id=assessment.id).delete()
        for pos, item in enumerate(questions, 1):
            options = item.get('options', [])
            answer = int(item.get('correct_option', -1))
            if not isinstance(options, list) or len(options) < 2 or not 0 <= answer < len(options):
                db.session.rollback()
                return problem(422, 'Questão com alternativas ou gabarito inválido')
            db.session.add(AssessmentQuestion(assessment_id=assessment.id, prompt=str(item.get('prompt', ''))[:400], options=options, correct_option=answer, position=pos))
        db.session.commit()
        return jsonify(assessment=assessment.public())
    @app.patch('/api/v1/admin/users/<user_id>')
    @require_user('admin')
    def admin_update_user(user_id):
        user = db.session.get(User, user_id)
        if not user:
            return problem(404, 'Usuário não encontrado')
        data = request.get_json(silent=True) or {}
        if 'role' in data:
            if data['role'] not in ('student', 'instructor', 'admin'):
                return problem(422, 'Perfil inválido')
            user.role = data['role']
        if 'status' in data:
            if data['status'] not in ('active', 'suspended'):
                return problem(422, 'Estado inválido')
            if data['status'] == 'suspended' and user.status != 'suspended':
                if user.id == g.user.id:
                    return problem(409, 'Você não pode suspender a própria conta administrativa')
                if user.role == 'admin' and User.query.filter_by(role='admin', status='active').count() <= 1:
                    return problem(409, 'A plataforma precisa manter ao menos um administrador ativo')
            user.status = data['status']
        db.session.commit()
        return jsonify(user=user.public())

    @app.delete('/api/v1/admin/users/<user_id>')
    @require_user('admin')
    def admin_delete_student(user_id):
        user = db.session.get(User, user_id)
        if not user:
            return problem(404, 'Usuário não encontrado')
        if user.role != 'student':
            return problem(409, 'Somente contas de alunos podem ser excluídas por esta ação')

        enrollment_ids = db.session.query(Enrollment.id).filter_by(student_id=user.id).subquery()
        PaymentEvent.query.filter(PaymentEvent.enrollment_id.in_(enrollment_ids)).delete(synchronize_session=False)
        AssessmentAttempt.query.filter_by(student_id=user.id).delete(synchronize_session=False)
        CourseResume.query.filter_by(student_id=user.id).delete(synchronize_session=False)
        LessonCompletion.query.filter_by(student_id=user.id).delete(synchronize_session=False)
        Favorite.query.filter_by(student_id=user.id).delete(synchronize_session=False)
        NotificationOutbox.query.filter_by(recipient_id=user.id).delete(synchronize_session=False)
        ServerSession.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        Enrollment.query.filter_by(student_id=user.id).delete(synchronize_session=False)
        db.session.delete(user)
        db.session.commit()
        return '', 204

    @app.get('/api/v1/admin/users')
    @require_user('admin')
    def admin_users():
        return jsonify(items=[x.public() for x in User.query.order_by(User.name).all()])

    @app.post('/api/v1/integrations/payments/webhook')
    def payment_webhook():
        secret = os.getenv('PAYMENT_WEBHOOK_SECRET', '')
        raw_body = request.get_data(cache=True)
        supplied = request.headers.get('X-Webhook-Signature', '')
        import hmac
        expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest() if secret else ''
        if not secret or not hmac.compare_digest(expected, supplied):
            return problem(401, 'Assinatura do webhook inválida')
        data = request.get_json(silent=True) or {}
        event_id = str(data.get('event_id', ''))[:160]
        enrollment = db.session.get(Enrollment, str(data.get('enrollment_id', '')))
        if not event_id or not enrollment:
            return problem(404, 'Evento ou matrícula não encontrada')
        previous = PaymentEvent.query.filter_by(provider_event_id=event_id).first()
        if previous:
            return jsonify(status=previous.status, duplicate=True)
        digest = hashlib.sha256(raw_body).hexdigest()
        event = PaymentEvent(provider_event_id=event_id, enrollment_id=enrollment.id, payload_digest=digest, status='received')
        db.session.add(event)
        try:
            amount = Decimal(str(data.get('amount', '-1'))).quantize(Decimal('0.01'))
        except Exception:
            amount = Decimal('-1.00')
        if amount != enrollment.course.price or data.get('currency') != 'BRL':
            event.status = 'review'
            db.session.commit()
            return problem(422, 'Valor/moeda divergente; evento enviado para revisão')
        if data.get('status') == 'approved' and enrollment.status == 'pending_payment':
            enrollment.status, enrollment.activated_at = 'active', now_utc()
            db.session.add(NotificationOutbox(event_key=f'enrollment:{enrollment.id}', recipient_id=enrollment.student_id, event_type='enrollment_confirmed', payload={'course_id': enrollment.course_id}))
        elif data.get('status') == 'failed' and enrollment.status == 'pending_payment':
            enrollment.status = 'payment_failed'
        event.status = 'processed'
        db.session.commit()
        return jsonify(status=enrollment.status, duplicate=False)

    return app


def problem(status, detail):
    return jsonify(type='about:blank', title='Erro na solicitação', status=status, detail=detail), status


def seed_demo_data():
    """Seed predictable local demo accounts and the LearnPlay catalog."""
    if User.query.first():
        return
    student = User(name='Ana Martins', email='aluna@learnplay.local', password_hash=generate_password_hash(os.getenv('DEMO_STUDENT_PASSWORD', 'Aluno12345!'), method='scrypt'), role='student')
    teacher = User(name='Rafael Costa', email='professor@learnplay.local', password_hash=generate_password_hash(os.getenv('DEMO_INSTRUCTOR_PASSWORD', 'Professor123!'), method='scrypt'), role='instructor')
    admin = User(name='Equipe LearnPlay', email='admin@learnplay.local', password_hash=generate_password_hash(os.getenv('DEMO_ADMIN_PASSWORD', 'Admin123456!'), method='scrypt'), role='admin')
    db.session.add_all([student, teacher, admin])
    db.session.flush()
    courses = [
        Course(instructor_id=teacher.id, title='Python do zero ao primeiro projeto', description='Aprenda lógica, estruturas de dados e automação criando projetos práticos desde a primeira aula.', category='Programação', level='Iniciante', price=0, status='published', cover_color='violet'),
        Course(instructor_id=teacher.id, title='Design de interfaces digitais', description='Construa interfaces acessíveis, consistentes e prontas para testes com fundamentos de UX e UI.', category='Design', level='Intermediário', price=89.90, status='published', cover_color='orange'),
        Course(instructor_id=teacher.id, title='Git e GitHub para equipes', description='Domine branches, revisão de código e colaboração em projetos reais.', category='Tecnologia', level='Iniciante', price=49.90, status='published', cover_color='blue'),
        Course(instructor_id=teacher.id, title='Comunicação e liderança', description='Práticas para conduzir reuniões, dar feedback e alinhar objetivos.', category='Negócios', level='Todos os níveis', price=0, status='published', cover_color='green'),
    ]
    db.session.add_all(courses)
    db.session.flush()
    for course, topics in zip(courses, [
        ['Primeiros passos com Python', 'Variáveis e tipos de dados', 'Decisões e repetições', 'Projeto: lista de tarefas'],
        ['Princípios de UX', 'Tipografia e cor', 'Componentes e estados'],
        ['Versionamento na prática', 'Branches e merges', 'Pull requests'],
        ['Comunicação clara', 'Feedback que desenvolve', 'Plano de ação'],
    ]):
        section = Section(course_id=course.id, title='Fundamentos e prática', position=1)
        db.session.add(section)
        db.session.flush()
        for pos, title in enumerate(topics, 1):
            db.session.add(Lesson(section_id=section.id, title=title, description=f'Conteúdo demonstrativo: {title.lower()}.', position=pos, duration_seconds=600 + pos * 120))
        assessment = Assessment(course_id=course.id, title='Revisão do módulo', passing_score=70, max_attempts=3)
        db.session.add(assessment)
        db.session.flush()
        db.session.add_all([
            AssessmentQuestion(assessment_id=assessment.id, prompt='Qual é o objetivo principal deste módulo?', options=['Aplicar os conceitos em um exercício', 'Ignorar a prática', 'Evitar revisar o conteúdo'], correct_option=0, position=1),
            AssessmentQuestion(assessment_id=assessment.id, prompt='Qual é uma boa forma de consolidar o aprendizado?', options=['Não praticar', 'Construir um pequeno projeto', 'Pular todas as aulas'], correct_option=1, position=2),
        ])
    db.session.commit()


app = create_app()
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if os.getenv('SEED_DEMO', 'true').lower() == 'true':
            seed_demo_data()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')), debug=False)






