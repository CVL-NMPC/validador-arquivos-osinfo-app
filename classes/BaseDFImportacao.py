import requests
import re
import logging
import utils.util as util
import pandas as pd
from pycpfcnpj import cpfcnpj
import classes.ModelosArquivos as modeloArquivos

class BaseDFImportacao:
    def __init__(self, dataframe = None, base_url=None, listaOS=None, progress_bar = None, modulo = None, tipo_arquivo = None):
        self.df = pd.DataFrame()
        if len(dataframe):
            self.df = dataframe
        
        self.df.columns = self.df.columns.str.upper()
        self.modelo = modeloArquivos.ModeloArqruivos(modulo, tipo_arquivo)
        self.base_url = base_url
        self.url_pdf_base = base_url + "/download/{numero_da_instituicao}/45/{nome_do_pdf}"
        self.instituicao = self.df[listaOS].iloc[0,0]  # Código da instituição
        self.url_pdf_formatada = ""
        self.arquivos = {}
        self.id_contrato = None
        self.pBar = progress_bar
        self.dfCodigosDespesas = pd.DataFrame()
        self.dfRubricas = pd.DataFrame()
        self.dfTiposDocumentos = pd.DataFrame()
        self.dfUnidades = pd.DataFrame()
        self.dfContasBancarias = pd.DataFrame()
        self.session = requests.Session()

        # definir na subclasse
        self.nome_classe = 'DEFINIR CLASSE'
        

    def check_header(self) -> bool:
        cabecalho = self.modelo.retornaCabecalho()
        for col in cabecalho:
            if not col in self.df.columns:
                raise Exception(f"Coluna ({col}) não foi encontrada no cabeçalho do arquivo de importação de self.nome_classe")
        return True

    def load_lists_from_osinfo_subclasse(self):
        #sobrescrever nas classes filhas
        pass

    def load_lists_from_osinfo(self, index, nome_coluna = 'COD_CONTRATO'):
        result = False
        try:
            if not self.df.at[index, nome_coluna]:
                raise Exception(f"O preenchimento da coluna ({nome_coluna}) é obrigatório")
            
            current_contract_id = self.dfContratos.loc[self.dfContratos['num_contrato'] == self.df.at[index, nome_coluna], 'id_contrato'].values[0]
            if self.df.at[index, nome_coluna] == '' or self.id_contrato != current_contract_id:
                self.id_contrato = current_contract_id

                if self.id_contrato is None:
                    raise Exception(f"Contrato {self.df.at[0, 'COD_CONTRATO']} não encontrado")
                
                self.load_lists_from_osinfo_subclasse()
                
        except Exception as e:
            msg = f"check_df_data carregamento das listagens: {e}"
            logging.error(msg)
            raise Exception(msg)

    def check_df_data_subclasse(self, index):
        return []
        #sobrescrever nas classes filhas

    def check_df_data(self):
        self.load_contract_list()
        qtdLinhas = self.df.shape[0]
        try:
            for index, line in self.df.iterrows():
                if self.pBar:
                    self.pBar.progress(int(((index +1 ) / qtdLinhas)*100))
                                    
                self.load_lists_from_osinfo(index = index)
                
                problemas = self.check_df_data_subclasse(index)
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
        for col in self.modelo.camposObrigatorios:
            if not col in self.df.columns:
                raise Exception(f"Coluna ({col}) não foi encontrada na no cabeçalho do arquivo de importação de despesas")
            if pd.isnull(self.df.at[index, col]): 
                problemas.append('Valor ausente em ' + col )
        return ', '.join(problemas) if problemas else None

    def check_unidade(self, index):
        resultado = ''
        valor = str(self.df.at[index, 'COD_UNIDADE'])
        dfFiltrado = self.dfUnidades[ self.dfUnidades['cod_unidade'] == valor ]
        if dfFiltrado.empty:
            resultado = f"Código da UNIDADE não é valido ({valor})"
        return resultado


    def check_integrity_fisica_vs_juridica(self, index):
        # verifica se a despesa está completa de acordo com o tipo de pessoa
        # Verifica se a despesa está preenchida apenas com os campos relativos a CPF ou CNPJ
        isFisica = False
        isJuridica = False

        if not pd.isnull(self.df.at[index, 'CPF']) or not pd.isnull(self.df.at[index, 'NOME']):
            isFisica = True

        if not pd.isnull(self.df.at[index, 'CNPJ']) or not pd.isnull(self.df.at[index, 'RAZAO']):
            isJuridica = True

        if isFisica and isJuridica:
            return 'A despesa é de ambos tipos de pessoa fisica e juridica.'

        if not isFisica and not isJuridica:
            return 'A despesa não possui dados de Pessoa Física ou Juridica.'
            
        if isFisica:
            if not (self.df.at[index, 'CPF'] and self.df.at[index, 'NOME']):
                return 'Dados incompletos para pessoa fisica.'

        if isJuridica:
            if not (self.df.at[index, 'CNPJ'] and self.df.at[index, 'RAZAO']):
                return 'Dados incompletos para pessoa juridica.'

    def check_tipo_despesa(self, index):
        resultado = ''
        valor = str(self.df.at[index, 'DESPESA'])
        dfFiltrado = self.dfCodigosDespesas[ self.dfCodigosDespesas['cod_despesa'] == valor ]
        if dfFiltrado.empty:
            resultado = f"Código de DESPESA não é valido"
        return resultado

    def check_rubrica(self, index):
        resultado = ''
        valor = self.df.at[index, 'RUBRICA']
        dfFiltrado = self.dfRubricas[ self.dfRubricas['id_rubrica'] == int(valor) ]
        if dfFiltrado.empty:
            resultado = f"A RUBRICA não é valida"
        return resultado
    
    def check_tipo_documento(self, index):
        resultado = ''
        valor = str(self.df.at[index, 'TIPO'])
        dfFiltrado = self.dfTiposDocumentos[ self.dfTiposDocumentos['cod_tipo_documento'] == valor ]
        if dfFiltrado.empty:
            resultado = f"O TIPO de documento não é valido"
        return resultado

    def check_integrity_TipoNF_vs_NumDocumento(self, index):
        if not pd.isnull(self.df.at[index, 'TIPO']) and self.df.at[index, 'TIPO'] == 'NF':
            if pd.isnull(self.df.at[index, 'NUM_DOCUMENTO']):
                return 'Necessário informar o Número do Documento para o Tipo de Documento de Nota Fiscal'
            if not re.fullmatch(r'[0-9]+', self.df.at[index, 'NUM_DOCUMENTO']):
                return 'Número do Documento inválido para o Tipo de Documento de Nota Fiscal'
        return ''

    def check_conta_bancaria(self, index):
        resultado = ''
        agencia = self.df.at[index, 'AGENCIA']
        conta = self.df.at[index, 'CONTA_CORRENTE']
        dfFiltrado = self.dfContasBancarias[ (self.dfContasBancarias['codigo_agencia'] == int(agencia)) & (self.dfContasBancarias['conta_e_digito'] == conta) ]
        if dfFiltrado.empty:
            resultado = f"Os campos AGENCIA e CONTA_CORRENTE não parecem corretos para esse contrato ({agencia}, {conta})"
        return resultado    

    def check_full_dates(self, index):
        resultado = ''
        for campo in self.modelo.datasCompletas:
            if campo in self.df.columns:
                valor = self.df.at[index, campo]
                if not pd.isnull(valor):
                    padrao = re.compile(r'^\d{4}-\d{2}-\d{2}$')
                    if not re.match(padrao, str(valor)):
                        resultado += ', ' + f"{campo} possui formato invalido"
        return resultado

    def check_short_dates(self, index):
        resultado = ''
        for campo in self.modelo.datasAbrevidadas:
            if campo in self.df.columns:
                valor = self.df.at[index, campo]
                if not pd.isnull(valor):
                    padrao = re.compile(r'^\d{4}-\d{2}$')
                    if not re.match(padrao, str(valor)):
                        resultado += ', ' + f"{campo} possui formato invalido"
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
    
    def check_cpf(self, index):
        resultado = ''
        valor = self.df.at[index, 'CPF']
        if not pd.isnull(valor):
            if not cpfcnpj.validate(valor):
                resultado += ', ' + f"CPF possui formato invalido"
        return resultado

    def check_cnpj(self, index, campo = 'CNPJ'):
        resultado = ''
        valor = self.df.at[index, campo]
        if not pd.isnull(valor):
            if not cpfcnpj.validate(valor):
                resultado += ', ' + f"{campo} possui formato invalido"
        return resultado
    
    def check_short_dates(self, index):
        resultado = ''
        for campo in self.modelo.datasAbreviadas:
            if campo in self.df.columns:
                valor = self.df.at[index, campo]
                if not pd.isnull(valor):
                    padrao = re.compile(r'^\d{4}-\d{2}$')
                    if not re.match(padrao, str(valor)):
                        resultado += ', ' + f"{campo} possui formato invalido"
        return resultado
    
    def check_currency_values_br(self, index):
        resultado = ''
        for campo in self.modelo.camposMonetarios:
            if campo in self.df.columns:
                valor = self.df.at[index, campo]
                if not pd.isnull(valor):
                    padrao = re.compile(r'\d+(\.\d{3})*(,\d{1,2})?')
                    if not re.fullmatch(padrao, str(valor)):
                        resultado += ', ' + f"{campo} possui formato invalido"
        return resultado  
        
    def check_chars_len(self, index):
        resultado = ''
        for key, value in self.modelo.limitesTamanho.items():
            if key in self.df.columns:
                valor = self.df.at[index, key]
                if not pd.isnull(valor):
                    if len(str(valor)) > value:
                        resultado += ', ' + f"O dado inserido na coluna {key} possui tamanho maior que {value}"
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

    def load_expepense_type_list(self):
        self.dfCodigosDespesas = pd.DataFrame()
        url = self.base_url + '/expenseType/server/expenseTypeServices/getExpenseTypesList'
        try:
            requisicao = requests.post(url)
            requisicao.raise_for_status()
            self.dfCodigosDespesas = pd.DataFrame(data=requisicao.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter códigos de despesa: {e}")

    def load_expenditures_list(self):
        self.dfRubricas = pd.DataFrame()
        url = self.base_url + '/expenditure/server/expenditureServices/getExpendituresList'
        try:
            requisicao = requests.post(url)
            requisicao.raise_for_status()
            self.dfRubricas = pd.DataFrame(data=requisicao.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter lista de Rubricas: {e}")     

    def load_document_type_list(self):
        self.dfTiposDocumentos = pd.DataFrame()
        url = self.base_url + '/documentType/server/documentTypeServices/getDocumentTypesList'
        try:
            requisicao = requests.post(url)
            requisicao.raise_for_status()
            self.dfTiposDocumentos= pd.DataFrame(data=requisicao.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter lista de tipos de documentos: {e}")    

    def load_bank_account_by_contract_id(self):
        self.dfContasBancarias = pd.DataFrame()
        url = self.base_url + '/bankAccount/server/bankAccountServices/getBankAccountByContractId'
        try:
            requisicao = requests.post(url, json=str(self.id_contrato))
            requisicao.raise_for_status()
            self.dfContasBancarias = pd.DataFrame(data=requisicao.json())
            self.dfContasBancarias['conta_e_digito'] = [f"{x}{y}" for x,y in zip(self.dfContasBancarias['codigo_cc'], self.dfContasBancarias['digito_cc']) ]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter lista de tipos de documentos: {e}")  

    def load_unit_list_by_os_contract_unit_type(self):
        self.dfUnidades = pd.DataFrame()
        url = self.base_url + '/common/unit/server/unitServicesOld/getUnitsListByOsContractUnitType'
        try:
            requisicao = requests.post(url, json={"cod_unidade":"","id_contrato":str(self.id_contrato),"sigla_tipo":""})
            requisicao.raise_for_status()
            self.dfUnidades = pd.DataFrame(data=requisicao.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter lista de tipos de documentos: {e}")