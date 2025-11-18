import streamlit as st
import re
import io
from datetime import datetime

st.set_page_config(page_title="Team Sheet Extractor for aText", layout="wide")
st.title("Team Sheet Extractor → aText Export")

# --- Sidebar ---
st.sidebar.header("Options")
show_numbers = st.sidebar.checkbox("Include Numbers", value=True)
team_text = st.sidebar.text_input("Text to append after player name", value="")
file_name_input = st.sidebar.text_input("Filename (optional)", value="")

# Checkbox: skip left column of numbers
skip_left_column = st.sidebar.checkbox("Skip left column of numbers", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("Paste team sheet text below:")

# --- Input ---
input_text = st.text_area("Paste team sheet here", height=250)

# --- Processing ---
extracted_players = []
skipped_lines = []

ignore_words = [
    "All-rounders", "Wicketkeepers", "Bowlers",
    "Forwards", "Defenders", "Goalkeepers", "Midfielders",
    "Forward", "Defender", "Goalkeeper", "Midfielder",
    # Basketball positions
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

# Common lowercase name particles
name_particles = ["de", "van", "von", "da", "di", "le", "la", "del", "du", "Mac", "Mc"]

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
        line = re.sub(r"^[\*\s]+", "", original_line)
        line = re.sub(r"\(.*?\)", "", line)
        for word in ignore_words + ignore_countries:
            line = re.sub(rf"\b{re.escape(word)}\b", "", line)

        # --- GET NUMBER ---
        numbers_in_line = re.findall(r"\d+", line)
        if skip_left_column:
            number = numbers_in_line[1] if len(numbers_in_line) > 1 else ""
            line_no_number = re.sub(r"^\d+\s+\d+\s*", "", line).strip()
        else:
            number = numbers_in_line[0] if len(numbers_in_line) > 0 else ""
            line_no_number = re.sub(r"^\d+\s*", "", line).strip()

        line_no_number = re.sub(r"^(GK|DF|MF|FW)\b", "", line_no_number).strip()

        # --- NAME EXTRACTION ---
        particles_regex = "|".join(name_particles)
        name_match = re.findall(
            rf"[A-Z][a-zA-Z'`.-]+(?:\s(?:{particles_regex})?\s?[A-Z][a-zA-Z'`.-]+)+",
            line_no_number
        )

        if name_match:
            name = name_match[0].strip()
            if team_text:
                name += f" {team_text}"
            extracted_players.append((number, name))
        else:
            skipped_lines.append(original_line)

# --- Output ---
if extracted_players:
    st.subheader("Extracted Team Sheet for aText")
    st.text("\n".join(f"{num}\t{name}" for num, name in extracted_players))

    # Determine filename
    if file_name_input.strip():
        base_filename = file_name_input.strip()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"atext_export_{timestamp}"

    filename = base_filename + ".txt"  # Tab-delimited text for aText

    # Build tab-delimited data
    output = io.StringIO()
    for number, name in extracted_players:
        output.write(f"{number}\t{name}\n")

    file_data = output.getvalue()

    st.download_button(
        label="Download as aText-ready TXT",
        data=file_data,
        file_name=filename,
        mime="text/plain"
    )

    if skipped_lines:
        st.subheader("Skipped Lines (names not recognized)")
        st.text("\n".join(skipped_lines))
else:
    st.info("No player names detected. Make sure your team sheet is pasted correctly.")
