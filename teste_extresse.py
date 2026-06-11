import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# CONFIGURAÇÃO DO ESTRESSE
NUM_THREADS = 5  # Quantidade de janelas paralelas batendo juntas
PAGINAS_TESTE = range(1, 100)  # Vai tentar puxar as 10 primeiras páginas ao mesmo tempo


def worker_estresse(num_pagina):
    """Worker isolado: simula o comportamento exato de uma thread do APPA."""
    url_api = f"https://pncp.gov.br/api/consulta/v1/contratacoes/proposta?dataFinal=20260610&pagina={num_pagina}&tamanhoPagina=10"

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--blink-settings=imagesEnabled=false")

    # ATENÇÃO: Deixando SEM proxy para forçar o IP de casa no limite do WAF
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    start_time = time.time()
    try:
        print(f"[*] Thread [Página {num_pagina}] disparada...")
        driver.get(url_api)

        # Simula o tempo de descriptografia do JavaScript
        time.sleep(4)

        conteudo_tela = driver.find_element("tag name", "body").text
        duration = time.time() - start_time

        if "request rejected" in conteudo_tela.lower() or "<html" in conteudo_tela.lower():
            print(f"[-] [Página {num_pagina}] ❌ BARRAÇÃO DETECTADA PELO WAF ({duration:.2f}s)")
            return num_pagina, "WAF_BLOCK"

        # Valida se o conteúdo é um JSON válido
        dados = json.loads(conteudo_tela)
        print(f"[✓] [Página {num_pagina}]  SUCESSO! Capturados {len(dados.get('data', []))} itens ({duration:.2f}s)")
        return num_pagina, "SUCCESS"

    except json.JSONDecodeError as e_erro_json:
        print(f"[-] [Página {num_pagina}] ⚠️ DADO CORROMPIDO (JSONDecodeError - Extra data ou Vazio)")
        print(f" erro: {e_erro_json}")
        return num_pagina, "JSON_ERROR"
    except Exception as e:
        print(f"[-] [Página {num_pagina}] 💥 ERRO CRÍTICO NA THREAD: {e}")
        return num_pagina, "FATAL_ERROR"
    finally:
        driver.quit()


# DISPARADOR DO ATAQUE DE TESTE
print(f"================================================================")
print(f"🚀 INICIANDO TESTE DE ESTRESSE CONCORRENTE NO PNCP")
print(f"🔥 Threads em paralelo: {NUM_THREADS} | Páginas mapeadas: {len(PAGINAS_TESTE)}")
print(f"================================================================")

resultados = {"SUCCESS": 0, "WAF_BLOCK": 0, "JSON_ERROR": 0, "FATAL_ERROR": 0}
start_global = time.time()

with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    futures = {executor.submit(worker_estresse, p): p for p in PAGINAS_TESTE}

    for future in as_completed(futures):
        _, status = future.result()
        resultados[status] += 1

duracao_total = time.time() - start_global
print(f"\n================================================================")
print(f"📊 RELATÓRIO FINAL DE ESTRESSE (Duração: {duracao_total:.2f}s)")
print(f"================================================================")
print(f" Sucessos: {resultados['SUCCESS']}")
print(f" Bloqueios de WAF: {resultados['WAF_BLOCK']}")
print(f" Instabilidades de JSON: {resultados['JSON_ERROR']}")
print(f" Falhas de Conexão: {resultados['FATAL_ERROR']}")
print(f"================================================================")