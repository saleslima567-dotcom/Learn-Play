# AV2 — Arquitetura da Plataforma LearnPlay
## Passo 2 — Documentar toda a estrutura arquitetural

**Disciplina:** Arquitetura de Software  
**Equipe:** preencher com os nomes reais dos integrantes (máximo de 4 pessoas)  
**Data:** 7 de novembro de 2026  
**Status:** documentação arquitetural preliminar para orientar a implementação do protótipo  
**Documento relacionado:** 01_Passo_1_Arquitetura.md

---

## 1. Objetivo, público e convenções

Este documento consolida a arquitetura da LearnPlay definida no Passo 1 e especifica as fronteiras entre componentes, contratos, fluxos, dados, implantação e decisões técnicas. Destina-se à equipe que implementará o protótipo e às pessoas que revisarão sua aderência aos requisitos.

Os diagramas em diagramas/ são fontes Mermaid editáveis. As rotas e os campos neste documento constituem a proposta inicial do contrato REST. A especificação formal em contratos/openapi.yaml é a fonte de verdade para endpoints documentados. A matriz de rastreabilidade está em matriz_rastreabilidade.csv. Decisões importantes estão registradas separadamente em adrs/.

### 1.1 Termos

- **Aluno:** usuário que se matricula, acessa aulas e acompanha seu progresso.
- **Professor:** usuário que mantém cursos e conteúdos sob sua responsabilidade.
- **Administrador:** usuário autorizado a gerenciar contas, catálogo e operações.
- **Matrícula:** relação única entre aluno e curso, com estado próprio.
- **Conclusão:** registro idempotente de uma aula concluída por um aluno.
- **Adaptador:** componente que isola uma integração externa atrás de uma interface interna.
- **Monólito modular:** uma aplicação backend implantável como unidade única, composta por módulos com responsabilidades e dependências explícitas.

## 2. Contexto e limites

A LearnPlay conecta alunos, professores e administradores a serviços de pagamento, e-mail e armazenamento de mídia. A plataforma controla contas, catálogo, matrículas, autorização de conteúdo e progresso. O gateway de pagamento processa dados financeiros; a plataforma guarda apenas identificadores e estados da transação. Vídeos e arquivos ficam em armazenamento de objetos e são acessados por referências autorizadas.

### 2.1 Limites de responsabilidade

**Dentro da plataforma:** autenticação e autorização; catálogo; regras de matrícula; associação entre curso, aulas e avaliação; registro de progresso; resultados; operação administrativa; geração de notificações; integração com serviços externos.

**Fora da plataforma:** processamento financeiro do cartão; hospedagem física dos vídeos; entrega de e-mail; autenticação do provedor externo de pagamento; conectividade de internet do aluno. A plataforma valida callbacks e contratos, mas não substitui esses provedores.

### 2.2 Atores e objetivos

| Ator | Objetivo | Ações autorizadas principais |
|---|---|---|
| Visitante | Descobrir cursos e criar conta. | Consultar catálogo e detalhes públicos; registrar-se; autenticar-se. |
| Aluno | Aprender e acompanhar resultados. | Matricular-se; acessar conteúdo liberado; registrar conclusão; realizar avaliação; consultar progresso. |
| Professor | Produzir e acompanhar cursos. | Manter cursos próprios; organizar módulos, aulas e avaliações; consultar resultados agregados autorizados. |
| Administrador | Operar a plataforma. | Gerenciar usuários e estados de publicação; revisar eventos operacionais; não visualizar segredos de autenticação. |
| Gateway de pagamento | Confirmar cobranças. | Receber solicitação e enviar evento assinado de estado da cobrança. |
| Armazenamento de mídia | Guardar conteúdo. | Receber e servir objetos por autorização temporária. |
| Provedor de e-mail | Entregar mensagens. | Receber solicitações de envio e devolver identificador/estado. |

## 3. Princípios e visão de implantação

