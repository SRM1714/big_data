import psycopg2

class PostgresConnector:
    def __init__(self, db_name):
        # con options imposto il search_path sullo schema oncomx_v1_0_25
        self.conn = psycopg2.connect(
            dbname=db_name,
            user="uzh_user",
            password="bigdata@uzh",
            host="160.85.252.195",
            port=5433,
            options=f"-c search_path={db_name},public"
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
