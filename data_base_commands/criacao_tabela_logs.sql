CREATE TABLE public.logs_bot_pncp(
id SERIAL PRIMARY KEY,
timestamp_log TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
cliente VARCHAR(255) NOT  NULL,
etapa VARCHAR(255) NOT NULL,
nivel VARCHAR(255) NOT NULL,
codigo_erro VARCHAR(255),
mensagem TEXT,
stack_trace TEXT
);
CREATE INDEX idx_logs_cliente ON public.logs_bot_pncp(cliente);
CREATE INDEX idx_logs_data ON public.logs_bot_pncp(timestamp_log);

