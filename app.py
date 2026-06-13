import streamlit as st
import pandas as pd
import sys
import requests
from math import radians, sin, cos, sqrt, atan2
sys.path.insert(0, ".")
from utils import (load_data, calc_custom_score, score_detail_table,
                   ROST_SCORE, SCHADEN_SCORE, REPARATUR_SCORE,
                   FAHRBEREIT_SCORE, ZUSTAND_SCORE, score_hu)

st.set_page_config(page_title="VW T4 Anzeigen", layout="wide")
st.title("🚐 VW T4 Kleinanzeigen")

@st.cache_data
def get_coords(plz):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"postalcode": plz, "countrycodes": "de", "format": "json", "limit": 1},
            headers={"User-Agent": "VWT4App/1.0"},
            timeout=10
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

df = load_data()

# --- Sidebar Filter ---
st.sidebar.header("🔍 Filter")

preis_min, preis_max = int(df["preis_num"].min(skipna=True)), int(df["preis_num"].max(skipna=True))
preis_range = st.sidebar.slider("Preis (€)", preis_min, preis_max, (preis_min, preis_max), step=50)

km_min, km_max = int(df["km_num"].min()), int(df["km_num"].max())
km_range = st.sidebar.slider("Kilometerstand", km_min, km_max, (km_min, km_max), step=5000)

jahr_min, jahr_max = int(df["jahr"].min()), int(df["jahr"].max())
jahr_range = st.sidebar.slider("Baujahr", jahr_min, jahr_max, (jahr_min, jahr_max), step=1)

ps_min = int(df["ps_num"].min(skipna=True))
ps_max = int(df["ps_num"].max(skipna=True))
ps_range = st.sidebar.slider("Leistung (PS)", ps_min, ps_max, (ps_min, ps_max), step=1)

hu_optionen = sorted([x for x in df["hu_monat_num"].unique() if x != "unbekannt"])
hu_filter = st.sidebar.multiselect("HU bis (frühestens)", hu_optionen)

rost_filter = st.sidebar.multiselect("Rost", ["vorhanden", "nicht vorhanden", "unbekannt"])
fahrbereit_filter = st.sidebar.multiselect("Fahrbereit", ["ja", "nein", "eingeschraenkt", "unbekannt"])
reparaturstau_filter = st.sidebar.multiselect("Reparaturstau", ["ja", "nein", "unbekannt"])
vorbesitzer_filter = st.sidebar.multiselect("Vorbesitzer", ["privat", "gewerblich", "unbekannt"])

zustand_optionen = sorted(df["Fahrzeugzustand"].dropna().unique().tolist())
zustand_filter = st.sidebar.multiselect("Fahrzeugzustand", zustand_optionen)

kraftstoff_optionen = sorted(df["Kraftstoffart"].dropna().unique().tolist())
kraftstoff_filter = st.sidebar.multiselect("Kraftstoffart", kraftstoff_optionen)

getriebe_optionen = sorted(df["Getriebe"].dropna().unique().tolist())
getriebe_filter = st.sidebar.multiselect("Getriebe", getriebe_optionen)

farbe_optionen = sorted(df["Außenfarbe"].dropna().unique().tolist())
farbe_filter = st.sidebar.multiselect("Außenfarbe", farbe_optionen)

fahrzeugart_optionen = sorted(df["fahrzeugart"].dropna().unique().tolist())
fahrzeugart_filter = st.sidebar.multiselect("Fahrzeugart", fahrzeugart_optionen)

st.sidebar.subheader("🔧 Ausstattung")
hat_ahk = st.sidebar.checkbox("Anhängerkupplung (AHK)")
hat_camper = st.sidebar.checkbox("Camper-Ausbau")
hat_standheizung = st.sidebar.checkbox("Standheizung")
hat_hochdach = st.sidebar.checkbox("Hochdach")
hat_lkw = st.sidebar.checkbox("LKW-Zulassung")

