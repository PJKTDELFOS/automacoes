import json
import hashlib
from datetime import datetime, timedelta
import requests
import time
from engine_busca_pncp.db_manager import DBManager
from engine_busca_pncp.log_manager import LogManager


class ColetorCentral:
    def __init__(self,dias_padrao=15):
        self.db = DBManager()
        self.log = LogManager(self.db)
        self.endpoint = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
        self.dias_coleta=dias_padrao

    def get_certame_hash(self,item):
        payload=(f"{item.get('orgaoEntidade', {}).get('cnpj', '')}{item.get('anoCompra')}"
                 f"{item.get('numeroCompra')}"
                 f"{item.get('unidadeOrgao', {}).get('codigoUnidade', '')}")
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def coleta_diaria(self,dias_futuros=None):
        hoje = datetime.now()
        pagina = 1
        total_novos = 0
        dias = dias_futuros if dias_futuros is not None else self.dias_coleta
        data_limite = hoje + timedelta(days=dias)
        data_final_api = data_limite.strftime("%Y%m%d")
        data_para_exibir = data_limite.strftime("%d/%m/%Y")

        # Headers mais completos para evitar bloqueios de firewall
        headers = {
            'accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Referer': 'https://pncp.gov.br/app/editais'
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

                # LOOP DE RESILIÊNCIA (TENTATIVAS)
                for tentativa in range(1, 4):  # Tenta até 3 vezes
                    try:
                        # Timeout de 30s evita que o bot fique travado se a rede oscilar
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

                # Se após as tentativas não conseguirmos os dados, encerramos a coleta
                if not sucesso_na_pagina or not dados:
                    print(f"[-] Não foi possível obter a página {pagina}. Encerrando coleta para segurança.")
                    break

                items = dados.get('data', [])
                if not items:
                    print("[*] Fim dos dados retornados pela API.")
                    break

                # PROCESSAMENTO DOS ITENS
                for item in items:
                    id_hash = self.get_certame_hash(item)
                    # O persistir_bruto retorna True se for um item novo (insert)
                    if self._persistir_bruto(id_hash, item):
                        total_novos += 1

                total_paginas = dados.get('totalPaginas', 0)
                print(f"[Página {pagina}/{total_paginas}] Novos itens acumulados: {total_novos}")

                if pagina >= total_paginas:
                    break

                pagina += 1
                # Intervalo de 2 segundos entre páginas para não "estressar" o servidor
                time.sleep(2)

            # REGISTRO FINAL DE LOG
            self.log.registro(
                "SISTEMA", "COLETOR", "SUCCESS", "COL_DONE",
                f"Coleta finalizada com sucesso. {total_novos} novos itens inseridos."
            )
            print(f"[+] Processo concluído. Total de novos registros: {total_novos}")

        except Exception as e:
            self.log.registro(
                "SISTEMA", "COLETOR", "CRITICAL", "COL_FAIL", "Falha catastrófica na coleta", str(e)
            )
            print(f"[-] Erro crítico no coletor: {e}")
    def _persistir_bruto(self,id_hash,item):

        sql='''
        insert into public.pncp_dados_brutos( 
        identificador_certame, uf, objeto, dados_json)
        values (%s, %s, %s, %s)
        on conflict (identificador_certame) do nothing
        '''

        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    uf = (
                            item.get('unidadeOrgao', {}).get('ufSigla') or
                            item.get('orgaoEntidade', {}).get('ufSigla') or
                            'BR'
                    )
                    objeto_texto = str(
                        item.get('objetoCompra') or
                        item.get('objeto') or
                        ""
                    ).lower()
                    cursor.execute(
                        sql,
                        (id_hash,
                        uf,
                        objeto_texto,
                        json.dumps(item)
                    ))
                    connection.commit()
                    return cursor.rowcount >0
        except Exception as e:
            print(f"Erro ao persistir item {id_hash}: {e}")
            return False






