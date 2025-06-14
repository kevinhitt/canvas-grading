#!/usr/bin/env python3
"""
generate_reports.py

Loads:
 - grade_sample.csv
 - question_bank.csv   (with question_id, response_id, text, is_correct)
 - question_mapping.csv (xml_group → matched_header)

Then builds per-student Markdown reports showing each incorrect question,
its lettered responses (A–D), coloring the correct one green and the
student’s selection red so your downstream Markdown→HTML converter picks it up.
"""

import pandas as pd
import os
import re

# ─── CONFIG ────────────────────────────────────────────────────────────────────
GRADE_CSV     = "grade_sample.csv"
QUESTION_CSV  = "question_bank.csv"
MAPPING_CSV   = "question_mapping.csv"
OUTPUT_DIR    = "student_reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FRONT_COLS   = ["name","id","sis_id","section","section_id","section_sis_id","submitted","attempt"]
SUMMARY_COLS = ["n correct","n incorrect","score"]

# ─── 1) Load grade CSV & detect question/flag columns ─────────────────────────
df_grade = pd.read_csv(GRADE_CSV, dtype=str)
middle   = [c for c in df_grade.columns if c not in FRONT_COLS + SUMMARY_COLS]
q_cols   = middle[0::2]
f_cols   = middle[1::2]

question_meta = []
for seq, (q_col, f_col) in enumerate(zip(q_cols, f_cols), start=1):
    if ":" not in q_col:
        raise ValueError(f"Question header {q_col!r} missing ':'")
    _, raw_txt = q_col.split(":", 1)
    qtext = raw_txt.strip()
    nums  = pd.to_numeric(df_grade[f_col], errors="coerce")
    if not set(nums.dropna().unique()).issubset({0,1}):
        raise ValueError(f"Flag column {f_col!r} has non-binary values")
    question_meta.append((seq, q_col, f_col, qtext))

# ─── 2) Load question_bank + mapping and build response_map ───────────────────
map_df = (
    pd.read_csv(MAPPING_CSV, dtype={"xml_group": int})
      .dropna(subset=["matched_header"])
)
qb = pd.read_csv(QUESTION_CSV, dtype=str)
qb["group"] = (qb.index // 5).astype(int)

# Build: grade-header → list of dict(text, is_correct)
response_map = {}
for _, m in map_df.iterrows():
    hdr = m["matched_header"]
    grp = int(m["xml_group"])
    block = qb[qb["group"] == grp]
    rows  = block.iloc[1:5] if len(block) >= 5 else block.iloc[1:]
    response_map[hdr] = [
        {"text": r["text"], "is_correct": r["is_correct"] == "1"}
        for _, r in rows.iterrows()
    ]

# ─── 3) Generate per-student Markdown ─────────────────────────────────────────
for _, student in df_grade.iterrows():
    sid   = student["id"]
    name  = student["name"]
    sect  = student["section"]
    score = student["score"]

    lines = [
        f"# {sid} – {name}",
        f"### {sect}",
        f"### Score: {score}%",
        "### Questions answered incorrectly:",
        ""
    ]

    for seq, q_col, f_col, qtext in question_meta:
        if float(student[f_col]) == 0:   # only for incorrect
            opts     = response_map.get(q_col, [])
            stud_ans = student[q_col].strip()

            lines.append(f"**Question {seq}:** {qtext}")
            for idx, resp in enumerate(opts):
                letter = chr(ord("A") + idx)
                text   = resp["text"]
                correct = resp["is_correct"]
                picked  = (text.strip() == stud_ans)

                display = f"{letter}. {text}"
                # color correct answers green
                if correct:
                    display = f'<span style="color:green;border: 1px solid green;border-radius: 10px;">{display}</span>'
                # color the student's (wrong) pick red
                if picked:
                    display = f'<span style="color:red">{display}</span>'

                lines.append(f"  {display}")
            lines.append("")

    if len(lines) == 4:
        lines.append("_No incorrect answers!_")

    safe = re.sub(r"[^\w\-]", "_", f"{sid}_{name}")
    with open(os.path.join(OUTPUT_DIR, safe + ".md"), "w", encoding="utf-8") as fo:
        fo.write("\n".join(lines))

print(f"✅ Generated colorized Markdown reports in ./{OUTPUT_DIR}/")