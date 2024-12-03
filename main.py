import tkinter as tk

from database import Database
from db_gui import DatabaseApp

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Database Manager")
    database = Database()
    app = DatabaseApp(root, database)
    root.mainloop()