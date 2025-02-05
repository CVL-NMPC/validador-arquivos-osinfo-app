import requests
import pandas as pd
import unicodedata
import streamlit as st
import re
from datetime import datetime
from difflib import SequenceMatcher
from classes.Despesa import Despesa, DespesaError

# Listas utilizadas no script
listaModulos = ['despesa', 'contratodeterceiro', 'receita', 'bempatrimoniado','saldo','itensdenotasficais']

listaAcoes = ['alteracao', 'exclusao', 'inclusao']

listaAtributosDespesa = ['valorpago', 'valor', 'valordocumento', 'rubrica', 'descricao', 'contacorrente', 'unidade', 'despesa', 'imagem', 'linha', 'codbancario', 'numerododocumento', 'cnpj', 'razao', 'datadeemissao', 'tipodedocumento', 'cpf', 'nome', 'datadevencimento', 'datadepagamento', 'datadeapuracao']

listaAtributosContratosTerceiros = ['imagemcontrato', 'nomedoarquivo', 'descricao', 'valormes', 'codunidade', 'contratoanomesfim', 'contratoanomesinicio', 'linha', 'vigencia']

listaAtributosReceitas = ['contratodegestaopartefixa', 'reccontgesfixa', 'repassecontratodegestaopartevariavel1', 'reccontgesvariavel', 'repassecontratodegestaopartevariavel2', 'reccontgesvariavel2','repassecontratodegestaopartevariavel3', 'reccontgesvariavel3','termoaditivoadicional(custeio)', 'rectaadiccusteio', 'termoaditivoadicional(investimento)', 'rectaadicinvest', 'resultadodeaplicacaofinanceira', 'recaplicfinanceira','estornodedespesas', 'recreembdespesas','obtencaoderecursosexternos', 'recrecursosexternos','retornodeemprestimorealizadoaoutrocontrato', 'recrecextras','emprestimotomadodeoutrocontrato', 'recoutrasreceitas','transferenciasentrecontasdeprovisionamentoeexecucao', 'recrepsusaih','transferenciadeprovisionamentodecolaboradoresoriundosdeoutrocontratoe/ouunidade','recrepsusamb']

listaAtributosBensPatrimoniados = ['codos','codunidade','codcontrato','anomesref','numcontroleos','numcontrolegov','descricaonf','quantidade','nf','cnpj','fornecedor','dataaquisicao','vidautil','valor','vinculacao','setordestino','codtipo','imgnf']

listaAtributosSaldos = ['valoremcontacorrente','vlcontacorrente','aplicacaofinanceira','vlaplfinanceira','provisao','vlcontaprovisao','valoremespecie','vlemespecie','imagemdoextrato','extrato']

listaAtributosItensNF = ['numerodanotafiscal', 'numdocumento', 'nf','codigodomaterial', 'codmatserv','descricao', 'descmatserv', 'unidadedemedida', 'unidmed', 'quantidade', 'qtd', 'valorunitario', 'precunit', 'valortotal', 'vlrtotitem','mesdereferencia', 'mesano', 'anodereferencia', 'mesano', 'fornecedor', 'cnpjforn', 'observacao']

# Mapa nomenclaturas das receitas
nomesReceitas = {
    'budgetMngtFixedValue' : 'Parte Fixa',
    'budgetMngtVariable1Value' : 'Parte Variável 1',
    'budgetMngtVariable2Value' : 'Parte Variável 2',
    'budgetMngtVariable3Value' : 'Parte Variável 3',
    'budgetAddCustTAValue' : 'Adicional Custeio',
    'budgetAddInvesTAValue' : 'Adicional Investimento',
    'investmentsValue' : 'Aplicação Financeira',
    'expensesReverseValue' : 'Estorno de Despesas',
    'externalResourcesValue' : 'Recursos Externos',
    'loanReverseValue': 'Retorno de Empréstimo',
    'loanAnotherContractValue' : 'Empréstimo Tomado',
    'transferAccountContractExecValue' : 'Transferência entre Contas',
    'transferResourceAnotherContractValue' : 'Transferência de Provisionamento'
}

#+++++++++++++++++++++++++++++FERRAMENTAS+++++++++++++++++++++++++++++

def abrirArquivo(caminhoArquivo: str):
    """
    Abre um arquivo CSV ou XLSX e carrega em um DataFrame.
    
    Args:
        caminhoArquivo (str): Caminho do arquivo CSV a ser carregado.
    
    Returns:
        pd.DataFrame: DataFrame contendo os dados do arquivo CSV.
    """
    df = None

    if caminhoArquivo.endswith('.xlsx'):
        df = pd.read_excel(caminhoArquivo)
    elif caminhoArquivo.endswith('.csv'):
        df = pd.read_csv(caminhoArquivo, sep=None, encoding="latin1", engine='python') 
    
    return df

def calcular_similaridade(novaPalavra, tipo):
    """
    Calcula a similaridade entre a nova palavra e uma lista de palavras pré-definidas.
    
    Args:
        novaPalavra (str): Palavra a ser comparada.
        tipo (int): Tipo de lista (1 para módulos, 2 para atributos).
    
    Returns:
        str: Palavra mais similar da lista ou a própria novaPalavra se a similaridade for zero.
    """

    tipos = {
        1 : listaAcoes,
        2 : listaModulos,
        3 : listaAtributosDespesa,
        4 : listaAtributosContratosTerceiros,
        5 : listaAtributosReceitas,
        6 : listaAtributosBensPatrimoniados,
        7 : listaAtributosSaldos,
        8 : listaAtributosItensNF
    }

    lista = tipos[tipo]

    distancias = {}

    for palavra in lista:        
        distancias[palavra] = SequenceMatcher(None, novaPalavra, palavra).ratio()       

    maxi =  max(distancias, key=distancias.get)

    return maxi if distancias[maxi] != 0.0 else novaPalavra

def remover_acentos(texto : str):
    """
        Remove acentos de um texto.
        
        Args:
            texto (str): Texto a ser normalizado.
        
        Returns:
            str: Texto sem acentos.
    """
    try:
        nfkd_form = unicodedata.normalize('NFKD', texto)
        only_ascii = nfkd_form.encode('ASCII', 'ignore')
        return only_ascii.decode('ascii')

    except:
        return texto

