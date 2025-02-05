import requests
import re
import classes.BaseDFImportacao as baseDfImportacao

class DespesasDFImportacao (baseDfImportacao.BaseDFImportacao):
    def __init__(self, dataframe = None, base_url=None, listaOS=None, progress_bar = None, modulo = None, tipo_arquivo = None):
        super().__init__(dataframe, base_url, listaOS, progress_bar, modulo, tipo_arquivo)
        self.nome_classe = 'DESPESAS'

    def load_lists_from_osinfo_subclasse(self):
        self.load_bank_account_by_contract_id()
        self.load_unit_list_by_os_contract_unit_type()
        self.load_document_type_list()
        self.load_expepense_type_list()
        self.load_expenditures_list()

    def check_df_data_subclasse(self, index):
        problemas = []
        problemas.append(self.check_mandatory_fields(index))
        problemas.append(self.check_integrity_fisica_vs_juridica(index))
        problemas.append(self.check_tipo_despesa(index))
        problemas.append(self.check_rubrica(index))
        problemas.append(self.check_tipo_documento(index))
        problemas.append(self.check_integrity_TipoNF_vs_NumDocumento(index))
        problemas.append(self.check_conta_bancaria(index))
        problemas.append(self.check_full_dates(index))
        problemas.append(self.check_short_dates(index))
        problemas.append(self.check_PDF(self.df.at[index, 'DESCRICAO']))
        problemas.append(self.check_cpf(index))
        problemas.append(self.check_cnpj(index))
        problemas.append(self.check_currency_values_br(index))
        problemas.append(self.check_chars_len(index))
        return problemas

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
            resultado = f"Código de DESPESA não é valido ({valor})"
        return resultado

    def check_rubrica(self, index):
        resultado = ''
        valor = self.df.at[index, 'RUBRICA']
        dfFiltrado = self.dfRubricas[ self.dfRubricas['id_rubrica'] == int(valor) ]
        if dfFiltrado.empty:
            resultado = f"A RUBRICA não é valida ({valor})"
        return resultado
    
    def check_tipo_documento(self, index):
        resultado = ''
        valor = str(self.df.at[index, 'TIPO'])
        dfFiltrado = self.dfTiposDocumentos[ self.dfTiposDocumentos['cod_tipo_documento'] == valor ]
        if dfFiltrado.empty:
            resultado = f"O TIPO de documento não é valido ({valor})"
        return resultado

    def check_integrity_TipoNF_vs_NumDocumento(self, index):
        if not pd.isnull(self.df.at[index, 'TIPO']) and self.df.at[index, 'TIPO'] == 'NF':
            if pd.isnull(self.df.at[index, 'NUM_DOCUMENTO']):
                return 'Necessário informar o Número do Documento para o Tipo de Documento de Nota Fiscal'
            if not re.fullmatch(r'[0-9]+', self.df.at[index, 'NUM_DOCUMENTO']):
                return 'Número do Documento inválido para o Tipo de Documento de Nota Fiscal'
        return ''

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
