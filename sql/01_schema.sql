-- 01_schema.sql · Sistema de Gestão de Academia (MySQL 8)
-- Executar uma vez no RDS: mysql -h <endpoint> -u <user> -p < sql/01_schema.sql

CREATE DATABASE IF NOT EXISTS academia
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE academia;

CREATE TABLE IF NOT EXISTS plano (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  nome          VARCHAR(80)   NOT NULL,
  valor_mensal  DECIMAL(10,2) NOT NULL,
  duracao_meses INT           NOT NULL DEFAULT 1,
  CONSTRAINT ck_plano_valor   CHECK (valor_mensal > 0),
  CONSTRAINT ck_plano_duracao CHECK (duracao_meses > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS aluno (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  nome      VARCHAR(120) NOT NULL,
  cpf       CHAR(11)     NOT NULL,
  email     VARCHAR(120) NULL,
  telefone  VARCHAR(20)  NULL,
  plano_id  INT          NOT NULL,
  criado_em TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_aluno_cpf UNIQUE (cpf),
  CONSTRAINT fk_aluno_plano FOREIGN KEY (plano_id)
    REFERENCES plano(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS aula (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  modalidade VARCHAR(60) NOT NULL,
  dia_semana VARCHAR(15) NOT NULL,
  horario    TIME        NOT NULL,
  instrutor  VARCHAR(80) NULL,
  vagas      INT         NOT NULL,
  CONSTRAINT ck_aula_vagas CHECK (vagas > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS inscricao (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  aluno_id  INT       NOT NULL,
  aula_id   INT       NOT NULL,
  criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_inscricao UNIQUE (aluno_id, aula_id),
  CONSTRAINT fk_insc_aluno FOREIGN KEY (aluno_id)
    REFERENCES aluno(id) ON DELETE CASCADE,
  CONSTRAINT fk_insc_aula FOREIGN KEY (aula_id)
    REFERENCES aula(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Usada nas próximas aulas (RF-02/RF-03); criada agora para o schema já ficar completo.
CREATE TABLE IF NOT EXISTS arquivo (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  aluno_id     INT          NOT NULL,
  tipo         VARCHAR(20)  NOT NULL,          -- 'foto' | 'atestado'
  chave_s3     VARCHAR(255) NOT NULL,
  chave_thumb  VARCHAR(255) NULL,
  tamanho_bytes INT         NULL,
  largura      INT          NULL,
  altura       INT          NULL,
  criado_em    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_arquivo_aluno FOREIGN KEY (aluno_id)
    REFERENCES aluno(id) ON DELETE CASCADE
) ENGINE=InnoDB;
