import os
import sqlite3
import hashlib
import io
import zipfile
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Expedientes Digitales", page_icon="📁", layout="wide"
)

# LÍMITE DE TAMAÑO MÁXIMO POR ARCHIVO (en Megabytes)
LIMITE_MB = 5

# DIRECTORIOS Y BASE DE DATOS
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "expedientes.db")
EXPEDIENTES_DIR = os.path.join(BASE_DIR, "Expedientes_Digitales")

os.makedirs(EXPEDIENTES_DIR, exist_ok=True)

# LISTA DE LOS 10 DOCUMENTOS OFICIALES REQUERIDOS
DOCS_REQUERIDOS = [
    "INE", "Comprobante_Domicilio", "Cartilla_Militar", "Acta_Nacimiento",
    "Cedula_Profesional", "CURP", "RFC", "Constancia_No_Moroso",
    "Titulo", "Carta_Decir_Verdad"
]

def hash_password(password):
    """Genera un hash SHA-256 para almacenamiento seguro de contraseñas."""
    return hashlib.sha256(password.strip().encode()).hexdigest()

def init_db():
    """Inicializa la estructura de tablas e inserta/repara al usuario Admin."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla de Usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            rol TEXT NOT NULL CHECK(rol IN ('admin', 'empleado'))
        )
    """)
    
    # Tabla de Personas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curp TEXT UNIQUE NOT NULL,
            rfc TEXT,
            clave_servidor_publico TEXT,
            nombre TEXT NOT NULL,
            primer_apellido TEXT NOT NULL,
            segundo_apellido TEXT,
            telefono TEXT,
            correo TEXT,
            area_puesto TEXT,
            fecha_ingreso_gem DATE,
            fecha_ingreso_nivel DATE,
            fecha_ingreso_institucion DATE,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (curp) REFERENCES usuarios (username) ON DELETE CASCADE
        )
    """)
    
    # Tabla de Documentos Oficiales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_curp TEXT NOT NULL,
            tipo_documento TEXT NOT NULL,
            nombre_archivo TEXT NOT NULL,
            ruta_archivo TEXT NOT NULL,
            tamano_mb REAL NOT NULL,
            fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (persona_curp) REFERENCES personas (curp) ON DELETE CASCADE
        )
    """)

    # Tabla de Constancias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS constancias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_curp TEXT NOT NULL,
            nombre_curso TEXT NOT NULL,
            institucion_imparte TEXT,
            horas INTEGER,
            fecha_emision DATE,
            nombre_archivo TEXT NOT NULL,
            ruta_archivo TEXT NOT NULL,
            tamano_mb REAL NOT NULL,
            fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (persona_curp) REFERENCES personas (curp) ON DELETE CASCADE
        )
    """)
    
    # Asegurar que el usuario 'admin' exista con la contraseña correcta
    cursor.execute("DELETE FROM usuarios WHERE username = 'admin'")
    cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
                   ('admin', hash_password('admin123'), 'admin'))
        
    conn.commit()
    conn.close()

init_db()

def validar_y_guardar_archivo(curp, uploaded_file, subcarpeta, nombre_prefix):
    """Valida el peso del PDF y lo guarda en disco."""
    if uploaded_file is None:
        return None, None

    tamano_mb = round(uploaded_file.size / (1024 * 1024), 2)
    if tamano_mb > LIMITE_MB:
        st.error(f"❌ Archivo '{uploaded_file.name}' ({tamano_mb} MB) supera el límite de {LIMITE_MB} MB.")
        return False, None

    folder_persona = os.path.join(EXPEDIENTES_DIR, curp.upper().strip(), subcarpeta)
    os.makedirs(folder_persona, exist_ok=True)

    clean_prefix = "".join(c for c in nombre_prefix if c.isalnum() or c in (" ", "_", "-")).rstrip()
    nombre_guardado = f"{clean_prefix.replace(' ', '_')}.pdf"
    ruta_completa = os.path.join(folder_persona, nombre_guardado)

    with open(ruta_completa, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return ruta_completa, tamano_mb

def crear_zip_expediente(curp):
    """Empaca todos los archivos de un expediente en un archivo ZIP en memoria."""
    folder_persona = os.path.join(EXPEDIENTES_DIR, curp.upper().strip())
    zip_buffer = io.BytesIO()
    
    if os.path.exists(folder_persona):
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(folder_persona):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_persona)
                    zip_file.write(file_path, arcname)
        zip_buffer.seek(0)
        return zip_buffer
    return None

# Manejo de Estado de Sesión
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["rol"] = None

# =========================================================
# MODULO DE AUTENTICACIÓN (LOGIN Y REGISTRO DE USUARIOS)
# =========================================================
if not st.session_state["authenticated"]:
    st.title("📁 Sistema de Expedientes Digitales")
    tab_login, tab_registro = st.tabs(["🔐 Iniciar Sesión", "✍️ Crear Cuenta (Servidor Público)"])

    with tab_login:
        st.subheader("Acceso al Sistema")
        with st.form("form_login"):
            usuario_raw = st.text_input("CURP o Usuario (Admin)")
            pass_input = st.text_input("Contraseña", type="password")
            btn_login = st.form_submit_button("Ingresar")

            if btn_login:
                usuario_clean = usuario_raw.strip()
                # Si es el usuario admin se trata en minúsculas, de lo contrario en mayúsculas (CURP)
                usuario_buscar = usuario_clean.lower() if usuario_clean.lower() == "admin" else usuario_clean.upper()

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT password, rol FROM usuarios WHERE username = ?", (usuario_buscar,))
                user_record = cursor.fetchone()
                conn.close()

                if user_record and user_record[0] == hash_password(pass_input):
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = usuario_buscar
                    st.session_state["rol"] = user_record[1]
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

    with tab_registro:
        st.subheader("Registro de Nuevo Servidor Público")
        st.info("Regístrese para comenzar a cargar su expediente personal.")
        with st.form("form_registro_usuario", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                reg_curp = st.text_input("CURP *").upper().strip()
                reg_nombre = st.text_input("Nombre(s) *")
                reg_telefono = st.text_input("Teléfono")
                reg_ingreso_gem = st.date_input("Fecha de Ingreso al GEM", value=None)
                reg_pass = st.text_input("Crea una Contraseña *", type="password")
            with col2:
                reg_rfc = st.text_input("RFC").upper().strip()
                reg_primer_apellido = st.text_input("Primer Apellido *")
                reg_correo = st.text_input("Correo Electrónico")
                reg_ingreso_nivel = st.date_input("Fecha de Ingreso al Nivel", value=None)
                reg_pass_confirm = st.text_input("Confirma tu Contraseña *", type="password")
            with col3:
                reg_clave_sp = st.text_input("Clave de Servidor Público")
                reg_segundo_apellido = st.text_input("Segundo Apellido")
                reg_puesto = st.text_input("Área / Puesto")
                reg_ingreso_inst = st.date_input("Fecha de Ingreso a la Institución", value=None)

            btn_registrar = st.form_submit_button("Registrarse e Iniciar")

            if btn_registrar:
                if not reg_curp or not reg_nombre or not reg_primer_apellido or not reg_pass:
                    st.error("Por favor completa los campos obligatorios (*).")
                elif reg_pass != reg_pass_confirm:
                    st.error("Las contraseñas no coinciden.")
                elif reg_curp.lower() == "admin":
                    st.error("El nombre de usuario 'admin' está reservado.")
                else:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, 'empleado')",
                                       (reg_curp, hash_password(reg_pass)))
                        cursor.execute("""
                            INSERT INTO personas (curp, rfc, clave_servidor_publico, nombre, primer_apellido, 
                                                 segundo_apellido, telefono, correo, area_puesto, 
                                                 fecha_ingreso_gem, fecha_ingreso_nivel, fecha_ingreso_institucion)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (reg_curp, reg_rfc, reg_clave_sp, reg_nombre, reg_primer_apellido, reg_segundo_apellido,
                              reg_telefono, reg_correo, reg_puesto,
                              str(reg_ingreso_gem) if reg_ingreso_gem else None,
                              str(reg_ingreso_nivel) if reg_ingreso_nivel else None,
                              str(reg_ingreso_inst) if reg_ingreso_inst else None))
                        conn.commit()
                        st.success("¡Registro exitoso! Ya puedes iniciar sesión con tu CURP y contraseña.")
                    except sqlite3.IntegrityError:
                        st.error(f"El CURP '{reg_curp}' ya se encuentra registrado.")
                    finally:
                        conn.close()

