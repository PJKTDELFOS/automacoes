import pandas as pd
from engine_busca_pncp.db_manager import DBManager

def exportar_para_excel(nome_arquivo):
    print("📊 Iniciando exportação para Excel...")
    db=DBManager()
    conn=db.get_connection()
    try:
        query="""
        SELECT
        cnpj_cpf as "CNPJ",
                razao_social as "Razão Social",
                email as "E-mail",
                telefone as "Telefone",
                status_enriquecimento as "Status Busca",
                status_envio_campanha as "Status Envio",
                data_importacao as "Data Coleta"
            FROM public.pncp_leads_brutos
            ORDER BY data_importacao DESC
        """
        df=pd.read_sql(query,conn)
        def classificar_telefone(telefone):
            if not telefone:return 'sem telefone'
            telefone_limpo=str(telefone).replace('(','').replace(')','').replace('-', '').replace(' ', '').replace('None', '')
            if not telefone_limpo:return 'Sem telefone'
            if len(telefone_limpo)>=11:return 'Celular/WHats'
            if len(telefone_limpo)==10:return 'fixo'
            return 'outro'
        if not df.empty:
            df['Tipo telefone']=df['Telefone'].apply(classificar_telefone)
        df.to_excel(nome_arquivo, index=False,engine='openpyxl')
        print(f"✅ Sucesso! Arquivo salvo como: {nome_arquivo}")
        print(f"📦 Total de linhas exportadas: {len(df)}")
    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    exportar_para_excel("Meus_Leads_limpos.xlsx")