1. **Regras no backend:** a interface não decide permissões, preços, estados de matrícula nem progresso.
2. **Dependências apontam para dentro:** módulos de domínio não importam Flask, SQLAlchemy, SDKs de pagamento ou SDK de armazenamento.
3. **Contratos explícitos:** interfaces HTTP e integrações externas têm esquema, autenticação, timeout e falhas documentados.
4. **Operações repetíveis:** matrícula, webhook de pagamento e conclusão de aula usam chaves de idempotência ou restrições únicas.
5. **Dados mínimos:** o banco guarda apenas os dados necessários para operar e demonstrar o protótipo.
6. **Segredos fora do código:** credenciais entram por ambiente de execução; logs não registram senhas, tokens, dados de cartão ou URLs assinadas.
7. **Evolução guiada por evidências:** separar um módulo como serviço só depois de haver necessidade de escala, autonomia de equipe ou isolamento operacional comprovada.

O diagrama de implantação é uma topologia lógica. A região, capacidade, plano e recursos do provedor serão definidos antes da publicação; metas de desempenho e disponibilidade continuam pendentes de validação.

## 4. Visões arquiteturais

### 4.1 Visão lógica

O backend é uma aplicação Flask com fronteiras por módulo de domínio e camadas de apresentação, aplicação, domínio e adaptadores. O frontend React consome somente a API pública versionada. O diagrama diagramas/visao_logica.mmd resume as dependências; diagramas/c3_componentes_api.mmd detalha os componentes da API.

#### Módulos e contratos internos

| Módulo | Comandos/casos de uso | Consultas | Dependências permitidas |
|---|---|---|---|
| Identidade e acesso | Registrar usuário, autenticar, encerrar sessão, autorizar ação. | Perfil e sessão atual. | Repositório de identidade, hash de senha, sessão. |
| Catálogo | Criar, atualizar, publicar e arquivar curso. | Listar e consultar cursos publicados. | Repositórios de curso, identidade para autoria. |
| Matrículas | Solicitar matrícula, confirmar ou recusar pagamento, cancelar conforme regra. | Estado e histórico da matrícula. | Catálogo, identidade, pagamento, repositório de matrícula, outbox. |
| Conteúdo | Manter módulos, aulas e referência de material. | Listar conteúdo conforme matrícula e estado de publicação. | Catálogo, matrícula, armazenamento de mídia. |
| Progresso | Marcar aula concluída e recalcular percentual. | Consultar conclusões e percentual. | Conteúdo, matrícula, repositório de progresso. |
| Avaliações | Publicar avaliação, receber tentativa, calcular resultado. | Consultar avaliações liberadas e resultado próprio. | Conteúdo, matrícula, progresso, repositório de avaliação. |
| Notificações | Registrar e enviar mensagem transacional. | Consultar estado técnico de envio. | Adaptador de e-mail e outbox. |
| Administração | Alterar estado de usuários/cursos e consultar eventos autorizados. | Consultar indicadores administrativos mínimos. | Identidade, catálogo, auditoria. |

Os módulos compartilham as entidades fundamentais por identificadores e interfaces. Não devem acessar diretamente tabelas de outro módulo para implementar regra de negócio. Quando um caso de uso precisar coordenar módulos, um serviço de aplicação orquestra as operações dentro de uma transação ou registra um evento persistente para processamento posterior. A outbox é escrita na mesma transação da mudança de negócio; um worker separado, construído a partir do mesmo artefato do backend, busca eventos pendentes, entrega notificações e marca o resultado. O worker não é um microsserviço de domínio independente.

### 4.2 Visão de desenvolvimento

Estrutura planejada para repositório único com diretórios separados para frontend, backend, infraestrutura e documentação:

```text
learnplay/
  frontend/
    src/pages/                 telas e rotas da interface
    src/components/            componentes reutilizáveis
    src/api/                   cliente HTTP, tipos e tratamento de erros
  backend/
    app/__init__.py            composição da aplicação Flask
    worker.py                  dispatcher da outbox de notificações
    app/api/v1/                blueprints, esquemas e autenticação HTTP
    app/modules/identity/      domínio e casos de uso de identidade
    app/modules/catalog/       domínio e casos de uso do catálogo
    app/modules/enrollments/   domínio e casos de uso de matrícula
    app/modules/content/       cursos, módulos, aulas e mídia
    app/modules/progress/      conclusão e cálculo de progresso
    app/modules/assessments/   avaliações e tentativas
    app/modules/notifications/ outbox e serviço de notificações
    app/infrastructure/db/     SQLAlchemy, mapeamentos e migrações
    app/infrastructure/        adaptadores externos e configuração
    migrations/                migrações do PostgreSQL
  infra/
    compose.yaml               ambiente local
    deployment/                configuração por ambiente
  docs/
    adr/                       decisões arquiteturais
    diagrams/                  fontes dos diagramas
    specs/                     especificações e critérios de aceitação
```

