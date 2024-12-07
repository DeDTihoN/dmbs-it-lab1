import tkinter as tk

from database import Database
from db_gui import ModernDatabaseApp

if __name__ == "__main__":
    # Create the main window
    root = tk.Tk()
    root.title("Modern Database Manager")
    
    # Initialize database and GUI
    database = Database()
    app = ModernDatabaseApp(root, database)
    
    # Start the application event loop
    root.mainloop()