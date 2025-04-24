import json

class SchemaBuilder:
    def __init__(self, schema_path):
        with open(schema_path) as f:
            self.schemas = json.load(f)

    def get_schema_string(self, db_id):
        for db in self.schemas:
            if db["db_id"] == db_id:
                lines = []
                tables = db["table_names_original"]
                columns = db["column_names_original"]
                types = db["column_types"]
                for i, (table_id, col_name) in enumerate(columns):
                    if col_name != "*":
                        lines.append(f"{tables[table_id]}.{col_name} ({types[i]})")
                return "\n".join(lines)
        return ""
