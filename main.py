from clientes.clientes import MonitorClientes
from datetime import datetime
import time

from engine_busca_pncp.coletor_central import ColetorCentral


def envios():
    print("\n" + "=" * 60)
    print("      SISTEMA DE MONITORAMENTO PNCP - PIPELINE INTEGRADO")
    print("=" * 60)
    # try:
    #     print("\n[1/2] Iniciando Coleta Centralizada (Cache)...")
    #     coletor=ColetorCentral(dias_padrao=6)
    #     coletor.coleta_diaria()
    # except Exception as e:
    #     print(f"[!] Erro crítico na coleta: {e}")
    #     print("[i] Tentando prosseguir com os dados já existentes no banco...")
    #
    # print("\n[2/2] Iniciando processamento dos robôs clientes...")
    # regioes
    REGIOES = {
        'NORTE': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
        'NORDESTE': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
        'CENTRO_OESTE': ['DF', 'GO', 'MT', 'MS'],
        'SUDESTE': ['ES', 'MG', 'RJ', 'SP'],
        'SUL': ['PR', 'RS', 'SC']
    }

    lista_de_clientes=[
        #CLIENTE 1
        {
            'classe':MonitorClientes,
            'nome':'Cliente A',
            'email':'albert.franca1992@gmail.com',
            'palavras':[
                'fogos','eventos'
            ],
            'uf':REGIOES['SUDESTE']
        },
        #CLIENTE2
        {
            'classe': MonitorClientes,
            'nome': 'Cliente B',
            'email': 'profissional.albert@gmail.com',
            'palavras': [
                'fogos','eventos'
            ],
            'uf': REGIOES['NORDESTE']
        },
        #CLIENTE 3
        {
            'classe': MonitorClientes,
            'nome': 'Cliente C',
            'email': 'orofissional.albert@gmail.com',
            'palavras': [
                'fogos','eventos'
            ],
            'uf': REGIOES['SUL']
        },
        {
            'classe': MonitorClientes,
            'nome': 'Cliente D',
            'email': 'albert-franca@hotmail.com',
            'palavras': [
                'fogos', 'eventos'
            ],
            'uf': REGIOES['CENTRO_OESTE']
        },


    ]
    print(f"\nIniciando bateria de testes em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("-" * 50)
    for i, conf in enumerate(lista_de_clientes):
        try:
            robo=conf['classe'](
                cliente=conf['nome'],
                palavras_chave=conf['palavras'],
                email_destino=conf['email'],
                uf=conf['uf']
            )
            print(f'enviando email para o cliente{lista_de_clientes[i]['nome']}')
            robo.executar()

            if i<len(lista_de_clientes)-1:
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