A estrutura de implementação poderá ser adaptada se o protótipo exigir menos arquivos, mantendo as mesmas fronteiras. Regras de domínio ficam testáveis sem inicializar servidor web; rotas convertem HTTP em comandos/consultas e formatam respostas.

### 4.3 Visão de processos

#### Matrícula em curso pago

1. O aluno autenticado escolhe um curso publicado.
2. A API valida perfil, publicação, pré-requisitos e ausência de matrícula ativa ou pendente conflitante.
3. Em uma transação, registra matrícula pendente e tentativa de pagamento com uma referência interna única.
4. O adaptador solicita cobrança ao provedor usando uma chave de idempotência. A API devolve ao frontend somente a URL ou token de checkout aprovado para exposição.
5. O provedor envia webhook assinado. A API verifica assinatura, timestamp, merchant, referência da tentativa, valor, moeda, evento e identificador já processado.
6. Se aprovado, a matrícula passa de pendente para ativa. Se recusado ou expirado, permanece sem acesso e recebe o estado correspondente.
7. A outbox registra a notificação de confirmação. Um trabalhador de notificações envia e-mail e marca o evento processado.
8. Repetições de webhook não repetem a ativação nem o envio lógico da confirmação.

Estados definidos: PENDING_PAYMENT → ACTIVE quando aprovado; PENDING_PAYMENT → PAYMENT_FAILED quando recusado; PENDING_PAYMENT → EXPIRED por expiração; ACTIVE → CANCELLED segundo política da plataforma. A transição não é inferida a partir de resposta do navegador.

#### Conclusão de aula

1. O aluno autenticado solicita conclusão de uma aula.
2. A API verifica que a aula existe, pertence ao curso e está disponível para aquele aluno matriculado.
3. A camada de aplicação insere a conclusão com unicidade por aluno e aula. Repetição retorna sucesso sem duplicar dado.
4. O serviço consulta o total de aulas publicadas e as conclusões válidas, calcula percentual inteiro ou decimal consistente e persiste o resultado somente se houver cache de progresso. Se o curso não tiver aulas publicadas, o progresso é 0%, evitando divisão por zero.
5. Se o curso foi concluído pela primeira vez, registra evento de conclusão e notificação na outbox.
6. A resposta apresenta conclusão e progresso atualizado.

#### Falhas e compensações

| Situação | Resposta | Persistência/recuperação |
|---|---|---|
| Curso não existe ou não está publicado | 404 ou 409 conforme visibilidade definida. | Não criar matrícula. Registrar evento sem dados sensíveis. |
| Curso sem conteúdo mínimo tenta ser publicado | 422 com campos faltantes. | Exigir título, descrição, ao menos uma seção e uma aula publicada. |
| Já matriculado | 200 com matrícula existente ou 409 conforme contrato. | Restrição única garante integridade. |
| Gateway indisponível antes de criar cobrança | 503 temporário. | Matrícula fica pendente identificada; permitir nova tentativa sem duplicar. |
| Webhook inválido/repetido | 401 para assinatura inválida; 200 sem novo efeito para evento repetido validado. | Evento válido registrado com ID único; divergência de valor/moeda fica em quarentena para revisão. |
| Armazenamento indisponível | Erro controlado ao disponibilizar mídia. | Não perder metadados; retentar emissão de URL conforme contrato. |
| E-mail indisponível | Matrícula não é desfeita. | Outbox mantém mensagem para retentativa com limite e backoff. |
| Duas conclusões simultâneas | Ambas podem receber confirmação lógica. | Constraint única mantém apenas um registro. |

### 4.4 Visão física

Ambiente de produção previsto:

- Frontend React hospedado como conteúdo estático com HTTPS.
- API Flask executada em serviço web atrás de terminação TLS e balanceamento.
- Uma ou mais instâncias de API sem estado local obrigatório; a escala horizontal não pode depender de arquivos/sessões locais.
- PostgreSQL gerenciado em rede privada, com alta disponibilidade configurada para a meta do serviço, backup automatizado, migrações versionadas, usuário de banco com privilégios mínimos e plano de restauração.
- Worker de notificações executado como processo do mesmo artefato backend; consome a outbox persistida no PostgreSQL e envia mensagens após commit. Pode escalar separadamente sem introduzir um serviço de domínio novo.
- Armazenamento S3 privado para vídeos e materiais, com URLs temporárias geradas após autorização da API.
- Gateway e provedor de e-mail acessados por saídas HTTPS com timeout e política de retentativa.
- Logs estruturados, métricas de saúde e alertas para erros da API, conexões ao banco e falhas das integrações.

