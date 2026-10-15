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
