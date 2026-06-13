import streamlit as st
import pandas as pd

st.set_page_config(page_title="VW T4 Anzeigen", layout="wide")
st.title("🚐 VW T4 Kleinanzeigen – Filter & Suche")

import sys
sys.path.insert(0, ".")
from utils import load_data
df = load_data()

# --- Sidebar Filter ---
st.sidebar.header("🔍 Filter")

preis_min, preis_max = int(df["preis_num"].min()), int(df["preis_num"].max())
preis_range = st.sidebar.slider("Preis (€)", preis_min, preis_max, (preis_min, preis_max), step=50)

km_min, km_max = int(df["km_num"].min()), int(df["km_num"].max())
km_range = st.sidebar.slider("Kilometerstand", km_min, km_max, (km_min, km_max), step=5000)

jahr_min, jahr_max = int(df["jahr"].min()), int(df["jahr"].max())
jahr_range = st.sidebar.slider("Baujahr", jahr_min, jahr_max, (jahr_min, jahr_max), step=1)

ps_min = int(df["ps_num"].min(skipna=True))
ps_max = int(df["ps_num"].max(skipna=True))
ps_range = st.sidebar.slider("Leistung (PS)", ps_min, ps_max, (ps_min, ps_max), step=1)

hu_optionen = sorted([x for x in df["hu_monat_num"].unique() if x != "unbekannt"])
hu_filter = st.sidebar.selectbox("HU bis (frühestens)", ["alle"] + hu_optionen)

rost_filter = st.sidebar.selectbox("Rost", ["alle", "vorhanden", "nicht vorhanden", "unbekannt"])
fahrbereit_filter = st.sidebar.selectbox("Fahrbereit", ["alle", "ja", "nein", "eingeschraenkt", "unbekannt"])
reparaturstau_filter = st.sidebar.selectbox("Reparaturstau", ["alle", "ja", "nein", "unbekannt"])
vorbesitzer_filter = st.sidebar.selectbox("Vorbesitzer", ["alle", "privat", "gewerblich", "unbekannt"])

zustand_optionen = ["alle"] + sorted(df["Fahrzeugzustand"].dropna().unique().tolist())
zustand_filter = st.sidebar.selectbox("Fahrzeugzustand", zustand_optionen)

kraftstoff_optionen = ["alle"] + sorted(df["Kraftstoffart"].dropna().unique().tolist())
kraftstoff_filter = st.sidebar.selectbox("Kraftstoffart", kraftstoff_optionen)

getriebe_optionen = ["alle"] + sorted(df["Getriebe"].dropna().unique().tolist())
getriebe_filter = st.sidebar.selectbox("Getriebe", getriebe_optionen)

farbe_optionen = ["alle"] + sorted(df["Außenfarbe"].dropna().unique().tolist())
farbe_filter = st.sidebar.selectbox("Außenfarbe", farbe_optionen)

fahrzeugart_optionen = ["alle"] + sorted(df["fahrzeugart"].dropna().unique().tolist())
fahrzeugart_filter = st.sidebar.selectbox("Fahrzeugart", fahrzeugart_optionen)

st.sidebar.subheader("🔧 Ausstattung")
hat_ahk = st.sidebar.checkbox("Anhängerkupplung (AHK)")
hat_camper = st.sidebar.checkbox("Camper-Ausbau")
hat_standheizung = st.sidebar.checkbox("Standheizung")
hat_hochdach = st.sidebar.checkbox("Hochdach")
hat_lkw = st.sidebar.checkbox("LKW-Zulassung")

ort_suche = st.sidebar.text_input("Standort enthält (PLZ oder Ort)")
freitext = st.sidebar.text_input("Freitext-Suche (Titel / Beschreibung)")
schaeden_suche = st.sidebar.text_input("Schäden enthält")
positive_suche = st.sidebar.text_input("Positive Signale enthält")
negative_suche = st.sidebar.text_input("Negative Signale enthält")

st.sidebar.header("↕️ Sortierung")
sort_col = st.sidebar.selectbox("Sortieren nach", [
    "preis_num", "km_num", "jahr", "score_gesamt",
    "score_technisch", "score_fahrbereit", "score_preis_leistung"
])
sort_asc = st.sidebar.radio("Reihenfolge", ["Aufsteigend", "Absteigend"]) == "Aufsteigend"

# --- Filterlogik ---
mask = (
    df["preis_num"].between(*preis_range) &
    df["km_num"].between(*km_range) &
    df["jahr"].between(*jahr_range) &
    (df["ps_num"].between(*ps_range) | df["ps_num"].isna())
)

