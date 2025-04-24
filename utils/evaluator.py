import json
import pandas as pd
from llm.client import LLMClient
from db.postgres import PostgresConnector
from utils.schema import SchemaBuilder
from utils.prompt_builder import PromptBuilder
from config import DB_NAME

class Evaluator:
    def __init__(self, dev_path):
        with open(dev_path) as f:
            self.data = json.load(f)

    def run(self, schema_path, limit=10):
        schema_builder = SchemaBuilder(schema_path)
        prompt_builder = PromptBuilder(schema_builder)
        llm = LLMClient()
        results = []

        for ex in self.data[:limit]:
            question = ex["question"]
            gold_sql = ex["query"].strip().rstrip(";")
            db_id = ex["db_id"]

            prompt = prompt_builder.build_prompt(question, db_id)
            print("\n---")
            print(f"[QUESTION]: {question}")
            print(f"[PROMPT]:\n{prompt}\n")

            try:
                raw_output = llm.infer(prompt)
                predicted_sql = raw_output.strip().split("\n")[0].strip().rstrip(";")
                print(f"[LLM RESPONSE]: {raw_output}")
                print(f"[PREDICTED SQL]: {predicted_sql}")
            except Exception as e:
                predicted_sql = f"[ERROR] {e}"

            is_exact = predicted_sql.lower() == gold_sql.lower()

            try:
                db = PostgresConnector(DB_NAME)
                gold_res = db.run_query(gold_sql)
                pred_res = db.run_query(predicted_sql)
                execution_match = gold_res == pred_res
                db.close()
            except Exception:
                execution_match = False

            results.append({
                "question": question,
                "gold_sql": gold_sql,
                "predicted_sql": predicted_sql,
                "exact_match": is_exact,
                "execution_match": execution_match
            })

        df = pd.DataFrame(results)
        df.to_csv("results/text2sql_results.csv", index=False)
        print("\n✅ Exact Match Accuracy:", df["exact_match"].mean())
        print("✅ Execution Accuracy:", df["execution_match"].mean())
        print("📁 Exported to results/text2sql_results.csv")
