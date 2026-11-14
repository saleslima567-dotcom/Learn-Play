# AV2 — LearnPlay
## Passo 3 — Protótipo funcional

**Disciplina:** Arquitetura de Software<br>
**Tecnologias:** React 19, TypeScript, Vite 8, Python 3.12, Flask, SQLAlchemy e PostgreSQL<br>
**Estudante:** Paulo Kauã<br>
**Matrícula:** 01855908<br>
**Início:** 7 de novembro de 2026<br>
**Atualização documental:** 14 de novembro de 2026<br>
**Base:** requisitos e decisões dos documentos dos Passos 1 e 2 nesta pasta.

## 1. Objetivo

Entregar um protótipo web executável da LearnPlay que demonstre os fluxos centrais de uma plataforma de cursos online, mantenha as decisões arquiteturais anteriores e permita validar regras no frontend e na API.

## 2. Funcionalidades do protótipo

- catálogo público com pesquisa, filtros, detalhes, ementa e preço;
- registro de aluno e login/logout por sessão de servidor, cookie HttpOnly e token CSRF;
- autorização por perfis de aluno, professor e administrador;
- matrícula gratuita ativa e matrícula paga pendente; confirmação de pagamento demonstrativa na interface;
- aulas protegidas por matrícula ativa e conclusão idempotente com cálculo de progresso;
- avaliação com alternativas, correção no backend, nota e limite de tentativas;
- painel do professor para criar curso, acrescentar aula publicada, definir avaliação e publicar após existir aula publicada;
- painel administrativo com busca de contas, alteração de perfil, suspensão/reativação e exclusão definitiva de contas de aluno;
- favoritos persistidos por aluno e atalho de navegação para a lista pessoal;
- salvamento da última aula acessada por curso para retomar o estudo;
- páginas Sobre e Ajuda com explicação dos fluxos reais e demonstrativos;
- certificado HTML imprimível após matrícula ativa e conclusão de todas as aulas publicadas;
- outbox persistente com worker de demonstração e health checks.

## 3. Organização do código

```text
backend/
  learnplay/app.py       modelos, API, regras e composição da aplicação Flask
  init_db.py             inicialização única e serializada do esquema/dados
  wsgi.py                carregamento WSGI; execução local chama init_db.py
  worker.py              consumo da outbox demonstrativa
  tests/test_api.py      testes automatizados das rotas e regras
frontend/
  src/main.tsx           interface React e integração HTTP
  src/style.css          estilos responsivos
  package.json           dependências e scripts Vite
compose.yaml             PostgreSQL, API, worker e frontend local
contratos/openapi.yaml   contrato HTTP atualizado para as rotas implementadas
```

Essa organização é a estrutura efetivamente entregue. Em relação ao desenho modular dos Passos 1 e 2, a implementação concentra API, modelos e regras em `app.py` e a interface em `main.tsx`; a separação em pacotes de domínio, repositórios e componentes ainda não foi feita. Os nomes internos `learnplay` que aparecem no caminho do backend e no cookie de sessão são identificadores legados; o nome apresentado na interface é `descomplica cursos`.

## 4. Critérios de aceitação e evidências

| Critério | Evidência |
|---|---|
| Pessoa visitante consulta cursos publicados | `GET /api/v1/courses`; teste de catálogo. |
| Escritas rejeitam token CSRF ausente | `test_csrf_blocks_mutation_without_token`. |
| Aluno pode matricular-se em curso gratuito | `test_free_enrollment_and_lesson_progress_are_idempotent`. |
| Matrícula paga não libera conteúdo antes de aprovada | `test_paid_enrollment_requires_demo_confirmation`. |
| Conclusão repetida não duplica progresso | mesmo teste verifica percentual e registro único. |
| Aluno não cria curso e professor consegue | `test_instructor_can_create_course_and_student_cannot`. |
| Professor cria aula e avaliação e publica curso válido | `test_instructor_can_author_lessons_assessment_and_publish`. |
| Tentativa é corrigida no servidor e bloqueada após o limite | `test_assessment_attempts_are_limited_and_score_is_computed`. |
| Webhook exige HMAC e evento repetido não duplica efeitos | `test_payment_webhook_signature_and_duplicate_event_are_idempotent`. |
| Certificado só é emitido após conclusão integral | `GET /api/v1/me/certificates/{courseId}` verifica matrícula e progresso. |
| Administrador pode excluir apenas uma conta de aluno | `DELETE /api/v1/admin/users/{userId}` apaga também os registros associados; a interface pede confirmação. |
| A ajuda explica os limites das integrações | Páginas Sobre e Ajuda descrevem pagamentos e player demonstrativos. |

**Registro de validação anterior, em 7 de novembro:** oito testes automatizados passaram; o frontend foi compilado e a API local iniciou com SQLite. O Compose/PostgreSQL não foi iniciado naquela rodada. Esse resultado não cobre as mudanças adicionadas depois, incluindo favoritos, retomada de aula, renovação automática do token CSRF e exclusão de alunos; elas precisam de uma nova rodada de validação antes de serem tratadas como verificadas.

## 5. Execução

As instruções de execução com Docker Compose e sem Docker, incluindo contas demonstrativas, estão no `README.md`. Para a suíte, use `python -m pytest -q` dentro de `backend/tests`; para a compilação use `npm ci && npm run build` em `frontend`.

## 6. Integrações demonstrativas e limites

- **Pagamento:** a interface ativa a matrícula por confirmação de demonstração. O webhook de integração valida HMAC-SHA256 do corpo bruto, unicidade do evento, valor e moeda. Nenhum gateway está conectado e nenhum cartão é processado.
- **Mídia:** o player ilustra a tela da aula; mídia remota, armazenamento S3 e URL assinada não foram conectados.
- **E-mail:** o worker retira mensagens da outbox e registra entregas no log com estado `sent_demo`; não envia e-mail.
- **Persistência:** o Compose usa PostgreSQL. SQLite suporta execução local e testes. O protótipo cria tabelas via `create_all`; migrações versionadas devem ser adicionadas antes de uma implantação real.
- **Metas não verificadas:** disponibilidade mensal, desempenho para mil sessões, teste de carga, backup/restauração, rate limiting e operação HTTPS não foram medidos ou configurados como produção.

## 7. Rastreabilidade arquitetural

Os módulos e fluxos mantêm as responsabilidades dos documentos anteriores: identidade e acesso, catálogo, matrículas, conteúdo, progresso, avaliações, notificações e administração. A especificação OpenAPI e a matriz de rastreabilidade ficam nos arquivos existentes desta pasta; este documento registra o que foi implementado e o que permanece demonstrativo.

## 8. Histórico de implementação e publicação

- Na primeira publicação no Render, a criação simultânea das tabelas por mais de um worker causou conflito no PostgreSQL. Foi adicionada a inicialização serializada em `backend/init_db.py` antes da subida do Gunicorn; depois disso, o serviço foi publicado e a página abriu no Render.
- Durante o uso do login apareceu “Token CSRF ausente ou inválido” quando o token em memória ficou diferente da sessão do navegador. O cliente agora renova o token e repete a operação uma vez quando a resposta identifica esse erro.
- A publicação é feita pelo GitHub e Render a partir do repositório. O nome visual do site foi alterado, embora o endereço `onrender.com` possa continuar contendo o identificador antigo do serviço.

Esses registros descrevem problemas observados durante a implantação; não substituem uma nova execução dos testes automatizados nem uma conferência do banco PostgreSQL hospedado.
