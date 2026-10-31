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
- Resolvido depois: os IDs reais foram preenchidos em `docs/seguranca.md` e os prints estão em `docs/evidencias/`.

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

## Entrada 5 · Recriação do ambiente em um novo Learner Lab (31/10/2026)

- **Data:** 31-10-2026
- **Ferramenta:** Claude (com acesso ao console da AWS pelo navegador e ao CloudShell)
- **Prompt:**
  > O laboratório está com US$ 45 de 50. Você consegue criar tudo igual em outro lab? Antes de recriar, garanta que o RDS não vai gastar tanto quanto no lab anterior.
- **O que a IA gerou:** scripts de CloudShell com AWS CLI (rede, RDS, buckets, Lambdas, API Gateway, front) e a recriação do ambiente na conta nova; a landing page foi baixada do site antigo e republicada em um bucket novo; atualização dos IDs na documentação.
- **Decisão do grupo:**
  - Aceito: RDS no tamanho mínimo (db.t3.micro, 20 GB gp2, zona única, sem backup automático, sem Performance Insights) e **parado ao final de cada sessão**; sem NAT Gateway, sem IP elástico e sem EC2.
  - Corrigido: (1) três Lambdas (presign, relatorios e miniatura) foram criadas com o handler `handler.lambda_handler`, mas o código usa `handler.handler`, o que causou HTTP 500 na aba Relatórios; o handler foi corrigido e testado. (2) A IA encerrou (terminate) duas EC2 antigas do Projeto 1 por engano, ao escolher a opção errada no menu; eram sobras sem relação com este projeto, e o fato foi comunicado ao grupo.
  - Rejeitado: reaproveitar nomes de bucket do lab antigo (já pertencem a outra conta); a landing foi publicada como `academia-landing-<id-da-conta>`.
  - Limitação: senhas do banco foram digitadas pelo próprio integrante no CloudShell; a IA não as viu nem as gravou.
- **Validação:** criação de aluno (201), exclusão de plano em uso (409), CPF inválido (400), upload de PNG 800x600 gerando miniatura e atualizando o RDS (status PROCESSADO), relatórios com HTTP 200, e RDS parado ao final.

## Reflexão final sobre o uso de IA

> Rascunho escrito pela IA a partir do que aconteceu no projeto; o grupo deve revisar e ajustar com suas palavras antes da entrega.

A IA acelerou muito a escrita da especificação, do design e do código das Lambdas, e principalmente a repetição do ambiente na AWS por CLI, o que tornou possível recriar tudo em poucas horas. Ela também errou de forma relevante: assumiu colunas que não existiam na tabela `arquivo`, errou o nome do handler de três Lambdas e encerrou recursos errados por engano. Por isso, tudo o que ela gerou foi conferido por teste (chamadas à API, logs do CloudWatch e consultas ao banco) e nada foi aceito só porque parecia certo. O aprendizado principal é que a IA é boa para gerar e repetir, mas a validação e as decisões de custo e segurança (RDS privado, sem NAT, SG por origem, RDS parado quando não usado) precisam ser do grupo.
