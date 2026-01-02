ALTER TABLE public.historico_licitacoes 
ADD CONSTRAINT unique_envio_cliente UNIQUE (identificador_pncp, cliente);