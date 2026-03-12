from operator import indexOf

import pytest
from engine_campanha.buscador_emails import BuscadorEmails


class BancoFalso:
    pass


def test_validador_email():
    robo=BuscadorEmails(db_manager=BancoFalso())
    resultado=robo.validar_email('contato@empresa.com.br')
    assert resultado =='contato@empresa.com.br'

def test_deve_recusar_sem_arroba():
    robo=BuscadorEmails(db_manager=BancoFalso())
    resultado=robo.validar_email('contatoempresa.com.br')
    assert resultado is None

def test_deve_ter_no_maximo_255():
    email_errado='a'*260+'@exemplo.com.br'
    robo=BuscadorEmails(db_manager=BancoFalso())
    resultado=robo.validar_email(email_errado)
    assert resultado is None
def test_email_nao_pode_vir_vazio():
    robo=BuscadorEmails(db_manager=BancoFalso())
    resultado_none=robo.validar_email(None)
    resultado_string_vazia=robo.validar_email('')
    assert resultado_none is None
    assert resultado_string_vazia is None

def test_tem_arroba_no_email():
    robo=BuscadorEmails(db_manager=BancoFalso())
    resultado=robo.validar_email('email@empresa.com.br')
    if not '@' in resultado:
        assert resultado is None
    assert resultado =='email@empresa.com.br'


















