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
            test_conexao=self.get_connection()
            test_conexao.close()
        except Exception as e:
            raise ConnectionError(f"Não foi possível conectar ao banco de dados: {e}")

    def get_connection(self):
        return psycopg2.connect(**self.db_params)

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