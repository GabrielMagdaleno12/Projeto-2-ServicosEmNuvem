-- 02_seed.sql · dados de exemplo (planos e aulas)
USE academia;

INSERT INTO plano (nome, valor_mensal, duracao_meses) VALUES
  ('Mensal',     120.00,  1),
  ('Trimestral', 330.00,  3),
  ('Anual',      1080.00, 12);

INSERT INTO aula (modalidade, dia_semana, horario, instrutor, vagas) VALUES
  ('Spinning',   'Segunda', '07:00:00', 'Rafael', 15),
  ('Yoga',       'Terça',   '18:30:00', 'Camila', 12),
  ('Funcional',  'Quarta',  '19:00:00', 'Bruno',  20),
  ('Pilates',    'Quinta',  '08:00:00', 'Camila', 10);
