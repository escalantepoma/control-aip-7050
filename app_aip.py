import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
from datetime import datetime, time, date, timedelta

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="Control AIP", layout="wide", initial_sidebar_state="expanded")

DATA_FILE = "asistencias_aip.csv"
DOCENTES_FILE = "docentes_registrados.csv"
CONFIG_FILE = "config.json"

# CLAVES DE ACCESO REESTRUCTURADAS
ADMIN_PASSWORD = "Aip7050*"
DOCENTE_PASSWORD = "Docente2026*"  # Clave general para que tus colegas ingresen a registrar

# ==========================================
# VARIABLES DE SESIÓN (MEMORIA)
# ==========================================
if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "mensaje_exito" not in st.session_state:
    st.session_state.mensaje_exito = False
if "rol_autenticado" not in st.session_state:
    st.session_state.rol_autenticado = "Público" # Roles: Público, Docente, Administrador

# ==========================================
# FUNCIONES: IDENTIDAD (CON AUTOCURACIÓN)
# ==========================================
def load_config():
    default_config = {"inst_name": "I.E. 7050 Nicanor Rivera Cáceres", "logo_path": None}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: 
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except:
            pass
    return default_config

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f: 
        json.dump(config, f, ensure_ascii=False)

# ==========================================
# FUNCIONES: ASISTENCIAS
# ==========================================
def load_data():
    columnas_estandar = ["Fecha", "Nivel", "Área", "Docente", "Grado", "Sección", "Alumnos", "Hora_Inicio", "Hora_Fin", "Actividad"]
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        
        if "Seccion" in df.columns and "Sección" in df.columns:
            df["Sección"] = df["Sección"].fillna(df["Seccion"])
            df = df.drop(columns=["Seccion"])
        elif "Seccion" in df.columns:
            df = df.rename(columns={"Seccion": "Sección"})
            
        if "Area" in df.columns and "Área" in df.columns:
            df["Área"] = df["Área"].fillna(df["Area"])
            df = df.drop(columns=["Area"])
        elif "Area" in df.columns:
            df = df.rename(columns={"Area": "Área"})
            
        df = df.loc[:, ~df.columns.duplicated()]
        
        for col in columnas_estandar:
            if col not in df.columns:
                df[col] = ""
                
        df['Fecha'] = df['Fecha'].astype(str)
        return df[columnas_estandar]
    else:
        df = pd.DataFrame(columns=columnas_estandar)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8")
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8")

def load_docentes():
    columnas_docentes = ["Nombre", "Nivel", "Área", "Grado_Asig", "Seccion_Asig"]
    if os.path.exists(DOCENTES_FILE):
        df = pd.read_csv(DOCENTES_FILE)
        if "Area" in df.columns:
            df = df.rename(columns={"Area": "Área"})
        if "Grado_Asig" not in df.columns:
            df["Grado_Asig"] = "Ninguno"
        if "Seccion_Asig" not in df.columns:
            df["Seccion_Asig"] = "Ninguna"
        df = df.sort_values(by="Nombre").reset_index(drop=True)
        return df[columnas_docentes]
    else:
        df = pd.DataFrame(columns=columnas_docentes)
        df.to_csv(DOCENTES_FILE, index=False, encoding="utf-8")
        return df

# --- AUXILIAR DE TIEMPO MATEMÁTICO ---
def calcular_horas_fila(row):
    try:
        fmt = "%H:%M"
        t_inicio = datetime.strptime(row["Hora_Inicio"], fmt)
        t_fin = datetime.strptime(row["Hora_Fin"], fmt)
        return ((t_fin - t_inicio).seconds / 60) / 60
    except:
        return 0.0

config = load_config()
df_asistencias = load_data()
df_docentes = load_docentes()

df_asistencias['Horas_Calculadas'] = df_asistencias.apply(calcular_horas_fila, axis=1)

