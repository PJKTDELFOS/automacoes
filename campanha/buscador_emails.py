import time
import requests
from engine_busca_pncp.db_manager import DBManager


class  BuscadorEmails:
    def __init__(self):
        self.db_manager = DBManager()
        self.api_url="https://brasilapi.com.br/api/cnpj/v1/{}"

    def consultar_api(self,cnpj):
        cnpj_limpo=str(cnpj).replace('.', '').replace('/', '').replace('-', '')
        try:
            print(f"   🔍 Consultando BrasilAPI: {cnpj_limpo}...")
            response=requests.get(self.api_url.format(cnpj_limpo),timeout=10)
            if response.status_code == 200:
                dados= response.json()
                email=dados.get('email',None)
                if email:
                    print(f"      📨 E-mail BRUTO recebido: '{email}'")
                else:
                    print("      ⚠️ JSON veio sem campo 'email' ou vazio.")
                if email and '@' in email:
                    if any(x in email.lower() for x in ['contabil', 'contador', 'fiscal', 'escritorio']):
                        print(f"      ⚠️ E-mail de contador ignorado: {email}")
                        return None
                    return email.lower()
            elif response.status_code == 404:
                print("      ❌ CNPJ não encontrado na Receita.")
            elif response.status_code == 429:
                print("      ⏳ Rate Limit (Muitas requisições). Pausando 15s...")
                time.sleep(15)
        except Exception as e:
            print(f"      ❌ Erro de conexão: {e}")

        return None
    def iniciar(self):
        print("🏭 Iniciando Enriquecimento de Leads...")
        while True:
            pendentes=self.db_manager.get_leads_para_enriquecimento(limite=50)
            if not pendentes:
                print("💤 Nada para fazer. Todos os CNPJs já foram processados.")
                break
            for cnpj,razao in pendentes:
                print(f"👉 Processando: {razao} ({cnpj})")
                email_encontrado=self.consultar_api(cnpj)
                if email_encontrado:
                    print(f"      ✅ SUCESSO! E-mail: {email_encontrado}")
                    self.db_manager.atualizar_led_enriquecido(cnpj,email_encontrado)
                else:
                    print("      🗑️ Sem e-mail válido.")
                    self.db_manager.marcar_processado_sem_sucesso(cnpj)
                time.sleep(2)


if __name__ == "__main__":
    robo = BuscadorEmails()
    robo.iniciar()