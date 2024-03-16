import os
import logging
import threading
import pkg_resources

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from youtube_bulk_upload import YouTubeBulkUpload


class ReusableWidgetFrame(tk.LabelFrame):
    def __init__(self, parent, title, **kwargs):
        kwargs.setdefault("padx", 10)  # Add default padding on the x-axis
        kwargs.setdefault("pady", 10)  # Add default padding on the y-axis
        super().__init__(parent, text=title, **kwargs)
        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.row = 0  # Keep track of the next row index to add widgets

    def new_row(self):
        self.row += 1

    def add_widgets(self, widgets):
        for widget in widgets:
            widget.grid(row=self.row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
            self.row += 1

    def add_find_replace_widgets(self, label_text):
        tk.Label(self, text=label_text).grid(row=self.row, column=0, sticky="w")

        # Listbox with a scrollbar for replacements
        self.row += 1
        self.replacements_listbox = tk.Listbox(self, height=4, width=50)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.replacements_listbox.yview)
        self.replacements_listbox.config(yscrollcommand=scrollbar.set)
        self.replacements_listbox.grid(row=self.row, column=0, columnspan=2, sticky="nsew", padx=(5, 0), pady=5)
        scrollbar.grid(row=self.row, column=2, sticky="ns", pady=5)

        # Entry fields for adding new find/replace pairs
        self.row += 1
        tk.Entry(self, textvariable=self.find_var, width=20).grid(row=self.row, column=0, sticky="ew", padx=(5, 0), pady=(5, 0))
        tk.Entry(self, textvariable=self.replace_var, width=20).grid(row=self.row, column=1, sticky="ew", pady=(5, 0))

        # Buttons for adding and removing replacements
        self.row += 1
        add_button = tk.Button(self, text="Add Replacement", command=self.add_replacement)
        add_button.grid(row=self.row, column=0, sticky="ew", padx=(5, 0), pady=5)
        remove_button = tk.Button(self, text="Remove Selected", command=self.remove_replacement)
        remove_button.grid(row=self.row, column=1, sticky="ew", pady=5)

    def add_replacement(self):
        find_text = self.find_var.get()
        replace_text = self.replace_var.get()
        if find_text and replace_text:
            self.replacements_listbox.insert(tk.END, f"{find_text} -> {replace_text}")
            self.find_var.set("")
            self.replace_var.set("")

    def remove_replacement(self):
        selected_indices = self.replacements_listbox.curselection()
        for i in reversed(selected_indices):
            self.replacements_listbox.delete(i)


