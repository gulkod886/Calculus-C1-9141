# Calculus-C1-9141
Everything related to the Calculus C1 9141 course.

## מאגר שאלות בחינה
- מבחנים מקוריים (PDF): `exams/`
- שאלות בפורמט TeX, קובץ לכל שאלה: `questions/`
- קטגוריות: `categories.json`
- תרגום לאנגלית של כל שאלה: `questions-en/` (אותו מבנה תיקיות)
- האתר: `site/index.html` (אפשר לפתוח ישירות בדפדפן); הגרסה האנגלית: `site/en/index.html`

אחרי כל שינוי בשאלות:
```
python3 scripts/build.py              # בניית האתר (עברית ואנגלית), tex/bank.tex ו-tex/bank-en.tex
python3 scripts/build.py --with-examples   # כולל שאלת הדוגמה
python3 scripts/build.py --zip   # גם dist/question-bank-he.zip ו-dist/question-bank-en.zip: אתר עצמאי לכל שפה, להעלאה למודל
```
אפשר לקמפל את `tex/bank.tex` ל-PDF עם XeLaTeX (`cd tex && xelatex bank.tex`).

פרטי הפורמט ותהליך העבודה מופיעים ב-`CLAUDE.md`.
