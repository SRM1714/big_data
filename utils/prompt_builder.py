import random

class PromptBuilder:
    def __init__(self, schema_builder, dev_data, num_shots=3):
        self.schema_builder = schema_builder
        self.dev_data = dev_data
        self.num_shots = num_shots

    def build_few_shot_examples(self):
        examples = random.sample(self.dev_data, self.num_shots)
        few_shot = ""
        for ex in examples:
            question = ex["question"]
            sql = ex["query"].strip().rstrip(";")
            few_shot += f"""
-- Example:
-- Question: {question}
-- SQL: {sql}
"""
        return few_shot.strip()

    def build_prompt(self, question, db_id):
        schema = self.schema_builder.get_schema_string(db_id)
        few_shot = self.build_few_shot_examples()

        return f"""
You are an expert data analyst. Translate the following natural language questions into SQL queries for PostgreSQL.

{few_shot}

-- Database schema:
{schema}

-- Now answer this:
-- Question: {question}
-- SQL:
Respond ONLY with the SQL query, no explanations, no markdown.""".strip()
