import pandas as pd
import streamlit as st

# Configuración de interfaz
st.set_page_config(
    page_title="Gestor de Expedientes (Demo UI)", page_icon="📁", layout="wide"
)

st.title("📁 Sistema de Expedientes Digitales — Vista Previa")

# Menú lateral
menu = [" Registrar Expediente", "🔍 Buscar y Consultar", "📊 Reportes Excel"]
opcion = st.sidebar.selectbox("Menú de Navegación", menu)

# ---------------------------------------------------------
# 1. REGISTRAR EXPEDIENTE (SOLO INTERFAZ)
# ---------------------------------------------------------
if opcion == " Registrar Expediente":
    st.subheader("Registro de Personal")

    with st.form("form_demo"):
        st.markdown("##### 👤 Datos Personales")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input("CURP *", placeholder="AAAA000000XXXXXX00")
            st.text_input("Nombre(s) *")
            st.text_input("Teléfono", placeholder="10 dígitos")
        with col2:
            st.text_input("RFC", placeholder="AAAA000000XXX")
            st.text_input("Primer Apellido *")
            st.text_input("Correo Electrónico")
        with col3:
            st.text_input("Área / Puesto")
            st.text_input("Segundo Apellido")

        st.markdown("---")
        st.markdown("##### 📄 Carga de Documentos Oficiales (9 Requisitos)")

        c1, c2 = st.columns(2)
        with c1:
            st.file_uploader(
                "1. CURP", type=["pdf", "png", "jpg"], key="u_curp"
            )
            st.file_uploader(
                "2. Acta de Nacimiento", type=["pdf", "png", "jpg"], key="u_acta"
            )
            st.file_uploader(
                "3. Comprobante de Domicilio",
                type=["pdf", "png", "jpg"],
                key="u_dom",
            )
            st.file_uploader(
                "4. F.U.M.P.", type=["pdf", "png", "jpg"], key="u_fump"
            )
            st.file_uploader(
                "5. RFC / Constancia Fiscal",
                type=["pdf", "png", "jpg"],
                key="u_rfc",
            )
        with c2:
            st.file_uploader(
                "6. Solicitud de Empleo",
                type=["pdf", "png", "jpg"],
                key="u_sol",
            )
            st.file_uploader(
                "7. Constancia de No Moroso",
                type=["pdf", "png", "jpg"],
                key="u_moroso",
            )
            st.file_uploader(
                "8. Cédula Profesional",
                type=["pdf", "png", "jpg"],
                key="u_cedula",
            )
            st.file_uploader(
                "9. Título Profesional",
                type=["pdf", "png", "jpg"],
                key="u_titulo",
            )

        st.markdown("---")
        guardar = st.form_submit_button("💾 Guardar Expediente (Demo)")

        if guardar:
            st.info(
                "💡 Botón presionado. En la siguiente etapa aquí se guardarán los archivos en carpeta y los datos en la BDDD."
            )

# ---------------------------------------------------------
# 2. BUSCAR Y CONSULTAR (SOLO INTERFAZ)
# ---------------------------------------------------------
elif opcion == "🔍 Buscar y Consultar":
    st.subheader("Búsqueda y Vista de Documentos")

    st.text_input("🔎 Buscar por Nombre, Apellidos, CURP o RFC:")

    # Tabla de ejemplo con datos ficticios
    datos_ejemplo = pd.DataFrame(
        {
            "CURP": ["GARM950512MDFXXX01", "VILA920101MDFXXX02"],
            "RFC": ["GARM950512XX1", "VILA920101XX2"],
            "Nombre": ["María", "Juan"],
            "Primer Apellido": ["García", "Pérez"],
            "Segundo Apellido": ["Mendoza", "López"],
            "Área/Puesto": ["Sistemas", "Administración"],
        }
    )

    st.write("**Resultados de búsqueda:**")
    st.dataframe(datos_ejemplo, use_container_width=True)

    st.markdown("---")
    st.selectbox(
        "Selecciona un expediente para revisar sus documentos:",
        [
            "-- Seleccionar --",
            "GARM950512MDFXXX01 - María García",
            "VILA920101MDFXXX02 - Juan Pérez",
        ],
    )

    # Vista previa visual de cómo lucirán los botones de descarga
    st.write("**Documentos cargados en el expediente (Ejemplo):**")
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.info("📄 **CURP**: `CURP_MARIA_GARCIA.pdf`")
        st.info("📄 **Cédula Profesional**: `CEDULA_MARIA_GARCIA.pdf`")
    with col_b:
        st.button("⬇️ Descargar", key="d1")
        st.button("⬇️ Descargar", key="d2")

# ---------------------------------------------------------
# 3. REPORTES (SOLO INTERFAZ)
# ---------------------------------------------------------
elif opcion == "📊 Reportes Excel":
    st.subheader("Vista Previa del Padrón")
    st.write(
        "Aquí se desplegará la tabla completa con opción de descarga a Excel."
    )

    datos_reporte = pd.DataFrame(
        {
            "ID": [1, 2],
            "CURP": ["GARM950512MDFXXX01", "VILA920101MDFXXX02"],
            "Nombre Completo": [
                "María García Mendoza",
                "Juan Pérez López",
            ],
            "Estatus Expediente": ["Completo (9/9)", "Incompleto (5/9)"],
        }
    )

    st.dataframe(datos_reporte, use_container_width=True)
    st.button("📥 Descargar Reporte en Excel (Demo)")