class YouTubeBulkUploaderGUI:
    def __init__(self, root):
        self.root = root

        # Define variables for inputs
        self.log_level_var = tk.StringVar(value="info")
        self.dry_run_var = tk.BooleanVar()
        self.noninteractive_var = tk.BooleanVar()
        self.source_directory_var = tk.StringVar(value=os.path.expanduser("~"))
        self.yt_client_secrets_file_var = tk.StringVar(value="client_secret.json")
        self.yt_category_id_var = tk.StringVar(value="10")
        self.yt_keywords_var = tk.StringVar(value="music")
        self.yt_desc_template_file_var = tk.StringVar(value="description_template.txt")
        self.yt_title_prefix_var = tk.StringVar()
        self.yt_title_suffix_var = tk.StringVar()
        self.thumb_file_prefix_var = tk.StringVar()
        self.thumb_file_suffix_var = tk.StringVar()
        self.thumb_file_extensions_var = tk.StringVar(value=".png .jpg .jpeg")

        self.row = 0
        self.setup_ui()

        self.root.update()  # Ensure the window is updated with the latest UI changes
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

    def setup_ui(self):
        # Fetch the package version
        package_version = pkg_resources.get_distribution("youtube-bulk-upload").version
        self.root.title(f"YouTube Bulk Upload - v{package_version}")

        # Configure the grid layout to allow frames to resize properly
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # General Options Frame
        self.general_frame = ReusableWidgetFrame(self.root, "General Options")
        self.general_frame.grid(row=self.row, column=0, padx=10, pady=5, sticky="nsew")
        self.general_frame.grid_rowconfigure(8, weight=1)
        self.general_frame.grid_columnconfigure(1, weight=1)
        self.add_general_options_widgets()

        # YouTube Title Frame with Find/Replace
        self.youtube_title_frame = ReusableWidgetFrame(self.root, "YouTube Title Options")
        self.youtube_title_frame.grid(row=self.row, column=1, padx=10, pady=5, sticky="nsew")
        self.youtube_title_frame.grid_rowconfigure(4, weight=1)
        self.youtube_title_frame.grid_columnconfigure(1, weight=1)
        self.add_youtube_title_widgets()

        self.row += 1

        # Thumbnail Options Frame with Find/Replace
        self.thumbnail_frame = ReusableWidgetFrame(self.root, "YouTube Thumbnail Options")
        self.thumbnail_frame.grid(row=self.row, column=0, padx=10, pady=5, sticky="nsew")
        self.thumbnail_frame.grid_rowconfigure(4, weight=1)
        self.thumbnail_frame.grid_columnconfigure(1, weight=1)
        self.add_thumbnail_options_widgets()

        # YouTube Description Frame with Find/Replace
        self.youtube_desc_frame = ReusableWidgetFrame(self.root, "YouTube Description Options")
        self.youtube_desc_frame.grid(row=self.row, column=1, padx=10, pady=5, sticky="nsew")
        self.youtube_desc_frame.grid_rowconfigure(4, weight=1)
        self.youtube_desc_frame.grid_columnconfigure(1, weight=1)
        self.add_youtube_description_widgets()

        self.row += 1

        # Run and Clear Log buttons
        self.run_button = tk.Button(self.root, text="Run", command=self.run_upload)
        self.run_button.grid(row=self.row, column=0, padx=10, pady=5, sticky="ew")
        self.clear_log_button = tk.Button(self.root, text="Clear Log", command=self.clear_log)
        self.clear_log_button.grid(row=self.row, column=1, padx=10, pady=5, sticky="ew")

        self.row += 1

        # Log output at the bottom spanning both columns
        tk.Label(self.root, text="Log Output:").grid(row=self.row, column=0, columnspan=2, sticky="w")
        self.log_output = scrolledtext.ScrolledText(self.root, height=10)
        self.log_output.grid(row=self.row, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.log_output.config(state=tk.DISABLED)  # Make log output read-only

        # Setup logging to text widget
        self.setup_logging()

    def add_general_options_widgets(self):
        frame = self.general_frame

        tk.Label(self.general_frame, text="Log Level:").grid(row=frame.row, column=0, sticky="w")
        tk.OptionMenu(self.general_frame, self.log_level_var, "info", "warning", "error", "debug").grid(
            row=frame.row, column=1, sticky="ew"
        )

        frame.new_row()
        tk.Checkbutton(self.general_frame, text="Dry Run", variable=self.dry_run_var).grid(row=frame.row, column=0, sticky="w")
        tk.Checkbutton(self.general_frame, text="Non-interactive", variable=self.noninteractive_var).grid(
            row=frame.row, column=1, sticky="w"
        )

        frame.new_row()
        tk.Label(self.general_frame, text="Source Directory:").grid(row=frame.row, column=0, sticky="w")
        tk.Entry(self.general_frame, textvariable=self.source_directory_var).grid(row=frame.row, column=1, sticky="ew")
        tk.Button(self.general_frame, text="Browse...", command=self.select_source_directory).grid(row=frame.row, column=2, sticky="ew")

        # YouTube Client Secrets File
        frame.new_row()
        tk.Label(self.general_frame, text="YouTube Client Secrets File:").grid(row=frame.row, column=0, sticky="w")
        tk.Entry(self.general_frame, textvariable=self.yt_client_secrets_file_var).grid(row=frame.row, column=1, sticky="ew")
        tk.Button(self.general_frame, text="Browse...", command=self.select_client_secrets_file).grid(row=frame.row, column=2, sticky="ew")

        # Input File Extensions
        frame.new_row()
        tk.Label(self.general_frame, text="Input File Extensions:").grid(row=frame.row, column=0, sticky="w")
        self.input_file_extensions_var = tk.StringVar(value=".mp4 .mov")  # Default value
        tk.Entry(self.general_frame, textvariable=self.input_file_extensions_var).grid(row=frame.row, column=1, sticky="ew")

        # Upload Batch Limit
        frame.new_row()
        tk.Label(self.general_frame, text="Upload Batch Limit:").grid(row=frame.row, column=0, sticky="w")
        self.upload_batch_limit_var = tk.IntVar(value=100)  # Default value
        tk.Entry(self.general_frame, textvariable=self.upload_batch_limit_var).grid(row=frame.row, column=1, sticky="ew")

        # YouTube Category ID
        frame.new_row()
        tk.Label(self.general_frame, text="YouTube Category ID:").grid(row=frame.row, column=0, sticky="w")
        tk.Entry(self.general_frame, textvariable=self.yt_category_id_var).grid(row=frame.row, column=1, sticky="ew")

        # YouTube Keywords
        frame.new_row()
        tk.Label(self.general_frame, text="YouTube Keywords:").grid(row=frame.row, column=0, sticky="w")
        tk.Entry(self.general_frame, textvariable=self.yt_keywords_var).grid(row=frame.row, column=1, sticky="ew")

    def add_youtube_title_widgets(self):
        frame = self.youtube_title_frame
        tk.Label(self.youtube_title_frame, text="Prefix:").grid(row=frame.row, column=0, sticky="w")
        tk.Entry(self.youtube_title_frame, textvariable=self.yt_title_prefix_var).grid(row=frame.row, column=1, sticky="ew")

        frame.new_row()
        tk.Label(self.youtube_title_frame, text="Suffix:").grid(row=frame.row, column=0, sticky="w")
        tk.Entry(self.youtube_title_frame, textvariable=self.yt_title_suffix_var).grid(row=frame.row, column=1, sticky="ew")

        frame.new_row()
        self.youtube_title_frame.add_find_replace_widgets("Find / Replace Patterns:")

    def add_youtube_description_widgets(self):
        frame = self.youtube_desc_frame
        tk.Label(self.youtube_desc_frame, text="Template File:").grid(row=frame.row, column=0, sticky="w")
        tk.Entry(self.youtube_desc_frame, textvariable=self.yt_desc_template_file_var).grid(row=frame.row, column=1, sticky="ew")

        frame.new_row()
        self.youtube_desc_frame.add_find_replace_widgets("Find / Replace Patterns:")

    def add_thumbnail_options_widgets(self):
        frame = self.thumbnail_frame
        tk.Label(self.thumbnail_frame, text="Filename Prefix:").grid(row=frame.row, column=0, sticky="w")
        tk.Entry(self.thumbnail_frame, textvariable=self.thumb_file_prefix_var).grid(row=frame.row, column=1, sticky="ew")

        frame.new_row()
        tk.Label(self.thumbnail_frame, text="Filename Suffix:").grid(row=frame.row, column=0, sticky="w")
        tk.Entry(self.thumbnail_frame, textvariable=self.thumb_file_suffix_var).grid(row=frame.row, column=1, sticky="ew")

        frame.new_row()
        tk.Label(self.thumbnail_frame, text="File Extensions:").grid(row=frame.row, column=0, sticky="w")
        tk.Entry(self.thumbnail_frame, textvariable=self.thumb_file_extensions_var).grid(row=frame.row, column=1, sticky="ew")

        frame.new_row()
        self.thumbnail_frame.add_find_replace_widgets("Find / Replace Patterns:")

    def setup_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        log_handler = TextHandler(self.log_output)
        log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(log_handler)

    def run_upload(self):
        # Collect values from GUI
        log_level_str = self.log_level_var.get()
        dry_run = self.dry_run_var.get()
        noninteractive = self.noninteractive_var.get()
        source_directory = self.source_directory_var.get()
        yt_client_secrets_file = self.yt_client_secrets_file_var.get()
        yt_category_id = self.yt_category_id_var.get()
        yt_keywords = self.yt_keywords_var.get().split()
        yt_desc_template_file = self.yt_desc_template_file_var.get()
        yt_title_prefix = self.yt_title_prefix_var.get()
        yt_title_suffix = self.yt_title_suffix_var.get()
        thumb_file_prefix = self.thumb_file_prefix_var.get()
        thumb_file_suffix = self.thumb_file_suffix_var.get()
        thumb_file_extensions = self.thumb_file_extensions_var.get().split()

        # Convert log level from string to logging module constant
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)

        # Initialize YouTubeBulkUpload with collected parameters
        youtube_bulk_upload = YouTubeBulkUpload(
            log_level=log_level,
            dry_run=dry_run,
            interactive_prompt=not noninteractive,
            source_directory=source_directory,
            youtube_client_secrets_file=yt_client_secrets_file,
            youtube_category_id=yt_category_id,
            youtube_keywords=yt_keywords,
            youtube_description_template_file=yt_desc_template_file,
            youtube_title_prefix=yt_title_prefix,
            youtube_title_suffix=yt_title_suffix,
            thumbnail_filename_prefix=thumb_file_prefix,
            thumbnail_filename_suffix=thumb_file_suffix,
            thumbnail_filename_extensions=thumb_file_extensions,
        )

        # Run the upload process in a separate thread to prevent GUI freezing
        upload_thread = threading.Thread(target=self.threaded_upload, args=(youtube_bulk_upload,))
        upload_thread.start()

    def select_client_secrets_file(self):
        filename = filedialog.askopenfilename(title="Select Client Secrets File", filetypes=[("JSON files", "*.json")])
        if filename:
            self.yt_client_secrets_file_var.set(filename)

    def select_source_directory(self):
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_directory_var.set(directory)

    def clear_log(self):
        self.log_output.config(state=tk.NORMAL)  # Enable text widget for editing
        self.log_output.delete("1.0", tk.END)
        self.log_output.config(state=tk.DISABLED)  # Disable text widget after clearing

    def threaded_upload(self, youtube_bulk_upload):
        try:
            uploaded_videos = youtube_bulk_upload.process()
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Upload complete! Videos uploaded: {len(uploaded_videos)}"))
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))


class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.config(state=tk.NORMAL)  # Enable text widget for editing
        self.text_widget.insert(tk.END, msg + "\n")
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)  # Disable text widget after updating


def main():
    root = tk.Tk()
    app = YouTubeBulkUploaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