def stringToFloat(valor : str):
    """
        Esta função converte uma string que representa um número com pontos decimais em uma string formatada corretamente.
        
        Parâmetros:
        valor (str): A string que representa o número a ser convertido.
        
        Retorna:
        str: A string formatada corretamente.
    """
    valorFatiado = valor.split('.')

    if len(valorFatiado) > 1:
        toString = ''.join(valorFatiado[:-1]) + '.' + valorFatiado[-1]

    else:
        toString = valorFatiado[0]
    
    floatValue = float(toString)
    floatValue = round(floatValue, 2)

    return floatValue

def obterInformacaoData(data):
    """
        Esta função extrai informações específicas de uma data fornecida em formato de string.
        
        Parâmetros:
        data (str): A data em formato de string no formato '%Y-%m-%d %H:%M:%S'.
        info (int): O tipo de informação a ser extraída. Pode ser:
                    1 - Dia
                    2 - Mês
                    3 - Ano
        
        Retorna:
        str: A informação extraída da data, sem zeros à esquerda.
    """
    info = {}
    dataPython = None
    data = data.strip()

    try:
        dataPython = datetime.strptime(data, '%Y-%m-%d %H:%M:%S')
    except:
        try:
            dataPython = datetime.strptime(data, '%Y-%m-%d')
        except:
            dataPython = datetime.strptime(data, '%Y-%m')

    infos = {
        1 : dataPython.day,
        2 : dataPython.month,
        3 : dataPython.year
    }    

    return {'dia':str(infos[1]).lstrip("0"), 'mes': str(infos[2]).lstrip("0"), 'ano': str(infos[3]).lstrip("0")}

#+++++++++++++++++++++++++++++TRATAMENTO+++++++++++++++++++++++++++++

def padronizarTexto(df): 
    """
    Padroniza o texto em um DataFrame, removendo acentos, espaços extras e convertendo para minúsculas.

    Args:
        df (pd.DataFrame): DataFrame contendo os dados a serem padronizados.

    Returns:
        pd.DataFrame: DataFrame padronizado.
    """

    df.columns = ['TIPO_MODULO', 'ANO_MES_REF', 'ACAO', 'ID', 'ATRIBUTO', 'NOVO_VALOR']

    df['TIPO_MODULO'] = df['TIPO_MODULO'].str.lower()
    df['ATRIBUTO'] = df['ATRIBUTO'].str.lower()
    df['ACAO'] = df['ACAO'].str.lower()    

    df['ACAO'] = df['ACAO'].map( lambda x : calcular_similaridade(x, 1) )
    df['TIPO_MODULO'] = df['TIPO_MODULO'].map( lambda x : calcular_similaridade(x, 2) )

    df['ATRIBUTO'] = df['ATRIBUTO'].map( lambda x : x.replace('_','').strip().lower() )

    df = df.map( remover_acentos )

    return df

def limparDados(df):
    """
    Limpa o DataFrame removendo linhas e colunas completamente vazias.

    Args:
        df (pd.DataFrame): DataFrame a ser limpo.

    Returns:
        pd.DataFrame: DataFrame sem linhas e colunas completamente vazias.
    """
    df = df.replace('nan', None)

    df = df.dropna(how='all')
    df = df.dropna(axis=1, how='all')
    
    return df

