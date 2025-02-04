from tkinter import *
import ttkbootstrap as ttk
import subprocess
import csv
import os
from ttkbootstrap.dialogs import Messagebox
import threading
import time


root = ttk.Window().winfo_toplevel()
root.attributes('-topmost', True)
root.title("Content Cache Manager")
root.geometry("800x800")
style = ttk.Style()
style.configure("Header.TLabel", font=("Helvetica", 24, "bold"))
style.configure("SubHeader.TLabel", font=("Helvetica", 12))
root.config()

current_widget = None  # To track the currently displayed widget
progress_running = False  # Flag to track progress status

def run_command(command):
    """Runs a terminal command and returns the output."""
    try:
        return subprocess.check_output(command, shell=True, text=True)
    except Exception as e:
        print(f"Error running command '{command}': {e}")
        return None

def fetch_keys(command, keys):
    try:
        result = run_command(command)
        if not result:
            return []

        fetched_values = []
        lines = result.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i].strip()  # Clean the current line

            for key in keys:
                if line.startswith(f"{key}:"):
                    value = line.split(":", 1)[1].strip()

                    while i + 1 < len(lines) and ":" not in lines[i + 1]:
                        value += " " + lines[i + 1].strip()
                        i += 1

                    fetched_values.append((key, value))
                    break
            i += 1

        return fetched_values

    except Exception as e:
        print(f"Error: {e}")
        return []

def fetch_multiline(command, keys):
    try:
        result = run_command(command)
        if not result:
            return []

        fetched_values = []
        lines = result.splitlines()
        i = 0

        printed_keys = {key: False for key in keys}  # Track printed keys

        while i < len(lines):
            line = lines[i].strip()  # Clean the current line

            for key in keys:
                if line.startswith(f"{key}:"):
                    value = line.split(":", 1)[1].strip()
                    if value != "(none)":
                        next_line = lines[i + 1].strip()
                        # i += 1
                        if "," in next_line:
                            parts = next_line.split(",")
                            if not printed_keys[key]:
                                fetched_values.append((key, parts[0].strip()))
                                printed_keys[key] = True
                            # print(val)
                            for part in parts[1:]:
                                fetched_values.append(("", part.strip()))
                            i += 1
                        else:
                            value += " " + next_line
                            i += 1  # Skip the next line as it has been appended
                            if not printed_keys[key]:
                                fetched_values.append((key, value))
                                printed_keys[key] = True
                            else:
                                fetched_values.append((key, value))
                    else:
                        if not printed_keys[key]:
                            fetched_values.append((key, value))
                            printed_keys[key] = True
                    break
            i += 1
        return fetched_values

    except Exception as e:
        print(f"Error: {e}")
        return []

def status():
    global current_widget
    command = "AssetCacheManagerUtil status"
    keys_to_fetch = ["ServerGUID", "Activated", "Port", "RestrictedMedia","CacheStatus", "StartupStatus", "PrivateAddresses", "TetheratorStatus", "StartupStatus", "PublicAddress", "RegistrationStatus"]
    fetched_values = fetch_keys(command, keys_to_fetch)

    # Remove existing widget
    if current_widget:
        current_widget.destroy()

    # Create new Treeview
    tv = ttk.Treeview(bootstyle='info', master=tree_frame, columns=(1, 2), height=10)
    tv.heading("1", text="Key")
    tv.heading("2", text="Value")
    tv.pack(fill=BOTH, expand=True)
    tv['show'] = 'headings'

    for values in fetched_values:
        tv.insert("", "end", values=(" ", " "))  # Empty row for spacing
        tv.insert("", "end", values=values)

    current_widget = tv  # Track the widget

def cache_data():
    global current_widget
    command = "AssetCacheManagerUtil status"
    keys_to_fetch = ["CacheStatus", "CacheFree", "CacheLimit", "CacheUsed"]
    fetched_values = fetch_keys(command, keys_to_fetch)

    # Remove existing widget
    if current_widget:
        current_widget.destroy()

    # Create new Treeview
    tv = ttk.Treeview(bootstyle='info', master=tree_frame, columns=(1, 2), height=10)
    tv.heading("1", text="Key")
    tv.heading("2", text="Value")
    tv.pack(fill=BOTH, expand=True)
    tv['show'] = 'headings'

    for values in fetched_values:
        tv.insert("", "end", values=(" ", " "))  # Empty row for spacing
        tv.insert("", "end", values=values)

    current_widget = tv

