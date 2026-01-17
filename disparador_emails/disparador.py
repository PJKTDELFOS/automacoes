
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from engine_busca_pncp.config import Config
from engine_busca_pncp.propriedades import Properties


class Disparador_de_emails:
    def __init__(self,email,cliente):
        self.email = email
        self.cliente = cliente

    def mensagem(self):
        html = f"""
    <html>
    <head>
    <style>
      body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
      .container {{ max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; }}
      .header {{ background-color: #2c3e50; color: #ffffff; padding: 20px; text-align: center; }}
      .content {{ padding: 30px; }}
      .benefit-box {{ background-color: #f9f9f9; border-left: 4px solid #27ae60; padding: 15px; margin-bottom: 20px; }}
      .instruction-box {{ background-color: #fff3cd; border: 1px solid #ffeeba; padding: 15px; border-radius: 5px; margin-top: 20px; }}
      .dev-section {{ background-color: #f4f7f6; padding: 20px; border-radius: 5px; margin-top: 30px; border-left: 4px solid #2c3e50; font-size: 14px; }}
      .price-tag {{ text-align: center; font-size: 24px; color: #27ae60; font-weight: bold; margin: 20px 0; }}
      .button {{ display: block; width: 220px; margin: 0 auto; padding: 15px; background-color: #27ae60; color: white !important; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold; }}
      .footer {{ font-size: 11px; color: #777; text-align: center; padding: 20px; }}
    </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1 style="color: #ffffff; margin: 0;">Sua busca por editais agora é inteligente</h1>
        </div>
        <div class="content">
          <p>Olá, <strong>{self.cliente}</strong>,</p>
          <p>Você sabia que uma empresa gasta, em média, <strong>4 horas por dia</strong> apenas para buscar e organizar editais? Isso representa mais de 80 horas mensais perdidas em processos manuais.</p>

          <p>Desenvolvemos uma solução de <strong>Inteligência em Licitações</strong> para encerrar a era dos boletins arcaicos. Diferente das ferramentas de mercado, onde você paga caro para ter mais trabalho de triagem, nossa tecnologia entrega <strong>oportunidades prontas para análise</strong>.</p>

          <h3>O diferencial para o seu negócio:</h3>
          <div class="benefit-box">
            <ul style="margin: 0; padding-left: 20px;">
              <li><strong>Zero Retrabalho:</strong> Nosso algoritmo identifica e descarta automaticamente licitações repetidas ou que você já recebeu. Você foca apenas no que é novidade.</li>
              <li><strong>Cronograma Pronto:</strong> Chega de copiar e colar. Você recebe o cronograma organizado em Excel  usando as mais modernas tecnologias de analise de dados, pronto para decidir o lance.</li>
              <li><strong>Filtro de Alta Precisão:</strong> Monitoramento 24/7 no PNCP focado estritamente no seu nicho, eliminando o ruído de editais irrelevantes.</li>
              <li><strong>Foco em Resultados:</strong> Substituímos o trabalho repetitivo por tempo livre para você analisar a viabilidade e vencer propostas.</li>
            </ul>
          </div>

          <h3 style="color: #2c3e50;">Inicie seu Teste Gratuito e Sem Compromisso</h3>
          <p>Validar a eficiência na prática é o melhor caminho. Receba nossas atualizações e sinta a diferença no seu dia a dia.</p>

          <div class="instruction-box">
            <strong>Como configurar seu teste:</strong><br>
            Clique no botão abaixo ou responda a este e-mail enviando as <strong>palavras-chave</strong> do seu setor (ex: "manutenção", "obras", "TI", "limpeza").
          </div>

          <p>Após o período de teste, a assinatura para manter sua operação automatizada é de apenas:</p>
          <div class="price-tag">R$ 99,90 / mês</div>

          <a href="mailto:boletinlicitacao@gmail.com?subject=Tenho Interesse no Teste do Robo" class="button">QUERO TESTAR GRÁTIS</a>

          <div class="dev-section">
            <strong>Especialista Responsável:</strong><br>
            Meu nome é <strong>Albert Pimentel França</strong>, desenvolvedor com <strong>mais de 10 anos de experiência direta na área de licitações públicas</strong>. 
            <br><br>
            Comprometido com a aplicação prática de soluções eficientes, utilizo Python, Django e análise de dados para automatizar processos administrativos. Minha missão é unir <strong>experiência de mercado e tecnologia</strong> para entregar precisão e alta qualidade aos meus clientes.
          </div>

          <p style="margin-top: 30px;">Transforme a burocracia em vantagem competitiva.</p>
          <p>Atenciosamente,<br><strong>Albert Pimentel França-Desenvolvedor</strong></p>
        </div>
        <div class="footer">
          Esta é uma mensagem de convite para teste de software de automação comercial.<br>
          Caso não deseje mais receber nossos comunicados, responda "Sair".
        </div>
      </div>
    </body>
    </html>
    """
        return html

    def _enviar_gmail(self, to, assunto, corpo_html):
        msg = MIMEMultipart()
        msg['From'] = Config.GMAIL_EMAIL_FROM
        msg['To'] = to
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo_html, 'html'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(Config.GMAIL_EMAIL_FROM, Config.GMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()

            return True
        except Exception as e:
            print(f'erro {e}')

            return False




