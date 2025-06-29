import mysql.connector
import time


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="word"
    )

def drop_table():
    conn = get_connection()
    cursor = conn.cursor()

    # 테이블 생성
    drop_sql = "DROP TABLE IF EXISTS words;"

    cursor.execute(drop_sql)

    cursor.close()
    conn.close()

def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    # 테이블 생성
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS words (
        id INT AUTO_INCREMENT PRIMARY KEY,
        word VARCHAR(100) NOT NULL,
        type VARCHAR(50) NOT NULL,
        sense_no VARCHAR(3) NOT NULL,
        pos VARCHAR(10) NOT NULL,
        definition TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    cursor.execute(create_table_sql)

    cursor.close()
    conn.close()


def insert_word(word, type_, sense_no, pos):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO words (word, type, sense_no, pos)
        VALUES (%s %s %s %s)
    """, (word, type_, sense_no, pos))

    conn.commit()
    cursor.close()
    conn.close()

def insert_words(words):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO words (word, definition, type, sense_no, pos)
        VALUES (%s, %s, %s, %s, %s)
    """

    values = [(item["word"], item["definition"], item["type"], item["sense_no"], item["pos"]) for item in words]

    cursor.executemany(sql, values)
    conn.commit()

    cursor.close()
    conn.close()


def fetchall():
    conn = get_connection()
    cursor = conn.cursor()

    sql = "SELECT id, word FROM words"

    cursor.execute(sql)

    a = cursor.fetchall()

    cursor.close()
    conn.close()

    return a

def fetchall_by_id(ids: list):
    if not ids:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    # IN 절을 동적으로 구성
    placeholders = ','.join(['%s'] * len(ids))
    sql = f"SELECT * FROM words WHERE id IN ({placeholders})"

    cursor.execute(sql, ids)
    results = cursor.fetchall()

    return results


async def fetchall_by_ids(ids: list):
    if not ids:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    # IN 절을 동적으로 구성
    placeholders = ','.join(['%s'] * len(ids))
    sql = f"SELECT * FROM words WHERE id IN ({placeholders})"

    cursor.execute(sql, ids)
    results = cursor.fetchall()

    return results


def fetchall_by_word(word):
    conn = get_connection()
    cursor = conn.cursor()

    # IN 절을 동적으로 구성
    sql = f"SELECT * FROM words WHERE word = %s"

    cursor.execute(sql, (word,))
    results = cursor.fetchall()

    return results


if __name__ == '__main__':
    pass