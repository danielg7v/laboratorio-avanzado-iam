"""AccessGuard AI — app de apoyo a la decisión sobre solicitudes de acceso IAM (Zero Trust / Menor Privilegio).

- Carga `models/model.joblib` de ESTE repositorio. NO consulta Databricks ni usa credenciales.
- Recibe los códigos de la solicitud, asigna una zona (verde / amarillo / rojo) y explica la decisión con SHAP local.
- Nunca auto-deniega: lo que no es verde lo revisa una persona del área IAM.

Ejecutar desde la raíz del repo:  streamlit run app/streamlit_app.py
"""
import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from accessguard.explain import (ZONE_GREEN, ZONE_LABELS, ZONE_RED, ZONE_YELLOW, assign_zone, describe_feature,  # noqa: E402
                                 explain_request, make_explainer, unseen_codes)

MODEL_PATH = ROOT / "models" / "model.joblib"
DEMO_PATH = ROOT / "models" / "demo_requests.json"

COLUMN_LABELS = {
    "RESOURCE": "Recurso solicitado (RESOURCE)", "MGR_ID": "Gerente (MGR_ID)", "ROLE_ROLLUP_2": "Agrupación de rol 2 (ROLE_ROLLUP_2)",
    "ROLE_DEPTNAME": "Departamento (ROLE_DEPTNAME)", "ROLE_TITLE": "Cargo (ROLE_TITLE)", "ROLE_FAMILY_DESC": "Descripción de familia de rol (ROLE_FAMILY_DESC)",
}
ZONE_STYLE = {
    ZONE_GREEN: ("#1B7F3B", "#E6F4EA", "🟢 VERDE · Auto-aprobación estricta",
                 "La probabilidad supera el umbral estricto (el de 0 accesos indebidos en validación cruzada). Se puede aprobar sin revisión, dejando registro de auditoría."),
    ZONE_YELLOW: ("#8A6100", "#FFF4D6", "🟡 AMARILLO · Cola de triaje priorizada",
                  "Caso ambiguo: va a un analista IAM. Cuanto más baja la probabilidad, antes debería revisarse."),
    ZONE_RED: ("#A4262C", "#FDE7E9", "🔴 ROJO · Revisión manual",
               "Entre las solicitudes más sospechosas. Revisión manual obligatoria. El sistema **no** deniega por sí solo."),
}


@st.cache_resource
def load_bundle():
    return joblib.load(MODEL_PATH)


@st.cache_resource
def load_explainer():
    b = load_bundle()
    return make_explainer(b["pipeline"], b["shap_background"])


@st.cache_data
def load_demo() -> dict:
    return json.loads(DEMO_PATH.read_text(encoding="utf-8")) if DEMO_PATH.exists() else {}


def apply_demo():
    demo = load_demo().get(st.session_state.get("demo_choice"))
    if demo:
        for col, v in demo.items():
            st.session_state[f"in_{col}"] = int(v)


def shap_chart(top: list):
    names = [describe_feature(t["feature"]) for t in top][::-1]
    vals = [t["shap"] for t in top][::-1]
    fig, ax = plt.subplots(figsize=(7, 0.45 * len(vals) + 0.8))
    ax.barh(names, vals, color=["#1B7F3B" if v > 0 else "#A4262C" for v in vals])
    ax.axvline(0, color="#444", lw=0.8)
    ax.set_xlabel("Efecto sobre la decisión (log-odds): verde empuja a aprobar · rojo empuja a revisar")
    ax.tick_params(labelsize=8)
    plt.tight_layout()
    return fig


