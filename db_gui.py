import re
import json
from typing import List, Dict, Union, Optional
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from tkinter.scrolledtext import ScrolledText

from database import *


class ModernDatabaseApp:
    def __init__(self, root, database: Database):
        self.root = root
        self.database = database
        
        # Configure the root window
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Create main frames
        self.left_frame = ttk.Frame(root)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        self.right_frame = ttk.Frame(root)
        self.right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Style configuration
        style = ttk.Style()
        style.configure('Treeview', rowheight=25)
        style.configure('TButton', padding=5)
        style.configure('Treeview.Heading', font=('Arial', 9))
        
        # Configure tag for header text wrapping
        self.table_view_font = ('Arial', 9)
        style.configure('Treeview.Heading', font=self.table_view_font)
        
        # Table list with label
        ttk.Label(self.left_frame, text="Tables", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        self.table_list = ttk.Treeview(self.left_frame, selectmode='browse', show='tree')
        self.table_list.pack(fill=tk.Y, expand=True)
        self.table_list.bind('<<TreeviewSelect>>', self.on_table_select)
        
        # Buttons frame
        self.buttons_frame = ttk.Frame(self.left_frame)
        self.buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(self.buttons_frame, text="New Table", command=self.show_create_table_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(self.buttons_frame, text="Delete Table", command=self.delete_table).pack(fill=tk.X, pady=2)
        ttk.Button(self.buttons_frame, text="Show Schema", command=self.show_schema).pack(fill=tk.X, pady=2)
        ttk.Button(self.buttons_frame, text="Save Database", command=self.save).pack(fill=tk.X, pady=2)
        ttk.Button(self.buttons_frame, text="Load Database", command=self.load).pack(fill=tk.X, pady=2)
        
        # Right side - table view
        self.table_frame = ttk.Frame(self.right_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Table operations frame
        self.table_ops_frame = ttk.Frame(self.table_frame)
        self.table_ops_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(self.table_ops_frame, text="Add Row", command=self.add_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.table_ops_frame, text="Edit Row", command=self.edit_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.table_ops_frame, text="Delete Row", command=self.delete_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.table_ops_frame, text="Add Column", command=self.add_column).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.table_ops_frame, text="Delete Column", command=self.delete_column).pack(side=tk.LEFT, padx=2)
        
        # Search frame
        self.search_frame = ttk.Frame(self.table_frame)
        self.search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_var.trace('w', self.on_search)
        
        # Table view
        self.table_view = ttk.Treeview(self.table_frame, selectmode='browse')
        self.table_view.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars for table view
        self.vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.table_view.yview)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.hsb = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.table_view.xview)
        self.hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.table_view.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        
        self.current_table = None
        self.refresh_table_list()

    def show_schema(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first")
            return
            
        schema_info = "Table Schema:\n\n"
        for field_name, field in self.current_table.schema.items():
            schema_info += f"Column: {field_name}\n"
            schema_info += f"Type: {field.type}\n"
            if field.type == 'enum':
                schema_info += f"Allowed values: {', '.join(field.enum_values)}\n"
            if field.auto_increment:
                schema_info += "Auto-increment: Yes\n"
            schema_info += "\n"
            
        dialog = SchemaDialog(self.root, "Table Schema", schema_info)
        self.root.wait_window(dialog)

    def edit_row(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first")
            return
            
        selection = self.table_view.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a row to edit")
            return
            
        row_id = self.table_view.index(selection[0])
        row_data = self.current_table.rows[row_id].data
        
        dialog = EditRowDialog(self.root, self.current_table, row_id, row_data)
        self.root.wait_window(dialog)
        self.refresh_table_view()

    def show_create_table_dialog(self):
        dialog = CreateTableDialog(self.root, self.database)
        self.root.wait_window(dialog)
        self.refresh_table_list()

    def delete_table(self):
        selection = self.table_list.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a table to delete")
            return
            
        table_name = self.table_list.item(selection[0])['text']
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the table '{table_name}'?"):
            try:
                self.database.delete_table(table_name)
                self.current_table = None
                self.refresh_table_list()
                self.refresh_table_view()
                messagebox.showinfo("Success", f"Table '{table_name}' deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def on_table_select(self, event):
        selection = self.table_list.selection()
        if not selection:
            return
        table_name = self.table_list.item(selection[0])['text']
        self.current_table = self.database.tables[table_name]
        self.refresh_table_view()

    def refresh_table_list(self):
        self.table_list.delete(*self.table_list.get_children())
        for table_name in self.database.tables.keys():
            self.table_list.insert('', 'end', text=table_name)

    def refresh_table_view(self):
        if not self.current_table:
            self.table_view['columns'] = ()
            for item in self.table_view.get_children():
                self.table_view.delete(item)
            return
            
        # Configure columns
        self.table_view['columns'] = tuple(self.current_table.schema.keys())
        self.table_view['show'] = 'headings'
        
        for col in self.current_table.schema.keys():
            field = self.current_table.schema[col]
            # Create a compact header format
            if field.type == 'enum':
                enum_values = ', '.join(field.enum_values)
                if len(enum_values) > 20:  # Truncate long enum lists
                    enum_values = enum_values[:17] + "..."
                header_text = f"{col} [{field.type}: {enum_values}]"
            else:
                header_text = f"{col} [{field.type}]"
                
            self.table_view.heading(col, text=header_text)
            # Set minimum width based on content and type
            min_width = max(len(header_text) * 8, 100)
            self.table_view.column(col, width=min_width, minwidth=min_width)
        
        # Clear existing items
        for item in self.table_view.get_children():
            self.table_view.delete(item)
        
        # Add rows
        for row in self.current_table.rows:
            values = [str(row.data.get(field, '')) for field in self.current_table.schema.keys()]
            self.table_view.insert('', 'end', values=values)

    def add_row(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first")
            return
        dialog = AddRowDialog(self.root, self.current_table)
        self.root.wait_window(dialog)
        self.refresh_table_view()

    def delete_row(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first")
            return
        selection = self.table_view.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a row to delete")
            return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected row?"):
            row_id = self.table_view.index(selection[0])
            try:
                self.current_table.delete_row(row_id)
                self.refresh_table_view()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def add_column(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first")
            return
        dialog = AddColumnDialog(self.root, self.current_table)
        self.root.wait_window(dialog)
        self.refresh_table_view()

    def delete_column(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first")
            return
        dialog = DeleteColumnDialog(self.root, self.current_table)
        self.root.wait_window(dialog)
        self.refresh_table_view()

    def on_search(self, *args):
        if not self.current_table or not self.search_var.get():
            self.refresh_table_view()
            return
            
        search_text = self.search_var.get()
        matching_rows = self.current_table.find_rows(search_text)
        
        # Clear existing items
        for item in self.table_view.get_children():
            self.table_view.delete(item)
        
        # Add matching rows
        for row in matching_rows:
            values = [str(row.data.get(field, '')) for field in self.current_table.schema.keys()]
            self.table_view.insert('', 'end', values=values)

    def save(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Save Database"
        )
        if filepath:
            try:
                self.database.save_to_disk(filepath)
                messagebox.showinfo("Success", "Database saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save database: {str(e)}")

    def load(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            title="Load Database"
        )
        if filepath:
            try:
                self.database.load_from_disk(filepath)
                self.refresh_table_list()
                self.current_table = None
                self.refresh_table_view()
                messagebox.showinfo("Success", "Database loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load database: {str(e)}")


class CreateTableDialog(tk.Toplevel):
    def __init__(self, parent, database):
        super().__init__(parent)
        self.database = database
        self.title("Create New Table")
        self.geometry("600x400")
        
        # Table name frame
        name_frame = ttk.Frame(self)
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(name_frame, text="Table Name:").pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(name_frame)
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Columns frame
        columns_frame = ttk.Frame(self)
        columns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(columns_frame, text="Columns:").pack(anchor=tk.W)
        
        # Columns list
        self.columns_text = ScrolledText(columns_frame, height=10)
        self.columns_text.pack(fill=tk.BOTH, expand=True)
        self.columns_text.insert('1.0', 
            "# Enter one column per line in the format: name:type\n"
            "# Available types: integer, real, char, string, email, enum\n"
            "# For enum, use: name:enum:value1,value2,value3\n"
            "# Example:\n"
            "# name:string\n"
            "# age:integer\n"
            "# status:enum:active,inactive,pending\n"
        )
        
        # Buttons
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Create", command=self.create_table).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def create_table(self):
        table_name = self.name_entry.get().strip()
        if not table_name:
            messagebox.showerror("Error", "Table name is required")
            return
            
        # Parse columns
        columns_text = self.columns_text.get('1.0', tk.END).strip()
        schema = []
        
        for line in columns_text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            try:
                if ':enum:' in line:
                    name, _, values = line.split(':')
                    schema.append(Field(name.strip(), 'enum', enum_values=values.split(',')))
                else:
                    name, type_ = line.split(':')
                    schema.append(Field(name.strip(), type_.strip()))
            except Exception as e:
                messagebox.showerror("Error", f"Invalid column definition: {line}\n{str(e)}")
                return
        
        try:
            self.database.create_table(table_name, schema)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


class AddRowDialog(tk.Toplevel):
    def __init__(self, parent, table):
        super().__init__(parent)
        self.table = table
        self.title("Add New Row")
        self.geometry("400x300")
        
        # Create entries for each field
        self.entries = {}
        for field_name, field in table.schema.items():
            if field.auto_increment:
                continue
            
            frame = ttk.Frame(self)
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(frame, text=f"{field_name}:").pack(side=tk.LEFT)
            
            if field.type == 'enum':
                var = tk.StringVar()
                entry = ttk.Combobox(frame, textvariable=var, values=field.enum_values)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                self.entries[field_name] = var
            else:
                var = tk.StringVar()
                entry = ttk.Entry(frame, textvariable=var)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                self.entries[field_name] = var
        
        # Buttons
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Add", command=self.add_row).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def add_row(self):
        row_data = {}
        for field_name, var in self.entries.items():
            value = var.get().strip()
            field = self.table.schema[field_name]
            
            try:
                if field.type == 'integer':
                    value = int(value)
                elif field.type == 'real':
                    value = float(value)
                row_data[field_name] = value
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for field {field_name}")
                return
        
        try:
            self.table.add_row(row_data)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


class AddColumnDialog(tk.Toplevel):
    def __init__(self, parent, table):
        super().__init__(parent)
        self.table = table
        self.title("Add New Column")
        self.geometry("400x200")
        
        # Column name
        name_frame = ttk.Frame(self)
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(name_frame, text="Column Name:").pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Column type
        type_frame = ttk.Frame(self)
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(type_frame, text="Column Type:").pack(side=tk.LEFT)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(type_frame, textvariable=self.type_var)
        self.type_combo['values'] = ('integer', 'real', 'char', 'string', 'email', 'enum')
        self.type_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.type_combo.bind('<<ComboboxSelected>>', self.on_type_select)
        
        # Enum values frame (initially hidden)
        self.enum_frame = ttk.Frame(self)
        ttk.Label(self.enum_frame, text="Enum Values (comma-separated):").pack(side=tk.LEFT)
        self.enum_var = tk.StringVar()
        ttk.Entry(self.enum_frame, textvariable=self.enum_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Buttons
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Add", command=self.add_column).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def on_type_select(self, event):
        if self.type_var.get() == 'enum':
            self.enum_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.enum_frame.pack_forget()

    def add_column(self):
        name = self.name_var.get().strip()
        type_ = self.type_var.get()
        
        if not name or not type_:
            messagebox.showerror("Error", "Name and type are required")
            return
        
        try:
            if type_ == 'enum':
                enum_values = [v.strip() for v in self.enum_var.get().split(',') if v.strip()]
                if not enum_values:
                    messagebox.showerror("Error", "Enum values are required")
                    return
                field = Field(name, type_, enum_values=enum_values)
            else:
                field = Field(name, type_)
            
            self.table.add_column(field)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


class DeleteColumnDialog(tk.Toplevel):
    def __init__(self, parent, table):
        super().__init__(parent)
        self.table = table
        self.title("Delete Column")
        self.geometry("300x150")
        
        # Column selection
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame, text="Select Column:").pack(side=tk.LEFT)
        self.column_var = tk.StringVar()
        columns = [name for name in table.schema.keys() if name != 'id']
        self.column_combo = ttk.Combobox(frame, textvariable=self.column_var, values=columns)
        self.column_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Buttons
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Delete", command=self.delete_column).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def delete_column(self):
        column = self.column_var.get()
        if not column:
            messagebox.showerror("Error", "Please select a column")
            return
            
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the column '{column}'?"):
            try:
                self.table.delete_column(column)
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))


class EditRowDialog(tk.Toplevel):
    def __init__(self, parent, table, row_id, row_data):
        super().__init__(parent)
        self.table = table
        self.row_id = row_id
        self.title("Edit Row")
        self.geometry("400x300")
        
        # Create entries for each field
        self.entries = {}
        for field_name, field in table.schema.items():
            if field.auto_increment:
                continue
            
            frame = ttk.Frame(self)
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(frame, text=f"{field_name} ({field.type}):").pack(side=tk.LEFT)
            
            if field.type == 'enum':
                var = tk.StringVar(value=row_data.get(field_name, ''))
                entry = ttk.Combobox(frame, textvariable=var, values=field.enum_values)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                self.entries[field_name] = var
            else:
                var = tk.StringVar(value=row_data.get(field_name, ''))
                entry = ttk.Entry(frame, textvariable=var)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                self.entries[field_name] = var
        
        # Buttons
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Save", command=self.save_row).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def save_row(self):
        row_data = {}
        for field_name, var in self.entries.items():
            value = var.get().strip()
            field = self.table.schema[field_name]
            
            try:
                if field.type == 'integer':
                    value = int(value)
                elif field.type == 'real':
                    value = float(value)
                row_data[field_name] = value
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for field {field_name}")
                return
        
        try:
            self.table.edit_row(self.row_id, row_data)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))


class SchemaDialog(tk.Toplevel):
    def __init__(self, parent, title, text):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x400")
        
        # Create text widget
        text_widget = ScrolledText(self, wrap=tk.WORD, width=40, height=20)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Insert text
        text_widget.insert('1.0', text)
        text_widget.configure(state='disabled')
        
        # Close button
        ttk.Button(self, text="Close", command=self.destroy).pack(pady=5)