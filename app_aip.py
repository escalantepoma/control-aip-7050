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

# CLAVE DE ACCESO DEL ADMINISTRADOR (Modifícala aquí si deseas otra)
ADMIN_PASSWORD = "Aip7050*"

# ==========================================
# VARIABLES DE SESIÓN (MEMORIA)
# ==========================================
if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "mensaje_exito" not in st.session_state:
    st.session_state.mensaje_exito = False
if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = False

# ==========================================
# FUNCIONES: IDENTIDAD (CON AUTOCURACIÓN)
# ==========================================
def load_config():
    default_config = {"inst_name": "I.E. 7050 Nicanor Rivera / 3022 Sabogal", "logo_path": None}
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
    if os.path.exists(DOCENTES_FILE):
        df = pd.read_csv(DOCENTES_FILE)
        if "Area" in df.columns:
            df = df.rename(columns={"Area": "Área"})
        df = df.sort_values(by="Nombre").reset_index(drop=True)
        return df
    else:
        return pd.DataFrame(columns=["Nombre", "Nivel", "Área"])

# --- AUXILIARES DE TIEMPO ---
def generar_opciones_horas():
    horas_ampm = []
    for h in range(7, 12):
        for m in [0, 15, 30, 45]:
            horas_ampm.append(f"{h:02d}:{m:02d} AM")
    for m in [0, 15, 30, 45]:
        horas_ampm.append(f"12:{m:02d} PM")
    for h in range(1, 9):
        for m in [0, 15, 30, 45]:
            horas_ampm.append(f"{h:02d}:{m:02d} PM")
    return horas_ampm

def convertir_to_24h(hora_str):
    try:
        in_time = datetime.strptime(hora_str.strip(), "%I:%M %p")
        return in_time.strftime("%H:%M")
    except:
        return "00:00"

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
lista_horas_ampm = generar_opciones_horas()

# Añadir columna de horas calculadas al DataFrame general para reportes reactivos
df_asistencias['Horas_Calculadas'] = df_asistencias.apply(calcular_horas_fila, axis=1)

# ==========================================
# BARRA LATERAL (ROLES E IDENTIDAD)
# ==========================================
with st.sidebar:
    if config.get("logo_path") and os.path.exists(config["logo_path"]):
        st.image(config["logo_path"], use_container_width=True)
        
    st.title(config.get("inst_name"))
    st.markdown("---")
    
    # Si cambia de rol, reseteamos la autenticación de administrador por seguridad
    rol = st.sidebar.radio("Seleccione su Rol", ["Docente", "Administrador (AIP)"])
    if rol == "Docente":
        st.session_state.admin_autenticado = False

