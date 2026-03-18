from django.utils import timezone
from .models import Stakeholder
from django.db.models import Q

class ClienteRepository:
    @staticmethod
    def obter_clientes_ativos():
        agora=timezone.now()
        clientes_db=Stakeholder.objects.filter(
            Q(categoria='Cliente')|
            Q(categoria='Interessado',data_fim_teste__gt=agora)
        )
        lista_stakeholders_para_receber_email=[]
        for stakeholder_ativo in clientes_db:
            lista_stakeholders_para_receber_email.append(
                {
                    'nome': stakeholder_ativo.nome_razaosocial,
                    'email': stakeholder_ativo.email,
                    'uf': stakeholder_ativo.UF,
                    'palavras_chave':stakeholder_ativo.palavras_chave,
                    'palavras_exclusao': stakeholder_ativo.palavras_exclusao,
                    'identificador': str(stakeholder_ativo.identificador),
                }
            )
        return lista_stakeholders_para_receber_email

