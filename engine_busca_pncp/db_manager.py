import os
from psycopg2 import pool
import psycopg2
from contextlib import contextmanager
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
            'port': Config.port,

        }
        self.pool=pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            **self.db_params,
            client_encoding='UTF8',
            connect_timeout=10
        )

        try:
            self.criar_estrutura_inicial()
            print(" Conexão PostgreSQL OK e estrutura verificada.")
        except Exception as e:
            raise ConnectionError(f"Não foi possível conectar ao banco de dados: {e}")

    @contextmanager
    def get_connection(self):
        conn=self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

#criaçao das tabelas
    def criar_estrutura_inicial(self):
        with self.get_connection() as conn:
            conn.autocommit = True # Importante para comandos CREATE
            with conn.cursor() as cur:
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
                cur.execute(
                    """
                    CREATE EXTENSION IF NOT EXISTS pg_trgm;
                    """
                )
                cur.execute("""
                                    CREATE INDEX IF NOT EXISTS idx_objeto_regex_trgm 
                                    ON public.pncp_dados_brutos USING GIN (objeto gin_trgm_ops);
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

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS public.pncp_leads_brutos (
                    cnpj_cpf VARCHAR(20) PRIMARY KEY,
                    razao_social TEXT,
                    email VARCHAR(255),
                    telefone VARCHAR(50),             -- Adicionei aqui
                    tipo_documento VARCHAR(10),
                    status_enriquecimento VARCHAR(20) DEFAULT 'PENDENTE',
                    status_envio_campanha VARCHAR(20) DEFAULT 'PENDENTE',
                    data_envio_campanha TIMESTAMP,    -- Adicionei aqui
                    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS public.controle_coleta_paginas_pncp(
                    id serial primary key,
                    data_coleta DATE not null,
                    numero_pagina integer not null ,
                    status VARCHAR(20) default 'PENDENTE',
                    tentativas integer default 0,
                    ultima_resposta_http  integer,
                    atualizado_em timestamp default current_timestamp,
                    unique (data_coleta, numero_pagina)
                    
                    );
                    """
                )

                cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_cliente ON public.logs_bot_pncp(cliente);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_data ON public.logs_bot_pncp(timestamp_log);")
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_status_busca ON public.pncp_leads_brutos(status_enriquecimento);")
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_status_campanha ON public.pncp_leads_brutos(status_envio_campanha);")
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_razao_social_busca ON public.pncp_leads_brutos(razao_social);")

#controle de atualizaçao das licitações no banco de dados
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

