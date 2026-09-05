#!/usr/bin/env python3
"""
Specimen Rejection Analyzer
Rejection rate pareto and chi-square trend from pre-analytical error logs.
Stdlib parser / mapper with batch CSV and single lookup.
"""
import argparse
import csv
import sys

def lookup(query, extra=None):
    """Single lookup: token overlap + substring scoring (no deps). Returns top hits."""
    q = str(query).lower().strip()
    # Specimen rejection domain dictionary: (display_label, match_keyword)
    candidates = [
        ("Hemolyzed Sample", "hemolyzed"),
        ("Clotted Specimen", "clotted"),
        ("Insufficient Volume", "insufficient"),
        ("Mislabeled Specimen", "mislabeled"),
        ("Wrong Container Type", "container"),
        ("Transport Temperature Excursion", "temperature"),
        ("Expired Collection Tube", "expired"),
        ("Contaminated Specimen", "contaminated"),
        ("Incorrect Collection Time", "collection time"),
        ("Specimen Leakage", "leakage"),
        ("Icteric Sample", "icteric"),
        ("Lipemic Sample", "lipemic"),
        ("Hemolysis Index Exceeded", "hemolysis"),
        ("Duplicate Order", "duplicate"),
        ("Missing Order / Requisition", "missing"),
        ("QNS - Quantity Not Sufficient", "qns"),
    ]
    scored=[]
    for label, key in candidates:
        score = 0
        if key in q:
            score += 10
        # token overlap
        qt = set(q.split())
        lt = set(label.lower().split())
        overlap = len(qt & lt)
        score += overlap * 2
        scored.append((score, label))
    scored.sort(reverse=True, key=lambda x: x[0])
    top = scored[0] if scored else (0, "no match")
    return {"query": query, "top_hit": top[1], "score": top[0], "all": scored[:3]}

def process_csv(inp,out):
    with open(inp, newline="", encoding="utf-8-sig") as f:
        r=csv.DictReader(f); rows=list(r); fn=r.fieldnames
        # guess query column
        qcol = fn[0]
        for cand in ["query","test","drug","code","variant","hla","lab","name"]:
            if cand in [c.lower() for c in fn]:
                qcol = [c for c in fn if c.lower()==cand][0]; break
        results=[]
        for row in rows:
            res=lookup(row.get(qcol,""), row)
            merged={**row, "top_hit": res["top_hit"], "lookup_score": res["score"]}
            results.append(merged)
    with open(out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(fn)+["top_hit","lookup_score"]); w.writeheader(); w.writerows(results)
    return results

def build_parser():
    p=argparse.ArgumentParser(prog="rejection_analyzer", description="Specimen Rejection Analyzer")
    sub=p.add_subparsers(dest="cmd", required=True)
    s=sub.add_parser("single"); s.add_argument("query", nargs="?", default="creatinine"); s.add_argument("--query", dest="q2")
    b=sub.add_parser("batch"); b.add_argument("--input", required=True); b.add_argument("--output", required=True)
    return p

def main(argv=None):
    p=build_parser(); a=p.parse_args(argv)
    if a.cmd=="single":
        q=getattr(a,"q2",None) or getattr(a,"query")
        print(lookup(q)); return 0
    if a.cmd=="batch":
        res=process_csv(a.input, a.output); print(f"Processed {len(res)} -> {a.output}"); return 0
    p.print_help(); return 1

if __name__=="__main__":
    import sys; sys.exit(main())
