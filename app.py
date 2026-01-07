import re
import streamlit as st

# 1. Konfiguracja
st.set_page_config(page_title="Parser DBL Stats", layout="wide", page_icon="⚔️")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .team-extra { color: #555; font-weight: bold; padding: 10px; background: #eee; border-radius: 5px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Logo
st.markdown("""
    <div style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 15px; margin-bottom: 25px">
        <h1 style="color: white; text-align: center; font-family: 'Arial Black'; letter-spacing: 5px; margin: 0;">
            PARSER <span style="color: #ff4b4b;">DBL</span> STATS
        </h1>
    </div>
    """, unsafe_allow_html=True)

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Ustawienia")
    pokaz_kd = st.checkbox("Pokazuj K/D Ratio", value=True)
    pokaz_mvp = st.checkbox("Wyróżnij Globalnego MVP", value=True)
    st.divider()
    filtr_gracza = st.text_input("Szukaj gracza:")

# 3. Wejście
tekst = st.text_area("Wklej logi tutaj:", height=250)

if st.button("🚀 Generuj Raport", type="primary"):
    if not tekst:
        st.warning("Najpierw wklej logi!")
    else:
        fragi = {1: {}, 2: {}}
        zgony_ogolne = {1: {}, 2: {}}
        # Statystyki drużynowe (nie przypisane do konkretnych osób)
        team_stats = {1: {"ff": 0, "js": 0}, 2: {"ff": 0, "js": 0}}
        logi_czatu = []

        linie = tekst.split("\n")
        for linia in linie:
            linia = linia.strip()
            if not linia: continue

            if "killed by" not in linia.lower() and "have been killed by" not in linia.lower():
                logi_czatu.append(linia)
                continue 

            linia_clean = re.sub(r"^\d{2}:\d{2}\s+", "", linia)

            # --- JUDGEMENT STRIKE ---
            if "killed by judgement strike" in linia_clean.lower():
                match = re.search(r"(.+?) \(Team (\d)\)", linia_clean)
                if match:
                    v_name, v_team = match.group(1).strip(), int(match.group(2))
                    zgony_ogolne[v_team][v_name] = zgony_ogolne[v_team].get(v_name, 0) + 1
                    beneficiary_team = 2 if v_team == 1 else 1
                    team_stats[beneficiary_team]["js"] += 1
                continue

            # --- FIRE FIELD ---
            if "killed by fire field" in linia_clean.lower():
                match = re.search(r"(.+?) \(Team (\d)\)", linia_clean)
                if match:
                    v_name, v_team = match.group(1).strip(), int(match.group(2))
                    zgony_ogolne[v_team][v_name] = zgony_ogolne[v_team].get(v_name, 0) + 1
                    # Punkt (korzyść) idzie do drużyny przeciwnej
                    beneficiary_team = 2 if v_team == 1 else 1
                    team_stats[beneficiary_team]["ff"] += 1
                continue

            # --- STANDARDOWY FRAG ---
            match_v = re.search(r"(.+?) \(Team (\d)\)", linia_clean)
            if match_v:
                v_name, v_team = match_v.group(1).strip(), int(match_v.group(2))
                zgony_ogolne[v_team][v_name] = zgony_ogolne[v_team].get(v_name, 0) + 1
                
                parts = re.split(r"killed by", linia_clean, flags=re.IGNORECASE)
                if len(parts) > 1:
                    match_k = re.search(r"(.+?) \(Team (\d)\)", parts[1].strip())
                    if match_k:
                        k_name, k_team = match_k.group(1).strip(), int(match_k.group(2))
                        fragi[k_team][k_name] = fragi[k_team].get(k_name, 0) + 1

        # MVP
        wszyscy = {}
        for t in [1, 2]:
            for p in set(fragi[t].keys()) | set(zgony_ogolne[t].keys()):
                k, d = fragi[t].get(p, 0), zgony_ogolne[t].get(p, 0)
                wszyscy[p] = {'k': k, 'd': d, 't': t, 'kd': (k/d if d > 0 else float(k))}
        
        g_mvp = max(wszyscy.keys(), key=lambda x: (wszyscy[x]['kd'], wszyscy[x]['k'])) if wszyscy else None

        t1_total = sum(fragi[1].values()) + team_stats[1]["js"] + team_stats[1]["ff"]
        t2_total = sum(fragi[2].values()) + team_stats[2]["js"] + team_stats[2]["ff"]
        
        if g_mvp and pokaz_mvp and wszyscy[g_mvp]['k'] > 0:
            st.success(f"🏆 **GLOBAL MVP: {g_mvp}** (Team {wszyscy[g_mvp]['t']})")

        c1, c2 = st.columns(2)

        def render_team(t_num, icon, score):
            with (c1 if t_num == 1 else c2):
                st.subheader(f"{icon} Team {t_num} | Suma: {score}")
                players = sorted(set(fragi[t_num].keys()) | set(zgony_ogolne[t_num].keys()), 
                                key=lambda x: (fragi[t_num].get(x,0) / zgony_ogolne[t_num].get(x,1) if zgony_ogolne[t_num].get(x,0) > 0 else fragi[t_num].get(x,0)), 
                                reverse=True)

                for p in players:
                    if filtr_gracza.strip() and filtr_gracza.lower() not in p.lower(): continue
                    k, d = fragi[t_num].get(p, 0), zgony_ogolne[t_num].get(p, 0)
                    kd = round(k/d, 2) if d > 0 else float(k)
                    mvp = "⭐ " if p == g_mvp and pokaz_mvp else ""
                    st.write(f"{mvp}**{p}**: {k} K / {d} D" + (f" (K/D: `{kd}`)" if pokaz_kd else ""))
                
                # WYPISYWANIE POD LUDŹMI (SUMA DRUŻYNOWA)
                ff_val = team_stats[t_num]["ff"]
                js_val = team_stats[t_num]["js"]
                if ff_val > 0 or js_val > 0:
                    st.markdown("<div class='team-extra'>Dodatkowe punkty drużyny:</div>", unsafe_allow_html=True)
                    if ff_val > 0: st.info(f"🔥 Fire Field: {ff_val}")
                    if js_val > 0: st.info(f"⚡ Judgement Strike: {js_val}")

        render_team(1, "🔵", t1_total)
        render_team(2, "🔴", t2_total)

        if logi_czatu:
            with st.expander("Pokaż zapis czatu"):
                for l in logi_czatu: st.text(l)
