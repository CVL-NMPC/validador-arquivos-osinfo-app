import requests
import pandas as pd
import classes.BaseDFImportacao as baseDfImportacao

class ItensNotaFiscalDFImportacao (baseDfImportacao.BaseDFImportacao):
    def __init__(self, dataframe = None, base_url=None, listaOS=None, progress_bar = None, modulo = None, tipo_arquivo = None):
        super().__init__(dataframe, base_url, listaOS, progress_bar, modulo, tipo_arquivo)
        self.nome_classe = 'ITENS NOTA FISCAL'

    def load_lists_from_osinfo_subclasse(self):
        pass

    def load_lists_from_osinfo(self, index, nome_coluna = 'COD_CONTRATO'):
        pass

    def check_df_data_subclasse(self, index):
        problemas = []
        problemas.append(self.check_mandatory_fields(index))
        problemas.append(self.check_tipo_item(index))
        problemas.append(self.check_short_dates(index))
        problemas.append(self.check_cnpj(index, 'CNPJ_FORN'))
        problemas.append(self.check_currency_values_br(index))
        problemas.append(self.check_chars_len(index))
        return problemas

    def check_tipo_item(self, index):
        resultado = ''
        valor = str(self.df.at[index, 'MAT_OU_SERV'])
        if not valor in ['S', 'M']:
            resultado = f"O TIPO de documento não é valido ({valor})"
        return resultado