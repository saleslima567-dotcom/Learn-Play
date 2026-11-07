# ADR-003 — API REST versionada para o cliente web

- **Status:** aceito.
- **Contexto:** o frontend React precisa consultar e alterar dados da plataforma; os contratos também organizam validação, autorização e integrações.
- **Decisão:** oferecer JSON por HTTPS sob /api/v1, com recursos e ações previsíveis. Erros seguem um formato uniforme. Mudanças incompatíveis entram em nova versão ou migração explícita.
- **Alternativas consideradas:** acesso direto do frontend ao banco; GraphQL; chamadas internas sem contrato estável.
- **Consequências positivas:** fronteira clara de segurança; documentação e contratos verificáveis; cliente pode evoluir separado da API; integração com sistemas externos fica explícita.
- **Consequências negativas:** requer paginação, compatibilidade e disciplina de versionamento; operações compostas podem exigir endpoints de caso de uso.
- **Regras de contrato:** autenticação por cookie seguro; CSRF em mutações; autorização no servidor; paginação por cursor; idempotência em matrícula e pagamentos; problemas HTTP padronizados.