# =========================================================
# VISTA GENERAL TRAS INICIAR SESIÓN
# =========================================================
else:
    curp_usuario = st.session_state["user"]
    rol_usuario = st.session_state["rol"]

    # Barra lateral de navegación y salida
    st.sidebar.markdown(f"👤 **Usuario:** `{curp_usuario}`")
    st.sidebar.markdown(f"🛡️ **Rol:** `{rol_usuario.upper()}`")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["authenticated"] = False
        st.session_state["user"] = None
        st.session_state["rol"] = None
        st.rerun()

    # ---------------------------------------------------------
    # PANEL SERVIDOR PÚBLICO
    # ---------------------------------------------------------
    if rol_usuario == "empleado":
        st.title("👤 Panel Personal del Servidor Público")
        menu_emp = st.sidebar.radio("Navegación", ["📄 Mi Expediente", "📜 Mis Constancias"])

        if menu_emp == "📄 Mi Expediente":
            st.subheader("Estado de Mi Expediente Digital")
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT tipo_documento, nombre_archivo, ruta_archivo, tamano_mb FROM documentos WHERE persona_curp = ?", (curp_usuario,))
            docs_subidos = {row[0]: row for row in cursor.fetchall()}
            conn.close()

            # Cálculo de avance
            conteo_cargados = len(docs_subidos)
            porcentaje = int((conteo_cargados / 10) * 100)
            
            st.progress(porcentaje / 100)
            if conteo_cargados == 10:
                st.success("🟢 **Expediente Completo** (10 de 10 documentos subidos).")
            else:
                st.warning(f"🟡 **Expediente Incompleto:** Tienes {conteo_cargados} de 10 documentos subidos ({porcentaje}%).")

            st.markdown("---")
            st.markdown("##### 📤 Subir / Actualizar Documentos Requeridos (Solo PDF, máx. 5 MB)")

            col_a, col_b = st.columns(2)
            docs_col1 = DOCS_REQUERIDOS[:5]
            docs_col2 = DOCS_REQUERIDOS[5:]

            for idx, doc_key in enumerate(docs_col1, start=1):
                with col_a:
                    st.write(f"**{idx}. {doc_key.replace('_', ' ')}**")
                    if doc_key in docs_subidos:
                        tipo, name, path, mb = docs_subidos[doc_key]
                        st.caption(f"✅ Cargado: `{name}` ({mb} MB)")
                    else:
                        st.caption("❌ Pendiente de carga")
                    
                    file_up = st.file_uploader(f"Cargar/Reemplazar {doc_key}", type=["pdf"], key=f"up_{doc_key}")
                    if file_up:
                        if st.button(f"Guardar {doc_key.replace('_', ' ')}", key=f"btn_{doc_key}"):
                            ruta, mb = validar_y_guardar_archivo(curp_usuario, file_up, "Documentos_Oficiales", doc_key)
                            if ruta:
                                conn = sqlite3.connect(DB_PATH)
                                cursor = conn.cursor()
                                cursor.execute("DELETE FROM documentos WHERE persona_curp = ? AND tipo_documento = ?", (curp_usuario, doc_key))
                                cursor.execute("INSERT INTO documentos (persona_curp, tipo_documento, nombre_archivo, ruta_archivo, tamano_mb) VALUES (?, ?, ?, ?, ?)",
                                               (curp_usuario, doc_key, file_up.name, ruta, mb))
                                conn.commit()
                                conn.close()
                                st.success("Documento guardado exitosamente.")
                                st.rerun()

            for idx, doc_key in enumerate(docs_col2, start=6):
                with col_b:
                    st.write(f"**{idx}. {doc_key.replace('_', ' ')}**")
                    if doc_key in docs_subidos:
                        tipo, name, path, mb = docs_subidos[doc_key]
                        st.caption(f"✅ Cargado: `{name}` ({mb} MB)")
                    else:
                        st.caption("❌ Pendiente de carga")

                    file_up = st.file_uploader(f"Cargar/Reemplazar {doc_key}", type=["pdf"], key=f"up_{doc_key}")
                    if file_up:
                        if st.button(f"Guardar {doc_key.replace('_', ' ')}", key=f"btn_{doc_key}"):
                            ruta, mb = validar_y_guardar_archivo(curp_usuario, file_up, "Documentos_Oficiales", doc_key)
                            if ruta:
                                conn = sqlite3.connect(DB_PATH)
                                cursor = conn.cursor()
                                cursor.execute("DELETE FROM documentos WHERE persona_curp = ? AND tipo_documento = ?", (curp_usuario, doc_key))
                                cursor.execute("INSERT INTO documentos (persona_curp, tipo_documento, nombre_archivo, ruta_archivo, tamano_mb) VALUES (?, ?, ?, ?, ?)",
                                               (curp_usuario, doc_key, file_up.name, ruta, mb))
                                conn.commit()
                                conn.close()
                                st.success("Documento guardado exitosamente.")
                                st.rerun()

        elif menu_emp == "📜 Mis Constancias":
            st.subheader("Registro de Constancias y Capacitaciones")
            
            with st.form("form_constancia_emp", clear_on_submit=True):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    nombre_curso = st.text_input("Nombre del Curso / Capacitación *")
                    institucion = st.text_input("Institución u Organismo Emisor")
                with col_c2:
                    horas = st.number_input("Horas de Duración / Valor Curricular", min_value=1, value=20, step=1)
                    fecha_emision = st.date_input("Fecha de Emisión", value=None)

                doc_const = st.file_uploader("Subir Constancia en PDF *", type=["pdf"], key="const_emp")
                btn_const = st.form_submit_button("📜 Guardar Constancia")

                if btn_const:
                    if not nombre_curso or doc_const is None:
                        st.error("Completa el nombre del curso y adjunta el archivo PDF.")
                    else:
                        prefijo = f"Constancia_{nombre_curso[:30]}"
                        ruta, mb = validar_y_guardar_archivo(curp_usuario, doc_const, "Constancias_y_Cursos", prefijo)
                        if ruta:
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO constancias (persona_curp, nombre_curso, institucion_imparte, horas, fecha_emision, nombre_archivo, ruta_archivo, tamano_mb)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (curp_usuario, nombre_curso, institucion, horas, str(fecha_emision) if fecha_emision else None, doc_const.name, ruta, mb))
                            conn.commit()
                            conn.close()
                            st.success(f"Constancia '{nombre_curso}' registrada exitosamente.")

            st.markdown("---")
            st.markdown("##### 🎓 Mi Historial de Constancias")
            conn = sqlite3.connect(DB_PATH)
            df_c = pd.read_sql_query("SELECT nombre_curso AS Curso, institucion_imparte AS Institución, horas AS Horas, fecha_emision AS Fecha, nombre_archivo AS Archivo, tamano_mb AS [MB] FROM constancias WHERE persona_curp = ?", conn, params=(curp_usuario,))
            conn.close()
            
            if not df_c.empty:
                st.dataframe(df_c, use_container_width=True)
                st.info(f"💡 **Total de Horas Curriculares Acumuladas:** {df_c['Horas'].sum()} hrs.")
            else:
                st.info("Aún no has registrado constancias de capacitación.")

    # ---------------------------------------------------------
    # PANEL ADMINISTRADOR
    # ---------------------------------------------------------
    elif rol_usuario == "admin":
        st.title("🛡️ Panel de Control Administrativo")
        menu_admin = st.sidebar.radio("Navegación Admin", [
            "📊 Dashboard General", "🔍 Consulta y Descargas ZIP", "📜 Control de Constancias", "📈 Exportar Reportes Excel"
        ])

        conn = sqlite3.connect(DB_PATH)

        if menu_admin == "📊 Dashboard General":
            st.subheader("Estado General de Expedientes")

            df_status = pd.read_sql_query("""
                SELECT p.curp AS CURP, p.clave_servidor_publico AS [Clave SP],
                       p.nombre || ' ' || p.primer_apellido || ' ' || COALESCE(p.segundo_apellido, '') AS [Servidor Público],
                       p.area_puesto AS [Área/Puesto],
                       COUNT(d.id) AS [Documentos Cargados]
                FROM personas p
                LEFT JOIN documentos d ON p.curp = d.persona_curp
                GROUP BY p.curp
            """, conn)

            if not df_status.empty:
                df_status["Estatus"] = df_status["Documentos Cargados"].apply(
                    lambda x: "🟢 Completo" if x == 10 else ("🟡 Incompleto" if x > 0 else "🔴 Sin documentos")
                )
                
                c_total, c_comp, c_incomp, c_vacio = st.columns(4)
                c_total.metric("Total Servidores Públicos", len(df_status))
                c_comp.metric("Expedientes Completos", len(df_status[df_status["Documentos Cargados"] == 10]))
                c_incomp.metric("Expedientes En Proceso", len(df_status[(df_status["Documentos Cargados"] > 0) & (df_status["Documentos Cargados"] < 10)]))
                c_vacio.metric("Sin Documentación", len(df_status[df_status["Documentos Cargados"] == 0]))

                st.markdown("---")
                st.dataframe(df_status, use_container_width=True)
            else:
                st.info("No hay Servidores Públicos registrados en el sistema.")

        elif menu_admin == "🔍 Consulta y Descargas ZIP":
            st.subheader("Revisión Individual y Descarga de Expedientes")

            df_p = pd.read_sql_query("SELECT curp, nombre || ' ' || primer_apellido || ' ' || COALESCE(segundo_apellido, '') AS nombre_completo, clave_servidor_publico FROM personas", conn)
            
            if not df_p.empty:
                opciones = {f"{row['nombre_completo']} | CURP: {row['curp']} | SP: {row['clave_servidor_publico'] or 'N/A'}": row['curp'] for _, row in df_p.iterrows()}
                selec = st.selectbox("Selecciona un Servidor Público:", list(opciones.keys()))
                curp_sel = opciones[selec]

                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"#### Expediente de: `{curp_sel}`")
                with col_b:
                    zip_data = crear_zip_expediente(curp_sel)
                    if zip_data:
                        st.download_button(
                            label="📦 Descargar Expediente en ZIP",
                            data=zip_data,
                            file_name=f"Expediente_{curp_sel}.zip",
                            mime="application/zip"
                        )

                st.markdown("---")
                tab1, tab2 = st.tabs(["📄 Documentos Oficiales", "📜 Constancias"])

                with tab1:
                    cursor = conn.cursor()
                    cursor.execute("SELECT tipo_documento, nombre_archivo, ruta_archivo, tamano_mb FROM documentos WHERE persona_curp = ?", (curp_sel,))
                    docs = cursor.fetchall()
                    if docs:
                        for tipo, name_file, path_file, tam_mb in docs:
                            c1, c2 = st.columns([3, 1])
                            c1.info(f"📄 **{tipo.replace('_', ' ')}** ({tam_mb} MB): `{name_file}`")
                            if os.path.exists(path_file):
                                with open(path_file, "rb") as f:
                                    c2.download_button("⬇️ Descargar", f.read(), file_name=os.path.basename(path_file), key=f"d_adm_{curp_sel}_{tipo}")
                    else:
                        st.warning("No hay documentos oficiales registrados para esta persona.")

                with tab2:
                    cursor = conn.cursor()
                    cursor.execute("SELECT nombre_curso, institucion_imparte, horas, fecha_emision, nombre_archivo, ruta_archivo, tamano_mb FROM constancias WHERE persona_curp = ?", (curp_sel,))
                    consts = cursor.fetchall()
                    if consts:
                        for curso, inst, hrs, f_emision, name_file, path_file, tam_mb in consts:
                            c1, c2 = st.columns([3, 1])
                            c1.success(f"🎓 **{curso}** | {inst or 'S/I'} ({hrs or 0} hrs) - Fecha: {f_emision or 'N/A'}\n`{name_file}` ({tam_mb} MB)")
                            if os.path.exists(path_file):
                                with open(path_file, "rb") as f:
                                    c2.download_button("⬇️ Descargar", f.read(), file_name=os.path.basename(path_file), key=f"d_c_{curp_sel}_{curso}")
                    else:
                        st.info("No hay constancias registradas para esta persona.")

        elif menu_admin == "📜 Control de Constancias":
            st.subheader("Reporte General de Capacitaciones Registradas")
            df_c_all = pd.read_sql_query("""
                SELECT c.id, p.curp AS CURP, p.clave_servidor_publico AS [Clave SP],
                       p.nombre || ' ' || p.primer_apellido || ' ' || COALESCE(p.segundo_apellido, '') AS [Servidor Público],
                       c.nombre_curso AS [Curso/Capacitación], c.institucion_imparte AS Institución, c.horas AS Horas, c.fecha_emision AS Fecha
                FROM constancias c
                JOIN personas p ON c.persona_curp = p.curp
            """, conn)
            
            if not df_c_all.empty:
                st.dataframe(df_c_all, use_container_width=True)
            else:
                st.info("No se han registrado constancias en el sistema.")

        elif menu_admin == "📈 Exportar Reportes Excel":
            st.subheader("Generación de Reportes Consolidados")

            t1, t2 = st.tabs(["📊 Padrón General", "🎓 Reporte de Capacitación"])

            with t1:
                df_exp = pd.read_sql_query("SELECT * FROM personas", conn)
                if not df_exp.empty:
                    st.dataframe(df_exp, use_container_width=True)
                    out1 = "padron_personal.xlsx"
                    df_exp.to_excel(out1, index=False)
                    with open(out1, "rb") as f:
                        st.download_button("📥 Descargar Padrón en Excel", f, file_name="Padron_Personal.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            with t2:
                df_rep_c = pd.read_sql_query("""
                    SELECT c.id, p.curp, p.clave_servidor_publico, 
                           p.nombre || ' ' || p.primer_apellido || ' ' || COALESCE(p.segundo_apellido, '') AS servidor_publico,
                           c.nombre_curso, c.institucion_imparte, c.horas, c.fecha_emision
                    FROM constancias c
                    JOIN personas p ON c.persona_curp = p.curp
                """, conn)
                if not df_rep_c.empty:
                    st.dataframe(df_rep_c, use_container_width=True)
                    out2 = "reporte_capacitaciones.xlsx"
                    df_rep_c.to_excel(out2, index=False)
                    with open(out2, "rb") as f:
                        st.download_button("📥 Descargar Reporte de Capacitaciones", f, file_name="Reporte_Capacitaciones.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        conn.close()