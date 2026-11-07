# AV2 — Arquitetura da Plataforma LearnPlay
## Passo 1 — Estruturar a arquitetura da aplicação

**Disciplina:** Arquitetura de Software  
**Equipe:** preencher com os nomes reais dos integrantes (máximo de 4 pessoas)  
**Data:** 7 de novembro de 2026  
**Etapa entregue:** Passo 1 — definição inicial da arquitetura

---

## 1. Resumo da solução

A LearnPlay é uma plataforma web de cursos online para alunos, professores e administradores. Alunos podem criar conta, consultar cursos, matricular-se, assistir às aulas, acompanhar o progresso e realizar avaliações. Professores organizam cursos, aulas e avaliações. Administradores gerenciam usuários, catálogo e operação da plataforma.

A solução será construída inicialmente como uma aplicação web com frontend React e uma API em Python/Flask. A API será um monólito modular organizado em camadas, com módulos de domínio separados. PostgreSQL armazenará dados transacionais; armazenamento de objetos compatível com S3 guardará vídeos e materiais. Um gateway de pagamento e um provedor de e-mail poderão ser integrados por contratos definidos.

A escolha favorece uma primeira versão compreensível e implantável por uma equipe pequena. A separação modular permite evoluir partes específicas caso o volume e os requisitos futuros justifiquem mudanças. A API HTTP e o worker da outbox podem executar como processos do mesmo artefato backend; o worker não cria um serviço de domínio independente. A arquitetura não assume microsserviços desde o início.

## 2. Escolha do negócio e contexto

**Negócio escolhido:** educação online.  
**Problema:** alunos precisam encontrar cursos, matricular-se e acompanhar aulas e avaliações em um único ambiente; professores precisam publicar conteúdo e observar o progresso dos alunos.  
**Usuários principais:** alunos, professores e administradores.  
**Premissa inicial de porte:** plataforma acadêmica de pequeno a médio porte, com meta de suportar até 1.000 sessões simultâneas na evolução da primeira versão. Essa meta orienta decisões iniciais e deverá ser confirmada por testes de carga antes de uma implantação de produção.

### 2.1 Objetivos de negócio

- Disponibilizar cursos e materiais em um catálogo pesquisável.
- Permitir matrícula e acesso controlado ao conteúdo.
- Registrar conclusões de aulas sem duplicar eventos de progresso.
- Oferecer avaliações e histórico de resultados.
- Permitir que professores mantenham cursos e acompanhem turmas.
- Dar aos administradores ferramentas para manter usuários e catálogo.

### 2.2 Escopo da primeira versão

**Incluído:** cadastro e autenticação; perfis de aluno, professor e administrador; catálogo e detalhes do curso; matrícula; lista e acesso a aulas; marcação de aula concluída; cálculo de progresso; avaliação simples; manutenção de cursos e aulas por perfil autorizado; integração prevista com armazenamento de mídia, e-mail e pagamento.

**Fora do escopo inicial:** aulas ao vivo; aplicativo móvel nativo; certificados oficiais; recomendações personalizadas; múltiplas instituições com isolamento de dados; pagamentos reais no protótipo acadêmico. O protótipo poderá simular a confirmação de pagamento. Essas exclusões reduzem o escopo sem alterar o desenho dos pontos de integração.

## 3. Requisitos

### 3.1 Requisitos funcionais

| ID | Requisito |
|---|---|
| RF01 | O sistema deve permitir cadastro, login e encerramento de sessão. |
| RF02 | O sistema deve aplicar permissões distintas a aluno, professor e administrador. |
| RF03 | O visitante deve consultar o catálogo e os detalhes públicos dos cursos. |
| RF04 | O aluno autenticado deve solicitar matrícula em um curso disponível. |
| RF05 | O sistema deve impedir matrícula duplicada do mesmo aluno no mesmo curso. |
| RF06 | O aluno matriculado deve consultar aulas e materiais do curso. |
| RF07 | O aluno deve marcar uma aula como concluída, e o sistema deve registrar essa conclusão uma única vez. |
| RF08 | O sistema deve calcular o progresso pela proporção de aulas concluídas sobre o total de aulas do curso. |
| RF09 | O aluno deve responder avaliações e consultar seus resultados. |
| RF10 | O professor deve criar e atualizar cursos, aulas e avaliações sob sua responsabilidade. |
| RF11 | O administrador deve gerenciar usuários, cursos e estados de publicação. |
| RF12 | O sistema deve notificar o usuário sobre eventos relevantes, como matrícula confirmada e conclusão de curso. |
| RF13 | O sistema deve permitir a integração com um provedor de pagamento para matrícula paga, mantendo a decisão de acesso vinculada à confirmação da transação. |

