# Trabalho Da Faculdade — LearnPlay

Plataforma demonstrativa de cursos online, desenvolvida com base na arquitetura dos Passos 1 e 2. O código do Passo 3 está em `frontend/`, `backend/` e `compose.yaml`.

## O que funciona no protótipo

O Passo 3 está descrito em `03_Passo_3_Prototipo.md`.

## Demonstração online

Visite o [LearnPlay hospedado no Render](https://learnplay-lzk9.onrender.com) para explorar este mini projeto: navegue pelo catálogo de cursos, veja as páginas de detalhes e experimente os fluxos demonstrativos de conta, matrícula, aulas e progresso. Pagamentos e reprodução de vídeos são apenas demonstrações; não há cobrança real nem conteúdo de vídeo hospedado.


- catálogo público com busca, categorias e detalhes;
- cadastro e login com sessão persistida no servidor, cookie HttpOnly e proteção CSRF;
- perfis de aluno, professor e administrador;
- matrícula gratuita e matrícula paga pendente com confirmação demonstrativa;
- conteúdo protegido por matrícula ativa, conclusão idempotente e cálculo de progresso;
- avaliação corrigida no servidor, nota e limite de tentativas;
- criação de cursos e aulas, publicação de aulas/cursos e configuração de avaliação pelo professor;
- gestão administrativa dos perfis;
- outbox persistente com worker de notificações demonstrativas;
- health checks e Docker Compose com PostgreSQL.

## Executar com Docker Compose

1. Instale Docker Desktop com Compose.
2. Na raiz do repositório — a pasta que contém `compose.yaml` — execute `docker compose up --build`.
3. Abra `http://localhost:5173`. A API responde em `http://localhost:5000/api/v1/health/ready`.
4. Para apagar dados e recomeçar: `docker compose down -v`.

O Compose usa valores locais de exemplo. Altere-os antes de qualquer ambiente compartilhado.

## Publicar no Render

O repositório inclui `render.yaml` (Blueprint) e o Dockerfile da raiz. O container compila o frontend React/Vite para produção e o Flask serve os arquivos e a API no mesmo domínio. O Blueprint cria o serviço web e um PostgreSQL gerenciado.

1. Envie a pasta do trabalho para um repositório GitHub. Não envie `.env` nem credenciais.
2. No Render, crie um Blueprint e conecte esse repositório. O Render lê `render.yaml` e mostra os serviços antes de criá-los.
3. Quando solicitado, informe três senhas fortes diferentes para as contas de demonstração (aluna, professor e administrador). Guarde-as; o Render não as exibe novamente no assistente.
4. Confirme a criação e aguarde o deploy ficar `Live`. Abra a URL exibida pelo Render para o serviço criado.

O plano gratuito do PostgreSQL expira após 30 dias e os serviços web gratuitos podem dormir quando ficam sem tráfego. Para manter o banco e os dados por mais tempo, escolha um plano PostgreSQL pago antes da expiração. Consulte [limitações dos planos gratuitos do Render](https://render.com/docs/free).

O worker de notificações não faz parte do Blueprint gratuito: o Render não oferece instância gratuita para Background Worker. A plataforma principal funciona sem ele, mas notificações da outbox ficam pendentes. Para executar o worker no Render, crie um Background Worker pago a partir do mesmo repositório e Dockerfile, com comando `python worker.py` e as mesmas variáveis `DATABASE_URL` e `SEED_DEMO` do serviço web.

## Executar sem Docker

Requer Python 3.12+, Node 24+ e rede local disponível.

Terminal 1 (PowerShell):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python wsgi.py
```

Terminal 2:

```powershell
cd frontend
npm ci
npm run dev
```

A API usa SQLite local em `backend/learnplay/instance/learnplay.db`; Vite encaminha `/api` para `http://localhost:5000`.

## Contas demonstrativas

Os perfis de teste usam os e-mails abaixo:

- Aluno: `aluna@learnplay.local`
- Professor: `professor@learnplay.local`
- Administrador: `admin@learnplay.local`

No Render, use as senhas definidas nas variáveis `DEMO_STUDENT_PASSWORD`, `DEMO_INSTRUCTOR_PASSWORD` e `DEMO_ADMIN_PASSWORD`. Não coloque senhas reais neste repositório. Na execução local, as credenciais demonstrativas aparecem na tela de login em `localhost`.

## Verificação

Na pasta `backend`, execute `python -m pytest -q`. Na pasta `frontend`, execute `npm run build`.

## Limites do protótipo

O player é demonstrativo; não há mídia hospedada nem URL assinada S3. Pagamento é simulado na interface; não processa cartões. O worker registra notificações no log sem enviar e-mail. As metas de desempenho, disponibilidade e recuperação não foram medidas. O esquema inicial usa `create_all`; produção exige migrações versionadas, segredos protegidos e cookies seguros via HTTPS.

Arquitetura, documentação, ADRs, diagramas Mermaid, contrato OpenAPI, matriz de rastreabilidade e relatório de revisão permanecem nesta pasta.
