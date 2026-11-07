# ADR-001 — Monólito modular em camadas

- **Status:** aceito para a primeira versão.
- **Contexto:** a descomplica cursos precisa entregar catálogo, identidade, matrícula, conteúdo, progresso e avaliações com equipe pequena e infraestrutura inicial simples. O crescimento futuro é possível, mas ainda não foi medido.
- **Decisão:** implementar uma API Flask implantável como serviço único, organizada por módulos de domínio e camadas de apresentação, aplicação, domínio e infraestrutura. O frontend React é um cliente separado da API.
- **Alternativas consideradas:** aplicação monolítica sem fronteiras internas; microsserviços desde a primeira versão; funções serverless por caso de uso.
- **Justificativa:** transações e operação são simples; responsabilidades ficam explícitas; a equipe consegue desenvolver e implantar sem operar vários serviços independentes. Módulos com contratos claros preservam a opção de extração futura.
- **Consequências positivas:** menor custo operacional inicial; depuração e transações mais simples; fronteiras úteis para documentação e testes.
- **Consequências negativas:** uma implantação de backend pode afetar vários módulos; disciplina de dependências é necessária; escala de partes isoladas é menos flexível.
- **Condição de revisão:** métricas mostram gargalo localizado, equipes precisam de ciclos de lançamento independentes, ou isolamento de falha exige processo separado.
