# Quiz Reporting Toolkit

A small pipeline to parse quiz XML, build a question bank, map questions to grades, and generate per-student reports.

*Note*: Each step produces or consumes a CSV/Markdown that the next step uses—run in sequence for end-to-end report generation.

## Files

1. **1_parse_quiz.py**  
   Parse the source XML into `question_bank.csv` (question-ID, response-ID, text, is_correct).

2. **5_build_bank.py**  
   Pivot `question_bank.csv` into `questions_wide.csv` (one row per question, columns A–D, `correct_label`).

3. **2_map_qa.py**  
   Contains `normalize()` and `best_match()` helpers for fuzzy-matching question texts.

4. **6_build_graded.py**  
   Read `grade_sample.csv` + `questions_wide.csv` → `grade_with_answers.csv` (flags → A/B/C/D).

5. **3_print_reports.py**  
   Generate per-student Markdown in `student_reports/`, highlighting correct (green) vs student (red) answers.

6. **4_htmlize.py**  
   Convert the Markdown reports to HTML (or PDF) via your favorite Markdown→HTML tool.

## Requirements

- Python 3.7+  
- `pandas`, `beautifulsoup4`, `difflib` (stdlib)  
- Optional for HTML conversion: `markdown`, `pdfkit`, etc.

```bash
pip install pandas beautifulsoup4
```

