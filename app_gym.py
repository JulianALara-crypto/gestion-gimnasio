import os
from datetime import datetime, timedelta
import pandas as pd

# 1. USAMOS LA RUTA EXACTA DE TU CARPETA DE WINDOWS
ruta_app = r"C:\Users\javila\gestion-gimnasio\app_gym.py"

def generar_codigo_nube():
    return f'''import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os
from datetime import datetime, timedelta
from PIL import Image
import urllib.parse

ruta_logo_gym = "logo_gym.png" 
icono_pestana = Image.open(ruta_logo_gym) if os.path.exists(ruta_logo_gym) else "🏋️‍♂️"

st.set_page_config(page_title="Gestor Gimnasio", page_icon=icono_pestana, layout="centered")

st.markdown("""
    <style>
        .stApp {{ background-color: #111111; }}
        h1, h2, h3, h4 {{ color: #ffffff !important; text-align: center; }}
        p, label, .stMarkdown {{ color: #dddddd !important; }}
        div[data-testid="stDecoration"] {{ display: none; }}
        .block-container {{ padding-top: 2rem; }}
    </style>
""", unsafe_allow_html=True)

METODOS_PAGO = ["Efectivo", "Transferencia Bancaria", "Nequi", "DaviPlata", "Bre-B", "Tarjeta Crédito/Débito", "Otro"]

conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        return conn.read(ttl=0, dtype=str).fillna("")
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
    "📊 Ver Base de Datos / Descargar"
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
            elif not df_clientes.empty and cedula in df_clientes["cedula"].values:
                st.error("❌ Esta cédula ya se encuentra registrada. Usa el módulo de 'Renovación de Membresía'.")
            else:
                fecha_vencimiento = fecha_ingreso + timedelta(days=30)
                nuevo_registro = pd.DataFrame([{{
                    "cedula": str(cedula),
                    "nombre_completo": str(nombre),
                    "eps": str(eps) if eps else "NO REGISTRA",
                    "whatsapp": str(whatsapp),
                    "metodo_pago": str(metodo_pago),
                    "fecha_ingreso": fecha_ingreso.strftime("%Y-%m-%d"),
                    "valor_pagado": str(int(valor_pagado)),
                    "fecha_vencimiento": fecha_vencimiento.strftime("%Y-%m-%d")
                }}])
                
                df_actualizado = pd.concat([df_clientes, nuevo_registro], ignore_index=True)
                conn.update(data=df_actualizado)
                st.success(f"🎉 ¡Cliente {{nombre}} registrado con éxito! Guardado en la nube.")
                st.rerun()

elif opcion == "🔄 Renovación de Membresía":
    st.subheader("Renovación de Clientes Antiguos")
    cedula_buscar = st.text_input("Buscar Cliente por Cédula / ID:").strip()
    
    if cedula_buscar and not df_clientes.empty:
        registro_existente = df_clientes[df_clientes["cedula"] == cedula_buscar]
        if not registro_existente.empty:
            cliente = registro_existente.iloc[0]
            st.info(f"👤 *Cliente Encontrado:* {{cliente['nombre_completo']}}")
            
            with st.form("form_renovacion"):
                st.text_input("Nombre Completo:", value=cliente['nombre_completo'], disabled=True)
                eps_act = st.text_input("Actualizar EPS:", value=cliente['eps'])
                whatsapp_act = st.text_input("Actualizar WhatsApp:", value=cliente['whatsapp'])
                st.markdown("---")
                
                index_metodo = METODOS_PAGO.index(cliente['metodo_pago']) if cliente['metodo_pago'] in METODOS_PAGO else 0
                metodo_pago_act = st.selectbox("Nuevo Método de Pago:", METODOS_PAGO, index=index_metodo)
                fecha_ingreso_act = st.date_input("Nueva Fecha de Pago:", datetime.today())
                
                try:
                    val_defecto = int(float(cliente['valor_pagado']))
                except Exception:
                    val_defecto = 0
                    
                valor_pagado_act = st.number_input("Nuevo Valor Pagado ($):", min_value=0, step=1000, value=val_defecto)
                
                btn_renovar = st.form_submit_button("Procesar Renovación de Membresía")
                if btn_renovar:
                    fecha_vencimiento_act = fecha_ingreso_act + timedelta(days=30)
                    
                    df_clientes.loc[df_clientes["cedula"] == cedula_buscar, ["eps", "whatsapp", "metodo_pago", "fecha_ingreso", "valor_pagado", "fecha_vencimiento"]] = [
                        str(eps_act), str(whatsapp_act), str(metodo_pago_act), fecha_ingreso_act.strftime("%Y-%m-%d"), str(int(valor_pagado_act)), fecha_vencimiento_act.strftime("%Y-%m-%d")
                    ]
                    conn.update(data=df_clientes)
                    st.success(f"🔄 ¡Membresía renovada correctamente en la nube!")
                    st.rerun()
        else:
            st.error("❌ La cédula ingresada no coincide con ningún cliente registrado.")

elif opcion == "🚨 Alertas de Vencimiento":
    st.subheader("Control de Vencimientos")
  L  st.info("Módulo de alertas activo.")
'''

# 2. ESCRITURA DEL ARCHIVO FORZANDO LA RUTA
with open(ruta_app, "w", encoding="utf-8") as f:
    f.write(generar_codigo_nube())

print(f"🚀 Archivo actualizado exitosamente en: {ruta_app}")
