from django.shortcuts import render


# Create your views here.


def pagina_inicial(request):
    return render(request,'appa_bot/tela_entrada.html')