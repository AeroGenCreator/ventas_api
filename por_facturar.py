import json
import datetime
import os 
import math

import lenguaje

from fpdf import FPDF
import streamlit as st
import pandas as pd

import email, smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

RUTA_CONFIG = 'configuracion_file.json'

HOY = datetime.date.today()

def get_folio_factura_descuento():
    try:
        if os.path.exists(RUTA_CONFIG) and os.path.getsize(RUTA_CONFIG) > 0:
            with open(RUTA_CONFIG,'r',encoding='utf-8') as conf:
                data = json.load(conf)
                porcentaje_descuento = data['configuracion']['descuento general']
                folio_factura = data['configuracion']['folio factura']
                return (porcentaje_descuento, folio_factura)
        else:
            return
    except TypeError:
        return

def nombres_de_facturas():
    try:
        if os.path.exists(RUTA_CONFIG) and os.path.getsize(RUTA_CONFIG) > 0:
            with open(RUTA_CONFIG,'r',encoding='utf-8') as conf:
                data = json.load(conf)
                lista_nombres = data['configuracion']['nombres de facturas']
                return lista_nombres
        else:
            return
    except TypeError:
        return

def escribir_nuevo_nombre_factura(nombre:str):
    try:
        if os.path.exists(RUTA_CONFIG) and os.path.getsize(RUTA_CONFIG) > 0:
            with open(RUTA_CONFIG,'r',encoding='utf-8') as conf:
                data = json.load(conf)
                data['configuracion']['nombres de facturas'].append(nombre)
                with open(RUTA_CONFIG,'w',encoding='utf-8') as esc:
                    json.dump(data,esc,indent=4,ensure_ascii=False)
                    return st.success(l.phrase[34])
        else:
            return
    except TypeError:
        return

def generar_factura_pdf(folio_name, folio_number, discount_percentage):
    # Creo una clase PDF con FPDF, la clase contendra header() y footer(), configuro alineacion, y colores
    class PDF(FPDF):
        def __init__(self, orientation = "portrait", unit = "mm", format = "letter"):
            super().__init__(orientation, unit, format)
            self.add_font(family='ArialUnicodeMS',fname='arial-unicode-ms.ttf',uni=True,style="")
        def header(self):
            self.set_text_color(0,0,255)
            self.set_font(family='ArialUnicodeMS',size=15)
            self.image('pro.jpg',w=13,h=13)
            self.cell(0,6,txt=l.phrase[61], border=False,ln=True,align='C')
            
        def footer(self):
            self.set_y(-10)
            self.set_font(family='ArialUnicodeMS',size=7)
            self.cell(0,6,txt=f'{l.phrase[15]} {self.page_no()}/{{nb}}', center=True)
        
    # Creo el resto de la hoja con PDF
    pdf = PDF(orientation='portrait',unit='mm',format='A5')
    # Inicializo el auto salto de pagina
    pdf.set_auto_page_break(auto=True, margin=15)

    # Establezco los parametros de la hoja, fuente, color, tamanho
    pdf.add_page()
    pdf.set_font(family='ArialUnicodeMS',size=8.5)
    pdf.set_line_width(0.2)
    pdf.set_draw_color(204,229,255)
    pdf.set_fill_color(204,229,255)
    pdf.set_text_color(64,64,64)
    
    # Dedermino el tamanho de mi pagina, lo divido y le resto 10 unidades.
    half_page = (pdf.w / 2) - 10
    pdf.cell(0,1,fill=True,ln=True)
    pdf.cell(0,6,text=f'{l.phrase[68]}: {folio_name}',align='C',border=True,ln=True)
    pdf.cell(half_page,6,text=f'{l.phrase[22]}: {folio_number}',align='C',border=True)

    pdf.set_text_color(64,64,64)
    pdf.cell(half_page,6,text=f'{l.phrase[30]}: {HOY.isoformat()}',align='C',ln=True,border=True)
    pdf.cell(0,1,fill=True,ln=True)
    
    pdf.cell(14,6,txt='PIEZAS',border=True,align='C')
    pdf.cell(18,6,text='MEDIDA',border=True,align='C')
    pdf.cell(76,6,txt='PRODUCTO',border=True,align='C')
    pdf.cell(20.5,6,txt='TOTAL', ln=True,border=True,align='R')
    
    pdf.cell(0,1,fill=True,ln=True)
    
    # Itero sobre los datos que estan en la tabla final guardada en el cache de streamlit
    # y los asigno a su celda pdf.
    pdf.set_font(family='ArialUnicodeMS',size=8)
    for index, row in st.session_state.df_c.iterrows():
        pdf.cell(14,5,txt=f'{row['Unidades']}',border=True,align='C')
        pdf.cell(18,5,text=f'{row['Medida']}',border=True,align='C')
        pdf.cell(76,5,txt=f'{row['Producto']}',border=True)
        pdf.cell(20.5,5,txt=f'$ {round(row['Total'],2)}', ln=True,border=True,align='R')
    
    pdf.set_font(family='ArialUnicodeMS',size=8.5)
    # Determino formatos e imprimo los contadores al final de la tabla.
    pdf.cell(0,1,fill=True,ln=True)
    pdf.cell(half_page,6,txt=f'{l.phrase[23]}: {st.session_state.productos}', border=True, align='C')
    pdf.cell(half_page,6,txt=f'{l.phrase[24]}: $ {round(st.session_state.total,2)}', border=True,align='C',ln=True)

    pdf.cell(half_page,6,text=f'{l.phrase[63]}: %{round(discount_percentage * 100)}',border=True,align='C')
    pdf.set_text_color(0,0,255)
    pdf.cell(half_page,6,text=f'{l.phrase[62]}: $ {round(st.session_state.total_desc,2)}',border=True,align='C',ln=True)
    
    # Guarda el PDF en un archivo temporal cpmo bytes, el output debe ser dest='S'
    pdf_output = bytes(pdf.output(dest='S'))
    return pdf_output

