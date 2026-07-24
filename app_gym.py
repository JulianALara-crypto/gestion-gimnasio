import streamlit as st
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
        .stApp { background-color: #111111; }
        h1, h2, h3, h4 { color: #ffffff !important; text-align: center; }
        p, label, .stMarkdown { color: #dddddd !important; }
        div[data-testid="stDecoration"] { display: none; }
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

DB_FILE = r"C:\Users\javila\gestion-gimnasio\clientes_gym.csv"

def cargar_datos():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame(columns=["cedula", "nombre_completo", "eps", "whatsapp", "metodo_pago", "fecha_ingreso", "valor_pagado", "fecha_vencimiento"])
    try:
        return pd.read_csv(DB_FILE, sep="|", dtype=str, encoding="utf-8", keep_default_na=False)
    except Exception:
        return pd.DataFrame(columns=["cedula", "nombre_completo", "eps", "whatsapp", "metodo_pago", "fecha_ingreso", "valor_pagado", "fecha_vencimiento"])

def guardar_datos(df):
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace(r'[\n\r\t]', ' ', regex=True).str.strip()
    df.to_csv(DB_FILE, sep="|", index=False, encoding="utf-8")

df_clientes = cargar_datos()

def convertir_a_csv(df):
    return df.to_csv(index=False, sep=";").encode('utf-8-sig')

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
        whatsapp = st.text_input("Número de WhatsApp (10 dígitos, ej: 312xxxxxxx):").strip()
        metodo_pago = st.selectbox("Método de Pago:", ["Efectivo", "Transferencia Bancaria", "Nequi", "DaviPlata", "Bre-B", "Otro"])
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
                    "cedula": str(cedula),
                    "nombre_completo": str(nombre),
                    "eps": str(eps) if eps else "NO REGISTRA",
                    "whatsapp": str(whatsapp),
                    "metodo_pago": str(metodo_pago),
                    "fecha_ingreso": fecha_ingreso.strftime("%Y-%m-%d"),
                    "valor_pagado": str(int(valor_pagado)),
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
            st.info(f"👤 *Cliente Encontrado:* {cliente['nombre_completo']}")
            
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
                
                # --- INDICATIVO AUTOMÁTICO 57 COLOMBIA ---
                num_celular = str(fila['whatsapp']).strip()
                if not num_celular.startswith("57"):
                    num_celular = "57" + num_celular
                
                texto_base = f"Hola {fila['nombre_completo']}, te saludamos de tu Gym. Te recordamos que tu mensualidad presenta un estado {estado} con fecha de corte el {fila['fecha_vencimiento']}. ¡Te esperamos para seguir entrenando juntos!"
                texto_codificado = urllib.parse.quote(texto_base)
                
                whatsapp_url = f"https://wa.me/{num_celular}?text={texto_codificado}"
                
                with st.container():
                    st.markdown(f"""
                        <div style="border: 1px solid #444; padding: 15px; border-radius: 8px; background-color: #222222; margin-bottom: 10px;">
                            <h4 style="margin:0; color:#ffffff; text-align:left;">{fila['nombre_completo']} ({estado})</h4>
                            <p style="margin:5px 0 0 0; font-size:14px; color:#ddd;"><b>Cédula:</b> {fila['cedula']} | <b>WhatsApp:</b> {fila['whatsapp']}</p>
                            <p style="margin:2px 0 0 0; font-size:14px; color:#ddd;"><b>Vence el:</b> {fila['fecha_vencimiento']} ({abs(dias_restantes)} días {'atrás' if dias_restantes < 0 else 'restantes'})</p>
                            <div style="margin-top: 10px; text-align: right;">
                                <a href="{whatsapp_url}" target="_blank" style="background-color: #25D366; color: white; padding: 6px 12px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 14px;">💬 Notificar por WhatsApp</a>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.success("✅ ¡Excelente! No hay clientes vencidos ni próximos a vencer en los siguientes 3 días.")
    else:
        st.info("📂 La base de datos se encuentra vacía actualmente.")

elif opcion == "📊 Ver Base de Datos / Descargar":
    st.subheader("Historial de Clientes Guardados")
    if not df_clientes.empty:
        st.write(f"Total de registros encontrados: {len(df_clientes)}")
        st.dataframe(df_clientes)
        csv_descarga = convertir_a_csv(df_clientes)
        st.download_button(
            label="📥 Descargar Base de Datos en CSV",
            data=csv_descarga,
            file_name="clientes_gym_web.csv",
            mime="text/csv",
        )
    else:
        st.info("📂 No hay datos registrados en la web en este momento.")
