# Especificação — Sistema de Gestão de Academia

> Projeto 2 · 2026.02 · Domínio: academia

## 1. Problema

Academias pequenas e médias controlam alunos, planos e frequência em planilhas ou cadernos. Isso gera:

- cadastros duplicados ou desatualizados;
- dificuldade para saber quem está com o plano vencido;
- nenhum controle de quais aulas coletivas lotam ou ficam vazias;
- documentos (atestado médico, foto) espalhados em WhatsApp e pastas locais.

**Solução:** uma aplicação web na AWS onde a recepção cadastra alunos e planos, inscreve alunos em aulas, anexa documentos e consulta relatórios de ocupação e frequência.

## 2. Personas

| Persona | Descrição | Objetivo principal |
|---|---|---|
| **Marina, recepcionista** | Atende no balcão, usa computador o dia todo | Cadastrar e consultar alunos rápido, anexar atestado, inscrever em aula |
| **Carlos, gerente** | Dono/gerente da academia | Ver relatórios de ocupação das aulas e de alunos por plano para decidir horários e preços |
| **Júlia, aluna** | Frequenta a academia | (Futuro) consultar suas inscrições. **Fora do escopo desta versão** |

## 3. Escopo

### Dentro do escopo
- Cadastro de planos, alunos, aulas e inscrições.
- Upload de foto do aluno e de atestado médico (PDF).
- Processamento automático do arquivo enviado (miniatura da foto).
- Relatórios gerenciais.
- Interface web simples para a recepção.

### Fora do escopo
- Login/autenticação de múltiplos perfis (assumimos uso interno da recepção).
- Pagamentos e cobrança.
- Aplicativo mobile.
- Catraca / controle de acesso físico.

## 4. Modelo conceitual (resumo)

- **Plano** (1) —— (N) **Aluno**: cada aluno tem um plano; um plano tem vários alunos.
- **Aluno** (N) —— (N) **Aula**, via **Inscrição**.
- **Aluno** possui arquivos (foto, atestado) armazenados no S3.

O detalhamento (ER, colunas, tipos) fica em `specs/design.md`.

## 5. Histórias de usuário e critérios de aceite

### HU-01 · Cadastrar aluno
**Como** recepcionista, **quero** cadastrar um aluno com nome, CPF, e-mail, telefone e plano, **para** manter o controle de quem frequenta a academia.

**Critérios de aceite:**
- **Dado** um formulário com nome, CPF válido e plano selecionado, **quando** eu salvar, **então** o aluno aparece na listagem.
- **Dado** um CPF já cadastrado, **quando** eu salvar, **então** o sistema recusa e mostra mensagem de duplicidade.
- **Dado** um campo obrigatório vazio, **quando** eu salvar, **então** o sistema indica qual campo falta e não grava.

### HU-02 · Consultar, editar e excluir aluno
**Como** recepcionista, **quero** buscar, alterar e remover alunos, **para** manter os dados corretos.

**Critérios de aceite:**
- **Dado** a listagem de alunos, **quando** eu buscar por parte do nome, **então** vejo só os alunos correspondentes.
- **Dado** um aluno existente, **quando** eu alterar o telefone e salvar, **então** a listagem mostra o novo valor.
- **Dado** um aluno com inscrições, **quando** eu excluí-lo, **então** o sistema remove também as inscrições dele (ou pede confirmação explícita).

### HU-03 · Gerenciar planos
**Como** gerente, **quero** criar, editar e remover planos (nome, valor mensal, duração em meses), **para** adequar a oferta da academia.

**Critérios de aceite:**
- **Dado** nome e valor positivo, **quando** eu salvar, **então** o plano aparece na lista e fica disponível no cadastro de aluno.
- **Dado** um plano com alunos vinculados, **quando** eu tentar excluí-lo, **então** o sistema bloqueia e informa quantos alunos o usam.
- **Dado** um valor negativo ou zero, **quando** eu salvar, **então** o sistema recusa.

### HU-04 · Gerenciar aulas
**Como** gerente, **quero** cadastrar aulas (modalidade, dia da semana, horário, instrutor, vagas), **para** organizar a grade.

**Critérios de aceite:**
- **Dado** modalidade, horário e vagas > 0, **quando** eu salvar, **então** a aula aparece na grade.
- **Dado** uma aula existente, **quando** eu alterar o número de vagas, **então** o novo limite passa a valer para inscrições futuras.

### HU-05 · Inscrever aluno em aula
**Como** recepcionista, **quero** inscrever um aluno em uma aula, **para** garantir sua vaga.

**Critérios de aceite:**
- **Dado** uma aula com vagas disponíveis, **quando** eu inscrever um aluno, **então** a inscrição é criada e as vagas restantes diminuem.
- **Dado** uma aula lotada, **quando** eu tentar inscrever, **então** o sistema recusa com mensagem "aula lotada".
- **Dado** um aluno já inscrito na aula, **quando** eu tentar inscrever de novo, **então** o sistema recusa a duplicidade.
- **Dado** uma inscrição existente, **quando** eu cancelá-la, **então** a vaga é liberada.

