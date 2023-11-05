import sqlite3
from datetime import datetime


class DBHelper:
    def __init__(self, dbname="test2.db"): # test.db
        self.dbname = dbname
        try:
            print(f"{datetime.now().isoformat(' ', 'seconds')} Initiating SQLite3 database connection to {self.dbname}...\n")
            self.locCon = sqlite3.connect(dbname, check_same_thread=False)
            self.locCon.row_factory = lambda cursor, row: row[0]
            self.cur = self.locCon.cursor()

        except sqlite3.Error as e:
            print(f"\nFailed to initiate SQLite3 database connection to {self.dbname}...\n")
            log().critical('local database initialisation error: "%s"', e)

    def setup(self):

        print(f"{datetime.now().isoformat(' ', 'seconds')} Initiating SQLite3 DB...\n")

        self.cur.execute('''CREATE TABLE IF NOT EXISTS users (
            id             INTEGER UNIQUE NOT NULL,
            username       VARCHAR (100),
            first_name     VARCHAR (50),
            tokens INTEGER DEFAULT (2),
            terms_accepted BOOL    DEFAULT FALSE,
            jobs_completed INTEGER DEFAULT (0),
            first_active   VARCHAR (19),
            last_active    VARCHAR (19),
            user_in_queue  BOOL    DEFAULT FALSE
        )''')
        self.locCon.commit()



    
    def check_user(self, user_id, username, first_name):
        self.cur.execute(f"SELECT id FROM users WHERE id = '{user_id}'")
        result = self.cur.fetchone()

        if not result:
            self.cur.execute("INSERT INTO users (id, username, first_name) VALUES (?, ?, ?)",
                        (user_id, username, first_name))
            self.locCon.commit()
            return False
        return True

    def check_terms(self, user_id):
        self.cur.execute(f"SELECT terms_accepted FROM users WHERE id = '{user_id}'")
        result = self.cur.fetchone()

        return result

    def accept_terms(self, user_id):
        try:
            self.cur.execute(f"UPDATE users SET terms_accepted = TRUE WHERE id = '{user_id}'")
            self.locCon.commit()

        except Exception as e:
            print(e)

    def update_jobs_completed(self, user_id):
        self.cur.execute(f"UPDATE users SET jobs_completed = jobs_completed + 1 WHERE id = '{user_id}'")
        self.locCon.commit()

    def update_first_active(self, user_id, timestamp):
        self.cur.execute(f"UPDATE users SET first_active = '{timestamp}' WHERE id = '{user_id}'")
        self.locCon.commit()

    def update_last_active(self, user_id, timestamp):
        self.cur.execute(f"UPDATE users SET last_active = '{timestamp}' WHERE id = '{user_id}'")
        self.locCon.commit()

    def get_user_names(self):
        self.cur.execute(f"SELECT username FROM users")
        result = self.cur.fetchall()
        return result
    
    def get_user_ids(self):
        self.cur.execute(f"SELECT id FROM users")
        result = self.cur.fetchall()

        return result
    
    def get_user_tokens(self, user_id):
        self.cur.execute(f"SELECT tokens FROM users WHERE id = '{user_id}'")
        result = self.cur.fetchone()

        return result

    def update_tokens(self, user_id, token_amount):
        try:
            self.cur.execute(f"UPDATE users SET tokens = tokens + '{token_amount}' WHERE id = '{user_id}'")
            self.locCon.commit()

        except Exception as e:
            print(e)

    def writeoff_token(self, user_id):
        try:
            self.cur.execute(f"UPDATE users SET tokens = tokens - 1 WHERE id = '{user_id}'")
            self.locCon.commit()

        except Exception as e:
            print(e)

    def check_queue_status(self, user_id):
        try:
            self.cur.execute(f"SELECT user_in_queue FROM users WHERE id = '{user_id}'")
            queue_status = self.cur.fetchone()

            if queue_status == 0: # if user not in queue, return true, else false
                return True
            return False

        except Exception as e:
            print(e)

    def user_in_queue(self, user_id):
        try:
            self.cur.execute(f"UPDATE users SET user_in_queue = TRUE WHERE id = '{user_id}'")
            self.locCon.commit()

        except Exception as e:
            print(e)

    def user_notin_queue(self, user_id):
        try:
            self.cur.execute(f"UPDATE users SET user_in_queue = FALSE WHERE id = '{user_id}'")
            self.locCon.commit()

        except Exception as e:
            print(e)

    def cancel_queue_status(self):
        try:
            self.cur.execute(f"UPDATE users SET user_in_queue = FALSE")
            self.locCon.commit()

        except Exception as e:
            print(e)


