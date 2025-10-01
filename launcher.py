"""Este archivo controla el flujo de navegacion de la aplicacion, todas las paginas
de la API se encuentran aqui"""

# Python Librerias

# Mis modulos
import lenguaje

# 3ros Librerias
import streamlit as st

l=lenguaje.tu_idioma()
st.sidebar.subheader(f':orange[{l.phrase[60]}]')

iterable_pages = [
st.Page(page='inicio.py', title=l.phrase[0], icon=':material/store:'),
st.Page(page='vender.py', title=l.phrase[1], icon=':material/sell:'),
st.Page(page='inventario.py', title=l.phrase[2], icon=':material/inventory_2:'),
st.Page(page='por_facturar.py', title=l.phrase[61], icon=':material/request_quote:'),
st.Page(page='historial.py', title=l.phrase[4], icon=':material/history:'),
st.Page(page='estadisticas.py', title=l.phrase[5], icon=':material/analytics:'),
st.Page(page='config.py', title=l.phrase[6], icon=':material/settings:')
]

to_run = st.navigation(pages=iterable_pages, position='sidebar')

to_run.run()
