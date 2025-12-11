import tkinter as tk
from tkinter import messagebox, filedialog
import os
import json
import datetime
from tkcalendar import Calendar

# --- CONFIGURATION & COLORS ---
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "simple_todo_config.json")

# Modern Dark Theme Palette
COLOR_BG = "#1e1e1e"        
COLOR_FG = "#ffffff"        
COLOR_ACCENT = "#007acc"    
COLOR_ACCENT_HOVER = "#005f9e"
COLOR_LIST_BG = "#252526"   
COLOR_INPUT_BG = "#3c3c3c"  
COLOR_DANGER = "#d32f2f"    

# Status Symbols for UI Display
SYMBOL_OPEN = "☐ "
SYMBOL_IN_PROGRESS = "▶ "
SYMBOL_COMPLETED = "☑ "
SYMBOL_CANCELED = "— "

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To Do App")
        self.root.geometry("400x600")
        self.root.configure(bg=COLOR_BG)

        self.save_directory = self.load_config()
        self.target_file = ""

        # --- UI Setup (Same as last version for cleanup) ---
        self.header_frame = tk.Frame(root, bg=COLOR_BG)
        self.header_frame.pack(pady=(20, 10), fill=tk.X, padx=20)
        
        self.title_label = tk.Label(self.header_frame, text="My Tasks", 
                                    font=("Segoe UI", 24, "bold"), 
                                    bg=COLOR_BG, fg=COLOR_FG)
        self.title_label.pack(side=tk.LEFT)

        self.location_label = tk.Label(root, text="Initializing...", 
                                       font=("Segoe UI", 8), 
                                       bg=COLOR_BG, fg="#888888")
        self.location_label.pack(pady=(0, 10), padx=20, anchor="w")

        self.input_frame = tk.Frame(root, bg=COLOR_BG)
        self.input_frame.pack(fill=tk.X, padx=20, pady=5)

        self.task_entry = tk.Entry(self.input_frame, font=("Segoe UI", 12), 
                                   bg=COLOR_INPUT_BG, fg=COLOR_FG, 
                                   insertbackground="white", relief="flat", highlightthickness=1, 
                                   highlightbackground="#555555", highlightcolor=COLOR_ACCENT)
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 10))
        self.task_entry.bind('<Return>', self.add_task_event)

        self.add_btn = tk.Button(self.input_frame, text="+", font=("Segoe UI", 12, "bold"),
                                 bg=COLOR_ACCENT, fg="white", activebackground=COLOR_ACCENT_HOVER,
                                 activeforeground="white", relief="flat", cursor="hand2",
                                 command=self.add_task)
        self.add_btn.pack(side=tk.RIGHT, ipadx=10, ipady=1)

        self.tasks_listbox = tk.Listbox(root, font=("Segoe UI", 11), 
                                        bg=COLOR_LIST_BG, fg=COLOR_FG,
                                        selectbackground="#37373d", selectforeground="white",
                                        activestyle="none", relief="flat", highlightthickness=0,
                                        borderwidth=0)
        self.tasks_listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        self.tasks_listbox.bind('<Double-1>', self.toggle_status)

        self.footer_frame = tk.Frame(root, bg=COLOR_BG)
        self.footer_frame.pack(fill=tk.X, padx=20, pady=20)

        self.del_btn = tk.Button(self.footer_frame, text="Delete Selected", font=("Segoe UI", 9),
                                 bg=COLOR_BG, fg=COLOR_DANGER, activebackground=COLOR_BG,
                                 activeforeground="#ff6666", relief="flat", cursor="hand2",
                                 command=self.delete_task)
        self.del_btn.pack(side=tk.LEFT)

        self.change_btn = tk.Button(self.footer_frame, text="Storage Settings", font=("Segoe UI", 9),
                                    bg=COLOR_BG, fg="#666666", activebackground=COLOR_BG,
                                    activeforeground="#999999", relief="flat", cursor="hand2",
                                    command=self.change_directory)
        self.change_btn.pack(side=tk.RIGHT)

        # --- Initialization Logic ---
        if not self.save_directory:
            self.root.after(100, self.change_directory)
        else:
            self.update_paths()
            self.load_from_md()

    # --- Configuration and File Path Methods (Unchanged) ---
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f).get("save_directory", "")
            except: return ""
        return ""

    def save_config(self, path):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"save_directory": path}, f)

    def update_paths(self):
        self.target_file = os.path.join(self.save_directory, "To Do.md")
        display = "..." + self.target_file[-40:] if len(self.target_file) > 40 else self.target_file
        self.location_label.config(text=f"📁 {display}")

    def change_directory(self):
        messagebox.showinfo("Setup", "Select the FOLDER where 'To Do.md' is saved.")
        new_dir = filedialog.askdirectory(title="Select Folder")
        if new_dir:
            self.save_directory = new_dir
            self.save_config(new_dir)
            self.update_paths()
            self.load_from_md()
        elif not self.save_directory:
            self.root.destroy()

    def add_task(self):
        task = self.task_entry.get()
        if task:
            # Task input is valid, but now we prompt for the date
            # Store the task temporarily and open the calendar pop-up
            self.pending_task = task
            self.select_due_date()
            # Do NOT clear the entry yet, and do NOT save yet

    def add_task_event(self, event): 
        # This remains the same, it just calls add_task()
        self.add_task()

    def select_due_date(self):
        """Opens a Toplevel window with a calendar. Clicking a date confirms and adds the task."""
        
        # 1. Create the Toplevel window
        top = tk.Toplevel(self.root)
        top.title("Select Due Date")
        # Make the window slightly smaller since we removed the button
        top.geometry("320x300") 
        top.configure(bg=COLOR_BG)
        top.grab_set() 
        top.resizable(False, False)

        # 2. Create the Calendar widget
        today = datetime.date.today()
        # Start the calendar on the current month, but keep tomorrow's date for reference
        tomorrow = today + datetime.timedelta(days=1)
        
        # Define the function that runs when a date is clicked
        def date_selected(event):
            # The .get_date() method must be called within this function
            selected_date_str = cal.get_date()
            
            if hasattr(self, 'pending_task'):
                # 3. Process Task: Construct the full task string
                task_with_due_date = f"{self.pending_task} -> Due [[{selected_date_str}]]"
                
                # 4. Sync, Insert, Clear, and Save
                self.load_from_md() 
                self.tasks_listbox.insert(tk.END, f"{SYMBOL_OPEN}{task_with_due_date}")
                self.task_entry.delete(0, tk.END)
                self.save_to_md()
                del self.pending_task
                
            top.destroy() # 5. Close the calendar window automatically

        # Calendar Setup
        cal = Calendar(top, 
                       font=("Segoe UI", 10, "bold"), 
                       selectmode='day',
                       cursor="hand1",
                       date_pattern='mm-dd-yy', 
                       
                       # Styling (as before)
                       background=COLOR_LIST_BG,
                       foreground=COLOR_FG,
                       normalbackground=COLOR_LIST_BG,
                       normalforeground=COLOR_FG,
                       headersbackground=COLOR_ACCENT,
                       headersforeground='white',
                       selectbackground=COLOR_ACCENT_HOVER,
                       selectforeground='white',
                       weekendbackground=COLOR_LIST_BG,
                       weekendforeground='#aaaaaa', 
                       showothermonth=False,
                       year=today.year, # Start calendar at current year/month
                       month=today.month, 
                       day=tomorrow.day) # Highlight tomorrow's date initially
        
        # Bind the function to the date selection event!
        cal.bind("<<CalendarSelected>>", date_selected)

        # Add padding and pack
        cal.pack(pady=15, padx=15, fill="both", expand=True) 
        
        # Handle closing the Toplevel window without selecting
        def on_close():
             if hasattr(self, 'pending_task'):
                 del self.pending_task
             top.destroy()

        top.protocol("WM_DELETE_WINDOW", on_close)

    def delete_task(self):
        try:
            index = self.tasks_listbox.curselection()[0]
            target_text = self.tasks_listbox.get(index)
            self.load_from_md() # Safe Sync
            
            all_items = self.tasks_listbox.get(0, tk.END)
            try:
                new_index = all_items.index(target_text)
                self.tasks_listbox.delete(new_index)
                self.save_to_md()
            except ValueError:
                pass # Already deleted externally
        except IndexError:
            pass 

    def toggle_status(self, event):
        """Cycles the status of the selected task on double-click."""
        try:
            index = self.tasks_listbox.curselection()[0]
            current_text = self.tasks_listbox.get(index)
            
            # 1. Determine the next status based on the current symbol
            if current_text.startswith(SYMBOL_OPEN):
                # OPEN -> IN PROGRESS
                new_text = current_text.replace(SYMBOL_OPEN, SYMBOL_IN_PROGRESS, 1)
            elif current_text.startswith(SYMBOL_IN_PROGRESS):
                # IN PROGRESS -> COMPLETED
                new_text = current_text.replace(SYMBOL_IN_PROGRESS, SYMBOL_COMPLETED, 1)
            elif current_text.startswith(SYMBOL_COMPLETED):
                # COMPLETED -> CANCELED
                new_text = current_text.replace(SYMBOL_COMPLETED, SYMBOL_CANCELED, 1)
            elif current_text.startswith(SYMBOL_CANCELED):
                # CANCELED -> OPEN (Starts the cycle over)
                new_text = current_text.replace(SYMBOL_CANCELED, SYMBOL_OPEN, 1)
            else:
                return # Safety break
            
            # 2. Sync, Update Listbox, and Save
            self.load_from_md() # Safe Sync
            all_items = self.tasks_listbox.get(0, tk.END)
            
            try:
                # Find the task again in the synced list
                new_index = all_items.index(current_text) 
                self.tasks_listbox.delete(new_index)
                self.tasks_listbox.insert(new_index, new_text)
                self.save_to_md()
            except ValueError:
                pass # Task was changed/deleted externally

        except IndexError:
            pass
        except Exception as e:
            print(f"Error during toggle: {e}")

    def save_to_md(self):
        if not self.target_file: return
        try:
            with open(self.target_file, "w", encoding="utf-8") as f:
                f.write("")
                items = self.tasks_listbox.get(0, tk.END)
                for item in items:
                    # Map UI symbols back to Markdown prefixes [ ], [/], [x], [-]
                    if item.startswith(SYMBOL_COMPLETED):
                        f.write(f"- [x] {item.replace(SYMBOL_COMPLETED, '')}\n")
                    elif item.startswith(SYMBOL_IN_PROGRESS):
                        f.write(f"- [/] {item.replace(SYMBOL_IN_PROGRESS, '')}\n")
                    elif item.startswith(SYMBOL_CANCELED):
                        f.write(f"- [-] {item.replace(SYMBOL_CANCELED, '')}\n")
                    else: # Default is Open
                        f.write(f"- [ ] {item.replace(SYMBOL_OPEN, '')}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_from_md(self):
        self.tasks_listbox.delete(0, tk.END)
        if os.path.exists(self.target_file):
            try:
                with open(self.target_file, "r", encoding="utf-8") as f:
                    for line in f.readlines():
                        line = line.strip()
                        text = line[6:] # Text starts after the 6-character prefix "- [Y] "
                        
                        # Map Markdown prefixes to UI symbols
                        if line.startswith("- [x] "):
                            self.tasks_listbox.insert(tk.END, f"{SYMBOL_COMPLETED}{text}")
                        elif line.startswith("- [/] "):
                            self.tasks_listbox.insert(tk.END, f"{SYMBOL_IN_PROGRESS}{text}")
                        elif line.startswith("- [-] "):
                            self.tasks_listbox.insert(tk.END, f"{SYMBOL_CANCELED}{text}")
                        elif line.startswith("- [ ] "):
                            self.tasks_listbox.insert(tk.END, f"{SYMBOL_OPEN}{text}")
            except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()