# ==========================================
# BARRA LATERAL (CONTROL DE ACCESO SEGURO)
# ==========================================
with st.sidebar:
    if config.get("logo_path") and os.path.exists(config["logo_path"]):
        st.image(config["logo_path"], use_container_width=True)
        
    st.title(config.get("inst_name"))
    st.markdown("---")
    
    if st.session_state.rol_autenticado == "Público":
        st.markdown("<h3 style='font-size:15px; font-weight:bold; color:#1e293b;'>🔒 Intranet / Registro</h3>", unsafe_allow_html=True)
        input_clave = st.text_input("Ingrese la contraseña de acceso:", type="password", help="Use la clave de Docente o Administrador")
        
        if st.button("🔓 Ingresar", type="primary", use_container_width=True):
            if input_clave == DOCENTE_PASSWORD:
                st.session_state.rol_autenticado = "Docente"
                st.rerun()
            elif input_clave == ADMIN_PASSWORD:
                st.session_state.rol_autenticado = "Administrador"
                st.rerun()
            else:
                st.error("⚠️ Contraseña incorrecta.")
    else:
        st.success(f"🟢 Sesión: {st.session_state.rol_autenticado}")
        if st.button("🔒 Cerrar Sesión Personal", use_container_width=True):
            st.session_state.rol_autenticado = "Público"
            st.rerun()