### HU-06 · Enviar foto e atestado do aluno
**Como** recepcionista, **quero** anexar a foto e o atestado médico (PDF) ao aluno, **para** ter a documentação centralizada.

**Critérios de aceite:**
- **Dado** um aluno cadastrado e um arquivo permitido (JPG/PNG/PDF até 5 MB), **quando** eu enviar, **então** o arquivo é armazenado no S3 e vinculado ao aluno.
- **Dado** um arquivo de tipo não permitido ou maior que o limite, **quando** eu enviar, **então** o sistema recusa antes do upload.
- **Dado** um arquivo enviado, **quando** eu abrir a ficha do aluno, **então** consigo ver/baixar o arquivo.
- O upload deve ocorrer direto do navegador para o S3 por **URL pré-assinada** gerada pelo backend.

### HU-07 · Miniatura automática da foto
**Como** recepcionista, **quero** que a foto enviada gere automaticamente uma miniatura, **para** a listagem carregar rápido.

**Critérios de aceite:**
- **Dado** uma foto enviada ao S3, **quando** o evento disparar a Lambda, **então** uma miniatura (ex.: 150×150) é gerada e salva no S3.
- **Dado** a miniatura gerada, **quando** a Lambda terminar, **então** a URL/chave da miniatura e os metadados (tamanho, dimensões) ficam gravados no RDS.
- **Dado** uma falha no processamento, **quando** ocorrer, **então** o erro fica registrado no CloudWatch Logs.

### HU-08 · Relatório de ocupação das aulas
**Como** gerente, **quero** ver para cada aula o número de inscritos, vagas e taxa de ocupação, **para** decidir quais horários manter ou reforçar.

**Critérios de aceite:**
- **Dado** aulas com inscrições, **quando** eu abrir o relatório, **então** vejo por aula: modalidade, horário, inscritos, vagas e % de ocupação.
- **Dado** uma aula sem inscrições, **quando** eu abrir o relatório, **então** ela aparece com 0 inscritos (não some da lista).
- Os dados vêm de `GET /relatorios/ocupacao-aulas`, com `JOIN` e `GROUP BY`.

### HU-09 · Relatório de alunos por plano
**Como** gerente, **quero** ver quantos alunos e qual receita mensal estimada cada plano tem, **para** avaliar a política de preços.

**Critérios de aceite:**
- **Dado** planos com alunos, **quando** eu abrir o relatório, **então** vejo por plano: nome, quantidade de alunos e receita estimada (alunos × valor).
- **Dado** um plano sem alunos, **quando** eu abrir o relatório, **então** ele aparece com 0.

## 6. Como os requisitos obrigatórios se aplicam ao domínio

| ID | Aplicação na academia | Histórias |
|---|---|---|
| **RF-01** | CRUD de **Plano**, **Aluno**, **Aula** e **Inscrição**, com relações 1:N (Plano→Aluno) e N:N (Aluno↔Aula) no RDS | HU-01 a HU-05 |
| **RF-02** | Upload de foto e atestado do aluno ao S3 por URL pré-assinada gerada pelo backend | HU-06 |
| **RF-03** | Evento `ObjectCreated` no S3 aciona Lambda que gera miniatura (e/ou importa CSV) e grava o resultado no RDS | HU-07|
| **RF-04** | `GET /relatorios/ocupacao-aulas` e `GET /relatorios/alunos-por-plano` no API Gateway, implementados em Lambda com JOIN/GROUP BY | HU-08, HU-09 |
| **RF-05** | Front-end estático (HTML/JS) publicado em S3 consumindo a API | todas |

## 7. Requisitos não funcionais

| ID | Aplicação |
|---|---|
| **RNF-01** | RDS (MySQL/PostgreSQL) em subnet privada, sem acesso público; Security Groups documentados em `design.md` |
| **RNF-02** | Credenciais fora do repositório (variáveis de ambiente das Lambdas, `.env` no `.gitignore`) |
| **RNF-03** | README com passo a passo para recriar tudo em nova sessão do Learner Lab, sem IP fixo |
| **RNF-04** | ADR no `design.md`: CRUD em Lambda ou em container (EC2/ECS) |
| **RNF-05** | Sem IaC; recursos criados via console/CLI e documentados no README |

## 8. Prioridade e plano de entrega

| Prioridade | Histórias | Entrega |
|---|---|---|
| Essencial | HU-01, HU-02, HU-03 (CRUD Plano + Aluno) | Aula 3 (23/10) |
| Essencial | HU-06, HU-07 (upload + Lambda), HU-08 (relatório) | Aula 4 (30/10) |
| Importante | HU-04, HU-05 (Aula + Inscrição), HU-09 | Aula 4 (30/10) |

## 9. Riscos

| Risco | Mitigação |
|---|---|
| Sessão do Learner Lab expira e perde endpoint/IP | README com passo a passo; sem IP fixo no código |
| Lambda na VPC sem internet para acessar S3 | VPC Gateway Endpoint para S3 (gratuito) |
| Estouro de orçamento | Sem NAT Gateway; `db.t3.micro`; desligar recursos ao fim da sessão |
| CORS bloqueando front-end | Configurar CORS no API Gateway e no bucket desde o início |