Ambiente local de desenvolvimento: serviços configurados por variáveis de ambiente e banco PostgreSQL em contêiner. A configuração local não deve conter credenciais de produção.

### 4.5 Cenários +1

- **S1 — Matrícula:** demonstra identidade, catálogo, matrícula, pagamento e notificação.
- **S2 — Concluir aula:** demonstra autorização, conteúdo, progresso e persistência idempotente.
- **S3 — Professor publica curso:** demonstra permissão por propriedade, catálogo e disponibilidade do curso.

### 4.6 Índice dos diagramas

- Contexto C1: diagramas/c1_contexto.mmd.
- Contêineres C2: diagramas/c2_conteineres.mmd.
- Componentes C3 da API: diagramas/c3_componentes_api.mmd.
- Visão lógica: diagramas/visao_logica.mmd.
- Visão de desenvolvimento: diagramas/visao_desenvolvimento.mmd.
- Visão física: diagramas/visao_fisica.mmd.
- Modelo de domínio: diagramas/modelo_dominio.mmd.
- Fluxo de matrícula: diagramas/fluxo_matricula.mmd.
- Fluxo de progresso: diagramas/fluxo_progresso.mmd.
- Sequência detalhada do pagamento: diagramas/sequencia_pagamento.mmd.

As fontes são Mermaid editável e seguem a mesma arquitetura descrita neste documento. C1 apresenta contexto; C2, processos e armazenamento; C3, componentes internos; as demais visões detalham comportamento, dados e implantação.
## 5. Modelo de domínio e persistência

O diagrama diagramas/modelo_dominio.mmd mostra as entidades e relações principais. PostgreSQL é a fonte de verdade dos dados transacionais.

| Entidade | Campos essenciais | Restrições relevantes |
|---|---|---|
| User | id, email normalizado, nome, password_hash, role, status, created_at | email único; hash apenas; role validado por enumeração. |
| Session | id/hash, user_id opcional, csrf_token_hash, expires_at, revoked_at, created_at | sessão pré-autenticada pode não ter user_id; sessão revogável; tokens brutos não persistidos. |
| Course | id, instructor_id, title, description, status, price, currency, published_at | preço não negativo; estado explícito; autoria vinculada a professor. |
| Section | id, course_id, title, position | posição única por curso. |
| Lesson | id, section_id, title, position, media_key, duration_seconds, status | mídia privada; posição única por seção. |
| Enrollment | id, student_id, course_id, status, created_at, activated_at | unicidade aluno+curso; transições autorizadas. |
| PaymentAttempt | id, enrollment_id, provider, provider_reference, status, amount, currency | valor e moeda congelados na tentativa; referência única no provedor. |
| PaymentEvent | id, provider_event_id, payment_attempt_id, received_at, payload_digest, status, review_code | event_id único; status RECEIVED/PROCESSED/REVIEW; guardar digest e motivo codificado, sem credenciais ou payload sensível. |
| LessonCompletion | id, student_id, lesson_id, completed_at | UNIQUE(student_id, lesson_id). |
| Assessment | id, course_id, title, passing_score, max_attempts, status | nota mínima e limite configurável; padrão inicial de três tentativas. |
| AssessmentQuestion | id, assessment_id, prompt, question_type, position, points | questão pertence a uma avaliação; posição única por avaliação. |
| AssessmentAttempt | id, assessment_id, student_id, attempt_number, score, submitted_at | tentativa vinculada a aluno matriculado; número único por aluno e avaliação; máximo configurado na avaliação. |
| AssessmentAnswer | id, assessment_id, attempt_id, question_id, answer_payload, is_correct | resposta pertence à tentativa e questão da mesma avaliação; UNIQUE(attempt_id, question_id) e FKs compostas garantem consistência; gabarito privado. |
| NotificationOutbox | id, event_key, recipient_id, type, payload_minimal, status, attempts | event_key único; retentativa sem duplicar efeito. |
| AuditEvent | id, actor_id, action, object_type, object_id, occurred_at | sem senha, token ou conteúdo sensível. |

