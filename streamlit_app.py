import streamlit as st
import re
import io
import csv
from datetime import datetime

st.set_page_config(page_title="Team Sheet Extractor", layout="wide")
st.title("Team Sheet Extractor")

# --- Sidebar ---
st.sidebar.header("Options")
use_second_number = st.sidebar.checkbox("Use second number as jersey", value=True)
team_text = st.sidebar.text_input("Text to append after player name", value="")
file_name_input = st.sidebar.text_input("Filename (optional)", value="")

# File format dropdown
file_format = st.sidebar.selectbox("Download format", ["CSV", "TSV"])

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

        # --- GET NUMBERS ---
        numbers = re.findall(r"\b\d+\b", line)
        number = ""
        if numbers:
            if use_second_number and len(numbers) > 1:
                number = numbers[1]  # Take the second number if ticked
            else:
                number = numbers[0]  # Take first number if unticked

        # Remove numbers from line for name extraction
        line_no_number = re.sub(r"^\d+\s*", "", line).strip()

        # NEW FIX: Remove GK / DF / MF / FW between number and name
        line_no_number = re.sub(r"^(GK|DF|MF|FW)\b", "", line_no_number).strip()

        # --- NAME EXTRACTION ---
        # Prefer 2+ capitalized words
        name_match = re.findall(r"[A-Z][a-zA-Z'`.-]+(?:\s[A-Z][a-zA-Z'`.-]+)+", line_no_number)

        # If none, try single capitalized word, only if safe
        if not name_match:
            single_name_match = re.findall(r"\b([A-Z][a-zA-Z'`.-]+)\b", line_no_number)
            if single_name_match:
                for candidate in single_name_match:
                    if candidate not in ignore_words + ignore_countries:
                        name_match = [candidate]
                        break  # Take first “safe” single word

        if name_match:
            name = name_match[0].strip()
            # Append team text
            if team_text:
                name += f" {team_text}"

            if number:
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
        if '\t' in player:
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
