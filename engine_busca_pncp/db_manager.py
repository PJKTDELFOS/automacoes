import os

import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
load_dotenv()

class DBManager:
    def __init__(self):
        self.conn_params={
            "dbname":os.getenv("DB_NAME"),
            "user":os.getenv("DB_USER"),
            "password":os.getenv("DB_PASSWORD"),
            "host":os.getenv("DB_HOST"),
            "port":os.getenv("DB_PORT"),
        }
        if not all(self.conn_params.values()):
            raise EnvironmentError("DATABASE NOT SET")

    def get_connection(self):
        return psycopg2.connect(**self.conn_params)

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