### 3.2 Requisitos não funcionais e critérios iniciais

| ID | Atributo | Critério inicial de aceitação |
|---|---|---|
| RNF01 | Segurança | Senhas armazenadas por hash seguro; autorização validada no servidor em cada operação protegida; tráfego externo por HTTPS; segredos somente em variáveis de ambiente. |
| RNF02 | Desempenho | Sob carga de até 1.000 sessões simultâneas na configuração dimensionada, 95% das consultas comuns do catálogo devem responder em até 2 segundos. Validar por teste de carga antes da produção. |
| RNF03 | Disponibilidade | Meta de 99,5% mensal após implantação de produção, com monitoramento e procedimento de restauração. |
| RNF04 | Integridade | Matrículas únicas por aluno e curso; conclusão de aula idempotente; transações consistentes para matrícula, pagamento e progresso. |
| RNF05 | Privacidade | Coletar somente dados necessários, limitar acesso por perfil e prever exportação e exclusão conforme política da plataforma e legislação aplicável. |
| RNF06 | Manutenibilidade | Separar apresentação, regras de aplicação, domínio e persistência; documentar interfaces e decisões; manter módulos com responsabilidade clara. |
| RNF07 | Escalabilidade | Permitir múltiplas instâncias da API sem estado de sessão local obrigatório; mídia fora do banco relacional; preparar índices e paginação no catálogo. |
| RNF08 | Recuperação | Fazer backup periódico do PostgreSQL e definir retenção e procedimento de restauração antes da produção. |
| RNF09 | Compatibilidade | Interface responsiva para navegadores modernos em desktop e celular. |

Os valores acima são metas arquiteturais para orientar o projeto; não representam resultados medidos. A capacidade real depende do ambiente e deverá ser validada posteriormente.

## 4. Tipo, estilo e decisões arquiteturais iniciais

### 4.1 Tipo e estilo escolhidos

- **Tipo de sistema:** aplicação web cliente-servidor, acessada por navegador.
- **Estilo do backend:** monólito modular organizado em camadas.
- **Integração:** API REST sobre HTTPS; chamadas a provedores externos encapsuladas em adaptadores.
- **Persistência:** banco relacional PostgreSQL e armazenamento de objetos para mídia.

### 4.2 Justificativa

A equipe precisa entregar uma solução inicial com fronteiras claras, documentação compreensível e custo operacional moderado. Um backend único simplifica implantação, transações e depuração. Os módulos de identidade, catálogo, matrícula, conteúdo, progresso, avaliação e notificações mantêm coesão e reduzem dependências cruzadas. Separar interface e API permite evolução independente do cliente web sem introduzir a operação distribuída de microsserviços.

A arquitetura poderá ser ampliada com cache, filas e serviços separados se métricas demonstrarem gargalos ou se equipes independentes precisarem de ciclos de implantação próprios. A adoção dessas peças será uma decisão futura baseada em requisitos e evidências.

### 4.3 Restrições tecnológicas

- Frontend: React e TypeScript.
- API: Python e Flask.
- Contrato externo: REST/JSON, versionado sob /api/v1.
- Dados transacionais: PostgreSQL.
- Mídia: serviço de objetos compatível com S3; o banco guarda metadados e referências, não os arquivos de vídeo.
- Implantação prevista para protótipo: frontend e API em serviços web; PostgreSQL gerenciado ou contêiner local. Configuração e credenciais por ambiente.
- Autenticação: sessão/token seguro com autorização por perfil; segredos nunca incluídos no repositório.

