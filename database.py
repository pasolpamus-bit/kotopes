import sqlite3
import time

class Database:
    def __init__(self, db_name="bybit_blockchain.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS holders (
                    token_symbol TEXT,
                    token_address TEXT,
                    wallet_address TEXT,
                    last_balance REAL,
                    timestamp REAL,
                    PRIMARY KEY (token_address, wallet_address)
                )
            """)

    def update_holder(self, symbol, token_addr, wallet, balance):
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO holders (token_symbol, token_address, wallet_address, last_balance, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol, token_addr, wallet, balance, time.time()))

    def get_holder_data(self, token_addr, wallet):
        cursor = self.conn.cursor()
        cursor.execute("SELECT last_balance, timestamp FROM holders WHERE token_address = ? AND wallet_address = ?", (token_addr, wallet))
        return cursor.fetchone()