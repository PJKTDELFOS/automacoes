import traceback
from datetime import datetime


class LogManager:

    def __init__(self,db_manager):
        self.db = db_manager

    def registro(self,cliente,etapa,nivel,codigo,mensagem,erro_bruto=None):
        stack_trace=None
        if erro_bruto:
            stack_trace=traceback.format_exc()

            query='''
            INSERT INTO public.logs_bot_pncp(cliente,etapa,nivel,codigo_erro,mensagem,stack_trace)
            VALUES(%s,%s,%s,%s,%s,%s)
            '''
            try:
                with self.db.get_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(query,(
                            cliente,
                            etapa,
                            nivel,
                            codigo,mensagem,
                            stack_trace
                        ))
                        connection.commit()
            except Exception as e:
                print(f"[{datetime.now()}] !!! FALHA GRAVE NO LOGMANAGER: {e}")
                print(f"Tentativa de log original: {cliente} | {codigo} | {mensagem}")