st.sidebar.subheader("📍 Standort")
home_plz = st.sidebar.text_input("Mein Standort (PLZ)", value="04109")
home_coords = get_coords(home_plz) if home_plz else None
if home_coords:
    st.sidebar.caption(f"✓ {home_plz} erkannt")
else:
    st.sidebar.caption("⚠ PLZ nicht gefunden")
max_entfernung = st.sidebar.slider("Max. Entfernung (km)", 0, 800, 800, step=10)

ort_suche = st.sidebar.text_input("Standort enthält (PLZ oder Ort)")
freitext = st.sidebar.text_input("Freitext-Suche (Titel / Beschreibung)")
schaeden_suche = st.sidebar.text_input("Schäden enthält")
positive_suche = st.sidebar.text_input("Positive Signale enthält")
negative_suche = st.sidebar.text_input("Negative Signale enthält")

st.sidebar.header("↕️ Sortierung")
sort_col = st.sidebar.selectbox("Sortieren nach", [
    "preis_num", "km_num", "jahr", "entfernung_km", "score_gesamt",
    "score_technisch", "score_fahrbereit", "score_preis_leistung"
])
sort_asc = st.sidebar.radio("Reihenfolge", ["Aufsteigend", "Absteigend"]) == "Aufsteigend"

# --- Filterlogik ---
mask = (
    (df["preis_num"].between(*preis_range) | df["preis_num"].isna()) &
    df["km_num"].between(*km_range) &
    df["jahr"].between(*jahr_range) &
    (df["ps_num"].between(*ps_range) | df["ps_num"].isna())
)

if hu_filter:
    mask &= df["hu_monat_num"].isin(hu_filter)
if rost_filter:
    mask &= df["rost_hinweise"].isin(rost_filter)
if fahrbereit_filter:
    mask &= df["fahrbereit"].isin(fahrbereit_filter)
if reparaturstau_filter:
    mask &= df["reparaturstau"].isin(reparaturstau_filter)
if vorbesitzer_filter:
    mask &= df["vorbesitzer_nutzung"].isin(vorbesitzer_filter)
if zustand_filter:
    mask &= df["Fahrzeugzustand"].isin(zustand_filter)
if kraftstoff_filter:
    mask &= df["Kraftstoffart"].isin(kraftstoff_filter)
if getriebe_filter:
    mask &= df["Getriebe"].isin(getriebe_filter)
if farbe_filter:
    mask &= df["Außenfarbe"].isin(farbe_filter)
if fahrzeugart_filter:
    mask &= df["fahrzeugart"].isin(fahrzeugart_filter)
if hat_ahk:
    mask &= df["hat_ahk"] == True
if hat_camper:
    mask &= df["hat_camper"] == True
if hat_standheizung:
    mask &= df["hat_standheizung"] == True
if hat_hochdach:
    mask &= df["hat_hochdach"] == True
if hat_lkw:
    mask &= df["hat_lkw_zulassung"] == True
if home_coords and max_entfernung < 800 and "entfernung_km" in df.columns:
    mask &= (df["entfernung_km"] <= max_entfernung) | df["entfernung_km"].isna()
if ort_suche:
    mask &= df["Ort"].str.contains(ort_suche, case=False, na=False)
if freitext:
    mask &= (
        df["titel"].str.contains(freitext, case=False, na=False) |
        df["beschreibung"].str.contains(freitext, case=False, na=False)
    )
if schaeden_suche:
    mask &= df["schadenshinweise"].str.contains(schaeden_suche, case=False, na=False)
if positive_suche:
    mask &= df["positive_signale"].str.contains(positive_suche, case=False, na=False)
if negative_suche:
    mask &= df["negative_signale"].str.contains(negative_suche, case=False, na=False)

filtered = df[mask].sort_values(sort_col, ascending=sort_asc, na_position="last")

