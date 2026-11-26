"""Автотесты данных (database.py)."""

from pathlib import Path

import pytest

from database import Database

@pytest.fixture
def db(tmp_path: Path):
    database = Database(str(tmp_path / "test_library.db"))
    yield database
    database.close()

def add_sample(
    database: Database,
    title="Мастер и Маргарита",
    volume="",
    author="Булгаков",
    year=1967,
    genre="роман",
) -> int:
    return database.add_book(title, volume, author, year, genre)

# --- нормализация ---

def test_norm_volume_empty_becomes_none(db: Database) -> None:
    assert db._norm_volume(None) is None
    assert db._norm_volume("") is None
    assert db._norm_volume("   ") is None
    assert db._norm_volume("2") == "2"

def test_norm_year_invalid_returns_none(db: Database) -> None:
    assert db._norm_year(None) is None
    assert db._norm_year("") is None
    assert db._norm_year("abc") is None
    assert db._norm_year(" 1967 ") == 1967

def test_save_text_trims_and_replaces_yo(db: Database) -> None:
    assert db._save_text("  Ёлка  ") == "Елка"
    assert db._save_text("подъём") == "подъем"

# --- CRUD ---

def test_add_and_get_all_books(db: Database) -> None:
    book_id = add_sample(db, volume="1")
    rows = db.get_all_books()
    assert len(rows) == 1
    rid, title, volume, author, year, genre = rows[0]
    assert rid == book_id
    assert title == "Мастер и Маргарита"
    assert volume == "1"
    assert author == "Булгаков"
    assert year == 1967
    assert genre == "роман"

def test_add_book_empty_volume_stored_as_null(db: Database) -> None:
    add_sample(db, volume="")
    _id, _t, volume, *_ = db.get_all_books()[0]
    assert volume is None
 
def test_update_book(db: Database) -> None:
    book_id = add_sample(db)
    assert db.update_book(
        book_id,
        "Собачье сердце",
        "2",
        "Булгаков",
        1925,
        "повесть",
    )
    row = db.get_all_books()[0]
    assert row[0] == book_id
    assert row[1] == "Собачье сердце"
    assert row[2] == "2"
    assert row[4] == 1925
    assert row[5] == "повесть"

def test_update_missing_book_returns_false(db: Database) -> None:
    assert not db.update_book(999, "X", "", "Y", 2000, "ж")

def test_delete_book(db: Database) -> None:
    book_id = add_sample(db)
    assert db.delete_book(book_id)
    assert db.get_all_books() == []

def test_delete_missing_book_returns_false(db: Database) -> None:
    assert not db.delete_book(999)

# --- дубликаты ---

def test_is_duplicate_same_fields_case_insensitive(db: Database) -> None:
    add_sample(db, title="Война и мир", author="Толстой", year=1869, genre="роман")
    assert db.is_duplicate_book(
        "война и мир", "", "ТОЛСТОЙ", "1869", "Роман"
    )

def test_is_duplicate_different_author_false(db: Database) -> None:
    add_sample(db)
    assert not db.is_duplicate_book(
        "Мастер и Маргарита", "", "Достоевский", 1967, "роман"
    )

def test_is_duplicate_respects_volume(db: Database) -> None:
    add_sample(db, volume="1")
    assert not db.is_duplicate_book(
        "Мастер и Маргарита", "2", "Булгаков", 1967, "роман"
    )
    assert db.is_duplicate_book(
        "Мастер и Маргарита", "1", "Булгаков", 1967, "роман"
    )

def test_is_duplicate_exclude_id_on_edit(db: Database) -> None:
    book_id = add_sample(db)
    assert not db.is_duplicate_book(
        "Мастер и Маргарита",
        "",
        "Булгаков",
        1967,
        "роман",
        exclude_id=book_id,
    )

def test_is_duplicate_yo_treated_as_e(db: Database) -> None:
    add_sample(db, title="Подъём", author="Автор", year=2000, genre="ж")
    assert db.is_duplicate_book("Подъем", "", "автор", 2000, "ж")

# --- поиск ---

def test_search_by_author_case_insensitive(db: Database) -> None:
    add_sample(db)
    add_sample(
        db,
        title="1984",
        author="Оруэлл",
        year=1949,
        genre="антиутопия",
    )
    found = db.search_book("оруэлл")
    assert len(found) == 1
    assert found[0][1] == "1984"

def test_search_by_title_fragment(db: Database) -> None:
    add_sample(db)
    found = db.search_book("маргарита")
    assert len(found) == 1
    assert found[0][3] == "Булгаков"

def test_search_by_year_as_text(db: Database) -> None:
    add_sample(db, year=1967)
    found = db.search_book("1967")
    assert len(found) == 1

def test_search_yo_query_finds_e_title(db: Database) -> None:
    db.add_book("Елка", "", "Тест", 2020, "ж")
    found = db.search_book("ёлка")
    assert len(found) == 1
    assert found[0][1] == "Елка"

def test_search_empty_term_returns_all(db: Database) -> None:
    add_sample(db)
    add_sample(db, title="1984", author="Оруэлл", year=1949, genre="антиутопия")
    found = db.search_book("")
    assert len(found) == 2

# --- статистика ---

def test_count_books(db: Database) -> None:
    assert db.count_books() == 0
    add_sample(db)
    add_sample(db, title="1984", author="Оруэлл", year=1949, genre="антиутопия")
    assert db.count_books() == 2

def test_count_by_genre_and_author(db: Database) -> None:
    add_sample(db)
    add_sample(db, title="1984", author="Оруэлл", year=1949, genre="антиутопия")
    add_sample(db, title="Скотный двор", author="Оруэлл", year=1945, genre="антиутопия")

    by_genre = dict(db.count_by_genre())
    assert by_genre["антиутопия"] == 2
    assert by_genre["роман"] == 1

    by_author = dict(db.count_by_author())
    assert by_author["Оруэлл"] == 2
    assert by_author["Булгаков"] == 1

def test_get_all_books_ordered_by_id(db: Database) -> None:
    first = add_sample(db, title="A")
    second = add_sample(db, title="B", author="X", year=2001, genre="g")
    ids = [row[0] for row in db.get_all_books()]
    assert ids == [first, second]