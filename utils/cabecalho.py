import streamlit as st
import os

def criar_cabecalho(titulo_pagina, titulo_aba):
    st.set_page_config(
        page_title=titulo_aba,
        page_icon='https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f5a5.svg',
        layout="wide"
    )
    image_path = os.path.join(os.getcwd(), "images", "RIOPREFEITURA_Controladoria_Geral_horizontal_azul.png")
    st.image(image=image_path, width=300)
    st.header(titulo_pagina.upper(), divider="gray")
