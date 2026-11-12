# Relatório de revisão e validação — AV2 LearnPlay

**Data:** 7 de novembro de 2026  
**Escopo:** todos os artefatos produzidos nos Passos 1 e 2.  
**Resultado:** documentação e especificações aprovadas nas verificações executadas, com correções aplicadas durante a revisão.

## 1. Arquivos revisados

- 01_Passo_1_Arquitetura.md e 02_Passo_2_Documentacao.md.
- README.md.
- Quatro ADRs em adrs/.
- Contrato contratos/openapi.yaml.
- Matriz matriz_rastreabilidade.csv.
- Dez fontes de diagrama em diagramas/.

## 2. Verificações executadas

| Verificação | Resultado |
|---|---|
| Parse e validação normativa do OpenAPI | Passou no validador OpenAPI 3.1: 18 caminhos, 18 operações e 61 referências locais resolvidas. |
| Parâmetros e segurança das rotas | Todos os parâmetros de caminho estão declarados; esquemas de autenticação referenciados existem; operações têm respostas. |
| Matriz de rastreabilidade | 19 linhas de dados, 6 colunas; todos os 22 requisitos funcionais e não funcionais do Passo 1 aparecem na matriz. |
| Referências entre documentos e arquivos | Os 15 caminhos explícitos citados no documento do Passo 2 existem. |
| Formatação Markdown | Blocos de código balanceados nos documentos principais. |
| Fontes Mermaid | Dez diagramas têm cabeçalho/tipo reconhecido; blocos de sequência estão balanceados; não há rótulos com quebra de linha acidental. |
| Consistência do fluxo de e-mail | API grava na outbox; worker envia; as visões C2 e física não mostram envio direto pela API. |
| Conteúdo essencial | Matrícula gratuita e paga, progresso idempotente, CSRF, tentativas de avaliação e validação de webhook conferidos entre texto, contrato e diagramas. |

## 3. Correções aplicadas

1. Corrigida uma junção de linhas no YAML do webhook que tornava o OpenAPI inválido.
2. Adicionado o fluxo para obter token CSRF antes do registro/login; registro e login agora exigem o token, e o login renova sessão e token.
3. Explicitado o worker de notificações que consome a outbox; removido envio de e-mail diretamente pela API nos diagramas e corrigido o fluxo de matrícula para que apenas cursos pagos recebam webhook de pagamento.
4. Completado o modelo de avaliação com questões, respostas, tentativas, limite inicial de três tentativas e regra de melhor nota.
5. Reforçada a validação do webhook para conferir assinatura, merchant, referência local, valor, moeda e repetição do evento antes de liberar matrícula.
6. Alinhados nomes de rotas e parâmetros entre Passo 1, Passo 2 e OpenAPI; completados health checks, criação de curso e administração de usuários.
7. Definida a obtenção de CSRF e a necessidade de hospedar frontend/API na mesma origem ou no mesmo site registrável para a política de cookie especificada.

## 4. Limites da validação

- **Não existe ainda código executável da plataforma** nos Passos 1 e 2. Portanto, não foi possível validar login, matrícula, pagamento, progresso, avaliação, persistência, migrações, implantação ou funcionamento em navegador. Esses comportamentos dependem do protótipo do Passo 3.
- As metas de até 1.000 sessões simultâneas, latência, disponibilidade, backup e recuperação são requisitos de projeto, não resultados medidos.
- As fontes Mermaid foram revisadas estruturalmente, mas não foram renderizadas: não há renderizador Mermaid instalado neste ambiente. A apresentação visual dos diagramas permanece sem verificação visual.
- Os nomes dos integrantes continuam como campo para preencher com os dados reais da equipe.

## 5. Conclusão

Não restaram erros de parse no OpenAPI nem lacunas na cobertura dos requisitos pela matriz. Os documentos e contratos estão coerentes após as correções listadas. A validação de comportamento da aplicação e a apresentação visual dos diagramas ainda dependem, respectivamente, do protótipo e de um renderizador Mermaid.
