# Python / backend/worker.py / Python 3.12 / LearnPlay notification outbox worker
import time
from learnplay.app import create_app, db, NotificationOutbox

app = create_app()


def dispatch_once():
    with app.app_context():
        rows = NotificationOutbox.query.filter_by(status='pending').order_by(NotificationOutbox.created_at).limit(50).all()
        for event in rows:
            event.attempts += 1
            app.logger.info('notification_demo_delivered type=%s event_key=%s recipient_id=%s', event.event_type, event.event_key, event.recipient_id)
            event.status = 'sent_demo'
        db.session.commit()
        return len(rows)


if __name__ == '__main__':
    while True:
        dispatch_once()
        time.sleep(int(os.getenv('OUTBOX_POLL_SECONDS', '5')))
