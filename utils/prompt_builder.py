# utils/prompt_builder.py

class PromptBuilder:
    def __init__(self, schema_builder, few_shot_path="prompts/few_shot_examples.txt"):
        # Carica gli esempi few-shot già formattati
        with open(few_shot_path, encoding="utf-8") as f:
            self.few_shot = f.read().strip()
        self.schema_builder = schema_builder

    def build_prompt(self, question, db_id):
        """
        Ritorna un prompt testuale. Il modello deve rispondere
        solo con la query SQL, niente spiegazioni, niente commenti,
        niente punti e virgola finali.
        """
        schema_str   = self.schema_builder.get_schema_string(db_id)
        #friendly_str = self.schema_builder.get_friendly_names_string(db_id)

        return f"""
You are an expert biomedical data analyst. When given a question, you must reply with exactly one valid PostgreSQL SQL statement. Do NOT include any explanation, comments, or trailing semicolons—only the SQL. Pay attention to the examples provided, they all come from the same database.


Requirements:
- Output only, and really only, and really only only the SQL statement (no explanations, no comments, no trailing semicolons).  
- We will evaluate Exact Match and Execution Accuracy, so be precise.

Below are 20 few-shot examples (10 simple, 10 complex) **from the same dataset**:

{self.few_shot}

-- Schema (table.column (type)):
{schema_str}

-- Question:
{question}

-- SQL:
""".strip()
