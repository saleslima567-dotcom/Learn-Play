# Python / backend/wsgi.py / Python 3.12 + Gunicorn / descomplica cursos API runtime
import os

from learnplay.app import app


if __name__ == '__main__':
    from init_db import initialize_database

    initialize_database()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')), debug=False)
