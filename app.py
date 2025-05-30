
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
from io import BytesIO

st.set_page_config(page_title="Analizador de Encuestas", layout="wide")
st.title("📊 Analizador de Encuestas")

# --- Funciones auxiliares ---

def limpiar_datos(df):
    """Elimina columnas y filas completamente vacías, y duplicados exactos."""
    df = df.dropna(axis=1, how='all')  # columnas vacías
    df = df.dropna(axis=0, how='all')  # filas vacías
    df = df.drop_duplicates()          # filas duplicadas
    return df

def split_multirespuesta(texto):
    """
    Separa una cadena por comas, excepto aquellas que están dentro de paréntesis.
    """
    if pd.isna(texto):
        return []
    partes = re.split(r',\s*(?![^()]*\))', str(texto))
    return [p.strip() for p in partes if p.strip()]

def preprocess_column_general(df, col):
    """Limpia y explota columnas con respuestas múltiples."""
    return df[col].dropna().astype(str).apply(split_multirespuesta).explode()

# --- Interfaz principal ---

uploaded_file = st.file_uploader("Sube un archivo Excel con respuestas", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df = limpiar_datos(df)
    st.success("¡Archivo cargado y limpiado correctamente!")

    st.subheader("Selecciona las preguntas a analizar")

    # Búsqueda manual de columnas
    search_query = st.text_input("🔍 Busca una pregunta por nombre (opcional)")
    filtered_columns = [col for col in df.columns if search_query.lower() in col.lower()] if search_query else df.columns.tolist()

    # Selección múltiple de columnas
    selected_columns = st.multiselect("Preguntas:", filtered_columns)

    if selected_columns:
        st.subheader("🔍 Análisis de las preguntas seleccionadas")

        if len(selected_columns) == 1:
            col = selected_columns[0]
            processed = preprocess_column_general(df, col)

            st.write(processed.value_counts())

            chart_type = st.selectbox("Selecciona tipo de gráfico:", ["Barras", "Pastel"])

            if chart_type == "Barras":
                fig, ax = plt.subplots()
                processed.value_counts().plot(kind="bar", ax=ax)
                ax.set_ylabel("Frecuencia")
            elif chart_type == "Pastel":
                fig, ax = plt.subplots(figsize=(5, 5))
                processed.value_counts().plot(kind="pie", ax=ax, autopct='%1.1f%%')
                ax.set_ylabel("")

            ax.set_title(col)
            st.pyplot(fig)

        elif len(selected_columns) == 2:
            col1, col2 = selected_columns
            df_comb = df[[col1, col2]].dropna(how='any').copy()

            for col in [col1, col2]:
                df_comb[col] = df_comb[col].astype(str).apply(split_multirespuesta)

            df_exploded = df_comb.explode(col1).explode(col2)

            st.write("### Tabla de contingencia")
            pivot = pd.crosstab(index=df_exploded[col1], columns=df_exploded[col2])
            st.dataframe(pivot)

            # Descarga de Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pivot.to_excel(writer, sheet_name='Tabla_Contingencia')
            output.seek(0)

            st.download_button(
                label="📥 Descargar tabla en Excel (.xlsx)",
                data=output,
                file_name="tabla_contingencia.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.write("### Opciones de visualización")
            chart_type = st.selectbox("Selecciona tipo de gráfico:", [
                "Barras agrupadas",
                f"Pastel por {col1}",
                f"Pastel por {col2}"
            ])

            if chart_type == "Barras agrupadas":
                fig, ax = plt.subplots(figsize=(10, 5))
                pivot.plot(kind="bar", ax=ax)
                ax.set_ylabel("Frecuencia")
                ax.set_title(f"{col1} vs {col2}")
            elif chart_type == f"Pastel por {col1}":
                fig, ax = plt.subplots(figsize=(5, 5))
                pivot.sum(axis=1).plot(kind="pie", ax=ax, autopct='%1.1f%%')
                ax.set_ylabel("")
                ax.set_title(f"Distribución por {col1}")
            elif chart_type == f"Pastel por {col2}":
                fig, ax = plt.subplots(figsize=(5, 5))
                pivot.sum(axis=0).plot(kind="pie", ax=ax, autopct='%1.1f%%')
                ax.set_ylabel("")
                ax.set_title(f"Distribución por {col2}")

            st.pyplot(fig)

        else:
            st.warning("Por ahora, el análisis combinado está disponible solo para dos columnas. Selecciona máximo dos.")
    else:
        st.info("Selecciona al menos una pregunta para ver el análisis.")
