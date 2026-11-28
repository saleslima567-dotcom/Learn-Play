# Python / backend/learnplay/app.py / Python 3.12 + Flask / LearnPlay REST API
from __future__ import annotations

import hashlib
import ipaddress
import time
from html import escape as html_escape
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import wraps
from urllib.parse import urlsplit

from flask import Flask, current_app, g, jsonify, make_response, render_template, request, send_file, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, and_, case, func, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge
from werkzeug.security import check_password_hash, generate_password_hash


from .demo_payments import METHODS, payment_qr, payment_receipt


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


class RateLimitBucket(db.Model):
    key = db.Column(db.String(64), primary_key=True)
    window = db.Column(db.BigInteger, primary_key=True)
    count = db.Column(db.Integer, nullable=False)


def take_rate_limit(scope, subject, limit, seconds=600):
    # Shared, atomic counters across Gunicorn workers; no extra service required.
    window = int(time.time()) // seconds * seconds
    key = token_hash(scope + ':' + subject)
    table = RateLimitBucket.__table__
    with db.engine.begin() as conn:
        insert = pg_insert if conn.dialect.name == 'postgresql' else sqlite_insert
        stmt = insert(table).values(key=key, window=window, count=1)
        stmt = stmt.on_conflict_do_update(index_elements=[table.c.key, table.c.window],
            set_={'count': table.c.count + 1},
            where=table.c.count < limit).returning(table.c.count)
        allowed = conn.execute(stmt).scalar_one_or_none() is not None
        # Expired buckets need not be retained; amortize cleanup.
        if secrets.randbelow(100) == 0:
            conn.execute(table.delete().where(table.c.window < int(time.time()) - 86400))
    return allowed


def client_address(app):
    # Trust forwarded addresses only when an operator explicitly configures
    # the number of trusted ingress hops. Do not trust caller-supplied prefixes.
    address = request.remote_addr or 'unknown'
    hops = app.config['TRUST_PROXY_HOPS']
    if hops:
        chain = request.headers.get('X-Forwarded-For', '').split(',')
        if len(chain) >= hops:
            address = chain[-hops].strip()
    try:
        return str(ipaddress.ip_address(address))
    except ValueError:
        return 'unknown'


DEMO_INSTRUCTOR_EMAIL = 'professor@learnplay.local'


# Public local demonstration credentials must never be accepted in production.
DEMO_ACCOUNTS = (
    ('aluna@learnplay.local', 'DEMO_STUDENT_PASSWORD', 'Aluno12345!'),
    (DEMO_INSTRUCTOR_EMAIL, 'DEMO_INSTRUCTOR_PASSWORD', 'Professor123!'),
    ('admin@learnplay.local', 'DEMO_ADMIN_PASSWORD', 'Admin123456!'),
)


def production_mode(app):
    return bool(app.config['SESSION_COOKIE_SECURE'] or os.getenv('RENDER') == 'true')


def demo_password(email):
    return next((default for address, _, default in DEMO_ACCOUNTS if address == email), None)


def revoke_insecure_demo_sessions():
    # Rotate only known insecure demo passwords using operator-configured secrets.
    if not production_mode(current_app):
        return
    defaults = {row[2] for row in DEMO_ACCOUNTS}
    configured = [os.getenv(key, '') for _, key, _ in DEMO_ACCOUNTS]
    for email, key, default in DEMO_ACCOUNTS:
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, default):
            continue
        new_password = os.getenv(key, '')
        if 16 <= len(new_password) <= 128 and new_password not in defaults and configured.count(new_password) == 1:
            user.password_hash = generate_password_hash(new_password, method='scrypt')
            current_app.logger.info('Rotated insecure demo credential for role=%s', user.role)
        else:
            current_app.logger.warning('Insecure demo credential blocked for role=%s; configure a unique strong secret in %s and redeploy.', user.role, key)
        ServerSession.query.filter_by(user_id=user.id, revoked_at=None).update({'revoked_at': now_utc()})
    db.session.commit()


