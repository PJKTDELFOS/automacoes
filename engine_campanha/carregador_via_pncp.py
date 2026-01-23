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
        self.endpoint = "https://pncp.gov.br/api/consulta/v1/contratos/atualizacao"
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
        data_limite = hoje - timedelta(days=dias)
        data_final_api = data_limite.strftime("%Y%m%d")
        data_para_exibir = data_limite.strftime("%d/%m/%Y")

        # Headers mais completos para evitar bloqueios de firewall
        headers = {
            'accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Referer': 'https://pncp.gov.br/app/contratos'
        }

        print(f"[*] Iniciando coleta central: {data_para_exibir}")
        print(f"[*] DEBUG: Data Final API: {data_final_api}")  # ADICIONE ISSO
        print(f"[*] DEBUG: Endpoint: {self.endpoint}")

        try:
            while True:
                params = {
                    'dataFinal': data_final_api,
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
                for item in items:
                    if self.salvar_db(item):
                        total_novos += 1
                total_paginas = dados.get('totalPaginas', 0)
                print(f"[Página {pagina}/{total_paginas}] Novos itens acumulados: {total_novos}")

                if pagina >= total_paginas:
                    break

                pagina += 1
                # Intervalo de 2 segundos entre páginas para não "estressar" o servidor
                time.sleep(2)

        except Exception as e:
            print(f"[*] Error: {e}")

    def salvar_db(self, item):
        query = """
        INSERT INTO public.pncp_leads_brutos 
        (cnpj_cpf, razao_social, email, tipo_documento)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (cnpj_cpf) 
        DO UPDATE SET 
            razao_social = EXCLUDED.razao_social,
            tipo_documento = EXCLUDED.tipo_documento
        """

        try:
            ni_bruto = item.get('niFornecedor')
            razao_social = item.get('nomeRazaoSocialFornecedor', '').upper()
            documento_limpo, tipo_doc = self.sanitizacao_validacao(ni_bruto)
            if not documento_limpo:
                return False
            with self.db_manager.get_connection() as connection:
                with connection.cursor() as cursor:


                    cursor.execute(
                        query,(documento_limpo,razao_social,None,tipo_doc)
                        )
                    connection.commit()
                    return cursor.rowcount >0
        except Exception as e:
            print(f"Erro ao persistir item : {e}")
            return False


