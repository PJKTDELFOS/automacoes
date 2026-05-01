import json
import hashlib
from datetime import datetime, timedelta
import requests
import time
from engine_busca_pncp.db_manager import DBManager
from engine_busca_pncp.log_manager import LogManager


class ColetorCentral:
    def __init__(self,db_manager,dias_padrao=15):
        self.db = db_manager
        self.log = LogManager(self.db)
        self.endpoint = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
        self.dias_coleta=dias_padrao
        self.session=requests.Session()

        self.session.headers.update(
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
        )

    def get_certame_hash(self,item):
        payload=(f"{item.get('orgaoEntidade', {}).get('cnpj', '')}{item.get('anoCompra')}"
                 f"{item.get('numeroCompra')}"
                 f"{item.get('unidadeOrgao', {}).get('codigoUnidade', '')}")
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()
    def coleta_diaria(self,dias_futuros=None):
        hoje = datetime.now()
        data_referencia=hoje.date()
        total_novos=0
        dias=dias_futuros if dias_futuros is not None else self.dias_coleta
        data_limite=hoje+timedelta(days=dias)
        data_final_api= data_limite.strftime("%Y%m%d")
        data_para_exibir = data_limite.strftime("%d/%m/%Y")



        print(f"[*] Iniciando coleta central: {data_para_exibir}")
        print(f"[*] DEBUG: Data Final API: {data_final_api}")  # ADICIONE ISSO
        print(f"[*] DEBUG: Endpoint: {self.endpoint}")

        try:
            params_inicial={
                'dataFinal': data_final_api,
                'pagina':1,
                'tamanhoPagina':50,
            }
            resp=self.session.get(self.endpoint,params=params_inicial,timeout=30)
            if resp.status_code == 200:
                total_paginas=resp.json().get('totalPaginas',1)
                self.db.registrar_mapeamento_diario_PNCP(data_referencia,total_paginas)
            else:
                print(f"[-] Falha ao acessar API para mapeamento: {resp.status_code}")
                return

            while True:
                tarefa=self.db.get_proxima_pagina_PNCP(data_referencia)
                if not tarefa:
                    print("[+] Nenhuma página pendente para hoje. Verificando integridade...")
                    break
                id_tarefa=tarefa['id']
                num_pagina=tarefa['numero_pagina']
                print(f'Processando pagina {num_pagina} ( tarefa ID: {id_tarefa} )')
                params={
                    'dataFinal': data_final_api,
                    'pagina': num_pagina,
                    'tamanhoPagina': 50,
                }

                try:
                    response=self.session.get(self.endpoint,params=params,timeout=30)
                    if response.status_code == 200:
                        try:
                            dados=response.json()
                            items=dados.get('data',[])
                            for item in items:
                                id_hash=self.get_certame_hash(item)
                                if self._persistir_bruto(id_hash,item):
                                    total_novos+=1
                            print(f'[*] Página {num_pagina} concluída. Total de novos editais até agora: {total_novos}')
                            self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'CONCLUIDO', 200)
                            time.sleep(2)
                        except Exception as e_proc:
                            print(f"[!] Erro ao processar dados da página {num_pagina}: {e_proc}")
                            self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'ERRO', 998)


                    elif response.status_code == 429:
                        print(f"[!] Rate Limit na página {num_pagina}. Aguardando 30s...")
                        self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'ERRO', 429)
                        time.sleep(30)
                    else:
                        self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'ERRO', response.status_code)
                        time.sleep(5)
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    print(f"[!] Erro de conexão na página {num_pagina}: {e}")
                    self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'ERRO', 999)
                    time.sleep(10)
            if self.db.verificar_conclusao_dia_PNCP(data_referencia):
                print(f"[🏆] Integridade confirmada! Disparando boletins para clientes...")
                return True
            else:
                print(f"[!] Coleta parcial. {total_novos} novos itens no banco, mas faltam páginas.")
                return False
        except Exception as e:
            self.log.registro('SISTEMA','COLETOR',
                              'CRITICAL','COL_FAIL','ERRO CATASTROFICO',str(e))
            print(f"[-] Erro crítico: {e}, 'caindo aqui" )



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






