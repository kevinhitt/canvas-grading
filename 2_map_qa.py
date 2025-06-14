import pandas as pd
import csv
import re
import html
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

GRADE_CSV       = "grade_sample.csv"
QUESTION_CSV    = "question_bank.csv"
THRESHOLD       = 0.75    # minimum match ratio

def normalize(text):
    # 1) drop HTML if any
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    # 2) unescape entities
    text = html.unescape(text)
    # 3) lowercase, remove punctuation, collapse whitespace
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ─── 1) Extract question texts from grade_sample headers ────────────────────
df_grade = pd.read_csv(GRADE_CSV, dtype=str)
all_cols = list(df_grade.columns)
# assume questions are at indices 8, 10, 12… per your pattern
q_cols    = all_cols[8::2]
grade_qs  = {}
for header in q_cols:
    # split off the leading “85145:” if present
    if ":" in header:
        _, body = header.split(":", 1)
    else:
        body = header
    clean = normalize(body)
    grade_qs[header] = clean

# ─── 2) Load & group question_bank.csv ───────────────────────────────────────
records = []
with open(QUESTION_CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    records = list(reader)

# every 5 rows = one question
xml_questions = []
for i in range(0, len(records), 5):
    q_row = records[i]
    raw_text = q_row["text"]
    xml_questions.append((i//5, raw_text, normalize(raw_text)))

# ─── 3) Fuzzy-match each XML question to the best CSV header ────────────────
def best_match(query, candidates):
    best_hdr, best_score = None, 0
    for hdr, text in candidates.items():
        score = SequenceMatcher(None, query, text).ratio()
        if score > best_score:
            best_hdr, best_score = hdr, score
    return best_hdr, best_score

mapping = []
for qid, raw, norm in xml_questions:
    hdr, score = best_match(norm, grade_qs)
    if score >= THRESHOLD:
        mapping.append({
            "xml_group": qid,
            "matched_header": hdr,
            "score": round(score, 3),
            "xml_snippet": raw[:60] + "…"
        })
    else:
        mapping.append({
            "xml_group": qid,
            "matched_header": None,
            "score": round(score, 3),
            "xml_snippet": raw[:60] + "…"
        })

# ─── 4) Review / Export your mapping ────────────────────────────────────────
mapping_df = pd.DataFrame(mapping)
mapping_df.to_csv("question_mapping.csv", index=False)
print(mapping_df)