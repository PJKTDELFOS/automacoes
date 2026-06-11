import requests
from engine_busca_pncp.config import Config

def handshake():
    print("[*] Executando Health Check na API do PNCP...")

    url_teste = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta?dataFinal=20260625&pagina=1&tamanhoPagina=1"

    # 🌟 O TRUNFO: Mapeia os Headers para simular o Chrome perfeitamente diante do WAF
    headers_fake = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://pncp.gov.br/"
    }

    proxy_dict = {
        "http": f"http://{Config.PROXY_HOST}:{Config.PROXY_PORT}",
        "https": f"http://{Config.PROXY_HOST}:{Config.PROXY_PORT}"
    }

    try:
        # Passamos os headers_fake na requisição
        response = requests.get(url_teste, proxies=proxy_dict, headers=headers_fake, timeout=15)
        response.raise_for_status()

        conteudo = response.text
        if "erro na comunicação" in conteudo.lower() or "hikari" in conteudo.lower():
            print("\n[❌ BLOQUEIO DA LARGADA] API do Governo está ONLINE, mas o BANCO DE DADOS deles caiu!")
            print(f"-> Resposta bruta do PNCP: {conteudo[:200]}...")
            return

        print("[✓] Health Check OK: API do PNCP respondendo perfeitamente.")
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        print(f"\n[❌ BLOQUEIO DA LARGADA] O servidor do PNCP cuspiu Erro HTTP {status_code}!")
        if status_code == 500:
            print("-> Motivo: Instabilidade interna ou estouro de pool no Java deles (HikariPool).")
        elif status_code in [502, 503, 504]:
            print("-> Motivo: Gateway caído. O servidor do governo desabou por completo.")
        print("[*] Operação abortada. Infraestrutura local protegida.\n")
        return

    except requests.exceptions.Timeout:
        print("\n[❌ BLOQUEIO DA LARGADA] Timeout severo na API do PNCP (Mais de 15 segundos sem sinal de vida).")
        print("-> Motivo: O servidor do governo travou a requisição em background ou o proxy está sofrendo gargalo.")
        print("[*] Operação abortada para evitar congelamento de threads zumbis.\n")
        return

    except requests.exceptions.RequestException as e:
        print(f"\n[⚠️ ALERTA DE REDE] Não foi possível alcançar o PNCP: {e}")
        print("-> Verifique se as credenciais ou a Whitelist do Proxy local estão ativas.")
        print("[*] Operação abortada por segurança de rede.\n")
        return