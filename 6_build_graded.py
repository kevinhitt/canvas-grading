#!/usr/bin/env python3
"""
pivot_grade_flags.py

Reads:
 - grade_sample.csv (with columns: question headers like '12345: Question text')
 - questions_wide.csv   (with columns question_text, A, B, C, D)

Produces grade_with_answers.csv where each flag column is replaced
by A/B/C/D based on matching the student's submitted answer text to the
A–D columns in questions_wide.csv, matching by question text (not IDs).
"""

import pandas as pd
import os
import re
from bs4 import BeautifulSoup
import html
from difflib import SequenceMatcher

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GRADE_CSV       = "grade_sample.csv"
QUESTIONS_WIDE  = "questions_wide.csv"
OUTPUT_CSV      = "grade_with_answers.csv"
FUZZY_THRESHOLD = 0.75  # fallback similarity threshold

OUTPUT_DIR = "."
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Columns to ignore when detecting question/flag columns
FRONT_COLS   = [
    "name", "id", "sis_id", "section", "section_id",
    "section_sis_id", "submitted", "attempt"
]
SUMMARY_COLS = ["n correct", "n incorrect", "score"]

# ─── HELPERS ───────────────────────────────────────────────────────────────────

def normalize_text(s):
    """
    Remove HTML tags, unescape entities, lowercase, strip punctuation and collapse whitespace.
    """
    if pd.isna(s) or not str(s).strip():
        return ""
    text = str(s)
    # strip HTML
    text = re.sub(r"<[^>]+>", " ", text)
    # parse HTML entities
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    text = html.unescape(text)
    # lowercase
    text = text.lower()
    # remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

# fuzzy match helper
def best_fuzzy_match(ans, options):
    best_letter, best_score = "", 0.0
    for letter, opt in options.items():
        score = SequenceMatcher(None, ans, normalize_text(opt)).ratio()
        if score > best_score:
            best_letter, best_score = letter, score
    return best_letter if best_score >= FUZZY_THRESHOLD else ""

# ─── 1) LOAD DATA ─────────────────────────────────────────────────────────────
df_grade = pd.read_csv(GRADE_CSV, dtype=str).fillna("")
qw       = pd.read_csv(QUESTIONS_WIDE, dtype=str).fillna("")

# Build a lookup: normalized_question_text -> { letter: raw option }
text_map = {}
for _, row in qw.iterrows():
    raw_qtext = row.get("question_text", "")
    norm_q   = normalize_text(raw_qtext)
    opts = {}
    for letter in ["A","B","C","D"]:
        val = row.get(letter, "")
        if pd.notna(val) and str(val).strip():
            opts[letter] = str(val).strip()
    if norm_q:
        text_map[norm_q] = opts

# ─── 2) DETECT QUESTION / FLAG PAIRS ───────────────────────────────────────────
cols_mid = [c for c in df_grade.columns if c not in FRONT_COLS + SUMMARY_COLS]
q_cols   = cols_mid[0::2]
f_cols   = cols_mid[1::2]

# ─── 3) REPLACE FLAGS WITH LETTERS ───────────────────────────────────────────
for q_col, f_col in zip(q_cols, f_cols):
    # extract only the question text portion after the colon
    parts = str(q_col).split(":", 1)
    qtext = parts[1] if len(parts) > 1 else parts[0]
    norm_q = normalize_text(qtext)
    options = text_map.get(norm_q)
    if not options:
        print(f"⚠️  No matching question text for header '{q_col}'")
        df_grade[f_col] = ""
        continue

    def map_to_letter(ans):
        norm_ans = normalize_text(ans)
        if not norm_ans:
            return ""
        # direct match
        for letter, opt in options.items():
            if normalize_text(opt) == norm_ans:
                return letter
        # fuzzy fallback
        return best_fuzzy_match(norm_ans, options)

    df_grade[f_col] = df_grade[q_col].apply(map_to_letter)

# ─── 4) WRITE OUTPUT ─────────────────────────────────────────────────────────
out_path = os.path.join(OUTPUT_DIR, OUTPUT_CSV)
df_grade.to_csv(out_path, index=False)
print(f"✅ Wrote {len(df_grade)} rows to {out_path}")