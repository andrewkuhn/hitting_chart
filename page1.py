import streamlit as st
from datetime import datetime

st.title("Hitting Chart - Page 1: Game Date")

if "game_date" not in st.session_state:
    st.session_state.game_date = datetime.now().date()

game_date = st.date_input("Select Game Date", st.session_state.game_date)

if st.button("Next: Enter Hits"):
    st.session_state.game_date = game_date
    st.session_state.page = "page2"
    st.experimental_rerun()
