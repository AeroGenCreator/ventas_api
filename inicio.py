import json
import datetime
import os

import lenguaje

import streamlit as st
import pandas as pd
from fpdf import FPDF

l = lenguaje.tu_idioma()
st.title(f':material/store: {l.phrase[0]}')

HOY = datetime.date.today().isoformat()
RUTA_CONFIG = 'configuracion_file.json'

def acceso_fondo_caja():
    
    try:
        if os.path.exists(RUTA_CONFIG) and os.path.getsize(RUTA_CONFIG) > 0:
            with open(RUTA_CONFIG,'r',encoding='utf-8') as f:
                datos = json.load(f)   
                return datos['configuracion']['caja fondo']
        else:
            st.warning(f'1. No se encuentra o se altero el archivo {RUTA_CONFIG}. Pedir ayuda con el soporte')
    except (FileNotFoundError,FileExistsError,json.JSONDecodeError):
        st.warning(f'2. No se encuentra o se altero el archivo <{RUTA_CONFIG}> Pedir ayuda con el soporte')

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

historial = acceso_a_historial()

def venta_total_de_hoy(data=historial, fecha=HOY):
    try:
        df = pd.DataFrame(data=historial)
        filtro = df[df['Fecha']==HOY]
        total = filtro['Total'].sum()
        return total
    except KeyError:
        return 0

def beneficio_bruto_de_hoy(data=historial,fecha=HOY):
    try:
        df = pd.DataFrame(historial)
        filtro = df[df['Fecha']==HOY]
        filtro['Costo De Bienes'] = filtro['Cantidad'] * filtro['Precio Compra']
        filtro['Beneficio Bruto'] = filtro['Total'] - filtro['Costo De Bienes']
        beneficio_bruto_total = filtro['Beneficio Bruto'].sum()
        return beneficio_bruto_total
    except KeyError:
        return 0
     
def margen_beneficio_bruto_hoy():
    try:
        venta_total = venta_total_de_hoy()
        beneficio_bruto = beneficio_bruto_de_hoy()
        try:
            margen = (beneficio_bruto/venta_total) * 100
            return round(margen,2)
        except ZeroDivisionError:
            return None
        
    except KeyError:
        return 0

def total_productos_del_dia(data=historial,fecha=HOY):
    try:
        df = pd.DataFrame(data=historial)
        filtro = df[df['Fecha']==HOY]
        productos_total = filtro['Cantidad'].sum()
        return productos_total
    except KeyError:
        return 0



venta = venta_total_de_hoy()
venta = str(venta)
venta = '$ ' + venta

beneficio = beneficio_bruto_de_hoy()
beneficio = str(beneficio)
beneficio = '$ ' + beneficio

margen_beneficio = margen_beneficio_bruto_hoy()
margen_beneficio = str(margen_beneficio)
margen_beneficio = '% ' + margen_beneficio

fondo = acceso_fondo_caja()
fondo = str(fondo)
fondo = '$ ' + fondo

caja = acceso_fondo_caja()
extra = venta_total_de_hoy()
total_en_caja = extra + caja
total_en_caja = str(total_en_caja)
total_en_caja = '$ ' + total_en_caja

tab_1, tab_2 = st.tabs([l.phrase[0],l.phrase[14]])

with tab_1:
    col_1, col_2 = st.columns([1,3])

    col_1.image('providencia_logo.jpeg',width=85,caption=l.phrase[7])
    col_2.metric(label=l.phrase[8],value=venta,border=True)

    col_3,col_4,col_5 = st.columns(3)

    col_3.metric(label=l.phrase[9],value=total_productos_del_dia(),border=True)
    col_4.metric(label=l.phrase[10],value=beneficio,border=True)
    col_5.metric(label=l.phrase[11],value=margen_beneficio,border=True)

    col_6, col_7 = st.columns(2)
    col_6.metric(label=l.phrase[12], value=fondo, border=True,width='stretch')
    col_7.metric(label=l.phrase[13], value=total_en_caja, border=True,width='stretch')

