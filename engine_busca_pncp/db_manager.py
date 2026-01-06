import os

import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
from engine_busca_pncp.config import Config
load_dotenv()

class DBManager:
    def __init__(self):
        self.db_params = {
            'dbname': Config.dbname,
            'user': Config.user,
            'password': Config.password,
            'host': Config.host,
            'port': Config.port
        }
        try:
            self.criar_estrutura_inicial()
            print(" Conexão PostgreSQL OK e estrutura verificada.")
        except Exception as e:
            raise ConnectionError(f"Não foi possível conectar ao banco de dados: {e}")

    def get_connection(self):
        return psycopg2.connect(**self.db_params)

    def criar_estrutura_inicial(self):
        # Usamos uma conexão temporária para criar as tabelas
        conn = self.get_connection()
        conn.autocommit = True # Importante para comandos CREATE
        try:
            with conn.cursor() as cur:
                # 1. Tabela de Dados Brutos
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS public.pncp_dados_brutos (
                        id SERIAL PRIMARY KEY,
                        data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        identificador_certame VARCHAR(255) UNIQUE,
                        uf VARCHAR(2),
                        objeto TEXT,
                        dados_json JSONB
                    );
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_objeto_busca_texto 
                    ON public.pncp_dados_brutos USING GIN (to_tsvector('portuguese', objeto));
                """)

                # 2. Tabela de Histórico de Envios
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS public.historico_licitacoes (
                        id SERIAL PRIMARY KEY,
                        identificador_pncp VARCHAR(255),
                        cliente VARCHAR(255),
                        data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT unique_envio_cliente UNIQUE (identificador_pncp, cliente)
                    );
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_historico_cliente_identificador 
                    ON public.historico_licitacoes (cliente, identificador_pncp);
                """)

                # 3. Tabela de Logs
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS public.logs_bot_pncp (
                        id SERIAL PRIMARY KEY,
                        timestamp_log TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cliente VARCHAR(255) NOT NULL,
                        etapa VARCHAR(255) NOT NULL,
                        nivel VARCHAR(255) NOT NULL,
                        codigo_erro VARCHAR(255),
                        mensagem TEXT,
                        stack_trace TEXT
                    );
                """)

                cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_cliente ON public.logs_bot_pncp(cliente);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_data ON public.logs_bot_pncp(timestamp_log);")
        finally:
            conn.close()

    def ja_enviado(self,identificador,cliente):
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT 1 FROM public.historico_licitacoes WHERE identificador_pncp = %s AND cliente = %s",
                        (identificador,cliente)
                    )
                    return cursor.fetchone() is not None
        except Exception as e:
            print(f' erro ao consultar DB {e}')
            return True

    def registro_envio(self,identificador,cliente):
        querry="""INSERT INTO public.historico_licitacoes (identificador_pncp, cliente) VALUES (%s, %s)
        ON CONFLICT (identificador_pncp, cliente) DO NOTHING
        """


        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        querry,
                        (identificador,cliente)
                    )
                connection.commit()
        except Exception as e:
            print(f' erro ao consultar DB {e}')