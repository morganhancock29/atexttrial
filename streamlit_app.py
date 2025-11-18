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
skip_left_column = st.sidebar.checkbox("Skip left column numbers", value=False)

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

        # --- NUMBER & NAME EXTRACTION ---
        number = ""
        name = ""

        if skip_left_column:
            # Treat first numeric token as jersey number (ignore left column)
            tokens = line.split()
            numeric_tokens = [token for token in tokens if token.isdigit()]
            if numeric_tokens:
                number = numeric_tokens[0]
                first_num_index = tokens.index(numeric_tokens[0])
                name_tokens = tokens[first_num_index + 1:]
            else:
                name_tokens = tokens
        else:
            # Old logic: use second number if there are two numbers at start
            tokens = line.split()
            numeric_tokens = [token for token in tokens if token.isdigit()]
            if len(numeric_tokens) >= 2:
                number = numeric_tokens[1]
                second_num_index = tokens.index(numeric_tokens[1])
                name_tokens = tokens[second_num_index + 1:]
            elif numeric_tokens:
                number = numeric_tokens[0]
                first_num_index = tokens.index(numeric_tokens[0])
                name_tokens = tokens[first_num_index + 1:]
            else:
                name_tokens = tokens

        # Remove positions like GK / DF / MF / FW at start of name_tokens
        if name_tokens and re.match(r"^(GK|DF|MF|FW)$", name_tokens[0]):
            name_tokens = name_tokens[1:]

        # Extract name: only include capitalized words
        name_words = [w for w in name_tokens if re.match(r"^[A-Z][a-zA-Z'`.-]+", w)]
        if name_words:
            name = " ".join(name_words)
            if team_text:
                name += f" {team_text}"
            if show_numbers and number:
                extracted_players.append(f"{number}\t{name}")
            else:
                extracted_players.append(name)

# --- Output ---
if extracted_players:
    st.subheader("Extracted Team Sheet")
    st.text("\n".join([p.replace("\t", " | ") for p in extracted_players]))

    # Determine filename
    base_filename = file_name_input.strip() if file_name_input.strip() else datetime.now().strftime("team_%Y%m%d_%H%M%S")
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
        if show_numbers and "\t" in player:
            number, name = map(str.strip, player.split("\t", 1))
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
