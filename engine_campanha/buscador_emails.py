import time
import requests
from engine_busca_pncp.db_manager import DBManager


class  BuscadorEmails:
    def __init__(self):
        self.db_manager = DBManager()
        self.brasil_api_url="https://brasilapi.com.br/api/cnpj/v1/{}"
        self.api_cnpj_ws="https://publica.cnpj.ws/cnpj/{}"

    def validar_email(self,email):
        if email and '@' in email:
            if any(x in email.lower() for x in ['contabil', 'contador', 'fiscal', 'escritorio']):
                print(f"      ⚠️ E-mail de contador ignorado: {email}")
                return None
            return email.lower()
        return None

    def validar_telefone(self,ddd_ou_completo,numero=None):
        resultado=None
        if numero:
            num_limpo=str(numero).strip().replace('-','').replace('.','').replace(' ','')
            ddd_limpo=str(ddd_ou_completo).strip() if ddd_ou_completo else ''
            resultado= f'({ddd_limpo}){num_limpo}'
        elif ddd_ou_completo:
            resultado=str(ddd_ou_completo).strip()
        if not resultado or len(resultado)<8:
            return None
        return resultado



    def consultar_api(self,cnpj):
        cnpj_limpo=str(cnpj).replace('.', '').replace('/', '').replace('-', '')
        email_validado=None
        telefone_validado=None
        try:
            print(f"   🔍 [1/2] Tentando BrasilAPI: {cnpj_limpo}...")
            response=requests.get(self.brasil_api_url.format(cnpj_limpo),timeout=5)
            if response.status_code==200:
                dados=response.json()
                email_bruto=dados.get('email',None)
                email_validado=self.validar_email(email_bruto)
                if email_validado:
                    print(f"      🔹 BrasilAPI trouxe E-mail: {email_validado}")

                telefone_bruto=dados.get('ddd_telefone_1','')
                telefone_validado=self.validar_telefone(telefone_bruto)
                if telefone_validado:
                    print(f"      🔹 BrasilAPI trouxe Telefone: {telefone_validado}")

            elif response.status_code==404:
                 print("      ⏳ email nao encontrado...")
        except Exception as e:
            print(f"      ⚠️ Erro BrasilAPI: {e}")
        if email_validado and telefone_validado:
            print(f"      ✅ Achou na BrasilAPI: {email_validado},{telefone_validado}")
            return email_validado, telefone_validado, 2

        try:
            print(f"      🕵️ [2/2] BrasilAPI falhou/vazia. Tentando CNPJ.ws...")
            response=requests.get(self.api_cnpj_ws.format(cnpj_limpo),timeout=10)
            espera_obrigatoria=22
            if response.status_code==200:
                dados=response.json()
                estabelecimento=dados.get('estabelecimento',{})
                if not email_validado:

                    email_bruto=estabelecimento.get('email',None)
                    email_novo=self.validar_email(email_bruto)
                    if email_novo:
                        email_validado=email_novo
                        print(f"      ✅ CNPJ.ws completou o E-mail: {email_validado}")
                if not telefone_validado:

                    ddd=estabelecimento.get('ddd1')
                    numero=estabelecimento.get('telefone1')
                    telefone_novo=self.validar_telefone(ddd,numero)
                    if telefone_novo:
                        telefone_validado=telefone_novo
                        print(f"      ✅ CNPJ.ws completou o Telefone: {telefone_validado}")


            elif response.status_code==429:
                print("      🛑 Rate Limit CNPJ.ws (Muitas requisições).")
                # Se tomou rate limit aqui, tem que esperar mais
                return email_validado,telefone_validado, 60
            if email_validado or telefone_validado:
                print('completado na cnpj.ws')
                return email_validado,telefone_validado,22
            else:
                return None,None,espera_obrigatoria

        except Exception as e:
            print(f"      ❌ Erro CNPJ.ws: {e}")
            return email_validado, telefone_validado, 22

    def iniciar(self):
        print("🏭 Iniciando Enriquecimento HÍBRIDO (BrasilAPI + CNPJ.ws)...")

        while True:
            pendentes = self.db_manager.get_leads_para_enriquecimento(limite=50)
            if not pendentes:
                print("💤 Nada para fazer. Todos os CNPJs já foram processados.")
                break
            for cnpj, razao in pendentes:
                email_encontrado,telefone,tempo_pausa=self.consultar_api(cnpj)
                if email_encontrado or telefone:
                    self.db_manager.atualizar_led_enriquecido(cnpj,email_encontrado,telefone)
                else:
                    self.db_manager.marcar_processado_sem_sucesso(cnpj)
                if tempo_pausa>2:
                    print(f"      ⏳ Pausando {tempo_pausa}s para respeitar a API...")
                time.sleep(tempo_pausa)



if __name__ == "__main__":
    robo = BuscadorEmails()
    robo.iniciar()