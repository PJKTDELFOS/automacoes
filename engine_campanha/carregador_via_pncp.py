import re
import time
from datetime import datetime, timedelta

import pandas as pd
import requests

from engine_busca_pncp.db_manager import DBManager
from utilitarios.validadores import Validadores


class CargaPNCP:
    def __init__(self, dias_coleta=15):
        self.db_manager = DBManager()
        self.endpoint = "https://pncp.gov.br/api/consulta/v1/contratos"
        self.dias_coleta = dias_coleta

    def sanitizacao_validacao(self, valor):
        if pd.isna(valor) or valor == "":
            return None, None

        if not valor: return None, None

        limpo = re.sub(r'\D', '', str(valor))
        tamanho = len(limpo)
        if tamanho == 14:
            if Validadores.validar_cnpj(limpo):
                return limpo, 'CNPJ'
        elif tamanho == 11:
            if Validadores.validador_cpf(limpo):
                return limpo, 'CPF'
        return None, None

    def coleta(self, dias_passados=None):
        hoje = datetime.now()
        pagina = 1
        total_novos = 0
        dias = dias_passados if dias_passados is not None else self.dias_coleta

        data_inicio = hoje - timedelta(days=dias)

        # --- TENTATIVA 2: MUDANDO PARA FORMATO COM TRAÇOS (YYYY-MM-DD) ---
        str_data_inicial = data_inicio.strftime("%Y%m%d") # PNCP costuma usar YYYYMMDD, mas vamos debugar
        str_data_final = hoje.strftime("%Y%m%d")

        data_exibir = data_inicio.strftime("%d/%m/%Y")

        # Headers mais completos para evitar bloqueios de firewall
        headers = {
            'accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Referer': 'https://pncp.gov.br/app/contratos'
        }

        print(f"[*] Iniciando coleta central: {str_data_final}")
        print(f"[*] DEBUG: Data Final API: {str_data_final}")  # ADICIONE ISSO
        print(f"[*] DEBUG: Endpoint: {self.endpoint}")

        try:
            while True:
                params = {
                    'dataInicial': str_data_inicial,
                    'dataFinal': str_data_final,
                    'pagina': pagina,
                    'tamanhoPagina': 50
                }

                sucesso_na_pagina = False
                dados = None

                for tentativa in range(1, 4):
                    try:
                        response = requests.get(self.endpoint, params=params, headers=headers, timeout=30)
                        if response.status_code == 200:
                            dados = response.json()
                            sucesso_na_pagina = True
                            break  # Sucesso! Sai do loop de tentativas

                        elif response.status_code == 429:  # Too Many Requests
                            print(
                                f"[!] Bloqueio por excesso de requisições. Tentativa {tentativa}. Esperando 30s...")
                            time.sleep(30)
                        else:
                            print(f"[!] Erro HTTP {response.status_code} na página {pagina}. Tentando novamente...")
                            time.sleep(5)

                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                        print(f"[!] Erro de conexão na página {pagina} (Tentativa {tentativa}): {e}")
                        time.sleep(10 * tentativa)  # Espera progressiva: 10s, 20s...
                if not sucesso_na_pagina or not dados:
                    print(f"[-] Não foi possível obter a página {pagina}. Encerrando coleta para segurança.")
                    break
                items = dados.get('data', [])
                if not items:
                    print("[*] Fim dos dados retornados pela API.")
                    break
                novos_nesta_pagina=self.salvar_db(items)
                total_novos+=novos_nesta_pagina

                total_paginas = dados.get('totalPaginas', 0)
                print(f"[Página {pagina}/{total_paginas}] Novos itens acumulados: {total_novos}")

                if pagina >= total_paginas:
                    break

                pagina += 1
                # Intervalo de 2 segundos entre páginas para não "estressar" o servidor
                time.sleep(2)

        except Exception as e:
            print(f"[*] Error: {e}")

    def salvar_db(self, lista_items):
        query = """
            INSERT INTO public.pncp_leads_brutos 
            (cnpj_cpf, razao_social, email, tipo_documento)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cnpj_cpf) 
            DO UPDATE SET 
            razao_social = EXCLUDED.razao_social
            """
        dados_para_inserir=[]

        for item in lista_items:
            ni_bruto=item.get('niFornecedor')
            razao_social = item.get('nomeRazaoSocialFornecedor', '') or item.get('nomeRazaoSocial', '')
            doc_limpo,tipo_doc=self.sanitizacao_validacao(ni_bruto)
            if doc_limpo and razao_social:
                dados_para_inserir.append(
                    (doc_limpo,razao_social.upper().strip(),None,tipo_doc)
                )
        if not dados_para_inserir:
            return 0
        contagem_sucessos=0
        try:
            with self.db_manager.get_connection() as connection:
                with connection.cursor() as cursor:
                    for tupla in dados_para_inserir:
                        cursor.execute(query, tupla)
                        if cursor.rowcount > 0:
                            contagem_sucessos+=1
                connection.commit()
            return contagem_sucessos
        except Exception as e:
            print(f"[!] Erro ao salvar lote no banco: {e}")
            return 0


if __name__ == "__main__":
    # Cria o robô. O padrão é 15 dias, mas para testar agora recomendo colocar 1 ou 3 dias.
    robo = CargaPNCP(dias_coleta=3)

    # Manda ele trabalhar
    robo.coleta()

