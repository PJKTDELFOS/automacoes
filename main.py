from clientes.clientes import MonitorClientes
from datetime import datetime
import time
import os
from engine_busca_pncp.coletor_central import ColetorCentral
from engine_busca_pncp.email_manager import EmailManager
from engine_busca_pncp.db_manager import DBManager
from engine_busca_pncp.propriedades import Properties
from clear_dir import Cleardirectory


def envios():
    print("\n" + "=" * 60)
    print("      SISTEMA DE MONITORAMENTO PNCP - PIPELINE INTEGRADO")
    print("=" * 60)

    # 1. Inicialização de Gerenciadores
    db = DBManager()
    mailer_gmail = EmailManager(metodo='gmail')
    mailer_resend = EmailManager(metodo='resend')

    # 2. Coleta Centralizada (Cache para evitar múltiplas requisições ao PNCP)
    try:
        print("\n[1/2] Iniciando Coleta Centralizada (Cache)...")
        coletor = ColetorCentral(dias_padrao=15)
        coletor.coleta_diaria()
    except Exception as e:
        print(f"[!] Erro crítico na coleta: {e}")
        print("[i] Tentando prosseguir com os dados já existentes no banco...")

    print("\n[2/2] Iniciando processamento dos robôs clientes...")

    # Configuração de Regiões para facilitar a manutenção
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
            'nome': 'Nova Rodovia 2007',
            'email': ['comercial@nrgourmet.com.br','Gerencia@nrgourmet.com.br'],
            'palavras': [
                'refeicao','alimentacao','catering','cafe','almoco','ceia','colacao','lanche','janta','cozinha',
                'copeiragem','apoio','formula','hipo','proteina','terceirizacao','cozinheiro','cozinheira','generos','alimenticios'
            ],
            'uf': REGIOES['SUDESTE'][2],  # RJ
            'metodo': 'resend'
        },


    ]

    print(f"\nIniciando bateria de processamento em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("-" * 50)

    for i, conf in enumerate(lista_de_clientes):
        try:
            # A. Instancia o robô (Arquitetura Limpa: sem e-mail no robô)
            robo = conf['classe'](
                cliente=conf['nome'],
                palavras_chave=conf['palavras'],
                uf=conf['uf']
            )

            # B. Executa Busca e gera Planilha (caminho_anexo será None se não houver resultados)
            caminho_anexo, ids_para_registrar = robo.executar()

            if caminho_anexo:
                print(f"[{conf['nome']}] Planilha gerada em: {caminho_anexo}")

                # C. Tratamento de múltiplos destinatários
                destinatarios = conf['email']
                if isinstance(destinatarios, str):
                    destinatarios = [destinatarios]

                # D. Seleção do motor de envio (Resend ou Gmail)
                mailer = mailer_resend if conf.get('metodo') == 'resend' else mailer_gmail

                print(f"📧 Enviando via {conf.get('metodo').upper()} para {len(destinatarios)} contato(s)...")

                sucesso_geral = True
                for email_dest in destinatarios:
                    print(f"   > Despachando para: {email_dest}")
                    sucesso = mailer.enviar(
                        cliente_dados={'nome': conf['nome'], 'email': email_dest},
                        df_resultados=robo.dados_filtrados,
                        palavras_chave=conf['palavras'],
                        uf=conf['uf'],
                        anexo_path=caminho_anexo
                    )
                    if not sucesso:
                        sucesso_geral = False

                # E. Registro no Banco (Somente se o envio funcionou)
                if sucesso_geral:
                    for id_hash in ids_para_registrar:
                        db.registro_envio(id_hash, conf['nome'])
                    print(f"✅ Processo concluído com sucesso para {conf['nome']}")
                else:
                    print(f"⚠️ Alerta: Um ou mais envios falharam para {conf['nome']}.")

            else:
                print(f"ℹ️ Sem novidades para {conf['nome']} nesta rodada.")

            # Anti-Spam: Intervalo entre robôs de clientes diferentes
            if i < len(lista_de_clientes) - 1:
                print("Aguardando 15s para o próximo cliente...")
                time.sleep(15)

        except Exception as e:
            print(f"🛑 Erro crítico ao processar cliente {conf['nome']}: {e}")
            continue

    print("-" * 50)
    print(f"Fim da execução! Local das planilhas: {Properties.TEMP_FOLDER}")


if __name__ == "__main__":
    # 1. Limpa a pasta temporária antes de começar para não enviar arquivos antigos por erro
    Cleardirectory()

    # 2. Inicia o pipeline
    envios()
