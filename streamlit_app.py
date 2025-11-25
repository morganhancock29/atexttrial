import streamlit as st
import re
import io
import csv
from datetime import datetime

st.set_page_config(page_title="Team Sheet Extractor", layout="wide")
st.title("Team Sheet Extractor")

# --- Sidebar ---
st.sidebar.header("Options")
include_numbers = st.sidebar.checkbox("Include Numbers", value=True)  # Default ON

prefix_text = st.sidebar.text_input("Prefix before number (optional)", value="")
team_text = st.sidebar.text_input("Text to append after player name", value="")
file_name_input = st.sidebar.text_input("Filename (optional)", value="")

# Download format dropdown
file_format = st.sidebar.selectbox("Download format", ["CSV (aText)", "TSV (PhotoMechanic)"])

# FAQ box
st.sidebar.markdown("---")
st.sidebar.markdown("""
### ❓ FAQ

**Why do some names not work?**  
Poor formatting, missing capital letters, or unexpected structures can prevent detection.  
Check the **Potential Issues** section near the bottom.

**CSV vs TSV**  
- **CSV (aText)** is recommended for aText  
- **TSV (PhotoMechanic)** preserves spacing and special characters

""")

st.sidebar.markdown("---")
st.sidebar.markdown("Paste team sheet text below:")

# --- Input ---
input_text = st.text_area("Paste team sheet here", height=250)

# --- Processing ---
extracted_players = []
skipped_lines = []
potential_issues = []

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

surname_prefixes = ["de", "van", "von", "da", "del", "di", "du", "la", "le", "Mac", "Mc", "van der", "van den", "der"]
prefix_pattern = r"(?:van der|van den|de|van|von|da|del|di|du|la|le|Mac|Mc|der)?"

# --- AUTO-DETECT LEFT INDEX NUMBERS ---
auto_skip_left = False
if input_text:
    sample_lines = [l.strip() for l in input_text.splitlines() if l.strip()]
    double_number_pattern = re.compile(r"^\d+\s+\d+\s+")
    double_count = sum(1 for l in sample_lines if double_number_pattern.match(l))

    if len(sample_lines) > 3 and double_count / len(sample_lines) >= 0.8:
        auto_skip_left = True
        st.info("Detected left-column index numbers — ignoring the first number automatically.")

# --- Main Loop ---
if input_text:
    lines = input_text.splitlines()

    for line in lines:
        original_line = line.strip()
        if not original_line:
            continue

        # Skip role headings
        if any(original_line.lower().startswith(h.lower()) for h in ignore_words):
            continue

        # Clean line
        line_clean = re.sub(r"^[\*\s]+", "", original_line)
        line_clean = re.sub(r"\(.*?\)", "", line_clean)
        for word in ignore_words + ignore_countries:
            line_clean = re.sub(rf"\b{re.escape(word)}\b", "", line_clean)

        # --- Number extraction with auto-skip-left ---
        numbers_in_line = re.findall(r"\d+", line_clean)

        if auto_skip_left:
            number = numbers_in_line[1] if len(numbers_in_line) > 1 else ""
            line_no_number = re.sub(r"^\d+\s+\d+\s*", "", line_clean).strip()
        else:
            number = numbers_in_line[0] if len(numbers_in_line) > 0 else ""
            line_no_number = re.sub(r"^\d+\s*", "", line_clean).strip()

        # Remove football role codes
        line_no_number = re.sub(r"^(GK|DF|MF|FW)\b", "", line_no_number).strip()

        # Capitalize first letter for regex purposes
        line_parsed = line_no_number
        if line_parsed and line_parsed[0].islower():
            line_parsed = line_parsed[0].upper() + line_parsed[1:]

        # Name regex
        multi_name_regex = re.compile(
            rf"[A-Z][a-zA-Z'`.-]+(?:\s{prefix_pattern}\s?[A-Z][a-zA-Z'`.-]+)+"
        )
        single_name_regex = re.compile(r"\b[A-Z][a-zA-Z'`.-]{3,}\b")

        match = multi_name_regex.search(line_parsed)
        if match:
            name = match.group().strip()
        else:
            match_single = single_name_regex.search(line_parsed)
            name = match_single.group().strip() if match_single else None

        # --- Meaningful issue detection ---
        issue_reason = None
        if not name:
            issue_reason = "No valid name detected"
        elif " " not in name and name[0].isupper() and len(name) < 4:
            issue_reason = "Name too short"
        elif name != name.title():
            issue_reason = "Possible missing capital letters in surname"

        if issue_reason:
            potential_issues.append(f"{original_line}  →  {issue_reason}")

        if name:
            # Append team text
            if team_text:
                name += f" {team_text}"

            # Add prefix before number
            if include_numbers and number and prefix_text:
                number = f"{prefix_text}{number}"

            extracted_players.append((number, name))
        else:
            skipped_lines.append(original_line)

# --- Output ---
if extracted_players:
    st.subheader("Extracted Team Sheet")
    st.text("\n".join([f"{num}\t{name}" if include_numbers and num else name for num, name in extracted_players]))

    if file_name_input.strip():
        base_filename = file_name_input.strip()
    else:
        base_filename = f"team_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

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
        if include_numbers:
            writer.writerow([num, name])
        else:
            writer.writerow(["", name])

    st.download_button(
        label=f"Download as {file_format}",
        data=output.getvalue(),
        file_name=filename,
        mime=mime
    )

    # --- Potential Issues ---
    if potential_issues:
        st.subheader("⚠️ Potential Problems")
        st.text("\n".join(potential_issues))

    # --- Skipped lines ---
    if skipped_lines:
        st.subheader("Skipped Lines (names not recognized)")
        st.text("\n".join(skipped_lines))

else:
    st.info("No player names detected. Make sure your team sheet is pasted correctly.")
