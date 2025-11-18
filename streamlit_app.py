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

        # --- CLEAN LINE ---
        # Remove leading '*' or whitespace
        line = re.sub(r"^[\*\s]+", "", line)
        # Remove content inside parentheses
        line = re.sub(r"\(.*?\)", "", line)
        # Remove any known positions / countries after the name
        for word in ignore_words + ignore_countries:
            line = re.sub(rf"\b{re.escape(word)}\b", "", line)

        # Split line into tokens
        tokens = line.split()
        if not tokens:
            continue

        # --- Determine jersey number ---
        jersey_number = ""
        name_tokens = []

        # Collect all numeric tokens at the start
        numeric_tokens = [token for token in tokens if token.isdigit()]

        # If the first token is just a line index, pick the second numeric token
        if len(numeric_tokens) >= 2:
            jersey_number = numeric_tokens[1]
            second_num_index = tokens.index(numeric_tokens[1])
            name_tokens = tokens[second_num_index + 1:]
        elif len(numeric_tokens) == 1:
            jersey_number = numeric_tokens[0]
            first_num_index = tokens.index(numeric_tokens[0])
            name_tokens = tokens[first_num_index + 1:]
        else:
            # No numeric token found, treat entire line as name
            name_tokens = tokens

        # Extract name: only include capitalized words (handles hyphenated names too)
        name_words = [w for w in name_tokens if re.match(r"^[A-Z][a-zA-Z'`.-]+", w)]
        if not name_words:
            continue
        name = " ".join(name_words)

        # Append team text
        if team_text:
            name += f" {team_text}"

        if show_numbers and jersey_number:
            extracted_players.append(f"{jersey_number}\t{name}")  # Use tab internally
        else:
            extracted_players.append(name)

# --- Output ---
if extracted_players:
    st.subheader("Extracted Team Sheet")
    st.text("\n".join([p.replace("\t", " | ") for p in extracted_players]))

    # Determine filename
    if file_name_input.strip():
        base_filename = file_name_input.strip()
    else:
        base_filename = datetime.now().strftime("team_%Y%m%d_%H%M%S")

    if download_format == "CSV":
        filename = base_filename if base_filename.lower().endswith(".csv") else base_filename + ".csv"
        delimiter = ","
        mime_type = "text/csv"
    else:
        filename = base_filename if base_filename.lower().endswith(".tsv") else base_filename + ".tsv"
        delimiter = "\t"
        mime_type = "text/tab-separated-values"

    # Write output
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter)
    for player in extracted_players:
        if show_numbers and "\t" in player:
            number, name = map(str.strip, player.split("\t", 1))
        else:
            number = ''
            name = player
        writer.writerow([number, name])
    file_data = output.getvalue()

    st.download_button(
        label=f"Download as {download_format}",
        data=file_data,
        file_name=filename,
        mime=mime_type
    )
else:
    st.info("No player names detected. Make sure your team sheet is pasted correctly.")
