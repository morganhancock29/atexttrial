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

# Checkbox: skip left column of numbers
skip_left_column = st.sidebar.checkbox("Skip left column of numbers", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("Paste team sheet text below:")

# --- Input ---
input_text = st.text_area("Paste team sheet here", height=250)

# --- Processing ---
extracted_players = []
skipped_lines = []

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

# Particles to keep with last name
particles = ["de", "van", "von", "del", "di", "le", "du", "la", "dos", "das"]

if input_text:
    lines = input_text.splitlines()
    for line in lines:
        original_line = line.strip()
        if not original_line:
            continue

        # Skip ignored headings
        if any(original_line.lower().startswith(h.lower()) for h in ignore_words):
            continue

        # --- CLEAN LINE ---
        line_clean = re.sub(r"^[\*\s]+", "", original_line)        # Remove leading '*' or whitespace
        line_clean = re.sub(r"\(.*?\)", "", line_clean)           # Remove content inside parentheses
        for word in ignore_words + ignore_countries:
            line_clean = re.sub(rf"\b{re.escape(word)}\b", "", line_clean)

        # --- GET NUMBER ---
        numbers_in_line = re.findall(r"\d+", line_clean)
        if skip_left_column:
            number = numbers_in_line[1] if len(numbers_in_line) > 1 else ""
            line_no_number = re.sub(r"^\d+\s+\d+\s*", "", line_clean).strip()
        else:
            number = numbers_in_line[0] if len(numbers_in_line) > 0 else ""
            line_no_number = re.sub(r"^\d+\s*", "", line_clean).strip()

        # Remove GK / DF / MF / FW between number and name
        line_no_number = re.sub(r"^(GK|DF|MF|FW)\b", "", line_no_number).strip()

        # Extract name: allow first+last, include particles
        name_match = re.findall(
            rf"[A-Z][a-zA-Z'`.-]+(?:\s(?:{'|'.join(particles)}\s)?[A-Z][a-zA-Z'`.-]+)+",
            line_no_number
        )

        if name_match:
            name = name_match[0].strip()
            if team_text:
                name += f" {team_text}"
            if show_numbers and number:
                extracted_players.append(f"{number}\t{name}")
            else:
                extracted_players.append(name)
        else:
            skipped_lines.append(original_line)

    # --- Output ---
    if extracted_players:
        st.subheader("Extracted Team Sheet")
        st.text("\n".join(extracted_players))

        # File output
        base_filename = file_name_input.strip() if file_name_input.strip() else datetime.now().strftime("team_%Y%m%d_%H%M%S")
        if file_format == "CSV":
            filename = f"{base_filename}.csv"
            delimiter = ","
            mime = "text/csv"
        else:
            filename = f"{base_filename}.tsv"
            delimiter = "\t"
            mime = "text/tab-separated-values"

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
            label=f"Download as {file_format}",
            data=output.getvalue(),
            file_name=filename,
            mime=mime
        )

    # --- Show input with skipped lines highlighted ---
    if skipped_lines:
        st.subheader("Input with Unrecognized Lines Highlighted")
        highlighted_text = ""
        for line in input_text.splitlines():
            if line.strip() in skipped_lines:
                highlighted_text += f"<span style='color:red'>{line}</span>\n"
            else:
                highlighted_text += f"{line}\n"
        st.markdown(f"<pre style='white-space: pre-wrap'>{highlighted_text}</pre>", unsafe_allow_html=True)

else:
    st.info("No player names detected. Make sure your team sheet is pasted correctly.")
