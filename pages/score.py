import streamlit as st
import sys
sys.path.insert(0, ".")
from utils import (load_data, calc_custom_score, score_detail_table,
                   ROST_SCORE, SCHADEN_SCORE, REPARATUR_SCORE,
                   FAHRBEREIT_SCORE, ZUSTAND_SCORE, score_hu)

st.set_page_config(page_title="Score-Analyse", layout="wide")
st.title("📊 Score-Analyse & Gewichtung")

df = load_data()

st.subheader("⚖️ Kategorie-Gewichtung")
col1, col2, col3 = st.columns(3)
with col1:
    w_tech  = st.slider("Technischer Zustand", 0, 10, 3)
    st.caption("Rost · Schäden · Reparaturstau")
with col2:
    w_fahr  = st.slider("Fahrbereitschaft", 0, 10, 3)
    st.caption("Fahrbereit · HU · Fahrzeugzustand")
with col3:
    w_preis = st.slider("Preis / Leistung", 0, 10, 3)
    st.caption("Preis · KM · Baujahr")

st.subheader("⚙️ Feld-Gewichtung")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Technisch**")
    w_rost    = st.slider("Rost",          0, 10, 3)
    w_schaden = st.slider("Schäden",       0, 10, 3)
    w_repa    = st.slider("Reparaturstau", 0, 10, 3)
with c2:
    st.markdown("**Fahrbereitschaft**")
    w_fahr2   = st.slider("Fahrbereit",       0, 10, 3)
    w_hu      = st.slider("HU",               0, 10, 3)
    w_zustand = st.slider("Fahrzeugzustand",  0, 10, 3)
with c3:
    st.markdown("**Preis / Leistung**")
    w_preis2  = st.slider("Preis",           0, 10, 3)
    w_km      = st.slider("Kilometerstand",  0, 10, 3)
    w_jahr    = st.slider("Baujahr",         0, 10, 3)

if st.button("🔄 Score neu berechnen"):
    weights = {
        "w_tech": w_tech, "w_fahr": w_fahr, "w_preis": w_preis,
        "w_rost": w_rost, "w_schaden": w_schaden, "w_repa": w_repa,
        "w_fahr2": w_fahr2, "w_hu": w_hu, "w_zustand": w_zustand,
        "w_preis2": w_preis2, "w_km": w_km, "w_jahr": w_jahr,
    }
    df["score_custom"] = df.apply(lambda r: calc_custom_score(r, df, weights), axis=1)
    st.session_state["df_scored"] = df
    st.success("Score neu berechnet!")

df_scored = st.session_state.get("df_scored", df)
score_col  = "score_custom" if "score_custom" in df_scored.columns else "score_gesamt"

st.divider()
st.subheader("🏆 Ranking")
anzahl = st.radio("Anzeigen", ["Top 10", "Alle"], horizontal=True)
n = 10 if anzahl == "Top 10" else len(df_scored)
top = df_scored.sort_values(score_col, ascending=False).head(n)

for _, r in top.iterrows():
    with st.expander(f"**{r['titel']}** — Score: {r[score_col]:.1f} | {r['preis_num']:.0f}€ | {r['km_num']:,.0f}km"):
        detail = score_detail_table(r, df_scored)
        st.dataframe(
            detail,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Punkte": st.column_config.ProgressColumn(
                    "Punkte", min_value=0, max_value=10, format="%.1f"),
            }
        )
        st.markdown(f"[🔗 Zur Anzeige]({r['url']})")
