# -*- coding: utf-8 -*-
import os,re
from datetime import datetime



class Properties:
    FILE_PREFIX = "Relatorio_Appa"
    FILE_EXTENSION = ".xlsx"
    TEMP_FOLDER = "temp_planilhas"

    EMAIL_SUBJECT = "🚀 Novas Oportunidades: {cliente}"
    EMAIL_FOOTER = "Appa Licitações - Inteligência em Monitoramento"


    @staticmethod
    def get_email_body(cliente,total_encontrado,palavras_chave,uf,quantidade):
        dia = datetime.now()
        dia_do_mes = datetime.now().strftime('%d/%m/%Y')
        termos_str = ", ".join([t.upper() for t in palavras_chave])
        cor_primaria = "#2c3e50"
        cor_destaque = "#3498db"

        mensagem=f"""
            <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
                    <div style="background-color: {cor_primaria}; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0; font-size: 20px;">Relatório de Oportunidades PNCP</h1>
                        <p style="margin: 5px 0 0 0; opacity: 0.8;">Monitoramento Inteligente de Licitações</p>
                    </div>

                    <div style="padding: 20px;">
                        <p>Olá, <strong>{cliente}</strong>,</p>
                        <p>Identificamos novas oportunidades no PNCP que coincidem com o seu perfil de busca.</p>

                        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background-color: #f9f9f9;">
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Hora envio:</strong></td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{dia.strftime('%H:%M')}</td>
                            </tr>
                             <tr>
                                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Data:</strong></td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{dia_do_mes}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Oportunidades:</strong></td>
                                <td style="padding: 10px; border: 1px solid #ddd; color: {cor_destaque}; font-weight: bold;">{quantidade} encontradas</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Filtro:</strong></td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{uf if uf else 'Brasil (Nacional)'}</td>
                            </tr>
                        </table>

                        <p style="font-size: 14px;"><strong>Termos monitorados nesta rodada:</strong><br>
                        <span style="color: #666;">{termos_str}</span></p>

                        <div style="background-color: #fff3cd; border-left: 5px solid #ffecb5; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; font-size: 14px; color: #856404;">
                                <strong>Importante:</strong> Os detalhes completos, prazos e links diretos estão disponíveis na planilha em anexo.
                            </p>
                        </div>
                    </div>

                    <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 12px; color: #999;">
                        <p style="margin: 0;">Este é um serviço automatizado. Por favor, não responda a este e-mail.</p>
                        <p style="margin: 5px 0 0 0;">&copy; 2026 Seu Sistema de Monitoramento</p>
                    </div>
                </div>
            </body>
            </html>
            """
        return mensagem

    @staticmethod
    def gerar_nome_arquivo(cliente):

        data_str = datetime.now().strftime("%d_%m_%Y")

        nome_limpo = re.sub(
            r'[^a-zA-Z0-9_]','_',
            cliente.lower()
        )
        nome_arquivo=f'{Properties.FILE_PREFIX}_{nome_limpo}_{data_str}{Properties.FILE_EXTENSION}'
        return nome_arquivo

    @staticmethod
    def get_temp_path(nome_arquivo):
        base=os.path.abspath(Properties.TEMP_FOLDER)
        caminho=os.path.abspath(
            os.path.join(base, nome_arquivo)
        )
        if not caminho.startswith(base+os.sep):
            raise ValueError(f"Nome de cliente inválido: tentativa de path traversal detectada")
        return caminho








