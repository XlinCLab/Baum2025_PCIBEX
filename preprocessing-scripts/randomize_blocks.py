import pandas as pd
import random
import os

# Load data
df = pd.read_csv(os.path.join("..", "pcibex-resources", "stimuli.csv"))

# Group by itemNummer and shuffle
items = list(df.groupby("itemNummer"))
random.shuffle(items)

# Block parameters
max_block_size = 12
n_blocks = (len(df) + max_block_size - 1) // max_block_size

# Initialize empty blocks
blocks = [[] for _ in range(n_blocks)]

# Distribute items across blocks
for item_num, item_trials in items:
    item_trials = item_trials.sample(frac=1)  # shuffle IA / DA

    first_trial = item_trials.iloc[0]
    second_trial = item_trials.iloc[1]

    # Find blocks with the fewest items (but not yet max size)
    candidate_blocks = [b for b in blocks if len(b) < max_block_size]
    min_length = min([len(b) for b in blocks])
    candidate_blocks = [idx for idx, b in enumerate(blocks) if len(b) == min_length]

    # If more than one block is possible, then further narrow the options down to a block that contains the fewest of the Bedingung label
    if len(candidate_blocks) > 1:
        first_bedingung = first_trial.bedingung
        candidate_blocks_bedingung_counts = {
            idx: pd.DataFrame(blocks[idx])['bedingung'].value_counts().get(first_bedingung, 0)
            if len(blocks[idx]) > 0 else 0
            for idx in candidate_blocks
        }
        min_bedingung_count = min(candidate_blocks_bedingung_counts[idx] for idx in candidate_blocks)
        candidate_blocks = [idx for idx in candidate_blocks if candidate_blocks_bedingung_counts[idx] == min_bedingung_count]

    # Pick one randomly among the smallest
    # Add the first trial to that block
    chosen_block_first = random.choice(candidate_blocks)
    blocks[chosen_block_first].append(first_trial)

    # Then generate candidates again, pick another block, and add the second trial there
    # Ensure the same item number does not end up in the same block
    candidate_blocks = [idx for idx, b in enumerate(blocks) if len(b) < max_block_size and abs(idx - chosen_block_first) >= 2]
    min_length = min([len(blocks[idx]) for idx in candidate_blocks])
    candidate_blocks = [idx for idx, b in enumerate(blocks) if idx in candidate_blocks and len(b) == min_length]

    # If more than one block is possible, then further narrow the options down to a block that contains the fewest of the Bedingung label
    if len(candidate_blocks) > 1:
        second_bedingung = second_trial.bedingung
        candidate_blocks_bedingung_counts = {
            idx: pd.DataFrame(blocks[idx])['bedingung'].value_counts().get(second_bedingung, 0)
            if len(blocks[idx]) > 0 else 0
            for idx in candidate_blocks
        }
        min_bedingung_count = min(candidate_blocks_bedingung_counts[idx] for idx in candidate_blocks)
        candidate_blocks = [idx for idx in candidate_blocks if candidate_blocks_bedingung_counts[idx] == min_bedingung_count]

    chosen_block_second = random.choice(candidate_blocks)
    blocks[chosen_block_second].append(second_trial)

# Convert blocks to DataFrames
blocks = [
    pd.DataFrame(block).assign(block=i + 1)
    for i, block in enumerate(blocks)
]

# Validate constraints
for i, block in enumerate(blocks):
    assert block["itemNummer"].nunique() == len(block), f"Item repeated in block {i}"
    assert {"IA", "DA"}.issubset(set(block["anapherArt"])), f"Missing IA or DA in block {i}"
    #assert {"V", "I", "S", "M"}.issubset(set(block["anapherArt"])), f"Missing Bedingung in block {i}"

# Concatenate blocks into final trial order
final_df = pd.concat(blocks, ignore_index=True)

# Add column with block and condition
final_df["block_bedingung"] = final_df["block"].astype(str) + final_df["bedingung"]
summary = final_df.groupby('block')['bedingung'].value_counts().unstack(fill_value=0)
print(summary)

# Save output files
final_df.to_csv(os.path.join("..", "pcibex-resources", "blocked_trials.csv"), index=False)
final_df.to_excel(os.path.join("..", "pcibex-resources", "blocked_trials.xlsx"), index=False)
