import os
import sqlite3
import pandas as pd
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Gestor de Expedientes Digitales", page_icon="📁", layout="wide"
)

# LÍMITE DE TAMAÑO MÁXIMO POR ARCHIVO (en Megabytes)
LIMITE_MB = 5

# DIRECTORIOS Y BASE DE DATOS
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "expedientes.db")
EXPEDIENTES_DIR = os.path.join(BASE_DIR, "Expedientes_Digitales")

os.makedirs(EXPEDIENTES_DIR, exist_ok=True)


def init_db():
    """Inicializa las tablas en la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla de Personas
    cursor.execute(
        """
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
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    
    # Tabla de Documentos Oficiales
    cursor.execute(
        """
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
    """
    )

    # Tabla de Constancias / Capacitaciones
    cursor.execute(
        """
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
    """
    )
    conn.commit()
    conn.close()


init_db()


def validar_y_guardar_archivo(curp, uploaded_file, subcarpeta, nombre_prefix):
    """Valida el límite de peso en MB y guarda el PDF en carpetas organizadas."""
    if uploaded_file is None:
        return None, None

    tamano_mb = round(uploaded_file.size / (1024 * 1024), 2)

    if tamano_mb > LIMITE_MB:
        st.error(
            f"❌ El archivo '{uploaded_file.name}' pesa {tamano_mb} MB y excede el límite permitido de {LIMITE_MB} MB."
        )
        return False, None

    folder_persona = os.path.join(EXPEDIENTES_DIR, curp.upper().strip(), subcarpeta)
    os.makedirs(folder_persona, exist_ok=True)

    # Limpiar nombre para evitar caracteres no válidos en rutas
    clean_prefix = "".join(c for c in nombre_prefix if c.isalnum() or c in (" ", "_", "-")).rstrip()
    nombre_guardado = f"{clean_prefix.replace(' ', '_')}.pdf"
    ruta_completa = os.path.join(folder_persona, nombre_guardado)

    with open(ruta_completa, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return ruta_completa, tamano_mb


def obtener_lista_personas():
    """Obtiene la lista de personas para usar en selectbox."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT curp, nombre, primer_apellido, segundo_apellido, clave_servidor_publico FROM personas ORDER BY primer_apellido, nombre",
        conn,
    )
    conn.close()
    return df


# --- INTERFAZ DE USUARIO ---
st.title("📁 Sistema de Expedientes Digitales")

menu = [
    " Registrar Expediente",
    "📜 Registrar Constancias",
    "🔍 Buscar y Consultar",
    "📊 Reportes Excel",
]
opcion = st.sidebar.selectbox("Menú de Navegación", menu)

# ---------------------------------------------------------
# REGISTRAR EXPEDIENTE
# ---------------------------------------------------------
if opcion == " Registrar Expediente":
    st.subheader("Registro de Personal y Documentación")
    st.info(
        f"📌 **Regla de Almacenamiento:** Todos los documentos deben subirse en formato **PDF** con un tamaño máximo de **{LIMITE_MB} MB** por archivo."
    )

    with st.form("form_registro", clear_on_submit=True):
        st.markdown("##### 👤 Datos Personales y Laborales")
        col1, col2, col3 = st.columns(3)
        with col1:
            curp = st.text_input("CURP *").upper().strip()
            nombre = st.text_input("Nombre(s) *")
            telefono = st.text_input("Teléfono")
            fecha_ingreso_gem = st.date_input(
                "Fecha de Ingreso al GEM", value=None
            )

        with col2:
            rfc = st.text_input("RFC").upper().strip()
            primer_apellido = st.text_input("Primer Apellido *")
            correo = st.text_input("Correo Electrónico")
            fecha_ingreso_nivel = st.date_input(
                "Fecha de Ingreso al Nivel", value=None
            )

        with col3:
            clave_sp = st.text_input("Clave de Servidor Público")
            segundo_apellido = st.text_input("Segundo Apellido")
            area_puesto = st.text_input("Área / Puesto")
            fecha_ingreso_inst = st.date_input(
                "Fecha de Ingreso a la Institución", value=None
            )

        st.markdown("---")
        st.markdown("##### 📄 Carga de Documentos Oficiales (Solo PDF)")

        c1, c2 = st.columns(2)
        with c1:
            doc_ine = st.file_uploader("1. INE (PDF)", type=["pdf"], key="ine")
            doc_domicilio = st.file_uploader(
                "2. Comprobante de Domicilio (PDF)", type=["pdf"], key="dom"
            )
            doc_cartilla = st.file_uploader(
                "3. Cartilla Militar (PDF)", type=["pdf"], key="cartilla"
            )
            doc_acta = st.file_uploader(
                "4. Acta de Nacimiento (PDF)", type=["pdf"], key="acta"
            )
            doc_cedula = st.file_uploader(
                "5. Cédula Profesional (PDF)", type=["pdf"], key="cedula"
            )
        with c2:
            doc_curp = st.file_uploader(
                "6. CURP (PDF)", type=["pdf"], key="curp_doc"
            )
            doc_rfc = st.file_uploader(
                "7. RFC (PDF)", type=["pdf"], key="rfc_doc"
            )
            doc_no_moroso = st.file_uploader(
                "8. Constancia de No Moroso (PDF)", type=["pdf"], key="moroso"
            )
            doc_titulo = st.file_uploader(
                "9. Título (PDF)", type=["pdf"], key="titulo"
            )
            doc_carta_verdad = st.file_uploader(
                "10. Carta Decir Verdad (PDF)", type=["pdf"], key="verdad"
            )

        submit = st.form_submit_button("💾 Guardar Expediente Completo")

        if submit:
            if not curp or not nombre or not primer_apellido:
                st.error(
                    "Ingresa los campos obligatorios (*): CURP, Nombre y Primer Apellido."
                )
            else:
                documentos_dict = {
                    "INE": doc_ine,
                    "Comprobante_Domicilio": doc_domicilio,
                    "Cartilla_Militar": doc_cartilla,
                    "Acta_Nacimiento": doc_acta,
                    "Cedula_Profesional": doc_cedula,
                    "CURP": doc_curp,
                    "RFC": doc_rfc,
                    "Constancia_No_Moroso": doc_no_moroso,
                    "Titulo": doc_titulo,
                    "Carta_Decir_Verdad": doc_carta_verdad,
                }

                # Validar peso de archivos
                excede_peso = False
                for tipo, file_obj in documentos_dict.items():
                    if file_obj is not None:
                        tam_mb = file_obj.size / (1024 * 1024)
                        if tam_mb > LIMITE_MB:
                            st.error(
                                f"❌ El archivo '{tipo.replace('_', ' ')}' excede el límite de {LIMITE_MB} MB (Pesa: {round(tam_mb, 2)} MB)."
                            )
                            excede_peso = True

                if not excede_peso:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    try:
                        cursor.execute(
                            """
                            INSERT INTO personas (
                                curp, rfc, clave_servidor_publico, nombre, primer_apellido, 
                                segundo_apellido, telefono, correo, area_puesto, 
                                fecha_ingreso_gem, fecha_ingreso_nivel, fecha_ingreso_institucion
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                curp,
                                rfc,
                                clave_sp,
                                nombre,
                                primer_apellido,
                                segundo_apellido,
                                telefono,
                                correo,
                                area_puesto,
                                str(fecha_ingreso_gem) if fecha_ingreso_gem else None,
                                str(fecha_ingreso_nivel) if fecha_ingreso_nivel else None,
                                str(fecha_ingreso_inst) if fecha_ingreso_inst else None,
                            ),
                        )

                        for tipo, file_obj in documentos_dict.items():
                            if file_obj is not None:
                                ruta, tamano_mb = validar_y_guardar_archivo(
                                    curp, file_obj, "Documentos_Oficiales", tipo
                                )
                                cursor.execute(
                                    """
                                    INSERT INTO documentos (persona_curp, tipo_documento, nombre_archivo, ruta_archivo, tamano_mb)
                                    VALUES (?, ?, ?, ?, ?)
                                """,
                                    (
                                        curp,
                                        tipo,
                                        file_obj.name,
                                        ruta,
                                        tamano_mb,
                                    ),
                                )

                        conn.commit()
                        st.success(
                            f"¡Expediente de {nombre} {primer_apellido} registrado con éxito!"
                        )
                    except sqlite3.IntegrityError:
                        st.error(
                            f"El CURP '{curp}' ya existe en la base de datos."
                        )
                    finally:
                        conn.close()

