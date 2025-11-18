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
download_format = st.sidebar.selectbox("Download format", ["CSV", "TSV"])

st.sidebar.markdown("---")
st.sidebar.markdown("Paste team sheet text below:")

# --- Input ---
input_text = st.text_area("Paste team sheet here", height=350)

# --- Processing ---
extracted_players = []

# Words/positions to completely remove after name
ignore_words = [
    "All-rounders", "Wicketkeepers", "Bowlers",
    "Forwards", "Defenders", "Goalkeepers", "Midfielders",
    "Forward", "Defender", "Goalkeeper", "Midfielder",
    "GK", "DF", "MF", "FW",
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

        # Remove starting '*' or whitespace
        line = re.sub(r"^[\*\s]+", "", line)
        # Remove contents inside parentheses
        line = re.sub(r"\(.*?\)", "", line)

        # Split line into tokens
        tokens = line.split()
        if not tokens:
            continue

        # --- Determine jersey number ---
        jersey_number = ""
        name_tokens = []

        # Loop through tokens to find the first number after the name
        for i, token in enumerate(tokens):
            # Skip positions/countries
            if token in ignore_words + ignore_countries:
                continue
            # First token that is purely numeric is likely jersey number
            if token.isdigit() and not jersey_number:
                jersey_number = token
                name_tokens = tokens[:i]  # Everything before number is name
                break

        # If no numeric token found, treat entire line as name
        if not jersey_number:
            name_tokens = tokens

        # Build player name
        name = " ".join(name_tokens).strip()

        # Remove trailing positions/countries accidentally left
        name = " ".join([w for w in name.split() if w not in ignore_words + ignore_countries])

        # Append team text if given
        if team_text:
            name += f" {team_text}"

        # Format output
        if show_numbers and jersey_number:
            extracted_players.append(f"{jersey_number}\t{name}")
        else:
            extracted_players.append(name)

# --- Output ---
if extracted_players:
    st.subheader("Extracted Team Sheet")
    st.text("\n".join(extracted_players))

    # Determine filename
    if file_name_input.strip():
        filename = file_name_input.strip()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"team_{timestamp}"

    # Add proper extension
    if download_format == "CSV":
        filename += ".csv"
        delimiter = ","
        mime = "text/csv"
    else:
        filename += ".tsv"
        delimiter = "\t"
        mime = "text/tab-separated-values"

    # Prepare download
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter)
    for player in extracted_players:
        if show_numbers and '\t' in player:
            number, name = map(str.strip, player.split('\t', 1))
        else:
            number = ''
            name = player
        writer.writerow([number, name])

    st.download_button(
        label=f"Download as {download_format}",
        data=output.getvalue(),
        file_name=filename,
        mime=mime
    )
else:
    st.info("No player names detected. Make sure your team sheet is pasted correctly.")
