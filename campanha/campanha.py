import time

from campanha.disparador import Disparador_de_emails
from listas_clientes import lista_clientes1,lista_clientes2
#reverter a correção caso o banco de dados de email nao se mostrar viavel
def campanha(lista_clientes):
    sucesso=0
    fracasso=0
    contador_lotes=0
    for cliente in lista_clientes:
        print(f"enviando para o cliente {cliente['nome']} ({cliente['email']})")
        disparador=Disparador_de_emails(cliente['email'],cliente['nome'])
        mensagem=disparador.mensagem()
        assunto_email=f"Oportunidade para a {cliente['nome']}: Automação de Licitações"
        envio=disparador._enviar_gmail(cliente['email'],assunto_email,mensagem,)
        contador_lotes += 1
        if envio:
            sucesso+=1

            print(f'total de envios bem sucedidos:{sucesso}')
        else:
            fracasso+=1
            print(f'total de envios mal sucedidos:{fracasso}')
        if contador_lotes ==20:
            print("\n" + "-" * 30)
            print("☕ Atingiu 20 envios. Pausando por 30 segundos...")
            print("-" * 30 + "\n")
            time.sleep(30)
            contador_lotes=0
            print("▶️ Retomando envios...")
        else:
            time.sleep(1)



    print("\n" + "=" * 30)
    print(f"Campanha Finalizada!")
    print(f"Enviados: {sucesso}")
    print(f"Falhas: {fracasso}")
    print("=" * 30)


if __name__ == "__main__":
    campanha(lista_clientes1)