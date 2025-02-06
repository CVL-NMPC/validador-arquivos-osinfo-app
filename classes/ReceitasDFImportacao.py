import requests
import pandas as pd
import classes.BaseDFImportacao as baseDfImportacao

class ReceitasDFImportacao (baseDfImportacao.BaseDFImportacao):
    def __init__(self, dataframe = None, base_url=None, listaOS=None, progress_bar = None, modulo = None, tipo_arquivo = None):
        super().__init__(dataframe, base_url, listaOS, progress_bar, modulo, tipo_arquivo)
        self.nome_classe = 'RECEITAS'

    def load_lists_from_osinfo_subclasse(self):
        # Implementar a chamada das listas já existentes ou implementar a criação das listas necessarias
        pass

    def check_df_data_subclasse(self, index):
        problemas = []
        # Implementar a verificação das linhas ou chamar as existentes necessarias
        return problemas