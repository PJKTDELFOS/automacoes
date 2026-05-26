import os
os.environ["PYTHONUTF8"] = "1"

import pandas as pd
from sqlalchemy import create_engine, text
from engine_busca_pncp.config import Config


def planilha_silvio(nome_arquivo):
    try:
        url = (
            f"postgresql+psycopg2://{Config.user}:{Config.password}"
            f"@{Config.host}:{Config.port}/{Config.dbname}"
        )
        engine = create_engine(url)

        querry = text("""
        SELECT * FROM public.pncp_dados_brutos
        WHERE (objeto ILIKE '%locação de veículo%' 
        OR objeto ILIKE '%locaçao de veiculo%' 
        OR objeto ILIKE '%prancha%'
        OR objeto ILIKE '%locaçao de caminhao%'
        OR objeto ILIKE '%transporte rodoviario'
        OR objeto ILIKE '%carga extraordianaria%'
        OR objeto ILIKE '%transporte rodoviario de cargas%')
          AND uf = 'RJ';
        """)

        with engine.connect() as conn:
            df = pd.read_sql(querry, con=conn)

        df.to_excel(nome_arquivo, index=False)
        print(f"✅ Sucesso! Arquivo salvo como: {nome_arquivo}")
        print(f"📦 Total de linhas exportadas: {len(df)}")

    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")


if __name__ == "__main__":
    planilha_silvio("planilhacarros.xlsx")