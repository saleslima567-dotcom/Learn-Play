# Python / backend/init_db.py / Python 3.12 / descomplica cursos one-time database initializer
import os

from learnplay.app import app, db, seed_demo_data


def initialize_database():
    with app.app_context():
        lock_connection = db.engine.connect()
        postgres = db.engine.dialect.name == 'postgresql'
        try:
            if postgres:
                lock_connection.execute(db.text('SELECT pg_advisory_lock(274991, 1)'))
                lock_connection.commit()
            db.create_all()
            if os.getenv('SEED_DEMO', 'true').lower() == 'true':
                seed_demo_data()
        finally:
            if postgres:
                lock_connection.execute(db.text('SELECT pg_advisory_unlock(274991, 1)'))
                lock_connection.commit()
            lock_connection.close()


if __name__ == '__main__':
    initialize_database()