## 5. Visão geral da solução

1. O navegador carrega a aplicação React.
2. O React envia requisições REST à API Flask.
3. A camada de apresentação valida entrada e autenticação e chama serviços de aplicação.
4. Os serviços aplicam as regras de negócio e coordenam módulos.
5. Repositórios acessam PostgreSQL. Arquivos de mídia são enviados e lidos no armazenamento de objetos por URLs controladas.
6. Integrações de pagamento e e-mail ficam atrás de adaptadores. A indisponibilidade de um serviço externo não deve deixar uma matrícula em estado ambíguo; a API registra estado pendente ou falha tratável.

## 6. Estrutura lógica e responsabilidades

| Módulo | Responsabilidade | Dados principais |
|---|---|---|
| Identidade e acesso | Cadastro, autenticação, perfis e autorização. | Usuário, perfil, credencial. |
| Catálogo | Publicação, busca e consulta de cursos. | Curso, categoria, instrutor. |
| Matrículas | Solicitação, confirmação e estado da matrícula; regra contra duplicidade. | Matrícula, estado de pagamento. |
| Conteúdo | Organização de módulos, aulas e referências de mídia. | Módulo, aula, material. |
| Progresso | Registro idempotente de conclusão e cálculo percentual. | Conclusão, progresso. |
| Avaliações | Questões, tentativas, respostas e nota. | Avaliação, questão, tentativa. |
| Notificações | Preparação e envio de mensagens transacionais. | Preferência e registro de envio. |
| Administração | Operações administrativas e auditoria de mudanças relevantes. | Eventos administrativos. |

### 6.1 Camadas

- **Apresentação:** interface React e endpoints Flask; validação de formato, autenticação e respostas HTTP.
- **Aplicação:** casos de uso, orquestração e transações.
- **Domínio:** entidades e regras, incluindo matrícula única, acesso ao conteúdo e conclusão idempotente.
- **Persistência e integrações:** repositórios PostgreSQL e adaptadores para pagamento, e-mail e armazenamento de mídia.

Regra de dependência: apresentação chama aplicação; aplicação usa domínio e interfaces de repositório; adaptadores implementam interfaces. O domínio não depende de frameworks web nem de fornecedores externos.

## 7. Interfaces e fluxos principais

### 7.1 Endpoints iniciais

| Método e rota | Acesso | Finalidade |
|---|---|---|
| GET /api/v1/auth/csrf | Público | Iniciar sessão pré-autenticada e obter token CSRF. |
| POST /api/v1/auth/register | Público + CSRF | Criar conta de aluno. |
| POST /api/v1/auth/login | Público + CSRF | Autenticar usuário e renovar sessão. |
| GET /api/v1/courses | Público | Listar cursos publicados com paginação. |
| GET /api/v1/courses/{courseId} | Público | Consultar detalhes do curso. |
| POST /api/v1/courses/{courseId}/enrollments | Aluno | Solicitar matrícula ou iniciar pagamento. |
| GET /api/v1/me/enrollments | Aluno | Consultar cursos matriculados. |
| GET /api/v1/courses/{courseId}/lessons | Aluno matriculado | Consultar aulas liberadas. |
| PUT /api/v1/lessons/{lessonId}/completion | Aluno matriculado | Marcar conclusão de forma idempotente. |
| GET /api/v1/me/progress/{courseId} | Aluno | Consultar progresso. |
| POST /api/v1/courses/{courseId}/assessments/{assessmentId}/attempts | Aluno matriculado | Enviar tentativa de avaliação. |
| POST /api/v1/instructor/courses; PATCH /api/v1/instructor/courses/{courseId} | Professor | Criar ou atualizar curso sob sua responsabilidade. |
| PATCH /api/v1/admin/users/{userId} | Administrador | Alterar estado ou perfil de conta, com auditoria. |
| GET /api/v1/health/live; GET /api/v1/health/ready | Público | Verificar estado do processo e prontidão. |
| POST /api/v1/integrations/payments/webhook | Gateway de pagamento | Receber confirmação assinada e idempotente. |

