from django import forms
from .models import Stakeholder



class StakeholderForm(forms.ModelForm):
    class Meta:
        model = Stakeholder
        fields = ('nome_razaosocial','email','CPF_CNPJ','palavras_chave','palavras_exclusao','UF')
        labels={
            'nome_razaosocial':'Nome ou Razão Social',
            'email':'E-mail',
            'CPF_CNPJ':'CPF/CNPJ',
            'palavras_chave':'Palavra-Chave para pesquisa',
            'palavras_exclusao':'Palavras para nao pesquisar',
            'UF':'UF'
        }

class AtualizarStakeHolderForm(forms.ModelForm):
    class Meta:
        model = Stakeholder
        fields = ('palavras_chave', 'palavras_exclusao','UF')
        labels = {
            'palavras_chave': 'Palavra Chave',
            'palavras_exclusao': 'Palavras para nao pesquisar',
            'UF': 'UF'
        }


