import re
import streamlit as st

# 1. Konfiguracja i Stylistyka
st.set_page_config(page_title="Pro Analizator Logów", layout="wide", page_icon="⚔️")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_name=True)

st.title("⚔️ Zaawansowany Analizator Logów Bitewnych")
st.caption("Automatycznie pomija czat i liczy statystyki K/D")

# 2. Sidebar (Ustawienia)
with st.sidebar:
    st.header("⚙️ Opcje widoku")
    pokaz_kd = st.checkbox("Pokazuj K/D Ratio", value=True)
    pokaz_mvp = st.checkbox("Wyróżnij MVP", value=True)
    st.divider()
    filtr_gracza = st.text_input("Szukaj gracza (filtr):")

# 3. Pole wejściowe
tekst = st.text_area("Wklej logi tutaj (zawierające czat, godziny i wyniki):", height=250)

if st.button("🚀 Generuj Raport", type="primary"):
    if not tekst:
        st.warning("Najpierw wklej logi!")
    else:
        # Inicjalizacja danych
        fragi_t1, fragi_t2 = {}, {}
        zgony_t1, zgony_t2 = {}, {}
        js_t1, js_t2 = 0, 0
        logi_czatu = []

        # Przetwarzanie linii
        linie = tekst.split("\n")
        for linia in linie:
            linia = linia.strip()
            if not linia: continue

            # --- FILTR CZATU ---
            if "killed by" not in linia.lower():
                logi_czatu.append(linia)
                continue 

            # --- LOGIKA JUDGEMENT STRIKE ---
            if "killed by judgement strike" in linia.lower():
                match_v = re.search(r"\(Team (\d)\)", linia)
                if match_v:
                    v_team = int(match_v.group(1))
                    if v_team == 1: js_t2 += 1
                    elif v_team == 2: js_t1 += 1
                continue

            # --- LOGIKA ZABÓJSTW ---
            # Wyciąganie Ofiary (pomija godzinę na początku)
            match_v = re.search(r"(?:^|\d{2}:\d{2}\s+)(.+?) \(Team (\d)\)", linia)
            if match_v:
                v_name = match_v.group(1).strip()
                v_team = int(match_v.group(2))
                
                # Wyciąganie Killera
                match_k = re.search(r"killed by ([^(]+)", linia)
                k_name = match_k.group(1).strip() if match_k else None
                
                match_k_team = re.search(r"killed by [^(]*\(Team (\d)\)", linia)
                k_team = int(match_k_team.group(1)) if match_k_team else None

                if k_name:
                    if k_team == 1: fragi_t1[k_name] = fragi_t1.get(k_name, 0) + 1
                    elif k_team == 2: fragi_t2[k_name] = fragi_t2.get(k_name, 0) + 1
                
                if v_team == 1: zgony_t1[v_name] = zgony_t1.get(v_name, 0) + 1
                elif v_team == 2: zgony_t2[v_name] = zgony_t2.get(v_name, 0) + 1

        # 4. Dashboard Wyników
        total_k1 = sum(fragi_t1.values()) + js_t1
        total_k2 = sum(fragi_t2.values()) + js_t2
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Wynik Team 1", total_k1, delta=total_k1 - total_k2)
        col_m2.metric("Wynik Team 2", total_k2, delta=total_k2 - total_k1)
        col_m3.metric("Wiadomości czatu", len(logi_czatu))

        st.divider()

        # Kolumny z graczami
        c1, c2 = st.columns(2)

        def render_team(fragi, zgony, js, title, theme):
            st.subheader(title)
            players = sorted(set(fragi.keys()) | set(zgony.keys()), 
                            key=lambda x: fragi.get(x, 0), reverse=True)
            
            if not players and js == 0:
                st.write("Brak danych dla tej drużyny.")
                return

            mvp = players[0] if players else None

            for p in players:
                if filtr_gracza.lower() and filtr_gracza.lower() not in p.lower():
                    continue
                
                k, d = fragi.get(p, 0), zgony.get(p, 0)
                kd = round(k/d, 2) if d > 0 else float(k)
                
                label = f"⭐ MVP | **{p}**" if pokaz_mvp and p == mvp and k > 0 else f"**{p}**"
                kd_text = f" (K/D: `{kd}`)" if pokaz_kd else ""
                st.write(f"{label}: {k} K / {d} D {kd_text}")
            
            if js > 0:
                st.info(f"🎯 Punkty z Judgement Strike: {js}")

        with c1:
            render_team(fragi_t1, zgony_t1, js_t1, "🔵 Drużyna 1", "blue")
        with c2:
            render_team(fragi_t2, zgony_t2, js_t2, "🔴 Drużyna 2", "red")

        # Bonus: Wyświetlanie odfiltrowanego czatu
        if logi_czatu:
            with st.expander("Pokaż zapis czatu (zignorowane linie)"):
                for l in logi_czatu:
                    st.text(l)
