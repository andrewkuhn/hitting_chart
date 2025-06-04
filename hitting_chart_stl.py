import streamlit as st
import psycopg2
import pandas as pd
import datetime
import os

# --- DB Connection ---
def get_db_params():
    return {
        "dbname": st.secrets["DB_NAME"],
        "user": st.secrets["DB_USER"],
        "password": st.secrets["DB_PASSWORD"],
        "host": st.secrets["DB_HOST"],
        "port": st.secrets["DB_PORT"],
    }
st.title("Hitting Chart Tracker")

# --- Basic Inputs ---
batter = st.text_input("Batter Name")
pa_number = st.number_input("Plate Appearance Number", min_value=1, step=1)
balls = st.number_input("Balls", min_value=0, max_value=3, step=1)
strikes = st.number_input("Strikes", min_value=0, max_value=2, step=1)
men_on_base = st.selectbox("Men on Base", [
    "None", "1B", "2B", "3B",
    "1B & 2B", "1B & 3B", "2B & 3B", "Bases Loaded"
])
outs = st.number_input("Outs", min_value=0, max_value=2, step=1)
game_date = st.date_input("Game Date", datetime.now().date())
inning = st.number_input("Inning", min_value=1, max_value=20, step=1)

# --- Outcome Type Selection ---
outcome_type = st.radio("Outcome Type", options=["", "Ball", "Out", "On Base", "Other"], index=0)

# --- Outcome Specific Dropdowns ---
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

# --- Direction Dropdown ---
direction = st.selectbox("Direction of Hit", [
    "", "Left", "Left-Center", "Center", "Right-Center", "Right", "Infield", "Foul"
])

# --- Submit Button ---
if st.button("Submit Hit"):
    # Basic validation
    if not batter:
        st.error("Please enter the batter's name.")
    elif not outcome_type or not outcome:
        st.error("Please select the outcome type and specific outcome.")
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
            conn.close()
            st.success("Hit data saved successfully!")

            # Clear fields after submission (optional)
            st.experimental_rerun()

        except Exception as e:
            st.error(f"Error saving data: {e}")
