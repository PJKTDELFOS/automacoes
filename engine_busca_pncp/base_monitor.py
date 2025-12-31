from email.mime.text import MIMEText
import requests
import pandas as pd
from datetime import datetime,timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from keys import KEYS
from abc import ABC, abstractmethod
from engine_busca_pncp.db_manager import DBManager
from textwrap import dedent
import time
import unicodedata


class BaseMonitor(ABC):

    def __init__(self, cliente,palavras_chave,email_destino,uf):
        self.cliente = cliente
        self.palavras_chave = [p.lower() for p in palavras_chave]
        self.email_destino = email_destino
        self.hoje=datetime.now()
        self.dados_filtrados=[]
        self.uf=uf if uf else ''
        self.db=DBManager()


    def gerar_id_unico(self,item):
        cnpj = item.get('orgaoEntidade', {}).get('cnpj', '00000000000000')
        ano = item.get('anoCompra', '')
        numero = item.get('numeroCompra', '')
        identificador = f'{cnpj}_{ano}_{numero}'
        return identificador

    def verificar_duplicidade(self,item):
        try:
            identificador = self.gerar_id_unico(item)
            return self.db.ja_enviado(identificador,self.cliente)
        except Exception as e:
            print(f"[{self.cliente}] Erro ao verificar duplicidade: {e}")
            return False
    @property
    def mensagem(self):
        quantidade=len(self.dados_filtrados)
        hora_dia=datetime.now().hour
        termos_str = ", ".join([t.upper() for t in self.palavras_chave])
        saudacao=None
        if hora_dia>=18:
            saudacao='Boa noite'
        elif hora_dia<18 and hora_dia>=12:
            saudacao='Boa tarde'
        elif hora_dia<12:
            saudacao='Bom dia'

        corpo = f"""
                {saudacao},

                Este é o seu relatório diário de monitoramento do PNCP para o cliente **{self.cliente}**.

                **Resumo da rodada:**
                - **Data:** {self.hoje.strftime('%d/%m/%Y')}
                - **Filtro Geográfico:** {self.uf if self.uf else 'Nacional'}
                - **Novas oportunidades encontradas:** {quantidade}
                - **Termos monitorados:** {termos_str}

                Em anexo, você encontrará a planilha detalhada com os links diretos para os certames e prazos de entrega de proposta.

                ---
                *Este é um e-mail automático enviado pelo seu Sistema de Monitoramento de Licitações.*
                """



        return dedent(corpo)


    def busca_na_api(self,dias_futuros=15):
        pagina_atual = 1
        total_paginas = 1
        data_limite=self.hoje+timedelta(days=dias_futuros)
        data_final_api = data_limite.strftime("%Y%m%d")

        headers = {
            'accept': 'application/json',
            "User-Agent": "Mozilla/5.0"
        }
        base_url = "https://pncp.gov.br/api/consulta"
        endpoint = f"{base_url}/v1/contratacoes/proposta"
        dados_brutos=[]
        while pagina_atual <= total_paginas:
            params = {
                'dataFinal': data_final_api,
                'uf': self.uf,  # paga pesquisas a nivel nacional so apagar o # do lado da uf
                'pagina': pagina_atual,
                'tamanhoPagina': 50,  # ajuste do tamanho da pagina, so vai ate 50
            }
            print(f' {self.cliente} consultando a pagina {pagina_atual}')
            response=requests.get(endpoint,params=params, headers=headers)
            response.raise_for_status()
            dados_json = response.json()
            total_paginas = dados_json.get('totalPaginas', 1)
            dados_brutos.extend(dados_json.get('data',[]))
            pagina_atual += 1
        return dados_brutos
    @abstractmethod
    def filtros(self,dados_brutos):
        pass

    @property
    def nome_arquivo(self):
        cliente_limpo=self.cliente.replace(' ','_')
        cliente_limpo = unicodedata.normalize('NFKD', cliente_limpo).encode('ASCII', 'ignore').decode('ASCII')
        data_str=self.hoje.strftime("%d_%m_%Y")
        nomearquivo=f'cronograma_{cliente_limpo}_{data_str}.xlsx'
        return nomearquivo


    @abstractmethod
    def gerar_planilha(self):
        if not self.dados_filtrados:
            return False
        try:
            df=pd.DataFrame(self.dados_filtrados)
            df.to_excel(self.nome_arquivo,index=False)
            return True
        except Exception as e:
            print(f"erro ao gerar planilha base {e}")
            return False


    def enviar(self):
        meu_email = 'boletinlicitacao@gmail.com'
        minha_senha = KEYS.senha
        email_destinho = self.email_destino

        msg = MIMEMultipart()
        msg['From'] = meu_email
        msg['To'] = email_destinho
        msg['Subject'] = f'Cronograma diario PNCP-{datetime.now().strftime("%d/%m/%Y")}'
        corpo = self.mensagem
        msg.attach(MIMEText(corpo, 'plain'))
        nome_base=os.path.basename(self.nome_arquivo)

        with open(self.nome_arquivo, 'rb') as arquivo:
            payload=arquivo.read()
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(payload)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{nome_base}"')
            msg.attach(part)
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(meu_email, minha_senha)
            server.sendmail(meu_email, email_destinho, msg.as_string())
            server.quit()
            print(f'Email enviado com sucesso! para {email_destinho}')
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            
            
    def executar(self):
        self.ids_a_registrar=[]
        self.dados_filtrados=[]
        print(f"\n" +"="*50)
        print(F"INICIANDO MONITORAMENTO :{self.cliente}")
        print("="*50)

        try:
            brutos=self.busca_na_api()
            self.filtros(brutos)


            if len(self.dados_filtrados)>0:
                print(f" [+] SUCESSO: {len(self.dados_filtrados)} certames encontrados.")

                if self.gerar_planilha():
                    print(f" [+] PLANILHA GERADA: {self.nome_arquivo}")
                    print(" [!] Aguardando liberação do sistema de arquivos...")
                    time.sleep(2)
                    self.enviar()
                    for id_licitacao in self.ids_a_registrar:
                        self.db.registro_envio(id_licitacao, self.cliente)
                    print(f" [+] {len(self.ids_a_registrar)} novos registros salvos no DB.")
                    print(f" [+] FLUXO DE ENVIO CONCLUÍDO.")
                else:
                    print(f" [!] ALERTA: Falha ao gerar a planilha para {self.cliente}.")
            else:
                print(f'{self.cliente} : Nenhuma oportunidade encontrada para os filtros')
        except requests.exceptions.RequestException as e:
            print(
                f'{self.cliente}: erro de conexão, não foi possivel acessar o PNCP, detalhes {e}'
            )
        except Exception as e:
            print(
                f'{self.cliente} Erro inesperado {e}'
            )
        finally:
            print(f' Finalizado {self.cliente}')
            print("="*50)