Integridade e exclusões: chaves estrangeiras preservam relações; remoção de conta/cursos deve seguir política de retenção, evitando cascatas que apaguem registros financeiros exigidos. Valores monetários usam decimal e moeda ISO, nunca ponto flutuante binário. Datas armazenadas em UTC. A nota final da avaliação será a melhor tentativa válida; bloquear novos envios quando atingir max_attempts. Gabarito e marcação de correção permanecem privados no backend e não são devolvidos antes da política de liberação definida pelo professor.

## 6. Interfaces e integrações

### 6.1 Convenções HTTP

- Prefixo versionado: /api/v1.
- Representação: application/json; UTF-8.
- Identificadores: UUID opaco na API.
- Paginação: limit e cursor; resposta traz items e next_cursor.
- Erros: application/problem+json com type, title, status, detail e request_id.
- Autenticação: cookie de sessão HttpOnly, Secure e SameSite=Lax; obter token pré-autenticado em GET /api/v1/auth/csrf e enviá-lo no header X-CSRF-Token em registro, login, logout e demais requisições mutáveis. Login rotaciona a sessão e devolve novo token CSRF. CORS restrito à origem exata.
- Autorização: verificada em cada endpoint e serviço. O frontend não é fronteira de segurança.
- Limites: validação de tamanho/tipo no upload, rate limit em login e endpoints públicos, timeout nas dependências externas.
- Idempotência: X-Idempotency-Key nas solicitações de matrícula/pagamento; UNIQUE no banco para matrícula e conclusão.

### 6.2 Contratos principais

#### Token CSRF — GET /api/v1/auth/csrf

Cria ou reutiliza uma sessão pré-autenticada e devolve csrf_token. O cliente mantém o token em memória e o envia no header X-CSRF-Token em toda operação mutável, inclusive registro e login.

#### Registrar conta — POST /api/v1/auth/register

Request: name, email, password. Email normalizado; senha nunca devolvida. 201 retorna user id, nome, email e role aluno. 409 para e-mail já cadastrado; 422 para campos inválidos.

#### Listar cursos — GET /api/v1/courses?limit=20&cursor=...

Resposta: items com id, title, short_description, instructor, price, currency, thumbnail_url e lesson_count; next_cursor. Somente cursos publicados são visíveis publicamente.

#### Solicitar matrícula — POST /api/v1/courses/{courseId}/enrollments

Header X-Idempotency-Key obrigatório em toda solicitação de matrícula. Request pode conter coupon_code. 201 para matrícula gratuita/ativa; 202 para checkout pendente, com enrollment_id, status e checkout_url originada do provedor autorizado. 401 sem sessão; 403 perfil inadequado; 404 curso não visível; 409 matrícula existente ou curso fechado; 503 falha temporária de integração.

#### Concluir aula — PUT /api/v1/lessons/{lessonId}/completion

Sem corpo adicional obrigatório. Valida matrícula e disponibilidade. Resposta 200 traz lesson_id, completed_at e progress_percent. A mesma chamada repetida mantém um único registro e devolve progresso atual.

#### Webhook de pagamento — POST /api/v1/integrations/payments/webhook

Autenticação por assinatura do provedor, segredo configurado fora do repositório. Validar assinatura, timestamp, replay, merchant, provider_event_id, referência da tentativa, valor e moeda contra o registro local; registrar provider_event_id único; responder após persistência durável; processar mudança de estado em transação. Evento duplicado validado não reaplica efeitos. Divergência de referência, valor ou moeda vai para quarentena e não ativa matrícula.

#### Health checks — GET /api/v1/health/live e GET /api/v1/health/ready

Live confirma que o processo responde; ready verifica somente dependências essenciais e devolve 503 sem expor credenciais ou topologia interna.

#### Criar curso — POST /api/v1/instructor/courses

Exige sessão, CSRF e perfil professor. Cria curso em rascunho ligado ao professor autenticado. Publicação ocorre após validar título, descrição, seção e aula.

#### Administrar usuário — PATCH /api/v1/admin/users/{userId}

Exige perfil administrador e CSRF. Pode alterar perfil ou estado; a operação é auditada. Negar alteração de perfil que permita autoelevação pelo mesmo ator.