def padronizarAtributos(df):
    """
    Padroniza os atributos no DataFrame, ajustando nomes e calculando similaridades.
    
    Args:
        df (pd.DataFrame): DataFrame contendo os dados a serem padronizados.
    
    Returns:
        pd.DataFrame: DataFrame com atributos padronizados.
    """    

    df.loc[ df['TIPO_MODULO'] == 'despesa', 'ATRIBUTO'] = df.loc[df['TIPO_MODULO'] == 'despesa']['ATRIBUTO'].map( lambda x : calcular_similaridade(x, 3)  )
    df.loc[ df['TIPO_MODULO'] == 'contratodeterceiro', 'ATRIBUTO'] = df.loc[df['TIPO_MODULO'] == 'contratodeterceiro']['ATRIBUTO'].map( lambda x : calcular_similaridade(x, 4)  )
    df.loc[ df['TIPO_MODULO'] == 'receita', 'ATRIBUTO'] = df.loc[df['TIPO_MODULO'] == 'receita']['ATRIBUTO'].map( lambda x : calcular_similaridade(x, 5)  )
    df.loc[ df['TIPO_MODULO'] == 'bempatrimoniado', 'ATRIBUTO'] = df.loc[df['TIPO_MODULO'] == 'bempatrimoniado']['ATRIBUTO'].map( lambda x : calcular_similaridade(x, 6)  )
    df.loc[ df['TIPO_MODULO'] == 'saldo', 'ATRIBUTO'] = df.loc[df['TIPO_MODULO'] == 'saldo']['ATRIBUTO'].map( lambda x : calcular_similaridade(x, 7)  )
    df.loc[ df['TIPO_MODULO'] == 'itensdenotasficais', 'ATRIBUTO'] = df.loc[df['TIPO_MODULO'] == 'itensdenotasficais']['ATRIBUTO'].map( lambda x : calcular_similaridade(x, 8)  )

    #Despesas
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'rubrica'), 'ATRIBUTO' ] = 'descricaoRubrica'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'despesa'), 'ATRIBUTO' ] = 'descricaoDespesa'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'unidade'), 'ATRIBUTO' ] = 'cod_unidade'    
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'valorpago'), 'ATRIBUTO' ] = 'valor_pago'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'valordocumento'), 'ATRIBUTO' ] = 'valor_documento'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'valor'), 'ATRIBUTO' ] = 'valor_pago'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'descricao'), 'ATRIBUTO' ] = 'descricao'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'imagem'), 'ATRIBUTO' ] = 'descricao'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'codbancario'), 'ATRIBUTO' ] = 'cod_bancario'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'contacorrente'), 'ATRIBUTO' ] = 'descricaoContaCorrente'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'numerododocumento'), 'ATRIBUTO' ] = 'num_documento'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'razao'), 'ATRIBUTO' ] = 'razao'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'cnpj'), 'ATRIBUTO' ] = 'cnpj'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'cpf'), 'ATRIBUTO' ] = 'cpf'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'nome'), 'ATRIBUTO' ] = 'nome'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'datadeemissao'), 'ATRIBUTO' ] = 'data_emissao'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'tipodedocumento'), 'ATRIBUTO' ] = 'descricaoTipoDocumento'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'datadevencimento'), 'ATRIBUTO' ] = 'data_vencimento'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'datadepagamento'), 'ATRIBUTO' ] = 'data_pagamento'
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'datadeapuracao'), 'ATRIBUTO' ] = 'data_apuracao'

    #Contratos de Terceiros
    df.loc[ (df['TIPO_MODULO'] == 'contratodeterceiro') & (df['ATRIBUTO'] == 'imagemcontrato'), 'ATRIBUTO' ] = 'imagem_contrato'
    df.loc[ (df['TIPO_MODULO'] == 'contratodeterceiro') & (df['ATRIBUTO'] == 'nomedoarquivo'), 'ATRIBUTO' ] = 'imagem_contrato'
    df.loc[ (df['TIPO_MODULO'] == 'contratodeterceiro') & (df['ATRIBUTO'] == 'descricao'), 'ATRIBUTO' ] = 'imagem_contrato'
    df.loc[ (df['TIPO_MODULO'] == 'contratodeterceiro') & (df['ATRIBUTO'] == 'valormes'), 'ATRIBUTO' ] = 'valor_mes'
    df.loc[ (df['TIPO_MODULO'] == 'contratodeterceiro') & (df['ATRIBUTO'] == 'codunidade'), 'ATRIBUTO' ] = 'cod_unidade'
    df.loc[ (df['TIPO_MODULO'] == 'contratodeterceiro') & (df['ATRIBUTO'] == 'contratoanomesfim'), 'ATRIBUTO' ] = 'contrato_ano_mes_fim'
    df.loc[ (df['TIPO_MODULO'] == 'contratodeterceiro') & (df['ATRIBUTO'] == 'contratoanomesinicio'), 'ATRIBUTO' ] = 'contrato_ano_mes_inicio'
    df.loc[ (df['TIPO_MODULO'] == 'contratodeterceiro') & (df['ATRIBUTO'] == 'vigencia'), 'ATRIBUTO' ] = 'vigencia'

    #Receitas
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'contratodegestaopartefixa') | (df['ATRIBUTO'] == 'reccontgesfixa')), 'ATRIBUTO' ] = 'budgetMngtFixedValue'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'repassecontratodegestaopartevariavel1') | (df['ATRIBUTO'] == 'reccontgesvariavel') ), 'ATRIBUTO' ] = 'budgetMngtVariable1Value'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'repassecontratodegestaopartevariavel2') | (df['ATRIBUTO'] == 'reccontgesvariavel2')), 'ATRIBUTO' ] = 'budgetMngtVariable2Value'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'repassecontratodegestaopartevariavel3') | (df['ATRIBUTO'] == 'reccontgesvariavel3')), 'ATRIBUTO' ] = 'budgetMngtVariable3Value'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'termoaditivoadicional(custeio)') | (df['ATRIBUTO'] == 'rectaadiccusteio')), 'ATRIBUTO' ] = 'budgetAddCustTAValue'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'termoaditivoadicional(investimento)') | (df['ATRIBUTO'] == 'rectaadiccusteio') ), 'ATRIBUTO' ] = 'budgetAddInvesTAValue'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'resultadodeaplicacaofinanceira') | (df['ATRIBUTO'] == 'recaplicfinanceira')), 'ATRIBUTO' ] = 'investmentsValue'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'estornodedespesas') | (df['ATRIBUTO'] == 'recreembdespesas') ), 'ATRIBUTO' ] = 'expensesReverseValue'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'obtencaoderecursosexternos') | (df['ATRIBUTO'] == 'recrecursosexternos') ), 'ATRIBUTO' ] = 'externalResourcesValue'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'retornodeemprestimorealizadoaoutrocontrato') | (df['ATRIBUTO'] == 'recrecextras') ), 'ATRIBUTO' ] = 'loanReverseValue'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'emprestimotomadodeoutrocontrato') | (df['ATRIBUTO'] == 'recoutrasreceitas')), 'ATRIBUTO' ] = 'loanAnotherContractValue'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'transferenciasentrecontasdeprovisionamentoeexecucao') | (df['ATRIBUTO'] == 'recrepsusaih') ), 'ATRIBUTO' ] = 'transferAccountContractExecValue'
    df.loc[ (df['TIPO_MODULO'] == 'receita') & ( (df['ATRIBUTO'] == 'transferenciadeprovisionamentodecolaboradoresoriundosdeoutrocontratoe/ouunidade') | (df['ATRIBUTO'] == 'recrepsusamb') ), 'ATRIBUTO' ] = 'transferResourceAnotherContractValue'

    #Bens Patrimoniados
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'codos'), 'ATRIBUTO' ] = 'cod_os'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'codunidade'), 'ATRIBUTO' ] = 'cod_unidade'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'codcontrato'), 'ATRIBUTO' ] = 'id_contrato'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'anomesref'), 'ATRIBUTO' ] = 'ref_ano_mes'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'numcontroleos'), 'ATRIBUTO' ] = 'num_controle'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'numcontrolegov'), 'ATRIBUTO' ] = ''
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'descricaonf'), 'ATRIBUTO' ] = 'img_nf'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'quantidade'), 'ATRIBUTO' ] = 'quantidade'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'nf'), 'ATRIBUTO' ] = 'nf'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'cnpj'), 'ATRIBUTO' ] = 'cnpj'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'fornecedor'), 'ATRIBUTO' ] = 'fornecedor'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'dataaquisicao'), 'ATRIBUTO' ] = 'data_aquisicao'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'vidautil'), 'ATRIBUTO' ] = 'vida_util'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'valor'), 'ATRIBUTO' ] = 'valor'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'vinculacao'), 'ATRIBUTO' ] = 'vinculacao'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'setordestino'), 'ATRIBUTO' ] = 'setor_destino'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'codtipo'), 'ATRIBUTO' ] = 'id_bem_tipo'
    df.loc[ (df['TIPO_MODULO'] == 'bempatrimoniado') & (df['ATRIBUTO'] == 'imgnf'), 'ATRIBUTO' ] = 'img_nf'

    #Saldos
    df.loc[ (df['TIPO_MODULO'] == 'saldo') & ( (df['ATRIBUTO'] == 'valoremcontacorrente') | (df['ATRIBUTO'] == 'vlcontacorrente')), 'ATRIBUTO' ] = 'bankAccountValue'
    df.loc[ (df['TIPO_MODULO'] == 'saldo') & ( (df['ATRIBUTO'] == 'aplicacaofinanceira') | (df['ATRIBUTO'] == 'vlaplfinanceira')), 'ATRIBUTO' ] = 'investmentValue'
    df.loc[ (df['TIPO_MODULO'] == 'saldo') & ( (df['ATRIBUTO'] == 'provisao') | (df['ATRIBUTO'] == 'vlcontaprovisao')), 'ATRIBUTO' ] = 'provisioningValue'
    df.loc[ (df['TIPO_MODULO'] == 'saldo') & ( (df['ATRIBUTO'] == 'valoremespecie') | (df['ATRIBUTO'] == 'vlemespecie')), 'ATRIBUTO' ] = 'valor'
    df.loc[ (df['TIPO_MODULO'] == 'saldo') & ( df['ATRIBUTO'] == 'imagemdoextrato' ), 'ATRIBUTO' ] = 'nome_arq_img_ext'
    df.loc[ (df['TIPO_MODULO'] == 'saldo') & ( df['ATRIBUTO'] == 'extrato' ), 'ATRIBUTO' ] = 'nome_arq_img_ext'

    #Itens de Notas Fiscais
    df.loc[ (df['TIPO_MODULO'] == 'itensdenotasficais') & ( (df['ATRIBUTO'] == 'numerodanotafiscal') | (df['ATRIBUTO'] == 'numdocumento') | (df['ATRIBUTO'] == 'nf')), 'ATRIBUTO' ] = 'itnf_num_documento'
    df.loc[ (df['TIPO_MODULO'] == 'itensdenotasficais') & ( (df['ATRIBUTO'] == 'codigodoservico') | (df['ATRIBUTO'] == 'codmatserv')), 'ATRIBUTO' ] = 'valor'
    df.loc[ (df['TIPO_MODULO'] == 'itensdenotasficais') & ( (df['ATRIBUTO'] == 'descricao') | (df['ATRIBUTO'] == 'descmatserv')), 'ATRIBUTO' ] = 'itnf_descricao_item'
    df.loc[ (df['TIPO_MODULO'] == 'itensdenotasficais') & ( (df['ATRIBUTO'] == 'unidadedemedida') | (df['ATRIBUTO'] == 'unidmed')), 'ATRIBUTO' ] = 'itnf_unidade_medida'
    df.loc[ (df['TIPO_MODULO'] == 'itensdenotasficais') & ( (df['ATRIBUTO'] == 'quantidade') | (df['ATRIBUTO'] == 'qtd')), 'ATRIBUTO' ] = 'itnf_quantidade'
    df.loc[ (df['TIPO_MODULO'] == 'itensdenotasficais') & ( (df['ATRIBUTO'] == 'valorunitario') | (df['ATRIBUTO'] == 'precunit')), 'ATRIBUTO' ] = 'itnf_valor_unitario'
    df.loc[ (df['TIPO_MODULO'] == 'itensdenotasficais') & ( (df['ATRIBUTO'] == 'valortotal') | (df['ATRIBUTO'] == 'vlrtotitem')), 'ATRIBUTO' ] = 'itnf_valor_total'
    df.loc[ (df['TIPO_MODULO'] == 'itensdenotasficais') & ( (df['ATRIBUTO'] == 'mesdereferencia') | (df['ATRIBUTO'] == 'mesano') | (df['ATRIBUTO'] == 'anodereferencia')), 'ATRIBUTO' ] = 'mes_ano'
    df.loc[ (df['TIPO_MODULO'] == 'itensdenotasficais') & ( (df['ATRIBUTO'] == 'fornecedor') | (df['ATRIBUTO'] == 'cnpjforn')), 'ATRIBUTO' ] = 'descricaoFornecedor'
    df.loc[ (df['TIPO_MODULO'] == 'itensdenotasficais') & ( (df['ATRIBUTO'] == 'observacao') | (df['ATRIBUTO'] == 'observacao')), 'ATRIBUTO' ] = 'itnf_observacao'

