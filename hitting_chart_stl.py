import streamlit as st
import psycopg2
from datetime import datetime

# Initialize session state variables
if 'batter' not in st.session_state:
    st.session_state.batter = ""
if 'game_date' not in st.session_state:
    st.session_state.game_date = datetime.now().date()
if 'outcome_type' not in st.session_state:
    st.session_state.outcome_type = ""
if 'direction' not in st.session_state:
    st.session_state.direction = None

# Database connection helper
def get_connection():
    return psycopg2.connect(
        host="your_host",
        database="your_db",
        user="your_user",
        password="your_password",
        port=5432
    )

st.title("Hitting Chart App")

# Input batter and date (outside form for simplicity)
st.session_state.batter = st.text_input("Batter Name", st.session_state.batter)
st.session_state.game_date = st.date_input("Game Date", st.session_state.game_date)

# Form for rest of the hit info
with st.form("hit_form"):
    col1, col2 = st.columns(2)

    with col1:
        inning = st.number_input("Inning", min_value=1, max_value=20, step=1)
        pa_number = st.number_input("Plate Appearance Number", min_value=1, step=1)
        outs = st.number_input("Outs", min_value=0, max_value=2, step=1)
        men_on_base = st.selectbox("Men on Base", ["None", "1B", "2B", "3B", "1B & 2B", "1B & 3B", "2B & 3B", "Bases Loaded"])
        balls = st.number_input("Balls", min_value=0, max_value=3, step=1)
        strikes = st.number_input("Strikes", min_value=0, max_value=2, step=1)

    with col2:
        outcome_type = st.radio("Outcome of the Play", options=["", "Out", "On Base"], index=0)

        if outcome_type != st.session_state.outcome_type:
            st.session_state.outcome_type = outcome_type

        out_detail = None
        on_base_detail = None

        if st.session_state.outcome_type == "Out":
            out_detail = st.selectbox("How did the batter get out?", ["", "Strikeout", "Groundout", "Flyout", "Lineout", "Popup", "Fielder's Choice", "Double Play", "Other"])

        elif st.session_state.outcome_type == "On Base":
            on_base_detail = st.selectbox("How did the batter reach base?", ["", "Single", "Double", "Triple", "Home Run", "Walk", "Hit By Pitch", "Error", "Fielder’s Choice (Safe)"])

    submitted = st.form_submit_button("Submit Hit")

    if submitted:
        if not st.session_state.outcome_type:
            st.warning("Please select an outcome.")
        else:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO pitches_faced (
                        batter, date, inning, pa_number, outs, men_on_base, balls, strikes,
                        outcome, out_detail, on_base_detail, direction
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    st.session_state.batter,
                    st.session_state.game_date,
                    inning,
                    pa_number,
                    outs,
                    men_on_base,
                    balls,
                    strikes,
                    st.session_state.outcome_type == "On Base",
                    out_detail,
                    on_base_detail,
                    st.session_state.direction
                ))
                conn.commit()
                conn.close()
                st.success("Hit saved!")

                # Reset outcome and direction after submit
                st.session_state.outcome_type = ""
                st.session_state.direction = None
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Error saving hit: {e}")

# Direction buttons outside form
st.markdown("### Direction of Hit")
colA, colB, colC, colD, colE, colF, colG = st.columns(7)
with colA:
    if st.button("Left"):
        st.session_state.direction = "Left"
with colB:
    if st.button("Left-Center"):
        st.session_state.direction = "Left-Center"
with colC:
    if st.button("Center"):
        st.session_state.direction = "Center"
with colD:
    if st.button("Right-Center"):
        st.session_state.direction = "Right-Center"
with colE:
    if st.button("Right"):
        st.session_state.direction = "Right"
with colF:
    if st.button("Infield"):
        st.session_state.direction = "Infield"
with colG:
    if st.button("Foul"):
        st.session_state.direction = "Foul"

if st.session_state.direction:
    st.info(f"Direction Selected: {st.session_state.direction}")