# ---------------------------------------------------------
# REGISTRAR CONSTANCIAS
# ---------------------------------------------------------
elif opcion == "📜 Registrar Constancias":
    st.subheader("Registro de Constancias, Cursos y Capacitaciones")

    df_pers = obtener_lista_personas()

    if df_pers.empty:
        st.warning("⚠️ Primero debes registrar al menos una persona en la sección 'Registrar Expediente'.")
    else:
        opciones_persona = {
            f"{row['primer_apellido']} {row['segundo_apellido'] or ''} {row['nombre']} | CURP: {row['curp']} | Clave SP: {row['clave_servidor_publico'] or 'N/A'}": row['curp']
            for _, row in df_pers.iterrows()
        }

        persona_seleccionada = st.selectbox(
            "Selecciona al Servidor Público *",
            list(opciones_persona.keys())
        )
        curp_asociada = opciones_persona[persona_seleccionada]

        st.markdown("---")

        with st.form("form_constancia", clear_on_submit=True):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                nombre_curso = st.text_input("Nombre del Curso / Capacitación / Diplomado *")
                institucion = st.text_input("Institución u Organismo que lo Imparte")
            with col_c2:
                horas = st.number_input("Horas de Duración / Valor Curricular", min_value=1, value=20, step=1)
                fecha_emision = st.date_input("Fecha de Término / Emisión", value=None)

            doc_constancia = st.file_uploader(
                "Subir Constancia o Documento Comprobatorio (PDF) *",
                type=["pdf"],
                key="constancia_pdf"
            )

            btn_guardar_constancia = st.form_submit_button("📜 Guardar Constancia")

            if btn_guardar_constancia:
                if not nombre_curso or doc_constancia is None:
                    st.error("Por favor completa los campos obligatorios (*): Nombre del curso y el archivo PDF.")
                else:
                    tam_mb = doc_constancia.size / (1024 * 1024)
                    if tam_mb > LIMITE_MB:
                        st.error(f"❌ La constancia excede el límite de {LIMITE_MB} MB (Pesa: {round(tam_mb, 2)} MB).")
                    else:
                        nombre_prefijo = f"Constancia_{nombre_curso[:30]}"
                        ruta, tamano_mb = validar_y_guardar_archivo(
                            curp_asociada, doc_constancia, "Constancias_y_Cursos", nombre_prefijo
                        )

                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            INSERT INTO constancias (
                                persona_curp, nombre_curso, institucion_imparte, 
                                horas, fecha_emision, nombre_archivo, ruta_archivo, tamano_mb
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                curp_asociada,
                                nombre_curso,
                                institucion,
                                horas,
                                str(fecha_emision) if fecha_emision else None,
                                doc_constancia.name,
                                ruta,
                                tamano_mb,
                            ),
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"¡Constancia '{nombre_curso}' registrada correctamente para {curp_asociada}!")