def padronizarValores(df):
    """
    Padroniza os valores na coluna 'NOVO_VALOR' do DataFrame com base no atributo.

    Args:
        df (pd.DataFrame): DataFrame contendo os dados a serem padronizados.

    Returns:
        pd.DataFrame: DataFrame com valores padronizados na coluna 'NOVO_VALOR'.
    """
    ########## Aplicação Geral ##########

    #Ids no formato de inteiro
    df['ID'] = df['ID'].str.replace(".0","").str.replace("-","")

    #Caso seja unidade, pegar o ID 
    df.loc[ df['ATRIBUTO'] == 'cod_unidade','NOVO_VALOR'] = [ x.split(' ')[0] for x in df[df['ATRIBUTO'] == 'cod_unidade']['NOVO_VALOR'] ]

    #Se for valor, formatar para passar para float
    df.loc[ df['ATRIBUTO'].str.contains("valor") , 'NOVO_VALOR'] = [ stringToFloat(x.replace(',','.')) for x in df[df['ATRIBUTO'].str.contains("valor")]['NOVO_VALOR'] ]

    #Se for imagem, formatar sem .pdf
    df.loc[ (df['ATRIBUTO'] == 'descricao') | (df['ATRIBUTO'] == 'imagem_contrato') | (df['ATRIBUTO'] == 'img_nf') | (df['ATRIBUTO'] == 'nome_arq_img_ext') ,'NOVO_VALOR'] = [ x.strip().replace('.pdf','') for x in df[(df['ATRIBUTO'] == 'descricao') | (df['ATRIBUTO'] == 'imagem_contrato') | (df['ATRIBUTO'] == 'img_nf') | (df['ATRIBUTO'] == 'nome_arq_img_ext') ]['NOVO_VALOR'] ]      

    ########## Apenas para Despesas ##########

    # Datas
    df.loc[df['ATRIBUTO'] == 'data_emissao', 'NOVO_VALOR'] = [
        obterInformacaoData(x)['ano'] + '-' + 
        obterInformacaoData(x)['mes'].zfill(2) + '-' + 
        obterInformacaoData(x)['dia'].zfill(2) 
        for x in df[df['ATRIBUTO'] == 'data_emissao']['NOVO_VALOR']
    ]

    df.loc[df['ATRIBUTO'] == 'data_vencimento', 'NOVO_VALOR'] = [
        obterInformacaoData(x)['ano'] + '-' + 
        obterInformacaoData(x)['mes'].zfill(2) + '-' + 
        obterInformacaoData(x)['dia'].zfill(2) 
        for x in df[df['ATRIBUTO'] == 'data_vencimento']['NOVO_VALOR']
    ]

    df.loc[df['ATRIBUTO'] == 'data_pagamento', 'NOVO_VALOR'] = [
        obterInformacaoData(x)['ano'] + '-' + 
        obterInformacaoData(x)['mes'].zfill(2) + '-' + 
        obterInformacaoData(x)['dia'].zfill(2) 
        for x in df[df['ATRIBUTO'] == 'data_pagamento']['NOVO_VALOR']
    ]

    df.loc[df['ATRIBUTO'] == 'data_apuracao', 'NOVO_VALOR'] = [
        obterInformacaoData(x)['ano'] + '-' + 
        obterInformacaoData(x)['mes'].zfill(2) + '-' + 
        obterInformacaoData(x)['dia'].zfill(2) 
        for x in df[df['ATRIBUTO'] == 'data_apuracao']['NOVO_VALOR']
    ]

    #Remocao do '-' na cona corrente
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'descricaoContaCorrente'), 'NOVO_VALOR' ] = [ x.replace('-','') for x in df[ (df['TIPO_MODULO'] == 'despesa') & (df['ATRIBUTO'] == 'descricaoContaCorrente') ]['NOVO_VALOR'] ]

    #Obter apenas o codigo do plano de contas ou da rubrica
    df.loc[ (df['TIPO_MODULO'] == 'despesa') & ( (df['ATRIBUTO'] == 'descricaoDespesa') | (df['ATRIBUTO'] == 'descricaoRubrica') ), 'NOVO_VALOR' ] = [ x.split(' ')[0] for x in df[(df['TIPO_MODULO'] == 'despesa') & ( (df['ATRIBUTO'] == 'descricaoDespesa') | (df['ATRIBUTO'] == 'descricaoRubrica') )]['NOVO_VALOR'] ]

    #Se for identificador bancario, remover os pontos
    df.loc[ (df['TIPO_MODULO'] == 'despesa') &  (df['ATRIBUTO'] == 'cod_bancario'), 'NOVO_VALOR' ] = [ x.replace('.','') for x in df[ (df['TIPO_MODULO'] == 'despesa') &  (df['ATRIBUTO'] == 'cod_bancario') ]['NOVO_VALOR'] ]

    #Data de pagamento sem as horas:minutos:segundos
    df.loc[ (df['TIPO_MODULO'] == 'despesa') &  (df['ATRIBUTO'] == 'formattedPayDate'), 'NOVO_VALOR' ] = [ x.split(" ")[0] for x in df[ (df['TIPO_MODULO'] == 'despesa') &  (df['ATRIBUTO'] == 'formattedPayDate') ]['NOVO_VALOR'] ]

    ########## Apenas para Despesas ##########

    #Formatacao dos valores, para passar para float
    df.loc[ df['TIPO_MODULO'] == 'receita', 'NOVO_VALOR' ] = [ stringToFloat(x.replace(',','.')) for x in df[ df['TIPO_MODULO'] == 'receita' ]['NOVO_VALOR'] ]

    ########## Apenas para Despesas ##########

    #Apenas para Saldos - Valores
    df.loc[ (df['TIPO_MODULO'] == 'saldo') & (df['ATRIBUTO'].str.contains('Value|valor', regex=True))  , 'NOVO_VALOR' ] = [ stringToFloat(x.replace(',','.')) for x in df[ (df['TIPO_MODULO'] == 'saldo') & (df['ATRIBUTO'].str.contains('Value|valor', regex=True)) ]['NOVO_VALOR'] ]

