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

# Download format dropdown (CSV FIRST)
file_format = st.sidebar.selectbox("Download format", ["CSV (general)", "TSV (PhotoMechanic)"])

# Checkbox: skip left column of numbers
skip_left_column = st.sidebar.checkbox("Skip left column of numbers", value=False)

# --- FAQ Box (always visible) ---
st.sidebar.markdown(
    """
### 📘 FAQ

**How to paste team sheets:**  
Copy the text from your source and paste it into the main text box.

**Skip left column:**  
Use this if your team sheet has row numbers in the first column that you want to ignore.

**Names not recognized:**  
Some name formats may be skipped, including single-word names shorter than 4 letters or lines with unusual formatting.  
Check the **Skipped Lines** section below for anything the tool couldn’t detect.

**CSV vs TSV:**  
CSV works in aText.  
TSV is preferred for **Photo Mechanic** imports because it preserves spacing and special characters.
"""
)

st.sidebar.markdown("---")
st.sidebar.markdown("Paste team sheet text below:")

# --- Input ---
input_text = st.text_area("Paste team sheet here", height=250)

# --- Processing ---
extracted_players = []
skipped_lines = []

# Words/positions to remove after name
ignore_words = [
    "All-rounders", "Wicketkeepers", "Bowlers",
    "Forwards", "Defenders", "Goalkeepers", "Midfielders",
    "Forward", "Defender", "Goalkeeper", "Midfielder",
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

# Common lowercase particles in names
name_particles = ["de", "van", "von", "da", "di", "le", "la", "del", "du", "Mac", "Mc"]

if input_text:
    lines = input_text.splitlines()
    for line in lines:
        original_line = line.strip()
        if not original_line:
            continue

        # Ignore if line starts with category words
        if any(original_line.lower().startswith(h.lower()) for h in ignore_words):
            continue

        # Clean symbols
        line = re.sub(r"^[\*\s]+", "", original_line)
        line = re.sub(r"\(.*?\)", "", line)

        # Remove unwanted words and countries
        for word in ignore_words + ignore_countries:
            line = re.sub(rf"\b{re.escape(word)}\b", "", line)

        # Extract numbers
        numbers_in_line = re.findall(r"\d+", line)
        if skip_left_column:
            number = numbers_in_line[1] if len(numbers_in_line) > 1 else ""
            line_no_number = re.sub(r"^\d+\s+\d+\s*", "", line).strip()
        else:
            number = numbers_in_line[0] if len(numbers_in_line) > 0 else ""
            line_no_number = re.sub(r"^\d+\s*", "", line).strip()

        # Remove position codes
        line_no_number = re.sub(r"^(GK|DF|MF|FW)\b", "", line_no_number).strip()

        # Detect multi-word names
        particles_regex = "|".join(name_particles)
        name_match = re.findall(
            rf"[A-Z][a-zA-Z'`.-]+(?:\s(?:{particles_regex})?\s?[A-Z][a-zA-Z'`.-]+)+",
            line_no_number
        )

        # If not found, detect single names (4+ letters, first letter capital)
        if not name_match:
            single_name_match = re.findall(r"\b[A-Z][a-zA-Z'`.-]{3,}\b", line_no_number)
            if single_name_match:
                name_match = [single_name_match[0]]

        # If still nothing, skip
        if name_match:
            name = name_match[0].strip()
            if team_text:
                name += f" {team_text}"
            extracted_players.append((number, name))
        else:
            skipped_lines.append(original_line)

# --- Output ---
if extracted_players:
    st.subheader("Extracted Team Sheet")
    st.text("\n".join([f"{num}\t{name}" if num else name for num, name in extracted_players]))

    # Filename
    if file_name_input.strip():
        base_filename = file_name_input.strip()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"team_{timestamp}"

    # Output file type
    output = io.StringIO()
    if file_format == "CSV (general)":
        filename = base_filename + ".csv"
        delimiter = ","
        mime = "text/csv"
    else:
        filename = base_filename + ".tsv"
        delimiter = "\t"
        mime = "text/tab-separated-values"

    writer = csv.writer(output, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for num, name in extracted_players:
        writer.writerow([num, name])

    file_data = output.getvalue()

    st.download_button(
        label=f"Download as {file_format}",
        data=file_data,
        file_name=filename,
        mime=mime
    )

    if skipped_lines:
        st.subheader("Skipped Lines (names not recognized)")
        st.text("\n".join(skipped_lines))
else:
    st.info("No player names detected. Make sure your team sheet is pasted correctly.")
