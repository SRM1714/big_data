# utils/prompt_builder.py

class PromptBuilder:
    """
    Costruisce un prompt che:
      - include sempre few-shot + schema flattened
      - in caso di errore SQL inietta anche l’error_context
      - forza a restituire SOLO la query SQL completa, senza commenti né ";" finali
    """
    def __init__(self, schema_builder, few_shot_path="prompts/few_shot_examples.txt"):
        with open(few_shot_path, encoding="utf-8") as f:
            self.few_shot = f.read().strip()
        self.schema_builder = schema_builder

    def build_prompt(self,
                     question: str,
                     db_id: str,
                     error_context: str = None) -> str:
        parts = []

        # Se abbiamo un contesto di errore, lo iniettiamo per la correzione
        if error_context:
            parts.append(
                f"ERROR CONTEXT: {error_context.strip()}\n"
                "Please correct your SQL below, following the examples and schema exactly.\n\n"
            )

        # Istruzioni principali
        parts.append(
            "You are an expert biomedical data analyst. When given a question,\n"
            "you must reply with exactly one valid PostgreSQL SQL statement.\n"
            "Do NOT include any explanation, comments, or trailing semicolons—only the SQL.\n\n"
            "Requirements:\n"
            "1. Output ONLY the SQL statement.\n"
            "2. Use UPPERCASE for SQL keywords.\n"
            "3. Match table.column names exactly as shown below.\n"
            "4. Follow the style and formatting of the few-shot examples.\n"
            "5. Do not introduce unused aliases, functions, or tables.\n\n"
            "OUTPUT FORMAT:\n"
            "SELECT column1, column2\n"
            "FROM table1\n"
            "JOIN table2 ON table1.key = table2.key\n"
            "WHERE condition\n\n"
        )

        # Few-shot examples
        parts.append("Below are 20 few-shot examples (10 simple, 10 complex):\n\n")
        parts.append(self.few_shot)
        parts.append("\n\n")

        # Schema flattened
        schema_flat = self.schema_builder.get_flat_schema_string(db_id)
        parts.append(f"-- Flattened schema (table.column (type)):\n{schema_flat}\n\n")

        # Domanda
        parts.append(f"-- Question:\n{question}\n\n-- SQL:\n")

        return "".join(parts)