#+++++++++++++++++++++++++++++VERIFICACAO+++++++++++++++++++++++++++++

def verificarDespesas(df):
    """
        Esta função verifica as despesas em um DataFrame e compara os valores com os dados obtidos de um serviço externo.
        
        Parâmetros:
        df (DataFrame): O DataFrame contendo as despesas a serem verificadas.
        
        Retorna:
        list: Uma lista de dicionários contendo os resultados da verificação.
    """
    results = []

    df_alteracao_despesas = df[df['ACAO'] == 'alteracao']
    df_exclusao_despesas = df[df['ACAO'] == 'exclusao']

    alteracoes_despesas = df_alteracao_despesas.to_dict('records')
    exclusoes_despesas = df_exclusao_despesas.to_dict('records')
    qtd = len(alteracoes_despesas)
    for linha in alteracoes_despesas:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = int(linha['ID'])
        valor = linha['NOVO_VALOR']

        try:
            despesa = Despesa()
            despesa.osinfo_load_from_id(id)
            data = despesa.dados | despesa.dados_aux

            data['descricaoRubrica'] = data['descricaoRubrica'].split(' ')[0]
            data['descricaoDespesa'] = data['descricaoDespesa'].split(' ')[0]
            data['descricaoContaCorrente'] = data['descricaoContaCorrente'].replace('-','')
            
            #para poder comparar o valor da descricao que está no painel com a descricao que está sendo enviada, ignoramos uma ocorrencia de .pdf no final
            valorOriginalStr = re.sub(r"(?i)\.pdf$", "", str(data[atributo]), count=1)
            valorDesbloqueioStr = re.sub(r"(?i)\.pdf$", "", str(valor), count=1)

            obj = {
                'modulo': modulo,
                'acao': acao,
                'id': id,
                'atributo': atributo,
                'competencia': competencia,
                'desbloqueio': valor,
                'painel': str(data[atributo]),
                'atendido': ('SIM' if valorDesbloqueioStr == valorOriginalStr else 'NAO') if not 'valor' in atributo else 'SIM' if float(valor) == float(data[atributo]) else 'NAO'
            }
            
        except Exception as e:
            obj = {
                'modulo': modulo,
                'acao': acao,
                'id': id,
                'atributo': atributo,
                'competencia': competencia,
                'desbloqueio': valor,
                'painel': f"Erro (verificarDespesas): {e}",
                'atendido': '?'
            }

        results.append(obj)

    for linha in exclusoes_despesas:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = int(linha['ID'])
        valor = linha['NOVO_VALOR']           

        #response = requests.post('https://osinfo.prefeitura.rio/expenses/server/expensesService/getExpenseFromId',json=id)
        url = st.secrets['base_url'] + '/expenses/server/expensesService/getExpenseFromId'
        response = requests.post(url, json=id)
        data = response.json()
        
        obj = {
            'modulo': modulo,
            'acao': acao,
            'id': id,
            'atributo': atributo,
            'competencia': competencia,
            'desbloqueio': '',
            'painel': '',
            'atendido': 'SIM' if str(data['id_documento']) == '0' else 'NAO'
        }           

        results.append(obj)

    return results

