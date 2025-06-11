import tkinter as tk
from tkinter import messagebox, Toplevel, Scrollbar, Text
import os
from tkinter import ttk
import threading
import tempfile
import zipfile
import datetime

# List of safe-to-delete file extensions
SAFE_TO_DELETE_EXTENSIONS = {
    '.log',  # Log files
    '.tmp',  # Temporary files
    '.old',  # Old file versions
    '.swp',  # Vim swap files
    '.swo',  # Vim swap files
    '.dmp',  # Memory dump files
    '.cache',  # Cache files
    '.aux',  # LaTeX intermediate files
    '.out',  # LaTeX intermediate files
    '.pyc',  # Compiled Python files
    '.DS_Store',  # macOS folder cache
    'Thumbs.db'  # Windows thumbnail cache
}

found_files = []
found_folders = []


def on_find():
    global found_files, found_dirs, found_folders
    selected_index = listbox.curselection()
    user_path = path_entry.get().strip()
    found_dirs = []
    found_files = []
    found_folders = []

    if selected_index:
        path_to_search = listbox.get(selected_index)
    elif user_path:
        path_to_search = user_path
    else:
        result_label.config(text="Please select or enter a path")
        return

    text_box.config(state=tk.NORMAL)
    text_box.delete("1.0", tk.END)
    text_box.insert(tk.END, path_to_search)
    text_box.config(state=tk.DISABLED)

    if not os.path.exists(path_to_search):
        result_label.config(text="Invalid path. Please check again.")
        show_more_button.pack_forget()
        delete_button.pack_forget()
        progress.pack_forget()
        return

    include_all_files = var_include_all.get()

    # First: count total dirs + files to set progress max
    total_items = 0
    for root_dir, dirs, files in os.walk(path_to_search):
        total_items += len(dirs) + len(files)

    if total_items == 0:
        result_label.config(text="No files or folders found.")
        show_more_button.pack_forget()
        delete_button.pack_forget()
        progress.pack_forget()
        return

    # Show and reset progress bar
    progress.pack(pady=(5, 10))
    progress['maximum'] = total_items
    progress['value'] = 0

    count = 0

    # Now actual scanning, updating progress
    for root_dir, dirs, files in os.walk(path_to_search):
        if not include_all_files:
            # Only collect files with safe-to-delete extensions
            for file in files:
                count += 1
                progress['value'] = count
                root.update()
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in SAFE_TO_DELETE_EXTENSIONS or file in SAFE_TO_DELETE_EXTENSIONS:
                    found_files.append(os.path.join(root_dir, file))
        else:
            # Collect all folders and files
            found_folders.extend([os.path.join(root_dir, d) for d in dirs])
            for file in files:
                found_files.append(os.path.join(root_dir, file))
                count += 1
                progress['value'] = count
                root.update()

            # Count dirs for progress but already added to found_folders
            count += len(dirs)
            progress['value'] = count
            root.update()

        # Update count for dirs too
        count += len(dirs)
        progress['value'] = count
        root.update()

    if not found_files and not found_folders:
        result_label.config(text="No files or folders found based on the selected option.")
        show_more_button.pack_forget()
        delete_button.pack_forget()
    else:
        total_items_found = len(found_files) + len(found_folders)
        result_label.config(text=f"📂 Found {len(found_folders)} folders and 🧹 {len(found_files)} files (Total: {total_items_found})")
        show_more_button.pack(pady=(10, 2))
        delete_button.pack(pady=(2, 15))

    progress.pack_forget()  # Hide progress bar after done



