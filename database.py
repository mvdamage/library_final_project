import sqlite3

class Database:
    def __init__(self, db_name="library.db"):
        self.conn = sqlite3.connect(db_name)
        self.conn.create_function(
            "py_lower",
            1,
            lambda value: "" if value is None else str(value).casefold().replace("ё", "е"),
        )
        self.cursor = self.conn.cursor()
        self.create_table()
    
    def create_table(self):
        """Создание таблицы книг, если она не существует"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                volume TEXT,
                author TEXT NOT NULL,
                year INTEGER NOT NULL,
                genre TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    # Нормализация тома
    def _norm_volume(self, volume):
        """Пустой том → NULL, иначе текст как ввели."""
        if volume is None:
            return None
        s = str(volume).strip().replace("Ё", "Е").replace("ё", "е")
        return None if not s else s

    # Нормализация года
    def _norm_year(self, year):
        if year is None:
            return None
        s = str(year).strip()
        if not s or not s.isdigit():
            return None
        return int(s)
    
    # Нормализация текстовых строк без пробелов, без учета регистра; ё -> е при поиске и дубликатах
    def _norm_text(self, value):
        if value is None:
            return ""
        s = str(value).strip().casefold()
        return s.replace("ё", "е")

    def _save_text(self, value):
        """БД: пробелы по краям, замена ё → е.
        Регистр не меняется"""
        if value is None:
            return ""
        s = str(value).strip()
        return s.replace("Ё", "Е").replace("ё", "е")
    
    def is_duplicate_book(self, title, volume, author, year, genre, exclude_id=None):
        """True — такая книга уже есть (все поля совпадают, регистр не важен).
        exclude_id — при редактировании не сравнивать с самой собой.
        """
        t = self._norm_text(title)
        a = self._norm_text(author)
        g = self._norm_text(genre)
        vol = self._norm_volume(volume)
        y = self._norm_year(year)
        self.cursor.execute(
            "SELECT id, title, volume, author, year, genre FROM library"
        )
        for row in self.cursor.fetchall():
            bid, r_title, r_vol, r_author, r_year, r_genre = row
            if exclude_id is not None and bid == exclude_id:
                continue
            if (
                self._norm_text(r_title) == t
                and self._norm_volume(r_vol) == vol
                and self._norm_text(r_author) == a
                and self._norm_year(r_year) == y
                and self._norm_text(r_genre) == g
            ):
                return True
        return False
  
    def add_book(self, title, volume, author, year, genre):
        """Добавление новой книги"""
        title = self._save_text(title)
        author = self._save_text(author)
        genre = self._save_text(genre)
        volume = self._norm_volume(volume)
        year = self._norm_year(year)
        self.cursor.execute('''
            INSERT INTO library (title, volume, author, year, genre)
            VALUES (?, ?, ?, ?, ?)
         ''', (title, volume, author, year, genre))
        self.conn.commit()
        return self.cursor.lastrowid
 
    def get_all_books(self):
        """Получение всех книг"""
        self.cursor.execute('''
            SELECT id, title, volume, author, year, genre 
            FROM library ORDER BY id
        ''')
        return self.cursor.fetchall()
    
    def delete_book(self, book_id):
        """Удаление книги"""
        self.cursor.execute("DELETE FROM library WHERE id = ?", (book_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def update_book(self, book_id, title, volume, author, year, genre):
        """Обновление книги"""
        title = self._save_text(title)
        author = self._save_text(author)
        genre = self._save_text(genre)
        volume = self._norm_volume(volume)
        year = self._norm_year(year)
        self.cursor.execute('''
            UPDATE library 
            SET title = ?, volume = ?, author = ?, year = ?, genre = ?
            WHERE id = ?
        ''', (title, volume, author, year, genre, book_id))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def _norm_search(self, text):
        """Нормализация поиска"""
        if text is None:
            return ""
        return str(text).strip().casefold().replace("ё", "е")
    
    def search_book(self, search_term):
        """Поиск по названию, автору, жанру, году без учёта регистра"""
        pattern = f"%{self._norm_search(search_term)}%"
        self.cursor.execute(
            '''
            SELECT id, title, volume, author, year, genre
            FROM library
            WHERE py_lower(title) LIKE ?
                OR py_lower(author) LIKE ?
                OR py_lower(genre) LIKE ?
                OR CAST(year AS TEXT) LIKE ?
            ORDER BY id
            ''',
            (pattern, pattern, pattern, pattern),
        )
        return self.cursor.fetchall() 

    def count_books(self):
        """Общее количество книг"""
        self.cursor.execute("SELECT COUNT(*) FROM library")
        return self.cursor.fetchone()[0]
    
    def count_by_genre(self):
        """Количество книг по жанрам"""
        self.cursor.execute('''
            SELECT genre, COUNT(*) AS genre_count
            FROM library
            GROUP BY genre
            ORDER BY genre_count DESC;
        ''')
        return self.cursor.fetchall()
    
    def count_by_author(self):
        """Количество книг по авторам"""
        self.cursor.execute('''
            SELECT author, COUNT(*) AS author_count
            FROM library
            GROUP BY author
            ORDER BY author_count DESC;
        ''')
        return self.cursor.fetchall()
    
    def close(self):
        """Закрытие соединения с базой данных"""
        self.conn.close()