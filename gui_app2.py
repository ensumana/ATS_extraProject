import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime
import threading
import os

from tkcalendar import DateEntry

# Your Outlook downloader
from outlook_engine import download_resumes

# ATS parser import (must exist in same project)
from ats_parser import process_resumes


# ----------------------------
# UI CONFIG
# ----------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ATSApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("ATS Resume System")
        self.geometry("650x450")

        self.build_ui()

    def build_ui(self):

        ctk.CTkLabel(
            self,
            text="ATS Resume Downloader + Parser",
            font=("Arial", 20, "bold")
        ).pack(pady=15)

        # Folder
        self.folder_path = ctk.StringVar(value="Select folder")

        ctk.CTkEntry(self, textvariable=self.folder_path, width=420).pack(pady=10)

        ctk.CTkButton(
            self,
            text="Browse Folder",
            command=self.browse_folder
        ).pack(pady=5)

        # Dates
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=10)

        self.from_date = DateEntry(self.frame, date_pattern="dd-mm-yyyy")
        self.to_date = DateEntry(self.frame, date_pattern="dd-mm-yyyy")

        ctk.CTkLabel(self.frame, text="From").grid(row=0, column=0, padx=10)
        self.from_date.grid(row=1, column=0, padx=10)

        ctk.CTkLabel(self.frame, text="To").grid(row=0, column=1, padx=10)
        self.to_date.grid(row=1, column=1, padx=10)

        # Progress
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.set(0)
        self.progress.pack(pady=20)

        self.status = ctk.CTkLabel(self, text="Idle")
        self.status.pack()

        # Button
        ctk.CTkButton(
            self,
            text="Run ATS Pipeline",
            height=40,
            command=self.start_pipeline
        ).pack(pady=20)

    # ----------------------------
    # FOLDER SELECT
    # ----------------------------
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    # ----------------------------
    # PROGRESS
    # ----------------------------
    def update_progress(self, value):
        self.progress.set(value / 100)
        self.status.configure(text=f"Processing {value}%")
        self.update_idletasks()

    # ----------------------------
    # START THREAD
    # ----------------------------
    def start_pipeline(self):
        thread = threading.Thread(target=self.run_pipeline)
        thread.daemon = True
        thread.start()

    # ----------------------------
    # MAIN PIPELINE
    # ----------------------------
    def run_pipeline(self):

        try:
            folder = self.folder_path.get()

            if not os.path.exists(folder):
                messagebox.showerror("Error", "Select valid folder")
                return

            # ---------------- DATE FIX ----------------
            from_date = datetime.strptime(
                self.from_date.get(),
                "%d-%m-%Y"
            ).replace(hour=0, minute=0, second=0)

            to_date = datetime.strptime(
                self.to_date.get(),
                "%d-%m-%Y"
            ).replace(hour=23, minute=59, second=59)

            if from_date > to_date:
                messagebox.showerror("Error", "Invalid date range")
                return

            self.status.configure(text="Downloading resumes...")

            processed, downloaded = download_resumes(
                folder,
                from_date,
                to_date,
                self.update_progress
            )

            self.status.configure(text="Parsing resumes...")

            excel_file = process_resumes(folder)

            self.progress.set(1.0)

            messagebox.showinfo(
                "Completed",
                f"Processed Emails: {processed}\n"
                f"Downloaded: {downloaded}\n\n"
                f"Excel Generated:\n{excel_file}"
            )

            self.status.configure(text="Completed")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status.configure(text="Failed")


# ----------------------------
# RUN APP
# ----------------------------
if __name__ == "__main__":
    app = ATSApp()
    app.mainloop()