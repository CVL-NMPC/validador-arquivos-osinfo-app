import pandas as pd
import requests
import json
import re
## DEBUG ##
#import streamlit as st

# Dicionário de erros
erros = {
    "01": "Todos os campos devem ser preenchidos!",
    "02": "O arquivo NÃO está no formato UTF-8!",
    "03": "O arquivo não tem o layout de Despesas ou não é compatível com o modelo DESPESAS GNOSIS.",
    "04": "O arquivo não tem o layout de Contratos de Terceiros ou não é compatível com o modelo ANEXOS.",
    "05": 'O arquivo não tem o layout de Contratos de Saldos ou não é compatível com o modelo SALDO IPCEP.',
    "06": 'O arquivo não tem o layout de Bens Patrimoniados ou não é compatível com o modelo BENS CEP28.'
}

def carregaSecretarias():
    arqSecretaria = open('data/secretarias.json')
    dadosSecretarias = json.load(arqSecretaria)
    arqSecretaria.close()
    opcoes = []

    for secretaria in dadosSecretarias["secretarias"]:
        opcoes.append(secretaria["nome_secretaria"])
    
    return opcoes

def carregaInstituicoes():
    arqInstituicoes = open("data/instituicoes.json")
    dadosInstituicoes = json.load(arqInstituicoes)
    arqInstituicoes.close()
    opcoes = []

    for instituicao in dadosInstituicoes["VW_OS"]:
        opcoes.append(instituicao["DSC_OS"])
    
    return opcoes

def carregaContratos():
    arqContratos = open("data/contratos.json")
    dadosContratos = json.load(arqContratos)
    arqContratos.close()
    opcoes = []

    for contrato in dadosContratos["VW_CONTRATO_V2"]:
        opcoes.append(contrato["DSC_CONTRATO"])
    
    opcoes.sort()
    return opcoes

def carregaInstrumentos():
    arqContratos = open("data/contratos.json")
    dadosContratos = json.load(arqContratos)
    arqContratos.close()

    return dadosContratos

class Validadora:
    def __init__(self, base_url, instituicao):
        self.base_url = base_url  # URL base para a verificação dos arquivos PDF.
        self.instituicao = instituicao  # Código da instituição
        self.url_formatada = ""
        self.arquivos = {}
        self.session = requests.Session()  # Use uma sessão para melhor desempenho em múltiplas requisições

    def formatar_url(self, nome_imagem):
        # Remove leading/trailing spaces and replace spaces with %20 for URL encoding
        self.coluna_imagem = nome_imagem.strip().replace(" ", "%20")
        # Ensure the file name ends with .pdf
        if not self.coluna_imagem.casefold().endswith('.pdf'):
            self.coluna_imagem += '.pdf'
        # Format the URL with the institution code and the PDF file name
        self.url_formatada = self.base_url.format(numero_da_instituicao=self.instituicao, nome_do_pdf=self.coluna_imagem)

    def validarPDF(self, nome_imagem):
        if nome_imagem is None:
            return "Campo não preenchido"
        
        self.formatar_url(nome_imagem)

        # Return cached result if available        
        if self.url_formatada in self.arquivos:           
            return self.arquivos[self.url_formatada]
        try:
            response = self.session.head(self.url_formatada, timeout=10)
            # Evaluate the file status based on the header's Content-Length
            if response.status_code == 200:
                if int(response.headers.get('Content-Length', 1)) == 0:
                    status = 'Corrompido'
                else:
                    status = 'Sim'
            else:
                status = 'Não'

        except requests.RequestException as e:
            status = f'Erro de verificação: {str(e)}'

        self.arquivos[self.url_formatada] = status
        return status

    def validarData(self, data=None):
        padrao = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        if data is not None:
            if re.match(padrao, str(data)):
                return "Sim"
            else:
                return "Não"
        else:
            return "Não"

    def validarDataAbreviada(self, data=None):
        padrao = re.compile(r'^\d{4}-\d{2}$')
        if data is not None:
            if re.match(padrao, str(data)):
                return "Sim"
            else:
                return "Não"
        else:
            return "Não"

