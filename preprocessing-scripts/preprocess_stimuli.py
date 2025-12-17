import os
import re
import pandas as pd

DEFINITE_ARTICLES_REGEX = r"(?<=\b)(der|die|das|den|dem|des)(?=\b)"

# Column labels
STIMULUS_COLUMN = "stimulussatz"
CRITICAL_PHRASE_COLUMN = "anapher"
CRITICAL_PHRASE_IDX_COLUMN = "anapherIdx"
ITEM_NUMBER_COLUMN = "itemNummer"

# Load data
stimuli_csv = os.path.abspath(os.path.join("..", "input", "stimuli.csv"))
stimuli_data = pd.read_csv(stimuli_csv, dtype={ITEM_NUMBER_COLUMN: str})

# Strip whitespace from all string cells and convert empty entries to NaN
stimuli_data = stimuli_data.applymap(
    lambda x: x.strip() if isinstance(x, str) else x
)
stimuli_data = stimuli_data.replace('', pd.NA)

# Drop rows with empty stimulus and/or item number column
stimuli_data.dropna(subset=[STIMULUS_COLUMN, ITEM_NUMBER_COLUMN])
# (should be dropped already but just in case) drop rows which are totally empty
stimuli_data = stimuli_data.dropna(how='all')

# Add forward-slash as word chunk delimiter and mark the critical region with an asterisk
def annotate_critical_phrase(stimulus, critical_phrase):
    if critical_phrase in stimulus:
        stimulus = stimulus.replace(critical_phrase, "*" + critical_phrase + "*")
    else:
        # Define regular expression which would match the critical phrase in another inflection
        noun = critical_phrase.split()[-1]
        critical_phrase_regex = rf"{DEFINITE_ARTICLES_REGEX}(\s+{noun}(e?[nmsr])?)"
        if re.search(critical_phrase_regex, stimulus):
            stimulus = re.sub(critical_phrase_regex, r"*\1\2*", stimulus)
        else:
            print(f"Could not automatically annotate critical region: {stimulus} | {critical_phrase}")
    return stimulus

def chunk_stimulus(stimulus):
    # Convert forward-slashes to whitespace (in case input is already chunked)
    stimulus = re.sub(r'\/+', ' ', stimulus)
    # Convert whitespace (back) to forward-slashes
    stimulus = re.sub(r'\s', '/', stimulus)
    # Convert forward-slashes within asterisk pairs back to whitespace
    stimulus = re.sub(r'(\*[^\*]*?)/([^\*]*?\*)', r'\1 \2', stimulus)
    return stimulus

def index_critical_phrase(stimulus):
    chunks = stimulus.split("/")
    for i, chunk in enumerate(chunks):
        if "*" in chunk:
            return i

def split_stimulus_sentences(stimulus):
    return re.sub(r"\./", ".//", stimulus)

stimuli_data[STIMULUS_COLUMN] = stimuli_data.apply(
    lambda row: annotate_critical_phrase(
        row[STIMULUS_COLUMN],
        row[CRITICAL_PHRASE_COLUMN]
    ),
    axis=1
)
stimuli_data[STIMULUS_COLUMN] = stimuli_data[STIMULUS_COLUMN].apply(chunk_stimulus)

# Split first and second sentence of stimulus text with double-slash
stimuli_data[STIMULUS_COLUMN] = stimuli_data.apply(
    lambda row: split_stimulus_sentences(row[STIMULUS_COLUMN]),
    axis=1
)

# Add column indicating which chunk index the critical phrase is at
stimuli_data[CRITICAL_PHRASE_IDX_COLUMN] = stimuli_data.apply(
    lambda row: index_critical_phrase(
        row[STIMULUS_COLUMN]
    ),
    axis=1
)

# Write cleaned CSV
outfile = os.path.join("..", "pcibex-resources", "stimuli_preprocessed")
stimuli_data.to_csv(outfile + ".csv", index=False)
stimuli_data.to_excel(outfile + ".xlsx", index=False)
print(f"Wrote preprocessed stimuli to {outfile}.csv")
print(f"Wrote preprocessed stimuli to {outfile}.xlsx")