#campanha
    def get_leads_para_enriquecimento(self,limite=50):
        query="""
        SELECT cnpj_cpf,razao_social from public.pncp_leads_brutos 
        WHERE status_enriquecimento = 'PENDENTE' AND tipo_documento = 'CNPJ'
        LIMIT %s
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query,(limite,))
                    return cursor.fetchall()
        except Exception as e:
            print(f' erro ao consultar DB {e}')
            return []
    def atualizar_led_enriquecido(self,cnpj,email,telefone):
        query="""
        UPDATE public.pncp_leads_brutos 
        SET 
            email = CASE WHEN %s IS NOT NULL THEN %s ELSE email END, 
            telefone = CASE WHEN %s IS NOT NULL THEN %s ELSE telefone END,
            status_enriquecimento = 'PROCESSADO'
        WHERE cnpj_cpf = %s
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query,(email,email,telefone,telefone,cnpj))
                    if cursor.rowcount == 0:
                        print(f"      ⚠️ AVISO: Nenhuma linha atualizada para {cnpj}. CNPJ existe?")
                    else:
                        print(f"      💾 DB: {cnpj} atualizado com sucesso (Commit OK).")

                connection.commit()
        except Exception as e:
            print(f"Erro ao atualizar lead {cnpj}: {e}")

    def marcar_processado_sem_sucesso(self,cnpj):
        query="UPDATE public.pncp_leads_brutos SET status_enriquecimento = 'NAO_ENCONTRADO' WHERE cnpj_cpf = %s"
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query,(cnpj,))
                connection.commit()
        except Exception as e:
            print(f"Erro ao marcar lead {cnpj}: {e}")

    def get_leads_campanha(self,limite=50):
        query="""
            SELECT cnpj_cpf, razao_social, email FROM public.pncp_leads_brutos 
            WHERE status_envio_campanha = 'PENDENTE' 
            AND email IS NOT NULL AND email != ''
            LIMIT %s
        
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query,(limite,))
                    return cursor.fetchall()
        except Exception as e:
            print(f' erro ao buscar campanha {e}')
            return []

    def atualizar_status_campanha(self,cnpj,status_novo):
        if status_novo in ['enviado','sucesso']:
            query="""
            UPDATE public.pncp_leads_brutos 
                SET status_envio_campanha = %s, 
                    data_envio_campanha = NOW() 
                WHERE cnpj_cpf = %s
            """
        else:
            query="""
            UPDATE public.pncp_leads_brutos 
                SET status_envio_campanha = %s 
                WHERE cnpj_cpf = %s
            """

        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query,(status_novo,cnpj))
                connection.commit()
        except Exception as e:
            print(f"Erro status campanha {cnpj}: {e}")

#limpeza do db da tabela de licitações
    def limpar_db_datas_vencidas(self):
        query='''
        DELETE FROM public.pncp_dados_brutos
        where (dados_json->>'dataEncerramentoProposta') IS NOT NULL
        AND (dados_json->>'dataEncerramentoProposta')::timestamp < NOW();
        '''
        try:
            with self.get_connection() as connection:
                with connection.cursor()as cursor:
                    cursor.execute(query)
                    linhas_deletadas=cursor.rowcount
                connection.commit()
                print(f"      🧹 Faxina do Banco: {linhas_deletadas} "
                      f"licitações vencidas foram deletadas com sucesso!")
                return linhas_deletadas
        except Exception as e:
            print(f' erro ao limpar das linhas {e}')
            return 0

#controle de paginas diarias para atualizaçao e envio
    def registrar_mapeamento_diario_PNCP(self, data_coleta, total_paginas):
        if not total_paginas or total_paginas < 0:
            return
        querry = """
        INSERT INTO public.controle_coleta_paginas_pncp (data_coleta, numero_pagina) VALUES (%s, %s)
         ON CONFLICT (data_coleta, numero_pagina) DO NOTHING;

        """
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    dados = [(data_coleta, p) for p in range(1, total_paginas + 1)]
                    cursor.executemany(querry, dados)
                connection.commit()
                print(f"[DB] Mapeamento concluído: {total_paginas} páginas registradas para {data_coleta}.")
        except Exception as e:
            print(f"Erro ao registrar mapeamento: {e}")

    def get_proxima_pagina_PNCP(self, data_coleta):
        query = """
        SELECT id,numero_pagina from public.controle_coleta_paginas_pncp
        WHERE data_coleta = %s
        AND status in ('PENDENTE', 'ERRO')
        and tentativas < 10
        order by numero_pagina asc
        limit 1
        """

        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (data_coleta,))
                    res = cursor.fetchone()
                    if res:
                        return {'id': res[0], 'numero_pagina': res[1]}
                    return None
        except Exception as e:
            print(f"Erro ao buscar próxima página: {e}")
            return None

    def atualizar_status_tarefa_PNCP(self, tarefa_id, status, code=None):
        query = """
        update public.controle_coleta_paginas_pncp
        set status = %s,
            ultima_resposta_http = %s,
            tentativas = tentativas + 1,
            atualizado_em = NOW()
        where id = %s
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (status, code, tarefa_id))
                connection.commit()
        except Exception as e:
            print(f"Erro ao atualizar status da tarefa {tarefa_id}: {e}")

    def verificar_conclusao_dia_PNCP(self, data_coleta):
        query = """
        select count(*) from public.controle_coleta_paginas_pncp
        where data_coleta = %s and status != 'CONCLUIDO'
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (data_coleta,))
                    pendentes = cursor.fetchone()[0]
                    return pendentes == 0
        except Exception as e:
            print(f"Erro no check de conclusão: {e}")
            return False

    def reset_paginas_falhadas(self):
        querry="""
        update public.controle_coleta_paginas_pncp
        set status ='PENDENTE',
            tentativas = 0
        where tentativas >= 10
        and status= 'ERRO'
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(querry)
                    linhas_afetadas=cursor.rowcount
                connection.commit()
                if linhas_afetadas>0:
                    print(
                        f"[🔄] Reset de Erros: {linhas_afetadas} páginas voltaram para a fila de processamento."
                    )
        except Exception as e:
            print(f"[-] Erro ao resetar páginas falhadas: {e}")
            return 0





