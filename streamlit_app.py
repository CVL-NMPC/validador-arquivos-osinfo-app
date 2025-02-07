import streamlit as st

pages_app = {
    "Validação de Arquivos": [
        st.Page("pages_app/01_Valida_Importação.py", title="Arquivos de importação"),
    ],
    "Modelo de Arquivo": [
        st.Page("pages_app/modelos_arquivos_importacao.py", title="Importação"),
    ],
    "Sobre": [
        st.Page("pages_app/sobre_aplicacao.py", title="Sobre a aplicação"),
    ]
}


pg = st.navigation(pages_app)
pg.run()
