import re
import json
from typing import List, Dict, Union, Optional
# Classes for database management
class Field:
    def __init__(self, name: str, type_: str, enum_values: Optional[List[str]] = None):
        self.name = name
        self.type = type_
        self.enum_values = enum_values  # Только для типа enum

    def validate(self, value):
        if self.type == "integer":
            return isinstance(value, int)
        elif self.type == "real":
            return isinstance(value, float)
        elif self.type == "char":
            return isinstance(value, str) and len(value) == 1
        elif self.type == "string":
            return isinstance(value, str)
        elif self.type == "email":
            return re.match(r"[^@]+@[^@]+\.[^@]+", value) is not None
        elif self.type == "enum":
            if self.enum_values is None:
                raise ValueError(f"Enum field '{self.name}' does not have defined values.")
            return value in self.enum_values
        else:
            return False



class Row:
    def __init__(self, data: Dict[str, Union[int, float, str]]):
        self.data = data


class Table:
    def __init__(self, name: str, schema: List[Field]):
        self.name = name
        self.schema = {field.name: field for field in schema}
        self.rows = []

    def add_row(self, row: Dict[str, Union[int, float, str]]):
        for field_name, value in row.items():
            if field_name not in self.schema or not self.schema[field_name].validate(value):
                raise ValueError(f"Invalid value for field {field_name}")
        self.rows.append(Row(row))

    def delete_row(self, row_id: int):
        if row_id < 0 or row_id >= len(self.rows):
            raise IndexError("Row ID out of range")
        self.rows.pop(row_id)

    def edit_row(self, row_id: int, new_data: Dict[str, Union[int, float, str]]):
        if row_id < 0 or row_id >= len(self.rows):
            raise IndexError("Row ID out of range")
        self.add_row(new_data)
        self.delete_row(row_id)

    def find_rows(self, pattern: str) -> List[Row]:
        regex = re.compile(pattern)
        return [row for row in self.rows if any(regex.search(str(value)) for value in row.data.values())]


class Database:
    def __init__(self):
        self.tables = {}

    def create_table(self, name: str, schema: List[Field]):
        if name in self.tables:
            raise ValueError("Table already exists")
        self.tables[name] = Table(name, schema)

    def delete_table(self, name: str):
        if name not in self.tables:
            raise ValueError("Table does not exist")
        del self.tables[name]

    def save_to_disk(self, filepath: str):
        data = {
            table_name: {
                "schema": [
                    {
                        "name": field.name,
                        "type": field.type,
                        "enum_values": field.enum_values  # Добавлено для сохранения допустимых значений enum
                    }
                    for field in table.schema.values()
                ],
                "rows": [row.data for row in table.rows]
            }
            for table_name, table in self.tables.items()
        }
        with open(filepath, "w") as f:
            json.dump(data, f)

    def load_from_disk(self, filepath: str):
        with open(filepath, "r") as f:
            data = json.load(f)
        self.tables = {}
        for table_name, table_data in data.items():
            schema = [
                Field(
                    name=field["name"],
                    type_=field["type"],
                    enum_values=field.get("enum_values")  # Восстанавливаем enum_values
                )
                for field in table_data["schema"]
            ]
            table = Table(table_name, schema)
            for row_data in table_data["rows"]:
                table.add_row(row_data)
            self.tables[table_name] = table