def verificarReceitas(df):
    """
        Esta função verifica as receitas em um DataFrame e compara os valores com os dados obtidos de um serviço externo.
        
        Parâmetros:
        df (DataFrame): O DataFrame contendo as despesas a serem verificadas.
        
        Retorna:
        list: Uma lista de dicionários contendo os resultados da verificação.
    """
    results = []

    df_alteracao_receitas = df[df['ACAO'] == 'alteracao']
    df_exclusao_receitas = df[df['ACAO'] == 'exclusao']

    alteracoes_receitas = df_alteracao_receitas.to_dict('records')
    exclusoes_receitas = df_exclusao_receitas.to_dict('records')

    df_painel = pd.DataFrame()

    for linha in alteracoes_receitas:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = int(linha['ID'])
        valor = linha['NOVO_VALOR']     

        if df_painel.empty:
            #response = requests.post('https://osinfo.prefeitura.rio/income/server/incomeServices/getIncomeListFromReference', json={"cod_os":1,"ref_mes":competencia.split('-')[1],"ref_ano":competencia.split('-')[0],"propria_os":"N"})
            url = st.secrets['base_url'] + '/income/server/incomeServices/getIncomeListFromReference'
            response = requests.post(url, json={"cod_os":1,"ref_mes":competencia.split('-')[1],"ref_ano":competencia.split('-')[0],"propria_os":"N"})
            data = response.json()
            df_painel = pd.DataFrame(data=data)          

        try:           

            df_painel.loc[ :, 'descricaoContaCorrente'] = df_painel['descricaoContaCorrente'].str.replace("-","")

            linha_painel = df_painel[ df_painel['descricaoContaCorrente'] == str(id) ]

            valor_painel = linha_painel[atributo].values[0]

            valor_painel = stringToFloat(valor_painel.replace(',','.'))
            
            obj = {
                'modulo': modulo,
                'acao': acao,
                'id': id,
                'atributo': nomesReceitas[atributo],
                'competencia': competencia,
                'desbloqueio': valor,
                'painel': str(valor_painel),
                'atendido': 'SIM' if float(valor) == float(valor_painel) else 'NAO'
            }
            
        except:
            obj = {
                'modulo': modulo,
                'acao': acao,
                'id': id,
                'atributo': atributo,
                'competencia': competencia,
                'desbloqueio': valor,
                'painel': 'error no painel',
                'atendido': '?'
            } 

        results.append(obj)

    for linha in exclusoes_receitas:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = int(linha['ID'])
        valor = linha['NOVO_VALOR']           

        #response = requests.post('https://osinfo.prefeitura.rio/expenses/server/expensesService/getExpenseFromId',json=id)
        url = st.secrets['base_url'] + '/expenses/server/expensesService/getExpenseFromId'
        response = requests.post(url, json=id)
        data = response.json()        
        
        obj = {
            'modulo': modulo,
            'acao': acao,
            'id': id,
            'atributo': atributo,
            'competencia': competencia,
            'desbloqueio': '',
            'painel': '',
            'atendido': 'SIM' if str(data['id_receita_dados']) == '0' else 'NAO'
        }           

        results.append(obj)

    return results

def verificarContratosTerceiros(df):
    """
        Esta função verifica os contratos de terceiros em um DataFrame e compara os valores com os dados obtidos de um serviço externo.
        
        Parâmetros:
        df (DataFrame): O DataFrame contendo as despesas a serem verificadas.
        
        Retorna:
        list: Uma lista de dicionários contendo os resultados da verificação.
    """

    results = []

    df_alteracao_ctTerceiro = df[df['ACAO'] == 'alteracao']
    df_exclusao_ctTerceiro = df[df['ACAO'] == 'exclusao']

    alteracoes_ctTerceiro = df_alteracao_ctTerceiro.to_dict('records')
    exclusoes_ctTerceiro = df_exclusao_ctTerceiro.to_dict('records')

    for linha in alteracoes_ctTerceiro:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = int(linha['ID'])
        valor = linha['NOVO_VALOR']

        obj = None

        try:
            #response = requests.post('https://osinfo.prefeitura.rio/supplierContract/server/supplierContractService/getSupplierContractFromId', json=id)
            url = st.secrets['base_url'] + '/supplierContract/server/supplierContractService/getSupplierContractFromId'
            response = requests.post(url, json=id)
            data = response.json()
            data['imagem_contrato'] = data['imagem_contrato'].replace('.pdf','').replace('.PDF','').strip()

            if atributo == 'contrato_ano_mes_fim':
                dataInfos = obterInformacaoData(valor)
                dataDesbloqueio = dataInfos['ano'] + '-' + dataInfos['mes']    
                dataPainel = str(data['contrato_ano_fim']) + '-' + str(data['contrato_mes_fim'])

                obj = {
                    'modulo': modulo,
                    'acao': acao,
                    'id': id,
                    'atributo': atributo,
                    'competencia': competencia,
                    'desbloqueio': dataDesbloqueio,
                    'painel': dataPainel,
                    'atendido': 'SIM' if dataPainel == dataDesbloqueio else 'NAO'
                }

            elif atributo == 'contrato_ano_mes_inicio':
                dataInfos = obterInformacaoData(valor)
                dataDesbloqueio = dataInfos['ano'] + '-' + dataInfos['mes']    
                dataPainel = str(data['contrato_ano_inicio']) + '-' + str(data['contrato_mes_inicio'])  

                obj = {
                    'modulo': modulo,
                    'acao': acao,
                    'id': id,
                    'atributo': atributo,
                    'competencia': competencia,
                    'competencia': competencia,
                    'desbloqueio': dataDesbloqueio,
                    'atendido': 'SIM' if dataPainel == dataDesbloqueio else 'NAO'
                }

            else:
                obj = {
                    'modulo': modulo,
                    'acao': acao,
                    'id': id,
                    'atributo': atributo,
                    'competencia': competencia,
                    'desbloqueio': valor,
                    'painel': str(data[atributo]),
                    'atendido': ('SIM' if str(valor) == str(data[atributo]) else 'NAO') if not 'valor' in atributo else 'SIM' if float(valor) == float(data[atributo]) else 'NAO'
                }

        except:
            obj = {
                'modulo': modulo,
                'acao': acao,
                'id': id,
                'atributo': atributo,
                'competencia': competencia,
                'desbloqueio': valor,
                'painel': 'error no painel',
                'atendido': '?'
            } 
        
        results.append(obj)

    for linha in exclusoes_ctTerceiro:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = int(linha['ID'])
        valor = linha['NOVO_VALOR']           

        #response = requests.post('https://osinfo.prefeitura.rio/supplierContract/server/supplierContractService/getSupplierContractFromId',json=id)
        url = st.secrets['base_url'] + '/supplierContract/server/supplierContractService/getSupplierContractFromId'
        response = requests.post(url, json=id)
        data = response.json()
        
        obj = {
            'modulo': modulo,
            'acao': acao,
            'id': id,
            'atributo': atributo,
            'competencia': competencia,
            'desbloqueio': '',
            'painel': '',
            'atendido': 'SIM' if str(data['id_serv_ter']) == '0' else 'NAO'
        }    

    return results
        
