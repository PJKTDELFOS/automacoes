create table public.pncp_dados_brutos(
id serial primary key,
data_coleta timestamp default current_timestamp,
identificador_certame varchar(255) unique,
uf varchar(2),
objeto text,
dados_jason JSONB
);
create index idx_objeto_busca_texto on public.pncp_dados_brutos using gin (to_tsvector('portuguese',objeto))