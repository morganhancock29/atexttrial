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

# File format dropdown
file_format = st.sidebar.selectbox("Download format", ["CSV", "TSV"])

# New checkbox: skip left column of numbers
skip_left_column = st.sidebar.checkbox("Skip left column of numbers", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("Paste team sheet text below:")

# --- Input ---
input_text = st.text_area("Paste team sheet here", height=250)

# --- Processing ---
extracted_players = []

# Words/positions to completely remove after name
ignore_words = [
    "All-rounders", "Wicketkeepers", "Bowlers",
    "Forwards", "Defenders", "Goalkeepers", "Midfielders",
    "Forward", "Defender", "Goalkeeper", "Midfielder",
    # Basketball positions
    "Point Guard", "PG", "Shooting Guard", "SG", "Small Forward", "SF",
    "Power Forward", "PF", "Center", "C"
]

# Countries to ignore
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
        # Remove leading '*' or whitespace
        line = re.sub(r"^[\*\s]+", "", line)
        # Remove content inside parentheses
        line = re.sub(r"\(.*?\)", "", line)
        # Remove any known positions / countries after the name
        for word in ignore_words + ignore_countries:
            line = re.sub(rf"\b{re.escape(word)}\b", "", line)

        # --- GET NUMBER ---
        # If skipping left column, use second number; else use first
        numbers_in_line = re.findall(r"\d+", line)
        if skip_left_column:
            number = numbers_in_line[1] if len(numbers_in_line) > 1 else ""
        else:
            number = numbers_in_line[0] if len(numbers_in_line) > 0 else ""

        # Remove the number(s) for name extraction
        if skip_left_column:
            # Remove first two numbers if they exist
            line_no_number = re.sub(r"^\d+\s+\d+\s*", "", line).strip()
        else:
            # Remove only the first number
            line_no_number = re.sub(r"^\d+\s*", "", line).strip()

        # NEW FIX: Remove GK / DF / MF / FW between number and name
        line_no_number = re.sub(r"^(GK|DF|MF|FW)\b", "", line_no_number).strip()

        # Extract name: look for 2+ capitalized words
        name_match = re.findall(r"[A-Z][a-zA-Z'`.-]+(?:\s[A-Z][a-zA-Z'`.-]+)+", line_no_number)
        if name_match:
            name = name_match[0].strip()

            # Append team text
            if team_text:
                name += f" {team_text}"

            if show_numbers and number:
                extracted_players.append(f"{number}\t{name}")
            else:
                extracted_players.append(name)

# --- Output ---
if extracted_players:
    st.subheader("Extracted Team Sheet")
    st.text("\n".join(extracted_players))

    # Determine filename
    if file_name_input.strip():
        base_filename = file_name_input.strip()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"team_{timestamp}"

    # Set extension based on dropdown
    if file_format == "CSV":
        filename = base_filename + ".csv"
        delimiter = ","
        mime = "text/csv"
    else:
        filename = base_filename + ".tsv"
        delimiter = "\t"
        mime = "text/tab-separated-values"

    # Build data
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter)
    for player in extracted_players:
        if show_numbers and '\t' in player:
            number, name = map(str.strip, player.split('\t', 1))
        else:
            number = ''
            name = player
        writer.writerow([number, name])

    file_data = output.getvalue()

    st.download_button(
        label=f"Download as {file_format}",
        data=file_data,
        file_name=filename,
        mime=mime
    )
else:
    st.info("No player names detected. Make sure your team sheet is pasted correctly.")