# ==========================================
# ENTORNO PRIVADO: ADMINISTRADOR (AIP)
# ==========================================
if st.session_state.rol_autenticado == "Administrador":
    st.title("🛠️ Panel Superior - Gestión Coordinación AIP")
    
    tab_reportes, tab_docentes, tab_config, tab_eliminar = st.tabs(["Dashboard General", "Base de Datos Docente", "Identidad Institucional", "Control de Errores"])
    
    with tab_reportes:
        st.markdown("### 📊 Registro Completo de Auditoría e Historial de Visitas")
        if not df_asistencias.empty:
            df_asistencias['Grado y Sección'] = df_asistencias['Grado'].astype(str) + " - " + df_asistencias['Sección'].astype(str)
            
            with st.container(border=True):
                col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
                with col_f1:
                    lista_grados = sorted(df_asistencias['Grado'].dropna().unique().tolist())
                    admin_f_grado = st.selectbox("Filtrar por Grado:", ["Todos"] + lista_grados, key="admin_f_grado")
                with col_f2:
                    lista_secciones = sorted(df_asistencias['Sección'].dropna().unique().tolist())
                    admin_f_seccion = st.selectbox("Filtrar por Sección:", ["Todas"] + lista_secciones, key="admin_f_seccion")
                with col_f3:
                    admin_tipo_fecha = st.selectbox("Temporalidad de Reporte:", ["Todas las fechas (Histórico)", "Rango personalizado (Calendario)"], key="admin_tipo_fecha")
                    if admin_tipo_fecha == "Rango personalizado (Calendario)":
                        hoy_date = date.today()
                        inicio_ano = date(hoy_date.year, 1, 1)
                        admin_rango_fechas = st.date_input("Especifique Fecha Inicio y Fin:", value=(inicio_ano, hoy_date), key="admin_rango_fechas")
                    else:
                        admin_rango_fechas = None

            df_filtrado = df_asistencias.copy()
            df_filtrado['Fecha_Obj'] = pd.to_datetime(df_filtrado['Fecha']).dt.date
            
            if admin_f_grado != "Todos": df_filtrado = df_filtrado[df_filtrado['Grado'] == admin_f_grado]
            if admin_f_seccion != "Todas": df_filtrado = df_filtrado[df_filtrado['Sección'] == admin_f_seccion]
            if admin_rango_fechas and isinstance(admin_rango_fechas, tuple) and len(admin_rango_fechas) == 2:
                df_filtrado = df_filtrado[(df_filtrado['Fecha_Obj'] >= admin_rango_fechas[0]) & (df_filtrado['Fecha_Obj'] <= admin_rango_fechas[1])]

            if not df_filtrado.empty:
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("Sesiones Filtradas", len(df_filtrado))
                col_m2.metric("Horas de Uso", f"{df_filtrado['Horas_Calculadas'].sum():.1f} hrs")
                col_m3.metric("Días Asistidos Únicos", f"{df_filtrado['Fecha'].nunique()} días")
                col_m4.metric("Alumnos Atendidos", int(df_filtrado['Alumnos'].sum()))
                
                st.markdown("---")
                df_visual = df_filtrado.copy()
                def format_to_ampm(val_str):
                    try: return datetime.strptime(val_str, "%H:%M").strftime("%I:%M %p")
                    except: return val_str
                df_visual['Hora_Inicio'] = df_visual['Hora_Inicio'].apply(format_to_ampm)
                df_visual['Hora_Fin'] = df_visual['Hora_Fin'].apply(format_to_ampm)
                st.dataframe(df_visual.drop(columns=['Horas_Calculadas', 'Grado y Sección', 'Fecha_Obj'], errors='ignore'), use_container_width=True)
            else:
                st.warning("⚠️ No se encontraron registros con los filtros seleccionados.")
        else:
            st.info("No hay registros acumulados actualmente.")

    with tab_config:
        st.subheader("Configuración de la Institución")
        new_name = st.text_input("Nombre de la Institución", config.get("inst_name"))
        logo_file = st.file_uploader("Subir Logo de la Institución (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        
        if st.button("Guardar Configuración"):
            config["inst_name"] = new_name
            if logo_file:
                if not os.path.exists("assets"):
                    os.makedirs("assets")
                ruta_logo = f"assets/{logo_file.name}"
                with open(ruta_logo, "wb") as f:
                    f.write(logo_file.getbuffer())
                config["logo_path"] = ruta_logo
                
            save_config(config)
            st.success("✅ Configuración guardada correctamente.")
            st.rerun() 
            
    with tab_docentes:
        st.markdown("<h2 style='font-size:22px; font-weight:bold; margin-bottom:15px;'>👥 Registro de Personal</h2>", unsafe_allow_html=True)
        col_registro, col_baja = st.columns(2)
        
        with col_registro:
            st.markdown("<h3 style='font-size:16px; font-weight:bold; color:#1e293b; margin-bottom:8px;'>👤 Agregar Docente Manual</h3>", unsafe_allow_html=True)
            with st.container(border=True):
                nuevo_nombre = st.text_input("Apellidos y Nombres", placeholder="Ej: Escalante Poma, Henry", key="input_nuevo_nombre")
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    nuevo_nivel = st.selectbox("Nivel", ["Primaria", "Secundaria"], key="input_nuevo_nivel")
                with sub_col2:
                    nueva_area = st.text_input("Área Curricular", placeholder="Ej: Aula / Comunicación", key="input_nueva_area")
                
                st.markdown("**Asignación de Aula fija:**")
                col_asig1, col_asig2 = st.columns(2)
                with col_asig1:
                    asig_grado = st.selectbox("Grado Asignado", ["Ninguno", "1ro", "2do", "3ro", "4to", "5to", "6to"], key="asig_grado")
                with col_asig2:
                    asig_seccion = st.selectbox("Sección Asignada", ["Ninguna", "A", "B", "C", "D", "E", "F", "G", "H"], key="asig_seccion")

                if st.button("➕ Agregar Docente Manual", type="primary", use_container_width=True):
                    if nuevo_nombre.strip() == "":
                        st.error("⚠️ Ingrese los Apellidos y Nombres del docente.")
                    else:
                        nuevo_doc = pd.DataFrame([{
                            "Nombre": nuevo_nombre.strip(), "Nivel": nuevo_nivel, "Área": nueva_area.strip() if nueva_area.strip() else "Aula",
                            "Grado_Asig": asig_grado, "Seccion_Asig": asig_seccion
                        }])
                        df_docentes = pd.concat([df_docentes, nuevo_doc], ignore_index=True)
                        df_docentes.to_csv(DOCENTES_FILE, index=False, encoding="utf-8")
                        st.success(f"✅ ¡Docente registrado con éxito!")
                        st.rerun()

        with col_baja:
            st.markdown("<h3 style='font-size:16px; font-weight:bold; color:#1e293b; margin-bottom:8px;'>🚨 Bajas de Personal</h3>", unsafe_allow_html=True)
            with st.container(border=True):
                if not df_docentes.empty:
                    lista_docentes_eliminar = df_docentes['Nombre'].tolist()
                    docente_a_eliminar = st.selectbox("Docente a retirar:", ["-- Seleccionar docente --"] + lista_docentes_eliminar)
                    st.markdown("<div style='margin-top: 104px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️ Eliminar Docente Seleccionado", type="primary", use_container_width=True):
                        if docente_a_eliminar != "-- Seleccionar docente --":
                            df_docentes = df_docentes[df_docentes['Nombre'] != docente_a_eliminar].reset_index(drop=True)
                            df_docentes.to_csv(DOCENTES_FILE, index=False, encoding="utf-8")
                            st.success(f"💥 Docente removido.")
                            st.rerun()
                else:
                    st.info("No hay docentes registrados.")
                        
        st.markdown("---")
        st.markdown("### 📥 Carga Masiva mediante Excel")
        archivo_excel = st.file_uploader("Cargar Excel (.xlsx)", type=["xlsx"])
        if archivo_excel is not None:
            try:
                df_nuevos_docentes = pd.read_excel(archivo_excel)
                df_nuevos_docentes.columns = [c.replace("Area", "Área") for c in df_nuevos_docentes.columns]
                if "Grado_Asig" not in df_nuevos_docentes.columns: df_nuevos_docentes["Grado_Asig"] = "Ninguno"
                if "Seccion_Asig" not in df_nuevos_docentes.columns: df_nuevos_docentes["Seccion_Asig"] = "Ninguna"
                
                df_nuevos_docentes = df_nuevos_docentes[["Nombre", "Nivel", "Área", "Grado_Asig", "Seccion_Asig"]]
                df_nuevos_docentes.to_csv(DOCENTES_FILE, index=False, encoding="utf-8")
                st.success("✅ ¡Base de datos cargada!")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
                
        st.markdown("---")
        st.dataframe(df_docentes, use_container_width=True)

    with tab_eliminar:
        st.markdown("### 🗑️ Eliminar Registros Erróneos")
        if not df_asistencias.empty:
            lista_registros = [f"ID: {i} | {row['Fecha']} - {row['Docente']} - Aula: {row['Grado']} '{row['Sección']}'" for i, row in df_asistencias.iterrows()]
            registro_seleccionado = st.selectbox("Seleccione el registro que desea borrar:", ["-- Seleccionar registro --"] + lista_registros)
            if registro_seleccionado != "-- Seleccionar registro --":
                id_borrar = int(registro_seleccionado.split("|")[0].replace("ID:", "").strip())
                if st.button("🚨 Eliminar definitivamente", type="primary"):
                    df_asistencias = df_asistencias.drop(id_borrar).reset_index(drop=True)
                    save_data(df_asistencias)
                    st.success("✅ Registro borrado.")
                    st.rerun()
        else: st.info("No hay registros que eliminar.")

# ==========================================
# ENTORNO PRIVADO: VISTA DOCENTE (REGISTRO)
# ==========================================
elif st.session_state.rol_autenticado == "Docente":
    st.title("💻 Intranet de Docentes - Registro AIP")
    
    if st.session_state.mensaje_exito:
        st.success("✅ ¡Los datos de la asistencia se guardaron de manera exitosa!")
        st.balloons()
        st.session_state.mensaje_exito = False 
        
    if df_docentes.empty:
        st.warning("⚠️ El Admin aún no ha cargado la lista de docentes.")
    else:
        lista_nombres = df_docentes['Nombre'].tolist()
        k = st.session_state.form_key 
        
        opciones_grado_primaria = ["1ro", "2do", "3ro", "4to", "5to", "6to"]
        opciones_grado_secundaria = ["1ro", "2do", "3ro", "4to", "5to"]
        opciones_seccion = ["A", "B", "C", "D", "E", "F", "G", "H"]

        def actualizar_valores_docente():
            doc_sel = st.session_state[f"doc_sel_{k}"]
            if doc_sel != "🔍 Escriba para buscar docente...":
                datos_doc = df_docentes[df_docentes['Nombre'] == doc_sel].iloc[0]
                nivel_doc = datos_doc['Nivel'].strip().lower()
                g_raw = str(datos_doc.get('Grado_Asig', "Ninguno")).strip().lower()
                s_defecto = str(datos_doc.get('Seccion_Asig', "Ninguna")).strip().upper()
                
                op_grado = opciones_grado_primaria if nivel_doc == "primaria" else opciones_grado_secundaria
                grado_detectado = op_grado[0]
                for opcion in op_grado:
                    if len(g_raw) > 0 and (g_raw[0] in opcion or opcion in g_raw):
                        grado_detectado = opcion
                        break
                st.session_state[f"gr_f_{nivel_doc}_{k}"] = grado_detectado
                st.session_state[f"se_f_{k}"] = s_defecto if s_defecto in opciones_seccion else opciones_seccion[0]
                st.session_state[f"al_w_{k}"] = 0
                st.session_state[f"ac_w_{k}"] = ""

        docente_seleccionado = st.selectbox("Seleccione su Nombre y Apellido:", ["🔍 Escriba para buscar docente..."] + lista_nombres, key=f"doc_sel_{k}", on_change=actualizar_valores_docente)
        
        if docente_seleccionado != "🔍 Escriba para buscar docente...":
            datos_doc = df_docentes[df_docentes['Nombre'] == docente_seleccionado].iloc[0]
            nivel_doc = datos_doc['Nivel'].strip()
            area_doc = datos_doc['Área']
            
            st.info(f"👤 **Área:** {area_doc}  |  🏫 **Nivel:** {nivel_doc}")
            
            with st.container(border=True):
                st.markdown("### Formulario de Entrada de Sesión")
                col1, col2 = st.columns(2)
                opciones_grado = opciones_grado_primaria if nivel_doc.lower() == "primaria" else opciones_grado_secundaria
                
                key_g = f"gr_f_{nivel_doc.lower()}_{k}"
                if key_g not in st.session_state: st.session_state[key_g] = opciones_grado[0]
                if f"se_f_{k}" not in st.session_state: st.session_state[f"se_f_{k}"] = "A"
                if f"al_w_{k}" not in st.session_state: st.session_state[f"al_w_{k}"] = 0
                if f"ac_w_{k}" not in st.session_state: st.session_state[f"ac_w_{k}"] = ""

                with col1:
                    grado = st.selectbox("Grado que ingresa", opciones_grado, key=key_g)
                    alumnos = st.number_input("Cantidad de Alumnos", min_value=0, max_value=50, key=f"al_w_{k}")
                with col2:
                    seccion = st.selectbox("Sección", opciones_seccion, key=f"se_f_{k}")
                    fecha = st.date_input("Fecha de la Sesión:", value=datetime.today(), key=f"fe_w_{k}")
                    
                    # Traductor de Fecha en Español
                    meses_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                    dias_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                    st.markdown(f"📅 **Día Elegido:** {dias_es[fecha.weekday()]} {fecha.day} de {meses_es[fecha.month - 1]} del {fecha.year}")

                st.markdown("🕒 **Horario Real de la Sesión (Escriba o elija la hora exacta minuto a minuto)**")
                col3, col4 = st.columns(2)
                with col3: 
                    # AGREGADO: step=60 obliga a Streamlit a mostrar e incrementar el menú minuto a minuto
                    sel_hora_inicio = st.time_input("Hora de Ingreso Exacta:", value=time(8, 0), step=60, key=f"hi_exacta_{k}")
                with col4: 
                    sel_hora_fin = st.time_input("Hora de Salida Exacta:", value=time(9, 30), step=60, key=f"hf_exacta_{k}")
                
                actividad = st.text_area("Tema o Actividad a desarrollar", placeholder="Ej: Programación en Scratch...", key=f"ac_w_{k}")
                
                if st.button("💾 Guardar y Registrar Sesión", type="primary", use_container_width=True):
                    str_hora_inicio = sel_hora_inicio.strftime("%H:%M")
                    str_hora_fin = sel_hora_fin.strftime("%H:%M")
                    
                    if sel_hora_fin <= sel_hora_inicio: st.error("⚠️ La hora de salida debe ser posterior a la hora de ingreso.")
                    elif alumnos == 0: st.error("⚠️ Especifique el número real de alumnos.")
                    else:
                        nuevo_registro = {
                            "Fecha": str(fecha), "Nivel": nivel_doc, "Área": area_doc, "Docente": docente_seleccionado,
                            "Grado": grado, "Sección": seccion, "Alumnos": int(alumnos), "Hora_Inicio": str_hora_inicio,
                            "Hora_Fin": str_hora_fin, "Actividad": actividad
                        }
                        df_asistencias = pd.concat([df_asistencias, pd.DataFrame([nuevo_registro])], ignore_index=True)
                        save_data(df_asistencias.drop(columns=['Horas_Calculadas'], errors='ignore'))
                        st.session_state.mensaje_exito = True
                        st.session_state.form_key += 1
                        st.rerun()

# ==========================================
# ENTORNO PÚBLICO: PÁGINA WEB PRINCIPAL (HOME)
# ==========================================
else:
    st.markdown(f"<h1 style='text-align: center; color: #0f172a;'>📊 Dashboard de Innovación Pedagógica (AIP)</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 18px; color: #475569;'>Monitoreo en tiempo real del uso del Laboratorio Tecnológico de la {config.get('inst_name')}</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not df_asistencias.empty:
        df_asistencias['Grado y Sección'] = df_asistencias['Grado'].astype(str) + " - " + df_asistencias['Sección'].astype(str)
        
        with st.container(border=True):
            st.markdown("🔍 **Filtros de Búsqueda para la Comunidad Educativa**")
            col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
            with col_f1:
                lista_grados = sorted(df_asistencias['Grado'].dropna().unique().tolist())
                pub_f_grado = st.selectbox("Seleccionar Grado:", ["Todos"] + lista_grados, key="pub_grado")
            with col_f2:
                lista_secciones = sorted(df_asistencias['Sección'].dropna().unique().tolist())
                pub_f_seccion = st.selectbox("Seleccionar Sección:", ["Todas"] + lista_secciones, key="pub_seccion")
            with col_f3:
                pub_tipo_fecha = st.selectbox("Rango Temporal:", ["Histórico Completo", "Rango de Calendario"], key="pub_tipo_f")
                if pub_tipo_fecha == "Rango de Calendario":
                    hoy_date = date.today()
                    inicio_ano = date(hoy_date.year, 1, 1)
                    pub_rango_fechas = st.date_input("Especifique las Fechas:", value=(inicio_ano, hoy_date), key="pub_fechas")
                else:
                    pub_rango_fechas = None

        df_pub_filtrado = df_asistencias.copy()
        df_pub_filtrado['Fecha_Obj'] = pd.to_datetime(df_pub_filtrado['Fecha']).dt.date
        
        if pub_f_grado != "Todos": df_pub_filtrado = df_pub_filtrado[df_pub_filtrado['Grado'] == pub_f_grado]
        if pub_f_seccion != "Todas": df_pub_filtrado = df_pub_filtrado[df_pub_filtrado['Sección'] == pub_f_seccion]
        if pub_rango_fechas and isinstance(pub_rango_fechas, tuple) and len(pub_rango_fechas) == 2:
            df_pub_filtrado = df_pub_filtrado[(df_pub_filtrado['Fecha_Obj'] >= pub_rango_fechas[0]) & (df_pub_filtrado['Fecha_Obj'] <= pub_rango_fechas[1])]

        if not df_pub_filtrado.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("📌 Clases Dictadas", len(df_pub_filtrado))
            m_col2.metric("⏱️ Horas de Laboratorio", f"{df_pub_filtrado['Horas_Calculadas'].sum():.1f} hrs")
            m_col3.metric("📅 Días de Actividad", f"{df_pub_filtrado['Fecha'].nunique()} días")
            m_col4.metric("👥 Estudiantes Atendidos", int(df_pub_filtrado['Alumnos'].sum()))
            
            st.markdown("---")
            
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.markdown("<h3 style='font-size:18px; font-weight:bold; color:#1e293b;'>📈 Consumo de Horas Pedagógicas por Aula</h3>", unsafe_allow_html=True)
                df_horas_aula = df_pub_filtrado.groupby('Grado y Sección')['Horas_Calculadas'].sum().reset_index().sort_values(by='Horas_Calculadas', ascending=False)
                fig_barras = px.bar(df_horas_aula, x='Grado y Sección', y='Horas_Calculadas', text_auto='.1f', color='Horas_Calculadas', color_continuous_scale=px.colors.sequential.Plotly3)
                fig_barras.update_layout(xaxis_title="Aula (Grado y Sección)", yaxis_title="Total Horas")
                st.plotly_chart(fig_barras, use_container_width=True)
            with g_col2:
                st.markdown("<h3 style='font-size:18px; font-weight:bold; color:#1e293b;'>🥧 Porcentaje de Visitas al Laboratorio</h3>", unsafe_allow_html=True)
                fig_pie = px.pie(df_pub_filtrado, names='Grado y Sección', hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("🔍 No se encontraron registros para los filtros seleccionados.")
    else:
        st.info("👋 ¡Bienvenidos! Actualmente no hay sesiones registradas en este periodo escolar.")