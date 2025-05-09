import json

def flatten_schema_from_file(tables_path: str, db_id: str) -> str:
    """
    Flattens a Spider-style schema into a single string with table-prefixed columns.

    Parameters:
        tables_path: Path to tables.json
        db_id: Database ID to extract schema for (e.g., "oncomx")

    Returns:
        A string where each line is: table.column (type)
    """
    with open(tables_path, encoding='utf-8') as f:
        data = json.load(f)

    for db in data:
        if db["db_id"] == db_id:
            lines = []
            tables = db["table_names_original"]
            columns = db["column_names_original"]
            types = db["column_types"]

            for idx, (table_id, col_name) in enumerate(columns):
                if col_name != "*":
                    col_type = types[idx]
                    table_name = tables[table_id]
                    lines.append(f"{table_name}.{col_name} ({col_type})")

            return "\n".join(lines)

    raise ValueError(f"Database ID '{db_id}' not found in {tables_path}")
