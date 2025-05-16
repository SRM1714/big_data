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
    """
    Chiama il modello k volte e ritorna la query più frequente,
    estraendo l’intero blocco SQL fra ```sql```...``` o, in mancanza,
    tutto il testo restituito.
    """
    candidates = []
    for _ in range(k):
        raw = llm.infer(prompt)
        m = re.search(r"```sql\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
        sql = m.group(1) if m else raw
        candidates.append(sql.strip().rstrip(';'))
    return max(set(candidates), key=candidates.count)

def _clean_result(rows):
    """
    Sostituisce ogni None in "" per evitare TypeError su sorted()
    """
    cleaned = []
    for row in rows:
        cleaned.append(tuple("" if v is None else v for v in row))
    return cleaned

class Evaluator:
    def __init__(self, dev_path: str):
        with open(dev_path, encoding="utf-8") as f:
            self.data = json.load(f)

    def run(self,
            schema_path: str,
            db_name: str,
            few_shot_path: str,
            limit: int,
            max_retries: int = 5):
        schema_builder = SchemaBuilder(schema_path)
        prompt_builder = PromptBuilder(schema_builder, few_shot_path)
        llm = LLMClient()
        records = []

        examples = (self.data.copy()
                    if limit is None or limit >= len(self.data)
                    else random.sample(self.data, limit))

        for ex in examples:
            q     = ex["question"]
            gold  = ex["query"].strip().rstrip(";")
            db_id = ex["db_id"]

            # 1) Prompt iniziale
            prompt = prompt_builder.build_prompt(q, db_id)
            predicted_sql = infer_with_vote(llm, prompt, k=3)
            print(f"[PREDICTED SQL]:\n{predicted_sql}")

            gold_norm = normalize_sql(gold)
            db = PostgresConnector(db_name)
            exec_match = False

            # 2) Loop di retry se ci sono errori SQL
            for attempt in range(1, max_retries+1):
                result = db.run_query(predicted_sql)

                if not (isinstance(result, str) and result.startswith("[ERROR]")):
                    # puliamo eventuali None
                    gold_res = db.run_query(gold)
                    g_clean = _clean_result(gold_res if isinstance(gold_res, list) else [])
                    r_clean = _clean_result(result   if isinstance(result,   list) else [])
                    exec_match = (sorted(g_clean) == sorted(r_clean))
                    if not exec_match:
                        print(f">>> MISMATCH execution after retry {attempt}")
                    break

                # rollback e nuovo prompt con error_context
                db.conn.rollback()
                error_msg = result
                print(f"[SQL ERROR retry {attempt}]: {error_msg}")

                feedback = prompt_builder.build_prompt(
                    question=q,
                    db_id=db_id,
                    error_context=error_msg
                )
                predicted_sql = infer_with_vote(llm, feedback, k=1)
                print(f"[CORRECTED SQL attempt {attempt}]:\n{predicted_sql}")

            db.close()

            # 3) Exact match sull’ultima versione
            final_norm = normalize_sql(predicted_sql)
            exact_match = (final_norm == gold_norm)

            records.append({
                "question":        q,
                "gold_sql":        gold,
                "predicted_sql":   predicted_sql,
                "exact_match":     exact_match,
                "execution_match": exec_match
            })

        df = pd.DataFrame(records)
        df.to_csv("results/text2sql_results.csv", index=False)
        print("\nExact Match Accuracy:   ", df["exact_match"].mean())
        print("Execution Accuracy:     ", df["execution_match"].mean())
        print("Risultati salvati in results/text2sql_results.csv")
