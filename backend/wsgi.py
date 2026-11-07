# Python / backend/wsgi.py / Python 3.12 + Gunicorn / LearnPlay API runtime
from learnplay.app import app, db, seed_demo_data

with app.app_context():
    db.create_all()
    if __import__('os').getenv('SEED_DEMO', 'true').lower() == 'true':
        seed_demo_data()
