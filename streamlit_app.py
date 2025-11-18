import streamlit as st
import re
import io
import csv
from datetime import datetime

st.set_page_config(page_title="Team Sheet Extractor", layout="wide")
st.title("Team Sheet Extractor")

# --- Sidebar Options ---
st.sidebar.header("Options")
include_numbers = st.sidebar.checkbox("Include Numbers", value=True)
file_format = st.sidebar.selectbox("Download format", ["CSV (aText)", "TSV (PhotoMechanic)"])
file_name_input = st.sidebar.text_input("Filename (optional)", value="team_sheet")
skip_left_column = st.sidebar.checkbox("Skip left column of numbers", value=False)

# --- FAQ ---
st.sidebar.markdown("### FAQ")
st.sidebar.markdown("""
- **How to paste team sheets:** Copy text from your source and paste it in the main text box.  
- **Include numbers:** By default, player numbers are included in the output. Uncheck to remove them.  
- **Skip left column:** Use this if your team sheet has row numbers in the first column you want to ignore.  
- **Names not recognized:** Some unusual name formats might be skipped; check the 'Skipped Lines' section below.  
- **CSV vs TSV:** CSV works in aText; TSV is preferred for PhotoMechanic import.
""")

# --- Input ---
st.markdown("---")
st.markdown("### Paste team sheet text below:")
input_text = st.text_area("", height=300)

# --- Processing ---
extracted_players = []
skipped_lines = []

# Name particles to allow lowercase middle parts
name_particles = ["de", "van", "von", "da", "di", "le", "la", "del", "du", "Mac", "Mc", "O'"]

if input_text:
    lines = input_text.splitlines()
    for line in lines:
        original_line = line.strip()
        if not original_line:
            continue

        # Remove left index/number if required
        numbers_in_line = re.findall(r"\d+", original_line)
        if skip_left_column:
            number = numbers_in_line[1] if len(numbers_in_line) > 1 else ""
            line_no_number = re.sub(r"^\d+\s+\d+\s*", "", original_line).strip()
        else:
            number = numbers_in_line[0] if len(numbers_in_line) > 0 else ""
            line_no_number = re.sub(r"^\d+\s*", "", original_line).strip()

        # Remove parentheticals (country tags, etc.)
        line_no_number = re.sub(r"\(.*?\)", "", line_no_number)

        # Regex for first + last names, allowing optional particles
        particles_regex = "|".join(name_particles)
        name_match = re.findall(
            rf"\b[A-Z][a-zA-Z'`.-]+(?:\s(?:{particles_regex})\s)?[A-Z][a-zA-Z'`.-]+|\b[A-Z][a-zA-Z'`.-]{{3,}}\b",
            line_no_number
        )

        if name_match:
            name = name_match[0].strip()
            if include_numbers and number:
                extracted_players.append((number, name))
            else:
                extracted_players.append(("", name))
        else:
            skipped_lines.append(original_line)

# --- Output ---
if extracted_players:
    st.subheader("Extracted Team Sheet")
    st.text("\n".join([f"{num}\t{name}" if num else name for num, name in extracted_players]))

    # Determine filename
    base_filename = file_name_input.strip() or datetime.now().strftime("team_%Y%m%d_%H%M%S")

    output = io.StringIO()
    if file_format == "CSV (aText)":
        delimiter = ","
        mime = "text/csv"
        filename = f"{base_filename}.csv"
    else:
        delimiter = "\t"
        mime = "text/tab-separated-values"
        filename = f"{base_filename}.tsv"

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
