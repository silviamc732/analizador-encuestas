import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Analizador de Encuestas", layout="wide")
st.title("📊 Analizador de Encuestas")

# Subida del archivo Excel
uploaded_file = st.file_uploader("Sube un archivo Excel con respuestas", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("¡Archivo cargado correctamente!")

    st.subheader("Selecciona las preguntas a analizar")

    # Búsqueda manual de columnas
    search_query = st.text_input("🔍 Busca una pregunta por nombre (opcional)")
    filtered_columns = [col for col in df.columns if search_query.lower() in col.lower()] if search_query else df.columns.tolist()

    # Selección múltiple de columnas
    selected_columns = st.multiselect("Preguntas:", filtered_columns)

    def preprocess_column(col):
        return df[col].dropna().astype(str).str.split(",\s*").explode()

    if selected_columns:
        st.subheader("🔍 Análisis de las preguntas seleccionadas")

        if len(selected_columns) == 1:
            col = selected_columns[0]
            processed = preprocess_column(col)

            st.write(processed.value_counts())

            chart_type = st.selectbox("Selecciona tipo de gráfico:", ["Barras", "Pastel"])
            fig, ax = plt.subplots()

            if chart_type == "Barras":
                processed.value_counts().plot(kind="bar", ax=ax)
                ax.set_ylabel("Frecuencia")
            elif chart_type == "Pastel":
                processed.value_counts().plot(kind="pie", ax=ax, autopct='%1.1f%%')
                ax.set_ylabel("")

            ax.set_title(col)
            st.pyplot(fig)

        elif len(selected_columns) == 2:
            col1, col2 = selected_columns
            df_comb = df[[col1, col2]].dropna(how='any').copy()

            for col in [col1, col2]:
                df_comb[col] = df_comb[col].astype(str).str.split(",\s*")

            df_exploded = df_comb.copy()
            for col in [col1, col2]:
                df_exploded = df_exploded.explode(col)

            st.write("### Tabla de contingencia")
            pivot = pd.crosstab(index=df_exploded[col1], columns=df_exploded[col2])
            st.dataframe(pivot)

            # Botón para descargar la tabla en Excel (.xlsx)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pivot.to_excel(writer, sheet_name='Tabla_Contingencia')
            output.seek(0)  # Muy importante

            st.download_button(
                label="📥 Descargar tabla en Excel (.xlsx)",
                data=output,
                file_name="tabla_contingencia.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Opciones para graficar
            st.write("### Opciones de visualización")
            chart_type = st.selectbox("Selecciona tipo de gráfico:", [
                "Barras agrupadas",
                f"Pastel por {col1}",
                f"Pastel por {col2}"
            ])

            fig, ax = plt.subplots(figsize=(10, 5))

            if chart_type == "Barras agrupadas":
                pivot.plot(kind="bar", ax=ax)
                ax.set_ylabel("Frecuencia")
                ax.set_title(f"{col1} vs {col2}")
            elif chart_type == f"Pastel por {col1}":
                pivot.sum(axis=1).plot(kind="pie", ax=ax, autopct='%1.1f%%')
                ax.set_ylabel("")
                ax.set_title(f"Distribución por {col1}")
            elif chart_type == f"Pastel por {col2}":
                pivot.sum(axis=0).plot(kind="pie", ax=ax, autopct='%1.1f%%')
                ax.set_ylabel("")
                ax.set_title(f"Distribución por {col2}")

            st.pyplot(fig)

        else:
            st.warning("Por ahora, el análisis combinado está disponible solo para dos columnas. Selecciona máximo dos.")
    else:
        st.info("Selecciona al menos una pregunta para ver el análisis.")