def cache_usage():
    global current_widget
    command = "AssetCacheManagerUtil status"
    keys_to_fetch = ["CacheUsed", "CacheDetails", "iCloud", "Mac Software", "iOS Software",
                     "Other"]
    fetched_values = fetch_keys(command, keys_to_fetch)

    # Remove existing widget
    if current_widget:
        current_widget.destroy()

    # Create new Treeview
    tv = ttk.Treeview(bootstyle='info', master=tree_frame, columns=(1, 2), height=10)
    tv.heading("1", text="Key")
    tv.heading("2", text="Value")
    tv.pack(fill=BOTH, expand=True)
    tv['show'] = 'headings'

    for values in fetched_values:
        tv.insert("", "end", values=(" ", " "))  # Empty row for spacing
        tv.insert("", "end", values=values)

    current_widget = tv

#use if required in future
def meter_use():
    global current_widget
    command = "AssetCacheManagerUtil status"

    actual_cache_used = 0.0
    cache_limit = 0.0

    result = run_command(command)
    if result:
        lines = result.splitlines()
        for line in lines:
            if "CacheFree:" in line:
                actual_cache_used = float(line.split(":")[1].strip().split()[0])
            elif "CacheLimit:" in line:
                cache_limit = float(line.split(":")[1].strip().split()[0])

    cache_used_percentage = (actual_cache_used / cache_limit) * 100 if cache_limit > 0 else 0
    cache_used_percentage = round(cache_used_percentage, 1)

    # Remove existing widget
    if current_widget:
        current_widget.destroy()

    # Create Meter widget
    meter = ttk.Meter(
        master=tree_frame,
        metersize=320,
        textright="%",
        amountused=cache_used_percentage,
        amounttotal=100,
        stripethickness=20,
        bootstyle="primary",
        # subtextstyle="warning",
        textfont=("Calibri", 30, "bold"),
        subtext=f"{actual_cache_used:.2f} GB of {cache_limit:.2f} GB used",
        subtextfont=("Calibri", 12),
    )
    meter.pack(fill=BOTH, expand=True, pady=50)

    current_widget = meter

def bytes_transfer():
    global current_widget
    command = "AssetCacheManagerUtil status"
    keys_to_fetch = ["TotalBytesAreSince", "TotalBytesDropped", "TotalBytesImported",
                     "TotalBytesReturnedToChildren", "TotalBytesReturnedToClients",
                     "TotalBytesReturnedToPeers", "TotalBytesStoredFromOrigin",
                     "TotalBytesStoredFromParents", "TotalBytesStoredFromPeers"]
    fetched_values = fetch_keys(command, keys_to_fetch)

    # Remove existing widget
    if current_widget:
        current_widget.destroy()

    # Create new Treeview
    tv = ttk.Treeview(bootstyle='info', master=tree_frame, columns=(1, 2), height=10)
    tv.heading("1", text="Key")
    tv.heading("2", text="Value")
    tv.pack(fill=BOTH, expand=True)
    tv['show'] = 'headings'

    for values in fetched_values:
        tv.insert("", "end", values=(" ", " "))  # Empty row for spacing
        tv.insert("", "end", values=values)

    current_widget = tv

def other_data():
    global current_widget
    command = "AssetCacheManagerUtil status"
    keys_to_fetch = ["Peers", "Parents"]
    fetched_values = fetch_multiline(command, keys_to_fetch)

    # Remove existing widget
    if current_widget:
        current_widget.destroy()

    # Create new Treeview
    tv = ttk.Treeview(bootstyle='info', master=tree_frame, columns=(1, 2), height=10)
    tv.heading("1", text="Key")
    tv.heading("2", text="Value")
    tv.pack(fill=BOTH, expand=True)
    tv['show'] = 'headings'

    for values in fetched_values:
        tv.insert("", "end", values=(" ", " "))  # Empty row for spacing
        tv.insert("", "end", values=values)

    current_widget = tv