if hu_filter != "alle":
    mask &= df["hu_monat_num"] >= hu_filter

if rost_filter != "alle":
    mask &= df["rost_hinweise"] == rost_filter

if fahrbereit_filter != "alle":
    mask &= df["fahrbereit"] == fahrbereit_filter

if reparaturstau_filter != "alle":
    mask &= df["reparaturstau"] == reparaturstau_filter

if vorbesitzer_filter != "alle":
    mask &= df["vorbesitzer_nutzung"] == vorbesitzer_filter

if zustand_filter != "alle":
    mask &= df["Fahrzeugzustand"] == zustand_filter

if kraftstoff_filter != "alle":
    mask &= df["Kraftstoffart"] == kraftstoff_filter

if getriebe_filter != "alle":
    mask &= df["Getriebe"] == getriebe_filter

if farbe_filter != "alle":
    mask &= df["Außenfarbe"] == farbe_filter

if fahrzeugart_filter != "alle":
    mask &= df["fahrzeugart"] == fahrzeugart_filter

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

filtered = df[mask].sort_values(sort_col, ascending=sort_asc)

# --- Metriken ---
st.markdown(f"**{len(filtered)} Anzeigen gefunden**")

st.subheader("📊 Statistiken (gefilterte Anzeigen)")
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

# --- Ansicht ---
ansicht = st.radio("Ansicht", ["Tabelle", "Karten"], horizontal=True)

tabellen_spalten = [
    "titel", "preis_num", "km_num", "jahr", "Leistung",
    "Kraftstoffart", "Getriebe", "Fahrzeugzustand", "Außenfarbe",
    "HU bis", "Ort", "rost_hinweise", "fahrbereit", "reparaturstau",
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
            "score_gesamt": st.column_config.NumberColumn("Score ∅", format="%.1f"),
            "score_technisch": st.column_config.NumberColumn("Score Tech", format="%.1f"),
            "score_fahrbereit": st.column_config.NumberColumn("Score Fahr", format="%.1f"),
            "score_preis_leistung": st.column_config.NumberColumn("Score P/L", format="%.1f"),
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
                    st.markdown(f"💶 **{r['preis_num']:.0f} €** &nbsp;|&nbsp; 🛣️ {r['km_num']:,.0f} km &nbsp;|&nbsp; 📅 {int(r['jahr']) if pd.notna(r['jahr']) else '?'}")
                    st.markdown(f"⚙️ {r.get('Kraftstoffart','?')} | {r.get('Getriebe','?')} | {r.get('Leistung','?')}")
                    st.markdown(f"🎨 {r.get('Außenfarbe','?')} | 🔧 {r.get('Fahrzeugzustand','?')}")
                    st.markdown(f"📍 {r.get('Ort','?')} &nbsp;|&nbsp; 🔩 HU: {r.get('HU bis','?')}")

                    badges = []
                    if r.get("rost_hinweise") == "vorhanden": badges.append("🟠 Rost")
                    if r.get("hat_camper"): badges.append("🏕️ Camper")
                    if r.get("hat_ahk"): badges.append("🔗 AHK")
                    if r.get("hat_standheizung"): badges.append("🔥 Standheizung")
                    if r.get("hat_hochdach"): badges.append("🏠 Hochdach")
                    if r.get("hat_lkw_zulassung"): badges.append("🚛 LKW")
                    if r.get("negative_signale") not in ["keine", "unbekannt"]:
                        badges.append(f"⚠️ {r.get('negative_signale','')}")
                    if badges:
                        st.markdown(" &nbsp; ".join(badges))

                    with st.expander("📊 Scores & Details"):
                        s1, s2, s3, s4 = st.columns(4)
                        s1.metric("Gesamt", f"{r.get('score_gesamt', 0):.1f}")
                        s2.metric("Technik", f"{r.get('score_technisch', 0):.1f}")
                        s3.metric("Fahrbereit", f"{r.get('score_fahrbereit', 0):.1f}")
                        s4.metric("Preis/L", f"{r.get('score_preis_leistung', 0):.1f}")
                        st.write("**Fahrbereit:**", r.get("fahrbereit", "–"))
                        st.write("**Rost:**", r.get("rost_hinweise", "–"))
                        st.write("**Reparaturstau:**", r.get("reparaturstau", "–"))
                        st.write("**Positive Signale:**", r.get("positive_signale", "–"))
                        st.write("**Schäden:**", r.get("schadenshinweise", "–"))
                        st.write("**Ausstattung:**", r.get("ausstattung_extra", "–"))
                        st.write("**Umbauten:**", r.get("umbauten", "–"))