def verificarBensPatrimoniados(df):
    """
        Esta função verifica os bens patrimoniados em um DataFrame e compara os valores com os dados obtidos de um serviço externo.
        
        Parâmetros:
        df (DataFrame): O DataFrame contendo as despesas a serem verificadas.
        
        Retorna:
        list: Uma lista de dicionários contendo os resultados da verificação.
    """

    results = []

    df_alteracao_bens = df[df['ACAO'] == 'alteracao']
    df_exclusao_bens = df[df['ACAO'] == 'exclusao']

    alteracoes_bens = df_alteracao_bens.to_dict('records')
    exclusoes_bens = df_exclusao_bens.to_dict('records')

    for linha in alteracoes_bens:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = int(linha['ID'])
        valor = linha['NOVO_VALOR']               

        try:
            #response = requests.post('https://osinfo.prefeitura.rio/asset/server/assetService/getAssetFromId',json=id)
            url = st.secrets['base_url'] + '/asset/server/assetService/getAssetFromId'
            response = requests.post(url, json=id)
            data = response.json()

            data['img_nf'] = data['img_nf'].strip().replace('.pdf','').replace('.PDF','')
            data['decricaoUnidade'] = data['decricaoUnidade'].split(' ')[0]
            data['setor_destino'] = remover_acentos(data['setor_destino'].strip().upper())
            
            obj = {
                'modulo': modulo,
                'acao': acao,
                'id': id,
                'atributo': atributo,
                'competencia': competencia,
                'desbloqueio': valor,
                'painel': str(data[atributo]),
                'atendido': ('SIM' if str(valor) == str(data[atributo]) else 'NAO') if not 'valor' in atributo else 'SIM' if float(valor) == float(data[atributo]) else 'NAO'
            }
            
        except:
            obj = {
                'modulo': modulo,
                'acao': acao,
                'id': id,
                'atributo': atributo,
                'competencia': competencia,
                'desbloqueio': valor,
                'painel': 'error no painel',
                'atendido': '?'
            } 

        results.append(obj)

    for linha in exclusoes_bens:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = int(linha['ID'])
        valor = linha['NOVO_VALOR']         

        #response = requests.post('https://osinfo.prefeitura.rio/asset/server/assetService/getAssetFromId',json=id)
        url = st.secrets['base_url'] + '/asset/server/assetService/getAssetFromId'
        response = requests.post(url, json=id)
        data = response.json()
        
        obj = {
            'modulo': modulo,
            'acao': acao,
            'id': id,
            'atributo': atributo,
            'competencia': competencia,
            'desbloqueio': '',
            'painel': '',
            'atendido': 'SIM' if str(data['id_bem']) == '0' else 'NAO'
        }           

        results.append(obj)

    return results

def verificarSaldos(df):
    """
        Esta função verifica as saldos em um DataFrame e compara os valores com os dados obtidos de um serviço externo.
        
        Parâmetros:
        df (DataFrame): O DataFrame contendo as despesas a serem verificadas.
        
        Retorna:
        list: Uma lista de dicionários contendo os resultados da verificação.
    """
    results = []

    df_alteracao_saldos = df[df['ACAO'] == 'alteracao']
    df_exclusao_saldos = df[df['ACAO'] == 'exclusao']

    alteracoes_saldos = df_alteracao_saldos.to_dict('records')
    exclusoes_saldos = df_exclusao_saldos.to_dict('records')

    df_painel = pd.DataFrame()

    for linha in alteracoes_saldos:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = str(linha['ID']).lower()
        valor = linha['NOVO_VALOR']

        if df_painel.empty:
            #response = requests.post('https://osinfo.prefeitura.rio/balance/server/balanceServices/getBalanceListFromReference', json={"cod_os":1,"ref_mes":competencia.split('-')[1],"ref_ano":competencia.split('-')[0],"propria_os":"N"})
            url = st.secrets['base_url'] + '/balance/server/balanceServices/getBalanceListFromReference'
            response = requests.post(url, json={"cod_os":1,"ref_mes":competencia.split('-')[1],"ref_ano":competencia.split('-')[0],"propria_os":"N"})
            data = response.json()

            df_painel = pd.DataFrame(data=data)

            df_painel.loc[ :, 'descricaoContaCorrente'] = df_painel['descricaoContaCorrente'].str.replace("-","").str.lower()

        #try:     
        linha_painel = df_painel[ df_painel['descricaoContaCorrente'] == id ]

        valor_painel = linha_painel[atributo].values[0]        

        if atributo == 'nome_arq_img_ext':
            valor_painel = valor_painel.split('>')[1].split('<')[0].replace('.pdf','').replace('.PDF','').strip()

        else:
            valor_painel = stringToFloat(str(valor_painel).replace(',','.'))
        
        obj = {
            'modulo': modulo,
            'acao': acao,
            'id': id,
            'atributo': atributo,
            'competencia': competencia,
            'desbloqueio': valor,
            'painel': str(valor_painel),
            'atendido': ('SIM' if str(valor) == str(valor_painel) else 'NAO') if atributo == 'nome_arq_img_ext' else 'SIM' if float(valor) == float(valor_painel) else 'NAO'
        }
            
        # except:
        #     obj = {
        #         'modulo': modulo,
        #         'acao': acao,
        #         'id': id,
        #         'atributo': atributo,
        #         'competencia': competencia,
        #         'desbloqueio': valor,
        #         'painel': 'error no painel',
        #         'atendido': '?'
        #     } 

        results.append(obj)

    for linha in exclusoes_saldos:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = int(linha['ID'])
        valor = linha['NOVO_VALOR']           

        linha_painel = df_painel[ df_painel['descricaoContaCorrente'] == str(id) ]

        valor_painel = linha_painel[atributo].values[0]      
        
        obj = {
            'modulo': modulo,
            'acao': acao,
            'id': id,
            'atributo': atributo,
            'competencia': competencia,
            'desbloqueio': '',
            'painel': '',
            'atendido': 'SIM' if str(valor_painel) == '0' else 'NAO'
        }           

        results.append(obj)

    return results

