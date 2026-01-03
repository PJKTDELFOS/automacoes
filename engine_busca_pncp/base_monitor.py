import json
from email.mime.text import MIMEText
import pandas as pd
from datetime import datetime
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
import io

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
        query=f'SELECT identificador_certame,dados_json from public.pncp_dados_brutos where ({condicoes}) '
        params=[
            f'%{p}%' for p in self.palavras_chave
        ]
        if self.uf:
            if isinstance(self.uf,list):
                placeholders=', '.join(['%s']*len(self.uf))
                query+=f' and uf in ({placeholders})'
                params.extend([u.upper() for u in self.uf])
            else:
                query += ' AND uf = %s'
                params.append(self.uf.upper())

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

    def gerar_planilha(self):
        if not self.dados_filtrados:
            return None
        try:
            df=pd.DataFrame(self.dados_filtrados)
            output=io.BytesIO()

            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)
            return output

        except Exception as e:
            self.logger.registro(self.cliente, "EXCEL", "ERROR", "BIT_ERR", "Falha em memória", e)
            return None


    def enviar(self,buffer_excel):
        meu_email = 'boletinlicitacao@gmail.com'
        minha_senha = KEYS.senha
        email_destinho = self.email_destino

        msg = MIMEMultipart()
        msg['From'] = meu_email
        msg['To'] = email_destinho
        msg['Subject'] = f'Cronograma diario PNCP-{datetime.now().strftime("%d/%m/%Y")}'
        corpo = self.mensagem
        msg.attach(MIMEText(corpo, 'html'))
        # nome_base=os.path.basename(self.nome_arquivo)

        try:
            part=MIMEBase('application', 'octet-stream')
            part.set_payload(buffer_excel.getvalue())
            encoders.encode_base64(part)
            nome_exibicao=self.nome_arquivo
            part.add_header('Content-Disposition', f'attachment; filename="{nome_exibicao}"')
            msg.attach(part)
        except Exception as e:
            print(f"Erro ao anexar arquivo em memória: {e}")
            return False
        try:
            server=smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(meu_email, minha_senha)
            server.sendmail(meu_email, email_destinho, msg.as_string())
            server.quit()
            print(f'[+] Email enviado com sucesso para {email_destinho} (Via RAM)')
            return True
        except Exception as e:
            print(f"[-] Erro ao enviar e-mail: {e}")
            raise e

    def executar(self):
        try:
            dados_brutos=self.busca_db_central()
            self.filtrar_novidades(dados_brutos)
            if not self.dados_filtrados:
                self.logger.registro(self.cliente,"FILTRO", "INFO",
                                     "EMPTY", "Nenhuma novidade encontrada.")
                return
            self.filtros(self.dados_filtrados)
            buffer=self.gerar_planilha()

            if buffer:
                try:
                    self.enviar(buffer)
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

    @property
    def mensagem(self):
        quantidade = len(self.dados_filtrados)
        dia=datetime.now()
        dia_do_mes = datetime.now().strftime('%d/%m/%Y')
        hora_dia = datetime.now().hour
        minuto=dia.minute
        termos_str = ", ".join([t.upper() for t in self.palavras_chave])
        saudacao = None
        if hora_dia >= 18:
            saudacao = 'Boa noite'
        elif hora_dia < 18 and hora_dia >= 12:
            saudacao = 'Boa tarde'
        elif hora_dia < 12:
            saudacao = 'Bom dia'


        cor_primaria = "#2c3e50"
        cor_destaque = "#3498db"
        html = f"""
            <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
                    <div style="background-color: {cor_primaria}; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0; font-size: 20px;">Relatório de Oportunidades PNCP</h1>
                        <p style="margin: 5px 0 0 0; opacity: 0.8;">Monitoramento Inteligente de Licitações</p>
                    </div>

                    <div style="padding: 20px;">
                        <p>Olá, <strong>{self.cliente}</strong>,</p>
                        <p>Identificamos novas oportunidades no PNCP que coincidem com o seu perfil de busca.</p>

                        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background-color: #f9f9f9;">
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Hora envio:</strong></td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{hora_dia}:{minuto}</td>
                            </tr>
                             <tr>
                                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Data:</strong></td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{dia_do_mes}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Oportunidades:</strong></td>
                                <td style="padding: 10px; border: 1px solid #ddd; color: {cor_destaque}; font-weight: bold;">{quantidade} encontradas</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Filtro:</strong></td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{self.uf if self.uf else 'Brasil (Nacional)'}</td>
                            </tr>
                        </table>

                        <p style="font-size: 14px;"><strong>Termos monitorados nesta rodada:</strong><br>
                        <span style="color: #666;">{termos_str}</span></p>

                        <div style="background-color: #fff3cd; border-left: 5px solid #ffecb5; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-size: 14px; color: #856404;">
                                <strong>Importante:</strong> Os detalhes completos, prazos e links diretos estão disponíveis na planilha em anexo.
                            </p>
                        </div>
                    </div>

                    <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 12px; color: #999;">
                        <p style="margin: 0;">Este é um serviço automatizado. Por favor, não responda a este e-mail.</p>
                        <p style="margin: 5px 0 0 0;">&copy; 2026 Seu Sistema de Monitoramento</p>
                    </div>
                </div>
            </body>
            </html>
            """

        return  html #dedent(corpo)

    @abstractmethod
    def filtros(self, dados_brutos):
        pass

    @property
    def nome_arquivo(self):
        cliente_limpo = self.cliente.replace(' ', '_')
        cliente_limpo = unicodedata.normalize('NFKD', cliente_limpo).encode('ASCII', 'ignore').decode('ASCII')
        data_str = self.hoje.strftime("%d_%m_%Y")
        nomearquivo = f'cronograma_{cliente_limpo}_{data_str}.xlsx'
        return nomearquivo