def cache_locator():
    global current_widget
    command = "AssetCacheManagerUtil settings"
    keys_to_fetch = ["DataPath"]
    fetched_values = fetch_keys(command, keys_to_fetch)

    # Remove existing widget
    if current_widget:
        current_widget.destroy()

    # Create new Treeview
    tv = ttk.Treeview(bootstyle='info', master=tree_frame, columns=(1, 2), height=10)
    tv.heading("1", text="Key")
    tv.heading("2", text="Value")
    tv.pack(fill=BOTH, expand=True)
    tv['show'] = 'headings'

    for values in fetched_values:
        tv.insert("", "end", values=(" ", " "))  # Empty row for spacing
        tv.insert("", "end", values=values)

    current_widget = tv

def view_settings():
    global current_widget
    command = "AssetCacheManagerUtil settings"
    keys_to_fetch = ["AllowPersonalCaching", "AllowSharedCaching", "AllowTetheredCaching",
                     "CacheLimit", "ListenRangesOnly", "LocalSubnetsOnly", "ParentSelectionPolicy",
                     "PeerLocalSubnetsOnly"]
    fetched_values = fetch_keys(command, keys_to_fetch)

    # Remove existing widget
    if current_widget:
        current_widget.destroy()

    # Create new Treeview
    tv = ttk.Treeview(bootstyle='info', master=tree_frame, columns=(1, 2), height=10)
    tv.heading("1", text="Key")
    tv.heading("2", text="Value")
    tv.pack(fill=BOTH, expand=True)
    tv['show'] = 'headings'

    for values in fetched_values:
        tv.insert("", "end", values=(" ", " "))  # Empty row for spacing
        tv.insert("", "end", values=values)

    current_widget = tv  # Track the widget

