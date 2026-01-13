import argparse
from collections import defaultdict
import pandas as pd
import re


COMMENT_CH = "#"
RESULTS_SPLIT_PATTERN = re.compile(r"^# Results on .*GMT$")


class ParticipantResults:
    counter = 0

    def __init__(self, raw_results: list, sep: str = ","):
        # Parse raw results
        self.sep = sep
        self.raw_results = raw_results
        self.raw_results_no_comments, self.comment_lines = self.split_comment_lines()
        self.first_line = self.raw_results_no_comments[0]
        self.timestamp, self.md5_hash = self.parse_first_line()
        self.result_sections = self.split_sections()

        # Parse demographics section
        self.demographics = self.parse_demographics()

        # Parse results sections
        self.result_keys = [key for key in self.result_sections if key not in {"consent", "demographics", "instructions", "practice-trial", "practice-end", "break"}]
        self.reading_time_results = self.parse_reading_time_results()

        # Combine demographics and results into single dataframe
        self.results = self.merge_demographics_and_results()

    def split_comment_lines(self) -> tuple[list, list]:
        """Split comment lines from raw results."""
        comment_lines = []
        result_lines = []
        for line in self.raw_results:
            if line.startswith(COMMENT_CH):
                comment_lines.append(line)
            else:
                result_lines.append(line)
        return result_lines, comment_lines

    def parse_first_line(self) -> tuple[str, str]:
        """Parse results receipt timestamp and participant's MD5 hash from the first line of results."""
        components = self.first_line.split(self.sep)
        # First column: Results reception time = timestamp
        timestamp = components[0]
        # MD5 hash of participants IP address
        md5_hash = components[1]
        return timestamp, md5_hash

    def split_sections(self, section_label_col_idx: int = 5) -> defaultdict:
        """Split sections of results by label."""
        # NB: default index is 5 because PCIBEX labels as 6th column starting from 1
        result_sections = defaultdict(lambda: [])
        for line in self.raw_results_no_comments:
            fields = line.split(self.sep)
            if len(fields) < section_label_col_idx:
                raise ValueError(f"Not enough fields found for label column at index {section_label_col_idx}")
            line_label = fields[section_label_col_idx]
            result_sections[line_label].append(line)
        return result_sections

    def parse_demographics(self) -> dict:
        """Parse responses to demographics section into a dictionary."""
        # Increment ParticipantResults class counter and assign participant ID based on this value
        ParticipantResults.counter += 1
        participant_id = ParticipantResults.counter

        # Parse demographic results lines
        demographics_lines = self.result_sections["demographics"]
        demographics = {"versuchspersonenID": f"{participant_id:03d}"}
        for line in demographics_lines:
            fields = line.split(self.sep)
            if fields[7] != "PennController":
                demographic_label = fields[8]   # label in column 9
                demographic_value = fields[10]  # value in column 11
                demographics[demographic_label] = demographic_value.strip() if demographic_value.strip() else pd.NA
        return demographics

    def parse_comprehension_question_responses(self) -> dict:
        """Parse selected responses to intermittent comprehension questions."""
        questionResponses = {}
        for result_key in self.result_keys:
            result_lines = self.result_sections[result_key]
            result_lines = [line.split(self.sep) for line in result_lines]
            # Filter lines related to comprehension question responses only
            result_lines = [line for line in result_lines if line[7] == "Selector"]
            for line in result_lines:
                selected_answer = line[10].lower()      # column 11
                question = line[23]                     # column 23
                itemNumber = line[13]                   # column 14
                anapherArt = line[17]                   # type of anapher (IA or DA, column 18)
                expectedAnswer = line[24].lower()       # column 25
                entry = {
                    "question": question,
                    "answer": selected_answer,
                    "erwarteteAntwort": expectedAnswer,
                    "correct": selected_answer == expectedAnswer,
                    "itemNummer": itemNumber,
                    "anapherArt": anapherArt,
                }
                questionId = itemNumber + anapherArt
                questionResponses[questionId] = entry
        return questionResponses

    def parse_reading_time_results(self) -> pd.DataFrame:
        parsed_results = []
        full_stimuli = defaultdict(lambda: {})
        stimulus_counter = 0
        last_item = None
        for result_key in self.result_keys:
            result_lines = self.result_sections[result_key]
            result_lines = [line.split(self.sep) for line in result_lines]
            # Filter out START/END tokens and comprehension questions
            result_lines = [line for line in result_lines if line[7] == "Controller-DashedSentence"]
            # NB: event time in column 12
            # Sort by event time (column 12), DashedSentence_pt1 or 2 (column 9), word number within dashed sentence (column 10)
            result_lines.sort(key = lambda x: (x[11], x[8], x[9]))

            # Extract relevant values from filtered and sorted results
            part1_index = 0
            for line in result_lines:
                sentence_part = line[8]     # DashedSentence_pt1 or DashedSentence_pt2 (column 9)
                chunkIdx = int(line[9])     # index of word/chunk within sentence
                itemNumber = line[13]       # column 14
                anapherArt = line[17]       # type of anapher (IA or DA, column 18)

                # If new itemNumber + anapher condition, increment the stimulus counter
                if itemNumber + anapherArt != last_item:
                    last_item = itemNumber + anapherArt
                    stimulus_counter += 1

                # Adjust the word/chunk index for words in pt2 as the indices start over
                if sentence_part.endswith("pt2"):
                    chunkIdx += part1_index
                    full_stimuli[itemNumber][2] = line[27].strip()
                else:
                    part1_index = chunkIdx
                    full_stimuli[itemNumber][1] = line[27].strip()

                # Compute position with respect to anapher of interest
                anapherIdx = int(line[22])          # column 23
                posWrtAnapher = (chunkIdx - 1) - anapherIdx

                # Compile dictionary of result values
                line_values = {
                    "stimulusIdx": stimulus_counter,# sequence of stimulus within experiment
                    "stimulusSatz": "",             # placeholder for full stimulus sentences
                    "wort": line[10],               # column 11
                    "chunkIdx": chunkIdx,           # adjusted index of sentence chunk
                    "posWrtAnapher": posWrtAnapher, # position (+/-) with respect to stimulus chunk containing anapher of interest
                    "leseZeit": line[25],           # column 26
                    "itemNummer": itemNumber,       # column 14
                    "block": line[14],              # column 15
                    "kontext": line[15],            # column 16
                    "bedingung": line[16],          # column 17
                    "anapherArt": line[17],         # column 18
                    "unterkategorie": line[18],     # column 19
                    "spezifikation": line[19],      # column 20
                    "anker": line[20],              # column 21
                    "anapher": line[21],            # column 22
                    "verstaendnisfrage": line[23] if line[23] else pd.NA,  # column 24
                    "erwarteteAntwort": line[24] if line[24] else pd.NA,   # column 25
                    "antwortRichtig": pd.NA,        # placeholder for evaluation of answer to comprehension question
                }
                parsed_results.append(line_values)

        # Parse responses to comprehension questions
        compQuestionResponses = self.parse_comprehension_question_responses()
        for result in parsed_results:
            itemNumber = result["itemNummer"]

            # Combine the full sentences and add to individual results
            fullStimulus = " ".join([full_stimuli[itemNumber][1], full_stimuli[itemNumber][2]])
            result["stimulusSatz"] = fullStimulus

            # Add evaluation of comprehension question responses
            anapherArt = result["anapherArt"]
            stimulusId = itemNumber + anapherArt
            if stimulusId in compQuestionResponses:
                result["antwortRichtig"] = compQuestionResponses[stimulusId]["correct"]

        parsed_results = pd.DataFrame(parsed_results)
        return parsed_results

    def merge_demographics_and_results(self) -> pd.DataFrame:
        """Merges demographics section into experimental reading time results as new static columns."""
        merged_results = self.reading_time_results.copy()
        for field, value in self.demographics.items():
            assert field not in self.reading_time_results.columns
            merged_results[field] = value
        return merged_results

