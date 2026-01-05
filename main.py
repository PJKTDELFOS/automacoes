from clientes.clientes import MonitorClientes
from datetime import datetime
import time
import os

from engine_busca_pncp.coletor_central import ColetorCentral
from engine_busca_pncp.email_manager import EmailManager
from engine_busca_pncp.db_manager import DBManager
from engine_busca_pncp.propriedades import Properties


def envios():
    print("\n" + "=" * 60)
    print("      SISTEMA DE MONITORAMENTO PNCP - PIPELINE INTEGRADO")
    print("=" * 60)

    # Gerenciadores e Banco
    db = DBManager()
    mailer_gmail = EmailManager(metodo='gmail')
    mailer_resend = EmailManager(metodo='resend')

    try:
        print("\n[1/2] Iniciando Coleta Centralizada (Cache)...")
        # coletor = ColetorCentral(dias_padrao=3)
        # coletor.coleta_diaria()
    except Exception as e:
        print(f"[!] Erro crítico na coleta: {e}")
        print("[i] Tentando prosseguir com os dados já existentes no banco...")

    print("\n[2/2] Iniciando processamento dos robôs clientes...")

    REGIOES = {
        'NORTE': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
        'NORDESTE': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
        'CENTRO_OESTE': ['DF', 'GO', 'MT', 'MS'],
        'SUDESTE': ['ES', 'MG', 'RJ', 'SP'],
        'SUL': ['PR', 'RS', 'SC']
    }

    lista_de_clientes = [
        {
            'classe': MonitorClientes,
            'nome': 'clinte A',  # Exemplo para Resend
            'email': 'profissional.albert@gmail.com',
            'palavras': ["evento"],
            'uf': REGIOES['SUDESTE'][2],
            'metodo': 'resend'
        },
        {
            'classe': MonitorClientes,
            'nome': 'Cliente B',
            'email': 'profissional.albert@gmail.com',
            'palavras': ['fogos', 'eventos'],
            'uf': REGIOES['NORDESTE'],
            'metodo': 'gmail'
        },
        {
            'classe': MonitorClientes,
            'nome': 'Cliente C',
            'email': 'profissional.albert@gmail.com',
            'palavras': ['fogos', 'eventos'],
            'uf': REGIOES['SUL'],
            'metodo': 'gmail'
        }
    ]

    print(f"\nIniciando bateria de testes em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("-" * 50)

    for i, conf in enumerate(lista_de_clientes):
        try:
            # 1. Instancia o robô (BaseMonitor)
            # Nota: Removemos 'email_destino' se você tirou do __init__ da BaseMonitor
            robo = conf['classe'](
                cliente=conf['nome'],
                palavras_chave=conf['palavras'],
                uf=conf['uf']
            )

            # 2. Executa Busca, Filtro e Geração de Planilha Física
            # Agora retorna: caminho do arquivo e lista de IDs
            caminho_anexo, ids_para_registrar = robo.executar()

            if caminho_anexo:
                print(f"[{conf['nome']}] Planilha gerada em: {caminho_anexo}")

                # Escolhe o Mailer baseado na config do cliente
                mailer = mailer_resend if conf.get('metodo') == 'resend' else mailer_gmail

                print(f"📧 Enviando via {conf.get('metodo').upper()}...")

                # 3. Dispara o e-mail
                sucesso = mailer.enviar(
                    cliente_dados={'nome': conf['nome'], 'email': conf['email']},
                    df_resultados=robo.dados_filtrados,
                    palavras_chave=conf['palavras'],
                    uf=conf['uf'],
                    anexo_path=caminho_anexo
                )

                if sucesso:
                    # 4. Somente após o envio bem-sucedido, registra os IDs no histórico
                    for id_hash in ids_para_registrar:
                        db.registro_envio(id_hash, conf['nome'])
                    print(f"✅ Processo concluído para {conf['nome']}")
                else:
                    print(f"❌ Falha no envio para {conf['nome']}. IDs não foram registrados.")

            else:
                print(f"ℹ️ Sem novidades para {conf['nome']}.")

            # Anti-Spam
            if i < len(lista_de_clientes) - 1:
                segundos_espera = 15
                print(f"Aguardando {segundos_espera}s...")
                time.sleep(segundos_espera)

        except Exception as e:
            print(f"Erro crítico ao processar cliente {conf['nome']}: {e}")
            continue

    print("-" * 50)
    print(f"Bateria finalizada! Verifique as planilhas em: {Properties.TEMP_FOLDER}")


if __name__ == "__main__":
    envios()
