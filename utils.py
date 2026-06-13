import streamlit as st
import pandas as pd

# --- Scoring-Tabellen ---
ROST_SCORE     = {"nicht vorhanden": 10, "unbekannt": 5, "vorhanden": 0}
SCHADEN_SCORE  = {"nicht vorhanden": 10, "unbekannt": 5, "vorhanden": 0}
REPARATUR_SCORE= {"nein": 10, "unbekannt": 5, "ja": 0}
FAHRBEREIT_SCORE={"ja": 10, "eingeschraenkt": 5, "unbekannt": 3, "nein": 0}
ZUSTAND_SCORE  = {"Unbeschädigtes Fahrzeug": 10, "Beschädigtes Fahrzeug": 0}

@st.cache_data
def load_data():
    return pd.read_parquet("data/final/output_final.parquet")

def score_hu(hu_str):
    try:
        year, month = str(hu_str).split("-")
        from datetime import date
        hu = date(int(year), int(month), 1)
        now = date.today()
        months = (hu.year - now.year) * 12 + (hu.month - now.month)
        months = max(0, min(months, 24))
        return round(months / 24 * 10, 1)
    except Exception:
        return 5

def calc_score_technisch(row):
    s  = ROST_SCORE.get(str(row.get("rost_hinweise","unbekannt")).lower(), 5)
    s += SCHADEN_SCORE.get(str(row.get("schadenshinweise","unbekannt")).lower(), 5)
    s += REPARATUR_SCORE.get(str(row.get("reparaturstau","unbekannt")).lower(), 5)
    return round(s / 3, 1)

def calc_score_fahrbereit(row):
    s  = FAHRBEREIT_SCORE.get(str(row.get("fahrbereit","unbekannt")).lower(), 3)
    s += score_hu(row.get("hu_monat_num","unbekannt"))
    s += ZUSTAND_SCORE.get(str(row.get("Fahrzeugzustand","")), 5)
    return round(s / 3, 1)

def calc_score_preis_leistung(row, df):
    scores = []
    for col, invert in [("preis_num", True), ("km_num", True), ("jahr", False)]:
        try:
            val    = float(row[col])
            median = df[col].median()
            std    = df[col].std()
            if std == 0:
                scores.append(5)
                continue
            z = (val - median) / std
            if invert: z = -z
            scores.append(round(min(10, max(0, 5 + z * 2)), 1))
        except Exception:
            scores.append(5)
    return round(sum(scores) / len(scores), 1)

def calc_custom_score(row, df, weights):
    """Berechnet Score mit benutzerdefinierten Gewichtungen.
    weights = {
        'w_tech': 3, 'w_fahr': 3, 'w_preis': 3,
        'w_rost': 3, 'w_schaden': 3, 'w_repa': 3,
        'w_fahr2': 3, 'w_hu': 3, 'w_zustand': 3,
        'w_preis2': 3, 'w_km': 3, 'w_jahr': 3,
    }
    """
    w = weights

    # Technisch
    r  = ROST_SCORE.get(str(row.get("rost_hinweise","unbekannt")).lower(), 5) * w["w_rost"]
    s  = SCHADEN_SCORE.get(str(row.get("schadenshinweise","unbekannt")).lower(), 5) * w["w_schaden"]
    rp = REPARATUR_SCORE.get(str(row.get("reparaturstau","unbekannt")).lower(), 5) * w["w_repa"]
    tech = (r + s + rp) / max(w["w_rost"] + w["w_schaden"] + w["w_repa"], 1)

    # Fahrbereit
    f  = FAHRBEREIT_SCORE.get(str(row.get("fahrbereit","unbekannt")).lower(), 3) * w["w_fahr2"]
    h  = score_hu(row.get("hu_monat_num","unbekannt")) * w["w_hu"]
    z  = ZUSTAND_SCORE.get(str(row.get("Fahrzeugzustand","")), 5) * w["w_zustand"]
    fahr = (f + h + z) / max(w["w_fahr2"] + w["w_hu"] + w["w_zustand"], 1)

    # Preis/Leistung
    pl_scores = []
    for col, invert, ww in [("preis_num", True, w["w_preis2"]),
                             ("km_num",    True, w["w_km"]),
                             ("jahr",      False, w["w_jahr"])]:
        try:
            val    = float(row[col])
            median = df[col].median()
            std    = df[col].std()
            z_s    = (val - median) / std
            if invert: z_s = -z_s
            pl_scores.append(round(min(10, max(0, 5 + z_s * 2)), 1) * ww)
        except Exception:
            pl_scores.append(5 * ww)
    pl = sum(pl_scores) / max(w["w_preis2"] + w["w_km"] + w["w_jahr"], 1)

    gesamt = (tech * w["w_tech"] + fahr * w["w_fahr"] + pl * w["w_preis"]) / max(w["w_tech"] + w["w_fahr"] + w["w_preis"], 1)
    return round(gesamt, 1)

def score_detail_table(row, df):
    """Gibt DataFrame mit Feldbeiträgen zurück."""
    details = []

    details.append({"Kategorie": "Technisch", "Feld": "Rost",
        "Wert": row.get("rost_hinweise","unbekannt"),
        "Punkte": ROST_SCORE.get(str(row.get("rost_hinweise","unbekannt")).lower(), 5), "Max": 10})
    details.append({"Kategorie": "Technisch", "Feld": "Schäden",
        "Wert": row.get("schadenshinweise","unbekannt"),
        "Punkte": SCHADEN_SCORE.get(str(row.get("schadenshinweise","unbekannt")).lower(), 5), "Max": 10})
    details.append({"Kategorie": "Technisch", "Feld": "Reparaturstau",
        "Wert": row.get("reparaturstau","unbekannt"),
        "Punkte": REPARATUR_SCORE.get(str(row.get("reparaturstau","unbekannt")).lower(), 5), "Max": 10})

    details.append({"Kategorie": "Fahrbereit", "Feld": "Fahrbereit",
        "Wert": row.get("fahrbereit","unbekannt"),
        "Punkte": FAHRBEREIT_SCORE.get(str(row.get("fahrbereit","unbekannt")).lower(), 3), "Max": 10})
    details.append({"Kategorie": "Fahrbereit", "Feld": "HU bis",
        "Wert": row.get("HU bis","unbekannt"),
        "Punkte": score_hu(row.get("hu_monat_num","unbekannt")), "Max": 10})
    details.append({"Kategorie": "Fahrbereit", "Feld": "Fahrzeugzustand",
        "Wert": row.get("Fahrzeugzustand","unbekannt"),
        "Punkte": ZUSTAND_SCORE.get(str(row.get("Fahrzeugzustand","")), 5), "Max": 10})

    for col, invert, label in [("preis_num", True, "Preis"),
                                ("km_num",    True, "Kilometerstand"),
                                ("jahr",      False, "Baujahr")]:
        try:
            val    = float(row[col])
            median = df[col].median()
            std    = df[col].std()
            z      = (val - median) / std
            if invert: z = -z
            s = round(min(10, max(0, 5 + z * 2)), 1)
        except Exception:
            s = 5
            val = "unbekannt"
        details.append({"Kategorie": "Preis/Leistung", "Feld": label,
            "Wert": val, "Punkte": s, "Max": 10})

    return pd.DataFrame(details)