# --- Tabs ---
tab1, tab2 = st.tabs(["📋 Anzeigen", "📊 Score-Analyse"])

with tab1:
    st.markdown(f"**{len(filtered)} Anzeigen gefunden**")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("⌀ Preis", f"{filtered['preis_num'].mean():.0f} €")
        st.metric("Median Preis", f"{filtered['preis_num'].median():.0f} €")
    with m2:
        st.metric("⌀ Kilometerstand", f"{filtered['km_num'].mean():,.0f} km")
        st.metric("Median KM", f"{filtered['km_num'].median():,.0f} km")
    with m3:
        st.metric("⌀ Baujahr", f"{filtered['jahr'].mean():.0f}")
        st.metric("Median Baujahr", f"{filtered['jahr'].median():.0f}")

    st.divider()
    ansicht = st.radio("Ansicht", ["Tabelle", "Karten"], horizontal=True)

    tabellen_spalten = [
        "titel", "preis_num", "km_num", "jahr", "Leistung",
        "Kraftstoffart", "Getriebe", "Fahrzeugzustand", "Außenfarbe",
        "HU bis", "Ort", "entfernung_km", "rost_hinweise", "fahrbereit",
        "reparaturstau", "fahrzeugart",
        "score_technisch", "score_fahrbereit", "score_preis_leistung", "score_gesamt",
        "url"
    ]

    if ansicht == "Tabelle":
        anzeige_df = filtered[[c for c in tabellen_spalten if c in filtered.columns]].copy()
        st.dataframe(
            anzeige_df,
            use_container_width=True,
            column_config={
                "url": st.column_config.LinkColumn("Link"),
                "preis_num": st.column_config.NumberColumn("Preis (€)", format="%.0f €"),
                "km_num": st.column_config.NumberColumn("KM", format="%.0f km"),
                "entfernung_km": st.column_config.NumberColumn("Entfernung", format="%.0f km"),
                "score_gesamt": st.column_config.NumberColumn("Score ∅", format="%.1f"),
                "score_technisch": st.column_config.NumberColumn("Tech", format="%.1f"),
                "score_fahrbereit": st.column_config.NumberColumn("Fahr", format="%.1f"),
                "score_preis_leistung": st.column_config.NumberColumn("P/L", format="%.1f"),
            },
            hide_index=True
        )
    else:
        cols_per_row = 2
        rows = [filtered.iloc[i:i+cols_per_row] for i in range(0, len(filtered), cols_per_row)]
        for row in rows:
            cols = st.columns(cols_per_row)
            for col, (_, r) in zip(cols, row.iterrows()):
                with col:
                    with st.container(border=True):
                        st.markdown(f"### [{r['titel']}]({r['url']})")
                        dist = f" | 📍 {r['entfernung_km']:.0f} km" if pd.notna(r.get('entfernung_km')) else ""
                        st.markdown(f"💶 **{r['preis_num']:.0f} €** | 🛣️ {r['km_num']:,.0f} km | 📅 {int(r['jahr']) if pd.notna(r['jahr']) else '?'}{dist}")
                        st.markdown(f"⚙️ {r.get('Kraftstoffart','?')} | {r.get('Getriebe','?')} | {r.get('Leistung','?')}")
                        st.markdown(f"🔩 HU: {r.get('HU bis','?')} | 🚗 {r.get('fahrzeugart','?')}")
                        badges = []
                        if r.get("rost_hinweise") == "vorhanden": badges.append("🟠 Rost")
                        if r.get("hat_camper"): badges.append("🏕️ Camper")
                        if r.get("hat_ahk"): badges.append("🔗 AHK")
                        if r.get("hat_standheizung"): badges.append("🔥 Standh.")
                        if r.get("hat_hochdach"): badges.append("🏠 Hochdach")
                        if r.get("hat_lkw_zulassung"): badges.append("🚛 LKW")
                        if r.get("negative_signale") not in ["keine", "unbekannt"]:
                            badges.append(f"⚠️ {r.get('negative_signale','')}")
                        if badges:
                            st.markdown(" | ".join(badges))
                        with st.expander("📊 Scores & Details"):
                            s1, s2, s3, s4 = st.columns(4)
                            s1.metric("Gesamt", f"{r.get('score_gesamt',0):.1f}")
                            s2.metric("Technik", f"{r.get('score_technisch',0):.1f}")
                            s3.metric("Fahrbereit", f"{r.get('score_fahrbereit',0):.1f}")
                            s4.metric("Preis/L", f"{r.get('score_preis_leistung',0):.1f}")
                            st.write("**Fahrbereit:**", r.get("fahrbereit","–"))
                            st.write("**Rost:**", r.get("rost_hinweise","–"))
                            st.write("**Reparaturstau:**", r.get("reparaturstau","–"))
                            st.write("**Positive Signale:**", r.get("positive_signale","–"))
                            st.write("**Schäden:**", r.get("schadenshinweise","–"))
                            st.write("**Ausstattung:**", r.get("ausstattung_extra","–"))

