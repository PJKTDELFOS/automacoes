from appa_bot.forms import StakeholderForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from engine_campanha.disparador import Disparador_de_emails



class MainServices:

    @staticmethod
    def criar_stakeholders(form):

        novo_stakeholder = form.save(commit=False)
        novo_stakeholder.categoria = 'Interessado'
        novo_stakeholder.data_inicio_teste = timezone.now()
        novo_stakeholder.data_fim_teste = timezone.now() + timedelta(days=15)
        novo_stakeholder.save()

        try:
            mensageiro=Disparador_de_emails(novo_stakeholder.email,novo_stakeholder.nome_razaosocial)
            corpo=mensageiro.mensagem_boas_vindas(
                data_fim=novo_stakeholder.data_fim_teste,
                palavras=novo_stakeholder.palavras_chave,
                exclusoes=novo_stakeholder.palavras_exclusao,
                identificador=str(novo_stakeholder.identificador),
                uf=novo_stakeholder.UF
            )
            assunto = "🎉 Bem-vindo ao Appa! Seu teste começou."
            mensageiro._enviar_gmail(
                novo_stakeholder.email,assunto=assunto,corpo_html=corpo,
            )
        except Exception as e:
            print(f"Erro silencioso ao enviar e-mail de boas vindas: {e}")
        return novo_stakeholder

    @staticmethod
    def atualizar_stakeholder(form):
        stakeholder = form.save()
        return stakeholder



