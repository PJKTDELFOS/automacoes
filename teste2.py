import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from engine_busca_pncp.config import Config

# 1. Credenciais reais da sua Webshare
PROXY_HOST = Config.PROXY_HOST
PROXY_PORT = Config.PROXY_PORT
PROXY_USER = Config.PROXY_USER
PROXY_PASSWORD = Config.PROXY_PASSWORD

print("[*] Iniciando teste de bypass do WAF via Engine de Navegador (Selenium)...")

# 2. Configurações do Chrome invisível
options = Options()
options.add_argument("--headless=new")  # Força o modo 100% invisível
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--blink-settings=imagesEnabled=false")  # Desliga imagens para ser ultra rápido

# 3. Injeta a URL do Proxy com autenticação diretamente no Chrome
# O Chrome aceita o proxy direto por argumento de inicialização
proxy_server = f"{PROXY_HOST}:{PROXY_PORT}"
options.add_argument(f'--proxy-server=http://{proxy_server}')

# Executa o download automático do driver compatível com o seu Chrome atual
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Endpoint da API do governo que estava dando erro
url_api = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta?dataFinal=20260610&pagina=1&tamanhoPagina=10"

try:
    print(f"[*] Acessando a API passando pelo Proxy da Webshare...")
    driver.get(url_api)

    # Aguarda 5 segundos para o WAF executar o Javascript e processar os cookies na primeira chamada
    print("[*] Aguardando 5 segundos para o Firewall processar os cookies...")
    time.sleep(5)

    # Quando o Chrome acessa um link que retorna JSON, ele joga o texto dentro de uma tag <pre>
    conteudo_tela = driver.find_element("tag name", "body").text

    print(f"\n[+] Status da resposta visualizado na tela.")

    # Validação: Se contiver tags HTML ou a frase de rejeição, o WAF barrou
    if "request rejected" in conteudo_tela.lower() or "<html" in conteudo_tela.lower():
        print("\n[-] O Firewall do Governo ainda barrou o navegador. Conteúdo:")
        print(conteudo_tela[:400])
    else:
        print("\n[✓] SUCESSO ABSOLUTO! O navegador passou pelo WAF e capturou o JSON:")
        # Tenta parsear o texto da tela como JSON real do Python
        dados_json = json.loads(conteudo_tela)
        print(f"[*] Total de itens capturados: {len(dados_json.get('data', []))}")
        print(json.dumps(dados_json, indent=2, ensure_ascii=False)[:600])

except Exception as e:
    print(f"\n[-] Erro durante a execução do teste com Selenium: {e}")

finally:
    # Garante que o processo do Chrome na memória seja fechado
    driver.quit()
    print("\n[*] Navegador encerrado.")