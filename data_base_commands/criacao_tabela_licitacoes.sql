create table historico_licitacoes(
id SERIAL PRIMARY KEY,
identificador_pncp VARCHAR(255),
cliente VARCHAR(255),
data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
UNIQUE (identificador_pncp,cliente)
);