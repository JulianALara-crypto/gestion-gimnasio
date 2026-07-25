import streamlit as st
import pandas as pd
import requests
import os
import urllib.parse
from datetime import datetime, timedelta
from PIL import Image

# ⚠️ PEGA TU URL DE GOOGLE ENTRE LAS COMILLAS AQUÍ ABAJO:
URL_API = "https://script.google.com/macros/s/AKfycbx8WbLwZfPztKvvWy-G5kjEu8gPWGajGl3t5APuRTL1c9gHVhS9O97gYK43VIiEqDpC/exec"

ruta_logo_gym = "logo_gym.png" 
icono_pestana = Image.open(ruta_logo_gym) if os.path.exists(ruta_logo_gym) else "🏋️‍♂️"

st.set_page_config(page_title="Gestor Gimnasio", page_icon=icono_pestana, layout="centered")

st.markdown("""
    <style>
        .stApp { background-color: #111111; }
        h1, h2, h3, h4 { color: #ffffff !important; text-align: center; }
        p, label, .stMarkdown { color: #dddddd !important; }
        div[data-testid="stDecoration"] { display: none; }
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

METODOS_PAGO = ["Efectivo", "Transferencia Bancaria", "Nequi", "DaviPlata", "Bre-B", "Tarjeta Crédito/Débito", "Otro"]

def cargar_datos():
    try:
        response = requests.get(URL_API)
        datos = response.json()
        if len(datos) <= 1:
            return pd.DataFrame(columns=["cedula", "nombre_completo", "eps", "whatsapp", "metodo_pago", "fecha_ingreso", "valor_pagado", "fecha_vencimiento"])
        # datos[0] contiene los nombres de las columnas ['cedula', 'nombre_completo', ...]
        # datos[1:] contiene las filas de los clientes registrados
        return pd.DataFrame(datos[1:], columns=datos[0])
    except Exception:
        return pd.DataFrame(columns=["cedula", "nombre_completo", "eps", "whatsapp", "metodo_pago", "fecha_ingreso", "valor_pagado", "fecha_vencimiento"])


df_clientes = cargar_datos()

if os.path.exists(ruta_logo_gym):
    col1, col2, col3 = st.columns(3)
    with col2: 
        st.image(Image.open(ruta_logo_gym), width=160)

st.title("SISTEMA DE GESTIÓN - POWER TRAINING GYM")

opcion = st.sidebar.radio("MENÚ DE OPERACIONES", [
    "🆕 Registrar Nuevo Cliente", 
    "🔄 Renovación de Membresía", 
    "🚨 Alertas de Vencimiento",
    "📊 Ver Base de Datos"
])

if opcion == "🆕 Registrar Nuevo Cliente":
    st.subheader("Formulario de Inscripción")
    with st.form("form_nuevo_cliente", clear_on_submit=True):
        cedula = st.text_input("Número de Cédula / ID:").strip()
        nombre = st.text_input("Nombre Completo y Apellidos:").strip()
        eps = st.text_input("Entidad de Salud (EPS):").strip()
        whatsapp = st.text_input("Número de WhatsApp (10 dígitos):").strip()
        metodo_pago = st.selectbox("Método de Pago:", METODOS_PAGO)
        fecha_ingreso = st.date_input("Fecha de Ingreso:", datetime.today())
        valor_pagado = st.number_input("Valor Pagado ($):", min_value=0, step=1000, value=0)
        
        btn_registrar = st.form_submit_button("Guardar Registro de Cliente")
        
        if btn_registrar:
            if not cedula or not nombre or not whatsapp:
                st.error("⚠️ Los campos Cédula, Nombre y WhatsApp son obligatorios.")
            elif not df_clientes.empty and "cedula" in df_clientes.columns and str(cedula) in df_clientes["cedula"].astype(str).values:
                st.error("❌ Esta cédula ya se encuentra registrada.")
            else:
                fecha_vencimiento = fecha_ingreso + timedelta(days=30)
                fila = [
                    str(cedula), str(nombre), str(eps) if eps else "NO REGISTRA",
                    str(whatsapp), str(metodo_pago), fecha_ingreso.strftime("%Y-%m-%d"),
                    str(int(valor_pagado)), fecha_vencimiento.strftime("%Y-%m-%d")
                ]
                try:
                    res = requests.post(URL_API, json={"action": "registrar", "row": fila})
                    st.success(f"🎉 ¡Cliente {nombre} registrado con éxito!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al conectar con la base de datos: {e}")

elif opcion == "🔄 Renovación de Membresía":
    st.subheader("Renovación de Clientes Antiguos")
    cedula_buscar = st.text_input("Buscar Cliente por Cédula / ID:").strip()
    
    if cedula_buscar and not df_clientes.empty and "cedula" in df_clientes.columns:
        df_clientes["cedula"] = df_clientes["cedula"].astype(str)
        registro_existente = df_clientes[df_clientes["cedula"] == str(cedula_buscar)]
        if not registro_existente.empty:
            cliente = registro_existente.iloc[0]
            st.info(f"👤 *Cliente Encontrado:* {cliente['nombre_completo']}")
            
            with st.form("form_renovacion"):
                st.text_input("Nombre Completo:", value=cliente['nombre_completo'], disabled=True)
                eps_act = st.text_input("Actualizar EPS:", value=cliente['eps'])
                whatsapp_act = st.text_input("Actualizar WhatsApp:", value=cliente['whatsapp'])
                st.markdown("---")
                
                index_metodo = METODOS_PAGO.index(cliente['metodo_pago']) if cliente['metodo_pago'] in METODOS_PAGO else 0
                metodo_pago_act = st.selectbox("Nuevo Método de Pago:", METODOS_PAGO, index=index_metodo)
                fecha_ingreso_act = st.date_input("Nueva Fecha de Pago:", datetime.today())
                
                try: val_defecto = int(float(cliente['valor_pagado']))
                except: val_defecto = 0
                    
                valor_pagado_act = st.number_input("Nuevo Valor Pagado ($):", min_value=0, step=1000, value=val_defecto)
                
                btn_renovar = st.form_submit_button("Procesar Renovación de Membresía")
                if btn_renovar:
                    fecha_vencimiento_act = fecha_ingreso_act + timedelta(days=30)
                    fila_actualizada = [
                        str(cedula_buscar), str(cliente['nombre_completo']), str(eps_act),
                        str(whatsapp_act), str(metodo_pago_act), fecha_ingreso_act.strftime("%Y-%m-%d"),
                        str(int(valor_pagado_act)), fecha_vencimiento_act.strftime("%Y-%m-%d")
                    ]
                    try:
                        requests.post(URL_API, json={"action": "actualizar", "cedula": cedula_buscar, "row": fila_actualizada})
                        st.success(f"🔄 ¡Membresía renovada correctamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al conectar con la base de datos: {e}")
        else:
            st.error("❌ La cédula ingresada no coincide con ningún cliente registrado.")

elif opcion == "🚨 Alertas de Vencimiento":
    st.subheader("Control y Alertas de Membresías")
    
    if not df_clientes.empty and "fecha_vencimiento" in df_clientes.columns:
        # Clonamos el dataframe para no dañar los datos originales
        df_alertas = df_clientes.copy()
        
        # Convertimos las fechas de texto a fechas reales de Python de forma segura
        df_alertas["fecha_vencimiento"] = pd.to_datetime(df_alertas["fecha_vencimiento"], errors="coerce").dt.date
        fecha_hoy = datetime.today().date()
        
        # Filtramos filas que tengan fechas válidas
        df_alertas = df_alertas.dropna(subset=["fecha_vencimiento"])
        
        # Calculamos cuántos días le quedan a cada cliente
        df_alertas["Dias_Restantes"] = df_alertas["fecha_vencimiento"].apply(lambda x: (x - fecha_hoy).days)
        
        # Clasificamos a los clientes en Vencidos o Próximos a Vencer (en menos de 5 días)
        df_vencidos = df_alertas[df_alertas["Dias_Restantes"] <= 5].sort_values(by="Dias_Restantes")
        
        if not df_vencidos.empty:
            st.warning(f"🚨 Se encontraron {len(df_vencidos)} clientes con membresía vencida o por vencer.")
            
            for index, fila in df_vencidos.iterrows():
                # Configuramos el estado visual según los días restantes
                if fila['Dias_Restantes'] < 0:
                    estado = f"🔴 VENCIDO hace {abs(fila['Dias_Restantes'])} días"
                elif fila['Dias_Restantes'] == 0:
                    estado = "🟡 VENCE HOY"
                else:
                    estado = f"🟢 Vence en {fila['Dias_Restantes']} días"
                
                # Armamos una tarjeta visual limpia para cada cliente
                with st.container():
                    col_info, col_accion = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"""
                        **👤 {fila['nombre_completo']}**  
                        * **Cédula / ID:** {fila['cedula']}  
                        * **Fecha de Vencimiento:** {fila['fecha_vencimiento'].strftime('%d/%m/%Y')}  
                        * **Estado:** {estado}
                        """)
                    
                    with col_accion:
                        # Limpiamos el número de WhatsApp quitando espacios
                        num_whatsapp = str(fila['whatsapp']).strip()
                        # Texto predefinido y automatizado para el cobro
                        mensaje_cobro = f"Hola {fila['nombre_completo']}, te saludamos de Power Training Gym. Te recordamos que tu membresía venció el {fila['fecha_vencimiento'].strftime('%d/%m/%Y')}. ¡Te esperamos para renovar!"
                        mensaje_codificado = urllib.parse.quote(mensaje_cobro)
                        url_whatsapp = f"https://wa.me{num_whatsapp}?text={mensaje_codificado}"
                        
                        # Botón que redirecciona directamente a la API web de WhatsApp
                        st.link_button("💬 Cobrar", url_whatsapp, use_container_width=True)
                    
                    st.markdown("---")
        else:
            st.success("🎉 ¡Excelente! No tienes clientes vencidos ni próximos a vencer en los siguientes 5 días.")
    else:
        st.info("La base de datos se encuentra vacía. No hay alertas que procesar.")


elif opcion == "📊 Ver Base de Datos":
    st.subheader("Registros en la Base de Datos")
    if not df_clientes.empty:
        st.dataframe(df_clientes)
    else:
        st.info("La base de datos se encuentra vacía o no se pudo leer.")
