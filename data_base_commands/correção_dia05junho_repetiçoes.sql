-- PASSO 1: Criar uma tabela temporária para organizar os dados limpos
CREATE TEMP TABLE pncp_dados_brutos_limpos AS
SELECT DISTINCT ON (dados_json->>'numeroControlePNCP') 
    id,
    data_coleta,
    MD5(dados_json->>'numeroControlePNCP') AS novo_hash, -- Corrigido para MD5 com precisão
    uf,
    objeto,
    dados_json
FROM public.pncp_dados_brutos
WHERE dados_json->>'numeroControlePNCP' IS NOT NULL
ORDER BY dados_json->>'numeroControlePNCP', id ASC;


-- PASSO 2: Limpar completamente o lixo da tabela oficial (Preservando a estrutura e o SERIAL)
TRUNCATE TABLE public.pncp_dados_brutos;


-- PASSO 3: Se a restrição UNIQUE antiga ainda estiver lá com outro nome, vamos garantir que ela caia para não atrapalhar
ALTER TABLE public.pncp_dados_brutos DROP CONSTRAINT IF EXISTS unique_identificador_certame;
ALTER TABLE public.pncp_dados_brutos DROP CONSTRAINT IF EXISTS pncp_dados_brutos_identificador_certame_key;


-- PASSO 4: Devolver os dados limpos e convertidos para a tabela oficial
INSERT INTO public.pncp_dados_brutos (id, data_coleta, identificador_certame, uf, objeto, dados_json)
SELECT id, data_coleta, novo_hash, uf, objeto, dados_json
FROM pncp_dados_brutos_limpos;


-- PASSO 5: Aplicar a nova trava indestrutível de unicidade
ALTER TABLE public.pncp_dados_brutos ADD CONSTRAINT unique_identificador_certame UNIQUE (identificador_certame);


-- PASSO 6: Calibrar a sequência do seu ID SERIAL para acompanhar o volume atual
SELECT setval('public.pncp_dados_brutos_id_seq', COALESCE((SELECT MAX(id) FROM public.pncp_dados_brutos), 1), true);