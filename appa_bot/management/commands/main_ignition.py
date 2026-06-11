from django.core.management.base import BaseCommand
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException
from engine_busca_pncp.coletor_central import ColetorCentral
from engine_busca_pncp.db_manager import DBManager
import time


class Command(BaseCommand):

    help = 'Coleta novos editais do PNCP e persiste no banco central.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("=== Iniciando Coletor APPA ==="))

        link_db = None
        try:
            self.stdout.write("Conectando ao Banco de Dados Central...")
            try:
                link_db = DBManager()
            except ConnectionError as e:
                self.stdout.write(self.style.ERROR(f"Falha ao conectar ao banco: {e}"))
                return

            # --- ETAPA 1: Faxina diária ---
            self.stdout.write(self.style.WARNING("\n[ETAPA 1] Faxina Diária do Banco de Dados..."))
            try:
                linhas_removidas = link_db.limpar_db_datas_vencidas()
                paginas_reiniciadas = link_db.reset_paginas_falhadas()

                if paginas_reiniciadas and paginas_reiniciadas > 0:
                    self.stdout.write(self.style.SUCCESS(
                        f"  -> {paginas_reiniciadas} páginas reprocessadas do dia anterior."
                    ))
                if linhas_removidas and linhas_removidas > 0:
                    self.stdout.write(self.style.SUCCESS(
                        f"  -> {linhas_removidas} licitações vencidas apagadas."
                    ))
                else:
                    self.stdout.write("  -> Nenhuma licitação vencida para apagar hoje.")
                    self.stdout.write("  -> Nenhuma página para reprocessar hoje.")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  -> Erro ao tentar limpar o banco: {e}"))

            # --- ETAPA 2: Coleta ---
            self.stdout.write(self.style.WARNING("\n[ETAPA 2] Coletando novos editais do PNCP..."))

            coletor = ColetorCentral(db_manager=link_db, dias_padrao=15)

            try:
                coleta_ok = coletor.coleta_diaria()

                if not coleta_ok:
                    self.stdout.write(self.style.HTTP_INFO(
                        "\n[!] Coleta incompleta. Aguardando 30s para segunda tentativa..."
                    ))
                    time.sleep(30)
                    coleta_ok = coletor.coleta_diaria()

                if not coleta_ok:
                    self.stdout.write(self.style.ERROR(
                        "\n[!] Coleta falhou após retentativa. Encerrando."
                    ))
                    return

            except SessionNotCreatedException as e:
                self.stdout.write(self.style.ERROR(f"[!] ChromeDriver falhou ao iniciar sessão: {e}"))
                return
            except WebDriverException as e:
                self.stdout.write(self.style.ERROR(f"[!] Erro de conexão no Selenium: {e}"))
                return

            self.stdout.write(self.style.SUCCESS("\n=== Coleta Finalizada com Sucesso! ==="))

        finally:
            if link_db:
                link_db.close_()