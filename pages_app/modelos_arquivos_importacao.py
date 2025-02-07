import streamlit as st
import base64
import utils.cabecalho as cabecalho

def convert_file_to_b64(file_path):
    with open(arquivo, "rb") as f:
        file_data = f.read()
        b64 = base64.b64encode(file_data).decode()
        return b64

def criar_href(file_path, file_name, caption):
    b64 = convert_file_to_b64(file_path)
    href = f'<a href="data:file/csv;base64,{b64}" download="{file_name}">📥 Baixar modelo de importação de {caption}</a>'
    return href

cabecalho.criar_cabecalho("Arquivos de modelo para importação", "Modelos de arquivos")


arquivo = 'modelos_arquivo_importacao/modelo_importacao_despesas.csv'
st.markdown(criar_href(arquivo, "modelo_importacao_despesas.csv", "DESPESAS"), unsafe_allow_html=True)

arquivo = 'modelos_arquivo_importacao/modelo_importacao_bens_patrimoniados.csv'
st.markdown(criar_href(arquivo, "modelo_importacao_bens_patrimoniados.csv", "BENS PATRIMONIADOS"), unsafe_allow_html=True)

arquivo = 'modelos_arquivo_importacao/modelo_importacao_contratos_terceiros.csv'
st.markdown(criar_href(arquivo, "modelo_importacao_contratos_terceiros.csv", "CONTRATOS DE TERCEIROS"), unsafe_allow_html=True)

arquivo = 'modelos_arquivo_importacao/modelo_importacao_itens_nota_fiscal.csv'
st.markdown(criar_href(arquivo, "modelo_importacao_itens_nota_fiscal.csv", "ITENS DE NOTA FISCAL"), unsafe_allow_html=True)

arquivo = "modelos_arquivo_importacao/modelo_importacao_saldos.csv"
st.markdown(criar_href(arquivo, "modelo_importacao_saldos.csv", "SALDOS"), unsafe_allow_html=True)