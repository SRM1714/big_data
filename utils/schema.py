# utils/schema.py

import json

class SchemaBuilder:
    def __init__(self, schema_path):
        with open(schema_path, encoding="utf-8") as f:
            self.schemas = json.load(f)

    def get_schema_string(self, db_id):
        """
        Restituisce righe del tipo:
         table_name.column_name (type)
        """
        for db in self.schemas:
            if db["db_id"] == db_id:
                tables  = db["table_names_original"]
                cols    = db["column_names_original"]
                types   = db["column_types"]
                lines = [
                    f"{tables[tid]}.{col} ({types[i]})"
                    for i, (tid, col) in enumerate(cols)
                    if col != "*"
                ]
                return "\n".join(lines)
        return ""

    def get_friendly_names_string(self, db_id):
        """
        Restituisce mapping:
         table_name.column_name -> friendly_column_name
        basato su `column_names` e `column_names_original`
        """
        for db in self.schemas:
            if db["db_id"] == db_id:
                tables        = db["table_names_original"]
                cols_orig     = db["column_names_original"]
                friendly_cols = db.get("column_names", [])
                lines = []
                for (tid, col), friendly in zip(cols_orig, friendly_cols):
                    if col != "*":
                        tbl = tables[tid]
                        lines.append(f"{tbl}.{col} -> {friendly}")
                return "\n".join(lines)
        return ""
