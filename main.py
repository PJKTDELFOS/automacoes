from clientes.efata import ClientesEfataEventos
from datetime import datetime
import time

def envios():
    clientes_config=[
        #CLIENTE 1
        {
            'classe':ClientesEfataEventos,
            'nome':'Efata Eventos',
            'email':'albert.franca1992@gmail.com',
            'palavras':[
                'encanamentos','concreto'
            ],
            'uf':'PA'
        },
        #CLIENTE2
        {
            'classe': ClientesEfataEventos,
            'nome': 'nr alimentação',
            'email': 'profissional.albert@gmail.com',
            'palavras': [
                'peças','automotivas'
            ],
            'uf': 'MA'
        },
        #CLIENTE 3
        {
            'classe': ClientesEfataEventos,
            'nome': 'GEMAQ',
            'email': 'orofissional.albert@gmail.com',
            'palavras': [
                'fogos','eventos'
            ],
            'uf': 'PR'
        },


    ]
    print(f"\nIniciando bateria de testes em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("-" * 50)
    for i, conf in enumerate(clientes_config):
        try:
            robo=conf['classe'](
                cliente=conf['nome'],
                palavras_chave=conf['palavras'],
                email_destino=conf['email'],
                uf=conf['uf']
            )
            robo.executar()

            if i<len(clientes_config)-1:
                segundos_espera=30
                print(f"Aguardando {segundos_espera} segundos para o próximo cliente (Segurança Anti-Spam)...")
                time.sleep(segundos_espera)
        except Exception as e:
            print(f"Erro crítico ao processar cliente {conf['nome']}: {e}")
            continue
        print("-" * 50)
        print("Bateria de testes finalizada com sucesso!")




if __name__ == "__main__":
    envios()