# ==========================================
# VISTA: ADMINISTRADOR (AIP) CON FILTRO DE SEGURIDAD
# ==========================================
if rol == "Administrador (AIP)":
    st.title("🛠️ Control y Monitoreo del Laboratorio AIP")
    
    # CONTROL DE ACCESO
    if not st.session_state.admin_autenticado:
        st.markdown("<h3 style='font-size:16px; font-weight:bold; color:#1e293b;'>🔒 Autenticación Requerida</h3>", unsafe_allow_html=True)
        with st.container(border=True):
            input_pass = st.text_input("Ingrese la clave de acceso de la Coordinación AIP:", type="password")
            if st.button("🔑 Ingresar al Panel", type="primary", use_container_width=True):
                if input_pass == ADMIN_PASSWORD:
                    st.session_state.admin_autenticado = True
                    st.success("Acceso concedido.")
                    st.rerun()
                else:
                    st.error("❌ Clave incorrecta. Inténtelo nuevamente.")
    else:
        # BOTÓN PARA CERRAR SESIÓN DEL ADMINISTRADOR
        if st.sidebar.button("🔒 Cerrar Sesión Administrador"):
            st.session_state.admin_autenticado = False
            st.rerun()

        tab_config, tab_dashboard, tab_docentes = st.tabs(["Identidad", "Dashboard y Reportes", "Gestión de Docentes"])
        
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
            st.markdown("<h2 style='font-size:22px; font-weight:bold; margin-bottom:15px;'>👥 Registro y Control de la Base de Datos Docente</h2>", unsafe_allow_html=True)
            col_registro, col_baja = st.columns(2)
            
            with col_registro:
                st.markdown("<h3 style='font-size:16px; font-weight:bold; color:#1e293b; margin-bottom:8px;'>👤 Agregar Docente Manual</h3>", unsafe_allow_html=True)
                with st.container(border=True):
                    nuevo_nombre = st.text_input("Apellidos y Nombres", placeholder="Ej: Escalante Poma, Henry", key="input_nuevo_nombre")
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1:
                        nuevo_nivel = st.selectbox("Nivel", ["Primaria", "Secundaria"], key="input_nuevo_nivel")
                    with sub_col2:
                        nueva_area = st.text_input("Área Curricular", placeholder="Ej: Matemática", key="input_nueva_area")
                    
                    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                    if st.button("➕ Agregar Docente Manual", type="primary", use_container_width=True):
                        if nuevo_nombre.strip() == "" or nueva_area.strip() == "":
                            st.error("⚠️ Ingrese Nombre y Área Curricular.")
                        else:
                            if not df_docentes.empty and nuevo_nombre.strip().lower() in df_docentes['Nombre'].str.strip().str.lower().values:
                                st.warning(f"💡 El docente ya se encuentra registrado.")
                            else:
                                nuevo_doc = pd.DataFrame([{"Nombre": nuevo_nombre.strip(), "Nivel": nuevo_nivel, "Área": nueva_area.strip()}])
                                df_docentes = pd.concat([df_docentes, nuevo_doc], ignore_index=True)
                                df_docentes.to_csv(DOCENTES_FILE, index=False, encoding="utf-8")
                                st.success(f"✅ ¡Docente registrado con éxito!")
                                st.rerun()

            with col_baja:
                st.markdown("<h3 style='font-size:16px; font-weight:bold; color:#1e293b; margin-bottom:8px;'>🚨 Depuración (Cambio de Año / Bajas)</h3>", unsafe_allow_html=True)
                with st.container(border=True):
                    st.write("Remueva del sistema al personal que ya no laborará en la institución:")
                    if not df_docentes.empty:
                        lista_docentes_eliminar = df_docentes['Nombre'].tolist()
                        docente_a_eliminar = st.selectbox("Docente a retirar:", ["-- Seleccionar docente --"] + lista_docentes_eliminar, key="select_docente_eliminar")
                        st.markdown("<div style='margin-top: 48px;'></div>", unsafe_allow_html=True)
                        if st.button("🗑️ Eliminar Docente Seleccionado", type="primary", use_container_width=True):
                            if docente_a_eliminar != "-- Seleccionar docente --":
                                df_docentes = df_docentes[df_docentes['Nombre'] != docente_a_eliminar].reset_index(drop=True)
                                df_docentes.to_csv(DOCENTES_FILE, index=False, encoding="utf-8")
                                st.success(f"💥 Docente removido de la base de datos.")
                                st.rerun()
                            else:
                                st.error("⚠️ Por favor, elija un docente válido.")
                    else:
                        st.info("No hay docentes registrados en la base de datos actualmente.")
                            
            st.markdown("---")
            st.markdown("<h3 style='font-size:16px; font-weight:bold; color:#1e293b; margin-bottom:8px;'>📥 Carga Masiva mediante Archivo Excel</h3>", unsafe_allow_html=True)
            archivo_excel = st.file_uploader("Cargar Excel (.xlsx)", type=["xlsx"], key="excel_uploader", label_visibility="collapsed")
            
            if archivo_excel is not None:
                try:
                    df_nuevos_docentes = pd.read_excel(archivo_excel)
                    df_nuevos_docentes.columns = [c.replace("Area", "Área") for c in df_nuevos_docentes.columns]
                    if all(col in df_nuevos_docentes.columns for col in ["Nombre", "Nivel", "Área"]):
                        df_nuevos_docentes.to_csv(DOCENTES_FILE, index=False, encoding="utf-8")
                        st.success("✅ ¡Base de datos de docentes actualizada con éxito!")
                        st.rerun() 
                    else:
                        st.error("El Excel debe contener las columnas de encabezado exactas: Nombre, Nivel, Área")
                except Exception as e:
                    st.error(f"Error al procesar el Excel: {e}")
                    
            st.markdown("---")
            st.markdown("<h3 style='font-size:16px; font-weight:bold; color:#1e293b; margin-bottom:8px;'>📋 Listado Actual de Personal Registrado</h3>", unsafe_allow_html=True)
            st.dataframe(df_docentes, use_container_width=True)

        with tab_dashboard:
            st.subheader("Estadísticas del Laboratorio")
            if not df_asistencias.empty:
                df_asistencias['Grado y Sección'] = df_asistencias['Grado'].astype(str) + " - " + df_asistencias['Sección'].astype(str)
                
                st.markdown("<h3 style='font-size:16px; font-weight:bold; color:#1e293b; margin-bottom:2px;'>🔍 Panel de Filtros de Auditoría</h3>", unsafe_allow_html=True)
                with st.container(border=True):
                    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
                    with col_f1:
                        lista_grados = sorted(df_asistencias['Grado'].dropna().unique().tolist())
                        f_grado = st.selectbox("Filtrar por Grado:", ["Todos"] + lista_grados)
                    with col_f2:
                        lista_secciones = sorted(df_asistencias['Sección'].dropna().unique().tolist())
                        f_seccion = st.selectbox("Filtrar por Sección:", ["Todas"] + lista_secciones)
                    with col_f3:
                        tipo_fecha = st.selectbox("Temporalidad de Reporte:", ["Todas las fechas (Histórico)", "Rango personalizado (Calendario)"])
                        if tipo_fecha == "Rango personalizado (Calendario)":
                            hoy_date = date.today()
                            inicio_ano = date(hoy_date.year, 1, 1)
                            rango_fechas = st.date_input("Especifique Fecha Inicio y Fin:", value=(inicio_ano, hoy_date))
                        else:
                            rango_fechas = None

                df_filtrado = df_asistencias.copy()
                df_filtrado['Fecha_Obj'] = pd.to_datetime(df_filtrado['Fecha']).dt.date
                
                if f_grado != "Todos":
                    df_filtrado = df_filtrado[df_filtrado['Grado'] == f_grado]
                if f_seccion != "Todas":
                    df_filtrado = df_filtrado[df_filtrado['Sección'] == f_seccion]
                    
                if rango_fechas and isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
                    f_inicio, f_fin = rango_fechas
                    df_filtrado = df_filtrado[(df_filtrado['Fecha_Obj'] >= f_inicio) & (df_filtrado['Fecha_Obj'] <= f_fin)]

                st.markdown("#### Métricas del Periodo Seleccionado")
                if not df_filtrado.empty:
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    total_horas_f = df_filtrado['Horas_Calculadas'].sum()
                    total_dias_f = df_filtrado['Fecha'].nunique()
                    
                    col_m1.metric("Sesiones Filtradas", len(df_filtrado))
                    col_m2.metric("Horas de Uso", f"{total_horas_f:.1f} hrs")
                    col_m3.metric("Días Asistidos Únicos", f"{total_dias_f} días")
                    col_m4.metric("Alumnos Atendidos", int(df_filtrado['Alumnos'].sum()))
                    
                    st.markdown("---")
                    col_graf1, col_graf2 = st.columns(2)
                    with col_graf1:
                        st.markdown("### 📊 Total Horas de Uso por Aula")
                        df_horas_aula = df_filtrado.groupby('Grado y Sección')['Horas_Calculadas'].sum().reset_index()
                        df_horas_aula = df_horas_aula.sort_values(by='Horas_Calculadas', ascending=False)
                        fig_barras = px.bar(df_horas_aula, x='Grado y Sección', y='Horas_Calculadas', title="Horas Pedagógicas Consumidas", text_auto='.1f', color='Horas_Calculadas', color_continuous_scale=px.colors.sequential.Viridis)
                        st.plotly_chart(fig_barras, use_container_width=True)
                    with col_graf2:
                        st.markdown("### 🥧 Distribución Porcentual (Sesiones)")
                        fig_pie = px.pie(df_filtrado, names='Grado y Sección', title="Frecuencia de Visitas", hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    st.markdown("### 🗂️ Base de Datos Completa (Filtrada)")
                    df_visual = df_filtrado.copy()
                    def format_to_ampm(val_str):
                        try: return datetime.strptime(val_str, "%H:%M").strftime("%I:%M %p")
                        except: return val_str
                    df_visual['Hora_Inicio'] = df_visual['Hora_Inicio'].apply(format_to_ampm)
                    df_visual['Hora_Fin'] = df_visual['Hora_Fin'].apply(format_to_ampm)
                    st.dataframe(df_visual.drop(columns=['Horas_Calculadas', 'Grado y Sección', 'Fecha_Obj'], errors='ignore'), use_container_width=True)
                else:
                    st.warning("⚠️ No se encontraron registros de asistencias con los filtros seleccionados.")

                # --- MÓDULO DE BORRADO ---
                st.markdown("---")
                st.markdown("### 🗑️ Gestión de Errores (Eliminar Registros)")
                lista_registros = []
                for i, row in df_asistencias.iterrows():
                    lista_registros.append(f"ID: {i} | {row['Fecha']} - {row['Docente']} - Aula: {row['Grado']} '{row['Sección']}'")
                registro_seleccionado = st.selectbox("Seleccione el registro que desea eliminar:", ["-- Seleccionar registro --"] + lista_registros)
                if registro_seleccionado != "-- Seleccionar registro --":
                    id_borrar = int(registro_seleccionado.split("|")[0].replace("ID:", "").strip())
                    if st.button("🚨 Eliminar este registro definitivamente", type="primary"):
                        df_asistencias = df_asistencias.drop(id_borrar).reset_index(drop=True)
                        save_data(df_asistencias.drop(columns=['Horas_Calculadas', 'Grado y Sección'], errors='ignore'))
                        st.success("✅ Registro eliminado correctamente.")
                        st.rerun()
            else:
                st.info("Aún no hay registros de asistencia en este periodo.")

# ==========================================
# VISTA: DOCENTE CON HISTORIAL PERSONAL INTEGRADO
# ==========================================
elif rol == "Docente":
    st.title("💻 Registro de Uso del AIP")
    
    if st.session_state.mensaje_exito:
        st.success("✅ ¡Los datos de la asistencia se guardaron de manera exitosa!")
        st.balloons()
        st.session_state.mensaje_exito = False 
    
    if df_docentes.empty:
        st.warning("⚠️ El Administrador aún no ha cargado la lista de docentes.")
    else:
        lista_nombres = df_docentes['Nombre'].tolist()
        k = st.session_state.form_key 
        
        docente_seleccionado = st.selectbox(
            "Seleccione su nombre o apellido:", 
            ["🔍 Escriba para buscar docente..."] + lista_nombres, 
            key=f"docente_{k}"
        )
        
        if docente_seleccionado != "🔍 Escriba para buscar docente...":
            datos_doc = df_docentes[df_docentes['Nombre'] == docente_seleccionado].iloc[0]
            nivel_doc = datos_doc['Nivel'].strip()
            area_doc = datos_doc['Área']
            
            st.info(f"👤 **Nivel:** {nivel_doc} | 📚 **Área:** {area_doc}")
            
            # --- NUEVO REQUERIMIENTO: PANEL DE HISTORIAL PERSONAL DEL DOCENTE ---
            st.markdown("<h3 style='font-size:15px; font-weight:bold; color:#0369a1; margin-bottom:4px;'>📊 Mi Reporte de Uso Acumulado hasta la Fecha</h3>", unsafe_allow_html=True)
            
            df_docente_historial = df_asistencias[df_asistencias['Docente'] == docente_seleccionado]
            
            with st.container(border=True):
                if not df_docente_historial.empty:
                    h_col1, h_col2, h_col3 = st.columns(3)
                    
                    mis_horas = df_docente_historial['Horas_Calculadas'].sum()
                    mis_dias = df_docente_historial['Fecha'].nunique()
                    mis_alumnos = df_docente_historial['Alumnos'].sum()
                    
                    h_col1.metric("📆 Días que asistí", f"{mis_dias} días")
                    h_col2.metric("⏱️ Total Horas Acumuladas", f"{mis_horas:.1f} hrs")
                    h_col3.metric("👨‍🏫 Estudiantes Atendidos", f"{int(mis_alumnos)} alumnos")
                else:
                    st.markdown("<span style='color:gray; font-size:13px;'>Aún no registras asistencias en este periodo escolar. ¡Tu primer registro aparecerá aquí!</span>", unsafe_allow_html=True)
            
            # Formulario tradicional de registro
            st.markdown("### Detalles de la Nueva Sesión")
            col1, col2 = st.columns(2)
            
            with col1:
                if nivel_doc.lower() == "primaria":
                    opciones_grado = ["1ro", "2do", "3ro", "4to", "5to", "6to"]
                else:
                    opciones_grado = ["1ro", "2do", "3ro", "4to", "5to"]
                grado = st.selectbox("Grado que ingresa", opciones_grado, key=f"grado_{k}")
                alumnos = st.number_input("Cantidad de Alumnos", min_value=1, max_value=50, value=25, step=1, key=f"alumnos_{k}")
                
            with col2:
                seccion = st.selectbox("Sección", ["A", "B", "C", "D", "E", "F", "G", "H"], key=f"seccion_{k}")
                fecha = st.date_input("Seleccione la Fecha de la Sesión:", value=datetime.today(), key=f"fecha_widget_{k}")
                
                meses_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                dias_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                st.markdown(f"📅 **Día Elegido:** {dias_es[fecha.weekday()]}, {fecha.day} de {meses_es[fecha.month - 1]} de {fecha.year}")
            
            st.markdown("🕒 **Horario de la Sesión (Formato de 12 Horas)**")
            col3, col4 = st.columns(2)
            
            with col3:
                sel_hora_inicio = st.selectbox("Hora de Inicio", lista_horas_ampm, index=4, key=f"h_inicio_{k}")
            with col4:
                sel_hora_fin = st.selectbox("Hora de Fin", lista_horas_ampm, index=10, key=f"h_fin_{k}")
            
            st.markdown("---")
            actividad = st.text_area("Tema o Actividad a desarrollar", placeholder="Ej: Introducción a Scratch...", key=f"actividad_{k}")
            
            if st.button("💾 Registrar Asistencia", type="primary", use_container_width=True):
                fecha_str = str(fecha)
                str_hora_inicio = convertir_to_24h(sel_hora_inicio)
                str_hora_fin = convertir_to_24h(sel_hora_fin)
                
                es_duplicado = not df_asistencias[
                    (df_asistencias['Fecha'] == fecha_str) & 
                    (df_asistencias['Docente'] == docente_seleccionado) & 
                    (df_asistencias['Hora_Inicio'] == str_hora_inicio)
                ].empty
                
                if es_duplicado:
                    st.error(f"⚠️ **Registro Denegado:** Ya registraste una sesión para el **{fecha_str}** a las **{sel_hora_inicio}**.")
                elif str_hora_fin <= str_hora_inicio:
                    st.error("⚠️ **Error en el horario:** La hora de fin debe ser posterior a la de inicio.")
                else:
                    nuevo_registro = {
                        "Fecha": fecha_str, "Nivel": nivel_doc, "Área": area_doc,
                        "Docente": docente_seleccionado, "Grado": grado, "Sección": seccion,
                        "Alumnos": int(alumnos), "Hora_Inicio": str_hora_inicio,
                        "Hora_Fin": str_hora_fin, "Actividad": actividad
                    }
                    
                    df_asistencias = pd.concat([df_asistencias, pd.DataFrame([nuevo_registro])], ignore_index=True)
                    
                    # Quitar columnas calculadas antes de persistir al CSV limpio
                    df_a_guardar = df_asistencias.drop(columns=['Horas_Calculadas', 'Grado y Sección'], errors='ignore')
                    save_data(df_a_guardar)
                    
                    st.session_state.mensaje_exito = True
                    st.session_state.form_key += 1
                    st.rerun()