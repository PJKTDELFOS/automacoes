from django.core.management.base import BaseCommand
from appa_bot.repository import ClienteRepository
import time
from clear_dir import Cleardirectory
from clientes.clientes import MonitorClientes
from engine_busca_pncp.coletor_central import ColetorCentral
from engine_busca_pncp.db_manager import DBManager
from engine_busca_pncp.email_manager import EmailManager
import requests



class Command(BaseCommand):

    help = 'Orquestra a coleta do PNCP, cruza com os clientes ativos do Django e envia e-mails.'
    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.WARNING("=== Iniciando Orquestrador APPA ===")
        )
        self.stdout.write(
            "Limpando pasta temporária de planilhas..."
        )
        link_db=None
        try:
            Cleardirectory()
            self.stdout.write("Conectando ao Banco de Dados Central...")
            try:
                link_db = DBManager()
            except ConnectionError as e:
                self.stdout.write(self.style.ERROR(f"Falha ao conectar ao banco: {e}"))
                return

            mensageiro=EmailManager(db_manager=link_db,metodo='resend')

            self.stdout.write(self.style.WARNING("\n[ETAPA 1] Faxina Diária do Banco de Dados..."))
            try:
                linhas_removidas=link_db.limpar_db_datas_vencidas()
                paginas_reiniciadas=link_db.reset_paginas_falhadas()
                if paginas_reiniciadas and paginas_reiniciadas>0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  -> Sucesso! {paginas_reiniciadas} paginas que foram reprocessadas do dia anterior."
                        )
                    )

                if linhas_removidas and linhas_removidas >0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  -> Sucesso! {linhas_removidas} licitações vencidas apagadas."
                        )
                    )
                else:
                    self.stdout.write("  -> Nenhuma licitação vencida para apagar hoje.")
                    self.stdout.write("  -> Nenhuma pagina para reprocessar hoje.")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  -> Erro ao tentar limpar o banco: {e}"))

            self.stdout.write(
                self.style.WARNING(
                    "\n[ETAPA 2] Coletando novos editais do PNCP..."
                )
            )


            # hoje = datetime.now()
            # data_referencia = hoje.date()
            # tarefa = link_db.get_proxima_pagina_PNCP(data_referencia)
            # if tarefa is None:
            #     self.stdout.write(self.style.SUCCESS("[+] Tudo pronto! Nenhuma página restando."))
            #     return
            # num_pagina = tarefa['numero_pagina']

            # para testes do envio do email comentar aqui

            coletor = ColetorCentral(db_manager=link_db, dias_padrao=15)

            try:
                coleta_diaria_atualizada = coletor.coleta_diaria()

                if not coleta_diaria_atualizada:
                    self.stdout.write(self.style.HTTP_INFO(
                        "\n[!] Coleta incompleta. Aguardando 60s para uma segunda tentativa..."
                    ))
                    time.sleep(30)
                    coleta_diaria_atualizada = coletor.coleta_diaria()
                if not coleta_diaria_atualizada:
                    self.stdout.write(self.style.ERROR(
                        "\n[!] A coleta falhou após retentativa. Abortando envio para garantir integridade."))
                    return
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                print(f"[!] Erro de conexão na página : {e}")
                return




            self.stdout.write(self.style.SUCCESS("\n[OK] Base íntegra. Iniciando Etapa 3..."))
            stakeholders_ativos=ClienteRepository.obter_clientes_ativos()
            if not stakeholders_ativos:
                self.stdout.write(
                    self.style.ERROR(
                        "Nenhum cliente ativo encontrado hoje. Encerrando."
                    )
                )
                return
            self.stdout.write(
                self.style.SUCCESS(
                    f"-> {len(stakeholders_ativos)} clientes na fila de processamento.")
                )
            self.stdout.write(
                self.style.WARNING(
                    "\n[ETAPA 4] Iniciando o Match e Envio de E-mails..."
                )
            )
            for stakeholder in stakeholders_ativos:
                self.stdout.write(
                    f"\nProcessando cliente: {stakeholder['nome']}"
                )
                try:
                    monitor=MonitorClientes(
                        cliente=stakeholder['nome'],
                        palavras_chave=stakeholder['palavras_chave'],
                        uf=stakeholder['uf'],
                        db_manager=link_db,
                        palavras_exclusao=stakeholder.get('palavras_exclusao',[]),
                    )
                    caminho_planilha,ids_encontrados=monitor.executar()
                    if caminho_planilha and monitor.dados_filtrados:
                        self.stdout.write(
                        self.style.SUCCESS(f"  -> {len(ids_encontrados)} licitações novas encontradas! Disparando e-mail:{stakeholder['email']}")
                        )
                        sucesso=mensageiro.enviar(
                            cliente_dados=stakeholder,
                            df_resultados=monitor.dados_filtrados,
                            palavras_chave=stakeholder['palavras_chave'],
                            uf=stakeholder['uf'],
                            anexo_path=caminho_planilha
                        )
                        if sucesso:
                            for id_hash in ids_encontrados:
                                link_db.registro_envio(id_hash,stakeholder['nome'])
                            self.stdout.write(self.style.SUCCESS("  -> Status salvo no histórico com sucesso."))
                        else:
                            self.stdout.write(self.style.ERROR("  -> Falha ao enviar o e-mail. Tentaremos amanhã."))
                    else:
                        self.stdout.write("  -> Nenhuma licitação nova para este cliente hoje.")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  -> Erro crítico ao processar cliente {stakeholder['nome']}: {e}"))
                    continue
            self.stdout.write(self.style.SUCCESS("\n=== Processo Finalizado com Sucesso! ==="))
        finally:
            self.stdout.write("Limpando planilhas temporárias pós-envio...")

            Cleardirectory()
            link_db.close_()