def split_participant_results(result_lines: list) -> dict:
    """Split a list of lines of text by participant and initialize each as a ParticipantResults object."""
    participants_results = defaultdict(lambda: [])
    participant_id = 0
    for line in result_lines:
        if RESULTS_SPLIT_PATTERN.match(line):
            participant_id += 1
        participants_results[participant_id].append(line)
    if 0 in participants_results:
        del participants_results[0]

    participants_results = {
        pid: ParticipantResults(raw_results)
        for pid, raw_results in participants_results.items()
    }
    return participants_results


def merge_participant_results(participant_results: list[ParticipantResults]) -> pd.DataFrame:
    """Merge results dataframes from multiple participants into a single dataframe."""
    participant_result_dfs = [p.results for p in participant_results]
    merged_results = pd.concat(participant_result_dfs, ignore_index=True)
    return merged_results


def main(results_input_file: str, results_output_file: str):
    # Load results file as text
    with open(results_input_file, "r") as f:
        raw_results = f.readlines()

    # Split text file by participant results
    # Load each set of participant results into a ParticipantResults object
    results_per_participant = split_participant_results(raw_results)
    # Merge extracted and cleaned dataframes per participant back together 
    merged_results = merge_participant_results(results_per_participant.values())

    # Rewrite new cleaned results file
    merged_results.to_csv(results_output_file, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess results file from PCIBEX.")
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to the input file"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Path to the output file"
    )
    args = parser.parse_args()

    main(args.input, args.output)