# Public names in the demo catalog are separate from the account that manages the courses.
DEMO_COURSE_INSTRUCTORS = {
    ('Programação', 'Python do zero ao primeiro projeto'): 'Marina Azevedo',
    ('Design', 'Design de interfaces digitais'): 'Elisa Moura',
    ('Tecnologia', 'Git e GitHub para equipes'): 'Bruno Almeida',
    ('Negócios', 'Comunicação e liderança'): 'Camila Nogueira',
}


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

    def public(self, details=False, include_titles=False):
        lessons = Lesson.query.join(Section).filter(Section.course_id == self.id, Lesson.status == 'published').order_by(Section.position, Lesson.position).all()
        demo_name = None
        if self.instructor.email == DEMO_INSTRUCTOR_EMAIL:
            demo_name = DEMO_COURSE_INSTRUCTORS.get((self.category, self.title))
        data = {'id': self.id, 'title': self.title, 'description': self.description, 'category': self.category,
                'level': self.level, 'price': float(self.price), 'status': self.status,
                'cover_color': self.cover_color, 'instructor': demo_name or self.instructor.name,
                'instructor_is_demo': demo_name is not None,
                'lesson_count': len(lessons), 'duration_minutes': sum(x.duration_seconds for x in lessons) // 60}
        if include_titles:
            data['lesson_titles'] = [lesson.title for lesson in lessons]
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


class SharedCertificate(db.Model):
    enrollment_id = db.Column(db.String(36), db.ForeignKey('enrollment.id', ondelete='CASCADE'), primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False)
    holder_name = db.Column(db.String(100), nullable=False)
    course_title = db.Column(db.String(140), nullable=False)
    issued_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)

    def verification_url(self):
        return url_for('verify_shared_certificate', token=self.token)


