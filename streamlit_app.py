import streamlit as st

if "page" not in st.session_state:
    st.session_state.page = "page1"

if st.session_state.page == "page1":
    import page1_game_date
elif st.session_state.page == "page2":
    import page2_hit_entry
