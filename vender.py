import datetime
import json
import os
import io

from lenguaje import tu_idioma

import streamlit as st
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF

l=tu_idioma()

st.header(f':material/sell: {l.phrase[1]}')

DIRECCION = 'Santa Ana Chiautempan, Tlaxcala C.P. 90800'

RUTA_HISTORIAL = 'ventas_historial.json'
RUTA_PRODUCTOS = '_inventario_providencia.json'

CODIGO_QR = 'Cero'

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

def get_folio(data:dict):
    try:
        df = pd.DataFrame(data=data)

        folio = df['Folio']
        folio = sorted(folio,reverse=True)

        if len(folio) > 0:
            folio = folio[0]
            folio += 1
            return folio
        else:
            return 0
    except KeyError:
        return 0

def acceso_a_productos():
    try:
        if os.path.exists(RUTA_PRODUCTOS) and os.path.getsize(RUTA_PRODUCTOS) > 0:
            with open(RUTA_PRODUCTOS, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            st.warning(l.phrase[19])
    except(FileNotFoundError,json.JSONDecodeError):
        st.error(l.phrase[18])

def formulario_venta(folio:int, data:dict):

    # Creo los DataFrames y hago copia 1 y copia 2
    df=pd.DataFrame(data=data)
    df['Indice P'] = df['Producto']
    copia1 = df.copy()
    copia1['Precio Lista']=round(copia1['Precio Lista'],2)
    copia2 = df.copy()
    
    df.set_index(keys='Indice P',inplace=True)
    copia1.set_index(keys='Producto',inplace=True)
    copia2.set_index(keys='Producto',inplace=True)

    OPCIONES = copia1.index.to_list()

    DF_VACIO = pd.DataFrame({
        'Piezas':[None],
        'Producto':[None],
        'C 1':[None],
        'C 2':[None],
        'U. Medida':[None],
        'Precio':[None],
        'Total':[None],
        'Existencias':[None],
        'Codigos':[None]
    })

    TOTAL_PRODUCTOS = 0
    TOTAL_COSTO = 0

    if 'df' not in st.session_state:
        st.session_state.df = DF_VACIO
    if 'total_productos' not in st.session_state:
        st.session_state.total_productos = TOTAL_PRODUCTOS
    if 'total_costo' not in st.session_state:
        st.session_state.total_costo = TOTAL_COSTO

    HOY = datetime.date.today()

    st.write(f'{l.phrase[20]}: {DIRECCION}')

    col_1, col_2, col_3 = st.columns(3)
    col_1.write(f'__{l.phrase[21]}__')
    col_2.write(f'__{l.phrase[22]}: :red[{folio}]__')
    col_3.write(HOY)

    df_venta = st.data_editor(
        data=st.session_state.df,
        num_rows='dynamic',
        column_config={
            'Piezas':st.column_config.NumberColumn(
                width=75,
                help=':orange[Piezas]',
                required=True,
                pinned=True,
                min_value=1,
                step=1
            ),
            'Producto':st.column_config.SelectboxColumn(
                width=250,
                help=':orange[Producto]',
                required=True,
                pinned=True,
                options=OPCIONES,
                ),
            'C 1':st.column_config.TextColumn(
                width=75,
                help=':orange[Categoría 1]',
                disabled=True,
                pinned=True,
            ),
            'C 2':st.column_config.TextColumn(
                width=75,
                help=':orange[Categoría 2]',
                disabled=True,
                pinned=True
            ),
            'U. Medida':st.column_config.TextColumn(
                width=70,
                help=':orange[Unidad]',
                disabled=True,
                pinned=True,
            ),
            'Precio':st.column_config.NumberColumn(
                width=80,
                help=':orange[Precio]',
                disabled=True,
                pinned=True,
                format='dollar'
            ),
            'Total':st.column_config.NumberColumn(
                width=80,
                help=':orange[Total]',
                format='dollar',
                disabled=True,
                pinned=True,
            ),
            'Existencias':st.column_config.NumberColumn(
                width=60,
                help=':orange[Existencias]',
                disabled=True,
                pinned=True,
            ),
            'Codigos':st.column_config.TextColumn(
                width=60,
                help='Codigos',
                disabled=True,
                pinned=True
            )
        }
    )

    df_venta = pd.DataFrame(data=df_venta)

    if df_venta.empty:
        try:
            st.session_state.df=DF_VACIO
            st.session_state.total_productos=TOTAL_PRODUCTOS
            st.session_state.total_costo=TOTAL_COSTO
        except KeyError:
            if 'df' not in st.session_state:
                st.session_state.df =DF_VACIO
            if 'total_productos' not in st.session_state:
                st.session_state.total_productos=TOTAL_PRODUCTOS
            if 'total_costo' not in st.session_state:
                st.session_state.total_costo=TOTAL_COSTO

    col_4, col_5 = st.columns(2)

    col_4.metric(
        label=l.phrase[23],
        value=st.session_state.total_productos,
        border=True,
        height='stretch',
        )
    col_5.metric(
        label=l.phrase[24],
        value=st.session_state.total_costo,
        border=True,
        height='stretch'
        )

    col_6, col_7, col_8, = st.columns(3)

    with col_6:
        calculo = st.button(
            label=l.phrase[25],
            key='calcular_totales',
            type='secondary',
            help=':orange[Requiere Doble Click]',
            width='stretch'
        )
    with col_7:
        limpiar_tabla = st.button(
            label=l.phrase[26],
            key='reset_tabla',
            type='secondary',
            help=':orange[Requiere Doble Click]',
            width='stretch'
            )
    with col_8:
        registrar_venta = st.button(
            label=l.phrase[27],
            key='registrar_venta',
            type='primary',
            help=':orange[Requiere Doble Click]',
            width='stretch'
        )

    if calculo or registrar_venta:

        df_venta=df_venta.dropna(axis=0,how='any',subset=['Piezas','Producto'])
        df_venta=df_venta.drop_duplicates(subset=['Producto'],keep='first',ignore_index=True)

        copia1 = copia1.loc[df_venta['Producto'],:]

        df_union = df_venta.merge(copia1,how='left', on='Producto')

        df_union['C 1'] = df_union['Categoría 1']
        df_union['C 2'] = df_union['Categoría 2']
        df_union['U. Medida'] = df_union['Unidad']
        df_union['Precio'] = df_union['Precio Lista']
        df_union['Total'] = df_union['Piezas'] * df_union['Precio Lista']
        df_union['Existencias'] = df_union['Cantidad']
        df_union['Codigos'] = df_union['Codigo'].astype('str')

        df_union = df_union[[
            'Piezas',
            'Producto',
            'C 1',
            'C 2',
            'U. Medida',
            'Precio',
            'Total',
            'Existencias',
            'Codigos'
        ]]

        st.session_state.df=df_union
        st.session_state.total_productos = df_union['Piezas'].sum()
        st.session_state.total_costo = df_union['Total'].sum()

        if registrar_venta:
            
            df_salida = st.session_state.df
            productos_vendidos = st.session_state.total_productos
            costos_totales = st.session_state.total_costo
            
            try:
                st.session_state.df=DF_VACIO
                st.session_state.total_productos = TOTAL_PRODUCTOS
                st.session_state.total_costo = TOTAL_COSTO
            except KeyError:
                if 'df' not in st.session_state:
                    st.session_state.df = DF_VACIO
                if 'total_productos' not in st.session_state:
                    st.session_state.total_productos = TOTAL_PRODUCTOS
                if 'total_costo' not in st.session_state:
                    st.session_state.total_costo = TOTAL_COSTO
            
            # Filtro los articulos que no pueden ser vendidos por falta de inventario y aquellos de los cuales no se tenga inventario.
            df_salida['Mascara'] = (df_salida['Existencias'] - df_salida['Piezas']) < 0

            if df_salida['Mascara'].any():
                st.info(l.phrase[28])
                return
            
            df_salida.drop(inplace=True,labels='Mascara',axis=1)
            
            copia2 = copia2.loc[df_salida['Producto'],:]
            
            df_ajuste = df_salida.merge(copia2,how='left',on='Producto')
            df_ajuste['Cantidad'] = df_ajuste['Cantidad'] - df_ajuste['Piezas']
            df_ajuste = df_ajuste[[
                'Codigo',
                'Producto',
                'Cantidad',
                'Categoría 1',
                'Categoría 2',
                'Unidad',
                'Precio Compra',
                'Porcentaje Ganancia',
                'Precio Lista',
                'Clave',
                'Oficial'
                ]]
            
            df.loc[df_ajuste['Producto']]=df_ajuste.values
            df.reset_index(drop=True, inplace=True)
            datos = df.to_dict(orient='list')
            
            df_ajuste['Folio'] = folio
            df_ajuste['Fecha'] = HOY.isoformat()
            df_ajuste['Cantidad'] = df_salida['Piezas']
            df_ajuste['Total'] = df_salida['Piezas'] * df_salida['Precio']
            df_ajuste['Precio Compra'] = round(df_ajuste['Precio Compra'],2)
            df_ajuste = df_ajuste[[
                'Folio',
                'Fecha',
                'Codigo',
                'Producto',
                'Cantidad',
                'Categoría 1',
                'Categoría 2',
                'Unidad',
                'Precio Compra',
                'Porcentaje Ganancia',
                'Precio Lista',
                'Total',
                'Clave',
                'Oficial'
            ]]

            with open(RUTA_PRODUCTOS,'w',encoding='utf-8') as f:
                json.dump(datos,f,indent=4,ensure_ascii=False)

            if os.path.exists(RUTA_HISTORIAL) and os.path.getsize(RUTA_HISTORIAL) > 0:
                historial_actual = acceso_a_historial()
                df_historial = pd.DataFrame(data=historial_actual)
                datos_historial = pd.concat([df_historial,df_ajuste])
                datos_historial = datos_historial.to_dict(orient='list')
                with open(RUTA_HISTORIAL,'w',encoding='utf-8') as h:
                    json.dump(datos_historial,h,indent=4,ensure_ascii=False)
            else:
                with open(RUTA_HISTORIAL,'w',encoding='utf-8') as h:
                    datos_nuevos = df_ajuste.to_dict(orient='list')
                    json.dump(datos_nuevos,h,indent=4,ensure_ascii=False)

            st.success(l.phrase[29])

            # Aqui comienza el codigo que genera la nota impresa como hoja tamanho carta pdf:
            class PDF(FPDF):
                def __init__(self, orientation = "portrait", unit = "mm", format = "letter"):
                    super().__init__(orientation, unit, format)
                    self.add_font(family='ArialUnicodeMS',fname='arial-unicode-ms.ttf',uni=True)
                def header(self):
                    self.set_text_color(0,0,0)
                    self.set_font(family='ArialUnicodeMS',size=20)
                    self.image('pro.jpg',10,8,16)
                    self.cell(20,6,txt=l.phrase[21],border=False,center=True,ln=True,align='C')
                    self.ln(15)
                    return super().header()
                def footer(self):
                    self.set_y(-10)
                    self.set_font(family='ArialUnicodeMS',size=7)
                    self.cell(0,6,txt=f'{l.phrase[15]} {self.page_no()}/{{nb}}',center=True)
                    return super().footer()

            pdf = PDF()
            # Salto de pagina automatico
            pdf.set_auto_page_break(auto=True,margin=10)

            # Parametros para la hoja PDF
            pdf.add_page()
            pdf.set_font(family='ArialUnicodeMS',size=9)
            pdf.set_line_width(0.1)
            pdf.set_draw_color(224,224,224)
            pdf.set_fill_color(224,224,224)#204,255,229
            pdf.set_text_color(96,96,96)

            # Datos Extras:
            pdf.cell(98,6,txt=f'{l.phrase[20]}: {DIRECCION}',border=True,align='C')
            pdf.cell(49,6,txt=f'{l.phrase[30]}: {HOY.isoformat()}',border=True,align='C')
            pdf.cell(49,6,txt=f'{l.phrase[22]}: {str(folio)}',border=True,align='C',ln=True)
            # Linea Muerta
            pdf.cell(0,1,fill=True,ln=True)
            
            # Nombres De las Columnas
            
            pdf.cell(17,6,txt='UNI.',border=True,align='C')
            pdf.cell(92,6,txt='PRODUCTO',border=True,align='L')
            pdf.cell(26,6,text='PRECIO U.',border=True,align='R')
            pdf.cell(26,6,txt='TOTAL',border=True,align='R')
            pdf.cell(35,6,txt='CODIGO',border=True,align='C',ln=True)
            # Linea Muerta
            pdf.cell(0,1,fill=True,ln=True)
            
            # Iteramos en la tabla con datos de venta:
            for i,row in df_salida.iterrows():
                rv = io.BytesIO()
                barcode.Code128(row['Codigos'],writer=ImageWriter()).write(rv)
                rv.seek(0)
                y = pdf.get_y()
                x = pdf.get_x()
                x_pos = (x+17+92+26+26)
                pdf.cell(17,7,txt=f'{row['Piezas']}',border=True,align='C')
                pdf.cell(92,7,txt=f'{row['Producto']}',border=True,align='L') 
                pdf.cell(26,7,txt=f'$ {row['Precio']}',border=True,align='R') 
                pdf.cell(26,7,txt=f'$ {row['Total']}',border=True,align='R')
                pdf.image(y=y,x=x_pos,name=rv,w=35,h=7)
                pdf.ln()
                pdf.cell(0,1,fill=True,ln=True)

            # Tamanho de la pagina pdf:
            half_page = (pdf.w / 2) - 10
            pdf.cell(half_page,6,txt=f'{l.phrase[23]}: {productos_vendidos}', border=True, align='C')
            pdf.cell(half_page,6,txt=f'{l.phrase[24]}: $ {costos_totales}', border=True,align='C',ln=True)

            pdf_output = bytes(pdf.output(dest='S'))

            st.download_button(
                    label=l.phrase[16],
                    type='primary',
                    data=pdf_output,
                    key='descarga_venta_recibo',
                    file_name="Ticket Venta.pdf",
                    mime="application/pdf",
                    width='stretch'
                )

    if limpiar_tabla:
        try:
            st.session_state.df=DF_VACIO
            st.session_state.total_productos = TOTAL_PRODUCTOS
            st.session_state.total_costo = TOTAL_COSTO
        except KeyError:
            if 'df' not in st.session_state:
                st.session_state.df = DF_VACIO
            if 'total_productos' not in st.session_state:
                st.session_state.total_productos = TOTAL_PRODUCTOS
            if 'total_costo' not in st.session_state:
                st.session_state.total_costo = TOTAL_COSTO


# LLAMADO A LAS FUNCIONES -----------------------------------------------------------------------------------------------------------

historial = acceso_a_historial()
folio = get_folio(historial)
productos = acceso_a_productos()
formulario_venta(folio=folio,data=productos)
