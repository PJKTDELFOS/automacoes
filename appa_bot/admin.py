from django.contrib import admin
from .models import Stakeholder,logAcao
# Register your models here.



@admin.register(Stakeholder)
class StakeholderAdmin(admin.ModelAdmin):
    list_display = (
        'nome_razaosocial',
        'categoria',
        'data_cadastro',
        'data_fim_teste',
        'mostrar_ativo'
    )
    list_filter = ('categoria',)
    search_fields = ('nome_razaosocial','identificador')
    readonly_fields = ('identificador', 'data_cadastro')

    @admin.display(boolean=True, description='Ativo no Robô')
    def mostrar_ativo(self, obj):
        return obj.ativo


@admin.register(logAcao)
class LogAcaoAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'usuario', 'acao', 'content_type')
    list_filter = ('acao', 'data_hora')
    search_fields = ('acao',)
    readonly_fields = ('data_hora', 'usuario', 'acao', 'content_type', 'object_id')


    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False



