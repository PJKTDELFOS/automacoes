import json
import re

import pandas as pd
from datetime import datetime
import os
from abc import ABC, abstractmethod
from engine_busca_pncp.db_manager import DBManager
from engine_busca_pncp.log_manager import LogManager
from engine_busca_pncp.propriedades import Properties


class BaseMonitor(ABC):

    def __init__(self, cliente,palavras_chave,uf,db_manager,palavras_exclusao=None):
        self.cliente = cliente
        self.palavras_chave = [p.lower() for p in palavras_chave]
        self.hoje=datetime.now()
        self.dados_filtrados=[]
        self.ids_a_registrar=[]
        self.uf=uf if uf else ''
        self.db=db_manager
        self.logger=LogManager(self.db)
        self.palavras_exclusao=palavras_exclusao or []



    def busca_db_central(self):
        condicoes=' OR '.join(
            ["objeto ~* %s" for _ in self.palavras_chave]
        )
        query=f'SELECT identificador_certame,dados_json from public.pncp_dados_brutos where ({condicoes}) '
        params=[
            f'\\y{re.escape(p)}\\y' for p in self.palavras_chave
        ]
        if self.uf:
            if isinstance(self.uf,list):
                placeholders=', '.join(['%s']*len(self.uf))
                query+=f' and uf in ({placeholders})'
                params.extend([u.upper() for u in self.uf])
            else:
                query += ' AND uf = %s'
                params.append(self.uf.upper())
        if self.palavras_exclusao:
            condicoes_exclusao=' OR '.join(
                ["objeto ~* %s" for _ in self.palavras_exclusao]
            )
            query+=f' AND NOT ({condicoes_exclusao})'
            params.extend(
                [
                    f'\\y{re.escape(p)}\\y' for p in self.palavras_exclusao
                ]
            )

        try:
            with self.db.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, tuple(params))
                    rows=cursor.fetchall()
                    return[
                        (r[0],r[1]) for r in rows
                    ]

        except Exception as e:
            self.logger.registro(
                self.cliente,
                "DB_CACHE",
                "ERROR",
                "READ_CACHE_ERR",
                "Falha ao ler cache central",
                e

            )
            return []
    def filtrar_novidades(self,resultados_cache):
        self.dados_filtrados=[]
        self.ids_a_registrar=[]
        for id_hash,dados_json in resultados_cache:
            if not dados_json:
                continue
            try:
                if not self.db.ja_enviado(id_hash,self.cliente):
                    item=dados_json if isinstance(dados_json,dict) else json.loads(dados_json)
                    self.dados_filtrados.append(item)
                    self.ids_a_registrar.append(id_hash)
            except(json.decoder.JSONDecodeError,TypeError):
                continue

    def gerar_planilha(self):
        if not self.dados_filtrados:
            return None
        try:
            df=pd.DataFrame(self.dados_filtrados)
            nome_arquivo=Properties.gerar_nome_arquivo(self.cliente)
            caminho_final=Properties.get_temp_path(nome_arquivo)
            os.makedirs(Properties.TEMP_FOLDER,exist_ok=True)
            df.to_excel(caminho_final,index=False,engine='openpyxl')
            return caminho_final

        except Exception as e:
            self.logger.registro(self.cliente, "EXCEL", "ERROR", "BIT_ERR", "Falha em memória", e)
            return None

    def executar(self):
        try:
            dados_brutos=self.busca_db_central()
            self.filtrar_novidades(dados_brutos)
            if not self.dados_filtrados:
                return None,[]
            self.filtros(self.dados_filtrados)
            if not self.dados_filtrados:
                return None,[]
            caminho_anexo=self.gerar_planilha()
            return caminho_anexo,self.ids_a_registrar
        except Exception as e_geral:
            self.logger.registro(self.cliente, "SISTEMA", "CRITICAL", "FLOW_ERR", "Erro no fluxo da BaseMonitor",
                                 str(e_geral))
            return None, []




    @abstractmethod
    def filtros(self, dados_brutos):
        pass





