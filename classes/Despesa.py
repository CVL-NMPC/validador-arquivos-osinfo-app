import requests
import json
import re
import logging
import streamlit as st
from datetime import datetime
from pycpfcnpj import cpfcnpj

class Despesa:
    def __init__(self):
        self.dados = {}
        self.dados_aux = {}

    @property
    def dados(self):
        return self._dados
    
    @dados.setter
    def dados(self, value):
        self._dados = value

    @property
    def dados_aux(self):
        return self._dados_aux
    
    @dados_aux.setter
    def dados_aux(self, value):
        self._dados_aux = value
        
    def osinfo_load_from_id(self, id):
        try:
            self.id = int(id)
            url = st.secrets['base_url'] + '/expenses/server/expensesService/getExpenseFromId'
            cookie = st.secrets['cookie']
            response = requests.post(url
                                     , json=self.id
                                     , cookies={"osinfo":f"{cookie}"}
                                     )
            response.raise_for_status()
            self._load_from_json_data(response.json())
        except requests.RequestException as e:
            raise DespesaError(f"Erro na requisição: {e}", id=self.id)
        except KeyError as e:
            raise DespesaError(f"Chave ausente no retorno: {e}", id=self.id)
        except Exception as e:
            raise DespesaError(str(e), id=self.id)
        
    def osinfo_update_expense(self) -> str:
        try:
            str_json = self.get_json_BrDate()
            logging.info(str_json)

            url = st.secrets['base_url'] + '/expenses/server/expensesService/updateExpenses'
            response = requests.post(url, data=str_json, headers={'Content-Type': 'text/plain'}, timeout=10)
            response.raise_for_status()

            if 'ERROR' in response.text:
                raise DespesaError('OSINFO retornou 200 mas com mensagem de ERRO')
            if 'NOCHANGE' in response.text:
                return 'OSINFO : registros iguais'
            if 'NO FILE' in response.text:
                return 'OK - Arquivo não encontrado no painel'
            if 'OK' in response.text:
                return 'OK'
            raise DespesaError(f"OSINFO {response.text}")
        
        except requests.exceptions.Timeout as e:
            raise DespesaError(f"O tempo de espera da requisição foi atingido. Msg:{e}")
        except requests.exceptions.ConnectionError as e:
            raise DespesaError(f"Falha na conexão com o servidor. Msg:{e}")
        except requests.exceptions.HTTPError as e:
            raise DespesaError(f"HTTP: {e.response.status_code} - {e.response.text}. Msg:{e}")
        except requests.exceptions.RequestException as e:
            raise DespesaError(f"Erro desconhecido na requisição. Msg:{e}")
        except Exception as e:
            raise DespesaError(e)
    
    def load_from_json(self, jsonData):
        if isinstance(jsonData, str):
            try:
                jsonData = json.loads(jsonData)
            except json.JSONDecodeError as e:
                raise ValueError(f"Erro ao decodificar JSON: {e}")        
        self._load_from_json_data(jsonData)

    def _load_from_json_data(self, data):
        self._dados = {
            "id_documento": data['id_documento'],
            "id_log_importacao": data['id_log_importacao'],
            "cod_os": data['cod_os'],
            "data_envio": data['data_envio'],
            "cod_unidade": data['cod_unidade'],
            "id_contrato": data['id_contrato'],
            "ref_ano": data['ref_ano'],
            "ref_mes": data['ref_mes'],
            "id_tipo_documento": data['id_tipo_documento'],
            "codigo_fiscal": data['codigo_fiscal'],
            "cnpj": Despesa.check_and_format_cnpj(data['cnpj']),
            "razao": Despesa.check_and_format_razaosocial(data['razao']),
            "cpf": Despesa.check_and_format_cpf(data['cpf']),
            "nome": Despesa.check_and_format_nome(data['nome']),
            "num_documento": Despesa.check_numero_documento(data['num_documento']),
            "serie": data['serie'],
            "descricao": self.format_text_descricao(data['descricao']),
            "data_emissao": Despesa.str_to_US_str_date(data['data_emissao']),
            "data_vencimento": Despesa.str_to_US_str_date(data['data_vencimento']),
            "data_pagamento": Despesa.str_to_US_str_date(data['data_pagamento']),
            "data_apuracao": Despesa.str_to_US_str_date(data['data_apuracao']),
            "valor_documento": Despesa.format_monetary_value(data['valor_documento']),
            "valor_pago": Despesa.format_monetary_value(data['valor_pago']),
            "id_despesa": data['id_despesa'],
            "id_rubrica": data['id_rubrica'],
            "id_conta_bancaria": data['id_conta_bancaria'],
            "pmt_mes": data['pmt_mes'],
            "pmt_total": data['pmt_total'],
            "cod_bancario": data['cod_bancario'],
            "flg_justificativa": data['flg_justificativa'],
            "id_imagem": 0,
            "cod_usuario": 1236
        }
        #TODO vincular o usuário correto na alteração do painel
        # data['cod_usuario']
        self._dados_aux = {	
            "numeroContrato": data.get('numeroContrato', ''),
            "descricaoTipoDocumento": data.get('descricaoTipoDocumento', ''),
            "descricaoDespesa": data.get('descricaoDespesa', ''),
            "descricaoRubrica": data.get('descricaoRubrica', ''),
            "descricaoBanco": data.get('descricaoBanco', ''),
            "descricaoAgencia": data.get('descricaoAgencia', ''),
            "descricaoContaCorrente": data.get('descricaoContaCorrente', '')
        }

    def get_json(self):
        return json.dumps(self.dados)
    
    def get_json_BrDate(self):
        brDados = self.dados
        brDados["data_emissao"] = Despesa.str_to_BR_str_date(self.dados['data_emissao'])
        brDados["data_vencimento"] = Despesa.str_to_BR_str_date(self.dados['data_vencimento'])
        brDados["data_pagamento"] = Despesa.str_to_BR_str_date(self.dados['data_pagamento'])
        brDados["data_apuracao"] = Despesa.str_to_BR_str_date(self.dados['data_apuracao'])
        return json.dumps(brDados)

    def format_text_descricao(self, descricao) -> str:
        if '[' in descricao:
                match = re.search(r'\[(.*)\]', descricao)
                descricao = match.group(1)
        descricao = re.sub(r'\.?pdf', '', descricao.strip(), flags=re.IGNORECASE) 

        if not descricao.strip():
            raise DespesaError('A DESCRIÇÃO da despesa(nome do arquivo) não pode estar vazia ou conter só .pdf')
        
        return descricao + '.pdf'

    def check_integrity_fisica_vs_juridica(self):
        # verifica se a despesa está completa de acordo com o tipo de pessoa
        # Verifica se a despesa está preenchida apenas com os campos relativos a CPF ou CNPJ
        isFisica = False
        isJuridica = False

        if self.dados['cpf'] or self.dados['nome']:
            isFisica = True

        if self.dados['cnpj'] or self.dados['razao']:
            isJuridica = True

        if isFisica and isJuridica:
            raise DespesaError('A despesa é de ambos tipos de pessoa fisica e juridica. Verifique os dados.')

        if not isFisica and not isJuridica:
            raise DespesaError('A despesa não possui dados de Pessoa Física ou Juridica. Verifique os dados.')	
            
        if isFisica:
            if not (self.dados['cpf'] and self.dados['nome']):
                raise DespesaError('Dados incompletos para pessoa fisica. Verifique os dados.')       

        if isJuridica:
            if not (self.dados['cnpj'] and self.dados['razao']):
                raise DespesaError('Dados incompletos para pessoa juridica. Verifique os dados.')

    def check_integrity_TipoNF_vs_NumDocumento(self):
        if self.dados['id_tipo_documento'] and self.dados['id_tipo_documento'] == 1:
            if not self.dados['num_documento']:
                raise DespesaError('Necessário informar o Número do Documento para o Tipo de Documento de Nota Fiscal')
            if not re.fullmatch(r'[0-9]+', self.dados['num_documento']):
                raise DespesaError('Número do Documento inválido para o Tipo de Documento de Nota Fiscal')
                                
    def __str__(self):
        if not self.dados:
            return "Nenhuma despesa carregada."
        return "\n".join(f"{key}: {value}" for key, value in self.dados.items())

    @staticmethod
    def check_numero_documento(numdoc):
        if not numdoc or numdoc.strip() == '':
            return ''
        
        numdoc = numdoc.strip()
        if re.fullmatch(r'[a-zA-Z0-9\sà-üÀ-ÜçÇéÉãÃõÕôÔîÎûÛ_\-]+', numdoc):
            return numdoc
        
        raise DespesaError(f"O Número do Documento da despesa é inválido. Reporte ao desenvolvedor e pare a execução. {numdoc}")       

    @staticmethod
    def str_to_BR_str_date(data) -> str:
        match = re.search(r'\d{4}-\d{2}-\d{2}', data)
        if match:
            data_americana = match.group(0)
            data = datetime.strptime(data_americana, '%Y-%m-%d').strftime('%d/%m/%Y')
        return data
    
    @staticmethod
    def str_to_US_str_date(data) -> str:
        match = re.search(r'\d{2}/\d{2}/\d{4}', data)
        if match:
            data_brasileira = match.group(0)
            data = datetime.strptime(data_brasileira, '%d/%m/%Y').strftime('%Y-%m-%d')
        return data
    
    @staticmethod
    def check_and_format_cpf(cpf):
        if not cpf or cpf.strip() == '':
            return ''
        if '*' in cpf:
            raise DespesaError(f"O CPF da despesa está vindo com valores **** Reporte ao desenvolvedor e pare a execução. {cpf}")
        if cpfcnpj.validate(cpf.strip()):
            cpf_numerico = re.sub(r'[.\-\/\\]', '', cpf.strip())
            return f"{cpf_numerico[:3]}.{cpf_numerico[3:6]}.{cpf_numerico[6:9]}-{cpf_numerico[9:]}"

        raise DespesaError(f"O CPF da despesa é inválido. {cpf}")

    @staticmethod
    def check_and_format_cnpj(cnpj):
        if not cnpj or cnpj.strip() == '':
            return ''
        if '*' in cnpj:
            raise DespesaError(f"O CNPJ da despesa está vindo com valores **** Reporte ao desenvolvedor e pare a execução. {cnpj}")
        if cpfcnpj.validate(cnpj.strip()):
            cnpj_numerico = re.sub(r'[.\-\/\\]', '', cnpj.strip())
            return f"{cnpj_numerico[:2]}.{cnpj_numerico[2:5]}.{cnpj_numerico[5:8]}/{cnpj_numerico[8:12]}-{cnpj_numerico[12:]}"

        raise DespesaError(f"O CPF da despesa é inválido. {cnpj}")

    @staticmethod
    def format_monetary_value(valor):
        if type(valor) == float:
            return valor

        if type(valor) == str:
            valor = valor.replace(',','.')
            valorFatiado = valor.split('.')
            if len(valorFatiado) > 1:
                return float( ''.join(valorFatiado[:-1]) + '.' + valorFatiado[-1]) 
            return float(valorFatiado[0])
        return valor

    @staticmethod
    def check_and_format_nome(nome):    
        if not type(nome) == str:
            raise DespesaError(f"O NOME da pessoa física não é uma string. {nome}")
        
        if nome == '':
            return nome
            
        if len(nome.strip()) > 100:
            raise DespesaError(f"O NOME da pessoa física é muito grande (max 100). {nome}")

        if not re.fullmatch(r'[a-zA-Z0-9\sà-üÀ-ÜçÇéÉãÃõÕôÔîÎûÛ]+', nome.strip()):
            raise DespesaError(f"O NOME da pessoa possui caracteres inválidos. {nome}")
        
        return nome.strip()#.upper()

    @staticmethod
    def check_and_format_razaosocial(razao):
        if not type(razao) == str:
            raise DespesaError(f"A razaosocial da pessoa física não é uma string. {razao}")

        if razao == '':
            return razao

        if len(razao.strip()) > 100:
            raise DespesaError(f"A razaosocial da pessoa física é muito grande (max 100). {razao}")

        if not re.fullmatch(r'[a-zA-Z0-9\sà-üÀ-ÜçÇéÉãÃõÕôÔîÎûÛ\.,\-_&/\()\?%]+', razao.strip()):
            raise DespesaError(f"A razaosocial da pessoa possui caracteres inválidos. {razao}")
        
        return razao.strip()#.upper()

class DespesaError(Exception):
    """Exceção personalizada para erros na classe Despesa."""
    def __init__(self, message, id=None):
        if '<title>' in message:
            match = re.search(r'<title>(.*?)</title>', message, re.IGNORECASE)
            message = match.group(1)
        self.message = message.strip()
        self.id = id
        super().__init__(f"Erro ao carregar despesa: ID {id} - {message}" if id else message)