UPDATE public.pncp_leads_brutos
SET status_enriquecimento = 'PENDENTE'
WHERE status_enriquecimento = 'PROCESSADO'
  AND (email IS NULL OR email = '') -- Quem perdeu o e-mail
  AND telefone IS NOT NULL;
