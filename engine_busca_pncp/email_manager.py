import resend
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from engine_busca_pncp.config import Config
from engine_busca_pncp.propriedades import Properties
from engine_busca_pncp.log_manager import LogManager
from engine_busca_pncp.db_manager import DBManager

import os



class EmailManager:
    def __init__(self,metodo='gmail'):
        self.metodo=metodo.lower()
        self.db = DBManager()
        self.logger = LogManager(self.db)
        if self.metodo =='resend':
            resend.api_key=Config.RESEND_API_KEY

    def enviar(self,cliente_dados,df_resultados,palavras_chave,uf,anexo_path):
        corpo_html=Properties.get_email_body(
            cliente=cliente_dados['nome'],
            total_encontrado=len(df_resultados),
            palavras_chave=palavras_chave,
            uf=uf,
            quantidade=len(df_resultados)
        )
        assunto=Properties.EMAIL_SUBJECT.format(cliente=cliente_dados['nome'],)
        destinatario=cliente_dados['email']

        if self.metodo=='resend':
            return self._enviar_resend(destinatario,assunto,corpo_html,anexo_path)
        else:
            return self._enviar_gmail(destinatario, assunto, corpo_html, anexo_path)

    def _enviar_resend(self,to,assunto,corpo_html,anexo_path):
        nome_arquivo=os.path.basename(anexo_path)
        with open(anexo_path,"rb")as f:
            anexo_payload={
                'filename':nome_arquivo,
                'content':list(f.read())
            }
        try:
            resultado=resend.Emails.send({
                'from': f'Appa <{Config.EMAIL_RESEND_FROM}>',
                'to': [to],
                'subject': assunto,
                'html': corpo_html,
                'attachments': [anexo_payload]
            })
            self.logger.registro(
                cliente=to,
                etapa='Envio email',
                nivel='Sucesso',
                codigo='Email enviado',
                mensagem='Resendo enviado com Sucesso',

            )

            return resultado
        except Exception as e:
            self.logger.registro(
                cliente=to,
                etapa='Envio email',
                nivel='falha',
                codigo='RESEND FAIL',
                mensagem=str(e),
            )
            return None



    def _enviar_gmail(self,to,assunto,corpo_html,anexo_path):
        msg=MIMEMultipart()
        msg['From']=Config.GMAIL_EMAIL_FROM
        msg['To']=to
        msg['Subject']=assunto
        msg.attach(MIMEText(corpo_html,'html'))

        with open (anexo_path,"rb")as f:
            part=MIMEBase('application','octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',f'attachment; filename="{Properties.FILE_PREFIX}.xlsx"')
            msg.attach(part)

        try:


            server=smtplib.SMTP('smtp.gmail.com',587)
            server.starttls()
            server.login(Config.GMAIL_EMAIL_FROM,Config.GMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()

            self.logger.registro(
                cliente=to,
                etapa='Envio email',
                nivel='Sucesso',
                codigo='Email enviado',
                mensagem='Gmail enviado',

            )
            return True
        except Exception as e:
            self.logger.registro(
                cliente=to,
                etapa='Envio email',
                nivel='falha',
                codigo='GMAIL FAIL',
                mensagem=str(e),
            )
            return False



