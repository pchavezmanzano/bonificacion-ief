"""
Proyecto simple: consumir API pública (datos.gob.cl), limpiar y analizar con pandas,
graficar con matplotlib, y ofrecer una UI básica con Streamlit.

Ejecución:
- Consola:   python app.py
- UI Web:    streamlit run app.py
"""

import json, re, requests, pandas as pd
from pandas.api.types import is_string_dtype
import matplotlib
matplotlib.use("Agg")  # backend no interactivo
import matplotlib.pyplot as plt

API_URL = "https://datos.gob.cl/api/3/action/datastore_search"
API_PARAMS = {"resource_id": "ecc2be79-efc6-47c3-91c9-38df96fc0b06", "limit": 5000}


# ---------------- 1) Descarga ----------------
def fetch_data(url: str, params: dict, timeout: int = 30) -> dict:
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Error API:", e)
        return {}


# ---------------- 2) Limpieza ----------------
def normalize_cols(cols):
    return [re.sub(r"[^a-z0-9_]+", "", c.lower().replace(" ", "_")) for c in cols]

def to_float_cl(x):
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if s in {"", "-", "nan", "none", "null"}:
        return pd.NA
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return pd.NA

def records_to_df(data: dict) -> pd.DataFrame:
    if not isinstance(data, dict) or "result" not in data:
        return pd.DataFrame()
    df = pd.DataFrame(data["result"].get("records", []))
    if df.empty:
        return df

    # normaliza columnas
    df.columns = normalize_cols(df.columns)

    # normaliza TODAS las columnas de texto: "", none/null/nan -> NA
    for c in df.columns:
        if is_string_dtype(df[c]) or df[c].dtype == object:
            s = df[c].astype(str).str.strip()
            s_low = s.str.lower()
            df[c] = s.mask(s_low.isin(["", "none", "null", "nan"]), pd.NA)

    # limpieza específica claves
    for c in ("comuna", "region"):
        if c in df.columns:
            df[c] = df[c].astype("string").str.replace("\u00a0", "", regex=False).str.strip()

    # convierte numéricas en formato chileno
    candidates = [col for col in df.columns if any(k in col for k in ["mto", "monto", "hombre", "mujer", "no", "cantidad"])]
    for c in candidates:
        if is_string_dtype(df[c]) or df[c].dtype == object:
            df[c] = df[c].map(to_float_cl)

    # monto total si falta
    if "monto_m" not in df.columns and {"mtohombre", "mtomujer"}.issubset(df.columns):
        df["monto_m"] = df["mtohombre"].fillna(0) + df["mtomujer"].fillna(0)

    return df


# ---------------- 3) Reporte -----------------
def console_report(df: pd.DataFrame):
    if df.empty:
        print("DF vacío.")
        return
    print("Head:\n", df.head(), "\n")
    print("Forma:", df.shape, "\n")
    print("Columnas:", list(df.columns), "\n")

    th = float(df["mtohombre"].sum()) if "mtohombre" in df.columns else 0.0
    tm = float(df["mtomujer"].sum()) if "mtomujer" in df.columns else 0.0
    tg = float(df["monto_m"].sum()) if "monto_m" in df.columns else th + tm
    print(f"Tot Hombres: {th:,.0f} | Tot Mujeres: {tm:,.0f} | Tot General: {tg:,.0f}\n")

    if {"comuna", "monto_m"}.issubset(df.columns):
        df_ok = df[df["comuna"].notna()]
        top10 = (
            df_ok[["comuna", "monto_m"]]
            .groupby("comuna")["monto_m"].sum()
            .sort_values(ascending=False).head(10)
        )
        print("Top 10 comunas por monto total:\n", top10, "\n")


# ---------------- 4) Gráficos ----------------
def make_charts(df: pd.DataFrame):
    if df.empty:
        print("Sin datos para graficar.")
        return

    # Barras: top 10 por monto total (excluye nulos y 'None')
    if {"comuna", "monto_m"}.issubset(df.columns):
        df_ok = df[df["comuna"].notna()]
        top = (
            df_ok[["comuna", "monto_m"]]
            .groupby("comuna")["monto_m"].sum()
            .sort_values(ascending=False).head(10)
        )
        plt.figure(figsize=(12, 6))
        top.plot(kind="bar")
        plt.title("Top 10 comunas por monto total")
        plt.xlabel("Comuna"); plt.ylabel("Monto total")
        plt.tight_layout(); plt.savefig("grafico_barras.png"); print("OK: grafico_barras.png")
    else:
        print("Faltan columnas para barras.")

    # Líneas: hombres vs mujeres
    if {"comuna", "mtohombre", "mtomujer", "monto_m"}.issubset(df.columns):
        df_ok = df[df["comuna"].notna()]
        comp = (
            df_ok[["comuna", "mtohombre", "mtomujer", "monto_m"]]
            .groupby("comuna").sum()
            .sort_values(by="monto_m", ascending=False).head(20)
        )
        plt.figure(figsize=(14, 6))
        plt.plot(comp.index.astype(str), comp["mtohombre"], marker="o", label="Hombres")
        plt.plot(comp.index.astype(str), comp["mtomujer"], marker="s", label="Mujeres")
        plt.title("Comparación montos: Hombres vs Mujeres por comuna")
        plt.xlabel("Comuna"); plt.ylabel("Monto"); plt.xticks(rotation=45, ha="right"); plt.legend()
        plt.tight_layout(); plt.savefig("grafico_lineas.png"); print("OK: grafico_lineas.png")
    else:
        print("Faltan columnas para líneas.")


