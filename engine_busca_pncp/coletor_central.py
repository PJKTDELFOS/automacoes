import json
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import requests
import time
from engine_busca_pncp.db_manager import DBManager
from engine_busca_pncp.log_manager import LogManager


class ColetorCentral:
    def __init__(self, db_manager, dias_padrao=15, max_workers=5):
        self.db = db_manager
        self.log = LogManager(self.db)
        self.endpoint = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
        self.dias_coleta = dias_padrao
        self.max_workers = max_workers  # quantos "caixas" abertos ao mesmo tempo

        # Lock garante que dois workers não escrevam no banco ao mesmo tempo


        # Contador thread-safe de novos registros
        self._total_novos = 0
        self._counter_lock = threading.Lock()

        # Cada worker usa sua própria sessão HTTP (sessions não são thread-safe)
        self._session_local = threading.local()

    def _get_session(self):
        """Retorna uma sessão HTTP exclusiva para a thread atual."""
        if not hasattr(self._session_local, 'session'):
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            })
            self._session_local.session = session
        return self._session_local.session

    def get_certame_hash(self, item):
        payload = (
            f"{item.get('orgaoEntidade', {}).get('cnpj', '')}"
            f"{item.get('anoCompra')}"
            f"{item.get('numeroCompra')}"
            f"{item.get('unidadeOrgao', {}).get('codigoUnidade', '')}"
        )
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def _processar_pagina(self, id_tarefa, num_pagina, data_final_api):
        """
        Processa uma única página da API.
        Este método é executado em paralelo por múltiplos workers.
        Retorna o número de novos registros inseridos (0 em caso de erro).
        """
        params = {
            'dataFinal': data_final_api,
            'pagina': num_pagina,
            'tamanhoPagina': 50,
        }
        session = self._get_session()

        try:
            response = session.get(self.endpoint, params=params, timeout=60)

            if response.status_code == 200:
                try:
                    dados = response.json()
                    items = dados.get('data', [])
                    novos_pagina = 0
                    for item in items:
                        id_hash = self.get_certame_hash(item)
                        if self._persistir_bruto(id_hash, item):
                            novos_pagina += 1

                    self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'CONCLUIDO', 200)

                    # Atualiza contador global de forma segura entre threads
                    with self._counter_lock:
                        self._total_novos += novos_pagina

                    print(f"[✓] Página {num_pagina} concluída — {novos_pagina} novos | total: {self._total_novos}")
                    return novos_pagina

                except Exception as e_proc:
                    print(f"[!] Erro ao processar dados da página {num_pagina}: {e_proc}")
                    self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'ERRO', 998)
                    return 0

            elif response.status_code == 429:
                # Rate limit: marca como erro para ser reprocessado depois
                print(f"[!] Rate Limit na página {num_pagina}. Marcando para retry...")
                self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'ERRO', 429)
                time.sleep(5)  # pequena pausa só neste worker
                return 0

            else:
                print(f"[!] Página {num_pagina} retornou HTTP {response.status_code}")
                self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'ERRO', response.status_code)
                return 0

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"[!] Erro de conexão na página {num_pagina}: {e}")
            self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'ERRO', 999)
            return 0

    def coleta_diaria(self, dias_futuros=None):
        hoje = datetime.now()
        data_referencia = hoje.date()
        self._total_novos = 0  # reseta contador a cada execução

        dias = dias_futuros if dias_futuros is not None else self.dias_coleta
        data_limite = hoje + timedelta(days=dias)
        data_final_api = data_limite.strftime("%Y%m%d")
        data_para_exibir = data_limite.strftime("%d/%m/%Y")

        print(f"[*] Iniciando coleta central até: {data_para_exibir}")
        print(f"[*] Endpoint: {self.endpoint}")
        print(f"[*] Workers paralelos: {self.max_workers}")

        try:
            # --- ETAPA 1: Mapeamento (descobre quantas páginas existem) ---
            params_inicial = {
                'dataFinal': data_final_api,
                'pagina': 1,
                'tamanhoPagina': 50,
            }
            session = self._get_session()
            resp = session.get(self.endpoint, params=params_inicial, timeout=30)

            if resp.status_code == 200:
                total_paginas = resp.json().get('totalPaginas', 1)
                print(f"[*] Total de páginas mapeadas: {total_paginas}")
                self.db.registrar_mapeamento_diario_PNCP(data_referencia, total_paginas)
            else:
                print(f"[-] Falha ao acessar API para mapeamento: {resp.status_code}")
                return False

            # --- ETAPA 2: Coleta todas as tarefas pendentes de uma vez ---
            tarefas = []
            tarefa_no_banco=0
            while True:
                tarefa = self.db.get_proxima_pagina_PNCP(data_referencia)
                print(f'tarefa adicoionada{tarefa_no_banco+1}')
                if not tarefa:
                    break
                tarefas.append(tarefa)

            if not tarefas:
                print("[+] Nenhuma página pendente para hoje.")
            else:
                print(f"[*] {len(tarefas)} páginas para processar com {self.max_workers} workers...")

                # --- ETAPA 3: Processa todas as páginas em paralelo ---
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {
                        executor.submit(
                            self._processar_pagina,
                            t['id'],
                            t['numero_pagina'],
                            data_final_api
                        ): t['numero_pagina']
                        for t in tarefas
                    }

                    concluidas = 0
                    for future in as_completed(futures):
                        num_pagina = futures[future]
                        concluidas += 1
                        try:
                            future.result()
                        except Exception as e:
                            print(f"[!] Exceção não tratada na página {num_pagina}: {e}")

                        # Progresso a cada 50 páginas
                        if concluidas % 50 == 0:
                            print(f"[...] Progresso: {concluidas}/{len(tarefas)} páginas | {self._total_novos} novos registros")

            # --- ETAPA 4: Verifica se a coleta foi completa ---
            if self.db.verificar_conclusao_dia_PNCP(data_referencia):
                print(f"[🏆] Integridade confirmada! {self._total_novos} novos editais coletados.")
                return True
            else:
                print(f"[!] Coleta parcial. {self._total_novos} novos itens no banco, mas faltam páginas.")
                return False

        except Exception as e:
            self.log.registro('SISTEMA', 'COLETOR', 'CRITICAL', 'COL_FAIL', 'ERRO CATASTROFICO', str(e))
            print(f"[-] Erro crítico: {e}")
            return False

    def _persistir_bruto(self, id_hash, item):
        sql = '''
        INSERT INTO public.pncp_dados_brutos(
            identificador_certame, uf, objeto, dados_json)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (identificador_certame) DO NOTHING
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
                    cursor.execute(sql, (
                        id_hash,
                        uf,
                        objeto_texto,
                        json.dumps(item)
                    ))
                    connection.commit()
                    return cursor.rowcount > 0



        except Exception as e:
            print(f"Erro ao persistir item {id_hash}: {e}")
            return False
