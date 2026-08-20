import os
import sqlite3
import pandas as pd
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Gestor de Expedientes Digitales", page_icon="📁", layout="wide"
)

# DIRECTORIOS Y BASE DE DATOS
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "expedientes.db")
EXPEDIENTES_DIR = os.path.join(BASE_DIR, "Expedientes_Digitales")

# Asegurar carpeta de almacenamiento
os.makedirs(EXPEDIENTES_DIR, exist_ok=True)


def init_db():
    """Inicializa las tablas en la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curp TEXT UNIQUE NOT NULL,
            rfc TEXT,
            nombre TEXT NOT NULL,
            primer_apellido TEXT NOT NULL,
            segundo_apellido TEXT,
            telefono TEXT,
            correo TEXT,
            area_puesto TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_curp TEXT NOT NULL,
            tipo_documento TEXT NOT NULL,
            nombre_archivo TEXT NOT NULL,
            ruta_archivo TEXT NOT NULL,
            fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (persona_curp) REFERENCES personas (curp) ON DELETE CASCADE
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


def guardar_archivo(curp, uploaded_file, tipo_doc):
    """Guarda el archivo en carpetas físicas organizadas por CURP."""
    if uploaded_file is None:
        return None

    folder_persona = os.path.join(EXPEDIENTES_DIR, curp.upper().strip())
    os.makedirs(folder_persona, exist_ok=True)

    ext = os.path.splitext(uploaded_file.name)[1]
    nombre_guardado = f"{tipo_doc.replace(' ', '_')}{ext}"
    ruta_completa = os.path.join(folder_persona, nombre_guardado)

    with open(ruta_completa, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return ruta_completa


# --- INTERFAZ DE USUARIO ---
st.title("📁 Sistema de Expedientes Digitales")

menu = [" Registrar Expediente", "🔍 Buscar y Consultar", "📊 Reportes Excel"]
opcion = st.sidebar.selectbox("Menú de Navegación", menu)

# ---------------------------------------------------------
# REGISTRAR EXPEDIENTE
# ---------------------------------------------------------
if opcion == " Registrar Expediente":
    st.subheader("Registro de Personal y Documentación")

    with st.form("form_registro", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            curp = st.text_input("CURP *").upper().strip()
            nombre = st.text_input("Nombre(s) *")
            telefono = st.text_input("Teléfono")
        with col2:
            rfc = st.text_input("RFC").upper().strip()
            primer_apellido = st.text_input("Primer Apellido *")
            correo = st.text_input("Correo Electrónico")
        with col3:
            area_puesto = st.text_input("Área / Puesto")
            segundo_apellido = st.text_input("Segundo Apellido")

        st.markdown("---")
        st.write("### 📄 Carga de Documentos Oficiales")

        c1, c2 = st.columns(2)
        with c1:
            doc_curp = st.file_uploader(
                "1. CURP (PDF/Imagen)", type=["pdf", "png", "jpg", "jpeg"]
            )
            doc_acta = st.file_uploader(
                "2. Acta de Nacimiento", type=["pdf", "png", "jpg", "jpeg"]
            )
            doc_domicilio = st.file_uploader(
                "3. Comprobante de Domicilio", type=["pdf", "png", "jpg", "jpeg"]
            )
            doc_fump = st.file_uploader(
                "4. F.U.M.P.", type=["pdf", "png", "jpg", "jpeg"]
            )
            doc_rfc = st.file_uploader(
                "5. RFC / Constancia Fiscal", type=["pdf", "png", "jpg", "jpeg"]
            )
        with c2:
            doc_solicitud = st.file_uploader(
                "6. Solicitud de Empleo", type=["pdf", "png", "jpg", "jpeg"]
            )
            doc_no_moroso = st.file_uploader(
                "7. Constancia de No Moroso", type=["pdf", "png", "jpg", "jpeg"]
            )
            doc_cedula = st.file_uploader(
                "8. Cédula Profesional", type=["pdf", "png", "jpg", "jpeg"]
            )
            doc_titulo = st.file_uploader(
                "9. Título Profesional", type=["pdf", "png", "jpg", "jpeg"]
            )

        submit = st.form_submit_button("💾 Guardar Expediente Completo")

        if submit:
            if not curp or not nombre or not primer_apellido:
                st.error(
                    "Ingresa los campos obligatorios (*): CURP, Nombre y Primer Apellido."
                )
            else:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """
                        INSERT INTO personas (curp, rfc, nombre, primer_apellido, segundo_apellido, telefono, correo, area_puesto)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            curp,
                            rfc,
                            nombre,
                            primer_apellido,
                            segundo_apellido,
                            telefono,
                            correo,
                            area_puesto,
                        ),
                    )

                    # Mapeo de los 9 documentos oficiales
                    documentos_dict = {
                        "CURP": doc_curp,
                        "Acta_Nacimiento": doc_acta,
                        "Comprobante_Domicilio": doc_domicilio,
                        "FUMP": doc_fump,
                        "RFC": doc_rfc,
                        "Solicitud_Empleo": doc_solicitud,
                        "Constancia_No_Moroso": doc_no_moroso,
                        "Cedula_Profesional": doc_cedula,
                        "Titulo_Profesional": doc_titulo,
                    }

                    for tipo, file_obj in documentos_dict.items():
                        if file_obj is not None:
                            ruta = guardar_archivo(curp, file_obj, tipo)
                            cursor.execute(
                                """
                                INSERT INTO documentos (persona_curp, tipo_documento, nombre_archivo, ruta_archivo)
                                VALUES (?, ?, ?, ?)
                            """,
                                (curp, tipo, file_obj.name, ruta),
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
# BUSCAR Y CONSULTAR
# ---------------------------------------------------------
elif opcion == "🔍 Buscar y Consultar":
    st.subheader("Búsqueda y Descarga de Documentos")

    busqueda = st.text_input(
        "🔎 Buscar por Nombre, Apellidos, CURP o RFC:"
    ).strip()

    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT curp AS CURP, rfc AS RFC, nombre AS Nombre, 
               primer_apellido AS [Primer Apellido], segundo_apellido AS [Segundo Apellido],
               telefono AS Teléfono, area_puesto AS Puesto
        FROM personas
    """

    if busqueda:
        query += f" WHERE curp LIKE '%{busqueda}%' OR rfc LIKE '%{busqueda}%' OR nombre LIKE '%{busqueda}%' OR primer_apellido LIKE '%{busqueda}%'"

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
        cursor.execute(
            "SELECT tipo_documento, nombre_archivo, ruta_archivo FROM documentos WHERE persona_curp = ?",
            (curp_selec,),
        )
        docs = cursor.fetchall()

        if docs:
            st.write(f"**Documentos disponibles para {curp_selec}:**")
            for tipo, name_file, path_file in docs:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.info(
                        f"📄 **{tipo.replace('_', ' ')}**: `{name_file}`"
                    )
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
            st.warning("No hay archivos adjuntos cargados para esta persona.")

    conn.close()

# ---------------------------------------------------------
# REPORTES
# ---------------------------------------------------------
elif opcion == "📊 Reportes Excel":
    st.subheader("Padrón General de Registros")

    conn = sqlite3.connect(DB_PATH)
    df_todo = pd.read_sql_query("SELECT * FROM personas", conn)
    conn.close()

    if not df_todo.empty:
        st.dataframe(df_todo, use_container_width=True)

        output_excel = "reporte_expedientes.xlsx"
        df_todo.to_excel(output_excel, index=False)

        with open(output_excel, "rb") as f:
            st.download_button(
                label="📥 Exportar Base de Datos a Excel",
                data=f,
                file_name="Reporte_Expedientes.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    else:
        st.info("Aún no hay expedientes registrados.")