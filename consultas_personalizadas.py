import os
os.environ["PYTHONUTF8"] = "1"

import pandas as pd
import json
from sqlalchemy import create_engine, text
from engine_busca_pncp.config import Config
from clientes.clientes import MonitorClientes




def consultapersonalizada(nome_arquivo):
    try:
        url = (
            f"postgresql+psycopg2://{Config.user}:{Config.password}"
            f"@{Config.host}:{Config.port}/{Config.dbname}"
        )
        engine = create_engine(url)

        querry = text("""
        SELECT dados_json FROM public.pncp_dados_brutos
          WHERE (objeto ILIKE '%locação de veículo%' 
        OR objeto ILIKE '%locaçao de veiculo%' 
        OR objeto ILIKE '%prancha%'
        OR objeto ILIKE '%locaçao de caminhao%'
        OR objeto ILIKE '%transporte rodoviario%'
        OR objeto ILIKE '%carga extraordinaria%'
        OR objeto ILIKE '%transporte rodoviario de cargas%'
		OR objeto ILIKE '%batedor%'
		OR objeto ILIKE '%remoçao%'
		OR objeto ILIKE '%remoção%'
		OR objeto ILIKE '%reposicionamento%'
		OR objeto ILIKE '%movimentação%')
          AND uf = 'RJ';
          
        """)

        with engine.connect() as conn:
            df = pd.read_sql(querry, con=conn)

        df.to_excel(nome_arquivo, index=False)
        print(f"✅ Sucesso! Arquivo salvo como: {nome_arquivo}")
        print(f"📦 Total de linhas exportadas: {len(df)}")

        if df.empty:
            print("⚠️ Nenhuma licitação encontrada para os filtros aplicados.")
            return

        lista_licitacoes=[]
        for index,row in df.iterrows():
            item_json=row['dados_json']
            if isinstance(item_json,str):
                lista_licitacoes.append(json.loads(item_json))
            elif isinstance(item_json,dict):
                lista_licitacoes.append(item_json)

        cliente = "SILVIO - CONSULTA PERSONALIZADA"
        palavras_chave = ["LOCACAO", "VEICULO", "TRANSPORTE", "PRANCHA", "CAMINHAO"]
        monitor = MonitorClientes(db_manager=None,palavras_chave=palavras_chave,cliente=cliente,uf='RJ')
        caminho_salvo=monitor.gerar_planilha()
        print(f"✅ Sucesso Absoluto! Planilha do Silvio estilizada com openpyxl salva em: {caminho_salvo}")


    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")



if __name__ == "__main__":
    consultapersonalizada("planilha_dia_08_06_v3.xlsx")