# ---------------------------------------------------------
# BUSCAR Y CONSULTAR
# ---------------------------------------------------------
elif opcion == "🔍 Buscar y Consultar":
    st.subheader("Búsqueda y Descarga de Documentos y Constancias")

    busqueda = st.text_input(
        "🔎 Buscar por Nombre, Apellidos, CURP, RFC o Clave de Servidor Público:"
    ).strip()

    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT curp AS CURP, rfc AS RFC, clave_servidor_publico AS [Clave SP], 
               nombre AS Nombre, primer_apellido AS [Primer Apellido], segundo_apellido AS [Segundo Apellido],
               area_puesto AS Puesto, fecha_ingreso_gem AS [Ingreso GEM], 
               fecha_ingreso_nivel AS [Ingreso Nivel], fecha_ingreso_institucion AS [Ingreso Inst.]
        FROM personas
    """

    if busqueda:
        query += f" WHERE curp LIKE '%{busqueda}%' OR rfc LIKE '%{busqueda}%' OR clave_servidor_publico LIKE '%{busqueda}%' OR nombre LIKE '%{busqueda}%' OR primer_apellido LIKE '%{busqueda}%'"

    df_personas = pd.read_sql_query(query, conn)
    st.dataframe(df_personas, use_container_width=True)

    st.markdown("---")
    curps = (
        ["-- Seleccionar --"] + list(df_personas["CURP"].values)
        if not df_personas.empty
        else ["-- Seleccionar --"]
    )
    curp_selec = st.selectbox("Selecciona un CURP para revisar expediente:", curps)

    if curp_selec != "-- Seleccionar --":
        cursor = conn.cursor()
        
        # 1. Mostrar Documentos Oficiales
        st.markdown("### 📄 Documentos Oficiales")
        cursor.execute(
            "SELECT tipo_documento, nombre_archivo, ruta_archivo, tamano_mb FROM documentos WHERE persona_curp = ?",
            (curp_selec,),
        )
        docs = cursor.fetchall()

        if docs:
            for tipo, name_file, path_file, tam_mb in docs:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.info(f"📄 **{tipo.replace('_', ' ')}** ({tam_mb} MB): `{name_file}`")
                with col_b:
                    if os.path.exists(path_file):
                        with open(path_file, "rb") as f:
                            st.download_button(
                                label="⬇️ Descargar",
                                data=f.read(),
                                file_name=os.path.basename(path_file),
                                key=f"{curp_selec}_{tipo}",
                            )
                    else:
                        st.error("No localizado")
        else:
            st.warning("No hay documentos oficiales cargados.")

        # 2. Mostrar Constancias
        st.markdown("### 📜 Constancias y Capacitaciones")
        cursor.execute(
            "SELECT nombre_curso, institucion_imparte, horas, fecha_emision, nombre_archivo, ruta_archivo, tamano_mb FROM constancias WHERE persona_curp = ?",
            (curp_selec,),
        )
        constancias_list = cursor.fetchall()

        if constancias_list:
            for curso, inst, hrs, f_emision, name_file, path_file, tam_mb in constancias_list:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.success(
                        f"🎓 **{curso}** | {inst or 'S/I'} ({hrs or 0} hrs) - Emisión: {f_emision or 'N/A'}\n"
                        f"📄 Archivo ({tam_mb} MB): `{name_file}`"
                    )
                with col_b:
                    if os.path.exists(path_file):
                        with open(path_file, "rb") as f:
                            st.download_button(
                                label="⬇️ Descargar Constancia",
                                data=f.read(),
                                file_name=os.path.basename(path_file),
                                key=f"{curp_selec}_{curso}_{name_file}",
                            )
                    else:
                        st.error("No localizado")
        else:
            st.info("Aún no se han registrado constancias para esta persona.")

    conn.close()

# ---------------------------------------------------------
# REPORTES
# ---------------------------------------------------------
elif opcion == "📊 Reportes Excel":
    st.subheader("Reportes y Descarga de Información")

    tab1, tab2 = st.tabs(["👥 Padrón de Personal", "📜 Histórico de Constancias"])

    conn = sqlite3.connect(DB_PATH)

    with tab1:
        df_todo = pd.read_sql_query("SELECT * FROM personas", conn)
        if not df_todo.empty:
            st.dataframe(df_todo, use_container_width=True)

            output_excel = "reporte_expedientes.xlsx"
            df_todo.to_excel(output_excel, index=False)

            with open(output_excel, "rb") as f:
                st.download_button(
                    label="📥 Exportar Padrón de Personal a Excel",
                    data=f,
                    file_name="Padrón_Personal.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="exp_padrón"
                )
        else:
            st.info("Aún no hay expedientes registrados.")

    with tab2:
        df_constancias = pd.read_sql_query(
            """
            SELECT c.id, p.curp, p.clave_servidor_publico, p.nombre || ' ' || p.primer_apellido || ' ' || COALESCE(p.segundo_apellido, '') AS servidor_publico,
                   c.nombre_curso, c.institucion_imparte, c.horas, c.fecha_emision, c.tamano_mb, c.fecha_subida
            FROM constancias c
            JOIN personas p ON c.persona_curp = p.curp
            """, conn
        )
        if not df_constancias.empty:
            st.dataframe(df_constancias, use_container_width=True)

            output_excel_const = "reporte_constancias.xlsx"
            df_constancias.to_excel(output_excel_const, index=False)

            with open(output_excel_const, "rb") as f:
                st.download_button(
                    label="📥 Exportar Reporte de Constancias a Excel",
                    data=f,
                    file_name="Reporte_Constancias.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="exp_constancias"
                )
        else:
            st.info("Aún no hay constancias registradas.")

    conn.close()