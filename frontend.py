import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from typing import List, Dict, Optional
import json

# Mock data storage (replace with actual MongoDB later)
class DataStore:
    def __init__(self):
        self.brokers = []
        self.saudas = []
        self.lots = []
        self.products = []
        self._init_sample_data()
    
    def _init_sample_data(self):
        # Sample broker
        self.brokers.append({
            '_id': '1',
            'name': 'Ramesh Trading Co.',
            'party_name': 'Sharma Exports',
            'sauda_ids': ['1'],
            'created_at': datetime.now()
        })
        
        # Sample sauda
        self.saudas.append({
            '_id': '1',
            'name': 'Deal 2025-01',
            'date': datetime.now(),
            'total_lots': 2,
            'rate': 2450.50,
            'status': 'Ready for pickup',
            'list_of_lot_id': ['1'],
            'created_at': datetime.now()
        })
        
        # Sample lot
        self.lots.append({
            '_id': '1',
            'sauda_id': '1',
            'rice_lot_no': 'RICE-2025-001',
            'rice_agreement': 'AGR-4567',
            'rice_type': 'Basmati',
            'qtl': 150.25,
            'rice_bags_quantity': 300,
            'net_rice_bought': 148.0,
            'created_at': datetime.now()
        })

db = DataStore()

class TradingDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Management System")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f0f0')
        
        # Main container
        main_container = tk.Frame(root, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left sidebar
        self.create_sidebar(main_container)
        
        # Right content area
        self.content_frame = tk.Frame(main_container, bg='white', relief=tk.RAISED, bd=2)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Show brokers by default
        self.show_brokers()
    
    def create_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg='#2c3e50', width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Title
        title = tk.Label(sidebar, text="Trading System", font=('Arial', 16, 'bold'),
                        bg='#2c3e50', fg='white', pady=20)
        title.pack(fill=tk.X)
        
        # Navigation buttons
        buttons = [
            ("Brokers", self.show_brokers),
            ("Saudas (Deals)", self.show_saudas),
            ("Lots", self.show_lots),
            ("Products", self.show_products)
        ]
        
        for text, command in buttons:
            btn = tk.Button(sidebar, text=text, command=command,
                          bg='#34495e', fg='white', font=('Arial', 11),
                          bd=0, pady=15, activebackground='#1abc9c',
                          activeforeground='white', cursor='hand2')
            btn.pack(fill=tk.X, padx=10, pady=5)
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    # BROKERS SECTION
    def show_brokers(self):
        self.clear_content()
        
        # Header
        header = tk.Frame(self.content_frame, bg='white')
        header.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(header, text="Brokers Management", font=('Arial', 20, 'bold'),
                bg='white').pack(side=tk.LEFT)
        
        tk.Button(header, text="+ Add Broker", command=self.add_broker_form,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 padx=20, pady=8, cursor='hand2').pack(side=tk.RIGHT)
        
        # Search frame
        search_frame = tk.Frame(self.content_frame, bg='white')
        search_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        tk.Label(search_frame, text="Search:", bg='white', font=('Arial', 10)).pack(side=tk.LEFT)
        search_entry = tk.Entry(search_frame, font=('Arial', 10), width=30)
        search_entry.pack(side=tk.LEFT, padx=10)
        tk.Button(search_frame, text="Search", bg='#3498db', fg='white',
                 command=lambda: self.search_brokers(search_entry.get())).pack(side=tk.LEFT)
        
        # Table frame
        table_frame = tk.Frame(self.content_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Treeview
        columns = ('ID', 'Name', 'Party Name', 'Saudas Count', 'Created At')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate data
        for broker in db.brokers:
            tree.insert('', tk.END, values=(
                broker['_id'],
                broker['name'],
                broker['party_name'],
                len(broker['sauda_ids']),
                broker['created_at'].strftime('%Y-%m-%d')
            ))
        
        # Double click to view details
        tree.bind('<Double-1>', lambda e: self.view_broker_details(tree))
    
    def add_broker_form(self):
        form_window = tk.Toplevel(self.root)
        form_window.title("Add New Broker")
        form_window.geometry("500x300")
        form_window.configure(bg='white')
        
        tk.Label(form_window, text="Add New Broker", font=('Arial', 16, 'bold'),
                bg='white').pack(pady=20)
        
        fields_frame = tk.Frame(form_window, bg='white')
        fields_frame.pack(padx=40, pady=20, fill=tk.BOTH, expand=True)
        
        entries = {}
        fields = [('Name:', 'name'), ('Party Name:', 'party_name')]
        
        for i, (label, key) in enumerate(fields):
            tk.Label(fields_frame, text=label, bg='white', font=('Arial', 11)).grid(
                row=i, column=0, sticky='w', pady=10)
            entry = tk.Entry(fields_frame, font=('Arial', 11), width=30)
            entry.grid(row=i, column=1, pady=10, padx=10)
            entries[key] = entry
        
        def save_broker():
            new_broker = {
                '_id': str(len(db.brokers) + 1),
                'name': entries['name'].get(),
                'party_name': entries['party_name'].get(),
                'sauda_ids': [],
                'created_at': datetime.now()
            }
            db.brokers.append(new_broker)
            messagebox.showinfo("Success", "Broker added successfully!")
            form_window.destroy()
            self.show_brokers()
        
        tk.Button(fields_frame, text="Save", command=save_broker, bg='#27ae60',
                 fg='white', font=('Arial', 11, 'bold'), padx=30, pady=8).grid(
                     row=len(fields), column=1, pady=20, sticky='e')
    
    def view_broker_details(self, tree):
        selected = tree.selection()
        if not selected:
            return
        
        values = tree.item(selected[0])['values']
        broker_id = values[0]
        broker = next((b for b in db.brokers if b['_id'] == broker_id), None)
        
        if not broker:
            return
        
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Broker Details - {broker['name']}")
        detail_window.geometry("600x500")
        detail_window.configure(bg='white')
        
        # Details
        details_frame = tk.Frame(detail_window, bg='white')
        details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(details_frame, text=f"Broker: {broker['name']}", 
                font=('Arial', 16, 'bold'), bg='white').pack(anchor='w', pady=5)
        tk.Label(details_frame, text=f"Party: {broker['party_name']}", 
                font=('Arial', 12), bg='white').pack(anchor='w', pady=5)
        
        tk.Label(details_frame, text="\nLinked Saudas:", font=('Arial', 12, 'bold'),
                bg='white').pack(anchor='w', pady=10)
        
        # Show linked saudas
        for sauda_id in broker['sauda_ids']:
            sauda = next((s for s in db.saudas if s['_id'] == sauda_id), None)
            if sauda:
                tk.Label(details_frame, text=f"• {sauda['name']} - Status: {sauda['status']}", 
                        font=('Arial', 10), bg='white').pack(anchor='w', padx=20)
    
    def search_brokers(self, query):
        # Implement search functionality
        messagebox.showinfo("Search", f"Searching for: {query}")
    
    # SAUDAS SECTION
    def show_saudas(self):
        self.clear_content()
        
        # Header
        header = tk.Frame(self.content_frame, bg='white')
        header.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(header, text="Saudas (Deals) Management", font=('Arial', 20, 'bold'),
                bg='white').pack(side=tk.LEFT)
        
        tk.Button(header, text="+ Add Sauda", command=self.add_sauda_form,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 padx=20, pady=8, cursor='hand2').pack(side=tk.RIGHT)
        
        # Filter frame
        filter_frame = tk.Frame(self.content_frame, bg='white')
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        tk.Label(filter_frame, text="Status Filter:", bg='white', font=('Arial', 10)).pack(side=tk.LEFT)
        status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(filter_frame, textvariable=status_var, 
                                    values=["All", "Ready for pickup", "In transport", "Shipped"],
                                    state='readonly', width=20)
        status_combo.pack(side=tk.LEFT, padx=10)
        tk.Button(filter_frame, text="Filter", bg='#3498db', fg='white',
                 command=lambda: self.filter_saudas(status_var.get())).pack(side=tk.LEFT)
        
        # Table frame
        table_frame = tk.Frame(self.content_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Treeview
        columns = ('ID', 'Name', 'Date', 'Rate', 'Total Lots', 'Status', 'Lots Count')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate data
        for sauda in db.saudas:
            tree.insert('', tk.END, values=(
                sauda['_id'],
                sauda['name'],
                sauda['date'].strftime('%Y-%m-%d'),
                f"₹{sauda['rate']}",
                sauda['total_lots'],
                sauda['status'],
                len(sauda['list_of_lot_id'])
            ))
        
        # Double click to view details
        tree.bind('<Double-1>', lambda e: self.view_sauda_details(tree))
    
    def add_sauda_form(self):
        form_window = tk.Toplevel(self.root)
        form_window.title("Add New Sauda")
        form_window.geometry("500x400")
        form_window.configure(bg='white')
        
        tk.Label(form_window, text="Add New Sauda", font=('Arial', 16, 'bold'),
                bg='white').pack(pady=20)
        
        fields_frame = tk.Frame(form_window, bg='white')
        fields_frame.pack(padx=40, pady=20, fill=tk.BOTH, expand=True)
        
        entries = {}
        
        # Name
        tk.Label(fields_frame, text="Name:", bg='white', font=('Arial', 11)).grid(
            row=0, column=0, sticky='w', pady=10)
        entries['name'] = tk.Entry(fields_frame, font=('Arial', 11), width=30)
        entries['name'].grid(row=0, column=1, pady=10, padx=10)
        
        # Total Lots
        tk.Label(fields_frame, text="Total Lots:", bg='white', font=('Arial', 11)).grid(
            row=1, column=0, sticky='w', pady=10)
        entries['total_lots'] = tk.Entry(fields_frame, font=('Arial', 11), width=30)
        entries['total_lots'].grid(row=1, column=1, pady=10, padx=10)
        
        # Rate
        tk.Label(fields_frame, text="Rate (₹/qtl):", bg='white', font=('Arial', 11)).grid(
            row=2, column=0, sticky='w', pady=10)
        entries['rate'] = tk.Entry(fields_frame, font=('Arial', 11), width=30)
        entries['rate'].grid(row=2, column=1, pady=10, padx=10)
        
        # Status
        tk.Label(fields_frame, text="Status:", bg='white', font=('Arial', 11)).grid(
            row=3, column=0, sticky='w', pady=10)
        status_var = tk.StringVar(value="Ready for pickup")
        status_combo = ttk.Combobox(fields_frame, textvariable=status_var,
                                    values=["Ready for pickup", "In transport", "Shipped"],
                                    state='readonly', font=('Arial', 11), width=28)
        status_combo.grid(row=3, column=1, pady=10, padx=10)
        
        def save_sauda():
            try:
                new_sauda = {
                    '_id': str(len(db.saudas) + 1),
                    'name': entries['name'].get(),
                    'date': datetime.now(),
                    'total_lots': int(entries['total_lots'].get()),
                    'rate': float(entries['rate'].get()),
                    'status': status_var.get(),
                    'list_of_lot_id': [],
                    'created_at': datetime.now()
                }
                db.saudas.append(new_sauda)
                messagebox.showinfo("Success", "Sauda added successfully!")
                form_window.destroy()
                self.show_saudas()
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for lots and rate")
        
        tk.Button(fields_frame, text="Save", command=save_sauda, bg='#27ae60',
                 fg='white', font=('Arial', 11, 'bold'), padx=30, pady=8).grid(
                     row=4, column=1, pady=20, sticky='e')
    
    def view_sauda_details(self, tree):
        selected = tree.selection()
        if not selected:
            return
        
        values = tree.item(selected[0])['values']
        sauda_id = values[0]
        sauda = next((s for s in db.saudas if s['_id'] == sauda_id), None)
        
        if not sauda:
            return
        
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Sauda Details - {sauda['name']}")
        detail_window.geometry("700x600")
        detail_window.configure(bg='white')
        
        # Details
        details_frame = tk.Frame(detail_window, bg='white')
        details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(details_frame, text=f"Sauda: {sauda['name']}", 
                font=('Arial', 16, 'bold'), bg='white').pack(anchor='w', pady=5)
        tk.Label(details_frame, text=f"Date: {sauda['date'].strftime('%Y-%m-%d')}", 
                font=('Arial', 12), bg='white').pack(anchor='w', pady=2)
        tk.Label(details_frame, text=f"Rate: ₹{sauda['rate']}/qtl", 
                font=('Arial', 12), bg='white').pack(anchor='w', pady=2)
        tk.Label(details_frame, text=f"Total Lots: {sauda['total_lots']}", 
                font=('Arial', 12), bg='white').pack(anchor='w', pady=2)
        
        # Status change
        status_frame = tk.Frame(details_frame, bg='white')
        status_frame.pack(anchor='w', pady=10)
        tk.Label(status_frame, text="Status:", font=('Arial', 12, 'bold'), 
                bg='white').pack(side=tk.LEFT)
        status_var = tk.StringVar(value=sauda['status'])
        status_combo = ttk.Combobox(status_frame, textvariable=status_var,
                                    values=["Ready for pickup", "In transport", "Shipped"],
                                    state='readonly', width=20)
        status_combo.pack(side=tk.LEFT, padx=10)
        
        def update_status():
            sauda['status'] = status_var.get()
            messagebox.showinfo("Success", "Status updated!")
            self.show_saudas()
            detail_window.destroy()
        
        tk.Button(status_frame, text="Update", command=update_status, bg='#3498db',
                 fg='white').pack(side=tk.LEFT)
        
        tk.Label(details_frame, text="\nLinked Lots:", font=('Arial', 12, 'bold'),
                bg='white').pack(anchor='w', pady=10)
        
        # Show linked lots
        for lot_id in sauda['list_of_lot_id']:
            lot = next((l for l in db.lots if l['_id'] == lot_id), None)
            if lot:
                tk.Label(details_frame, 
                        text=f"• {lot['rice_lot_no']} - {lot['rice_type']} ({lot['qtl']} qtl)", 
                        font=('Arial', 10), bg='white').pack(anchor='w', padx=20)
    
    def filter_saudas(self, status):
        messagebox.showinfo("Filter", f"Filtering by: {status}")
    
    # LOTS SECTION
    def show_lots(self):
        self.clear_content()
        
        # Header
        header = tk.Frame(self.content_frame, bg='white')
        header.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(header, text="Lots Management", font=('Arial', 20, 'bold'),
                bg='white').pack(side=tk.LEFT)
        
        tk.Button(header, text="+ Add Lot", command=self.add_lot_form,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 padx=20, pady=8, cursor='hand2').pack(side=tk.RIGHT)
        
        # Info frame (top section with key fields)
        info_frame = tk.LabelFrame(self.content_frame, text="Summary", bg='#ecf0f1',
                                   font=('Arial', 11, 'bold'), padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        total_lots = len(db.lots)
        total_qtl = sum(lot.get('qtl', 0) for lot in db.lots)
        
        tk.Label(info_frame, text=f"Total Lots: {total_lots}", bg='#ecf0f1',
                font=('Arial', 11)).pack(side=tk.LEFT, padx=20)
        tk.Label(info_frame, text=f"Total Quantity: {total_qtl:.2f} qtl", bg='#ecf0f1',
                font=('Arial', 11)).pack(side=tk.LEFT, padx=20)
        
        # Table frame
        table_frame = tk.Frame(self.content_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Treeview
        columns = ('Lot No', 'Rice Type', 'Agreement', 'Quantity (qtl)', 'Bags', 'Net Rice', 'FRK')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate data
        for lot in db.lots:
            tree.insert('', tk.END, values=(
                lot.get('rice_lot_no', 'N/A'),
                lot.get('rice_type', 'N/A'),
                lot.get('rice_agreement', 'N/A'),
                f"{lot.get('qtl', 0):.2f}",
                lot.get('rice_bags_quantity', 0),
                f"{lot.get('net_rice_bought', 0):.2f}",
                'Yes' if lot.get('frk', False) else 'No'
            ))
        
        # Double click to view details
        tree.bind('<Double-1>', lambda e: self.view_lot_details(tree))
    
    def add_lot_form(self):
        form_window = tk.Toplevel(self.root)
        form_window.title("Add New Lot")
        form_window.geometry("600x700")
        form_window.configure(bg='white')
        
        # Create scrollable frame
        canvas = tk.Canvas(form_window, bg='white')
        scrollbar = ttk.Scrollbar(form_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        tk.Label(scrollable_frame, text="Add New Lot", font=('Arial', 16, 'bold'),
                bg='white').pack(pady=20)
        
        fields_frame = tk.Frame(scrollable_frame, bg='white')
        fields_frame.pack(padx=40, pady=20, fill=tk.BOTH, expand=True)
        
        entries = {}
        row = 0
        
        # Sauda selection
        tk.Label(fields_frame, text="Sauda:", bg='white', font=('Arial', 11)).grid(
            row=row, column=0, sticky='w', pady=10)
        sauda_var = tk.StringVar()
        sauda_names = [f"{s['_id']}: {s['name']}" for s in db.saudas]
        sauda_combo = ttk.Combobox(fields_frame, textvariable=sauda_var,
                                   values=sauda_names, width=28)
        sauda_combo.grid(row=row, column=1, pady=10, padx=10)
        entries['sauda'] = sauda_var
        row += 1
        
        # Basic fields
        basic_fields = [
            ('Lot Number:', 'rice_lot_no'),
            ('Agreement:', 'rice_agreement'),
            ('Rice Type:', 'rice_type'),
            ('Quantity (qtl):', 'qtl'),
            ('Bags Quantity:', 'rice_bags_quantity'),
            ('Net Rice Bought:', 'net_rice_bought'),
            ('Moisture Cut:', 'moisture_cut'),
        ]
        
        for label, key in basic_fields:
            tk.Label(fields_frame, text=label, bg='white', font=('Arial', 11)).grid(
                row=row, column=0, sticky='w', pady=10)
            entry = tk.Entry(fields_frame, font=('Arial', 11), width=30)
            entry.grid(row=row, column=1, pady=10, padx=10)
            entries[key] = entry
            row += 1
        
        # FRK checkbox
        tk.Label(fields_frame, text="FRK:", bg='white', font=('Arial', 11)).grid(
            row=row, column=0, sticky='w', pady=10)
        frk_var = tk.BooleanVar()
        frk_check = tk.Checkbutton(fields_frame, variable=frk_var, bg='white')
        frk_check.grid(row=row, column=1, sticky='w', pady=10, padx=10)
        entries['frk'] = frk_var
        row += 1
        
        def save_lot():
            try:
                sauda_id = sauda_var.get().split(':')[0] if sauda_var.get() else None
                
                new_lot = {
                    '_id': str(len(db.lots) + 1),
                    'sauda_id': sauda_id,
                    'rice_lot_no': entries['rice_lot_no'].get(),
                    'rice_agreement': entries['rice_agreement'].get(),
                    'rice_type': entries['rice_type'].get(),
                    'qtl': float(entries['qtl'].get()) if entries['qtl'].get() else 0,
                    'rice_bags_quantity': int(entries['rice_bags_quantity'].get()) if entries['rice_bags_quantity'].get() else 0,
                    'net_rice_bought': float(entries['net_rice_bought'].get()) if entries['net_rice_bought'].get() else 0,
                    'moisture_cut': float(entries['moisture_cut'].get()) if entries['moisture_cut'].get() else 0,
                    'frk': frk_var.get(),
                    'created_at': datetime.now()
                }
                db.lots.append(new_lot)
                
                # Update sauda's lot list
                if sauda_id:
                    sauda = next((s for s in db.saudas if s['_id'] == sauda_id), None)
                    if sauda:
                        sauda['list_of_lot_id'].append(new_lot['_id'])
                
                messagebox.showinfo("Success", "Lot added successfully!")
                form_window.destroy()
                self.show_lots()
            except ValueError as e:
                messagebox.showerror("Error", f"Please enter valid values: {str(e)}")
        
        tk.Button(fields_frame, text="Save", command=save_lot, bg='#27ae60',
                 fg='white', font=('Arial', 11, 'bold'), padx=30, pady=8).grid(
                     row=row, column=1, pady=20, sticky='e')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def view_lot_details(self, tree):
        selected = tree.selection()
        if not selected:
            return
        
        values = tree.item(selected[0])['values']
        lot_no = values[0]
        lot = next((l for l in db.lots if l.get('rice_lot_no') == lot_no), None)
        
        if not lot:
            return
        
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Lot Details - {lot['rice_lot_no']}")
        detail_window.geometry("600x600")
        detail_window.configure(bg='white')
        
        # Scrollable frame
        canvas = tk.Canvas(detail_window, bg='white')
        scrollbar = ttk.Scrollbar(detail_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        details_frame = tk.Frame(scrollable_frame, bg='white')
        details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(details_frame, text=f"Lot: {lot['rice_lot_no']}", 
                font=('Arial', 16, 'bold'), bg='white').pack(anchor='w', pady=5)
        
        # Display all fields
        fields = [
            ('Rice Type:', lot.get('rice_type', 'N/A')),
            ('Agreement:', lot.get('rice_agreement', 'N/A')),
            ('Quantity:', f"{lot.get('qtl', 0):.2f} qtl"),
            ('Bags:', lot.get('rice_bags_quantity', 0)),
            ('Net Rice Bought:', f"{lot.get('net_rice_bought', 0):.2f} qtl"),
            ('Moisture Cut:', f"{lot.get('moisture_cut', 0):.2f} qtl"),
            ('FRK:', 'Yes' if lot.get('frk', False) else 'No'),
            ('Deposit Centre:', lot.get('rice_deposit_centre', 'N/A')),
            ('QI Expense:', f"₹{lot.get('qi_expense', 0)}"),
            ('Dalali Expense:', f"₹{lot.get('lot_dalali_expense', 0)}"),
            ('Brokerage:', f"₹{lot.get('brokerage', 0)}"),
            ('Other Costs:', f"₹{lot.get('other_costs', 0)}"),
        ]
        
        for label, value in fields:
            frame = tk.Frame(details_frame, bg='white')
            frame.pack(fill=tk.X, pady=3)
            tk.Label(frame, text=label, font=('Arial', 11, 'bold'), 
                    bg='white', width=20, anchor='w').pack(side=tk.LEFT)
            tk.Label(frame, text=str(value), font=('Arial', 11), 
                    bg='white').pack(side=tk.LEFT, padx=10)
        
        # Link to parent sauda
        sauda_id = lot.get('sauda_id')
        if sauda_id:
            sauda = next((s for s in db.saudas if s['_id'] == sauda_id), None)
            if sauda:
                tk.Label(details_frame, text=f"\nParent Sauda: {sauda['name']}", 
                        font=('Arial', 11, 'bold'), bg='white', fg='#3498db').pack(anchor='w', pady=10)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
    
    # PRODUCTS SECTION
    def show_products(self):
        self.clear_content()
        
        # Header
        header = tk.Frame(self.content_frame, bg='white')
        header.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(header, text="Products Management", font=('Arial', 20, 'bold'),
                bg='white').pack(side=tk.LEFT)
        
        tk.Button(header, text="+ Add Product", command=self.add_product_form,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 padx=20, pady=8, cursor='hand2').pack(side=tk.RIGHT)
        
        # Info frame
        info_frame = tk.LabelFrame(self.content_frame, text="Summary", bg='#ecf0f1',
                                   font=('Arial', 11, 'bold'), padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        total_products = len(db.products)
        total_count = sum(p.get('total_count', 0) for p in db.products)
        
        tk.Label(info_frame, text=f"Total Products: {total_products}", bg='#ecf0f1',
                font=('Arial', 11)).pack(side=tk.LEFT, padx=20)
        tk.Label(info_frame, text=f"Total Count: {total_count}", bg='#ecf0f1',
                font=('Arial', 11)).pack(side=tk.LEFT, padx=20)
        
        # Table frame
        table_frame = tk.Frame(self.content_frame, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Treeview
        columns = ('ID', 'Lot No', 'Total Count', 'Shipping Date', 'Shipped Via', 'Sticker Date')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=140)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate data
        for product in db.products:
            lot = next((l for l in db.lots if l['_id'] == product.get('lot_id')), None)
            lot_no = lot.get('rice_lot_no', 'N/A') if lot else 'N/A'
            
            shipping_date = product.get('shipping_date')
            sticker_date = product.get('flap_sticker_t_date')
            
            tree.insert('', tk.END, values=(
                product.get('_id', 'N/A'),
                lot_no,
                product.get('total_count', 0),
                shipping_date.strftime('%Y-%m-%d') if shipping_date else 'N/A',
                product.get('shipped_via', 'N/A'),
                sticker_date.strftime('%Y-%m-%d') if sticker_date else 'N/A'
            ))
        
        # Double click to view details
        tree.bind('<Double-1>', lambda e: self.view_product_details(tree))
    
    def add_product_form(self):
        form_window = tk.Toplevel(self.root)
        form_window.title("Add New Product")
        form_window.geometry("500x450")
        form_window.configure(bg='white')
        
        tk.Label(form_window, text="Add New Product", font=('Arial', 16, 'bold'),
                bg='white').pack(pady=20)
        
        fields_frame = tk.Frame(form_window, bg='white')
        fields_frame.pack(padx=40, pady=20, fill=tk.BOTH, expand=True)
        
        entries = {}
        row = 0
        
        # Lot selection
        tk.Label(fields_frame, text="Lot:", bg='white', font=('Arial', 11)).grid(
            row=row, column=0, sticky='w', pady=10)
        lot_var = tk.StringVar()
        lot_names = [f"{l['_id']}: {l.get('rice_lot_no', 'N/A')}" for l in db.lots]
        lot_combo = ttk.Combobox(fields_frame, textvariable=lot_var,
                                values=lot_names, width=28)
        lot_combo.grid(row=row, column=1, pady=10, padx=10)
        entries['lot'] = lot_var
        row += 1
        
        # Total Count
        tk.Label(fields_frame, text="Total Count:", bg='white', font=('Arial', 11)).grid(
            row=row, column=0, sticky='w', pady=10)
        entries['total_count'] = tk.Entry(fields_frame, font=('Arial', 11), width=30)
        entries['total_count'].grid(row=row, column=1, pady=10, padx=10)
        row += 1
        
        # Shipped Via
        tk.Label(fields_frame, text="Shipped Via:", bg='white', font=('Arial', 11)).grid(
            row=row, column=0, sticky='w', pady=10)
        entries['shipped_via'] = tk.Entry(fields_frame, font=('Arial', 11), width=30)
        entries['shipped_via'].grid(row=row, column=1, pady=10, padx=10)
        row += 1
        
        # Sticker Via
        tk.Label(fields_frame, text="Sticker Batch:", bg='white', font=('Arial', 11)).grid(
            row=row, column=0, sticky='w', pady=10)
        entries['sticker_via'] = tk.Entry(fields_frame, font=('Arial', 11), width=30)
        entries['sticker_via'].grid(row=row, column=1, pady=10, padx=10)
        row += 1
        
        def save_product():
            try:
                lot_id = lot_var.get().split(':')[0] if lot_var.get() else None
                
                new_product = {
                    '_id': str(len(db.products) + 1),
                    'lot_id': lot_id,
                    'total_count': int(entries['total_count'].get()) if entries['total_count'].get() else 0,
                    'shipping_date': datetime.now(),
                    'shipped_via': entries['shipped_via'].get(),
                    'flap_sticker_t_date': datetime.now(),
                    'flap_sticker_t_via': entries['sticker_via'].get(),
                    'created_at': datetime.now()
                }
                db.products.append(new_product)
                messagebox.showinfo("Success", "Product added successfully!")
                form_window.destroy()
                self.show_products()
            except ValueError as e:
                messagebox.showerror("Error", f"Please enter valid values: {str(e)}")
        
        tk.Button(fields_frame, text="Save", command=save_product, bg='#27ae60',
                 fg='white', font=('Arial', 11, 'bold'), padx=30, pady=8).grid(
                     row=row, column=1, pady=20, sticky='e')
    
    def view_product_details(self, tree):
        selected = tree.selection()
        if not selected:
            return
        
        values = tree.item(selected[0])['values']
        product_id = values[0]
        product = next((p for p in db.products if p.get('_id') == product_id), None)
        
        if not product:
            return
        
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Product Details - {product_id}")
        detail_window.geometry("600x450")
        detail_window.configure(bg='white')
        
        details_frame = tk.Frame(detail_window, bg='white')
        details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(details_frame, text=f"Product ID: {product['_id']}", 
                font=('Arial', 16, 'bold'), bg='white').pack(anchor='w', pady=5)
        
        # Display fields
        fields = [
            ('Total Count:', product.get('total_count', 0)),
            ('Shipped Via:', product.get('shipped_via', 'N/A')),
            ('Sticker Batch:', product.get('flap_sticker_t_via', 'N/A')),
        ]
        
        shipping_date = product.get('shipping_date')
        sticker_date = product.get('flap_sticker_t_date')
        
        if shipping_date:
            fields.append(('Shipping Date:', shipping_date.strftime('%Y-%m-%d %H:%M')))
        if sticker_date:
            fields.append(('Sticker Date:', sticker_date.strftime('%Y-%m-%d %H:%M')))
        
        for label, value in fields:
            frame = tk.Frame(details_frame, bg='white')
            frame.pack(fill=tk.X, pady=5)
            tk.Label(frame, text=label, font=('Arial', 11, 'bold'), 
                    bg='white', width=20, anchor='w').pack(side=tk.LEFT)
            tk.Label(frame, text=str(value), font=('Arial', 11), 
                    bg='white').pack(side=tk.LEFT, padx=10)
        
        # Link to parent lot
        lot_id = product.get('lot_id')
        if lot_id:
            lot = next((l for l in db.lots if l['_id'] == lot_id), None)
            if lot:
                tk.Label(details_frame, text=f"\nParent Lot: {lot.get('rice_lot_no', 'N/A')}", 
                        font=('Arial', 11, 'bold'), bg='white', fg='#3498db').pack(anchor='w', pady=10)
                tk.Label(details_frame, text=f"Rice Type: {lot.get('rice_type', 'N/A')}", 
                        font=('Arial', 10), bg='white').pack(anchor='w', padx=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingDashboard(root)
    root.mainloop()