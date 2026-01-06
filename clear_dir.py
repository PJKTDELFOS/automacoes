import shutil
import os
from engine_busca_pncp.propriedades import Properties

def Cleardirectory():
    dir=Properties.TEMP_FOLDER
    if os.path.exists(dir):
        try:
            for arquivo in os.listdir(dir):
                file_path=os.path.join(dir, arquivo)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            print('Erro ao limpar a pasta')
            print(e)
    else:
        print(f'Pasta; {dir} nao encontrado')