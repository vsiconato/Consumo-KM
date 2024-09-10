import sqlite3

def check_db_status():
    conn = sqlite3.connect('test.db', timeout=10, isolation_level=None)
    cursor = conn.cursor()
    try:
        cursor.execute('PRAGMA database_list;')
        print(cursor.fetchall())
        cursor.execute('PRAGMA busy_timeout;')
        print(cursor.fetchall())
    except sqlite3.Error as e:
        print(f"Erro: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    check_db_status()

