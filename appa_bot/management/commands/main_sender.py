from django.core.management.base import BaseCommand
from appa_bot.repository import ClienteRepository
from clear_dir import Cleardirectory
from clientes.clientes import MonitorClientes
from engine_busca_pncp.db_manager import DBManager
from engine_busca_pncp.email_manager import EmailManager


class Command(BaseCommand):

    help = 'Cruza licitações coletadas com os clientes ativos e envia e-mails.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("=== Iniciando Remetente APPA ==="))
        self.stdout.write("Limpando pasta temporária de planilhas...")

        link_db = None
        try:
            Cleardirectory()

            self.stdout.write("Conectando ao Banco de Dados Central...")
            try:
                link_db = DBManager()
            except ConnectionError as e:
                self.stdout.write(self.style.ERROR(f"Falha ao conectar ao banco: {e}"))
                return

            mensageiro = EmailManager(db_manager=link_db, metodo='resend')

            # --- ETAPA 1: Carregar clientes ativos ---
            self.stdout.write(self.style.WARNING("\n[ETAPA 1] Carregando clientes ativos..."))
            stakeholders_ativos = ClienteRepository.obter_clientes_ativos()

            if not stakeholders_ativos:
                self.stdout.write(self.style.ERROR(
                    "Nenhum cliente ativo encontrado hoje. Encerrando."
                ))
                return

            self.stdout.write(self.style.SUCCESS(
                f"  -> {len(stakeholders_ativos)} clientes na fila de processamento."
            ))

            # --- ETAPA 2: Match e envio ---
            self.stdout.write(self.style.WARNING("\n[ETAPA 2] Iniciando Match e Envio de E-mails..."))

            for stakeholder in stakeholders_ativos:
                self.stdout.write(f"\nProcessando cliente: {stakeholder['nome']}")
                try:
                    monitor = MonitorClientes(
                        cliente=stakeholder['nome'],
                        palavras_chave=stakeholder['palavras_chave'],
                        uf=stakeholder['uf'],
                        db_manager=link_db,
                        palavras_exclusao=stakeholder.get('palavras_exclusao', []),
                    )
                    caminho_planilha, ids_encontrados = monitor.executar()

                    if caminho_planilha and monitor.dados_filtrados:
                        self.stdout.write(self.style.SUCCESS(
                            f"  -> {len(ids_encontrados)} licitações novas encontradas! "
                            f"Disparando e-mail: {stakeholder['email']}"
                        ))
                        sucesso = mensageiro.enviar(
                            cliente_dados=stakeholder,
                            df_resultados=monitor.dados_filtrados,
                            palavras_chave=stakeholder['palavras_chave'],
                            uf=stakeholder['uf'],
                            anexo_path=caminho_planilha
                        )

                        if sucesso:
                            for id_hash in ids_encontrados:
                                # Registros em loop intencional: falha parcial é tolerada.
                                # Na próxima execução o cliente recebe os itens não registrados
                                # junto do dia corrente. Janela máxima de atraso: 1 dia em 15.
                                # DEPENDE do ON CONFLICT DO NOTHING em registro_envio para idempotência.
                                link_db.registro_envio(id_hash, stakeholder['nome'])
                            self.stdout.write(self.style.SUCCESS(
                                "  -> Status salvo no histórico com sucesso."
                            ))
                        else:
                            self.stdout.write(self.style.ERROR(
                                "  -> Falha ao enviar o e-mail. Tentaremos amanhã."
                            ))
                    else:
                        self.stdout.write(
                            "  -> Nenhuma licitação nova para este cliente hoje."
                        )

                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"  -> Erro crítico ao processar cliente {stakeholder['nome']}: {e}"
                    ))
                    continue

            self.stdout.write(self.style.SUCCESS("\n=== Envio Finalizado com Sucesso! ==="))

        finally:
            self.stdout.write("Limpando planilhas temporárias pós-envio...")
            Cleardirectory()
            if link_db:
                link_db.close_()