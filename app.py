import streamlit as st
import pandas as pd
import ast
from datetime import datetime

st.set_page_config(page_title="VW T4 Anzeigen", layout="wide")
st.title("🚐 VW T4 Kleinanzeigen – Filter & Suche")

# --- Daten laden ---
@st.cache_data
def load_data():
    df = pd.read_csv("/home/scardia/Projekte/Transporter/output_final.csv")

    # Numerische Felder sicherstellen
    df["preis_num"] = pd.to_numeric(df["preis_num"], errors="coerce")
    df["km_num"] = pd.to_numeric(df["km_num"], errors="coerce")
    df["jahr"] = pd.to_numeric(df["jahr"], errors="coerce")

    # HU-Datum parsen (z.B. "November 2026" → datetime)
    def parse_hu(val):
        try:
            return pd.to_datetime(val, format="%B %Y", locale="de_DE")
        except:
            try:
                return pd.to_datetime(val)
            except:
                return pd.NaT

    df["hu_datum"] = df["HU bis"].apply(parse_hu)
    df["hu_monat_num"] = df["hu_datum"].apply(lambda x: x.strftime("%Y-%m") if pd.notna(x) else "unbekannt")

    return df

df = load_data()

# --- Sidebar Filter ---
st.sidebar.header("🔍 Filter")

# Preis
preis_min, preis_max = int(df["preis_num"].min()), int(df["preis_num"].max())
preis_range = st.sidebar.slider("Preis (€)", preis_min, preis_max, (preis_min, preis_max), step=50)

# Kilometerstand
km_min, km_max = int(df["km_num"].min()), int(df["km_num"].max())
km_range = st.sidebar.slider("Kilometerstand", km_min, km_max, (km_min, km_max), step=5000)

# Baujahr
jahr_min, jahr_max = int(df["jahr"].min()), int(df["jahr"].max())
jahr_range = st.sidebar.slider("Baujahr", jahr_min, jahr_max, (jahr_min, jahr_max), step=1)

# HU bis
hu_optionen = sorted([x for x in df["hu_monat_num"].unique() if x != "unbekannt"])
hu_optionen_all = ["alle"] + hu_optionen + ["unbekannt"]
hu_filter = st.sidebar.selectbox("HU bis (frühestens)", ["alle"] + hu_optionen)

# Rost
rost_filter = st.sidebar.selectbox("Rost", ["alle", "kein Rost", "Rost vorhanden"])

# Camper
camper_filter = st.sidebar.selectbox("Camper-Ausbau", ["alle", "Ja", "Nein"])

# Fahrzeugzustand
zustand_optionen = ["alle"] + sorted(df["Fahrzeugzustand"].dropna().unique().tolist())
zustand_filter = st.sidebar.selectbox("Fahrzeugzustand", zustand_optionen)

# Kraftstoff
kraftstoff_optionen = ["alle"] + sorted(df["Kraftstoffart"].dropna().unique().tolist())
kraftstoff_filter = st.sidebar.selectbox("Kraftstoffart", kraftstoff_optionen)

# Getriebe
getriebe_optionen = ["alle"] + sorted(df["Getriebe"].dropna().unique().tolist())
getriebe_filter = st.sidebar.selectbox("Getriebe", getriebe_optionen)

# Leistung
ps_min, ps_max = int(df["Leistung"].str.replace(" PS","").dropna().astype(float).min()), \
                  int(df["Leistung"].str.replace(" PS","").dropna().astype(float).max())
ps_range = st.sidebar.slider("Leistung (PS)", ps_min, ps_max, (ps_min, ps_max), step=1)

# Außenfarbe
farbe_optionen = ["alle"] + sorted(df["Außenfarbe"].dropna().unique().tolist())
farbe_filter = st.sidebar.selectbox("Außenfarbe", farbe_optionen)

# Standort / PLZ
ort_suche = st.sidebar.text_input("Standort enthält (PLZ oder Ort)")

# Freitext-Suche
freitext = st.sidebar.text_input("Freitext-Suche (Titel / Beschreibung)")

# Sortierung
st.sidebar.header("↕️ Sortierung")
sort_col = st.sidebar.selectbox("Sortieren nach", ["preis_num", "km_num", "jahr", "hu_datum"])
sort_asc = st.sidebar.radio("Reihenfolge", ["Aufsteigend", "Absteigend"]) == "Aufsteigend"

