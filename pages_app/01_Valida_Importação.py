# -*- encoding:utf-8 -*-
# streamlit run streamlit_app.py

import streamlit as st
import utils.util as util
import utils.cabecalho as cabecalho
from io import StringIO
import pandas as pd
import datetime
import classes.DespesasDFImportacao as DespesasDFImportacao
import classes.ContratosTerceirosDFImportacao as ContratosTerceirosDFImportacao
import classes.SaldosDFImportacao as SaldosDFImportacao
import classes.BensPatrimoniadosDFImportacao as BensPatrimoniadosDFImportacao


cabecalho.criar_cabecalho("Validação de arquivos de importação", "Validação Arquivos OSINFO")

# listas
tipoArquivo = ['Despesas', 'Contratos de Terceiros', 'Saldos', 'Bens Patrimoniados']

secretarias = util.obter_instituicoes()
instituicoes = util.carregaInstituicoes()
contratos = util.carregaContratos()
validou = ""
limite = 2000

with st.form('Valida Importação', clear_on_submit=False):
    tipoarquivoEscolhido = st.selectbox('Tipo de Arquivo', tipoArquivo, index=None, placeholder="Selecione o Tipo de Arquivo")
    # converterUTF8 = st.checkbox("Converter o arquivo para UTF-8?")
    arquivo = st.file_uploader("Arquivo a ser verificado", type="csv", help="Envie um arquivo de cada vez")
    processou = st.form_submit_button("Processar")

    if processou:
        if arquivo and tipoarquivoEscolhido:
            pBar = st.progress(0)
            try:                        
                string_data = StringIO(arquivo.getvalue().decode("utf-8-sig"))
                cabecalhoArquivo = string_data.readline().strip()
                string_data.seek(0)
                
                meuModelo = util.Modelo()
                cabecalhoArquivo = meuModelo.trataCabecalho(cabecalhoArquivo)

                df = pd.read_csv(string_data, sep=';', header=0, index_col=False, dtype=str)
                tamanho = len(df)                        
                st.info("Quantidade de linhas do arquivo: " +str(tamanho))
                st.write("Arquivo original:")
                st.dataframe(df)                        

                # Convertendo para string para garantir que não haja problemas
                listaOS = [column for column in df.columns if column in meuModelo.listaOS]                        
                if not len(listaOS) > 0:
                    raise Exception("Não foi possível identificar o código da instituição no arquivo enviado")

                if len(listaOS) > 0:
                    verificador = util.Validadora(st.secrets['base_url'], df[listaOS].iloc[0,0])
                    listaDatasCompletas = [column for column in df.columns if column in meuModelo.datasCompletas]
                    listaDatasAbreviadas = [column for column in df.columns if column in meuModelo.datasAbreviadas]
                    listacamposPDF = [column for column in df.columns if column in meuModelo.documentosPDF]
                    listaDatasCompletasRenomeado = [column + '_VALIDADA' for column in df.columns if column in meuModelo.datasCompletas]
                    listaDatasAbreviadasRenomeadas = [column + '_VALIDADA' for column in df.columns if column in meuModelo.datasAbreviadas]
                    listacamposPDFRenomeados = ['TEM_IMAGEM' for column in df.columns if column in meuModelo.documentosPDF]
                
                    if tipoarquivoEscolhido == "Despesas":
                        despesas = DespesasDFImportacao.DespesasDFImportacao(df, st.secrets['base_url'], listaOS, pBar)
                        despesas.check_header()
                        st.info('O cabeçalho é compatível com o modelo DESPESAS GNOSIS.')
                        if despesas.check_df_data():
                            validou = 1
                        st.dataframe(df) 

                    elif tipoarquivoEscolhido == "Contratos de Terceiros":
                        contratos = ContratosTerceirosDFImportacao.ContratosTerceirosDFImportacao(df, st.secrets['base_url'], listaOS, pBar)
                        contratos.check_header()
                        st.info('O cabeçalho é compatível com o modelo CONTRATOS DE TERCEIROS.')
                        if contratos.check_df_data():
                            validou = 1
                        st.dataframe(df)
                            
                    elif tipoarquivoEscolhido == "Saldos":
                        saldos = SaldosDFImportacao.SaldosDFImportacao(df, st.secrets['base_url'], listaOS, pBar)
                        saldos.check_header()
                        st.info('O cabeçalho é compatível com o modelo SALDOS.')
                        if saldos.check_df_data():
                            validou = 1
                        st.dataframe(df)

                    elif tipoarquivoEscolhido == "Bens Patrimoniados":
                        bens = BensPatrimoniadosDFImportacao.BensPatrimoniadosDFImportacao(df, st.secrets['base_url'], listaOS, pBar)
                        bens.check_header()
                        st.info('O cabeçalho é compatível com o modelo SALDOS.')
                        if bens.check_df_data():
                            validou = 1
                        st.dataframe(df)
                    else:
                        st.warning("Não foi possível identificar qual a verificação deve ser realizada.", icon="⚠️")
                    
                    st.success('Processamento concluído!')
            except UnicodeDecodeError:
                st.error(util.erros["02"])
            except Exception as e:
                st.error(f"Operação abortada: {e}")

        else:
            st.error('Todos os campos devem ser preenchidos!')

if validou:
    st.write("Arquivo processado:")
    st.dataframe(df)
    nomeArquivo = f"VALIDADO_{str(df.iloc[0,0])}_{datetime.datetime.now().strftime('%d-%m-%Y-%H-%M')}.csv"
    st.download_button(label="Download do arquivo CSV", data=df.to_csv(sep=';', index=False), mime='text/csv', file_name=nomeArquivo)