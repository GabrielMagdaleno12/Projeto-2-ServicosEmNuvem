# Log de uso de IA

> Registro dos prompts importantes: o que pedimos, o que a IA gerou e o que o grupo **aceitou, rejeitou ou corrigiu**.

## Entrada 1 · Especificação inicial (Aula 1)

- **Data:** 14-10-2026
- **Ferramenta:** Claude (o GitHub Copilot estava indisponível)
- **Prompt:**
  > Projeto de nuvem na AWS Learner Lab, domínio academia. Requisitos: CRUD de 2 entidades relacionadas no RDS, upload no S3 por URL pré-assinada, S3 → Lambda → RDS, relatório com JOIN/GROUP BY via API Gateway + Lambda, front-end estático. Gere o `spec.md` com problema, personas, 5+ histórias e como cada RF se aplica.
- **O que a IA gerou:** `specs/spec.md` com problema, 3 personas, 10 histórias com critérios de aceite, tabela RF-01..RF-05, RNFs, priorização e riscos.
- **Decisão do grupo:**
  - Aceito: estrutura geral, histórias HU-01 a HU-09
  - Rejeitado: HU-10 importação CSV, por falta de tempo
  - Corrigido: nomes das personas; campos da entidade Aluno

## Entrada 2 · Design e arquitetura (Aula 2)

- **Data:** 14-10-2026
- **Ferramenta:** Claude
- **Prompt:**
  > Com base no spec.md, gere o design.md: diagrama de arquitetura, modelo ER, rotas da API, Security Groups e o ADR do RNF-04 (CRUD em Lambda ou container).
- **O que a IA gerou:** `specs/design.md` com diagrama Mermaid, ER, 18 rotas, tabela de SGs, 4 ADRs e SQL dos relatórios.
- **Decisão do grupo:**
  - Aceito: ADR-001 (CRUD em Lambda), SGs separados por função, EC2 de administração para rodar os scripts SQL no RDS privado.
  - Rejeitado: acesso à EC2 por SSH com porta 22 aberta; optamos por Session Manager (sem entrada de rede).
  - Corrigido: CIDRs das subnets; rotas simplificadas; diagramas trocados de Mermaid para PlantUML porque o Mermaid não renderizava.

## Entrada 3 · Infraestrutura, segurança e revisão da documentação (Aula 3)

- **Data:** 23-10-2026
- **Ferramenta:** Claude
- **Prompt:**
> Revise o repositório contra o enunciado da Aula 3 e corrija: (1) `tasks.md` sem ID, requisito, responsável e status; (2) IDs reais de VPC, subnets, route tables e Security Groups em `docs/seguranca.md`; (3) citar o `academia-sg-lambda` na entrada do `academia-sg-rds`; (4) alinhar o `design.md` com os SGs reais; (5) registrar a Aula 3 no log de IA; (6) prints em `docs/evidencias/`. Diga também se algo precisa mudar na AWS.
- **O que a IA gerou:** `specs/tasks.md` em tabela (ID, requisito, tarefa, responsável, status); ajuste de `docs/seguranca.md` (origem do RDS = `academia-sg-lambda`); remoção de `sg-bastion` e Session Manager em `specs/design.md`; esta entrada; `docs/evidencias/README.md` com a lista de prints; lista de verificações a fazer no console da AWS.
- **Decisão do grupo:**
- Aceito: tabela de tarefas com IDs T-01 a T-29; SG do RDS aceitando a porta 3306 somente do `academia-sg-lambda`.
- Corrigido: a decisão da Entrada 2 (EC2 de administração com Session Manager) foi revertida. Não há bastion; os scripts SQL rodam pela Lambda `academia-dbinit` dentro da VPC.
- Pendente (a IA não tem acesso à conta AWS): IDs reais dos recursos e os prints. O grupo preenche a partir do console.
- Pendente: o grupo deve completar nesta entrada eventuais outros prompts usados na criação da infraestrutura da Aula 3 (VPC, RDS, Lambdas), se houver.

## Entrada 4 · Upload, evento S3 → Lambda → RDS e relatórios (Aula 4)

- **Data:** 28-10-2026
- **Ferramenta:** Claude
- **Prompt:**
  > Com base em `specs/spec.md` e `specs/design.md`, gere as Lambdas `presign`, `miniatura` e `relatorios` (Python 3.12, MySQL, PyMySQL, Pillow) para RF-02, RF-03 e RF-04, e explique como criar o que falta na AWS (bucket de uploads, gatilho S3, rotas do API Gateway) sem IaC e só com a LabRole.
- **O que a IA gerou:** os três handlers; os comandos de criação dos recursos na AWS; o trecho de front para upload e relatórios (`frontend/aula4.js`); os textos de README, design e ia-log.
- **Decisão do grupo:**
  - Aceito: URL pré-assinada SigV4; prefixos `uploads/` (gatilho) e `thumbs/` (saída) para evitar loop de eventos; reuso da conexão com o RDS fora do handler; validação do limite de 5 MB também na Lambda Miniatura.
  - Corrigido: a primeira versão assumia colunas que não existiam em `arquivo`; os handlers foram adaptados ao schema real (`tipo`, `chave_thumb`, sem coluna de status) e o script SQL extra foi descartado. A variável da senha do banco ficou padronizada como `DB_PASSWORD`. Foi acrescentada a rota `GET /alunos/{id}/arquivos`, porque o bucket é privado e o front precisa de URLs pré-assinadas para exibir as miniaturas.
  - Rejeitado: bucket de uploads público e upload passando pelo API Gateway/Lambda (limite de payload).
- **Validação:** teste ao vivo em 28/10/2026: relatórios com HTTP 200; upload de um PNG 400x300 gerou a miniatura em `thumbs/` e atualizou a linha em `arquivo` (123011 bytes, 400x300) em cerca de 1 s; o CloudWatch registrou "Novo objeto" e "Miniatura criada ... linhas atualizadas no RDS: 1"; o site exibiu a miniatura com status PROCESSADO.

