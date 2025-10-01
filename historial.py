import json
import os

import lenguaje

import streamlit as st

RUTA_HISTORIAL = 'ventas_historial.json'
def acceso_a_historial():
    try:
        if os.path.exists(RUTA_HISTORIAL) and os.path.getsize(RUTA_HISTORIAL) > 0:
            with open(RUTA_HISTORIAL,'r',encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            st.warning(l.phrase[17])
            
    except(FileNotFoundError, json.JSONDecodeError, TypeError):
        st.error(l.phrase[18])

l=lenguaje.tu_idioma()

st.header(f':material/history: {l.phrase[4]}')

data = acceso_a_historial()

st.dataframe(data=data,hide_index=True)