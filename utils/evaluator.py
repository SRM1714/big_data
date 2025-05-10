import json
import random
import pandas as pd
from llm.client import LLMClient
from db.postgres import PostgresConnector
from utils.schema import SchemaBuilder
from utils.prompt_builder import PromptBuilder
#from config import DB_NAME

class Evaluator:
    def __init__(self, dev_path):
        # Carica tutto il dev-set in memoria
        with open(dev_path, encoding="utf-8") as f:
            self.data = json.load(f)

    def run(self, schema_path, db_name, few_shot_path, limit):
        """
        Esegue la valutazione su un campione casuale di 'limit' esempi (o su tutto il dataset
        se limit è None o > len(self.data)).
        """
        schema_builder = SchemaBuilder(schema_path)
        prompt_builder = PromptBuilder(schema_builder, few_shot_path)
        llm = LLMClient()
        records = []

        # Scegli a caso 'limit' esempi dal dev-set
        if limit is None or limit >= len(self.data):
            examples = self.data.copy()
        else:
            examples = random.sample(self.data, limit)

        for ex in examples:
            q     = ex["question"]
            gold  = ex["query"].strip().rstrip(";")
            db_id = ex["db_id"]

            # Costruisci il prompt
            prompt = prompt_builder.build_prompt(q, db_id)
            print(f"\n---\n[QUESTION]: {q}\n[PROMPT]:\n{prompt}\n")

            # Chiedi la query al modello
            try:
                raw       = llm.infer(prompt)
                predicted = raw.strip().split("\n")[0].rstrip(";")
                print(f"[LLM RESPONSE]: {raw}")
                print(f"[PREDICTED SQL]: {predicted}")
            except Exception as e:
                predicted = ""
                print(f"[LLM ERROR]: {e}")

            # Exact match
            exact_match = (predicted.lower() == gold.lower())

            # Execution match
            try:
                db = PostgresConnector(db_name)
                gold_res = db.run_query(gold)
                print('ACTTUAL QUERY')
                print(gold)
                print('PREDICTED QUERY')
                print(predicted)
                pred_res = db.run_query(predicted)
                db.close()

                # Ordiniamo per confronto
                sorted_gold = sorted(gold_res)
                sorted_pred = sorted(pred_res)
                exec_match  = (sorted_gold == sorted_pred)

                if not exec_match:
                    print(">>> MISMATCH!")
                    print(" gold_res:", sorted_gold[:5], "… total", len(sorted_gold))
                    print(" pred_res:", sorted_pred[:5], "… total", len(sorted_pred))
            except Exception as e:
                exec_match = False
                print(f"[SQL EXECUTION ERROR]: {e}")

            # Registra il risultato
            records.append({
                "question":        q,
                "gold_sql":        gold,
                "predicted_sql":   predicted,
                "exact_match":     exact_match,
                "execution_match": exec_match
            })

        # Salva i risultati
        df = pd.DataFrame(records)
        df.to_csv("results/text2sql_results.csv", index=False)
        print("\nExact Match Accuracy:  ", df["exact_match"].mean())
        print("Execution Accuracy:    ", df["execution_match"].mean())
        print("Results written to results/text2sql_results.csv")