def por_facturar():
    """Esta Funcion Accede y Permite editar una tabla la cual calcula costos segun
    los productos listados en una cotizacion"""
    try:
        RUTA_PRODUCTOS = '_inventario_providencia.json'
    
        datos = get_folio_factura_descuento()
        
        DESCUENTO_PORCENTAJE = datos[0]
        FOLIO_FACTURA = datos[1]
        
        # Leo los datos de Productos, redondeo el precio de venta, creo la columna Producto Y Modelo
        # la asigno como el indice del DataFrame
        with open(RUTA_PRODUCTOS, 'r', encoding='utf-8') as file:
            df = pd.DataFrame(data=json.load(file))
            
            # Las opciones de busqueda seran Producto Y Modelo
            OPCIONES = df['Producto'].to_list()
            MEDIDAS = df['Unidad'].unique().tolist()
            #Creo un DataFrame vacio
            DF_VACIO = pd.DataFrame(
                {
                'Unidades':[None],
                'Medida':[None],
                'Producto':[None],
                'Total':[None],
                'Existencias':[None],
                'Claves':[None]
                }
            )

            # Inicializo contadores de items y costo total
            cotizacion_total = 0
            con_descuento = 0
            productos_en_cotizacion = 0

            # Asigno el DataFrame vacio y lo contadores al cache de streamlit
            if 'df_c' not in st.session_state:
                st.session_state.df_c = DF_VACIO
            if 'total'not in st.session_state:
                st.session_state.total = cotizacion_total
            if 'productos' not in st.session_state:
                st.session_state.productos = productos_en_cotizacion
            if 'total_desc' not in st.session_state:
                st.session_state.total_desc = con_descuento
            
            split1, split2 = st.columns([1,3])
            nombres = nombres_de_facturas()
            last = nombres[-1]
            ind = nombres.index(last)
            nombre_factura = split2.selectbox(label=f':red[{l.phrase[66]}]',options=nombres,accept_new_options=True,index=ind)
            if nombre_factura not in nombres:
                guarda_nombre = split2.button(label=l.phrase[67],key='guardar_nombre_nuevo_de_factura',width='stretch',type='primary')
                if guarda_nombre:
                    escribir_nuevo_nombre_factura(nombre_factura)
            
            split1.write(f'{l.phrase[22]}: :red[{FOLIO_FACTURA}]')
            # Creo un DataFrame editable con filas dinamicas, asigno la salida a "edicion"
            edicion = st.data_editor(
                data=st.session_state.df_c,
                key='df_edicion_cot_llave',
                num_rows='dynamic',
                column_order=['Unidades','Medida','Producto','Total','Existencias','Claves'],
                hide_index=True,
                column_config={
                    'Unidades':st.column_config.NumberColumn(disabled=False,width=90,help=':orange[Unidades]',step=0.01),
                    'Medida':st.column_config.SelectboxColumn(options=MEDIDAS,width=90,help=':orange[Como se mide el Producto]',default='Pieza'),
                    'Producto':st.column_config.SelectboxColumn(options=OPCIONES,width=300,help=':orange[Producto Y Modelo]'),
                    'Total':st.column_config.NumberColumn(disabled=False,width=90, format='dollar',help=':orange[Total]',step=0.01),
                    'Existencias':st.column_config.TextColumn(disabled=True, width=80,help=':orange[Existencias]'),
                    'Claves':st.column_config.TextColumn(disabled=True,width=80,help=':orange[Claves Unicas]')
                }
            )
            
            # Interaccion:
            split3,split4 = st.columns([1,3])
            split3.write(f'{l.phrase[63]}: :red[{DESCUENTO_PORCENTAJE}]')
            cambio_descuento = split4.number_input(
                width='stretch',
                label=f':red[{l.phrase[64]}]',
                min_value=0,
                max_value=100,
                value=DESCUENTO_PORCENTAJE,
                format="%d"
            )
            if cambio_descuento:
                cambio_descuento /= 100
                DESCUENTO_PORCENTAJE = cambio_descuento

            # Inicializo los widgets para los contadores en la UI
            metric1,metric2,metric3 = st.columns([1,1.5,1.5])
            metric1.metric(l.phrase[23],value=st.session_state.productos,border=True)
            metric2.metric(l.phrase[24],value=round(st.session_state.total,2),border=True)
            metric3.metric(l.phrase[62],value=round(st.session_state.total_desc,2),border=True)

            # La salida "edicion" la convierto a DataFrame
            edicion = pd.DataFrame(edicion)

            # Creo los botones calculo, limpiar tabla, e imprimir
            col1, col2, col3, col_mail= st.columns(4)
            with col1:
                calcular_total = st.button(label=l.phrase[25],width='stretch',key='calcular_total_cot')
            with col2:
                limpiar_tabla = st.button(label=l.phrase[26],width='stretch',key='limpiar_tabla_cot')
            with col3:
                imprimir = st.button(label=l.phrase[55], type='primary', width='stretch',key='imprimir_cot')
            with col_mail:
                send_email = st.button(
                    label=l.phrase[71],
                    key='enviar_por_email',
                    width='stretch',
                    type='primary'
                    )
            # Limpio el cache de streamlit para la situacion de limpiar una tabla.
            if edicion.empty:
                try:
                    st.session_state.df_c = DF_VACIO
                    st.session_state.total = cotizacion_total
                    st.session_state.productos = productos_en_cotizacion
                    st.session_state.total_desc = con_descuento
                except(KeyError):
                    if 'df_c' not in st.session_state:
                        st.session_state.df_c = DF_VACIO
                    if 'total' not in st.session_state:
                        st.session_state.total = cotizacion_total
                    if 'productos' not in st.session_state:
                        st.session_state.productos = productos_en_cotizacion
                    if 'total_desc' not in st.session_state:
                        st.session_state.total_desc = con_descuento
            # Limpio la tabla y los contadores, asi mismo re-asigno DataFrame vacio y contadores vacios
            # Para el caso de tener eliminados los caches en streamlit.
            if limpiar_tabla:
                try:
                    st.session_state.df_c = DF_VACIO
                    st.session_state.total = cotizacion_total
                    st.session_state.productos = productos_en_cotizacion
                    st.session_state.total_desc = con_descuento
                except(KeyError):
                    if 'df_c' not in st.session_state:
                        st.session_state.df_c = DF_VACIO
                    if 'total' not in st.session_state:
                        st.session_state.total = cotizacion_total
                    if 'productos' not in st.session_state:
                        st.session_state.productos = productos_en_cotizacion
                    if 'total_desc' not in st.session_state:
                        st.session_state.total_desc = con_descuento
            # Elimino filas vacias para Productos y Cantidades, elimino los duplicados de la tabla
            # manteniendo primeras apariciones. Si la tabla esta vacia, la reinicio en el cache.
            # Uno la salida "edicion" con "df" con sus indices correspondientes "Producto"
            if calcular_total or imprimir or send_email:
                if edicion['Medida'].isnull().any():
                    st.dataframe(edicion[edicion['Medida'].isnull()],hide_index=True)
                    st.info('No Se Ha Especificado El Tipo De Unidad Para La Columna :orange["Medida"].')
                    st.session_state.df_c = edicion
                    st.stop()

                edicion = edicion.dropna(axis=0,how='any',subset=['Unidades','Producto','Total'])
                if edicion.empty:
                    st.session_state.df_c = DF_VACIO
                else:
                    edicion['Producto'] = edicion['Producto'].apply(lambda x: x.strip().upper())
                    filtro = edicion['Producto'].tolist()
                    df = df[df['Producto'].isin(filtro)]
                    union = pd.merge(
                        df,
                        edicion,
                        how='left',
                        on='Producto'
                        )
                    # Hago el calculo de totales de la tabla y asigno totales a los contadores.
                    union['Existencias'] = union['Cantidad']
                    union['Claves'] = union['Clave']

                    union['redondeo'] = union['Unidades']
                    union['redondeo'] = union['redondeo'].apply(lambda x: math.floor(x))
                    productos_en_cotizacion += union['redondeo'].apply(lambda x: 1 if x == 0 else x).sum()
                    union = union.reindex(columns=['Unidades','Medida','Producto','Total','Existencias','Claves'])

                    cotizacion_total += union['Total'].sum()
                    
                    descuento_aplicado = cotizacion_total - (cotizacion_total * DESCUENTO_PORCENTAJE)
                    # Por ultimo se asignas al cache los nuevos datos para ser mostrados en la pantalla.
                    st.session_state.total_desc = descuento_aplicado
                    st.session_state.productos = productos_en_cotizacion
                    st.session_state.total = cotizacion_total
                    st.session_state.df_c = union
            
            if imprimir:
                # Funcion que genera un PDF, lo regresa en bytes.
                pdf_bytes = generar_factura_pdf(nombre_factura,FOLIO_FACTURA,DESCUENTO_PORCENTAJE)
                # Proporciona el botón de descarga de streamlit y le asigno el pdf temporal.
                st.download_button(
                    label=l.phrase[16],
                    type='primary',
                    data=pdf_bytes,
                    file_name=f"{l.phrase[68]}.pdf",
                    mime="application/pdf",
                    width='stretch'
                )
                # Mensaje de limpiar tabla
                st.info(l.phrase[26])
                # Aumentamos en 1 el contador de: Numero de Folio
                FOLIO_FACTURA += 1
                try:
                    if os.path.exists(RUTA_CONFIG) and os.path.getsize(RUTA_CONFIG) > 0:
                        with open(RUTA_CONFIG,'r',encoding='utf-8') as cambio_folio:
                            datos = json.load(cambio_folio)   
                            datos['configuracion']['folio factura'] = FOLIO_FACTURA
                        with open(RUTA_CONFIG,'w',encoding='utf-8') as escritura:
                            json.dump(datos,escritura,indent=4,ensure_ascii=False)
                    else:
                        st.warning(f'1. No se encuentra o se altero el archivo {RUTA_CONFIG}. Pedir ayuda con el soporte')
                except (FileNotFoundError,FileExistsError,json.JSONDecodeError):
                    st.warning(f'2. No se encuentra o se altero el archivo <{RUTA_CONFIG}> Pedir ayuda con el soporte')
                return
            
            if send_email:
                pdf_bytes_email = generar_factura_pdf(nombre_factura,FOLIO_FACTURA,DESCUENTO_PORCENTAJE)

                subject = l.phrase[68]
                port = 465 # SSL para gmail
                smtp_server = "smtp.gmail.com"
                remitente = st.secrets['email']['user']
                password = st.secrets['email']['password']
                destino = st.secrets['email']['destinatarios']
                body = 'Ferreteria La Providencia: Facturar'

                message = MIMEMultipart()
                message['From']=remitente
                message['To']=destino
                message['Subject']=subject
                message.attach(MIMEText(body,'plain'))

                part = MIMEBase("application", "pdf")
                part.set_payload(pdf_bytes_email)
                encoders.encode_base64(part)
                part.add_header(
                "Content-Disposition",
                f"attachment; filename= {l.phrase[68]}"
                )

                message.attach(part)
                
                text = message.as_string()

                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                    server.login(user=remitente,password=password)
                    server.sendmail(from_addr=remitente, to_addrs=destino, msg=text)

                st.success(l.phrase[70])
                FOLIO_FACTURA += 1
                try:
                    if os.path.exists(RUTA_CONFIG) and os.path.getsize(RUTA_CONFIG) > 0:
                        with open(RUTA_CONFIG,'r',encoding='utf-8') as cambio_folio:
                            datos = json.load(cambio_folio)   
                            datos['configuracion']['folio factura'] = FOLIO_FACTURA
                        with open(RUTA_CONFIG,'w',encoding='utf-8') as escritura:
                            json.dump(datos,escritura,indent=4,ensure_ascii=False)
                    else:
                        st.warning(f'1. No se encuentra o se altero el archivo {RUTA_CONFIG}. Pedir ayuda con el soporte')
                except (FileNotFoundError,FileExistsError,json.JSONDecodeError):
                    st.warning(f'2. No se encuentra o se altero el archivo <{RUTA_CONFIG}> Pedir ayuda con el soporte')
                return

    #Si hay problemas con la lectura se advierte la probable falta de datos.
    except (FileExistsError,json.JSONDecodeError,TypeError):
        st.warning(l.phrase[19])

#-------------------------------------------------------------------------------------------
# Accededo al modulo de idioma, con la configuracion elegida por el usuario
l=lenguaje.tu_idioma()

# Titulo y llamo a la funcion de cotizacion:
st.header(f':material/request_quote: {l.phrase[61]}')

por_facturar()
