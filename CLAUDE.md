# Exam question bank for Calculus C1 (9141)

## Layout
- `exams/` — original files as uploaded: `exams/מבחנים/<year>/...` (final exams) and `exams/בחנים/...` (midterm quizzes). Some include solutions, some are handwritten solution scans.
- `questions/<numeric year>/<slug>/q<N>.tex` — one file per question. Numeric year: תשפ"ה = 5785. Slug: `semA-moedA`, `semA-moedB`, `semA-moedC`, `semA-special` (מועד מיוחד), `semA-sample` (מבחן לדוגמה), `semB-moedA`, `quiz` (בוחן), `quiz-sample`; add `-<name>` for a lecturer-specific version (e.g. `semA-moedA-hodisman`). Folders starting with `_` are examples and are not built.
- `questions-en/<same path>.tex` — English translation of each question: only the `question`/`hint`/`solution` environments (metadata comes from the Hebrew file; `% note:` must be given in English if the Hebrew file has a note). Same number of hints, math identical to the Hebrew file, no Hebrew characters outside comments.
- `categories.json` — category list (id + Hebrew `name` + English `name_en`). Add a category here before using it.
- `scripts/build.py` — builds `site/data/questions.js` + `tex/bank.tex` (Hebrew) and `site/en/data/questions.js` + `tex/bank-en.tex` (English). Run after every change; it fails on missing metadata, an unknown category, or a malformed English file.
- `site/` — static site (RTL, MathJax). Opens directly as `site/index.html`, no server needed. `site/en/index.html` is the English version (LTR); it shares `site/app.js` and `site/style.css` (UI strings in `app.js` are chosen by `<html lang>`).

## Question file format
```tex
% year: תשפ"ה
% type: מבחן            (מבחן | בוחן; default מבחן)
% semester: א           (א | ב)
% moed: ב               (א | ב | ג | מיוחד | לדוגמה; optional for a בוחן)
% note: קבוצת חודיסמן    (optional, distinguishes parallel versions)
% part: ב               (optional: only if the exam is split into parts חלק א/ב with their own numbering)
% number: 3             (question number as in the exam)
                         (number restarts within each part: part ב, number 1 — do NOT renumber or add a prefix to the question text)
% points: 20            (optional)
% categories: sequences, monotone-seq
% official_solution: yes (only if the solution is based on a solution attached to the exam — official or handwritten)
% source: exams/מבחנים/תשפה/מועד ב תשפה.pdf

\begin{question} ... \end{question}
\begin{hint} ... \end{hint}        (zero or more, shown one at a time, easiest first)
\begin{solution} ... \end{solution}  (exactly one)
```
Supported text-mode LaTeX: `$..$`, `\[..\]`, `align*` and similar, `enumerate`/`itemize` (`\item[label]`), `\textbf`, `\emph`, `\underline`, `\\`. Avoid other packages/macros (no tikz, no `\usepackage`); the site renders math with MathJax, so stay within amsmath/amssymb. Macros `\R \N \Q \Z \eps` are defined. For sub-parts use `\begin{enumerate}` — the site numbers them א, ב, ג automatically. Figures cannot be shown; describe them in words.

## Processing a new exam PDF
1. Read the whole PDF. Identify every question. Sub-parts (א, ב, ג) stay in one file with `enumerate` **only if they are directly connected** (a later part uses an earlier result, or step-by-step investigation of the same function). Independent sub-parts are split: `q4a.tex`, `q4b.tex` with `% number: 4א` / `4ב`, each with its own points, categories, hints and self-contained solution; the shared stem is copied into each part (plural → singular, "בשאלה זו אין קשר בין הסעיפים" dropped). Points are written `(10 נק')` at the start of the question.
2. Transcribe the question text into TeX **exactly** (wording, notation, numbers). Do not "fix" the question. Exception: function names are always TeX operators (`\sin`, `\cos`, `\ln`, `\arctan`, …), never bare letters `sin(x)`, even if the source looks like that. If something can't be read, write `\textbf{[לא קריא]}` and flag it to the user.
3. Choose 1–3 categories from `categories.json` (several when the question really combines topics). Format tags come on top of those: `multiple-choice` (שאלה אמריקאית — the student picks one of several given answers) and `true-false` (נכון / לא נכון).
4. Write a full, detailed solution in Hebrew at the level of the course: every step justified, theorems named, the final answer stated clearly. If the exam has an official solution, use it but expand it.
5. Add 1–3 hints for questions where a hint helps (the key idea, not the solution). Short computational questions can go without hints.
6. Check the math (substitute numbers, verify limits/derivatives numerically with python when possible).
7. Write the English translation in `questions-en/` (same relative path). Sub-part references become "part (a)", `\item[(א)]` → `\item[(a)]`, `(10 נק')` → `(10 pts)`, Hebrew year → `2024/25`.
8. Run `python3 scripts/build.py` and fix any errors. Its last line reports how many questions have an English translation; keep it at 100%.

## Known source quirks (decided once, keep consistent)
- The header wins over the filename. Files named "מועד ג" whose header says "מועד מיוחד" → `moed: מיוחד` / `semA-special`; files named "מועד מיוחד" whose header says "מועד ג" → `moed: ג` / `semA-moedC`.
- `exams/מבחנים/תשעט/חודיסמן ...` are actually תשע"ט semester B exams (Dr. Krapivnik).
- `exams/מבחנים/תשעח/... סמסטר ב` headers say תשע"ז but are dated 2018 → filed as תשע"ח semester B.
- `exams/מבחנים/תשפא/מועד ב תשפא.docx` is a different course (ODE 9341) — not included.
- `exams/מבחנים/תשפו/` scanner files: AnyScanner = מועד א תשפ"ו, sol B = מועד ב תשפ"ו (handwritten solution), TapScanner = solution of בוחן תשפ"ו, CamScanner = solution of sample בוחן תשפ"ה.
- Typos in the exams are kept verbatim in the question and pointed out in the solution.

## QA
After a batch of changes, render every question/hint/solution in a headless browser (both `site/index.html` and `site/en/index.html`) and look for `mjx-merror` elements and raw `\command` text outside math. Also check that `cases`/`align` blocks still have their `\\` row separators (shell heredocs can collapse them).
