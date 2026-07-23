import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import urllib.parse
from PIL import Image

ruta_logo_gym = "logo_gym.png" 

if os.path.exists(ruta_logo_gym):
    icono_pestana = Image.open(ruta_logo_gym)
else:
    icono_pestana = "🏋️‍♂️"

st.set_page_config(page_title="Gestor Gimnasio", page_icon=icono_pestana, layout="centered")

st.markdown("""
    <style>
        .stApp { background-color: #111111; }
        h1, h2, h3 { color: #ffffff; text-align: center; }
        p, label { color: #dddddd !important; }
        div[data-testid="stDecoration"] { display: none; }
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

DB_FILE = "clientes_gym.csv"
NUM_ADMIN_WHATSAPP = "573000000000" # <-- REEMPLAZAR AQUÍ CON EL WHATSAPP DEL ADMINISTRADOR

def cargar_datos():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["cedula", "nombre_completo", "eps", "whatsapp", "metodo_pago", "fecha_ingreso", "valor_pagado", "fecha_vencimiento"])
        df.to_csv(DB_FILE, sep="|", index=False, encoding="utf-8")
        return df
    return pd.read_csv(DB_FILE, sep="|", dtype={"cedula": str, "whatsapp": str}, encoding="utf-8", keep_default_na=False)

def guardar_datos(df):
    df.to_csv(DB_FILE, sep="|", index=False, encoding="utf-8")

df_clientes = cargar_datos()

if os.path.exists(ruta_logo_gym):
    col1, col2, col3 = st.columns(3)
    with col2: 
        st.image(Image.open(ruta_logo_gym), width=160)

st.title("🏋️‍♂️ SISTEMA DE GESTIÓN - GIMNASIO")

opcion = st.sidebar.radio("MENÚ DE OPERACIONES", ["🆕 Registrar Nuevo Cliente", "🔄 Renovación de Membresía", "🚨 Alertas de Vencimiento"])

if opcion == "🆕 Registrar Nuevo Cliente":
    st.subheader("Formulario de Inscripción")
    with st.form("form_nuevo_cliente", clear_on_submit=True):
        cedula = st.text_input("Número de Cédula / ID:").strip()
        nombre = st.text_input("Nombre Completo y Apellidos:").strip()
        eps = st.text_input("Entidad de Salud (EPS):").strip()
        whatsapp = st.text_input("Número de WhatsApp (Ej: 573xxxxxxxxx):").strip()
        metodo_pago = st.selectbox("Método de Pago:", ["Efectivo", "Transferencia Bancaria", "Tarjeta de Crédito/Débito", "Otro"])
        fecha_ingreso = st.date_input("Fecha de Ingreso:", datetime.today())
        valor_pagado = st.number_input("Valor Pagado ($):", min_value=0, step=1000, value=0)
        
        btn_registrar = st.form_submit_button("Guardar Registro de Cliente")
        
        if btn_registrar:
            if not cedula or not nombre or not whatsapp:
                st.error("⚠️ Los campos Cédula, Nombre y WhatsApp son obligatorios.")
            elif cedula in df_clientes["cedula"].values:
                st.error("❌ Esta cédula ya se encuentra registrada. Usa el módulo de 'Renovación de Membresía'.")
            else:
                fecha_vencimiento = fecha_ingreso + timedelta(days=30)
                nuevo_registro = {
                    "cedula": cedula,
                    "nombre_completo": nombre,
                    "eps": eps,
                    "whatsapp": whatsapp,
                    "metodo_pago": metodo_pago,
                    "fecha_ingreso": fecha_ingreso.strftime("%Y-%m-%d"),
                    "valor_pagado": int(valor_pagado),
                    "fecha_vencimiento": fecha_vencimiento.strftime("%Y-%m-%d")
                }
                df_clientes = pd.concat([df_clientes, pd.DataFrame([nuevo_registro])], ignore_index=True)
                guardar_datos(df_clientes)
                st.success(f"🎉 ¡Cliente {nombre} registrado con éxito! Vence el: {fecha_vencimiento.strftime('%Y-%m-%d')}")

elif opcion == "🔄 Renovación de Membresía":
    st.subheader("Renovación de Clientes Antiguos")
    cedula_buscar = st.text_input("Buscar Cliente por Cédula / ID:").strip()
    
    if cedula_buscar:
        registro_existente = df_clientes[df_clientes["cedula"] == cedula_buscar]
        if not registro_existente.empty:
            cliente = registro_existente.iloc[0]
            st.info(f"👤 **Cliente Encontrado:** {cliente['nombre_completo']}")
            
            with st.form("form_renovacion"):
                st.text_input("Nombre Completo:", value=cliente['nombre_completo'], disabled=True)
                eps_act = st.text_input("Actualizar EPS (Opcional):", value=cliente['eps'])
                whatsapp_act = st.text_input("Actualizar WhatsApp:", value=cliente['whatsapp'])
                st.markdown("---")
                st.markdown("### Datos del Nuevo Periodo de Pago")
                lista_metodos = ["Efectivo", "Transferencia Bancaria", "Tarjeta de Crédito/Débito", "Otro"]
                index_metodo = lista_metodos.index(cliente['metodo_pago']) if cliente['metodo_pago'] in lista_metodos else 0
                metodo_pago_act = st.selectbox("Nuevo Método de Pago:", lista_metodos, index=index_metodo)
                fecha_ingreso_act = st.date_input("Nueva Fecha de Pago / Ingreso:", datetime.today())
                valor_pagado_act = st.number_input("Nuevo Valor Pagado ($):", min_value=0, step=1000, value=int(cliente['valor_pagado']) if str(cliente['valor_pagado']).isdigit() else 0)
                
                btn_renovar = st.form_submit_button("Procesar Renovación de Membresía")
                if btn_renovar:
                    fecha_vencimiento_act = fecha_ingreso_act + timedelta(days=30)
                    df_clientes.loc[df_clientes["cedula"] == cedula_buscar, ["eps", "whatsapp", "metodo_pago", "fecha_ingreso", "valor_pagado", "fecha_vencimiento"]] = [
                        eps_act, whatsapp_act, metodo_pago_act, fecha_ingreso_act.strftime("%Y-%m-%d"), int(valor_pagado_act), fecha_vencimiento_act.strftime("%Y-%m-%d")
                    ]
                    guardar_datos(df_clientes)
                    st.success(f"🔄 ¡Membresía renovada correctamente! Nuevo vencimiento: {fecha_vencimiento_act.strftime('%Y-%m-%d')}")
        else:
            st.error("❌ El número de cédula ingresado no coincide con ningún cliente registrado.")

elif opcion == "🚨 Alertas de Vencimiento":
    st.subheader("Control de Mensualidades por Vencer o Vencidas")
    hoy = datetime.today().date()
    
    if not df_clientes.empty:
        df_calculo = df_clientes.copy()
        df_calculo["fecha_vencimiento_dt"] = pd.to_datetime(df_calculo["fecha_vencimiento"], errors='coerce').dt.date
        clientes_alerta = df_calculo[df_calculo["fecha_vencimiento_dt"] <= (hoy + timedelta(days=3))]
        
        if not clientes_alerta.empty:
            st.warning(f"Se encontraron {len(clientes_alerta)} mensualidades que requieren atención inmediata.")
            for idx, fila in clientes_alerta.iterrows():
                estado = "🔴 VENCIDO" if fila["fecha_vencimiento_dt"] < hoy else "🟡 POR VENCER"
                dias_restantes = (fila["fecha_vencimiento_dt"] - hoy).days
                
                with st.container():
                    st.markdown(f"""
                        <div style="border: 1px solid #444; padding: 15px; border-radius: 8px; background-color: #222222; margin-bottom: 10px;">
                            <h4 style="margin:0; color:#ffffff;">{fila['nombre_completo']} ({estado})</h4>
                            <p style="margin:5px 0 0 0; font-size:14px;"><b>Cédula:</b> {fila['cedula']} | <b>Vencimiento:</b> {fila['fecha_vencimiento']} ({dias_restantes} días)</p>
                            <p style="margin:2px 0 0 0; font-size:14px;"><b>WhatsApp Cliente:</b> {fila['whatsapp']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    msg_cliente = f"Hola {fila['nombre_completo']}, te saludamos de tu Gym. Te recordamos que tu mensualidad presenta un estado {estado} con fecha de corte el {fila['fecha_vencimiento']}. ¡Te esperamos para seguir entrenando juntos!"
                    msg_admin = f"ALERTA GYM: El cliente {fila['nombre_completo']} con Cédula {fila['cedula']} se encuentra {estado}. Su vencimiento fue el {fila['fecha_vencimiento']}. Tel: {fila['whatsapp']}"
                    
                    url_cliente = f"https://whatsapp.com{fila['whatsapp']}&text={urllib.parse.quote(msg_cliente)}"
                    url_admin = f"https://whatsapp.com{NUM_ADMIN_WHATSAPP}&text={urllib.parse.quote(msg_admin)}"
                    
                    col1, col2 = st.columns(2)
                    with col1: st.link_button("📲 Notificar al Cliente", url_cliente, use_container_width=True)
                    with col2: st.link_button("🛡️ Enviar Alerta al Admin", url_admin, use_container_width=True)
                    st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.success("🎉 ¡Excelente! No hay membresías vencidas ni próximas a vencer en los siguientes 3 días.")
    else: st.info("La base de datos se encuentra vacía actualmente.")
