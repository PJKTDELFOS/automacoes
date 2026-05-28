SELECT 
    dados_json->>'numeroControlePNCP' as controle,
    dados_json->'orgaoEntidade'->>'cnpj' as cnpj,
    dados_json->>'anoCompra' as ano,
    dados_json->>'sequencialCompra' as seq,
    identificador_certame,
    COUNT(*)
FROM public.pncp_dados_brutos
GROUP BY 1,2,3,4,5
HAVING COUNT(*) > 1
ORDER BY 1;