# ---------------- 5) UI Streamlit -----------
# Diccionario de códigos de región a nombres oficiales
REGIONES_CHILE = {
    "1": "Tarapacá",
    "2": "Antofagasta",
    "3": "Atacama",
    "4": "Coquimbo",
    "5": "Valparaíso",
    "6": "O'Higgins",
    "7": "Maule",
    "8": "Biobío",
    "9": "La Araucanía",
    "10": "Los Lagos",
    "11": "Aysén",
    "12": "Magallanes",
    "13": "Metropolitana de Santiago",
    "14": "Los Ríos",
    "15": "Arica y Parinacota",
    "16": "Ñuble"
}

def run_streamlit_ui(df: pd.DataFrame) -> None:
    try:
        import streamlit as st
    except Exception:
        return

    st.title("Bonificación Ingreso Ético Familiar · datos.gob.cl")
    st.caption("Exploración simple · Python + pandas + matplotlib + Streamlit")

    if df.empty:
        st.warning("Sin datos.")
        return

    region_col = "region" if "region" in df.columns else None
    comuna_col = "comuna" if "comuna" in df.columns else None

    # Filtro región mostrando nombres
    if region_col:
        regiones_codigos = sorted(
            x for x in df[region_col].dropna().astype(str).str.strip().unique()
            if x.lower() != "none"
        )
        regiones_nombres = [REGIONES_CHILE.get(c, f"Región {c}") for c in regiones_codigos]
        opciones = ["(todas)"] + regiones_nombres

        pick = st.selectbox("Filtrar por región:", opciones, key="region_selector")

        # Si selecciona "(todas)" mostramos todo
        if pick == "(todas)":
            work = df
        else:
            # Buscar código por nombre seleccionado
            codigo_region = next((c for c, n in REGIONES_CHILE.items() if n == pick), None)
            work = df[df[region_col].astype(str).str.strip() == str(codigo_region)]
    else:
        st.info("No hay columna de región.")
        work = df

    st.subheader("Datos")
    st.dataframe(work)

    # Métricas principales
    th = float(work["mtohombre"].sum()) if "mtohombre" in work.columns else 0.0
    tm = float(work["mtomujer"].sum()) if "mtomujer" in work.columns else 0.0
    tg = float(work["monto_m"].sum()) if "monto_m" in work.columns else th + tm

    c1, c2, c3 = st.columns(3)
    c1.metric("Monto hombres", f"{th:,.0f}".replace(",", "."))
    c2.metric("Monto mujeres", f"{tm:,.0f}".replace(",", "."))
    c3.metric("Monto total", f"{tg:,.0f}".replace(",", "."))

    # Top 20 comunas por monto (excluye nulos)
    if comuna_col and "monto_m" in work.columns:
        df_ok = work[work[comuna_col].notna()]
        top20 = (
            df_ok[[comuna_col, "monto_m"]]
            .groupby(comuna_col)["monto_m"]
            .sum()
            .sort_values(ascending=False)
            .head(20)
        )
        titulo = (
            "Top 20 comunas por monto total (todas las regiones)"
            if pick == "(todas)"
            else f"Top 20 comunas por monto total · {pick}"
        )
        st.subheader(titulo)
        st.bar_chart(top20.sort_values(ascending=True))


# ---------------- Main ----------------------
if __name__ == "__main__":
    print("Descargando datos...")
    data = fetch_data(API_URL, API_PARAMS)
    if data:
        try:
            print("Fragmento JSON:\n", json.dumps(data, ensure_ascii=False, indent=2)[:1000], "\n")
        except Exception:
            pass
    df = records_to_df(data)
    console_report(df)
    make_charts(df)
    run_streamlit_ui(df)
    print("\nPara UI: streamlit run app.py")
