import streamlit as st
import psycopg2
import pandas as pd
import datetime

# db setup
def get_db_params():
    return {
        "dbname": st.secrets["DB_NAME"],
        "user": st.secrets["DB_USER"],
        "password": st.secrets["DB_PASSWORD"],
        "host": st.secrets["DB_HOST"],
        "port": st.secrets["DB_PORT"],
    }

def get_connection():
    params = get_db_params()
    return psycopg2.connect(**params)

# table check
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

# batters db
def get_batters():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM batters ORDER BY name")
    batters = [row[0] for row in cur.fetchall()]
    conn.close()
    return batters

# session state setup
if 'page' not in st.session_state:
    st.session_state.page = 'batter_date'
if 'batter' not in st.session_state:
    st.session_state.batter = None
if 'game_date' not in st.session_state:
    st.session_state.game_date = datetime.date.today()

st.title("Hitting Chart")

# page 1
if st.session_state.page == 'batter_date':
    st.header("Select Batter and Date")

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

# page 2
elif st.session_state.page == 'hit_entry':
    st.header(f"Hit Entry for {st.session_state.batter} on {st.session_state.game_date}")

    with st.form("hit_form"):
        col1, col2 = st.columns(2)

        with col1:
            inning = st.number_input("Inning", min_value=1, max_value=20, step=1)
            pa_number = st.number_input("Plate Appearance Number", min_value=1, step=1)
            outs = st.number_input("Outs", min_value=0, max_value=2, step=1)
            men_on_base = st.selectbox("Men on Base", [
                "None", "1B", "2B", "3B", 
                "1B & 2B", "1B & 3B", "2B & 3B", "Bases Loaded"
            ])

        with col2:
            balls = st.number_input("Balls", min_value=0, max_value=3, step=1)
            strikes = st.number_input("Strikes", min_value=0, max_value=2, step=1)
            outcome_label = st.selectbox("Outcome of the Play", ["", "Out", "On Base"])

            outcome = None
            out_detail = None
            on_base_detail = None

            if outcome_label == "Out":
                outcome = False
                out_detail = st.selectbox("How did the batter get out?", [
                    "", "Strikeout", "Groundout", "Flyout", "Lineout", 
                    "Popup", "Fielder's Choice", "Double Play", "Other"
                ])
            elif outcome_label == "On Base":
                outcome = True
                on_base_detail = st.selectbox("How did the batter reach base?", [
                    "", "Single", "Double", "Triple", "Home Run", 
                    "Walk", "Hit By Pitch", "Error", "Fielder’s Choice (Safe)"
                ])

        st.markdown("### Direction of Hit")
        direction = st.radio(
            "Select Hit Direction:",
            ["", "Left", "Left-Center", "Center", "Right-Center", "Right", "Infield", "Foul"],
            horizontal=True
        )

        submitted = st.form_submit_button("Submit Hit")

        if submitted:
            if not outcome_label:
                st.warning("Please select an outcome.")
            elif outcome_label == "Out" and not out_detail:
                st.warning("Please select how the batter got out.")
            elif outcome_label == "On Base" and not on_base_detail:
                st.warning("Please select how the batter got on base.")
            elif direction == "":
                st.warning("Please select a hit direction.")
            else:
                try:
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
                        outcome,
                        out_detail,
                        on_base_detail,
                        direction
                    ))
                    conn.commit()
                    conn.close()
                    st.success("Hit saved!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error saving hit: {e}")

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
            df = df[[
                "Play #", "inning", "pa_number", "outs", "balls", "strikes",
                "outcome", "out_detail", "on_base_detail", "direction"
            ]]
            st.dataframe(
                df.reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )

    except Exception as e:
        st.error(f"Error loading pitches_faced: {e}")

    if st.button("Back to Batter & Date"):
        st.session_state.page = 'batter_date'
        st.rerun()