class ProjectAchievement(db.Model):
    student_id = db.Column(db.String(36), db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    course_id = db.Column(db.String(36), db.ForeignKey('course.id', ondelete='CASCADE'), primary_key=True)
    url = db.Column(db.String(2048), nullable=False)


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


class DemoPayment(db.Model):
    enrollment_id = db.Column(db.String(36), db.ForeignKey('enrollment.id', ondelete='CASCADE'), primary_key=True)
    reference = db.Column(db.String(36), nullable=False, unique=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    course_title = db.Column(db.String(140), nullable=False)
    method = db.Column(db.String(12), nullable=False)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)


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


def course_lessons_completed(student_id, course_id):
    published = Lesson.query.join(Section).filter(Section.course_id == course_id, Lesson.status == 'published')
    completed_ids = db.session.query(LessonCompletion.lesson_id).filter_by(student_id=student_id)
    return published.first() is not None and published.filter(~Lesson.id.in_(completed_ids)).first() is None


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
        MAX_CONTENT_LENGTH=128 * 1024,
        TRUST_PROXY_HOPS=int(os.getenv('TRUST_PROXY_HOPS', '0')),
        RATE_LIMITS_ENABLED=True,
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_error):
        return problem(413, 'Requisição muito grande')

    @app.errorhandler(BadRequest)
    def malformed(_error):
        return problem(400, 'Requisição inválida')

    @app.before_request
    def protect_requests():
        if not request.path.startswith('/api/v1/'):
            return
        if request.content_length is not None and request.content_length > app.config['MAX_CONTENT_LENGTH']:
            return problem(413, 'Requisição muito grande')
        data = {}
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and request.is_json:
            data = request.get_json()
            if not isinstance(data, dict):
                return problem(422, 'O corpo JSON deve ser um objeto')
        if not app.config['RATE_LIMITS_ENABLED']:
            return
        path = request.path
        ip = client_address(app)
        buckets = []
        if path == '/api/v1/auth/csrf':
            buckets = [('csrf-ip', ip, 60)]
        elif path == '/api/v1/auth/register':
            buckets = [('register-ip', ip, 10)]
        elif path == '/api/v1/auth/login':
            email = data.get('email', '')
            email = email.strip().lower()[:254] if isinstance(email, str) else ''
            buckets = [('login-ip', ip, 30), ('login-account', email, 10)]
        if any(not take_rate_limit(scope, subject, limit) for scope, subject, limit in buckets):
            response = jsonify(type='about:blank', title='Limite de solicitações', status=429, detail='Muitas solicitações. Tente novamente mais tarde.')
            response.status_code = 429
            response.headers['Retry-After'] = str(600 - int(time.time()) % 600)
            return response

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
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            if not g.server_session or not secrets.compare_digest(token_hash(request.headers.get('X-CSRF-Token', '')), g.server_session.csrf_hash):
                return problem(403, 'Token CSRF ausente ou inválido')

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        certificate_verification = request.path.startswith('/certificados/verificar/')
        response.headers['Referrer-Policy'] = 'no-referrer' if certificate_verification else 'same-origin'
        if certificate_verification:
            response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
        response.headers['Cache-Control'] = 'no-store' if certificate_verification or request.path.startswith('/api/v1/') else 'no-cache'
        if request.path.startswith('/api/v1/'):
            response.vary.add('Cookie')
        if production_mode(app):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
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
        if not all(isinstance(data.get(field), str) for field in ('name', 'email', 'password')):
            return problem(422, 'Campos de cadastro inválidos')
        name, email, password = data['name'].strip(), data['email'].strip().lower(), data['password']
        if len(name) < 2 or len(name) > 100 or not 3 <= len(email) <= 254 or email.count('@') != 1 or not all(email.split('@')) or any(c.isspace() for c in email) or len(password) < 10 or len(password) > 128:
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
        email, password = data.get('email'), data.get('password')
        if not isinstance(email, str) or not isinstance(password, str) or not 1 <= len(email) <= 254 or not 1 <= len(password) <= 128:
            return problem(401, 'E-mail ou senha inválidos')
        email = email.strip().lower()
        if production_mode(app) and demo_password(email) == password:
            return problem(401, 'E-mail ou senha inválidos')
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password) or user.status != 'active':
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
        return jsonify(items=[c.public(include_titles=True) for c in items], next_cursor=None)

    @app.get('/api/v1/courses/<course_id>')
    def course_detail(course_id):
        course = db.session.get(Course, course_id)
        if not course or course.status != 'published':
            return problem(404, 'Curso não encontrado')
        data = course.public(details=True)
        if g.user:
            enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=course.id).first()
            data['enrollment_status'] = enrollment.status if enrollment else None
            if enrollment and enrollment.status == 'active':
                achievement = db.session.get(ProjectAchievement, (g.user.id, course_id))
                data['project_url'] = achievement.url if achievement else None
                shared = db.session.get(SharedCertificate, enrollment.id)
                data['certificate_verification_url'] = shared.verification_url() if shared else None
            data['completed_lesson_ids'] = [x.lesson_id for x in LessonCompletion.query.join(Lesson).join(Section).filter(LessonCompletion.student_id == g.user.id, Section.course_id == course.id).all()]
        return jsonify(data)

    @app.post('/api/v1/courses/<course_id>/enrollments')
    @require_user('student')
    def enroll(course_id):
        course = db.session.get(Course, course_id)
        if not course or course.status != 'published':
            return problem(404, 'Curso não encontrado')
        status = 'active' if course.price == 0 else 'pending_payment'
        insert = pg_insert if db.engine.dialect.name == 'postgresql' else sqlite_insert
        statement = insert(Enrollment).values(
            id=str(uuid.uuid4()), student_id=g.user.id, course_id=course.id,
            status=status, activated_at=now_utc() if status == 'active' else None,
        )
        key = ['student_id', 'course_id']
        if status == 'active':
            statement = statement.on_conflict_do_update(
                index_elements=key, set_={'status': status, 'activated_at': statement.excluded.activated_at},
                where=Enrollment.status != status,
            )
        else:
            statement = statement.on_conflict_do_nothing(index_elements=key)
        created = db.session.execute(statement.returning(Enrollment.id)).scalar()
        if created and status == 'active':
            notify_enrollment(created, g.user.id, course.id)
        db.session.commit()
        enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=course.id).one()
        return jsonify(enrollment.public()), (201 if status == 'active' else 202) if created else 200

    def notify_enrollment(enrollment_id, student_id, course_id):
        db.session.add(NotificationOutbox(event_key=f'enrollment:{enrollment_id}', recipient_id=student_id,
                                          event_type='enrollment_confirmed', payload={'course_id': course_id}))

    def owned_enrollment(enrollment_id, lock=False):
        if len(enrollment_id) != 36:
            return None
        query = Enrollment.query.filter_by(id=enrollment_id, student_id=g.user.id)
        if lock and db.engine.dialect.name == 'sqlite':
            # SQLite serializes writers and does not implement SELECT FOR UPDATE.
            db.session.execute(update(Enrollment).where(Enrollment.id == enrollment_id,
                               Enrollment.student_id == g.user.id).values(status=Enrollment.status))
        return (query.with_for_update() if lock else query).first()

    def payment_state(enrollment, payment):
        approved = bool(payment and payment.approved_at and enrollment.status == 'active')
        pending = bool(enrollment.status != 'active' and enrollment.course.status == 'published' and enrollment.course.price > 0)
        current = payment if approved or (pending and payment and payment.amount == enrollment.course.price) else None
        return jsonify(
            enrollment_status=enrollment.status,
            available=pending,
            course_title=current.course_title if current else enrollment.course.title,
            amount=float(current.amount if current else enrollment.course.price),
            method=current.method if current else None,
            reference=current.reference if current else None,
            qr_url=url_for('demo_pix_qr', enrollment_id=enrollment.id, reference=current.reference)
            if current and current.method == 'pix' and not approved else None,
            receipt_url=url_for('download_payment_receipt', enrollment_id=enrollment.id) if approved else None,
        )

    @app.get('/api/v1/me/enrollments/<enrollment_id>/payment')
    @require_user('student')
    def get_payment(enrollment_id):
        enrollment = owned_enrollment(enrollment_id)
        if not enrollment:
            return problem(404, 'Matrícula não encontrada')
        return payment_state(enrollment, db.session.get(DemoPayment, enrollment.id))

    @app.post('/api/v1/me/enrollments/<enrollment_id>/payment')
    @require_user('student')
    def prepare_payment(enrollment_id):
        enrollment = owned_enrollment(enrollment_id, lock=True)
        if not enrollment:
            return problem(404, 'Matrícula não encontrada')
        payment = db.session.get(DemoPayment, enrollment.id)
        if enrollment.status == 'active':
            return payment_state(enrollment, payment)
        course = enrollment.course
        if course.price <= 0 or course.status != 'published':
            return problem(409, 'Este curso está indisponível para pagamento')
        data = request.get_json(silent=True)
        method = data.get('method') if isinstance(data, dict) else None
        if not isinstance(method, str) or method not in METHODS:
            return problem(422, 'Escolha Pix, crédito ou débito')
        if not payment:
            payment = DemoPayment(enrollment_id=enrollment.id)
            db.session.add(payment)
        if payment.method != method or payment.amount != course.price:
            payment.method, payment.amount = method, course.price
            payment.course_title, payment.reference = course.title, str(uuid.uuid4())
        db.session.commit()
        return payment_state(enrollment, payment)

    @app.post('/api/v1/me/enrollments/<enrollment_id>/payment/approve')
    @require_user('student')
    def approve_payment(enrollment_id):
        enrollment = owned_enrollment(enrollment_id, lock=True)
        if not enrollment:
            return problem(404, 'Matrícula não encontrada')
        payment = db.session.get(DemoPayment, enrollment.id)
        if enrollment.status == 'active':
            return payment_state(enrollment, payment)
        data = request.get_json(silent=True)
        reference = data.get('reference') if isinstance(data, dict) else None
        if (not payment or payment.reference != reference or payment.amount != enrollment.course.price
                or enrollment.course.price <= 0 or enrollment.course.status != 'published'):
            return problem(409, 'Os dados do pagamento mudaram. Escolha a forma de pagamento novamente.')
        payment.approved_at = now_utc()
        enrollment.status, enrollment.activated_at = 'active', payment.approved_at
        notify_enrollment(enrollment.id, enrollment.student_id, enrollment.course_id)
        db.session.commit()
        return payment_state(enrollment, payment)

    @app.get('/api/v1/me/enrollments/<enrollment_id>/pix/<reference>.png')
    @require_user('student')
    def demo_pix_qr(enrollment_id, reference):
        enrollment = owned_enrollment(enrollment_id)
        payment = db.session.get(DemoPayment, enrollment.id) if enrollment else None
        if (not payment or payment.method != 'pix' or payment.reference != reference or payment.approved_at
                or enrollment.status == 'active' or payment.amount != enrollment.course.price
                or enrollment.course.status != 'published'):
            return problem(404, 'QR Code indisponível')
        return send_file(payment_qr(payment.reference), mimetype='image/png')

    @app.get('/api/v1/me/enrollments/<enrollment_id>/receipt')
    @require_user('student')
    def download_payment_receipt(enrollment_id):
        enrollment = owned_enrollment(enrollment_id)
        payment = db.session.get(DemoPayment, enrollment.id) if enrollment else None
        if not payment or not payment.approved_at or enrollment.status != 'active':
            return problem(404, 'Comprovante não disponível')
        return send_file(payment_receipt(payment, g.user.name), mimetype='application/pdf', as_attachment=True,
                         download_name=f'learnplay-comprovante-teste-{payment.reference}.pdf')

    @app.get('/api/v1/me/enrollments')
    @require_user()
    def my_enrollments():
        items = Enrollment.query.filter_by(student_id=g.user.id).order_by(Enrollment.created_at.desc()).all()
        active_ids = [item.course_id for item in items if item.status == 'active']
        targets = {}
        if active_ids:
            # Same fallback as the classroom: saved lesson, first unfinished, then first published.
            rows = (db.session.query(Section.course_id, Lesson.id, Lesson.title, CourseResume.id)
                    .select_from(Lesson).join(Section, Section.id == Lesson.section_id)
                    .outerjoin(CourseResume, and_(CourseResume.student_id == g.user.id,
                               CourseResume.course_id == Section.course_id, CourseResume.lesson_id == Lesson.id))
                    .outerjoin(LessonCompletion, and_(LessonCompletion.student_id == g.user.id,
                               LessonCompletion.lesson_id == Lesson.id))
                    .filter(Section.course_id.in_(active_ids), Lesson.status == 'published')
                    .order_by(Section.course_id, case((CourseResume.id.is_not(None), 0),
                              (LessonCompletion.id.is_(None), 1), else_=2),
                              Section.position, Lesson.position, Lesson.id))
            for course_id, lesson_id, title, saved in rows:
                if course_id not in targets:
                    targets[course_id] = {'id': lesson_id, 'title': title, 'saved': saved is not None}
        paid_ids = {row.enrollment_id for row in db.session.query(DemoPayment.enrollment_id).filter(
            DemoPayment.enrollment_id.in_([item.id for item in items if item.status == 'active']),
            DemoPayment.approved_at.is_not(None),
        )}
        return jsonify(items=[{
            **item.public(), 'resume_lesson': targets.get(item.course_id),
            'receipt_url': url_for('download_payment_receipt', enrollment_id=item.id) if item.id in paid_ids else None,
        } for item in items])

    @app.put('/api/v1/me/projects/<course_id>')
    @require_user('student')
    def save_project_achievement(course_id):
        enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=course_id, status='active').first()
        if not enrollment or enrollment.course.status != 'published':
            return problem(403, 'Matrícula ativa necessária')
        if not course_lessons_completed(g.user.id, course_id):
            return problem(409, 'Conclua todas as aulas antes de registrar a entrega')
        body = request.get_json(silent=True)
        url = body.get('url') if isinstance(body, dict) else None
        if not isinstance(url, str) or len(url) > 2048:
            return problem(422, 'Informe um link HTTPS válido')
        url = url.strip()
        try:
            parsed = urlsplit(url)
            valid = (parsed.scheme == 'https' and parsed.hostname and parsed.username is None
                     and parsed.password is None and not any(ch.isspace() or ord(ch) < 32 or ch == '\\' for ch in url))
        except ValueError:
            valid = False
        if not valid:
            return problem(422, 'Informe um link HTTPS válido')
        insert = pg_insert if db.engine.dialect.name == 'postgresql' else sqlite_insert
        record = insert(ProjectAchievement).values(student_id=g.user.id, course_id=course_id, url=url)
        db.session.execute(record.on_conflict_do_update(index_elements=['student_id', 'course_id'], set_={'url': url}))
        db.session.commit()
        return jsonify(project_url=url)

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

    @app.route('/api/v1/me/certificates/<course_id>/share', methods=['PUT', 'DELETE'])
    @require_user('student')
    def share_certificate(course_id):
        enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=course_id,
                                                 status='active').with_for_update().first()
        if not enrollment:
            return problem(404, 'Curso ou matrícula ativa não encontrada')
        certificate = db.session.get(SharedCertificate, enrollment.id)
        if request.method == 'DELETE':
            if certificate:
                db.session.delete(certificate)
                db.session.commit()
            return '', 204
        if certificate is None:
            if not course_lessons_completed(g.user.id, course_id):
                return problem(409, 'Conclua todas as aulas antes de compartilhar o certificado')
            certificate = SharedCertificate(enrollment_id=enrollment.id, token=secrets.token_urlsafe(24),
                                            holder_name=g.user.name, course_title=enrollment.course.title)
            db.session.add(certificate)
        # Capture the URL before commit so a concurrent revoke cannot expire the ORM instance first.
        verification_url = certificate.verification_url()
        db.session.commit()
        return jsonify(verification_url=verification_url)

    @app.get('/certificados/verificar/<token>')
    def verify_shared_certificate(token):
        certificate = None
        if len(token) == 32:
            certificate = (SharedCertificate.query.join(Enrollment).join(User, User.id == Enrollment.student_id)
                           .filter(SharedCertificate.token == token, Enrollment.status == 'active',
                                   User.status == 'active').first())
        if not certificate:
            return render_template('certificate_verification.html', certificate=None), 404
        return render_template('certificate_verification.html', certificate=certificate,
                               issued_on=certificate.issued_at.strftime('%d/%m/%Y'))

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
        # Serialize attempts per enrollment in PostgreSQL before reading the count.
        enrollment = Enrollment.query.filter_by(student_id=g.user.id, course_id=course_id, status='active').with_for_update().first()
        assessment = db.session.get(Assessment, assessment_id)
        if not enrollment or not assessment or assessment.course_id != course_id:
            return problem(403, 'Avaliação indisponível sem matrícula ativa')
        questions = AssessmentQuestion.query.filter_by(assessment_id=assessment_id).all()
        previous = AssessmentAttempt.query.filter_by(student_id=g.user.id, assessment_id=assessment_id).order_by(AssessmentAttempt.attempt_number).all()
        if len(previous) >= assessment.max_attempts:
            return problem(409, 'Limite de tentativas atingido')
        answers = (request.get_json(silent=True) or {}).get('answers', {})
        if not isinstance(answers, dict) or set(answers) != {q.id for q in questions} or any(type(answers[q.id]) is not int or not 0 <= answers[q.id] < len(q.options) for q in questions):
            return problem(422, 'Responda todas as questões')
        incorrect_ids = [q.id for q in questions if answers[q.id] != q.correct_option]
        score = round(100 * (len(questions) - len(incorrect_ids)) / len(questions)) if questions else 0
        attempt = AssessmentAttempt(assessment_id=assessment_id, student_id=g.user.id, attempt_number=len(previous) + 1, score=score)
        db.session.add(attempt)
        db.session.commit()
        return jsonify(attempt_number=attempt.attempt_number, score=score, passed=score >= assessment.passing_score,
                       best_score=max([x.score for x in previous] + [score]), attempts_remaining=assessment.max_attempts - attempt.attempt_number,
                       incorrect_question_ids=incorrect_ids)

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
        SharedCertificate.query.filter(SharedCertificate.enrollment_id.in_(enrollment_ids.select())).delete(synchronize_session=False)
        DemoPayment.query.filter(DemoPayment.enrollment_id.in_(enrollment_ids.select())).delete(synchronize_session=False)
        PaymentEvent.query.filter(PaymentEvent.enrollment_id.in_(enrollment_ids.select())).delete(synchronize_session=False)
        AssessmentAttempt.query.filter_by(student_id=user.id).delete(synchronize_session=False)
        ProjectAchievement.query.filter_by(student_id=user.id).delete(synchronize_session=False)
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

    return app


def problem(status, detail):
    return jsonify(type='about:blank', title='Erro na solicitação', status=status, detail=detail), status


def seed_demo_data():
    """Seed predictable local demo accounts and the LearnPlay catalog."""
    if User.query.first():
        return
    from flask import current_app
    configured = [os.getenv(key) for _, key, _ in DEMO_ACCOUNTS]
    if production_mode(current_app) and (
        any(not value or len(value) < 16 or len(value) > 128 or value in {row[2] for row in DEMO_ACCOUNTS} for value in configured)
        or len(set(configured)) != len(configured)
    ):
        current_app.logger.warning('Demo seed skipped: production requires three unique non-default secrets.')
        return
    student = User(name='Ana Martins', email='aluna@learnplay.local', password_hash=generate_password_hash(os.getenv('DEMO_STUDENT_PASSWORD', 'Aluno12345!'), method='scrypt'), role='student')
    teacher = User(name='Rafael Costa', email=DEMO_INSTRUCTOR_EMAIL, password_hash=generate_password_hash(os.getenv('DEMO_INSTRUCTOR_PASSWORD', 'Professor123!'), method='scrypt'), role='instructor')
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
        revoke_insecure_demo_sessions()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')), debug=False)






