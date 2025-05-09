class PromptBuilder:
    def __init__(self, schema_builder, few_shot_path):
        with open(few_shot_path) as f:
            self.few_shot = f.read()
        self.schema_builder = schema_builder


    def build_prompt(self, question, db_id):
        schema = self.schema_builder.get_flat_schema_string(db_id)
        return f"""
You are an expert data analyst. Translate the following natural language questions into SQL queries for PostgreSQL.

{self.few_shot}

-- Database schema:
{schema}

-- Now answer this:
-- Question: {question}
-- SQL:
Only answer with the SQL query, no explanation""".strip()
