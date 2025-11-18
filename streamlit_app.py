import streamlit as st
import re
import io
import csv
from datetime import datetime

st.set_page_config(page_title="Team Sheet Extractor", layout="wide")
st.title("Team Sheet Extractor")

# --- Sidebar ---
st.sidebar.header("Options")
show_numbers = st.sidebar.checkbox("Include Numbers", value=True)
team_text = st.sidebar.text_input("Text to append after player name", value="")
file_name_input = st.sidebar.text_input("Filename (optional)", value="")
file_format = st.sidebar.selectbox("Download format", ["CSV", "TSV"])
skip_left_column = st.sidebar.checkbox("Skip left column numbers", value=False)  # tick = skip left column

st.sidebar.markdown("---")
st.sidebar.markdown("Paste team sheet text below:")

# --- Input ---
input_text = st.text_area("Paste team sheet here", height=250)

# --- Processing ---
extracted_players = []

ignore_words = [
    "All-rounders", "Wicketkeepers", "Bowlers",
    "Forwards", "Defenders", "Goalkeepers", "Midfielders",
    "Forward", "Defender", "Goalkeeper", "Midfielder",
    "Point Guard", "PG", "Shooting Guard", "SG", "Small Forward", "SF",
    "Power Forward", "PF", "Center", "C"
]

ignore_countries = [
    "Australia", "AUS", "New Zealand", "NZ", "United States", "America", "USA", "Canada",
    "England", "South Africa", "India", "Pakistan", "Sri Lanka", "West Indies",
    "Bangladesh", "Afghanistan", "Ireland", "Scotland", "Netherlands", "Germany", "France",
    "Italy", "Spain", "Portugal", "Belgium", "Greece", "Turkey", "China", "Japan", "Korea",
    "Brazil", "Argentina", "Mexico", "Sweden", "Norway", "Denmark", "Finland", "Poland",
    "Russia", "Ukraine", "Egypt", "Morocco", "Nigeria"
]

if input_text:
    lines = input_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip ignored headings
        if any(line.lower().startswith(h.lower()) for h in ignore_words):
            continue

        # --- CLEAN LINE ---
        line = re.sub(r"^[\*\s]+", "", line)  # Remove leading '*' or whitespace
        line = re.sub(r"\(.*?\)", "", line)   # Remove content inside parentheses
        for word in ignore_words + ignore_countries:
            line = re.sub(rf"\b{re.escape(word)}\b", "", line)

        # --- GET NUMBER & NAME ---
        num_match = re.findall(r"\d+", line)
        number = ""
        line_no_number = line

        if skip_left_column:
            # If skipping left column, take the first number as jersey
            if num_match:
                number = num_match[0]
                line_no_
