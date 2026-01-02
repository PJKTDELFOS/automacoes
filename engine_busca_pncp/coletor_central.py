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
        hoje=datetime.now()
        pagina=1
        total_novos=0
        dias=dias_futuros if dias_futuros is not None else self.dias_coleta
        data_limite = hoje +  timedelta(days=dias)
        data_final_api = data_limite.strftime("%Y%m%d")
        data_para_exibir=data_limite.strftime("%d/%m/%Y")
        headers = {
            'accept': 'application/json',
            "User-Agent": "Mozilla/5.0"
        }

        print(f"[*] Iniciando coleta central: {data_para_exibir}")

        try:
            while True:
                params={'dataFinal': data_final_api,
                        'pagina':pagina,
                        'tamanhoPagina': 50}
                response = requests.get(self.endpoint, params=params, headers=headers)
                if response.status_code != 200:
                    self.log.registro(
                        "SISTEMA",
                        "API_COLETOR",
                        "ERROR",
                        "API_HTTP_ERR",
                        f"Status: {response.status_code}"
                    )
                    break
                dados=response.json()
                items=dados.get('data',[])
                if not items:break
                for item in items:
                    id_hash=self.get_certame_hash(item)
                    if self._persistir_bruto(id_hash,item):
                        total_novos+=1
                total_paginas=dados.get('totalPaginas',0)
                print(f"[Página {pagina}/{total_paginas}] Novos itens nesta leva: {total_novos}")
                if pagina >=total_paginas:
                    break
                pagina+=1
                time.sleep(0.5)
            self.log.registro(
                "SISTEMA", "COLETOR", "SUCCESS", "COL_DONE",
                f"Coleta finalizada com sucesso. {total_novos} novos itens inseridos."
            )
            print(f"[+] Processo concluído. Total de novos registros: {total_novos}")
        except Exception as e:
            self.log.registro(
                "SISTEMA", "COLETOR", "CRITICAL", "COL_FAIL", "Falha catastrófica na coleta", e
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