def on_delete():
    global found_files, found_dirs
    if not found_files:
        messagebox.showinfo("Info", "No files to delete.")
        return

    confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(found_files)} files?")
    if not confirm:
        return

    # Backup if requested
    if var_take_backup.get():
        try:
            # Create backup folder (Desktop/TempBackup) or somewhere safe
            backup_folder = os.path.join(os.path.expanduser("~"), "Desktop", "TempBackup")
            os.makedirs(backup_folder, exist_ok=True)

            # Create a zip file with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_zip_path = os.path.join(backup_folder, f"backup_{timestamp}.zip")

            with zipfile.ZipFile(backup_zip_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                for file in found_files:
                    # Add file with relative path (optional)
                    backup_zip.write(file, arcname=os.path.basename(file))

            messagebox.showinfo("Backup Created", f"Backup created at:\n{backup_zip_path}")
        except Exception as e:
            messagebox.showerror("Backup Failed", f"Backup failed:\n{str(e)}")
            return  # Stop deletion if backup failed

    deleted_count, failed_files = 0, []

    delete_progress['maximum'] = len(found_files)
    delete_progress['value'] = 0
    delete_progress.pack(pady=(5, 10))
    root.update()

    for i, file in enumerate(found_files, start=1):
        try:
            os.remove(file)
            deleted_count += 1
        except Exception as e:
            failed_files.append(f"{file} - {str(e)}")

        delete_progress['value'] = i
        root.update()

    delete_progress.pack_forget()

    deleted_folders = 0
    for folder in sorted(found_dirs, key=lambda x: -len(x)):
        try:
            os.rmdir(folder)
            deleted_folders += 1
        except:
            pass

    result = f"🗑️ {deleted_count} files deleted.\n📁 {deleted_folders} empty folders removed."
    if failed_files:
        result += f"\n⚠️ {len(failed_files)} files couldn't be deleted."
    result_label.config(text=result)

    found_files.clear()
    found_dirs.clear()
    show_more_button.pack_forget()
    delete_button.pack_forget()


def show_more_window():
    if not found_files and not found_folders:
        messagebox.showinfo("Info", "No files or folders to show.")
        return

    top = Toplevel(root)
    top.title("Found Files" if not var_include_all.get() else "Found Files and Folders")
    top.geometry("800x400")
    top.configure(bg="#f9f9f9")

    scrollbar = Scrollbar(top)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text_area = Text(top, wrap="none", yscrollcommand=scrollbar.set,
                     font=("Segoe UI", 10), bg="#ffffff", fg="#333333")
    text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    if not var_include_all.get():
        # Show only safe-to-delete files
        text_area.insert(tk.END, "🧾 Safe-to-delete files:\n")
        for file in found_files:
            text_area.insert(tk.END, file + "\n")
    else:
        # Show folders and all files
        if found_folders:
            text_area.insert(tk.END, "📁 Folders:\n")
            for folder in found_folders:
                text_area.insert(tk.END, folder + "\n")

        if found_files:
            text_area.insert(tk.END, "\n🧾 Files:\n")
            for file in found_files:
                text_area.insert(tk.END, file + "\n")


    text_area.config(state=tk.DISABLED)
    scrollbar.config(command=text_area.yview)




root = tk.Tk()
root.title("Temp files cleaner")
root.geometry("700x700")
root.configure(bg="#f0f2f5")

title_font = ("Segoe UI", 14, "bold")
section_font = ("Segoe UI", 11)
entry_font = ("Segoe UI", 10)

temp_dir = tempfile.gettempdir()
appData_temp = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp')
win_temp = "C:\\Windows\\Temp"
default_paths = [temp_dir, appData_temp, win_temp]

instruction_text = (
    f"Below are paths that often contain bulk log/temp files:\n"
    f"• {temp_dir}\n"
    f"• {appData_temp}\n\n"
    f"You can choose one or paste a custom path below:"
)

instruction_box = tk.Text(root, height=6, width=80, wrap="word",
                          font=section_font, bg="#f0f2f5", bd=0)
instruction_box.insert(tk.END, instruction_text)
instruction_box.config(state=tk.DISABLED)
instruction_box.pack(pady=(15, 5))

result_label = tk.Label(root, text="")
result_label.pack()

progress = ttk.Progressbar(root, orient='horizontal', length=600, mode='determinate')
progress.pack(pady=(5, 10))
progress.pack_forget()

delete_progress = ttk.Progressbar(root, orient='horizontal', length=300, mode='determinate')
delete_progress.pack(pady=(5, 10))
delete_progress.pack_forget() 

listbox = tk.Listbox(root, height=4, width=100, font=entry_font)
for path in default_paths:
    listbox.insert(tk.END, path)
listbox.pack(pady=(5, 10), padx=20)

path_entry = tk.Entry(root, width=100, font=entry_font)
path_entry.insert(0, "Paste your path here")
path_entry.pack(pady=(0, 10), padx=20)

var_include_all = tk.BooleanVar(value=False) 
radio_button = tk.Checkbutton(root, text="Include ALL files and folders (not recommended)",
                              variable=var_include_all, font=entry_font, bg="#f0f2f5")
radio_button.pack(pady=(5, 0), padx=20, anchor='w')

info_label = tk.Label(root, text="By default, only safe-to-delete files (.log, .tmp, .old, etc.) will be removed. Check the box above to delete everything.",
                      font=("Segoe UI", 9), bg="#f0f2f5", fg="#555555", anchor='w', justify='left')
info_label.pack(pady=(0, 10), padx=22, fill='x')

var_take_backup = tk.BooleanVar(value=False)
backup_checkbox = tk.Checkbutton(root, text="Take backup before deleting",
                                 variable=var_take_backup, font=entry_font, bg="#f0f2f5")
backup_checkbox.pack(pady=(5, 0), padx=20, anchor='w')


text_box = tk.Text(root, height=1, width=100, font=("Segoe UI", 10), bg="#ffffff", fg="#444444")
text_box.config(state=tk.DISABLED)
text_box.pack(pady=(0, 20)) 

find_button = tk.Button(root, text="🔍 Find", command=on_find, font=("Segoe UI", 10, "bold"), bg="#4caf50", fg="white", padx=10, pady=5)
find_button.pack(pady=(5, 5))

show_more_button = tk.Button(root, text="📄 Show More", command=show_more_window, font=("Segoe UI", 10, "bold"), bg="#2196f3", fg="white", padx=10, pady=5)
show_more_button.pack_forget()

delete_button = tk.Button(root, text="🗑️ Delete Found Files", command=on_delete, font=("Segoe UI", 10, "bold"), bg="#f44336", fg="white", padx=10, pady=5)
delete_button.pack_forget()

result_label = tk.Label(root, text="", font=("Segoe UI", 10, "italic"), bg="#f0f2f5", fg="#333333")
result_label.pack(pady=(5, 10))

root.mainloop()