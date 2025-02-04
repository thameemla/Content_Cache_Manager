import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import csv
import os
import json
from datetime import datetime
import threading
import re


class ContentCacheMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Content Cache Monitor")
        self.root.geometry("1200x800")

        # Configure styles
        self.style = ttk.Style()
        self.style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'))
        self.style.configure('SubHeader.TLabel', font=('Helvetica', 14, 'bold'))
        self.style.configure('Status.TLabel', font=('Helvetica', 12))
        self.style.configure('TableHeader.TLabel', font=('Helvetica', 12, 'bold'))
        self.style.configure('TableValue.TLabel', font=('Helvetica', 12))
        self.style.configure('Custom.TButton', padding=5)

        # Create main container
        self.main_container = ttk.Frame(self.root, padding="20")
        self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create tabs
        self.tab_control = ttk.Notebook(self.main_container)

        # Dashboard tab
        self.dashboard_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.dashboard_tab, text='Dashboard')

        # Logs tab
        self.logs_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.logs_tab, text='Logs')

        self.tab_control.pack(expand=1, fill="both")

        self.setup_dashboard()
        self.setup_logs_tab()

        # Initialize cache status
        self.update_cache_status()

    def setup_dashboard(self):
        # Main frame with scrollbar
        main_frame = ttk.Frame(self.dashboard_tab)
        main_frame.pack(fill="both", expand=True)

        # Create canvas with scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)

        # Scrollable frame
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Header
        header = ttk.Label(self.scrollable_frame, text="Content Cache Status",
                           style='Header.TLabel')
        header.pack(pady=(0, 20))

        # Create frames for different sections
        self.status_frame = ttk.LabelFrame(self.scrollable_frame, text="Cache Status", padding=10)
        self.status_frame.pack(fill="x", padx=10, pady=5)

        # Grid configuration for status frame
        self.status_frame.columnconfigure(1, weight=1)
        self.status_frame.columnconfigure(3, weight=1)

        # Control frame
        control_frame = ttk.Frame(self.scrollable_frame)
        control_frame.pack(fill="x", pady=10)

        # Refresh button
        refresh_btn = ttk.Button(control_frame, text="↻ Refresh Status",
                                 command=self.update_cache_status, style='Custom.TButton')
        refresh_btn.pack(side="right", padx=5)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_logs_tab(self):
        # Header
        header = ttk.Label(self.logs_tab, text="Content Cache Log Manager",
                           style='Header.TLabel')
        header.pack(pady=(0, 20))

        # Configure custom styles
        style = ttk.Style()
        style.configure('Custom.TButton', padding=(10, 10))  # Adjust padding to increase height

        # Log frame
        log_frame = ttk.LabelFrame(self.logs_tab, text="Download Logs", padding="15")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Info label
        info_label = ttk.Label(log_frame,
                               text="Download and process content cache logs. Results will be saved as CSV.",
                               style='Status.TLabel')
        info_label.pack(pady=(0, 10))

        # Download button
        download_btn = ttk.Button(log_frame, text="📥 Download Logs",
                                  command=self.download_logs, style='Custom.TButton')
        download_btn.pack(pady=5)

        # Status label
        self.log_status_label = ttk.Label(log_frame, text="", style='Status.TLabel')
        self.log_status_label.pack(pady=10)

        # Progress bar
        self.progress_bar = ttk.Progressbar(log_frame, mode='indeterminate')

    def create_status_row(self, key, value, row):
        # Create label
        label = ttk.Label(self.status_frame, text=key, style='TableHeader.TLabel')
        label.grid(row=row, column=0, sticky="w", padx=10, pady=5)

        # Create value display
        value_display = ttk.Label(self.status_frame, text=str(value),
                                  style='TableValue.TLabel', wraplength=400)
        value_display.grid(row=row, column=1, sticky="w", padx=10, pady=5)

        return value_display

    def parse_status_output(self, output):
        status_dict = {}
        lines = output.strip().split('\n')
        current_key = None

        for line in lines:
            line = line.rstrip()
            if not line:
                continue

            # Remove "Content caching status:" header
            if line.startswith("Content caching status:"):
                continue

            # Check for main key-value pairs
            if ':' in line:
                parts = line.split(':', 1)
                key = parts[0].strip()
                value = parts[1].strip()

                # Handle empty or "none" values
                if value in ['(none)', '']:
                    value = 'None'

                # Store the key-value pair and set current_key
                status_dict[key] = value
                current_key = key
            else:
                # Handle sub-items or lines without a key
                if current_key:
                    # If the current key's value is "None", initialize as a list
                    if status_dict[current_key] == 'None':
                        status_dict[current_key] = []
                    elif not isinstance(status_dict[current_key], list):
                        # If it's not a list, convert the value into a list
                        status_dict[current_key] = [status_dict[current_key]]

                    # Append the line to the current key's value
                    status_dict[current_key].append(line.strip())

        return status_dict

    def update_cache_status(self):
        try:
            # Clear existing status items
            for widget in self.status_frame.winfo_children():
                widget.destroy()

            result = subprocess.run(['assetcachemanagerutil', 'status'],
                                    capture_output=True, text=True)

            if result.returncode == 0:
                status_dict = self.parse_status_output(result.stdout)

                # Display status items in a grid layout
                row = 0
                col = 0
                items_per_column = len(status_dict) // 2 + len(status_dict) % 2

                for key, value in status_dict.items():
                    # Format list values
                    if isinstance(value, list):
                        value = '\n'.join(value)

                    # Color code certain status values
                    style = 'TableValue.TLabel'
                    if key in ['CacheStatus', 'StartupStatus'] and value == 'OK':
                        value = '✅ ' + value
                    elif value == 'true':
                        value = '✅ Enabled'
                    elif value == 'false':
                        value = '❌ Disabled'

                    # Create status row
                    if row < items_per_column:
                        self.create_status_row(key, value, row)
                    else:
                        # Start new column
                        label = ttk.Label(self.status_frame, text=key, style='TableHeader.TLabel')
                        label.grid(row=row - items_per_column, column=2, sticky="w", padx=10, pady=5)

                        value_display = ttk.Label(self.status_frame, text=str(value),
                                                  style=style, wraplength=400)
                        value_display.grid(row=row - items_per_column, column=3, sticky="w", padx=10, pady=5)

                    row += 1
            else:
                messagebox.showerror("Error", "Failed to get cache status")

        except Exception as e:
            messagebox.showerror("Error", f"Error updating cache status: {str(e)}")

    def parse_log_line(self, line):
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+[+-]\d{4})\s+' + \
                  r'(0x[0-9a-f]+)\s+(\w+)\s+(0x[0-9a-f]+)\s+(\d+)\s+(\d+)\s+' + \
                  r'(\w+):\s+\[([\w\.]+):[\w]+\]\s+(.+)'

        match = re.match(pattern, line)
        if match:
            return {
                'timestamp': match.group(1),
                'thread_id': match.group(2),
                'type': match.group(3),
                'activity_id': match.group(4),
                'pid': match.group(5),
                'ttl': match.group(6),
                'process': match.group(7),
                'subsystem': match.group(8),
                'message': match.group(9)
            }
        return None

    def download_logs(self):
        def run_log_command():
            try:
                self.progress_bar.pack(pady=10)
                self.progress_bar.start(10)
                self.log_status_label.config(text="Downloading logs...")

                log_command = ['log', 'show', '--predicate', 'subsystem == "com.apple.AssetCache"']
                result = subprocess.run(log_command, capture_output=True, text=True)

                if result.returncode == 0:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.expanduser(f"~/Desktop/content_cache_logs_{timestamp}.csv")

                    with open(filename, 'w', newline='') as csvfile:
                        fieldnames = ['timestamp', 'thread_id', 'type', 'activity_id',
                                      'pid', 'ttl', 'process', 'subsystem', 'message']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()

                        for line in result.stdout.split('\n'):
                            if line.strip():
                                parsed_data = self.parse_log_line(line.strip())
                                if parsed_data:
                                    writer.writerow(parsed_data)
                                else:
                                    writer.writerow({
                                        'timestamp': datetime.now().isoformat(),
                                        'message': line.strip(),
                                        'thread_id': '', 'type': '', 'activity_id': '',
                                        'pid': '', 'ttl': '', 'process': '', 'subsystem': ''
                                    })

                    self.log_status_label.config(
                        text=f"✅ Logs successfully saved to:\n{filename}")
                else:
                    self.log_status_label.config(text="❌ Error: Failed to retrieve logs")
                    messagebox.showerror("Error", "Failed to retrieve logs")

                self.progress_bar.stop()
                self.progress_bar.pack_forget()

            except Exception as e:
                self.log_status_label.config(text="❌ Error: Failed to process logs")
                messagebox.showerror("Error", f"Error processing logs: {str(e)}")
                self.progress_bar.stop()
                self.progress_bar.pack_forget()

        thread = threading.Thread(target=run_log_command)
        thread.daemon = True
        thread.start()


def main():
    root = tk.Tk()
    app = ContentCacheMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
