from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import time

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

# Visita o portal e espera o WAF validar
driver.get("https://pncp.gov.br")
time.sleep(5)

# Extrai cookies e user-agent do Chrome real
cookies = {c['name']: c['value'] for c in driver.get_cookies()}
user_agent = driver.execute_script("return navigator.userAgent")
print(f"User-Agent: {user_agent}")
print(f"Cookies: {list(cookies.keys())}")

driver.quit()

# Monta sessão com cookies reais
session = requests.Session()
session.headers.update({
    'User-Agent': user_agent,
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'pt-BR,pt;q=0.9',
    'Referer': 'https://pncp.gov.br/',
    'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
})
for name, value in cookies.items():
    session.cookies.set(name, value)

resp = session.get(
    "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta",
    params={
        "dataFinal": "20260610",
        "pagina": 1,
        "tamanhoPagina": 10,
        "codigoModalidadeContratacao": 6
    },
    timeout=30
)

print(f"\nStatus: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('content-type')}")
print(resp.text[:300])