# db/postgres.py

import psycopg2

class PostgresConnector:
    def __init__(self, db_name, schema_name=None):
        """
        db_name: nome del database PostgreSQL
        schema_name: nome del primo schema in search_path (se None, user db_name)
        """
        schema = schema_name or db_name
        # connect e settaggio del search_path allo schema corretto + public
        self.conn = psycopg2.connect(
            dbname=db_name,
            user="uzh_user",
            password="bigdata@uzh",
            host="160.85.252.195",
            port=5433,
            options=f"-c search_path={schema},public"
        )
        # ogni statement è autocommit
        self.conn.autocommit = True

    def run_query(self, sql: str):
        """
        Esegue la query SQL e restituisce:
         - lista di tuple se SELECT
         - [] se DDL o no resultset
         - stringa "[ERROR] ..." in caso di eccezione
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
                try:
                    return cur.fetchall()
                except psycopg2.ProgrammingError:
                    return []
        except Exception as e:
            self.conn.rollback()
            return f"[ERROR] {e}"

    def close(self):
        self.conn.close()
