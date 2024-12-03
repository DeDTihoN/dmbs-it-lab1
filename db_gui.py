import re
import json
from typing import List, Dict, Union, Optional
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog

from database import *


class DatabaseApp:
    def __init__(self, root, database: Database):
        self.root = root
        self.database = database

        # Main window layout
        self.table_list = tk.Listbox(root, selectmode=tk.SINGLE)
        self.table_list.pack(side=tk.LEFT, fill=tk.Y)

        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.add_table_btn = tk.Button(self.buttons_frame, text="Add Table", command=self.add_table)
        self.add_table_btn.pack()

        self.del_table_btn = tk.Button(self.buttons_frame, text="Delete Table", command=self.delete_table)
        self.del_table_btn.pack()

        self.open_table_btn = tk.Button(self.buttons_frame, text="Open Table", command=self.open_table)
        self.open_table_btn.pack()

        self.save_btn = tk.Button(self.buttons_frame, text="Save", command=self.save)
        self.save_btn.pack()

        self.load_btn = tk.Button(self.buttons_frame, text="Load", command=self.load)
        self.load_btn.pack()

        self.refresh_table_list()

    def add_table(self):
        table_name = simpledialog.askstring("Table Name", "Enter table name:")
        if not table_name:
            return
        schema_fields = simpledialog.askstring("Schema", "Enter fields (name:type,name:type):")
        if not schema_fields:
            return
        schema = []
        for field_def in schema_fields.split(","):
            name, type_ = field_def.split(":")
            name, type_ = name.strip(), type_.strip()
            if type_ == "enum":
                enum_values = simpledialog.askstring("Enum Values", f"Enter allowed values for enum field '{name}' (comma-separated):")
                if not enum_values:
                    messagebox.showerror("Error", f"Enum field '{name}' requires values.")
                    return
                schema.append(Field(name, type_, enum_values=enum_values.split(",")))
            else:
                schema.append(Field(name, type_))
        try:
            self.database.create_table(table_name, schema)
            self.refresh_table_list()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def delete_table(self):
        selected = self.table_list.curselection()
        if not selected:
            return
        table_name = self.table_list.get(selected[0])
        try:
            self.database.delete_table(table_name)
            self.refresh_table_list()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def open_table(self):
        selected = self.table_list.curselection()
        if not selected:
            return
        table_name = self.table_list.get(selected[0])
        table = self.database.tables[table_name]
        TableManager(self.root, table)

    def save(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return
        self.database.save_to_disk(filepath)

    def load(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return
        self.database.load_from_disk(filepath)
        self.refresh_table_list()

    def refresh_table_list(self):
        self.table_list.delete(0, tk.END)
        for table_name in self.database.tables.keys():
            self.table_list.insert(tk.END, table_name)


class TableManager:
    def __init__(self, parent, table):
        self.table = table
        self.window = tk.Toplevel(parent)
        self.window.title(f"Table: {self.table.name}")

        # Header Frame
        self.header_frame = tk.Frame(self.window)
        self.header_frame.pack(fill=tk.X)

        # Displaying headers
        for field in self.table.schema.values():
            label = tk.Label(self.header_frame, text=field.name, borderwidth=1, relief="solid", padx=5, pady=5)
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Content Frame
        self.content_frame = tk.Frame(self.window)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Listbox for rows
        self.rows_list = tk.Listbox(self.content_frame)
        self.rows_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for rows
        self.scrollbar = tk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.rows_list.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rows_list.config(yscrollcommand=self.scrollbar.set)

        # Buttons Frame
        self.buttons_frame = tk.Frame(self.window)
        self.buttons_frame.pack(fill=tk.X)

        self.add_row_btn = tk.Button(self.buttons_frame, text="Add Row", command=self.add_row)
        self.add_row_btn.pack(side=tk.LEFT)

        self.del_row_btn = tk.Button(self.buttons_frame, text="Delete Row", command=self.delete_row)
        self.del_row_btn.pack(side=tk.LEFT)

        self.search_btn = tk.Button(self.buttons_frame, text="Search", command=self.search_row)
        self.search_btn.pack(side=tk.LEFT)

        self.refresh_rows()

    def add_row(self):
        row_data = simpledialog.askstring("Add Row", "Enter row data (field=value,field=value):")
        if not row_data:
            return
        row = {}
        for item in row_data.split(","):
            field, value = item.split("=")
            field = field.strip()
            if field not in self.table.schema:
                messagebox.showerror("Error", f"Field '{field}' not in schema.")
                return
            field_obj = self.table.schema[field]
            if field_obj.type == "enum" and value not in field_obj.enum_values:
                messagebox.showerror("Error", f"Invalid value '{value}' for enum field '{field}'. Allowed values: {', '.join(field_obj.enum_values)}.")
                return
            value = self.cast_value(field_obj.type, value.strip(), field=field_obj)
            if value is None:
                messagebox.showerror("Error", f"Invalid value for field '{field}'.")
                return
            row[field] = value
        try:
            self.table.add_row(row)
            self.refresh_rows()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def delete_row(self):
        selected = self.rows_list.curselection()
        if not selected:
            return
        row_id = selected[0]
        try:
            self.table.delete_row(row_id)
            self.refresh_rows()
        except IndexError as e:
            messagebox.showerror("Error", str(e))

    def search_row(self):
        field_name = simpledialog.askstring("Search", "Enter field name for search:")
        if not field_name or field_name not in self.table.schema:
            messagebox.showerror("Error", "Invalid field name.")
            return
        search_value = simpledialog.askstring("Search", f"Enter value to search in '{field_name}':")
        if not search_value:
            return

        self.rows_list.delete(0, tk.END)
        regex = re.compile(re.escape(search_value), re.IGNORECASE)
        for row in self.table.rows:
            if regex.search(str(row.data.get(field_name, ""))):
                row_values = [str(row.data.get(field, "")) for field in self.table.schema.keys()]
                self.rows_list.insert(tk.END, " | ".join(row_values))

    def refresh_rows(self):
        self.rows_list.delete(0, tk.END)
        for row in self.table.rows:
            row_values = [str(row.data.get(field_name, "")) for field_name in self.table.schema.keys()]
            self.rows_list.insert(tk.END, " | ".join(row_values))

    def cast_value(self, type_, value, field=None):
        try:
            if type_ == "integer":
                return int(value)
            elif type_ == "real":
                return float(value)
            elif type_ in ["char", "string", "email"]:
                return value
            elif type_ == "enum":
                if field is None or not field.enum_values:
                    raise ValueError("Enum field requires a defined set of valid values.")
                if value not in field.enum_values:
                    raise ValueError(
                        f"Invalid value '{value}' for enum field. Allowed values are: {', '.join(field.enum_values)}.")
                return value
            else:
                return None
        except ValueError:
            return None