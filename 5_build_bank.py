#!/usr/bin/env python3
"""
pivot_question_bank.py

Reads question_bank.csv (columns: question_id, response_id, text, is_correct),
strips HTML from question_text, and emits questions_wide.csv with one row per question:

  question_id, question_text, A, B, C, D, correct_label
"""

import pandas as pd
from bs4 import BeautifulSoup

# 1) Load & sanitize
qb = pd.read_csv("question_bank.csv", dtype=str)
qb["response_id"] = qb["response_id"].fillna("").astype(str)
qb["is_correct"]  = qb["is_correct"].fillna("").astype(str)

records = []

# 2) Group by question_id
for qid, grp in qb.groupby("question_id", sort=False):
    # extract & clean question_text (response_id == "")
    q_rows = grp[grp["response_id"] == ""]
    if q_rows.empty:
        print(f"⚠️  Skipping {qid!r}: no question-text row.")
        continue
    question_text = q_rows.iloc[0]["text"]
    # strip HTML
    question_text = BeautifulSoup(question_text, "html.parser").get_text().strip()

    # grab response rows
    resp = grp[grp["response_id"] != ""].reset_index(drop=True)
    if resp.empty:
        print(f"⚠️  No responses for {qid!r}; skipping.")
        continue
    if len(resp) != 4:
        print(f"⚠️  Question {qid!r} has {len(resp)} responses (expected 4).")

    options = resp["text"].astype(str).str.strip().tolist()
    correct_indices = [i for i, v in enumerate(resp["is_correct"]) if v == "1"]
    correct_label = chr(ord("A") + correct_indices[0]) if correct_indices else ""

    row = {
        "question_id":   qid,
        "question_text": question_text,
        "correct_label": correct_label
    }
    for idx, letter in enumerate(["A", "B", "C", "D"]):
        row[letter] = options[idx] if idx < len(options) else ""
    records.append(row)

# 3) Write out
out = pd.DataFrame(records)
out.to_csv("questions_wide.csv", index=False)
print(f"✅ questions_wide.csv written with {len(out)} questions.")