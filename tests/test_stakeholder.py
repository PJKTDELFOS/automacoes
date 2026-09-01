import pytest
from appa_bot.models import Stakeholder



@pytest.mark.django_db
def test_cliente_esta_sempre_ativo():
    stakeholder=Stakeholder.objects.create(
        categoria="Cliente",
        nome_razaosocial="Empresa Teste",
        CPF_CNPJ="12345678900",
        email="teste@example.com",
        palavras_chave=["pythob"],
        UF=["SP"]
    )
    assert stakeholder.ativo is True