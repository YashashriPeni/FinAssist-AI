import sqlite3


def create_database():

    conn = sqlite3.connect("loan_history.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS loan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant TEXT,
            income REAL,
            credit_score INTEGER,
            loan_amount REAL,
            recommended_product TEXT,
            emi REAL
        )
        """
    )

    conn.commit()
    conn.close()


def save_analysis(
        applicant,
        income,
        credit_score,
        loan_amount,
        recommended_product,
        emi):

    conn = sqlite3.connect("loan_history.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO loan_history
        (
            applicant,
            income,
            credit_score,
            loan_amount,
            recommended_product,
            emi
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            applicant,
            income,
            credit_score,
            loan_amount,
            recommended_product,
            emi
        )
    )

    conn.commit()
    conn.close()


def get_history():

    conn = sqlite3.connect("loan_history.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            applicant,
            income,
            credit_score,
            loan_amount,
            recommended_product,
            emi
        FROM loan_history
        ORDER BY id DESC
        """
    )

    data = cursor.fetchall()

    conn.close()

    return data


def get_history_with_id():
    conn = sqlite3.connect("loan_history.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            applicant,
            income,
            credit_score,
            loan_amount,
            recommended_product,
            emi
        FROM loan_history
        ORDER BY id DESC
        """
    )
    data = cursor.fetchall()
    conn.close()
    return data


def delete_history_item(item_id):
    conn = sqlite3.connect("loan_history.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM loan_history WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def clear_all_history():
    conn = sqlite3.connect("loan_history.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM loan_history;")
    conn.commit()
    conn.close()