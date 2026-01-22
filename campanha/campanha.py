import time
from disparador import Disparador_de_emails
import random
from engine_busca_pncp.db_manager import DBManager
#reverter a correção caso o banco de dados de email nao se mostrar viavel


def busca_leads(limite=50):
    db=DBManager()
    conn=db.get_connection()
    lista_formatada=[]
    try:
        with conn.cursor() as cursor:
            query="""
                SELECT cnpj_cpf, razao_social, email 
                FROM public.pncp_leads_brutos 
                WHERE status_enriquecimento = 'PROCESSADO' 
                AND (status_envio_campanha IS NULL OR status_envio_campanha = 'PENDENTE')
                AND email IS NOT NULL
                LIMIT %s
            """
            cursor.execute(query,(limite,))
            resultados=cursor.fetchall()

            for row in resultados:
                cnpj,nome,email=row
                lista_formatada.append(
                    {'cnpj':cnpj, 'nome':nome, 'email':email}
                )
    except Exception as e:
        print(f"❌ Erro ao buscar no banco: {e}")
    finally:
        conn.close()
    return lista_formatada

def campanha(lista_clientes):
    db=DBManager()
    sucesso=0
    print(f"🚀 Iniciando envio para {len(lista_clientes)} clientes...")

    for i, cliente in enumerate(lista_clientes,1):
        print(f"[{i}] Enviando para: {cliente['nome']}...")
        disparador=Disparador_de_emails(cliente['email'],cliente['nome'])
        mensagem=disparador.mensagem()
        assunto=f"Oportunidade para {cliente['nome']}"
        envio=disparador._enviar_gmail(cliente['email'],assunto,mensagem)
        if envio:
            print('enviado')
            sucesso+=1
            db.atualizar_status_campanha(cliente['cnpj'],status_novo='sucesso')
        else:
            db.atualizar_status_campanha(cliente['cnpj'], status_novo='fracasso')
        tempo=random.randint(15,30)
        time.sleep(tempo)

if __name__ == '__main__':
    leads=busca_leads(limite=50)
    if leads:
        campanha(leads)
    else:
        print("Nenhum cliente foi enviado")





