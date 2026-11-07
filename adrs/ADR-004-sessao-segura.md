# ADR-004 — Sessão protegida por cookie e autorização no servidor

- **Status:** aceito para a aplicação web.
- **Contexto:** a interface React usa a API da descomplica cursos. A autenticação precisa impedir exposição de credenciais, apoiar encerramento de sessão e aplicar perfis e propriedade de recurso.
- **Decisão:** manter sessão revogável identificada por cookie HttpOnly, Secure e SameSite; armazenar o estado da sessão no servidor; criar sessão pré-autenticada e token CSRF; exigir CSRF em registro/login e operações mutáveis; rotacionar sessão e token após login; persistir somente hashes de sessão e CSRF. Senhas recebem hash Argon2id ou equivalente atual. O backend valida perfil e propriedade em todas as operações protegidas.
- **Alternativas consideradas:** JWT persistido em localStorage; credenciais em cada requisição; autenticação somente no frontend.
- **Consequências positivas:** token não fica acessível ao JavaScript da página; logout e revogação são diretos; autorização se mantém centralizada.
- **Consequências negativas:** requer armazenamento compartilhado de sessão em múltiplas instâncias e configuração de cookie/origem; CSRF precisa de validação consistente.
- **Condições operacionais:** HTTPS obrigatório; origem CORS restrita; segredo por ambiente; limites contra força bruta; mensagens uniformes de login; sessão sem dados sensíveis desnecessários.


