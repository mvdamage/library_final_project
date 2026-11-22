from datetime import datetime

from html import escape

from pathlib import Path

def build_txt_report(books, by_genre, by_author):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    lines = [
        "Отчёт: домашняя библиотека",
        f"Дата: {now}",
        f"Всего книг: {len(books)}",
        "",
        "— Книги —",
    ]
    for b in books:
        # (id, title, volume, author, year, genre)
        vol = f", том {b[2]}" if b[2] not in (None, "") else ""
        lines.append(f"{b[3]} — «{b[1]}»{vol} ({b[4]}, {b[5]})")
    lines += ["", "— По жанрам —"]
    for genre, cnt in by_genre:
        lines.append(f"{genre}: {cnt}")
    lines += ["", "— По авторам —"]
    for author, cnt in by_author:
        lines.append(f"{author}: {cnt}")
    return "\n".join(lines) + "\n"

def build_html_report(books, by_genre, by_author):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    rows = ""
    for b in books:
        vol = escape(str(b[2])) if b[2] not in (None, "") else "—"
        rows += (
            f"<tr><td>{escape(b[1])}</td><td>{vol}</td>"
            f"<td>{escape(b[3])}</td><td>{b[4]}</td>"
            f"<td>{escape(b[5])}</td></tr>"
        )
    return f"""<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="utf-8">
<title>Библиотека</title>
<style>
body {{ font-family: Segoe UI, sans-serif; margin: 24px; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
th {{ background: #9fa1a3; color: #fff; }}
</style>
</head><body>
<h1>Домашняя библиотека</h1>
<p>Сформирован: {now}. Всего: {len(books)}</p>
<h2>Книги</h2>
<table><tr><th>Название</th><th>Том</th><th>Автор</th><th>Год</th><th>Жанр</th></tr>
{rows or "<tr><td colspan='5'>Нет книг</td></tr>"}
</table>
</body></html>"""

def save_report(path, content):
    Path(path).write_text(content, encoding="utf-8")