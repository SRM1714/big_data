import psycopg2

class PostgresConnector:
    def __init__(self, db_name):
        self.conn = psycopg2.connect(
            dbname=db_name,
            user="uzh_user",
            password="bigdata@uzh",
            host="160.85.252.195",
            port=5433
        )

    def run_query(self, sql):
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
                return cur.fetchall()
        except Exception as e:
            return f"[ERROR] {e}"

    def close(self):
        self.conn.close()
