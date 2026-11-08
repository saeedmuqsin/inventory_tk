import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

from click import confirm

# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ==================== CONTROLLER FUNCTIONS ====================
def fetch_all_products():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_product(name, qty, price, cat):
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO products (name, quantity, price, category) VALUES (?, ?, ?, ?)",
            (name, qty, price, cat)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", f"Product '{name}' already exists.")
        return False
    finally:
        conn.close()

def update_product(p_id, name, qty, price, cat):
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET name=?, quantity=?, price=?, category=? WHERE id=?",
        (name, qty, price, cat, p_id)
    )
    conn.commit()
    conn.close()

def delete_product(p_id):
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (p_id,))
    conn.commit()
    conn.close()

def search_products(query):
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE name LIKE ? OR category LIKE ?", (f"%{query}%", f"%{query}%"))
    rows = cursor.fetchall()
    conn.close()
    return rows

# ==================== GUI APPLICATION ====================
class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management System")
        self.root.geometry("950x600")
        self.root.config(bg="#f4f6f9")
        
        self.selected_item_id = None
        
        # Styles
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), background="#d1d5db")
        self.style.configure("Treeview", rowheight=25, font=("Helvetica", 10))
        self.style.map("Treeview", background=[("selected", "#0284c7")])
        
        self.create_widgets()
        self.refresh_table()

    def create_widgets(self):
        # Title Banner
        title = tk.Label(
            self.root,
            text="📦 Inventory Management Dashboard",
            font=("Helvetica", 18, "bold"),
            bg="#1e293b",
            fg="white",
            padx=12,
            pady=12
        )
        title.pack(fill=tk.X)

        # Main Layout Container
        main_frame = tk.Frame(self.root, bg="#f4f6f9")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # --- LEFT PANEL: Form Inputs ---
        form_frame = tk.LabelFrame(main_frame, text=" Product Details ", font=("Helvetica", 11, "bold"), bg="white", padx=15, pady=15)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        # Inputs Fields
        tk.Label(form_frame, text="Product Name *", font=("Helvetica", 10), bg="white").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_name = ttk.Entry(form_frame, width=25)
        self.ent_name.grid(row=1, column=0, pady=(0, 10), sticky="w")

        tk.Label(form_frame, text="Quantity *", font=("Helvetica", 10), bg="white").grid(row=2, column=0, sticky="w", pady=5)
        self.ent_qty = ttk.Entry(form_frame, width=25)
        self.ent_qty.grid(row=3, column=0, pady=(0, 10), sticky="w")

        tk.Label(form_frame, text="Price ($) *", font=("Helvetica", 10), bg="white").grid(row=4, column=0, sticky="w", pady=5)
        self.ent_price = ttk.Entry(form_frame, width=25)
        self.ent_price.grid(row=5, column=0, pady=(0, 10), sticky="w")

        tk.Label(form_frame, text="Category", font=("Helvetica", 10), bg="white").grid(row=6, column=0, sticky="w", pady=5)
        self.ent_cat = ttk.Entry(form_frame, width=25)
        self.ent_cat.grid(row=7, column=0, pady=(0, 15), sticky="w")

        # Action Buttons
        btn_config = {"width": 18}
        ttk.Button(form_frame, text="➕ Add Item", command=self.handle_add, **btn_config).grid(row=8, column=0, pady=5)
        ttk.Button(form_frame, text="🔄 Update Item", command=self.handle_update, **btn_config).grid(row=9, column=0, pady=5)
        ttk.Button(form_frame, text="❌ Delete Item", command=self.handle_delete, **btn_config).grid(row=10, column=0, pady=5)
        ttk.Button(form_frame, text="🧹 Clear Fields", command=self.clear_entries, **btn_config).grid(row=11, column=0, pady=5)

        # --- RIGHT PANEL: Search & Table View ---
        right_frame = tk.Frame(main_frame, bg="#f4f6f9")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Search Utilities
        search_frame = tk.Frame(right_frame, bg="#f4f6f9")
        search_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(search_frame, text="Search Name/Category:", font=("Helvetica", 10), bg="#f4f6f9").pack(side=tk.LEFT, padx=(0, 5))
        self.ent_search = ttk.Entry(search_frame, width=30)
        self.ent_search.pack(side=tk.LEFT, padx=5)
        self.ent_search.bind("<KeyRelease>", self.handle_search)

        ttk.Button(search_frame, text="Reset", command=self.reset_search).pack(side=tk.LEFT, padx=5)

        # Data Inventory Treeview Grid
        table_frame = tk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "name", "qty", "price", "cat")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Product Name")
        self.tree.heading("qty", text="In Stock")
        self.tree.heading("price", text="Price")
        self.tree.heading("cat", text="Category")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=200, anchor="w")
        self.tree.column("qty", width=90, anchor="center")
        self.tree.column("price", width=90, anchor="e")
        self.tree.column("cat", width=150, anchor="w")

        # Scrollbars
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.handle_row_select)

    # ==================== EVENT HANDLERS ====================
    def validate_inputs(self):
        name = self.ent_name.get().strip()
        qty = self.ent_qty.get().strip()
        price = self.ent_price.get().strip()
        cat = self.ent_cat.get().strip() or "General"

        if not name or not qty or not price:
            messagebox.showwarning("Validation Error", "All fields marked with (*) are strictly required.")
            return None

        try:
            qty = int(qty)
            if qty < 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Validation Error", "Quantity must be a valid positive integer.")
            return None

        try:
            price = float(price)
            if price < 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Validation Error", "Price must be a valid positive decimal number.")
            return None

        return name, qty, price, cat

    def refresh_table(self, rows=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        data = rows if rows is not None else fetch_all_products()
        for row in data:
            # Formats price visualization to standard currency currency string
            formatted_row = (row[0], row[1], row[2], f"${row[3]:.2f}", row[4])
            self.tree.insert("", tk.END, values=formatted_row)

    def handle_row_select(self, _event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        row_data = self.tree.item(selected_items[0])["values"]
        self.selected_item_id = row_data[0]
        
        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, row_data[1])
        
        self.ent_qty.delete(0, tk.END)
        self.ent_qty.insert(0, row_data[2])
        
        self.ent_price.delete(0, tk.END)
        # Stripping dollar sign for numeric re-entry manipulation
        self.ent_price.insert(0, str(row_data[3]).replace("$", ""))
        
        self.ent_cat.delete(0, tk.END)
        self.ent_cat.insert(0, row_data[4])

    def handle_add(self):
        inputs = self.validate_inputs()
        if inputs:
            success = add_product(*inputs)
            if success:
                self.refresh_table()
                self.clear_entries()

    def handle_update(self):
        if not self.selected_item_id:
            messagebox.showwarning("Selection Required", "Please select a product from the table view first.")
            return
        
        inputs = self.validate_inputs()
        if inputs:
            update_product(self.selected_item_id, *inputs)
            self.refresh_table()
            self.clear_entries()
            messagebox.showinfo("Success", "Product record changed smoothly.")

    def handle_delete(self):
        if not self.selected_item_id:
            messagebox.showwarning("Selection Required", "Please highlight the inventory entry to wipe out.")
            return
        
        confirm = messagebox.askyesno("Confirm Delete", "Are you entirely certain you want to wipe out this record?")
        if confirm:
            delete_product(self.selected_item_id)
            self.refresh_table()
            self.clear_entries()

    def handle_search(self, event):
        query = self.ent_search.get().strip()
        results = search_products(query)
        self.refresh_table(results)

    def reset_search(self):
        self.ent_search.delete(0, tk.END)
        self.refresh_table()
        
    def clear_entries(self):
        self.selected_item_id = None
        self.ent_name.delete(0, tk.END)
        self.ent_qty.delete(0, tk.END)
        self.ent_price.delete(0, tk.END)
        self.ent_cat.delete(0, tk.END)
        self.tree.selection_remove(self.tree.selection())



if __name__ == "__main__":
    init_db()
    window = tk.Tk()
    app = InventoryApp(window)
    window.mainloop()
