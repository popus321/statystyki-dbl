import re
import streamlit as st

# Konfiguracja strony
st.set_page_config(page_title="Statystyki Fragów i Zgonów", layout="wide")

st.title("📊 Analizator Logów Bitewnych")

# Główne pole tekstowe (zastępuje scrolledtext)
tekst = st.text_area("Wklej logi poniżej:", height=300)

col1, col2 = st.columns(2)

if st.button("Policz statystyki", type="primary"):
    if not tekst:
        st.warning("Najpierw wklej logi!")
    else:
        fragi_team1, fragi_team2 = {}, {}
        smierci_team1, smierci_team2 = {}, {}
        js_team1, js_team2 = 0, 0

        wydarzenia = tekst.split(".")

        for zdarzenie in wydarzenia:
            zdarzenie = zdarzenie.strip()
            if not zdarzenie: continue

            # --- Judgement Strike ---
            if "killed by judgement strike" in zdarzenie.lower():
                match_victim = re.search(r"\(Team (\d)\)", zdarzenie)
                if match_victim:
                    victim_team = int(match_victim.group(1))
                    if victim_team == 1: js_team2 += 1
                    elif victim_team == 2: js_team1 += 1
                continue

            # --- Ofiara ---
            match_victim = re.search(r"(.+?) \(Team (\d)\)", zdarzenie)
            if match_victim:
                victim = match_victim.group(1).strip()
                victim = re.sub(r"^\d{2}:\d{2}\s+", "", victim)
                victim_team = int(match_victim.group(2))
            else:
                victim, victim_team = None, None

            # --- Killer ---
            match_killer = re.search(r"killed by ([^(]+)", zdarzenie)
            killer = match_killer.group(1).strip() if match_killer else None
            match_killer_team = re.search(r"killed by [^(]*\(Team (\d)\)", zdarzenie)
            killer_team = int(match_killer_team.group(1)) if match_killer_team else None

            if killer:
                if killer_team == 1: fragi_team1[killer] = fragi_team1.get(killer, 0) + 1
                elif killer_team == 2: fragi_team2[killer] = fragi_team2.get(killer, 0) + 1
            if victim:
                if victim_team == 1: smierci_team1[victim] = smierci_team1.get(victim, 0) + 1
                elif victim_team == 2: smierci_team2[victim] = smierci_team2.get(victim, 0) + 1

        # --- Wyświetlanie Wyników ---
        c1, c2 = st.columns(2)

        with c1:
            st.info("### Team 1")
            gracze1 = sorted(set(fragi_team1.keys()) | set(smierci_team1.keys()), key=lambda x: fragi_team1.get(x, 0), reverse=True)
            for g in gracze1:
                st.write(f"**{g}**: {fragi_team1.get(g,0)} K / {smierci_team1.get(g,0)} D")
            if js_team1 > 0: st.write(f"🎯 Judgement Strike: {js_team1}")

        with c2:
            st.error("### Team 2")
            gracze2 = sorted(set(fragi_team2.keys()) | set(smierci_team2.keys()), key=lambda x: fragi_team2.get(x, 0), reverse=True)
            for g in gracze2:
                st.write(f"**{g}**: {fragi_team2.get(g,0)} K / {smierci_team2.get(g,0)} D")
            if js_team2 > 0: st.write(f"🎯 Judgement Strike: {js_team2}")
