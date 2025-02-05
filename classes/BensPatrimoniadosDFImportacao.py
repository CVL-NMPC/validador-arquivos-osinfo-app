import requests
import re
import logging
import utils.util as util
from datetime import datetime
import pandas as pd
from pycpfcnpj import cpfcnpj

class BensPatrimoniadosDFImportacao:
    def __init__(self, dataframe = None, base_url=None, listaOS=None, progress_bar = None):
        self.df = pd.DataFrame()
        if len(dataframe):
            self.df = dataframe
        
        self.df.columns = self.df.columns.str.upper()
        self.modelo = util.Modelo()
        self.base_url = base_url
        self.url_pdf_base = base_url + "/download/{numero_da_instituicao}/45/{nome_do_pdf}"  # URL base para a verificação dos arquivos PDF.
        self.instituicao = self.df[listaOS].iloc[0,0]  # Código da instituição
        self.url_pdf_formatada = ""
        self.arquivos = {}
        self.dfTiposDocumentos = pd.DataFrame()
        self.dfUnidades = pd.DataFrame()
        self.id_contrato = None
        self.pBar = progress_bar

        self.session = requests.Session()

        self.mandadory_fields = [
            "COD_OS",
            "COD_UNIDADE",
            "COD_CONTRATO",
            "ANO_MES_REF",
            "NUM_CONTROLE_OS",
            "COD_TIPO",
            "BEM_TIPO",
            "DESCRICAO_NF",
            "CNPJ",
            "FORNECEDOR",
            "QUANTIDADE",
            "NF",
            "DATA_AQUISICAO",
            "VIDA_UTIL",
            "VALOR",
            "VINCULACAO",
            "IMG_NF"
        ]

        self.len_constraints = {
            "DESCRICAO_NF" : 255,
            "FORNECEDOR" : 255,
            "NF" : 20,
            "VINCULACAO" : 255,
            "SETOR_DESTINO" : 100
        }
    def check_header(self) -> bool:
        cabecalho = self.modelo.retornaCabecalhoBens()
        for col in cabecalho:
            if not col in self.df.columns:
                raise Exception(f"Coluna ({col}) não foi encontrada no cabeçalho do arquivo de importação de BENS PATRIMONIADOS")
        return True

    def load_lists_from_osinfo(self, index, nome_coluna = 'COD_CONTRATO'):
        try:
            if not self.df.at[index, nome_coluna]:
                raise Exception(f"O preenchimento da coluna ({nome_coluna}) é obrigatório")
            
            current_contract_id = self.dfContratos.loc[self.dfContratos['num_contrato'] == self.df.at[index, nome_coluna], 'id_contrato'].values[0]
            if self.df.at[index, nome_coluna] == '' or self.id_contrato != current_contract_id:
                self.id_contrato = current_contract_id
                if self.id_contrato is None:
                    raise Exception(f"Contrato {self.df.at[0, 'COD_CONTRATO']} não encontrado")
                self.load_unit_list_by_os_contract_unit_type()
                self.load_asset_types()
        except Exception as e:
            msg = f"check_df_data carregamento das listagens: {e}"
            logging.error(msg)
            raise Exception(msg)

    def check_df_data(self):
        self.load_contract_list()
        qtdLinhas = self.df.shape[0]
        try:
            for index, line in self.df.iterrows():
                if self.pBar:
                    self.pBar.progress(int(((index +1 ) / qtdLinhas)*100))

                self.load_lists_from_osinfo(index = index)
                problemas = []
                problemas.append(self.check_mandatory_fields(index))
                problemas.append(self.check_asset_type(index))
                problemas.append(self.check_full_dates(index))
                problemas.append(self.check_short_dates(index))
                problemas.append(self.check_PDF(self.df.at[index, 'IMG_NF']))
                problemas.append(self.check_cnpj(index))
                problemas.append(self.check_currency_values_br(index))
                problemas.append(self.check_chars_len(index))
                
                problemas_validos = [p for p in problemas if p is not None]
                problemas_validos = re.sub( '^[^a-zA-Z]*', '', ( ', '.join(problemas_validos) ) )
                problemas_validos = re.sub( '( ,)+ ?', '', problemas_validos )
                self.df.at[index, 'PROBLEMAS'] = problemas_validos

            return (len(problemas) == 0)
        except Exception as e:
            msg = f"check_df_data verificação das linhas: {e}"
            logging.error(msg)
            raise Exception(msg)

    def check_mandatory_fields(self, index):
        problemas = []
        for col in self.mandadory_fields:
            if not col in self.df.columns:
                raise Exception( f"Coluna ({col}) não foi encontrada no cabeçalho do arquivo de importação de despesas" )
            if pd.isnull(self.df.at[index, col]): 
                problemas.append( 'Valor ausente em ' + col )
        return ', '.join(problemas) if problemas else None

    def check_unidade(self, index):
        resultado = ''
        valor = str(self.df.at[index, 'COD_UNIDADE'])
        dfFiltrado = self.dfUnidades[ self.dfUnidades['cod_unidade'] == valor ]
        if dfFiltrado.empty:
            resultado = f"Código da UNIDADE não é valido ({valor})"
        return resultado

    def check_full_dates(self, index):
        resultado = ''
        for campo in self.modelo.datasCompletasBens:
            if campo in self.df.columns:
                valor = self.df.at[index, campo]
                if not pd.isnull(valor):
                    padrao = re.compile(r'^\d{4}-\d{2}-\d{2}$')
                    if not re.match(padrao, str(valor)):
                        resultado += ', ' + f"{campo} possui formato invalido {valor}"
        return resultado

    def check_short_dates(self, index):
        resultado = ''
        for campo in self.modelo.datasAbreviadasBens:
            if campo in self.df.columns:
                valor = self.df.at[index, campo]
                if not pd.isnull(valor):
                    padrao = re.compile(r'^\d{4}-\d{2}$')
                    if not re.match(padrao, str(valor)):
                        resultado += ', ' + f"{campo} possui formato invalido {valor}"
        return resultado

    def check_currency_values_br(self, index):
        resultado = ''
        for campo in self.modelo.camposMonetariosBens:
            if campo in self.df.columns:
                valor = self.df.at[index, campo]
                if not pd.isnull(valor):
                    padrao = re.compile(r'\d+(\.\d{3})*(,\d{1,2})?')
                    if not re.fullmatch(padrao, str(valor)):
                        resultado += ', ' + f"{campo} possui formato invalido {valor}"
        return resultado
           
    def check_chars_len(self, index):
        resultado = ''
        for key, value in self.len_constraints.items():
            if key in self.df.columns:
                valor = self.df.at[index, key]
                if not pd.isnull(valor):
                    if len(str(valor)) > value:
                        resultado += ', ' + f"O dado inserido na coluna {key} possui tamanho maior que {value}"
        return resultado

    def formatar_url(self, nome_imagem):
        self.coluna_imagem = nome_imagem.strip().replace(" ", "%20")
        if not self.coluna_imagem.casefold().endswith('.pdf'):
            self.coluna_imagem += '.pdf'
        self.url_pdf_formatada = self.url_pdf_base.format(numero_da_instituicao=self.instituicao, nome_do_pdf=self.coluna_imagem)       

    def check_PDF(self, nome_imagem):
        if pd.isna(nome_imagem):
            return "Campo DESCRIÇÃO não preenchido"
        self.formatar_url(nome_imagem)

        if self.url_pdf_formatada in self.arquivos:           
            return self.arquivos[self.url_pdf_formatada]
        try:
            response = self.session.head(self.url_pdf_formatada, timeout=10)
            if response.status_code == 200:
                if int(response.headers.get('Content-Length', 1)) == 0:
                    status = f"Imagem corrompida ({nome_imagem})"
                else:
                    status = ''
            else:
                status = f"Imagem ausente ({nome_imagem})"
        except requests.RequestException as e:
            status = f"Erro de verificação: {str(e)}"

        self.arquivos[self.url_pdf_formatada] = status
        return status    
    
    def check_cnpj(self, index):
        resultado = ''
        valor = self.df.at[index, 'CNPJ']
        if not pd.isnull(valor):
            if not cpfcnpj.validate(valor):
                resultado += ', ' + f"CNPJ possui formato invalido {valor}"
        return resultado
    
    def check_short_dates(self, index):
        resultado = ''
        for campo in self.modelo.datasAbreviadasBens:
            if campo in self.df.columns:
                valor = self.df.at[index, campo]
                if not pd.isnull(valor):
                    padrao = re.compile(r'^\d{4}-\d{2}$')
                    if not re.match(padrao, str(valor)):
                        resultado += ', ' + f"{campo} possui formato invalido {valor}"
        return resultado

    def check_asset_type(self, index):
        resultado = ''
        valor = self.df.at[index, 'COD_TIPO']
        dfFiltrado = self.dfTiposBens.loc[ self.dfTiposBens['id_bem_tipo'].astype(int) == int(valor) ]
        if dfFiltrado.empty:
            resultado = f"O COD_TIPO de BEM não é valido ({valor})"
        return resultado    
    
    def load_contract_list(self):
        self.dfContratos = pd.DataFrame()
        url = self.base_url + '/contract/server/contractServices/getContractsList'
        try:
            headers = {'Content-Type': 'application/json'}
            instituicao = {"id_contrato": 0, "num_contrato": "", "cod_os": str(self.instituicao), "propria_os": "S"}
            requisicao = requests.post(url, json=instituicao, headers=headers)
            requisicao.raise_for_status()
            self.dfContratos = pd.DataFrame(data=requisicao.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter a lista de contratos: {e}")

    def load_unit_list_by_os_contract_unit_type(self):
        self.dfUnidades = pd.DataFrame()
        url = self.base_url + '/common/unit/server/unitServicesOld/getUnitsListByOsContractUnitType'
        try:
            requisicao = requests.post(url, json={"cod_unidade":"","id_contrato":str(self.id_contrato),"sigla_tipo":""})
            requisicao.raise_for_status()
            self.dfUnidades = pd.DataFrame(data=requisicao.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter lista de tipos de documentos: {e}")
        
    def load_asset_types(self):
        self.dfTiposBens = pd.DataFrame()
        url = self.base_url + '/asset/server/assetService/getAssetTypes'
        try:
            requisicao = requests.post(url)
            requisicao.raise_for_status()
            self.dfTiposBens = pd.DataFrame(data=requisicao.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter lista de tipos de bens: {e}")            