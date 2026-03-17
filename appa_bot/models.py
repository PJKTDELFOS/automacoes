import uuid
from django.contrib.auth.models import User
from django.db import models
from django_cryptography.fields import encrypt
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from datetime import timedelta

# Create your models here.


def fimteste():
    return timezone.now() + timedelta(days=15)

class Stakeholder(models.Model):
    categoria = models.CharField(
        max_length=100, blank=False, null=False,
        choices=(
        ('Interessado', 'Em teste'),
        ('Cliente', 'Cliente'),
        ),
        verbose_name="Stakeholder",
        )

    nome_razaosocial=models.CharField(
        max_length=100, blank=False, null=False, verbose_name='Nome / Razão Social'
    )
    CPF_CNPJ=encrypt(
        models.CharField(
        max_length=100, blank=False, null=False, verbose_name='CPF/CNPJ'
    )
    )
    email=encrypt(
        models.EmailField(
            max_length=100, blank=False, null=False, verbose_name='E-mail'
        )
    )
    palavras_chave=ArrayField(
        models.TextField(
            max_length=5000, blank=False, null=False, verbose_name='Palavras chave',
            help_text=' digitas as palavra chave ou termos de sua busca separadas por virgula'
        )
    )
    palavras_exclusao=ArrayField(
        models.TextField(
            max_length=5000, blank=True, null=True, verbose_name='Palavras chave',
            help_text=' digitas as palavra chave ou termos de sua busca separadas por virgula'
        )
    )
    UF=ArrayField(
        models.CharField(
            max_length=2, blank=False, null=False, verbose_name='UF',
            choices=(
                ('AC', 'Acre'),('AL', 'Alagoas'),('AP', 'Amapá'),('AM', 'Amazonas'),
                ('BA', 'Bahia'),('CE', 'Ceará'),('DF', 'Distrito Federal'),
                ('ES', 'Espírito Santo'),('GO', 'Goiás'),('MA', 'Maranhão'),
                ('MT', 'Mato Grosso'),('MS', 'Mato Grosso do Sul'),
                ('MG', 'Minas Gerais'),('PA', 'Pará'),('PB', 'Paraíba'),
                ('PR', 'Paraná'),('PE', 'Pernambuco'),('PI', 'Piauí'),
                ('RJ', 'Rio de Janeiro'),('RN', 'Rio Grande do Norte'),
                ('RS', 'Rio Grande do Sul'),('RO', 'Rondônia'),
                ('RR', 'Roraima'),('SC', 'Santa Catarina'),('SP', 'São Paulo'),
                ('SE', 'Sergipe'), ('TO', 'Tocantins'),
            )
        )
    )
    periodo_busca=models.IntegerField(verbose_name='Alcance em dias da busca')
    identificador=models.UUIDField(default=uuid.uuid4, editable=False,unique=True,blank=False,
                                   verbose_name='Identificador',null=False)
    data_cadastro=models.DateTimeField(auto_now_add=True,editable=False,verbose_name='Data de Cadastro',null=False,blank=False)
    data_fim_teste=models.DateTimeField(default=fimteste,verbose_name='Fim do Período de Teste',
                                        editable=False,null=False,blank=False)
    ativo=models.BooleanField(default=True,verbose_name='Ativo')



    def __str__(self):
        return self.nome_razaosocial



    class Meta:
        verbose_name = "Stakeholder"
        verbose_name_plural = "Stakeholders"












class logAcao(models.Model):
    usuario=models.ForeignKey(User,on_delete=models.SET_NULL,verbose_name='Usuario',null=True,)
    acao=models.CharField(default=None, max_length=255, blank=False, null=False, verbose_name='Acao')
    content_type=models.ForeignKey(ContentType,on_delete=models.CASCADE)
    object_id=models.PositiveIntegerField()
    objeto=GenericForeignKey('content_type', 'object_id')
    data_hora=models.DateTimeField(auto_now_add=True,verbose_name='Data e Hora')

    class Meta:
        verbose_name = 'Log Acao'
        verbose_name_plural = 'Log de Acoes'
        ordering=('-data_hora',)

    def __str__(self):
        return f"{self.data_hora} - {self.usuario} - {self.acao} - {self.objeto}"