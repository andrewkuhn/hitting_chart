import streamlit as st
import psycopg2

# --- Supabase PostgreSQL connection (update with your credentials) ---
def get_connection():
    return psycopg2.connect(
        host="db.supabase.co",           # Replace with your Supabase DB host
        database="your_database_name",   # Replace with your DB name
        user="your_db_user",             # Replace with your DB user
        password="your_db_password",     # Replace with your DB password
        port=5432
    )

def get_batters():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM Batters ORDER BY name")
        batters = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return batters
    except Exception as e:
        st.error(f"Error loading batters: {e}")
        return []

st.title("Hitting Chart - Page 2: Enter Hits")

# Check for game date in session state
game_date = st.session_state.get("game_date", None)
if not game_date:
    st.error("Game date not set. Please go back to Page 1 and select the game date.")
    st.stop()

st.write(f"**Game Date:** {game_date}")

# Load batter dropdown
batters = get_batters()
batter = st.selectbox("Select Batter", options=[""] + batters)

inning = st.number_input("Inning", min_value=1, max_value=20, step=1)
pa_number = st.number_input("Plate Appearance Number", min_value=1, step=1)
balls = st.number_input("Balls", min_value=0, max_value=3, step=1)
strikes = st.number_input("Strikes", min_value=0, max_value=2, step=1)
outs = st.number_input("Outs", min_value=0, max_value=2, step=1)

men_on_base = st.selectbox("Men on Base", [
    "None", "1B", "2B", "3B",
    "1B & 2B", "1B & 3B", "2B & 3B", "Bases Loaded"
])

outcome_type = st.radio("Outcome Type", options=["", "Ball", "Out", "On Base", "Other"], index=0)

outcome = None
if outcome_type == "Ball":
    outcome = st.selectbox("Select Ball Outcome", [
        "Ball (Ball Count)", "Hit By Pitch"
    ])
elif outcome_type == "Out":
    outcome = st.selectbox("Select Out Type", [
        "Strikeout", "Groundout", "Flyout", "Lineout",
        "Popup", "Fielder's Choice (Out)", "Double Play", "Other Out"
    ])
elif outcome_type == "On Base":
    outcome = st.selectbox("Select On Base Type", [
        "Single", "Double", "Triple", "Home Run",
        "Walk", "Fielder’s Choice (Safe)", "Error"
    ])
elif outcome_type == "Other":
    outcome = st.text_input("Describe Outcome")

direction = st.selectbox("Direction of Hit", [
    "", "Left", "Left-Center", "Center", "Right-Center", "Right", "Infield", "Foul"
])

if st.button("Submit Hit"):
    if not batter:
        st.error("Please select a batter.")
    elif not outcome_type or outcome_type == "":
        st.error("Please select an outcome type.")
    elif outcome_type != "Other" and (not outcome or outcome == ""):
        st.error("Please select an outcome.")
    else:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO pitches_faced (
                    batter, date, inning, pa_number, outs, men_on_base,
                    balls, strikes, outcome_type, outcome, direction
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                batter, game_date, inning, pa_number, outs, men_on_base,
                balls, strikes, outcome_type, outcome, direction
            ))
            conn.commit()
            cur.close()
            conn.close()
            st.success("Hit data saved successfully!")
            # Optionally reset inputs here
        except Exception as e:
            st.error(f"Error saving data: {e}")

if st.button("Back to Game Date"):
    st.session_state.page = "page1"
    st.experimental_rerun()
