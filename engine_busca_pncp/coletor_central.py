import json
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import time
import random

# Novos imports essenciais para a Engine de Navegador
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from engine_busca_pncp.db_manager import DBManager
from engine_busca_pncp.log_manager import LogManager
from engine_busca_pncp.config import Config


class ColetorCentral:
    def __init__(self, db_manager, dias_padrao=15, max_workers=5):
        self.db = db_manager
        self.log = LogManager(self.db)
        self.endpoint = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
        self.dias_coleta = dias_padrao
        self.max_workers = max_workers  # Quantidade de threads paralelas

        # Contador thread-safe de novos registros salvos
        self._total_novos = 0
        self._counter_lock = threading.Lock()

    def get_certame_hash(self, item):
        """Gera um ID único estável baseado nos metadados do certame."""
        id_oficial = item.get('numeroControlePNCP')
        if id_oficial:
            string_chave = str(id_oficial).strip()
        else:
            # 2. Plano B caso o governo envie um bloco corrompido sem o número de controle
            orgao = item.get('orgaoEntidade', {})
            cnpj = orgao.get('cnpj') or '00000000000000'
            ano = item.get('anoCompra') or '0000'
            seq = item.get('sequencialCompra') or '0'
            link = item.get('linkSistemaOrigem') or ''

            string_chave = f"{cnpj}-{ano}-{seq}-{link}"
        return hashlib.md5(string_chave.encode('utf-8')).hexdigest()

    def _criar_driver_headless(self):
        """Instancia um navegador Chrome invisível isolado e configurado com o Proxy da Webshare."""
        options = Options()
        options.add_argument("--headless=new")  # Força modo invisível dentro do Docker Linux
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--blink-settings=imagesEnabled=false")  # Ganha muita velocidade desativando imagens
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        # Injeta as configurações do Proxy diretamente na engine do navegador
        # proxy_server = f"{Config.PROXY_HOST}:{Config.PROXY_PORT}"
        # options.add_argument(f'--proxy-server=http://{proxy_server}')

        # Gerencia e baixa automaticamente a versão correta do ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver=webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(60)
        return driver

    def coleta_diaria(self):
        """Orquestrador principal do ciclo diário de raspagem de dados."""
        data_referencia = datetime.now().date()
        data_final_api = (datetime.now() + timedelta(days=self.dias_coleta)).strftime('%Y%m%d')

        print(f"[*] Iniciando coleta central até: {data_final_api}")
        print(f"[*] Endpoint: {self.endpoint}")
        print(f"[*] Workers paralelos: {self.max_workers}")

        self._total_novos = 0

        # --- ETAPA 1: Captura o mapeamento de total de páginas usando o Selenium ---
        driver = None

        try:
            driver = self._criar_driver_headless()
            # MUDANÇA DE OURO: Adicionado &ordenacao=asc para fixar a ordem das páginas iniciais
            url_mapeamento = f"{self.endpoint}?dataFinal={data_final_api}&pagina=1&tamanhoPagina=50&ordenacao=asc"
            driver.get(url_mapeamento)
            time.sleep(4)  # Janela de tempo pro WAF processar o Javascript e cookies iniciais

            # Quando o Chrome acessa um JSON, ele renderiza o texto puro dentro da tag body
            conteudo_bruto = driver.find_element("tag name", "body").text

            if "request rejected" in conteudo_bruto.lower() or "<html" in conteudo_bruto.lower():
                print("[-] O PNCP rejeitou a requisição inicial de mapeamento via Navegador.")
                driver.quit()
                return False

            dados = json.loads(conteudo_bruto)
            total_paginas = dados.get('totalPaginas', 0)
            print(f"[+] Mapeamento concluído: {total_paginas} páginas identificadas.")

            if total_paginas == 0:
                driver.quit()
                return True

            # Alimenta a tabela de controle de páginas (sua lógica original)
            self.db.registrar_mapeamento_diario_PNCP(data_referencia, total_paginas)
            driver.quit()

        except Exception as e_mapeamento:
            print(f"[-] Falha catastrófica no mapeamento inicial: {e_mapeamento}")
            if driver is not None:
                try:
                    driver.quit()
                except Exception as e:
                    print(f' falhando no mapeamento: {e}')
                    pass
            return False

        try:
            # --- ETAPA 2: Consome e esvazia a fila do banco de dados (Sua lógica mantida) ---
            tarefas = []
            while True:
                tarefa = self.db.get_proxima_pagina_PNCP(data_referencia)
                if not tarefa:
                    break
                tarefas.append(tarefa)
                print(f'[DEBUG] Tarefa adicionada à memória: {len(tarefas)} — página {tarefa["numero_pagina"]}')

            if not tarefas:
                print("[+] Nenhuma página pendente para processar hoje.")
                return True

            # --- ETAPA 3: Disparar os Workers paralelos no ThreadPoolExecutor com espaçamento ---
            print(f"[*] Processando {len(tarefas)} páginas com {self.max_workers} threads...")
            INTERVALO_ENTRE_WORKERS = 2  # Respiro em segundos para suavizar o consumo e o WAF

            futures = {}
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                for t in tarefas:
                    # Enfileira e dispara o worker para a página atual
                    future = executor.submit(self._processar_pagina, t['id'], t['numero_pagina'], data_final_api)
                    futures[future] = t

                    # Aplica o delay estratégico antes de disparar o próximo worker
                    time.sleep(INTERVALO_ENTRE_WORKERS)

                # Aguarda a conclusão de todos os que foram ativados
                for future in as_completed(futures):
                    try:
                        future.result(timeout=120)
                    except TimeoutError as e:
                        print(f"[-] Worker excedeu 120s — será reprocessado na repescagem.")

            # --- ETAPA 4: Rodadas de Repescagem de Erros (Corrigido contador de rodadas e adicionado delay) ---
            pendentes = True
            max_rodadas = 3
            rodada = 1
            while pendentes and rodada <= max_rodadas:
                retentar = []
                while True:
                    tarefa = self.db.get_proxima_pagina_PNCP(data_referencia)
                    if not tarefa:
                        break
                    retentar.append(tarefa)

                if not retentar:
                    break

                print(f"[↺] Rodada {rodada}/{max_rodadas} de recuperação para {len(retentar)} páginas que falharam...")

                futures_retentar = {}
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    for t in retentar:
                        future = executor.submit(self._processar_pagina, t['id'], t['numero_pagina'], data_final_api)
                        futures_retentar[future] = t

                        # Respiro idêntico na repescagem para manter a VPS fria
                        time.sleep(INTERVALO_ENTRE_WORKERS)

                    for future in as_completed(futures_retentar):
                        try:
                            future.result(timeout=120)
                        except TimeoutError as e:
                            print(f"[-] Worker excedeu 120s — será reprocessado na repescagem.")

                rodada += 1  # Incremento movido para o final do ciclo de forma correta

            # Verificação final de fechamento do dia
            if self.db.verificar_conclusao_dia_PNCP(data_referencia):
                self.log.registro('SISTEMA', 'COLETOR', 'INFO', 'COL_OK', 'SUCESSO',
                                  f'Coleta completa: {self._total_novos} novos registros.')
                print(f"[✓] Execução finalizada com Sucesso! Total de novos certames: {self._total_novos}")
                return True
            else:
                self.log.registro('SISTEMA', 'COLETOR', 'WARNING', 'COL_PARTIAL', 'COLETA INCOMPLETA',
                                  "Restam páginas com falha registradas.")
                print("[-] Varredura finalizada, mas ainda restam páginas com status de erro no banco.")
                return False

        except Exception as e:
            self.log.registro('SISTEMA', 'COLETOR', 'CRITICAL', 'COL_FAIL', 'ERRO CATASTROFICO', str(e))
            print(f"[-] Erro crítico no laço principal: {e}")
            return False

    def _processar_pagina(self, id_tarefa, num_pagina:int, data_final_api):
        """Worker das Threads: Abre um navegador próprio, resolve os cookies do WAF e persiste dados."""
        # MUDANÇA DE OURO: Adicionado &ordenacao=asc também nas requisições individuais das threads
        url_completa = f"{self.endpoint}?dataFinal={data_final_api}&pagina={num_pagina}&tamanhoPagina=50&ordenacao=asc"

        max_tentativas = 5

        for tentativa in range(1, max_tentativas + 1):
            driver = None
            try:
                # O jitter nativo ajuda a baralhar as requisições que chegam ao servidor
                time.sleep(random.uniform(0.5, 2))
                driver = self._criar_driver_headless()
                driver.get(url_completa)
                time.sleep(4)  # Aguarda a descriptografia e carregamento do JSON na tela

                conteudo_tela = driver.find_element("tag name", "body").text

                # Validação contra respostas falsas de bloqueio do Firewall
                if "request rejected" in conteudo_tela.lower() or "<html" in conteudo_tela.lower():
                    print(
                        f"[!] WAF interceptou a página {num_pagina}. Tentativa {tentativa}/{max_tentativas}. Recomeçando...")
                    driver.quit()
                    time.sleep(4)
                    continue

                if not conteudo_tela.startswith('{'):
                    print(f'fim da paginaçao real na {num_pagina}')
                    driver.quit()
                    self.db.atualizar_status_tarefa_PNCP(id_tarefa,'CONCLUIDO',204)
                    return 0

                # Transforma o texto extraído da tela em dicionário estruturado
                try:
                    dados = json.loads(conteudo_tela)
                except json.JSONDecodeError as e:
                    print(
                        f"[-] Instabilidade no servidor PNCP na página"
                        f" {num_pagina} ({str(e)}). A aguardar respiro... Tentativa {tentativa}/{max_tentativas}")
                    driver.quit()
                    time.sleep(8)
                    continue

                items = dados.get('data', [])
                num_items_recebidos=len(items)

                novos_pagina = 0

                for item in items:
                    id_hash = self.get_certame_hash(item)
                    if self._persistir_bruto(id_hash, item):
                        novos_pagina += 1

                # Atualiza a máquina de estados para Concluído no banco de dados
                self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'CONCLUIDO', 200)

                with self._counter_lock:
                    self._total_novos += novos_pagina

                print(
                    f"[✓] Página {num_pagina} concluída via Selenium — {novos_pagina} novos | Total Geral: {self._total_novos}")


                driver.quit()  # Fecha e mata o processo do Chrome da memória
                return novos_pagina

            except Exception as e_thread:
                print(f"[-] Erro na thread da página {num_pagina} (Tentativa {tentativa}/{max_tentativas}): {e_thread}")
                if driver is not None:
                    try:
                        driver.quit()
                    except Exception as e:
                        print(f' cai na falha final {e}')
                        pass
                time.sleep(4)

        # Caso todas as tentativas falhem, joga o status para ERRO para o seu botão de rollback manual agir
        self.db.atualizar_status_tarefa_PNCP(id_tarefa, 'ERRO', 500)
        return 0

    def _persistir_bruto(self, id_hash, item):
        """Mantém a gravação direta no banco PostgreSQL (Sua lógica mantida)."""
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