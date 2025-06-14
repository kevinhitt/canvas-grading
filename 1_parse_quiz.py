#!/usr/bin/env python3
"""
1_parse_quiz.py

Parse an IMS-style assessment XML and dump each question plus its
responses (and flag which is correct) to question_bank.csv.

Output columns:
 - question_id   : the <item> ident attribute
 - response_id   : the <response_label> ident (blank for the question row)
 - text          : the question text (first row) or the response text
 - is_correct    : “1” if this response is the correct one, “0” otherwise (blank for question row)
"""

import xml.etree.ElementTree as ET
import csv
import argparse
import sys

def extract_questions(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    records = []

    for item in root.findall(".//{*}item"):
        # get the question's ident
        qid = item.get("ident", "").strip()

        # find the correct response ident in the conditionvar
        correct_id = None
        vareq = item.find(".//{*}conditionvar//{*}varequal")
        if vareq is not None and vareq.text:
            correct_id = vareq.text.strip()

        # gather mattext under response_label and under itemmetadata so we can skip them
        bad_mattext = set(item.findall(".//{*}itemmetadata//{*}mattext"))
        for rl in item.findall(".//{*}response_label"):
            bad_mattext.update(rl.findall(".//{*}mattext"))

        # extract the question text = first mattext not in bad_mattext
        question_text = ""
        for mat in item.findall(".//{*}mattext"):
            if mat not in bad_mattext:
                question_text = "".join(mat.itertext()).strip()
                if question_text:
                    break

        # append the question row
        records.append({
            "question_id": qid,
            "response_id": "",
            "text": question_text,
            "is_correct": ""
        })

        # now append each response under its response_label
        for rl in item.findall(".//{*}response_label"):
            rid = rl.get("ident", "").strip()
            mat = rl.find(".//{*}mattext")
            resp_text = "".join(mat.itertext()).strip() if mat is not None else ""
            is_corr = "1" if rid == correct_id else "0"
            records.append({
                "question_id": qid,
                "response_id": rid,
                "text": resp_text,
                "is_correct": is_corr
            })

    return records

def write_csv(records, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f,
            fieldnames=["question_id", "response_id", "text", "is_correct"])
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)

def main():
    p = argparse.ArgumentParser(
        description="Extract questions & responses (with correct flags) from XML")
    p.add_argument("xml_file", help="path to source XML")
    p.add_argument(
        "-o", "--csv", default="question_bank.csv",
        help="output CSV filename (default: question_bank.csv)")
    args = p.parse_args()

    try:
        records = extract_questions(args.xml_file)
    except ET.ParseError as e:
        sys.exit(f"XML parse error: {e}")

    if not records:
        print("⚠️  No questions/responses extracted. Check your XML structure.")
    else:
        write_csv(records, args.csv)
        print(f"✅ Wrote {len(records)} rows to {args.csv}")

if __name__ == "__main__":
    main()
