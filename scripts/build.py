#!/usr/bin/env python3
"""Build the question bank.

Reads every questions/**/*.tex file (folders whose name starts with "_" are
skipped unless --with-examples is given), parses the metadata header and the
question / hint / solution environments, converts the text-mode LaTeX to HTML
(math is left as-is for MathJax), and writes:

  site/data/questions.js   - data for the website (window.BANK = {...})
  tex/bank.tex             - a single document with every question, for XeLaTeX

Uses the Python standard library only.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "questions"
CATEGORIES_FILE = ROOT / "categories.json"
OUT_JS = ROOT / "site" / "data" / "questions.js"
OUT_TEX = ROOT / "tex" / "bank.tex"

REQUIRED_META = ("year", "number", "categories")
EXAM_TYPES = ("מבחן", "בוחן")
GEMATRIA = dict(zip("אבגדהוזחטיכלמנסעפצקרשת",
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400]))
MATH_ENVS = ("equation", "equation*", "align", "align*", "gather", "gather*",
             "multline", "multline*", "cases", "array", "pmatrix", "bmatrix")


class BuildError(Exception):
    pass


# ---------------------------------------------------------------- parsing

def parse_meta(text, path):
    meta = {}
    for line in text.splitlines():
        m = re.match(r"^\s*%\s*([a-z_]+)\s*:\s*(.*?)\s*$", line)
        if m:
            meta[m.group(1)] = m.group(2)
    missing = [k for k in REQUIRED_META if not meta.get(k)]
    if missing:
        raise BuildError(f"{path}: missing metadata: {', '.join(missing)}")
    meta.setdefault("type", "מבחן")
    if meta["type"] not in EXAM_TYPES:
        raise BuildError(f"{path}: type must be one of {', '.join(EXAM_TYPES)}")
    if meta["type"] == "מבחן" and not meta.get("moed"):
        raise BuildError(f"{path}: missing metadata: moed")
    meta["year"] = normalize_year(meta["year"])
    meta["categories"] = [c.strip() for c in meta["categories"].split(",") if c.strip()]
    return meta


def normalize_year(y):
    """Hebrew year: unify the quote marks, e.g. 'תשפ"ה'."""
    letters = re.sub(r"[^א-ת]", "", y)
    if not letters:
        return y
    return letters if len(letters) == 1 else letters[:-1] + '"' + letters[-1]


def year_value(y):
    letters = re.sub(r"[^א-ת]", "", y)
    if letters:
        return 5000 + sum(GEMATRIA.get(c, 0) for c in letters.replace("ך", "כ").replace("ם", "מ")
                          .replace("ן", "נ").replace("ף", "פ").replace("ץ", "צ"))
    m = re.match(r"\d+", y)
    return int(m.group(0)) if m else 0


def env_bodies(text, name):
    pattern = re.compile(r"\\begin\{" + name + r"\}(.*?)\\end\{" + name + r"\}", re.S)
    return [m.group(1).strip() for m in pattern.finditer(text)]


def strip_comments(text):
    # Remove unescaped % to end of line.
    return re.sub(r"(?<!\\)%.*", "", text)


# ---------------------------------------------------------------- LaTeX -> HTML

def latex_to_html(src):
    """Convert text-mode LaTeX to HTML, leaving math for MathJax."""
    src = strip_comments(src)

    # 1. Pull math out so text-mode rules do not touch it.
    stash = []

    def keep(m):
        stash.append(m.group(0))
        return f"\x00{len(stash) - 1}\x00"

    env_alt = "|".join(re.escape(e) for e in MATH_ENVS)
    math_re = re.compile(
        r"\\begin\{(" + env_alt + r")\}.*?\\end\{\1\}"
        r"|\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|(?<!\\)\$.+?(?<!\\)\$",
        re.S,
    )
    src = math_re.sub(keep, src)

    s = html.escape(src, quote=False)

    # 2. Inline formatting (repeat to handle nesting).
    for _ in range(3):
        s = re.sub(r"\\textbf\{([^{}]*)\}", r"<strong>\1</strong>", s)
        s = re.sub(r"\\(?:emph|textit)\{([^{}]*)\}", r"<em>\1</em>", s)
        s = re.sub(r"\\underline\{([^{}]*)\}", r"<u>\1</u>", s)
        s = re.sub(r"\\texttt\{([^{}]*)\}", r"<code>\1</code>", s)
        s = re.sub(r"\\(?:textenglish|en)\{([^{}]*)\}", r'<span dir="ltr">\1</span>', s)

    # 3. Lists.
    s = re.sub(r"\\begin\{enumerate\}(\[[^\]]*\])?", lambda m: '<ol class="parts">', s)
    s = s.replace(r"\end{enumerate}", "</li></ol>")
    s = s.replace(r"\begin{itemize}", "<ul>").replace(r"\end{itemize}", "</li></ul>")
    s = re.sub(r"\\item\[([^\]]*)\]\s*", r'</li><li class="custom" data-label="\1">', s)
    s = re.sub(r"\\item\s*", "</li><li>", s)
    s = re.sub(r"(<ol class=\"parts\">|<ul>)\s*</li>", r"\1", s)

    # 4. Misc text-mode commands.
    s = re.sub(r"\\(?:medskip|bigskip|smallskip|noindent|par)\b", "\n\n", s)
    s = s.replace("\\\\", "<br>")
    s = s.replace("~", "&nbsp;")
    for cmd, rep in (("qquad", "&emsp;&emsp;"), ("quad", "&emsp;"), ("ldots", "…"),
                     ("dots", "…"), ("checkmark", "✓")):
        s = re.sub(r"\\" + cmd + r"\b\s?", rep, s)
    s = s.replace("``", "“").replace("''", "”")
    s = re.sub(r"\\([%&#_{}$])", r"\1", s)

    # 5. Paragraphs.
    # Text at top level becomes <p>s; text inside a list item stays bare
    # unless it has several paragraphs.
    out, depth = [], 0
    for tok in re.split(r"(</?(?:ol|ul|li)\b[^>]*>)", s):
        if tok.startswith("<"):
            depth += 1 if tok.startswith("<li") else -1 if tok == "</li>" else 0
            out.append(tok)
            continue
        paras = [p.strip() for p in re.split(r"\n\s*\n", tok) if p.strip()]
        if depth and len(paras) == 1:
            out.append(paras[0])
        else:
            out.extend(f"<p>{p}</p>" for p in paras)
    s = "\n".join(out)

    # 6. Restore math (escape for HTML; MathJax reads the decoded text).
    s = re.sub(r"\x00(\d+)\x00", lambda m: html.escape(stash[int(m.group(1))], quote=False), s)
    return s


# ---------------------------------------------------------------- build

def load_question(path, known_categories):
    raw = path.read_text(encoding="utf-8")
    meta = parse_meta(raw, path)
    unknown = [c for c in meta["categories"] if c not in known_categories]
    if unknown:
        raise BuildError(f"{path}: unknown categories: {', '.join(unknown)} (see categories.json)")

    questions = env_bodies(raw, "question")
    solutions = env_bodies(raw, "solution")
    if len(questions) != 1:
        raise BuildError(f"{path}: expected exactly one question environment, found {len(questions)}")
    if len(solutions) != 1:
        raise BuildError(f"{path}: expected exactly one solution environment, found {len(solutions)}")
    hints = env_bodies(raw, "hint")

    rel = path.relative_to(ROOT).as_posix()
    return {
        "id": path.relative_to(QUESTIONS_DIR).with_suffix("").as_posix(),
        "file": rel,
        "year": meta["year"],
        "yearValue": year_value(meta["year"]),
        "type": meta["type"],
        "semester": meta.get("semester", ""),
        "moed": meta.get("moed", ""),
        "note": meta.get("note", ""),
        "officialSolution": meta.get("official_solution", "").lower() in ("yes", "כן", "true"),
        "part": meta.get("part", ""),
        "number": meta["number"],
        "points": meta.get("points", ""),
        "source": meta.get("source", ""),
        "categories": meta["categories"],
        "question": latex_to_html(questions[0]),
        "hints": [latex_to_html(h) for h in hints],
        "solution": latex_to_html(solutions[0]),
        "_tex": {"question": questions[0], "hints": hints, "solution": solutions[0]},
    }


def sort_key(q):
    def num(x):
        m = re.match(r"\d+", str(x))
        return int(m.group(0)) if m else 0
    moed_order = {"א": 1, "ב": 2, "ג": 3, "מיוחד": 4, "לדוגמה": 0}
    return (q["yearValue"], q["semester"] or "א", EXAM_TYPES.index(q["type"]) * -1,
            moed_order.get(q["moed"], 9), q["note"], q["part"], num(q["number"]), q["number"])


def exam_label(q):
    parts = [q["year"]]
    if q["semester"]:
        parts.append(f"סמסטר {q['semester']}")
    if q["type"] == "בוחן":
        parts.append("בוחן" + (f" {q['moed']}" if q["moed"] else ""))
    elif q["moed"] == "לדוגמה":
        parts.append("מבחן לדוגמה")
    else:
        parts.append(f"מועד {q['moed']}")
    if q["note"]:
        parts.append(f"({q['note']})")
    return " ".join(parts)


def write_tex(questions):
    parts = [
        "% Generated by scripts/build.py - do not edit.",
        r"\documentclass[11pt]{article}",
        r"\input{preamble}",
        r"\begin{document}",
        r"\title{מאגר שאלות בחינה}\date{}\maketitle",
    ]
    current = None
    for q in questions:
        exam = exam_label(q)
        if exam != current:
            current = exam
            parts.append(rf"\section*{{{exam}}}")
        part = f"חלק {q['part']}', " if q["part"] else ""
        parts.append(rf"\subsection*{{{part}שאלה {q['number']}}}")
        parts.append(r"\begin{question}" + "\n" + q["_tex"]["question"] + "\n" + r"\end{question}")
        for h in q["_tex"]["hints"]:
            parts.append(r"\begin{hint}" + "\n" + h + "\n" + r"\end{hint}")
        parts.append(r"\begin{solution}" + "\n" + q["_tex"]["solution"] + "\n" + r"\end{solution}")
    parts.append(r"\end{document}")
    OUT_TEX.write_text("\n\n".join(parts) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--with-examples", action="store_true", help="include folders starting with '_'")
    args = ap.parse_args()

    categories = json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
    known = {c["id"] for c in categories}

    files = sorted(QUESTIONS_DIR.rglob("*.tex"))
    if not args.with_examples:
        files = [f for f in files
                 if not any(p.startswith("_") for p in f.relative_to(QUESTIONS_DIR).parts)]

    errors, questions = [], []
    for f in files:
        try:
            questions.append(load_question(f, known))
        except BuildError as e:
            errors.append(str(e))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)

    questions.sort(key=sort_key)
    for q in questions:
        q["exam"] = exam_label(q)
    write_tex(questions)

    for q in questions:
        del q["_tex"]
    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"categories": categories, "questions": questions},
                         ensure_ascii=False, indent=1)
    OUT_JS.write_text("// Generated by scripts/build.py - do not edit.\nwindow.BANK = " + payload + ";\n",
                      encoding="utf-8")
    exams = {exam_label(q) for q in questions}
    print(f"Built {len(questions)} questions from {len(exams)} exams -> "
          f"{OUT_JS.relative_to(ROOT)}, {OUT_TEX.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
