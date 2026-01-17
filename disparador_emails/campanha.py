from disparador_emails.disparador import Disparador_de_emails
from listas_clientes import lista_clientes1,lista_clientes2

def campanha(lista_clientes):
    sucesso=0
    fracasso=0
    for cliente in lista_clientes:
        print(f'enviando para o cliente {cliente['nomme']} ({cliente['email']})')
        disparador=Disparador_de_emails(cliente['email'],cliente['nomme'])
        mensagem=disparador.mensagem()
        assunto_email=f"Oportunidade para a {cliente['nomme']}: Automação de Licitações"
        envio=disparador._enviar_gmail(cliente['email'],assunto_email,mensagem,)
        if envio:
            sucesso+=1
            print(f'total de envios bem sucedidos:{sucesso}')
        else:
            fracasso+=1
            print(f'total de envios mal sucedidos:{fracasso}')
        print("\n" + "=" * 30)
        print(f"Campanha Finalizada!")
        print(f"Enviados: {sucesso}")
        print(f"Falhas: {fracasso}")
        print("=" * 30)


if __name__ == "__main__":
    campanha(lista_clientes1)