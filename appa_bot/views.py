from django.shortcuts import render,get_object_or_404,redirect
from .models import Stakeholder,logAcao
from.forms import StakeholderForm,AtualizarStakeHolderForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from engine_campanha.disparador import Disparador_de_emails
from appa_bot.repository import ClienteRepository



# Create your views here.


def pagina_inicial_landing_page(request):

    if request.method == "POST":
        form=StakeholderForm(request.POST)
        if form.is_valid():

            novo_stakeholder=form.save(commit=False)
            novo_stakeholder.categoria='Interessado'
            novo_stakeholder.data_inicio_teste=timezone.now()
            novo_stakeholder.data_fim_teste=timezone.now()+timedelta(days=15)
            novo_stakeholder.save()

            try:
                mensageiro = Disparador_de_emails( novo_stakeholder.email,novo_stakeholder.nome_razaosocial)
                corpo_email = mensageiro.mensagem_boas_vindas(
                    data_fim=novo_stakeholder.data_fim_teste,
                    palavras=novo_stakeholder.palavras_chave,
                    exclusoes=novo_stakeholder.palavras_exclusao,
                    identificador=str(novo_stakeholder.identificador),
                    uf=novo_stakeholder.UF
                )
                assunto = "🎉 Bem-vindo ao Appa! Seu teste começou."
                mensageiro._enviar_gmail(novo_stakeholder.email,assunto, corpo_email)

            except Exception as e:
                print(f"Erro ao enviar e-mail de boas vindas: {e}")

            return redirect('appa_bot:sucesso')

    else:
        form=StakeholderForm()

    return render(
            request,'appa_bot/landing_page.html', {'form': form}
        )

def pagina_sucesso(request):
    return render(request,'appa_bot/sucesso_cadastro.html')

