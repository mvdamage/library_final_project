"""Автотесты модуля отчетов (reports.py)."""

import re
from pathlib import Path

import pytest

from reports import build_html_report, build_txt_report, save_report

BOOK = (1, "Мастер и Маргарита", None, "Булгаков", 1967, "роман")
BOOK_WITH_VOL = (2, "Война и мир", "3", "Толстой", 1869, "роман")

@pytest.fixture
def sample_stats():
    by_genre = [("роман", 2), ("антиутопия", 1)]
    by_author = [("Толстой", 1), ("Булгаков", 1), ("Оруэлл", 1)]
    return by_genre, by_author

# --- TXT ---

def test_txt_report_header_and_count(sample_stats) -> None:
    by_genre, by_author = sample_stats
    txt = build_txt_report([BOOK], by_genre, by_author)

    assert "Отчет: домашняя библиотека" in txt
    assert re.search(r"Дата: \d{2}\.\d{2}\.\d{4} \d{2}:\d{2}", txt)
    assert "Всего книг: 1" in txt
    assert txt.endswith("\n")

def test_txt_report_lists_book_with_and_without_volume(sample_stats) -> None:
    by_genre, by_author = sample_stats
    txt = build_txt_report([BOOK, BOOK_WITH_VOL], by_genre, by_author)

    assert "Булгаков — «Мастер и Маргарита» (1967, роман)" in txt
    assert "Толстой — «Война и мир», том 3 (1869, роман)" in txt

def test_txt_report_stats_sections(sample_stats) -> None:
    by_genre, by_author = sample_stats
    txt = build_txt_report([BOOK], by_genre, by_author)

    assert "— По жанрам —" in txt
    assert "роман: 2" in txt
    assert "антиутопия: 1" in txt
    assert "— По авторам —" in txt
    assert "Булгаков: 1" in txt
    assert "Оруэлл: 1" in txt

def test_txt_report_empty_books_still_has_stats() -> None:
    txt = build_txt_report([], [("ж", 0)], [("Автор", 0)])

    assert "Всего книг: 0" in txt
    assert "— Книги —" in txt
    assert "ж: 0" in txt
    assert "Автор: 0" in txt

# --- HTML ---

def test_html_report_contains_book_and_metadata(sample_stats) -> None:
    by_genre, by_author = sample_stats
    html = build_html_report([BOOK], by_genre, by_author)

    assert "<!DOCTYPE html>" in html
    assert '<html lang="ru">' in html
    assert "<title>Библиотека</title>" in html
    assert "Домашняя библиотека" in html
    assert "Всего книг: 1" in html
    assert "Мастер и Маргарита" in html
    assert "Булгаков" in html
    assert "<table>" in html

def test_html_report_volume_dash_when_missing(sample_stats) -> None:
    by_genre, by_author = sample_stats
    html = build_html_report([BOOK], by_genre, by_author)

    assert "<td>—</td>" in html

def test_html_report_volume_when_present(sample_stats) -> None:
    by_genre, by_author = sample_stats
    html = build_html_report([BOOK_WITH_VOL], by_genre, by_author)

    assert "<td>3</td>" in html

def test_html_report_escapes_special_characters(sample_stats) -> None:
    by_genre, by_author = sample_stats
    dangerous = (3, "<script>alert(1)</script>", "", "А&Б", 2020, 'жанр "х"')
    html = build_html_report([dangerous], by_genre, by_author)

    assert "&lt;script&gt;" in html
    assert "А&amp;Б" in html
    assert "жанр &quot;х&quot;" in html or "жанр &#x27;х&#x27;" in html

def test_html_report_empty_books_placeholder() -> None:
    html = build_html_report([], [], [])

    assert "Нет книг" in html
    assert "Всего книг: 0" in html

def test_html_report_stats_with_data(sample_stats) -> None:
    by_genre, by_author = sample_stats
    html = build_html_report([BOOK], by_genre, by_author)

    assert "<h2>По жанрам</h2>" in html
    assert "<h2>По авторам</h2>" in html
    assert ">роман<" in html or "<td>роман</td>" in html
    assert "<td>2</td>" in html
    assert "<td>Булгаков</td>" in html

def test_html_report_stats_empty_shows_no_data() -> None:
    html = build_html_report([BOOK], [], [])

    assert "Нет данных" in html

# --- сохранение ---

def test_save_report_writes_utf8(tmp_path: Path) -> None:
    path = tmp_path / "otchet.txt"
    text = "Подъём: ёлка, «книга»"
    save_report(str(path), text)

    assert path.exists()
    assert path.read_text(encoding="utf-8") == text

def test_save_report_roundtrip_build_txt(tmp_path: Path, sample_stats) -> None:
    by_genre, by_author = sample_stats
    content = build_txt_report([BOOK], by_genre, by_author)
    path = tmp_path / "library_report.txt"
    save_report(path, content)

    assert "Мастер и Маргарита" in path.read_text(encoding="utf-8")