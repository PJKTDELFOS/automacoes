import json
from email.mime.text import MIMEText
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
from engine_busca_pncp.log_manager import LogManager
from textwrap import dedent
import unicodedata

class BaseMonitor(ABC):

    def __init__(self, cliente,palavras_chave,email_destino,uf):
        self.cliente = cliente
        self.palavras_chave = [p.lower() for p in palavras_chave]
        self.email_destino = email_destino
        self.hoje=datetime.now()
        self.dados_filtrados=[]
        self.ids_a_registrar=[]
        self.uf=uf if uf else ''
        self.db=DBManager()
        self.logger=LogManager(self.db)



    def busca_db_central(self):
        condicoes=' OR '.join(
            ["objeto ILIKE %s" for _ in self.palavras_chave]
        )
        query=f'SELECT identificador_certame,dados_json from public.pncp_dados_brutos where {condicoes} '
        params=[
            f'%{p}%' for p in self.palavras_chave
        ]
        if self.uf:
            query+=' AND uf = %s'
            params.append(self.uf)
        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, tuple(params))
                    rows=cursor.fetchall()
                    return[
                        (r[0],r[1]) for r in rows
                    ]

        except Exception as e:
            self.logger.registro(
                self.cliente,
                "DB_CACHE",
                "ERROR",
                "READ_CACHE_ERR",
                "Falha ao ler cache central",
                e

            )
            return []
    def filtrar_novidades(self,resultados_cache):
        self.dados_filtrados=[]
        self.ids_a_registrar=[]
        for id_hash,dados_json in resultados_cache:
            if not self.db.ja_enviado(id_hash,self.cliente):
                item=dados_json if isinstance(dados_json,dict) else json.loads(dados_json)
                self.dados_filtrados.append(item)
                self.ids_a_registrar.append(id_hash)

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
        try:
            dados_brutos=self.busca_db_central()
            self.filtrar_novidades(dados_brutos)
            if not self.dados_filtrados:
                self.logger.registro(self.cliente,"FILTRO", "INFO",
                                     "EMPTY", "Nenhuma novidade encontrada.")
                return
            if self.gerar_planilha():
                try:
                    self.enviar()
                    for id_hash in self.ids_a_registrar:
                        self.db.registro_envio(id_hash,self.cliente)
                    self.logger.registro(self.cliente,"EMAIL",
                                         "SUCCESS", "SENT",
                                         f"Enviado: {len(self.dados_filtrados)} itens.")
                except Exception as e_envio:
                    self.logger.registro(self.cliente,"EMAIL", "ERROR", "SMTP_FAIL", "Falha no disparo", e_envio)


        except Exception as e_geral:
            self.logger.registro(self.cliente, "SISTEMA", "CRITICAL", "FLOW_ERR", "Erro no fluxo principal", e_geral)
        finally:
            if hasattr(
                self, 'nome_arquivo'
            ) and os.path.exists(self.nome_arquivo):
                os.remove(self.nome_arquivo)




