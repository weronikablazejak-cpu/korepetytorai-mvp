import streamlit as st
from urllib.parse import urlparse, parse_qs
from backend import process_message

st.set_page_config(page_title="KorepetytorAI – Testy", page_icon="🎓")

# user_id z URL
params = st.experimental_get_query_params()
user_id = params.get("user_id", ["guest"])[0]

st.title("🎓 KorepetytorAI — wersja testowa MVP")
st.write(f"Twój ID: **{user_id}** (indywidualny progres)")

user_input = st.text_input("Zadaj pytanie:", "")

if st.button("Wyślij") and user_input.strip():
    answer, xp, total_xp, level, streak, badges = process_message(
        user_id,
        user_input
    )

    st.success(answer)
    st.info(f"+{xp} XP | Razem: {total_xp} XP | Poziom: {level}")
    st.info(f"🔥 Streak: {streak} dni")

    if badges:
        st.warning("🎉 Zdobyłeś nowe odznaki: " + ", ".join(badges))