def main() -> None:
    st.set_page_config(page_title="AccessGuard AI", page_icon="🛡️", layout="wide")
    st.title("🛡️ AccessGuard AI — Triaje de solicitudes de acceso")
    st.caption("Herramienta de apoyo bajo Zero Trust / Menor Privilegio. **No decide por sí sola:** ante la duda, escala a un analista IAM.")

    if not MODEL_PATH.exists():
        st.error("Falta `models/model.joblib`. Ejecuta los notebooks 06 y 07 para generarlo.")
        st.stop()
    bundle, explainer = load_bundle(), load_explainer()
    pipe, t_auto, t_low = bundle["pipeline"], bundle["t_auto_strict"], bundle["t_low"]
    cols = list(bundle["input_columns"])

    with st.sidebar:
        st.header("Política de zonas")
        st.markdown(f"- 🟢 **Verde:** p > {t_auto:.3f}\n- 🟡 **Amarillo:** {t_low:.3f} ≤ p ≤ {t_auto:.3f}\n- 🔴 **Rojo:** p < {t_low:.3f}")
        st.caption(f"Modelo: {bundle['model_name']} · congelado {bundle.get('frozen_at', '—')}. p = probabilidad de que la solicitud sea aprobada.")
        hm = bundle.get("holdout_metrics", {})
        if hm:
            st.caption(f"ROC-AUC en gerentes no vistos: {hm['roc_auc']:.2f}. El modelo ordena **moderadamente**: no es un oráculo.")

    demo = load_demo()
    if demo:
        st.selectbox("Cargar un ejemplo de demostración (opcional)", list(demo), index=None, key="demo_choice", on_change=apply_demo,
                     placeholder="Escribe los códigos a mano o elige un ejemplo")

    with st.form("solicitud"):
        st.subheader("Atributos de la solicitud")
        grid = st.columns(3)
        row = {}
        for i, c in enumerate(cols):
            with grid[i % 3]:
                row[c] = st.number_input(COLUMN_LABELS.get(c, c), min_value=0, step=1, key=f"in_{c}", help="Código numérico anónimo del dataset (no es una cantidad).")
        go = st.form_submit_button("Evaluar solicitud", type="primary")

    if not go:
        st.info("Completa los códigos y pulsa **Evaluar solicitud**.")
        return

    X = pd.DataFrame([row], columns=cols).astype("int64")
    exp = explain_request(pipe, explainer, X, top=8)
    p = exp["p_approve"]
    zone = str(assign_zone([p], t_low, t_auto)[0])
    fg, bg, title, text = ZONE_STYLE[zone]

    st.markdown(f"<div style='background:{bg};border-left:8px solid {fg};padding:1rem 1.2rem;border-radius:6px'>"
                f"<div style='color:{fg};font-size:1.4rem;font-weight:700'>{title}</div></div>", unsafe_allow_html=True)
    st.markdown(text)

    c1, c2, c3 = st.columns(3)
    c1.metric("p(aprobar)", f"{p:.1%}")
    c2.metric("Zona", ZONE_LABELS[zone])
    c3.metric("Umbral verde", f"{t_auto:.1%}", delta=f"{(p - t_auto) * 100:+.1f} pts", delta_color="off")
    st.progress(float(np.clip(p, 0, 1)), text=f"Posición de la solicitud (rojo < {t_low:.2f} ≤ amarillo ≤ {t_auto:.2f} < verde)")

    unseen = unseen_codes(pipe, X)
    if unseen:
        st.warning("Códigos **nunca vistos** en el entrenamiento: " + ", ".join(unseen) + ". El modelo no tiene historial de ellos; trata el resultado con más cautela.")

    st.subheader("¿Por qué? Explicación SHAP de esta solicitud")
    st.pyplot(shap_chart(exp["top"]))
    st.caption("Barras verdes empujan hacia aprobar; rojas, hacia revisar. Las variables resumen el **historial** (frecuencias y tasas de aprobación de los códigos), "
               "no el mérito de la persona. Probabilidad base del modelo: "
               f"{1 / (1 + np.exp(-exp['base_value'])):.1%}.")
    with st.expander("Detalle numérico"):
        st.dataframe(pd.DataFrame(exp["top"]).rename(columns={"feature": "variable", "shap": "SHAP", "value": "valor"}), hide_index=True)
    with st.expander("Uso responsable"):
        st.markdown("- Apoya, no reemplaza, la decisión de un analista IAM; nunca auto-deniega.\n"
                    "- Entrenado con el dataset Amazon Employee Access (códigos anónimos): no usar con otros datos sin revalidar.\n"
                    "- 0 accesos indebidos observados no prueba FPR = 0 %: en la reserva la zona verde dejó pasar "
                    f"{bundle.get('holdout_metrics', {}).get('strict_fp', '—')} accesos indebidos.\n"
                    "- Faltan datos de criticidad del recurso y de tiempos de espera reales (SLA).")


if __name__ == "__main__":
    main()