Respostas de erro devem usar códigos HTTP coerentes e um corpo JSON estável, com identificador de erro e mensagem compreensível. Endpoints administrativos nunca confiam apenas em controles da interface.

### 7.2 Fluxo de matrícula

1. Aluno autenticado escolhe um curso publicado.
2. API confirma disponibilidade, elegibilidade e ausência de matrícula anterior.
3. Para curso gratuito, cria matrícula ativa em transação. Para curso pago, cria estado pendente e inicia cobrança no adaptador de pagamento.
4. O provedor informa o resultado por retorno seguro. A API valida a notificação antes de ativar o acesso.
5. A API registra o resultado e solicita notificação por e-mail. Uma repetição da mesma solicitação não cria matrículas duplicadas.

### 7.3 Fluxo de conclusão de aula

1. Aluno matriculado solicita a conclusão de uma aula que pertence ao curso.
2. API verifica matrícula e disponibilidade da aula.
3. Serviço registra a conclusão com chave única para aluno e aula; repetir a chamada não duplica o registro.
4. Progresso é recalculado a partir das aulas concluídas e do total publicado.
5. API devolve o percentual atualizado. Notificação de conclusão do curso é disparada uma única vez quando aplicável.

## 8. Visões arquiteturais

A arquitetura é descrita por visões complementares, conforme o modelo 4+1 apresentado na Aula 04. O +1 reúne cenários que ajudam a validar as outras visões.

- **Visão lógica:** módulos, camadas, responsabilidades e relações — ver diagramas de contêineres e componentes.
- **Visão de desenvolvimento:** organização dos pacotes e dependências — ver estrutura de projeto.
- **Visão de processos:** comunicação durante matrícula e conclusão de aula — ver sequências.
- **Visão física:** distribuição prevista em ambiente de execução — ver implantação.
- **Cenários:** matrícula e atualização do progresso demonstram a interação entre as visões.

## 9. Diagramas C4

Os diagramas editáveis acompanham este documento na pasta diagramas. C1 mostra pessoas e sistemas externos; C2 mostra unidades implantáveis e armazenamento; C3 detalha os componentes internos da API. A seleção de nível segue a finalidade de comunicação e pode ser refinada na etapa de documentação.

## 10. Riscos arquiteturais iniciais e respostas

| Risco | Resposta arquitetural |
|---|---|
| Matrícula liberada sem confirmação de pagamento | Estados explícitos, verificação de assinatura/retorno e idempotência. |
| Duplicação de progresso por repetição de requisição | Restrição única no banco e operação idempotente. |
| Exposição de vídeos ou materiais privados | URLs temporárias e autorização antes da emissão. |
| Crescimento do catálogo causa consultas lentas | Paginação, índices e monitoramento; cache somente após medição. |
| Acoplamento entre módulos | APIs internas claras e regras de dependência entre camadas. |
| Dependência indisponível de e-mail ou pagamento | Adaptadores, timeout, registro de estado e retentativa controlada. |
| Meta de 1.000 sessões não atendida | Teste de carga e ajuste de instâncias/consultas antes da produção. |

## 11. Decisões que ficam para os próximos passos

O Passo 1 fixa o negócio, escopo, requisitos, estilo e estrutura inicial. O Passo 2 deverá registrar documentação detalhada, diagramas finais, interfaces, decisões (ADRs), rastreabilidade e tecnologias selecionadas. O Passo 3 deverá escolher funcionalidades do protótipo, especificar critérios verificáveis, implementar e validar a aplicação com apoio de IA. Não declarar metas de desempenho ou disponibilidade como comprovadas sem medi-las.

## 12. Arquivos desta etapa

- Este documento: arquitetura, requisitos, estrutura, interfaces, fluxos, restrições e riscos do Passo 1.
- Pasta diagramas: fontes Mermaid editáveis para contexto C1, contêineres C2, componentes C3, visão lógica, estrutura de desenvolvimento, sequência de matrícula, sequência de progresso e visão física.

---

**Base de elaboração:** conteúdo das Aulas 04, 05 e 06 de Arquitetura de Software, aplicado ao exemplo de plataforma de cursos online. Esta entrega cobre apenas o Passo 1 da AV2.