class Modelo:
    def __init__(self):
        self.Despesas = 'COD_OS;COD_UNIDADE;COD_CONTRATO;ANO_MES_REF;TIPO;CODIGO;CNPJ;RAZAO;CPF;NOME;NUM_DOCUMENTO;SERIE;DESCRICAO;DATA_EMISSAO;DATA_VENCIMENTO;DATA_PAGAMENTO;DATA_APURACAO;VALOR_DOCUMENTO;VALOR_PAGO;DESPESA;RUBRICA;BANCO;AGENCIA;CONTA_CORRENTE;PMT_PAGA;QTDE_PMT;IDENT_BANCARIO;FLAG_JUSTIFICATIVA'
        self.ContratosTerceiros = 'COD_OS;COD_UNIDADE;COD_CONTRATO;RAZAO_SOCIAL;CNPJ;SERVICO;VALOR_MES;VIGENCIA;CONTRATO_ANO_MES_INICIO;CONTRATO_ANO_MES_FIM;REF_TRI;REF_ANO_MES;IMG_CONTRATO'
        self.Saldos = 'COD_OS;COD_UNIDADE;COD_CONTRATO;ANO_MES_REF;BANCO;AGENCIA;CONTA_CORRENTE;VL_CONTA_CORRENTE;VL_APL_FINANCEIRA;VL_CONTA_PROVISAO;VL_EM_ESPECIE;EXTRATO'
        self.Bens = 'COD_OS;COD_UNIDADE;COD_CONTRATO;ANO_MES_REF;NUM_CONTROLE_OS;NUM_CONTROLE_GOV;COD_TIPO;BEM_TIPO;DESCRICAO_NF;CNPJ;FORNECEDOR;QUANTIDADE;NF;DATA_AQUISICAO;VIDA_UTIL;VALOR;VINCULACAO;SETOR_DESTINO;IMG_NF'
        self.Alteracao = ''
        self.cabecalhoDespesas = []
        self.cabecalhoContratosTerceiros = []
        self.cabecalhoSaldos = []
        self.cabecalhoBens = []

    def retornaCabecalhoDespesas(self):     
        if not self.cabecalhoDespesas:
            self.cabecalhoDespesas = self.trataCabecalho(self.Despesas)
            return self.cabecalhoDespesas
        else:        
            return self.cabecalhoDespesas
    
    def retornaCabecalhoContratosTerceiros(self):     
        if not self.cabecalhoContratosTerceiros:
            self.cabecalhoContratosTerceiros = self.trataCabecalho(self.ContratosTerceiros)
            return self.cabecalhoContratosTerceiros
        else:        
            return self.cabecalhoContratosTerceiros
        
    def retornaCabecalhoSaldos(self):     
        if not self.cabecalhoSaldos:
            self.cabecalhoSaldos = self.trataCabecalho(self.Saldos)
            return self.cabecalhoSaldos
        else:        
            return self.cabecalhoSaldos

    def retornaCabecalhoBens(self):     
        if not self.cabecalhoBens:
            self.cabecalhoBens = self.trataCabecalho(self.Bens)
            return self.cabecalhoBens
        else:        
            return self.cabecalhoBens              
    
    def trataCabecalho(self,cabecalho):
        cabecalhoTratado = cabecalho
        cabecalhoTratado = cabecalhoTratado.replace(" ","").strip('\r\n').upper()
        cabecalhoTratado = cabecalhoTratado.split(";")
        return cabecalhoTratado
    
    def contemCabecalho(self,cabecalhoModelo,cabecalhoArquivo):
        # Verificar se o cabecalhoModelo está contido em cabecalhoArquivo.
        todosContidos = all(item in cabecalhoArquivo for item in cabecalhoModelo)
        if todosContidos:
            return True
        else:
            return False