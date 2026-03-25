from django.core.exceptions import ValidationError
from django.shortcuts import render,get_object_or_404,redirect
from .models import Stakeholder
from.forms import StakeholderForm,AtualizarStakeHolderForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from appa_bot.services.main_services import MainServices

from engine_campanha.disparador import Disparador_de_emails
from appa_bot.repository import ClienteRepository



# Create your views here.


def pagina_landing_page(request):
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

def pagina_atualizar_sucesso(request):
    return render(
        request,'appa_bot/sucesso_atualizar.html'
    )

def pagina_inicial(request):
    return render(request,'appa_bot/pagina_inicial.html')


def buscar_clientes(request):
    if request.method=='POST':
        id_digitado=request.POST.get('id_digitado','').strip()

        if not id_digitado:
            messages.error(request, "Por favor, cole o seu ID.")
            return redirect('/')

        try:
            stakeholder=Stakeholder.objects.get(identificador=id_digitado)
            return redirect('appa:atualizar_palavras',identificador=stakeholder.identificador)
        except Stakeholder.DoesNotExist:
            messages.error(request, "ID não encontrado. Verifique se copiou corretamente.")
            return redirect('/')
        except(ValueError, ValidationError):
            messages.error(request, "Formato de ID inválido.")
            return redirect('/')
    return render(
        request,'appa_bot/acesso_cliente.html'
    )

def atualizar_parametros(request,identificador):
    stakeholder=get_object_or_404(Stakeholder,identificador=identificador)
    if request.method == "POST":
        form=AtualizarStakeHolderForm(request.POST,instance=stakeholder)
        if form.is_valid():
            try:
                MainServices.atualizar_stakeholder(form)
                messages.success(request,
                                 "Suas palavras-chave foram atualizadas com sucesso! O robô já vai usar as novas regras na próxima busca.")
                return redirect('appa:sucesso_atualizar')
            except Exception as e:
                messages.error(request, "Verifique os erros abaixo.")
    else:
        form=AtualizarStakeHolderForm(instance=stakeholder)
    contexto={
        'form':form,
        'stakeholder':stakeholder,
    }
    return render(
        request,'appa_bot/atualizar_config.html',context=contexto,
    )