# --- Filterlogik ---
def ps_to_num(val):
    try:
        return float(str(val).replace(" PS", ""))
    except:
        return None

df["ps_num"] = df["Leistung"].apply(ps_to_num)

mask = (
    df["preis_num"].between(*preis_range) &
    df["km_num"].between(*km_range) &
    df["jahr"].between(*jahr_range) &
    df["ps_num"].between(*ps_range)
)

if hu_filter != "alle":
    mask &= df["hu_monat_num"] >= hu_filter

if rost_filter == "kein Rost":
    mask &= df["hat_rost"] == False
elif rost_filter == "Rost vorhanden":
    mask &= df["hat_rost"] == True

if camper_filter == "Ja":
    mask &= df["is_camper"] == True
elif camper_filter == "Nein":
    mask &= df["is_camper"] == False

if zustand_filter != "alle":
    mask &= df["Fahrzeugzustand"] == zustand_filter

if kraftstoff_filter != "alle":
    mask &= df["Kraftstoffart"] == kraftstoff_filter

if getriebe_filter != "alle":
    mask &= df["Getriebe"] == getriebe_filter

if farbe_filter != "alle":
    mask &= df["Außenfarbe"] == farbe_filter

if ort_suche:
    mask &= df["Ort"].str.contains(ort_suche, case=False, na=False)

if freitext:
    mask &= (
        df["titel"].str.contains(freitext, case=False, na=False) |
        df["beschreibung"].str.contains(freitext, case=False, na=False)
    )

filtered = df[mask].sort_values(sort_col, ascending=sort_asc)

# --- Anzeige ---
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

ansicht = st.radio("Ansicht", ["Tabelle", "Karten"], horizontal=True)

# Spalten für Tabelle
tabellen_spalten = [
    "titel", "preis_num", "km_num", "jahr", "Leistung",
    "Kraftstoffart", "Getriebe", "Fahrzeugzustand", "Außenfarbe",
    "HU bis", "Ort", "hat_rost", "is_camper", "url"
]

if ansicht == "Tabelle":
    anzeige_df = filtered[tabellen_spalten].copy()
    anzeige_df.columns = [
        "Titel", "Preis (€)", "KM", "Baujahr", "PS",
        "Kraftstoff", "Getriebe", "Zustand", "Farbe",
        "HU bis", "Ort", "Rost", "Camper", "Link"
    ]
    st.dataframe(
        anzeige_df,
        use_container_width=True,
        column_config={
            "Link": st.column_config.LinkColumn("Link"),
            "Preis (€)": st.column_config.NumberColumn(format="%.0f €"),
            "KM": st.column_config.NumberColumn(format="%.0f km"),
        },
        hide_index=True
    )

else:  # Karten
    cols_per_row = 2
    rows = [filtered.iloc[i:i+cols_per_row] for i in range(0, len(filtered), cols_per_row)]

    for row in rows:
        cols = st.columns(cols_per_row)
        for col, (_, r) in zip(cols, row.iterrows()):
            with col:
                with st.container(border=True):
                    st.markdown(f"### [{r['titel']}]({r['url']})")
                    st.markdown(f"💶 **{r['preis_num']:.0f} €** &nbsp;|&nbsp; 🛣️ {r['km_num']:,.0f} km &nbsp;|&nbsp; 📅 {int(r['jahr']) if pd.notna(r['jahr']) else '?'}")
                    st.markdown(f"⚙️ {r['Kraftstoffart']} | {r['Getriebe']} | {r['Leistung']}")
                    st.markdown(f"🎨 {r['Außenfarbe']} | 🔧 {r['Fahrzeugzustand']}")
                    st.markdown(f"📍 {r['Ort']} &nbsp;|&nbsp; 🔩 HU: {r['HU bis']}")

                    badges = []
                    if r["hat_rost"]: badges.append("🟠 Rost")
                    if r["is_camper"]: badges.append("🏕️ Camper")
                    if r["negative_signale"] and r["negative_signale"] != "nicht spezifiziert":
                        badges.append("⚠️ Mängel")
                    if badges:
                        st.markdown(" &nbsp; ".join(badges))

                    with st.expander("Mehr Details"):
                        st.write("**Positive Signale:**", r.get("positive_signale", "–"))
                        st.write("**Schäden:**", r.get("schadenshinweise", "–"))
                        st.write("**Ausstattung:**", r.get("ausstattung_extra", "–"))
                        st.write("**Umbauten:**", r.get("umbauten", "–"))
