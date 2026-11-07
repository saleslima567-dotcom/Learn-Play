# LearnPlay API

Flask REST API em `backend/learnplay/app.py`; sessão de servidor persistida no banco. O arquivo `wsgi.py` cria o esquema inicial do protótipo e popula dados de demonstração. PostgreSQL é o padrão do Compose; SQLite é usado na execução local/testes.

`python -m pip install -r requirements.txt`
`python wsgi.py` (na pasta backend)
`python -m pytest -q`

O gateway de pagamento, mídia S3 e envio de e-mail são adaptadores demonstrativos. O webhook requer `PAYMENT_WEBHOOK_SECRET`; notificações são processadas pelo worker e registradas como `sent_demo`.
