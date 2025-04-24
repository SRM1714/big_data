class PromptBuilder:
    def __init__(self, schema_builder, few_shot_path="prompts/few_shot_examples.txt"):
        with open(few_shot_path) as f:
            self.few_shot = f.read()
        self.schema_builder = schema_builder

    def build_prompt(self, question, db_id):
        schema = self.schema_builder.get_schema_string(db_id)
        return f"""
You are an expert biomedical data analyst. Translate natural language questions into SQL queries for PostgreSQL.

{self.few_shot}

-- Schema:
{schema}

-- Now answer the following:
-- Question: {question}
-- SQL:""".strip()
