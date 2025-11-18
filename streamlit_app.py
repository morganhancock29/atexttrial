import streamlit as st
import re
import io
import csv
from datetime import datetime

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Team Sheet Extractor", layout="wide")
st.title("Team Sheet Extractor")

# -------------------------
# FAQ modal state
# -------------------------
if "show_faq" not in st.session_state:
    st.session_state.show_faq = False

# Top FAQ button
col_top_left, col_top_right = st.columns([0.15, 0.85])
with col_top_left:
    if st.button("📘 Open FAQ"):
        st.session_state.show_faq = True
with col_top_right:
    st.write("")  # spacer

# If FAQ is toggled, show FAQ block
if st.session_state.show_faq:
    st.markdown("---")
    st.header("FAQ")
    st.markdown(
        """
### ❗️ Why do some names not work?
- Lines with unusual formatting or invisible characters may be skipped.
- Lines with only one word are ignored to prevent errors.
- Lines in all lowercase may also be skipped.

### 📥 How to import CSV into aText
1. Export using **CSV**.
2. In aText: **File → Import → CSV**.
3. Choose:
   - Column 1 = Abbreviation
   - Column 2 = Text

### 📸 Why use TSV?
TSV is preferred for **Photo Mechanic** imports (preserves spacing and special characters).

### ✏️ Can I edit text before exporting?
Yes. The input box is editable and changes are reflected in downloads.

### ⚠️ Why might aText say "Error reading file"?
- File wasn't CSV
- Re-saved incorrectly (Excel changed encoding)
- Imported in wrong aText menu

### 🧹 Skip left column of numbers
Some team sheets include an index before jersey numbers, e.g.:
1 26 Taylor Smith
2 04 Jamie Doe
    
- If **Skip left column** is ON, the app removes the first number and uses the second.
- If lines already start with the actual number, leave **OFF**.
"""
    )
    if st.button("Close FAQ"):
        st.session_state.show_faq = False
    st.markdown("---")

# -------------------------
# Sidebar / Options
# -------------------------
st.sidebar.header("Options")
show_numbers = st.sidebar.checkbox("Include Numbers", value=True)
team_text = st.sidebar.text_input("Text to append after player name", value="")
file_name_input = st.sidebar.text_input("Filename (optional)", value="")

file_format = st.sidebar.selectbox("Download format", ["CSV", "TSV (PhotoMechanic)"])
skip_left_column = st.sidebar.checkbox("Skip left column of numbers", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("Paste team sheet text below:")

# -------------------------
# Main input
# -------------------------
input_text = st.text_area("Paste team sheet here", height=300)

# -------------------------
# Processing
# -------------------------
extracted_players = []
skipped_lines = []

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

name_particles = ["de", "van", "von", "da", "di", "le", "la", "del", "du", "mac", "mc"]

if input_text:
    lines = input_text.splitlines()
    for line in lines:
        original_line = line.strip()
        if not original_line:
            continue

        # skip section headings
        if any(original_line.lower().startswith(h.lower()) for h in ignore_words):
            continue

        # clean line
        line = re.sub(r"^[\*\s]+", "", original_line)
        line = re.sub(r"\(.*?\)", "", line)

        # remove trailing words
        for word in ignore_words + ignore_countries:
            line = re.sub(rf"\b{re.escape(word)}\b", "", line)

        # extract numbers
        numbers_in_line = re.findall(r"\d+", line)
        if skip_left_column:
            number = numbers_in_line[1] if len(numbers_in_line) > 1 else ""
            line_no_number = re.sub(r"^\d+\s+\d+\s*", "", line).strip()
        else:
            number = numbers_in_line[0] if numbers_in_line else ""
            line_no_number = re.sub(r"^\d+\s*", "", line).strip()

        line_no_number = re.sub(r"^(GK|DF|MF|FW|G|F|D)\b", "", line_no_number).strip()

        # extract names
        particles_regex = "|".join(re.escape(p) for p in name_particles)
        name_match = re.findall(
            rf"[A-Z][a-zA-Z'`.\-]+(?:\s(?:(?:{particles_regex})\s)?[A-Z][a-zA-Z'`.\-]+)+",
            line_no_number
        )

        if name_match:
            name = name_match[0].strip()
            if team_text:
                name = f"{name} {team_text}"
            if show_numbers and number:
                extracted_players.append(f"{number}\t{name}")
            else:
                extracted_players.append(name)
        else:
            skipped_lines.append(original_line)

# -------------------------
# Output & Download
# -------------------------
if extracted_players:
    st.subheader("Extracted Team Sheet")
    st.text("\n".join(extracted_players))

    base_filename = file_name_input.strip() if file_name_input.strip() else datetime.now().strftime("team_%Y%m%d_%H%M%S")

    if file_format == "CSV":
        filename = base_filename + ".csv"
        delimiter = ","
        mime = "text/csv"
    else:
        filename = base_filename + ".tsv"
        delimiter = "\t"
        mime = "text/tab-separated-values"

    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for player in extracted_players:
        if show_numbers and "\t" in player:
            number, name = map(str.strip, player.split("\t", 1))
        else:
            number = ""
            name = player
        writer.writerow([number, name])

    st.download_button(
        label=f"Download as {file_format}",
        data=output.getvalue(),
        file_name=filename,
        mime=mime
    )

    if skipped_lines:
        st.subheader("Skipped Lines (names not recognized)")
        st.text("\n".join(skipped_lines))
else:
    st.info("No player names detected. Make sure your team sheet is pasted correctly.")
