# utils/evaluator.py

import json
import random
import re
import pandas as pd
import sqlparse
from llm.client import LLMClient
from db.postgres import PostgresConnector
from utils.schema import SchemaBuilder
from utils.prompt_builder import PromptBuilder

def normalize_sql(sql: str) -> str:
    formatted = sqlparse.format(
        sql,
        keyword_case='upper',
        identifier_case='lower',
        strip_comments=True,
        reindent=True
    )
    return formatted.strip().rstrip(';')

def infer_with_vote(llm: LLMClient, prompt: str, k: int = 5) -> str:
    candidates = []
    for _ in range(k):
        raw = llm.infer(prompt)
        m = re.search(r"```sql\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
        sql = m.group(1) if m else raw
        candidates.append(sql.strip().rstrip(';'))
    return max(set(candidates), key=candidates.count)

def _clean_result(rows):
    """
    Replace None with "" and cast every value to str,
    so that sorted() can compare them without type errors.
    """
    cleaned = []
    for row in rows:
        cleaned.append(tuple("" if v is None else str(v) for v in row))
    return cleaned

class Evaluator:
    def __init__(self, 
                 dev_path: str):
        with open(dev_path, encoding="utf-8") as f:
            self.data = json.load(f)

    def run(self,
            schema_path: str,
            db_name: str,
            schema_name: str,
            few_shot_path: str,
            limit: int,
            max_retries: int = 5):
        """
        Ora accetta anche schema_name per PostgresConnector.
        """
        schema_builder = SchemaBuilder(schema_path)
        prompt_builder = PromptBuilder(schema_builder, few_shot_path)
        llm = LLMClient()
        records = []

        examples = (self.data.copy()
                    if limit is None or limit >= len(self.data)
                    else random.sample(self.data, limit))

        for ex in examples:
            question = ex["question"]
            gold_sql  = ex["query"].strip().rstrip(";")
            db_id     = ex["db_id"]

            # 1) initial inference
            prompt = prompt_builder.build_prompt(question, db_id)
            initial_pred = infer_with_vote(llm, prompt, k=5)

            gold_norm    = normalize_sql(gold_sql)
            initial_norm = normalize_sql(initial_pred)
            initial_exact = (initial_norm == gold_norm)

            # connessione col giusto schema
            db = PostgresConnector(db_name, schema_name=schema_name)
            first_result = db.run_query(initial_pred)
            if isinstance(first_result, list):
                g_clean      = _clean_result(db.run_query(gold_sql) or [])
                r_clean      = _clean_result(first_result)
                initial_exec = (sorted(g_clean) == sorted(r_clean))
            else:
                initial_exec = False

            predicted_sql = initial_pred
            final_exec    = False

            # 2) retry loop
            for attempt in range(1, max_retries+1):
                result = db.run_query(predicted_sql)
                if not (isinstance(result, str) and result.startswith("[ERROR]")):
                    gold_res  = db.run_query(gold_sql)
                    g_clean   = _clean_result(gold_res if isinstance(gold_res, list) else [])
                    r_clean   = _clean_result(result    if isinstance(result,   list) else [])
                    final_exec = (sorted(g_clean) == sorted(r_clean))
                    break

                db.conn.rollback()
                error_msg = result
                corrected_prompt = prompt_builder.build_prompt(
                    question=question,
                    db_id=db_id,
                    error_context=error_msg
                )
                predicted_sql = infer_with_vote(llm, corrected_prompt, k=1)

            db.close()

            final_norm   = normalize_sql(predicted_sql)
            final_exact  = (final_norm == gold_norm)

            records.append({
                "question":                question,
                "gold_sql":                gold_sql,
                "initial_predicted_sql":   initial_pred,
                "initial_exact_match":     initial_exact,
                "initial_execution_match": initial_exec,
                "final_predicted_sql":     predicted_sql,
                "final_exact_match":       final_exact,
                "final_execution_match":   final_exec
            })

        df = pd.DataFrame(records)
        df.to_csv("results/text2sql_results.csv", index=False)

        print("\n=== INITIAL (no correction) METRICS ===")
        print("Initial Exact-Match Accuracy:    ", df["initial_exact_match"].mean())
        print("Initial Execution Accuracy:      ", df["initial_execution_match"].mean())

        print("\n=== FINAL (with correction) METRICS ===")
        print("Final Exact-Match Accuracy:      ", df["final_exact_match"].mean())
        print("Final Execution Accuracy:        ", df["final_execution_match"].mean())

        print("\nResults saved to results/text2sql_results.csv")