def show_custom_message(msg, title):
    top = Toplevel(tree_frame)  # Attach to tree_frame
    top.geometry("300x150")  # Set custom size
    top.title(title)

    # Get root window position and size
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()

    # Calculate x and y for centering the window
    x = root_x + (root_width // 2) - (300 // 2)
    y = root_y + (root_height // 2) - (150 // 2)

    # Set the position of the Toplevel window
    top.geometry(f"300x150+{x}+{y}")

    Label(top, text=msg, font=("Calibri", 14)).pack(pady=40)
    ttk.Button(top, bootstyle="success", text="OK", command=top.destroy).pack(pady=10)

def clear_cache():
    options = ["Clear all", "Clear only personal (iCloud)", "Clear only shared"]
    myOption = StringVar()
    global current_widget

    def clear():
        osd = myOption.get()
        if osd == "Clear all":
            msg = "All cache Cleared"
            cmd = "osascript -e 'do shell script \"AssetCacheManagerUtil flushCache\" with administrator privileges'"
            subprocess.run(cmd, shell=True)
            show_custom_message(msg, osd)
        elif osd == "Clear only personal (iCloud)":
            msg = "iCloud Cache Cleared"
            cmd = "osascript -e 'do shell script \"AssetCacheManagerUtil flushPersonalCache\" with administrator privileges'"
            subprocess.run(cmd, shell=True)
            show_custom_message(msg, osd)
        elif osd == "Clear only shared":
            msg = "Shared Cache Cleared"
            cmd = "osascript -e 'do shell script \"AssetCacheManagerUtil flushSharedCache\" with administrator privileges'"
            subprocess.run(cmd, shell=True)
            show_custom_message(msg, osd)

    # Remove existing widget
    if current_widget:
        current_widget.destroy()

    # Create new Treeview
    tv = ttk.Labelframe(master=tree_frame, text="Choose which cache to clear")
    for option in options:
        (ttk.Radiobutton(master=tv, bootstyle='danger', variable=myOption, text=option, value=option)
         .pack(pady=20, anchor="w", padx=60))

    tv.pack(fill=BOTH, expand=True)
    ttk.Button(bootstyle="danger-outline", master=tv, command=clear, text="Clear").pack(padx=120, pady=20, anchor="w")

    current_widget = tv

# Function to show progress bar
def show_progress():
    progress_frame = ttk.Frame(master=tree_frame)
    progress_frame.pack(fill=BOTH, expand=True, pady=10)
    progress = ttk.Progressbar(master=progress_frame, bootstyle="primary-striped", mode="determinate")
    label = ttk.Label(master=progress_frame, text="Processing...")
    progress.pack(fill=X, expand=True)
    label.pack()
    progress.start(50)
    return progress_frame, progress

# Function to display logs (runs in a separate thread)
def get_log():
    def fetch_logs():
        global current_widget
        command = "log show --predicate 'subsystem == \"com.apple.AssetCache\"' --info"

        # Remove existing widget
        if current_widget:
            current_widget.destroy()

        progress_frame, progress = show_progress()
        root.update()

        result = run_command(command)
        progress.stop()
        progress_frame.destroy()

        if not result:
            Messagebox.show_error("No logs found.", "Error")
            return

        # Create new Treeview with scrollbars
        frame = ttk.Frame(master=tree_frame)
        frame.pack(fill=BOTH, expand=True)

        x_scroll = ttk.Scrollbar(master=frame, orient=HORIZONTAL)
        y_scroll = ttk.Scrollbar(master=frame, orient=VERTICAL)

        columns = (
        "timestamp", "thread_id", "type", "activity_id", "pid", "tti", "Process", "Subsystem", "Category", "Message")
        tv = ttk.Treeview(master=frame, columns=columns, height=10, xscrollcommand=x_scroll.set,
                          yscrollcommand=y_scroll.set, bootstyle='info')

        for col in columns:
            tv.heading(col, text=col)
            tv.column(col, width=120)

        tv['show'] = 'headings'

        x_scroll.config(command=tv.xview)
        y_scroll.config(command=tv.yview)

        x_scroll.pack(side=BOTTOM, fill=X)
        y_scroll.pack(side=RIGHT, fill=Y)
        tv.pack(fill=BOTH, expand=True)

        # Populate data
        lines = result.splitlines()
        for line in lines:
            parts = line.split(None, 9)  # Split into 10 parts
            if len(parts) == 10:
                tv.insert("", "end", values=parts)

        current_widget = frame

    threading.Thread(target=fetch_logs, daemon=True).start()

# Function to download logs (runs in a separate thread)
def download_logs():
    def fetch_and_save_logs():
        global current_widget
        command = "log show --predicate 'subsystem == \"com.apple.AssetCache\"' --info"

        # Remove existing widget
        if current_widget:
            current_widget.destroy()

        progress_frame, progress = show_progress()
        root.update()

        result = run_command(command)
        progress.stop()
        progress_frame.destroy()

        if not result:
            Messagebox.show_error("No logs found to download.", "Error")
            return

        desktop_path = os.path.expanduser("~/Desktop/logs.csv")
        with open(desktop_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["timestamp", "thread_id", "type", "activity_id", "pid", "tti", "Process", "Subsystem", "Category",
                 "Message"])

            lines = result.splitlines()
            for line in lines:
                parts = line.split(None, 9)
                if len(parts) == 10:
                    writer.writerow(parts)

        show_custom_message("File downloaded successfully to your Desktop", title="Download Logs")
        # Messagebox.show_info("File downloaded successfully to your Desktop", "Success")

    threading.Thread(target=fetch_and_save_logs, daemon=True).start()


def check_network():
    def fetch_network_data():
        global current_widget, progress_running
        command = "networkQuality"
        keys_to_fetch = ["Uplink capacity", "Downlink capacity", "Responsiveness", "Idle Latency"]

        # Remove existing widget
        if current_widget:
            current_widget.destroy()

        # Show circular progress bar
        progress_frame = ttk.Frame(master=tree_frame)
        progress_frame.pack(fill=BOTH, expand=True, pady=10)

        progress = ttk.Meter(
            master=progress_frame,
            metersize=320,  # Increased size
            stripethickness=2,
            bootstyle="success",
            amountused=0,
            amounttotal=100,
            interactive=False,
            subtext="Checking..."
        )
        progress.pack()

        progress_running = True  # Set flag to indicate progress is running

        def update_progress():
            for i in range(0, 101, 2):  # Slower progression
                if not progress_running:
                    return  # Stop updating if progress is no longer valid
                progress.configure(amountused=i)
                root.update()
                time.sleep(0.35)  # Increased delay for slower animation

        progress_thread = threading.Thread(target=update_progress, daemon=True)
        progress_thread.start()

        # Fetch network data
        fetched_values = fetch_keys(command, keys_to_fetch)

        progress_running = False  # Stop progress updates
        progress_frame.destroy()  # Now safe to destroy progress frame

        # Create frame for Treeview
        frame = ttk.Frame(master=tree_frame)
        frame.pack(fill=BOTH, expand=True)

        # Create new Treeview
        tv = ttk.Treeview(bootstyle='info', master=frame, columns=(1, 2), height=10)
        tv.heading("1", text="Key")
        tv.heading("2", text="Value")
        tv.pack(fill=BOTH, expand=True)
        tv['show'] = 'headings'

        # Insert values into Treeview
        for values in fetched_values:
            tv.insert("", "end", values=(" ", " "))  # Empty row for spacing
            tv.insert("", "end", values=values)

        current_widget = frame  # Track the widget

    threading.Thread(target=fetch_network_data, daemon=True).start()

entries_frame = ttk.Frame(master=root, padding=20)
entries_frame.pack(side=TOP, fill=X)
title = ttk.Label(master=entries_frame, text="Content Cache Manager", font=("Helvetica", 24, "bold"))
sub_title = ttk.Label(master=entries_frame, text="Monitor and manage your content cache efficiently", font=("Helvetica", 12))
title.grid(row=0, padx=10, pady=(10,0))
sub_title.grid(row=1, padx=10, pady=(5,20))

# Buttons Frame
btn_frame = ttk.LabelFrame(master=entries_frame, text="Choose Action", padding=20)
btn_frame.grid(row=2, column=0)

ttk.Button(bootstyle="success-outline", master=btn_frame, command=status, text="Check Status").grid(row=0, column=0, padx=5, pady=10)
ttk.Button(bootstyle="primary-outline", master=btn_frame, command=cache_data, text="Cache Data").grid(row=0, column=1)
ttk.Button(bootstyle="info-outline", master=btn_frame, command=cache_usage, text="Check Usage").grid(row=0, column=2, padx=5, pady=10)
ttk.Button(bootstyle="secondary-outline", master=btn_frame, command=bytes_transfer, text="Bytes Transfer").grid(row=0, column=3, padx=5)
ttk.Button(bootstyle="dark-outline", master=btn_frame, command=cache_locator, text="Cache Locator").grid(row=0, column=4)

ttk.Button(bootstyle="success-outline", master=btn_frame, command=view_settings, text="View Settings").grid(row=1, column=0, padx=5, pady=10)
ttk.Button(bootstyle="danger-outline", master=btn_frame, command=clear_cache, text="Clear Cache").grid(row=1, column=1)
ttk.Button(bootstyle="dark-outline", master=btn_frame, command=other_data, text="Other Data").grid(row=1, column=2)
ttk.Button(bootstyle="secondary-outline", master=btn_frame, command=download_logs, text="Download Logs").grid(row=1, column=3, padx=5)
ttk.Button(bootstyle="info-outline", master=btn_frame, command=get_log, text="See Logs").grid(row=1, column=4)
ttk.Button(bootstyle="info-outline", master=btn_frame, command=check_network, text="Check Network").grid(row=1, column=5)

# Result Frame (Dynamic Content)
tree_frame = ttk.LabelFrame(master=root, padding=20, text="Result")
tree_frame.place(x=20, y=290, width=750, height=400)

# Footer
footer = ttk.Frame(master=root)
footer.pack(side=BOTTOM, fill=X, pady=10)
ttk.Label(master=footer, text="Version 2.0", bootstyle="secondary").pack(side=LEFT, padx=20)
ttk.Label(master=footer, text="Prepared by LJ",bootstyle="secondary").pack(side=RIGHT, padx=20)

root.mainloop()
