from django.shortcuts import render,get_object_or_404,redirect
from .models import Stakeholder,logAcao
from.forms import StakeholderForm,AtualizarStakeHolderForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from appa_bot.services.main_services import MainServices

from engine_campanha.disparador import Disparador_de_emails
from appa_bot.repository import ClienteRepository



# Create your views here.


def pagina_landing_page(request):
    print("--- INÍCIO DO TESTE DETETIVE ---")
    print("MÉTODO DA REQUISIÇÃO:", request.method)
    if request.method == "POST":
        form = StakeholderForm(request.POST)
        if form.is_valid():
            try:
                MainServices.criar_stakeholders(form)
                return redirect('appa:sucesso')
            except Exception as e:
                messages.error(request, "Ocorreu um erro interno. Tente novamente.")
                print(f"Erro na view de cadastro: {e}")
    else:
        print("ENTROU NO ELSE (GET)!")
        form = StakeholderForm()
        print("O FORM ESTÁ AMARRADO A DADOS (BOUND)?", form.is_bound)
    return render(request, "appa_bot/landing_page.html", {"form":form})




    #
def pagina_sucesso(request):
    return render(request,'appa_bot/sucesso_cadastro.html')

def pagina_inicial(request):
    return render(request,'appa_bot/pagina_inicial.html')

