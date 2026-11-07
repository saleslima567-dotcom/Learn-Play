# ADR-002 — PostgreSQL transacional e armazenamento S3 para mídia

- **Status:** aceito.
- **Contexto:** matrículas, pagamentos, avaliações e progresso precisam de integridade relacional. Vídeos e materiais têm tamanho e padrão de acesso diferentes dos registros transacionais.
- **Decisão:** usar PostgreSQL para dados estruturados e transações; guardar objetos de mídia em armazenamento compatível com S3. O banco persiste metadados, chaves e estados, nunca os vídeos binários.
- **Alternativas consideradas:** guardar arquivos no PostgreSQL; armazenar vídeos no disco local da API; usar um banco documental como fonte transacional.
- **Consequências positivas:** constraints relacionais protegem matrícula única e conclusões; objetos de mídia escalam independentemente; URLs temporárias limitam acesso.
- **Consequências negativas:** dois sistemas precisam de credenciais, monitoramento e políticas de retenção; consistência entre metadata e arquivo precisa de tratamento compensatório; desenvolvimento exige adaptadores locais/sandbox.
- **Condições operacionais:** backups e migrações para PostgreSQL; bucket privado; upload validado; URLs curtas; sem segredo de produção no repositório.
