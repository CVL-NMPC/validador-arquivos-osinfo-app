from datetime import datetime
import pandas as pd
import requests
import streamlit as st
import os

class VerificarPDF:
    def __init__(self, base_url, log_directory, instituicao_directory, instituicao):
        print("Inicializando o verificador.")
        # Definição das propriedades básicas da classe.
        self.base_url = base_url + "/download/{numero_da_instituicao}/45/{nome_do_pdf}"  # URL base para a verificação dos arquivos PDF.
        self.log_directory = log_directory  # Diretório onde os logs serão salvos.
        self.instituicao_directory = instituicao_directory  # Diretório contendo os dados das instituições.
        self.instituicao = instituicao  # Dicionário com os códigos das instituições.

    def verificar_pdfs(self):
        # Cria o diretório de logs se ele ainda não existir.
        os.makedirs(self.log_directory, exist_ok=True)
        
        # Inicia o processo de verificação em cada pasta de instituição.
        for nome_instituicao in os.listdir(self.instituicao_directory):
            codigo_instituicao = self.instituicao.get(nome_instituicao)
            
            if codigo_instituicao:
                # Processamento para cada instituição encontrada.
                caminho_pasta_instituicao = os.path.join(self.instituicao_directory, nome_instituicao)
                
                # Processa cada arquivo de dados encontrado.
                for arquivo in os.listdir(caminho_pasta_instituicao):
                    if arquivo.endswith('.xlsx') or arquivo.endswith('.csv'):
                        print(f"Encontrado arquivo: {arquivo} para processamento.")
                        self.processar_arquivo(caminho_pasta_instituicao, arquivo, nome_instituicao, codigo_instituicao)

    def processar_arquivo(self, caminho_pasta_instituicao, nome_arquivo, nome_instituicao, codigo_instituicao):
        # Log do arquivo sendo processado.
        caminho_arquivo = os.path.join(caminho_pasta_instituicao, nome_arquivo)
        log_nome_arquivo = f"{os.path.splitext(nome_arquivo)[0]}_log.txt"
        log_caminho_arquivo = os.path.join(self.log_directory, log_nome_arquivo)
        
        # Leitura do arquivo Excel ou CSV.
        if nome_arquivo.endswith('.xlsx'):
            df = pd.read_excel(caminho_arquivo)
        elif nome_arquivo.endswith('.csv'):
            df = pd.read_csv(caminho_arquivo)

        # Verifica a presença das colunas específicas e processa cada arquivo listado.
        for column in ['NOVO_VALOR', 'DESCRIÇÃO']:
            if column in df.columns:
                for nome_imagem in df[column].unique():
                    if '_' in str(nome_imagem):
                        nome_imagem = nome_imagem.strip().replace(" ", "%")
                        if nome_imagem.casefold().endswith('.pdf'):
                            self.formatar_url(nome_imagem, codigo_instituicao)
                        else:
                            nome_imagem = nome_imagem + '.pdf'
                            self.formatar_url(nome_imagem, codigo_instituicao)
        
        # Exclusão do arquivo processado.
        os.remove(caminho_arquivo)

    def formatar_url(self, nome_imagem, codigo_instituicao, nome_instituicao, log_caminho_arquivo):
        # Construção da URL para verificação do arquivo PDF.
        print(f"Nome do PDF: {nome_imagem}")
        url = self.base_url.format(numero_da_instituicao=codigo_instituicao, nome_do_pdf=nome_imagem)
        self.check_url(url, nome_instituicao, nome_imagem, log_caminho_arquivo)

    def check_url(self, url, instituicao, nome_do_pdf, log_caminho_arquivo):
        # Verifica o status da URL usando uma solicitação HEAD.
        print(f"Verificando o status da URL: {url}")
        try:
            response = requests.head(url)
            
            # Avaliação do status do arquivo baseado no tamanho indicado no cabeçalho.
            if response.status_code == 200:
                status = 'Encontrado'
                if int(response.headers.get('Content-Length', 1)) == 0:
                    status = 'Corrompido'
            else:
                status = 'Não encontrado'
        except requests.RequestException as e:
            status = f'Erro de verificação: {str(e)}'

        # Registro do status no arquivo de log.
        print(f"Status: {status} para {nome_do_pdf}")
        mensagem_log = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Instituição: {instituicao}, PDF: {nome_do_pdf}, Status: {status}, URL: {url}\n"
        with open(log_caminho_arquivo, 'a') as log_file:
            log_file.write(mensagem_log)

# Códigos das instituições
codigos_os = {
    'spdm': '263', 'vivario': '264', 'fas': '265', 'cejam': '268',
    'riosaude': '9612', 'gnosis': '9615', 'ideias': '10040',
    'cieds': '10358', 'htmj': '9803', 'cruzvermelha': '9739',
    'fiotec': '259', 'iabas': '261', 'ciedsbrasil': '11225', 'ipcep': '9900'
}

# Diretórios de entrada de arquivos e saída de log
entrada = r"C:\Users\03477551\Documents\GMAPG_compartilhada\verificador_img_novo\Arquivos"
resultado = r"C:\Users\03477551\Documents\GMAPG_compartilhada\verificador_img_novo\Resultados"

# Definindo a URL
#base_url = "https://osinfo.prefeitura.rio/download/{numero_da_instituicao}/45/{nome_do_pdf}"
base_url = st.secrets["base_url"] + "/download/{numero_da_instituicao}/45/{nome_do_pdf}"

# Pau na máquina
verificador = VerificarPDF(base_url, resultado, entrada, codigos_os)
verificador.verificar_pdfs()