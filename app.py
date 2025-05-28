import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Analizador de Encuestas", layout="wide")

st.title("📊 Analizador de Encuestas")

# Subir archivo Excel
uploaded_file = st.file_uploader("Sube un archivo Excel con respuestas", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("¡Archivo cargado correctamente!")

    st.subheader("Selecciona las preguntas a analizar")

    # Búsqueda manual de columnas
    search_query = st.text_input("🔍 Busca una pregunta por nombre (opcional)")

    # Filtrar columnas por búsqueda
    if search_query:
        filtered_columns = [col for col in df.columns if search_query.lower() in col.lower()]
    else:
        filtered_columns = df.columns.tolist()

    selected_columns = st.multiselect("Preguntas:", filtered_columns)

    def preprocess_column(col):
        return df[col].dropna().astype(str).str.split(",\s*").explode()

    if selected_columns:
        st.subheader("🔍 Análisis de las preguntas seleccionadas")

        if len(selected_columns) == 1:
            col = selected_columns[0]
            processed = preprocess_column(col)

            st.write(processed.value_counts())

            fig, ax = plt.subplots()
            processed.value_counts().plot(kind="bar", ax=ax)
            ax.set_title(col)
            ax.set_ylabel("Frecuencia")
            st.pyplot(fig)

        elif len(selected_columns) == 2:
            df_comb = df[selected_columns].dropna(how='any').copy()
            for col in selected_columns:
                df_comb[col] = df_comb[col].astype(str).str.split(",\s*")

            df_exploded = df_comb.copy()
            for col in selected_columns:
                df_exploded = df_exploded.explode(col)

            st.write("### Tabla de contingencia")
            pivot = pd.crosstab(index=df_exploded[selected_columns[0]],
                                columns=df_exploded[selected_columns[1]])
            st.dataframe(pivot)

            st.write("### Gráfico de barras agrupadas")
            fig, ax = plt.subplots(figsize=(10, 5))
            pivot.plot(kind="bar", ax=ax)
            ax.set_ylabel("Frecuencia")
            ax.set_title(f"{selected_columns[0]} vs {selected_columns[1]}")
            st.pyplot(fig)

        else:
            st.warning("Por ahora, el análisis combinado está disponible solo para dos columnas. Selecciona máximo dos.")
    else:
        st.info("Selecciona al menos una pregunta para ver el análisis.")