with tab2:
    st.subheader("⚖️ Gewichtung anpassen")
    col1, col2, col3 = st.columns(3)
    with col1:
        w_tech = st.slider("Technischer Zustand", 0, 10, 3)
        st.caption("Rost · Schäden · Reparaturstau")
        w_rost    = st.slider("Rost",          0, 10, 3)
        w_schaden = st.slider("Schäden",       0, 10, 3)
        w_repa    = st.slider("Reparaturstau", 0, 10, 3)
    with col2:
        w_fahr = st.slider("Fahrbereitschaft", 0, 10, 3)
        st.caption("Fahrbereit · HU · Fahrzeugzustand")
        w_fahr2   = st.slider("Fahrbereit",      0, 10, 3)
        w_hu      = st.slider("HU",              0, 10, 3)
        w_zustand = st.slider("Fahrzeugzustand", 0, 10, 3)
    with col3:
        w_preis = st.slider("Preis / Leistung", 0, 10, 3)
        st.caption("Preis · KM · Baujahr")
        w_preis2  = st.slider("Preis",          0, 10, 3)
        w_km      = st.slider("Kilometerstand", 0, 10, 3)
        w_jahr    = st.slider("Baujahr",        0, 10, 3)

    if st.button("🔄 Score neu berechnen"):
        weights = {
            "w_tech": w_tech, "w_fahr": w_fahr, "w_preis": w_preis,
            "w_rost": w_rost, "w_schaden": w_schaden, "w_repa": w_repa,
            "w_fahr2": w_fahr2, "w_hu": w_hu, "w_zustand": w_zustand,
            "w_preis2": w_preis2, "w_km": w_km, "w_jahr": w_jahr,
        }
        filtered["score_custom"] = filtered.apply(
            lambda r: calc_custom_score(r, filtered, weights), axis=1)
        st.session_state["filtered_scored"] = filtered
        st.success(f"Score neu berechnet für {len(filtered)} gefilterte Anzeigen!")

    scored = st.session_state.get("filtered_scored", filtered)
    score_col = "score_custom" if "score_custom" in scored.columns else "score_gesamt"

    st.divider()
    st.subheader("🏆 Ranking")
    anzahl = st.radio("Anzeigen", ["Top 10", "Alle"], horizontal=True)
    n = 10 if anzahl == "Top 10" else len(scored)
    top = scored.sort_values(score_col, ascending=False).head(n)

    for _, r in top.iterrows():
        dist = f" | 📍 {r['entfernung_km']:.0f} km" if pd.notna(r.get('entfernung_km')) else ""
        with st.expander(f"**{r['titel']}** — Score: {r[score_col]:.1f} | {r['preis_num']:.0f}€ | {r['km_num']:,.0f}km{dist}"):
            detail = score_detail_table(r, scored)
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