#### Atualizar curso — PATCH /api/v1/instructor/courses/{courseId}

Exige perfil professor e propriedade do curso ou permissão administrativa. Campos alteráveis explicitamente enumerados. Estado publicado só muda após validações mínimas de título, descrição e conteúdo.

A especificação OpenAPI complementar encontra-se em contratos/openapi.yaml e inclui health checks, criação e atualização de cursos, administração de usuários, matrícula, conteúdo, progresso, avaliação e webhook de pagamento.

### 6.3 Integração de mídia

O banco guarda object_key, tipo, tamanho, duração e estado do arquivo. Upload inicia uma sessão controlada, valida autorização e limite, e usa URL pré-assinada de curta duração. Leitura exige matrícula ativa, depois a API gera URL temporária de leitura. Chaves não podem ser adivinhadas como mecanismo único de autorização. Não enviar vídeo binário por meio da API Flask.

### 6.4 Integração de e-mail

Eventos mínimos: conta criada, matrícula confirmada, redefinição de senha e conclusão de curso. Mensagens são solicitadas por outbox após confirmação transacional. Templates não expõem dados de outros usuários. Falha de e-mail não desfaz matrícula; retentativas são limitadas e observáveis.

## 7. Segurança e privacidade

- Senhas com Argon2id ou mecanismo de hash equivalente com parâmetros atuais, sal único e política de atualização.
- Sessões com rotação após autenticação, expiração, revogação em logout e alteração de senha.
- Cookies de sessão HttpOnly, Secure e SameSite=Lax; token CSRF para requisições mutáveis. Frontend e API devem usar a mesma origem ou subdomínios do mesmo site registrável, com CORS restrito à origem exata. Se forem hospedados em sites distintos, rever SameSite/CORS/CSRF antes da publicação.
- Autorização no servidor por perfil e propriedade do recurso; negar por padrão.
- Proteção contra enumeração de contas por mensagens de login uniformes e limites de tentativa.
- Entrada validada por esquema; consultas parametrizadas via ORM; saída HTML escapada.
- Segredos, chaves, tokens e URLs pré-assinadas nunca gravados em logs.
- Uploads com limite, tipos aceitos, nome de objeto aleatório e validação de conteúdo.
- Eventos administrativos auditáveis com dados mínimos.
- Retenção, exportação e exclusão de dados documentadas antes de produção; alinhar operação à LGPD.

## 8. Qualidade, observabilidade e recuperação

### 8.1 Cenários de qualidade

| Atributo | Estímulo | Resposta desejada | Medição/validação futura |
|---|---|---|---|
| Desempenho | 1.000 sessões concorrentes consultam catálogo. | p95 até 2 s na configuração de referência. | Teste de carga com dataset representativo. |
| Disponibilidade | Instância de API falha. | Tráfego direcionado a instância saudável; sem perda de dados confirmados. | Simulação de falha e métricas do serviço. |
| Segurança | Usuário tenta acessar curso sem matrícula. | 403/404 conforme política; nenhum link de mídia liberado. | Teste de autorização por perfil e propriedade. |
| Integridade | Cliente repete conclusão de aula. | Uma conclusão persistida e progresso consistente. | Requisição repetida e consulta ao banco. |
| Recuperação | Banco indisponível e restaurado. | Aplicação informa indisponibilidade; dados recuperados conforme RPO/RTO definidos. | Exercício de restauração. |
| Manutenibilidade | Nova regra de avaliação é adicionada. | Alteração concentrada no módulo de avaliação sem depender de rotas de outro módulo. | Revisão de dependências e revisão de código. |

RPO e RTO precisam ser definidos antes da produção, com o responsável pelo negócio. Logs e métricas terão request_id, nome de operação, duração e resultado, sem dados pessoais desnecessários. Health checks distinguem processo vivo de dependências prontas.

### 8.2 Estratégia de validação

- Testes unitários para regras de domínio e transições de estado.
- Testes de integração com PostgreSQL para constraints, transações e migrações.
- Testes de contrato para API e adaptadores externos.
- Testes de ponta a ponta para registro, matrícula, acesso, progresso e avaliação.
- Testes de segurança para autenticação, autorização, CSRF, rate limit e uploads.
- Teste de carga para a meta do RNF02, antes de tratar a capacidade como atingida.
- Verificação manual em navegadores desktop e móveis.

