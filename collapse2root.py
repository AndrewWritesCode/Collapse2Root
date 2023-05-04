import os
import shutil
import tempfile
import zipfile
from fileMapper import FileMap
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog


try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)  # change to a 2 for multiple monitor resolutions (will cause scaling)
except ImportError:
    pass


class FileMapperFrame(ttk.Frame):
    def __init__(self, parent):

        ttk.Frame.__init__(self, parent, padding="10 10 10 10")

        self.parent = parent
        self.large_btn_width = 50

        self.title = tk.StringVar()
        self.title.set("Collapse Files to Root")
        self.using_zip = tk.BooleanVar()
        self.using_zip.set(False)

        self.target_prompt = tk.StringVar()
        self.target_prompt.set("Define Directory to Collapse:")

        self.root_dir = tk.StringVar()
        self.json_path = tk.StringVar()

        self.using_omits = True
        self.using_omits_toggle = tk.StringVar()
        self.using_omits_toggle.set("[TOGGLE] Excluding the following extensions:")
        self.ext_omits = tk.StringVar()
        self.ext_omits_list = []
        self.ext_omits_submitted = tk.StringVar()

        self.status = tk.StringVar()
        self.status.set("Status: Awaiting Generation")

        self.has_generated = False

        self.init_components()

    def init_components(self):
        self.pack()
        self.init_title_frame()
        self.init_main_frame()
        self.init_omit_frame()
        self.init_generate_frame()
        self.init_output_frame()

    def init_title_frame(self):
        window_name = "Collapse2Root"
        frame = ttk.Frame(self)
        frame.grid(column=0, row=0, padx=2, pady=2)
        ttk.Label(frame, textvariable=self.title, font=("Arial", 28)).grid(column=0, row=0)
        ttk.Checkbutton(frame, text="Save as Zip", variable=self.using_zip,
                        onvalue=True, offvalue=False, command=self.title_toggle).grid(column=2, row=0, sticky=tk.E)
        self.winfo_toplevel().title(window_name)

    def init_main_frame(self):
        frame = ttk.Frame(self)
        frame.grid(column=0, row=1, padx=2, pady=2)

        entry_width = 65

        ttk.Label(frame, textvariable=self.target_prompt).grid(column=0, row=0, sticky=tk.W)
        ttk.Entry(frame, width=entry_width, textvariable=self.root_dir).grid(column=0, row=1, sticky=tk.W)
        ttk.Button(frame, text="Browse", command=self.get_root_dir).grid(column=1, row=1)

        ttk.Label(frame, text="Save As:").grid(column=0, row=3, sticky=tk.W)
        ttk.Entry(frame, width=entry_width, textvariable=self.json_path).grid(column=0, row=4, sticky=tk.W)
        ttk.Button(frame, text="Save As", command=self.get_json_path).grid(column=1, row=4)

        ttk.Label(frame, text="Comma Separated List of Extensions to Filter (such as .txt, .py, .etc):") \
            .grid(column=0, row=6, sticky=tk.W)
        ttk.Entry(frame, width=entry_width, textvariable=self.ext_omits).grid(column=0, row=7, sticky=tk.W)
        ttk.Button(frame, text="Submit", command=self.parse_omits).grid(column=1, row=7)

    def init_omit_frame(self):
        frame = ttk.Frame(self)
        frame.grid(column=0, row=2, padx=2, pady=2)

        ttk.Button(frame, textvariable=self.using_omits_toggle, command=self.omit_filter_toggle) \
            .grid(column=0, row=0, sticky=tk.W)
        ttk.Label(frame, textvariable=self.ext_omits_submitted, width=40).grid(column=1, row=0, sticky=tk.W)

    def title_toggle(self):
        if self.using_zip.get():
            self.target_prompt.set("Define a Zipfile to FileMap:")
        else:
            self.target_prompt.set("Define Directory to FileMap:")

    def omit_filter_toggle(self):
        if self.using_omits:
            self.using_omits_toggle.set("[TOGGLE] Including the following extensions:")
            self.using_omits = False
        else:
            self.using_omits_toggle.set("[TOGGLE] Excluding the following extensions:")
            self.using_omits = True

    def get_root_dir(self):
        if self.using_zip.get():
            root_dir = filedialog.askopenfilename(defaultextension=".*", filetypes=[("Zip", "*.zip")])
            self.root_dir.set(root_dir)
        else:
            root_dir = filedialog.askdirectory()
            self.root_dir.set(root_dir)

    def get_json_path(self):
        if self.using_zip.get():
            json_path = filedialog.asksaveasfilename(defaultextension=".*", filetypes=[("Zip", "*.zip")])
            self.json_path.set(json_path)
        else:
            json_path = filedialog.askdirectory()
            self.json_path.set(json_path)

    def parse_omits(self):
        o = self.ext_omits.get()
        o = o.replace(' ', '')
        if o != '':
            self.ext_omits_list = o.split(',')
            omit_text = ''
            for omit in self.ext_omits_list:
                if not omit.startswith('.'):
                    omit = f'.{omit}'
                omit_text += omit
                omit_text += ', '
            omit_text = omit_text[:-2]
            self.ext_omits_submitted.set(omit_text)
        else:
            self.ext_omits_list = []
            self.ext_omits_submitted.set("")

    def init_generate_frame(self):
        frame = ttk.Frame(self)
        frame.grid(column=0, row=3, padx=2, pady=5)

        ttk.Button(frame, width=self.large_btn_width, text="Collapse Files to Root",
                   command=self.generate).grid(column=0, row=0, pady=5)

    def collapse2root(self, file_map):
        os.chdir(self.root_dir.get())
        if not self.using_zip.get():
            for filename in file_map:
                i = 1
                for filepath in file_map[filename]["filepaths"]:
                    f_name = os.path.splitext(filename)
                    dst_name = os.path.join(self.json_path.get(), f"{f_name[0]}-{i}{f_name[1]}")
                    i += 1
                    shutil.copy(filepath, dst_name)
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                for filename in file_map:
                    i = 1
                    for filepath in file_map[filename]["filepaths"]:
                        f_name = os.path.splitext(filename)
                        dst_name = os.path.join(temp_dir, f"{f_name[0]}-{i}{f_name[1]}")
                        i += 1
                        shutil.copy(filepath, dst_name)
                shutil.make_archive(os.path.splitext(self.json_path.get())[0], 'zip', temp_dir)

    def generate(self):
        if (self.root_dir.get() != "") and (self.json_path.get() != ""):
            self.status.set("Status: RUNNING")

            if self.using_omits:
                file_map = FileMap(self.root_dir.get(),
                                   extensions2omit=self.ext_omits_list)
            else:
                file_map = FileMap(self.root_dir.get(),
                                   extensions2include=self.ext_omits_list)
            if file_map.exists():
                # file_map.export_map_to_json(self.json_path.get())
                self.collapse2root(file_map.map)

                self.has_generated = True
                self.status.set("Status: DONE!")
            else:
                self.status.set("STATUS: Can\'t Access Root Dir!")
        elif self.root_dir.get() == "":
            self.status.set("Status: Root Dir Undefined!")
        else:
            self.status.set("Status: Start Root Undefined!")

    def init_output_frame(self):
        frame = ttk.Frame(self)
        frame.grid(column=0, row=4, padx=2, pady=5)
        ttk.Label(frame, textvariable=self.status, font=("Arial", 24)).grid(column=0, row=0)
        ttk.Button(frame, width=self.large_btn_width,
                   text="Go to Output Directory", command=self.go_to_output_dir).grid(column=0, row=1, pady=8)

    def go_to_output_dir(self):
        if self.has_generated:
            try:
                os.startfile(os.path.dirname(self.json_path.get()))
            except IsADirectoryError:
                self.status.set("Status: Output Dir Not Found!")

    def go_to_file(self):
        if self.has_generated:
            try:
                os.startfile(self.json_path.get())
            except IsADirectoryError:
                self.status.set("Status: Output File Not Found!")


def main():
    root = tk.Tk()
    FileMapperFrame(root)
    if os.path.exists("FileMapper_icon.ico"):
        root.iconbitmap("FileMapper_icon.ico")
    root.mainloop()


if __name__ == "__main__":
    main()
