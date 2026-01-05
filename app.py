import re
import streamlit as st

# 1. Konfiguracja i Stylistyka
st.set_page_config(page_title="Pro Analizator Logów", layout="wide", page_icon="⚔️")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("⚔️ Zaawansowany Analizator Logów Bitewnych")
st.caption("Naprawiono: błąd z duplikowaniem nicków przez godzinę")

# 2. Sidebar (Ustawienia)
with st.sidebar:
    st.header("⚙️ Opcje widoku")
    pokaz_kd = st.checkbox("Pokazuj K/D Ratio", value=True)
    pokaz_mvp = st.checkbox("Wyróżnij MVP", value=True)
    st.divider()
    filtr_gracza = st.text_input("Szukaj gracza (filtr):")

# 3. Pole wejściowe
tekst = st.text_area("Wklej logi tutaj:", height=250)

if st.button("🚀 Generuj Raport", type="primary"):
    if not tekst:
        st.warning("Najpierw wklej logi!")
    else:
        fragi_t1, fragi_t2 = {}, {}
        zgony_t1, zgony_t2 = {}, {}
        js_t1, js_t2 = 0, 0
        logi_czatu = []

        linie = tekst.split("\n")
        for linia in linie:
            linia = linia.strip()
            if not linia: continue

            # --- FILTR CZATU ---
            if "killed by" not in linia.lower():
                logi_czatu.append(linia)
                continue 

            # --- OCZYSZCZANIE LINII Z GODZINY ---
            # Usuwa format HH:MM z początku linii, aby nick był czysty
            linia_clean = re.sub(r"^\d{2}:\d{2}\s+", "", linia)

            # --- LOGIKA JUDGEMENT STRIKE ---
            if "killed by judgement strike" in linia_clean.lower():
                match_v = re.search(r"\(Team (\d)\)", linia_clean)
                if match_v:
                    v_team = int(match_v.group(1))
                    if v_team == 1: js_t2 += 1
                    elif v_team == 2: js_t1 += 1
                continue

            # --- LOGIKA ZABÓJSTW ---
            # Ofiara: bierzemy tekst przed "(Team X)"
            match_v = re.search(r"(.+?) \(Team (\d)\)", linia_clean)
            if match_v:
                v_name = match_v.group(1).strip()
                v_team = int(match_v.group(2))
                
                # Killer: bierzemy tekst po "killed by" a przed (Team X)
                # Używamy re.search na fragmencie po 'killed by'
                if "killed by" in linia_clean.lower():
                    parts = re.split(r"killed by", linia_clean, flags=re.IGNORECASE)
                    killer_part = parts[1].strip()
                    
                    match_k = re.search(r"(.+?) \(Team (\d)\)", killer_part)
                    if match_k:
                        k_name = match_k.group(1).strip()
                        k_team = int(match_k.group(2))

                        if k_team == 1: fragi_t1[k_name] = fragi_t1.get(k_name, 0) + 1
                        elif k_team == 2: fragi_t2[k_name] = fragi_t2.get(k_name, 0) + 1
                
                if v_team == 1: zgony_t1[v_name] = zgony_t1.get(v_name, 0) + 1
                elif v_team == 2: zgony_t2[v_name] = zgony_t2.get(v_name, 0) + 1

        # 4. Dashboard Wyników
        total_k1 = sum(fragi_t1.values()) + js_t1
        total_k2 = sum(fragi_t2.values()) + js_t2
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Wynik Team 1", total_k1)
        col_m2.metric("Wynik Team 2", total_k2)
        col_m3.metric("Czat", len(logi_czatu))

        st.divider()

        c1, c2 = st.columns(2)

        def render_team(fragi, zgony, js, title):
            st.subheader(title)
            players = sorted(set(fragi.keys()) | set(zgony.keys()), 
                            key=lambda x: fragi.get(x, 0), reverse=True)
            
            for p in players:
                if filtr_gracza.lower() and filtr_gracza.lower() not in p.lower():
                    continue
                k, d = fragi.get(p, 0), zgony.get(p, 0)
                kd = round(k/d, 2) if d > 0 else float(k)
                prefix = "⭐ MVP | " if pokaz_mvp and players and p == players[0] and k > 0 else ""
                kd_text = f" (K/D: `{kd}`)" if pokaz_kd else ""
                st.write(f"{prefix}**{p}**: {k} K / {d} D {kd_text}")
            
            if js > 0:
                st.info(f"🎯 JS: {js}")

        with c1: render_team(fragi_t1, zgony_t1, js_t1, "🔵 Drużyna 1")
        with c2: render_team(fragi_t2, zgony_t2, js_t2, "🔴 Drużyna 2")

        if logi_czatu:
            with st.expander("Pokaż zapis czatu"):
                for l in logi_czatu: st.text(l)
