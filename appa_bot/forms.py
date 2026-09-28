from django import forms
from .models import Stakeholder

# Lista completa de opções incluindo o atalho 'BR' para a interface
ALL_UFS = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO', 'BR'
]

# Lista apenas com as 27 UFs reais para gravação final no banco de dados
ESTADOS_SOLIDOS = [uf for uf in ALL_UFS if uf != 'BR']

# Puxa as opções de escolha direto do modelo
uf_choices = Stakeholder._meta.get_field('UF').base_field.choices


class StakeholderForm(forms.ModelForm):
    UF = forms.MultipleChoiceField(
        choices=uf_choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='UF'
    )

    class Meta:
        model = Stakeholder
        fields = ('nome_razaosocial', 'email', 'CPF_CNPJ', 'palavras_chave', 'palavras_exclusao', 'UF')
        labels = {
            'nome_razaosocial': 'Nome ou Razão Social',
            'email': 'E-mail',
            'CPF_CNPJ': 'CPF/CNPJ',
            'palavras_chave': 'Palavra-Chave para pesquisa',
            'palavras_exclusao': 'Palavras para nao pesquisar',
            'UF': 'UF'
        }
        widgets = {
            'palavras_chave': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Digite as palavras-chave separadas por vírgula...'
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Normaliza maiúsculas nos dados recebidos via POST/GET
        if args and len(args) > 0 and args[0]:
            data = args[0].copy()
            if hasattr(data, 'getlist'):
                ufs = data.getlist('UF')
                data.setlist('UF', [uf.upper() for uf in ufs])
            elif 'UF' in data:
                if isinstance(data['UF'], str):
                    data['UF'] = data['UF'].upper()
                elif isinstance(data['UF'], list):
                    data['UF'] = [uf.upper() for uf in data['UF']]

            args = list(args)
            args[0] = data
            args = tuple(args)
        elif 'data' in kwargs and kwargs['data']:
            data = kwargs['data'].copy()
            if hasattr(data, 'getlist'):
                ufs = data.getlist('UF')
                data.setlist('UF', [uf.upper() for uf in ufs])
            elif 'UF' in data:
                if isinstance(data['UF'], str):
                    data['UF'] = data['UF'].upper()
                elif isinstance(data['UF'], list):
                    data['UF'] = [uf.upper() for uf in data['UF']]
            kwargs['data'] = data

        super().__init__(*args, **kwargs)

        # Garante que na abertura da página (GET) venha tudo selecionado por padrão
        if not self.is_bound and not self.initial.get('UF'):
            self.initial['UF'] = ALL_UFS

    def clean_UF(self):
        ufs = self.cleaned_data.get('UF', [])
        # Se marcou 'BR' ou enviou vazio, expande e salva todos os 27 estados reais
        if not ufs or 'BR' in ufs:
            return ESTADOS_SOLIDOS
        # Retorna apenas as UFs válidas selecionadas manualmente
        return [str(uf).upper() for uf in ufs if uf in ESTADOS_SOLIDOS]


class AtualizarStakeHolderForm(forms.ModelForm):
    UF = forms.MultipleChoiceField(
        choices=uf_choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='UF'
    )

    class Meta:
        model = Stakeholder
        fields = ('palavras_chave', 'palavras_exclusao', 'UF')
        labels = {
            'palavras_chave': 'Palavra Chave',
            'palavras_exclusao': 'Palavras para nao pesquisar',
            'UF': 'UF'
        }
        widgets = {
            'palavras_chave': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Digite as palavras-chave separadas por vírgula...'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Normalização de maiúsculas para o formulário de atualização
        if args and len(args) > 0 and args[0]:
            data = args[0].copy()
            if hasattr(data, 'getlist'):
                ufs = data.getlist('UF')
                data.setlist('UF', [uf.upper() for uf in ufs])
            elif 'UF' in data:
                if isinstance(data['UF'], str):
                    data['UF'] = data['UF'].upper()
                elif isinstance(data['UF'], list):
                    data['UF'] = [uf.upper() for uf in data['UF']]

            args = list(args)
            args[0] = data
            args = tuple(args)
        elif 'data' in kwargs and kwargs['data']:
            data = kwargs['data'].copy()
            if hasattr(data, 'getlist'):
                ufs = data.getlist('UF')
                data.setlist('UF', [uf.upper() for uf in ufs])
            elif 'UF' in data:
                if isinstance(data['UF'], str):
                    data['UF'] = data['UF'].upper()
                elif isinstance(data['UF'], list):
                    data['UF'] = [uf.upper() for uf in data['UF']]
            kwargs['data'] = data

        super().__init__(*args, **kwargs)

        if not self.is_bound and not self.initial.get('UF'):
            self.initial['UF'] = ALL_UFS

    def clean_UF(self):
        ufs = self.cleaned_data.get('UF', [])
        if not ufs or 'BR' in ufs:
            return ESTADOS_SOLIDOS
        return [str(uf).upper() for uf in ufs if uf in ESTADOS_SOLIDOS]