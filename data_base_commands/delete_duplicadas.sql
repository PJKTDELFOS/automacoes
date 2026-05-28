DELETE FROM public.pncp_dados_brutos
WHERE id IN (
    SELECT id FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY dados_json->>'numeroControlePNCP'
                   ORDER BY id ASC
               ) AS rn
        FROM public.pncp_dados_brutos
    ) t
    WHERE rn > 1
);