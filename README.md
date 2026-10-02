# Calculus-C1-9141
Everything related to the Calculus C1 9141 course.

## מאגר שאלות בחינה
- מבחנים מקוריים (PDF): `exams/`
- שאלות בפורמט TeX, קובץ לכל שאלה: `questions/`
- קטגוריות: `categories.json`
- האתר: `site/index.html` (אפשר לפתוח ישירות בדפדפן)

אחרי כל שינוי בשאלות:
```
python3 scripts/build.py              # בניית האתר ו-tex/bank.tex
python3 scripts/build.py --with-examples   # כולל שאלת הדוגמה
```
אפשר לקמפל את `tex/bank.tex` ל-PDF עם XeLaTeX (`cd tex && xelatex bank.tex`).

פרטי הפורמט ותהליך העבודה מופיעים ב-`CLAUDE.md`.
