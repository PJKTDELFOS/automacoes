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

    def __init__(self, *args, **kwargs):
        temp_data=None
        use_args=None
        if len (args)>0:
            temp_data=args[0]
            use_args=True
            if 'data' in kwargs:
                temp_data=kwargs['data']

            if temp_data is not None:
                data=temp_data.copy()
                if hasattr(data,'getlist'):
                    ufs=data.getlist('UF')
                    data.setlist('UF',
                                 [uf.upper() for uf in ufs])
                elif 'UF'in data:
                    if isinstance(data['UF'],str):
                        data['UF'] = data['UF'].upper()
                    elif isinstance(data['UF'],list):
                        data['UF'] = [uf.upper() for uf in data['UF']]
                if use_args:
                    args=list(args)
                    args[0]=data
                    args=tuple(args)
                else:
                    kwargs['data']=data
        super().__init__(*args, **kwargs)


class AtualizarStakeHolderForm(forms.ModelForm):
    class Meta:
        model = Stakeholder
        fields = ('palavras_chave', 'palavras_exclusao','UF')
        labels = {
            'palavras_chave': 'Palavra Chave',
            'palavras_exclusao': 'Palavras para nao pesquisar',
            'UF': 'UF'
        }

    def __init__(self, *args, **kwargs):
        temp_data = None
        use_args = None
        if len(args) > 0:
            temp_data = args[0]
            use_args = True
            if 'data' in kwargs:
                temp_data = kwargs['data']

            if temp_data is not None:
                data = temp_data.copy()
                if hasattr(data, 'getlist'):
                    ufs = data.getlist('UF')
                    data.setlist('UF',
                                 [uf.upper() for uf in ufs])
                elif 'UF' in data:
                    if isinstance(data['UF'], str):
                        data['UF'] = data['UF'].upper()
                    elif isinstance(data['UF'], list):
                        data['UF'] = [uf.upper() for uf in data['UF']]
                if use_args:
                    args = list(args)
                    args[0] = data
                    args = tuple(args)
                else:
                    kwargs['data'] = data
        super().__init__(*args, **kwargs)


