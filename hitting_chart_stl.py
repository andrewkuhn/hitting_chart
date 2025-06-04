import streamlit as st
import psycopg2
import pandas as pd
import datetime
import os

# ------------------- DB SETUP -------------------
def get_db_params():
    return {
        "dbname": st.secrets["DB_NAME"],
        "user": st.secrets["DB_USER"],
        "password": st.secrets["DB_PASSWORD"],
        "host": st.secrets["DB_HOST"],
        "port": st.secrets["DB_PORT"],
    }

def get_connection():
    return psycopg2.connect(**get_db_params())

def ensure_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS batters (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pitches_faced (
            id SERIAL PRIMARY KEY,
            batter TEXT NOT NULL,
            date DATE NOT NULL,
            inning INTEGER,
            pa_number INTEGER,
            outs INTEGER,
            men_on_base TEXT,
            balls INTEGER,
            strikes INTEGER,
            outcome BOOLEAN,
            out_detail TEXT,
            on_base_detail TEXT,
            direction TEXT
        )
    """)
    conn.commit()
    conn.close()

ensure_tables()

# ------------------- SESSION STATE -------------------
if 'page' not in st.session_state:
    st.session_state.page = 'batter_date'
if 'batter' not in st.session_state:
    st.session_state.batter = None
if 'game_date' not in st.session_state:
    st.session_state.game_date = datetime.date.today()
if 'outcome_label' not in st.session_state:
    st.session_state.outcome_label = ""
if 'direction' not in st.session_state:
    st.session_state.direction = None

# ------------------- PAGE 1 -------------------
st.title("Hitting Chart")

if st.session_state.page == 'batter_date':
    st.header("Select Batter and Date")

    # Fetch batters from DB
    def get_batters():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM batters ORDER BY name")
        batters = [row[0] for row in cur.fetchall()]
        conn.close()
        return batters

    batters = get_batters()
    batter = st.selectbox("Select Batter", options=[""] + batters)
    game_date = st.date_input("Game Date", value=st.session_state.game_date)

    if st.button("Continue"):
        if not batter:
            st.warning("Please select a batter.")
        else:
            st.session_state.batter = batter
            st.session_state.game_date = game_date
            st.session_state.page = 'hit_entry'
            st.rerun()

# ------------------- PAGE 2 -------------------
elif st.session_state.page == 'hit_entry':
    st.header(f"Hit Entry for {st.session_state.batter} on {st.session_state.game_date}")

    col1, col2 = st.columns(2)

    with col2:
        # Outcome selection outside the form to allow immediate rerun
        st.markdown("### Outcome of the Play")
        outcome_choice = st.radio("Select Outcome Type", ["", "Out", "On Base"], index=["", "Out", "On Base"].index(st.session_state.outcome_label), key="outcome_radio")
        st.session_state.outcome_label = outcome_choice

        out_detail = None
        on_base_detail = None

        if outcome_choice == "Out":
            out_detail = st.selectbox("How did the batter get out?", [
                "", "Strikeout", "Groundout", "Flyout", "Lineout",
                "Popup", "Fielder's Choice", "Double Play", "Other"
            ])
        elif outcome_choice == "On Base":
            on_base_detail = st.selectbox("How did the batter reach base?", [
                "", "Single", "Double", "Triple", "Home Run",
                "Walk", "Hit By Pitch", "Error", "Fielder’s Choice (Safe)"
            ])

    # Direction buttons
    st.markdown("### Direction of Hit")
    colA, colB, colC, colD, colE, colF, colG = st.columns(7)
    with colA: if st.button("Left"): st.session_state.direction = "Left"
    with colB: if st.button("Left-Center"): st.session_state.direction = "Left-Center"
    with colC: if st.button("Center"): st.session_state.direction = "Center"
    with colD: if st.button("Right-Center"): st.session_state.direction = "Right-Center"
    with colE: if st.button("Right"): st.session_state.direction = "Right"
    with colF: if st.button("Infield"): st.session_state.direction = "Infield"
    with colG: if st.button("Foul"): st.session_state.direction = "Foul"

    # Hit form (separate from outcome radio so outcome reacts instantly)
    with st.form("hit_form", clear_on_submit=True):
        with col1:
            inning = st.number_input("Inning", min_value=1, max_value=20, step=1)
            pa_number = st.number_input("Plate Appearance Number", min_value=1, step=1)
            outs = st.number_input("Outs", min_value=0, max_value=2, step=1)
            men_on_base = st.selectbox("Men on Base", [
                "None", "1B", "2B", "3B",
                "1B & 2B", "1B & 3B", "2B & 3B", "Bases Loaded"
            ])
            balls = st.number_input("Balls", min_value=0, max_value=3, step=1)
            strikes = st.number_input("Strikes", min_value=0, max_value=2, step=1)

        submitted = st.form_submit_button("Submit Hit")

        if submitted:
            if not outcome_choice:
                st.warning("Please select an outcome.")
            else:
                try:
                    outcome_bool = True if outcome_choice == "On Base" else False
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO pitches_faced (
                            batter, date, inning, pa_number, outs, men_on_base,
                            balls, strikes, outcome, out_detail, on_base_detail, direction
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
                        outcome_bool,
                        out_detail,
                        on_base_detail,
                        st.session_state.direction
                    ))
                    conn.commit()
                    conn.close()
                    st.success("Hit saved!")

                    # Reset outcome and direction
                    st.session_state.outcome_label = ""
                    st.session_state.direction = None
                    st.rerun()

                except Exception as e:
                    st.error(f"Error saving hit: {e}")

    # Display game log
    try:
        conn = get_connection()
        df = pd.read_sql("""
            SELECT id, inning, pa_number, outs, balls, strikes, outcome, out_detail, on_base_detail, direction
            FROM pitches_faced
            WHERE batter = %s AND date = %s
            ORDER BY id ASC
        """, conn, params=(st.session_state.batter, st.session_state.game_date))
        conn.close()

        if df.empty:
            st.info("No entries for this game yet.")
        else:
            df["Play #"] = range(1, len(df) + 1)
            df = df[["Play #", "inning", "pa_number", "outs", "balls", "strikes", "outcome", "out_detail", "on_base_detail", "direction"]]
            st.dataframe(df.reset_index(drop=True), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading pitches_faced: {e}")

    if st.button("Back to Batter & Date"):
        st.session_state.page = 'batter_date'
        st.rerun()
