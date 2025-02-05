import pandas as pd
import base64

class DataFrameUtils:
    @staticmethod
    def adiciona_linhas_erro(df_principal, df_erro, mensagem_erro, coluna_erro='ERROS'):
        if coluna_erro not in df_principal.columns:
            df_principal.insert(len(df_principal.columns), coluna_erro, '')

        df_erro[coluna_erro] = mensagem_erro
        df_principal = pd.concat([df_principal, df_erro])
        return df_principal

    @staticmethod
    def convert_df_to_csv(df):
        csv = df.to_csv(index=False, sep=';')
        return csv

    @staticmethod
    def get_download_link(df):
        csv = DataFrameUtils.convert_df_to_csv(df)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="AlteraçoesNaoAtendidasDespesa.csv">Clique aqui para baixar o CSV com somente as linhas que não foram atendidas</a>'
        return href    