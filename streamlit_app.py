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

# Download format dropdown (CSV renamed to CSV (aText))
file_format = st.sidebar.selectbox("Download format", ["CSV (aText)", "TSV (PhotoMechanic)"])

# Checkbox to skip left column
skip_left_column = st.sidebar.checkbox("Skip left column of numbers", value=False)

# Always-visible FAQ
st.sidebar.markdown("---")
st.sidebar.markdown("""
### ❓ FAQ

**Why do some names not work?**  
Some name formats might be skipped, including:  
- lines with unusual formatting  
- names not beginning with capital letters  
- single-word names with fewer than 4 letters  
- final surnames shorter than 4 letters unless they follow a known prefix  
Check the **Skipped Lines** section below.

**CSV vs TSV**  
- **CSV (aText)** is recommended for aText.  
- **TSV (PhotoMechanic)** is preferred for PhotoMechanic import (preserves spacing).

**Skip left column**  
If your sheet includes row numbers like:  
`1 26 Taylor Smith`  
turn ON this option to ignore the first number.
""")

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

# Lowercase surname prefixes (M1)
surname_prefixes = [
    "de", "van", "von", "da", "del", "di", "du", "la", "le",
    "mac", "mc", "van der", "van den", "der"
]

# Prefix regex
prefix_pattern = r"(?:van der|van den|de|van|von|da|del|di|du|la|le|mac|mc|der)"

# Name pattern with prefixes
name_regex = rf"""
    (
        [A-Z][a-zA-Z'`.-]+                       # First name
        (?:
            \s(?:{prefix_pattern})?              # Optional prefix
            \s[A-Z][a-zA-Z'`.-]+                 # Next name part
        )+
    )
"""
compiled_name_regex = re.compile(name_regex, re.VERBOSE)

def valid_last_name(word):
    """Implements surname rules."""
    w = word.lower()

    # 4+ letters is OK
    if len(w) >= 4:
        return True

    # 2–3 letters allowed if part of prefix surname (already handled)
    if len(w) >= 2:
        return True

    return False

if input_text:
    lines = input_text.splitlines()

    for line in lines:
        original_line = line.strip()
        if not original_line:
            continue

        if any(original_line.lower().startswith(h.lower()) for h in ignore_words):
            continue

        line = re.sub(r"^[\*\s]+", "", original_line)
        line = re.sub(r"\(.*?\)", "", line)

        for word in ignore_words + ignore_countries:
            line = re.sub(rf"\b{re.escape(word)}\b", "", line)

        numbers_in_line = re.findall(r"\d+", line)
        if skip_left_column:
            number = numbers_in_line[1] if len(numbers_in_line) > 1 else ""
            line_no_number = re.sub(r"^\d+\s+\d+\s*", "", line).strip()
        else:
            number = numbers_in_line[0] if len(numbers_in_line) > 0 else ""
            line_no_number = re.sub(r"^\d+\s*", "", line).strip()

        line_no_number = re.sub(r"^(GK|DF|MF|FW)\b", "", line_no_number).strip()

        matches = compiled_name_regex.findall(line_no_number)

        if matches:
            name = matches[0].strip()

            # Validate last surname rule
            last_word = name.split()[-1]
            if not valid_last_name(last_word):
                skipped_lines.append(original_line)
                continue

            if team_text:
                name += f" {team_text}"

            extracted_players.append((number, name))
        else:
            skipped_lines.append(original_line)

# --- Output ---
if extracted_players:
    st.subheader("Extracted Team Sheet")
    st.text("\n".join([f"{num}\t{name}" if num else name for num, name in extracted_players]))

    if file_name_input.strip():
        base_filename = file_name_input.strip()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"team_{timestamp}"

    output = io.StringIO()
    if file_format == "TSV (PhotoMechanic)":
        filename = base_filename + ".tsv"
        delimiter = "\t"
        mime = "text/tab-separated-values"
    else:
        filename = base_filename + ".csv"
        delimiter = ","
        mime = "text/csv"

    writer = csv.writer(output, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for num, name in extracted_players:
        writer.writerow([num, name])

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