with tab_2:
    
    div_1, div_2 = st.columns([1,1])
    div_1.write(f'{l.phrase[13]}: {total_en_caja}')
    div_2.write(f'{l.phrase[12]}: :red[{fondo}]')
    st.write(f'{l.phrase[8]}: {venta}')
    st.write(f'{l.phrase[10]} {beneficio}')
    st.write(f'{l.phrase[11]} {margen_beneficio}')
    corte = st.button(label=l.phrase[14],key='Corte del Dia',width='stretch',type='primary')

    if corte:
        class PDF(FPDF):
            def __init__(self, orientation = "portrait", unit = "mm", format = "letter"):
                super().__init__(orientation, unit, format)
                self.add_font(family='ArialUnicodeMS',fname='arial-unicode-ms.ttf',uni=True)
            def header(self):
                self.set_text_color(0,0,0)
                self.set_font(family='ArialUnicodeMS',size=20)
                self.image('pro.jpg', 10, 8, 16)
                self.cell(20,6,txt=l.phrase[14], border=False,center=True,ln=True,align='C')
                self.ln(15)
            def footer(self):
                self.set_y(-10)
                self.set_font(family='ArialUnicodeMS',size=7)
                self.cell(0,6,txt=f'{l.phrase[15]} {self.page_no()}/{{nb}}', center=True)
                    
        # Creo el resto de la hoja con PDF
        pdf = PDF(orientation='portrait',unit='mm',format='Letter')
        # Inicializo el auto salto de pagina
        pdf.set_auto_page_break(auto=True, margin=10)

        # Establezco los parametros de la hoja, fuente, color, tamanho
        pdf.add_page()
        pdf.set_font(family='ArialUnicodeMS',size=9)
        pdf.set_line_width(0.1)
        pdf.set_draw_color(224,224,224)
        pdf.set_fill_color(224,224,224)#204,255,229
        pdf.set_text_color(96,96,96)

        pdf.cell(65,6,text=f'Fecha: {HOY}',ln=True,border=True)
        pdf.cell(0,4,fill=True,ln=True)

        # Creo los nombre de las columnas, las cuales iran por encima de los datos de tabla
        pdf.cell(65,6,txt=l.phrase[13],border=True,align='C')
        pdf.cell(65,6,text=l.phrase[12],border=True,align='C')
        pdf.cell(66,6,text=l.phrase[8],border=True,align='C',ln=True)
        
        # Creo una linea muerta como separador
        pdf.cell(0,2,fill=True,ln=True)

        pdf.cell(65,6,txt=f'{total_en_caja}',border=True,align='C')
        pdf.cell(65,6,txt=f'{fondo}',border=True,align='C')
        pdf.cell(66,6,txt=f'{venta}',border=True,align='C',ln=True)

        # Dedermino el tamanho de mi pagina, lo divido y le resto 10 unidades.
        half_page = (pdf.w / 2) - 10

        # Determino formatos e imprimo los contadores al final de la tabla.
        pdf.cell(0,4,fill=True,ln=True)
        pdf.cell(half_page,6,txt=l.phrase[10], border=True, align='C')
        pdf.cell(half_page,6,txt=l.phrase[11], border=True, align='C',ln=True)

        pdf.cell(half_page,6,txt=f'{beneficio}',border=True, align='C')
        pdf.cell(half_page,6,txt=f'{margen_beneficio}',border=True,align='C',ln=True)
        
        # Guarda el PDF en un archivo temporal cpmo bytes, el output debe ser dest='S'
        pdf_output = bytes(pdf.output(dest='S'))
        
        # Proporciona el botón de descarga de streamlit y le asigno el pdf temporal.
        st.download_button(
            label=l.phrase[16],
            key='descarga_corte',
            type='primary',
            data=pdf_output,
            file_name="corde_del_dia.pdf",
            mime="application/pdf",
            width='stretch'
        )