Esta seção define o plano de validação; não afirma que os testes foram executados ou aprovados nesta etapa.

## 9. Decisões arquiteturais (ADRs)

As decisões aceitas e suas consequências estão em adrs/:

- ADR-001 — Monólito modular em camadas.
- ADR-002 — PostgreSQL para dados transacionais e S3 para mídia.
- ADR-003 — API REST versionada e React como cliente web.
- ADR-004 — Sessão protegida por cookie e autorização no servidor.

As decisões deverão ser revistas se requisitos ou evidências de operação mudarem. Uma alteração não apaga a decisão antiga: cria-se nova ADR que a substitui, mantendo contexto e consequências.

## 10. Rastreabilidade

A matriz em matriz_rastreabilidade.csv liga RFs e RNFs aos componentes responsáveis, às evidências arquiteturais e às decisões. Requisito sem componente ou cenário associado é lacuna. Componente sem requisito/objetivo associado deve ser justificado ou removido.

Resumo de rastreabilidade:

| Requisito | Componentes principais | Evidência |
|---|---|---|
| RF01–RF02 | Identidade e acesso; API | C3, ADR-004, contrato de autenticação. |
| RF03, RF10–RF11 | Catálogo; administração | C3, modelo de domínio, endpoints de cursos. |
| RF04–RF05, RF13 | Matrículas; adaptador de pagamento; outbox | Sequência de matrícula, constraints, ADR-002/003. |
| RF06–RF08 | Conteúdo; progresso | Sequência de conclusão, modelo de domínio. |
| RF09 | Avaliações | C3, modelo de domínio, cenário S2. |
| RF12 | Notificações | Outbox, contrato do provedor de e-mail. |
| RNF01, RNF05 | Identidade, API e adaptadores | Seção de segurança; ADR-004. |
| RNF02–RNF04, RNF07 | API, banco e armazenamento | Cenários de qualidade; ADR-001/002. |
| RNF06 | Todos os módulos | Visão lógica e de desenvolvimento. |
| RNF08–RNF09 | Banco, frontend e operação | Visão física e critérios de validação. |

## 11. Implantação e configuração

### 11.1 Ambientes

- **Local:** frontend e API em desenvolvimento; PostgreSQL isolado para integração; adaptadores externos simulados ou sandbox.
- **Homologação:** dados fictícios, credenciais próprias, integração sandbox, migrações aplicadas antes da troca de tráfego.
- **Produção:** serviços gerenciados, rede privada para banco, backup, HTTPS, monitoramento, contas com privilégio mínimo e rotação de segredos.

### 11.2 Configuração por ambiente

Variáveis previstas: APP_ENV, SECRET_KEY, DATABASE_URL, FRONTEND_ORIGIN, SESSION_COOKIE_SECURE, CSRF_SECRET, S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY, PAYMENT_BASE_URL, PAYMENT_WEBHOOK_SECRET, EMAIL_PROVIDER_KEY, LOG_LEVEL. Os valores reais devem ser inseridos no gerenciador de segredos do ambiente, nunca neste documento ou no controle de versão.

### 11.3 Migrações e lançamento

1. Construir artefatos versionados e executar validação automatizada.
2. Aplicar migrações compatíveis com a versão atual.
3. Implantar primeiro em homologação e validar fluxos principais.
4. Promover para produção com health checks e rollback documentado.
5. Observar erros, latência, conexões e eventos externos após cada lançamento.

## 12. Checklist de completude documental

- Contexto, objetivo, escopo e atores: documentados.
- Requisitos funcionais e não funcionais: documentados no Passo 1 e rastreados aqui.
- Estilo e justificativa: documentados e separados em ADRs.
- Componentes e responsabilidades: documentados.
- Visões lógica, desenvolvimento, processos, física e cenários: documentadas e diagramadas.
- Interfaces, integrações, fluxos e falhas: documentados; OpenAPI complementar incluída.
- Modelo de dados e restrições de integridade: documentados.
- Segurança, qualidade, observabilidade e validação: documentadas.
- Rastreabilidade de requisitos à arquitetura: incluída.
- Identificação da equipe: pendente de preenchimento com nomes reais.
- Evidência de execução e testes do protótipo: pertence ao Passo 3.

---

**Esta entrega cobre o Passo 2 da AV2.** A implementação do protótipo e a validação prática permanecem como trabalho do Passo 3.













