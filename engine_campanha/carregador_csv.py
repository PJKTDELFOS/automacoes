import re
import os
import pandas as pd
import psycopg2.extras
from engine_busca_pncp.db_manager import DBManager
from utilitarios.validadores import Validadores

pasta_arquivos=os.path.dirname(os.path.abspath(__file__))
caminho_csv=os.path.join(pasta_arquivos,'csv_campanha_janeiro.csv')



class CargaCSV:
    def __init__(self, caminho_arquivo):
        self.caminho_arquivo = caminho_arquivo
        self.db = DBManager()

    def sanitizacao_validacao(self, valor):
        if pd.isna(valor) or valor=="":
            return None,None

        if not valor: return None, None

        limpo = re.sub(r'\D', '', str(valor))
        tamanho = len(limpo)
        if tamanho == 14:
            if Validadores.validar_cnpj(limpo):
                return limpo, 'CNPJ'
        elif tamanho == 11:
            if Validadores.validador_cpf(limpo):
                return limpo, 'CPF'
        return None, None

    def carregar_dados_no_data_base(self):
        try:
            chunks = pd.read_csv(
                self.caminho_arquivo,
                sep=';',
                chunksize=5000,
                dtype=str,
                encoding='latin-1',
                on_bad_lines='skip',
                engine='c',
                quotechar='"'

            )
        except Exception as e:
            print(f"Erro ao abrir CSV: {e}")
            return
        total_inseridos = 0
        total_recusado=0
        conn=self.db.get_connection()
        try:
            with conn.cursor() as cursor:
                for lote in chunks:
                    dados_para_inserir=[]
                    for _,row in lote.iterrows():
                        doc_bruto=row.get('Código Contratado')
                        nome = row.get('Nome Contratado')
                        doc_final,tipo_doc=self.sanitizacao_validacao(doc_bruto)
                        if doc_final:
                            if nome:nome=str(nome).strip().upper()
                            dados_para_inserir.append((doc_final,nome,None,tipo_doc))
                        else:
                            total_recusado+=1
                if dados_para_inserir:
                    query="""
                    INSERT INTO public.pncp_leads_brutos 
                            (cnpj_cpf, razao_social, email, tipo_documento)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (cnpj_cpf) 
                            DO UPDATE SET razao_social = EXCLUDED.razao_social
                    """
                    psycopg2.extras.execute_batch(cursor, query, dados_para_inserir)
                    total_inseridos+=len(dados_para_inserir)
                    print(f"   ✅ Salvos: {len(dados_para_inserir)} | 🚫 Invalidos: {total_recusado}")
            conn.commit()
            print("=" * 40)
            print(f"🏁 SUCESSO! Leads Importados: {total_inseridos}")
            print(f"🗑️ Ignorados (CPF/CNPJ inválido): {total_recusado}")
        except Exception as e:
            conn.rollback()
            print(f"❌ Erro: {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    # NOME DO SEU ARQUIVO NOVO

    if os.path.exists(caminho_csv):
        carregador = CargaCSV(caminho_csv)
        carregador.carregar_dados_no_data_base()
    else:
        print(f"Arquivo '{caminho_csv}' não encontrado.")