def verificarItensDeNF(df):
    """
        Esta função verifica as saldos em um DataFrame e compara os valores com os dados obtidos de um serviço externo.
        
        Parâmetros:
        df (DataFrame): O DataFrame contendo as despesas a serem verificadas.
        
        Retorna:
        list: Uma lista de dicionários contendo os resultados da verificação.
    """
    results = []

    df_alteracao_itens = df[df['ACAO'] == 'alteracao']
    df_exclusao_itens = df[df['ACAO'] == 'exclusao']

    alteracoes_itens = df_alteracao_itens.to_dict('records')
    exclusoes_itens = df_exclusao_itens.to_dict('records')

    for linha in alteracoes_itens:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = str(linha['ID']).lower()
        valor = linha['NOVO_VALOR']

        #response = requests.post('https://osinfo.prefeitura.rio/invoiceItem/server/invoiceItemService/getInvoiceItemFromId', json=int(id))
        url = st.secrets['base_url'] + '/invoiceItem/server/invoiceItemService/getInvoiceItemFromId'
        response = requests.post(url, json=int(id))
        data = response.json()
        
        try:
            if atributo == 'mes_ano':
                dataInfos = obterInformacaoData(valor)
                dataDesbloqueio = dataInfos['ano'] + '-' + dataInfos['mes']    
                dataPainel = str(data['itnf_ref_ano']) + '-' + str(data['itnf_ref_mes'])

                obj = {
                    'modulo': modulo,
                    'acao': acao,
                    'id': id,
                    'atributo': atributo,
                    'competencia': competencia,
                    'desbloqueio': dataDesbloqueio,
                    'painel': dataPainel,
                    'atendido': 'SIM' if dataPainel == dataDesbloqueio else 'NAO'
                }
            
            elif atributo == 'descricaoFornecedor':
                obj = {
                    'modulo': modulo,
                    'acao': acao,
                    'id': id,
                    'atributo': atributo,
                    'competencia': competencia,
                    'desbloqueio': valor,
                    'painel': str(data[atributo]),
                    'atendido': ('SIM' if str(valor) in str(data[atributo]) else 'NAO') if 'valor' not in atributo else 'SIM' if float(valor) == float(data[atributo]) else 'NAO'
                }

            else:
                obj = {
                    'modulo': modulo,
                    'acao': acao,
                    'id': id,
                    'atributo': atributo,
                    'competencia': competencia,
                    'desbloqueio': valor,
                    'painel': str(data[atributo]),
                    'atendido': ('SIM' if str(valor) == str(data[atributo]) else 'NAO') if 'valor' not in atributo else 'SIM' if float(valor) == float(data[atributo]) else 'NAO'
                }
           
        except:
            obj = {
                'modulo': modulo,
                'acao': acao,
                'id': id,
                'atributo': atributo,
                'competencia': competencia,
                'desbloqueio': valor,
                'painel': 'error no painel',
                'atendido': '?'
            } 

        results.append(obj)

    for linha in exclusoes_itens:
        modulo = linha['TIPO_MODULO']
        acao = linha['ACAO']
        atributo = linha['ATRIBUTO']
        competencia = linha['ANO_MES_REF']
        id = int(linha['ID'])
        valor = linha['NOVO_VALOR']  

        #response = requests.post('https://osinfo.prefeitura.rio/invoiceItem/server/invoiceItemService/getInvoiceItemFromId', json=int(id))
        url = st.secrets['base_url'] + '/invoiceItem/server/invoiceItemService/getInvoiceItemFromId'
        response = requests.post(url, json=int(id))
        data = response.json()  
        
        obj = {
            'modulo': modulo,
            'acao': acao,
            'id': id,
            'atributo': atributo,
            'competencia': competencia,
            'desbloqueio': '',
            'painel': '',
            'atendido': 'SIM' if str(data['itnf_cd_item_nota_fiscal']) == '0' else 'NAO'
        }

        results.append(obj)

    return results


def validarAtendimento(df):
    """
    Valida os dados de atendimento, comparando os dados do arquivo com a API de despesas.
    
    Args:
        caminhoArquivo (str): Caminho do arquivo CSV contendo os dados de atendimento.
    
    Returns:
        list: Lista de dicionários contendo os resultados da validação.
    """

    df = df.astype('str')
    df = limparDados(df)    
    
    df = padronizarTexto(df)      
    
    padronizarAtributos(df)    

    padronizarValores(df)     

    df_despesa = df[df['TIPO_MODULO'] == 'despesa']
    df_receita = df[df['TIPO_MODULO'] == 'receita']
    df_contratoTerceiro = df[df['TIPO_MODULO'] == 'contratodeterceiro']
    df_bemPatrimoniado = df[ df['TIPO_MODULO'] == 'bempatrimoniado']
    df_saldo = df[ df['TIPO_MODULO'] == 'saldo']
    df_itens = df[ df['TIPO_MODULO'] == 'itensdenotasficais' ]

    results = []

    results += verificarDespesas(df_despesa)
    results += verificarReceitas(df_receita)
    results += verificarContratosTerceiros(df_contratoTerceiro)
    results += verificarBensPatrimoniados(df_bemPatrimoniado)
    results += verificarSaldos(df_saldo)
    results += verificarItensDeNF(df_itens)
        
    return results
