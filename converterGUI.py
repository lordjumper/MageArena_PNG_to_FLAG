import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
from PIL import Image, ImageTk
from png_converter import PixelGridConverter

class ConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MageArena Image to Flag Converter")
        self.root.geometry("1100x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.converter = PixelGridConverter()
        self.grid_data = ""
        self.preview_length = 1000
        self.showing_full = False
        self.preview_image = None
        
        self.setup_ui()
    
    def on_closing(self):
        self.root.destroy()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.create_file_section(left_frame)
        self.create_options_section(left_frame)
        self.create_output_section(left_frame)
        self.create_status_bar(main_frame)
        self.create_preview_section(right_frame)
        self.configure_grid_weights()
    
    def create_file_section(self, parent):
        file_frame = ttk.LabelFrame(parent, text="PNG File Selection", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(file_frame, text="Select PNG file:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        entry_frame = ttk.Frame(file_frame)
        entry_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        entry_frame.columnconfigure(0, weight=1)
        
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(entry_frame, textvariable=self.file_path_var, width=60)
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(entry_frame, text="Browse", command=self.browse_file).grid(row=0, column=1)
        
        self.convert_btn = ttk.Button(file_frame, text="Convert to Pixel Grid", command=self.convert_image_async)
        self.convert_btn.grid(row=2, column=0, pady=5)
        
        file_frame.columnconfigure(0, weight=1)
    
    def create_options_section(self, parent):
        options_frame = ttk.LabelFrame(parent, text="Options", padding="10")
        options_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.save_registry_var = tk.BooleanVar(value=True)
        self.preserve_colors_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Save to Unity Registry", 
                       variable=self.save_registry_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Preserve Original Colors", 
                       variable=self.preserve_colors_var).grid(row=0, column=1, sticky=tk.W, padx=(30, 0))
    
    def create_output_section(self, parent):
        output_frame = ttk.LabelFrame(parent, text="Pixel Grid Data Output", padding="10")
        output_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, width=85, height=15, state=tk.DISABLED)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        button_frame = ttk.Frame(output_frame)
        button_frame.grid(row=1, column=0, pady=(10, 0))
        
        self.show_more_btn = ttk.Button(button_frame, text="Show More", 
                                       command=self.toggle_output_view, state=tk.DISABLED)
        self.show_more_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.copy_btn = ttk.Button(button_frame, text="Copy to Clipboard", 
                                  command=self.copy_to_clipboard, state=tk.DISABLED)
        self.copy_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.export_btn = ttk.Button(button_frame, text="Export to Text File", 
                                    command=self.export_data, state=tk.DISABLED)
        self.export_btn.grid(row=0, column=2)
    
    def create_status_bar(self, parent):
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def create_preview_section(self, parent):
        preview_frame = ttk.LabelFrame(parent, text="Preview (100x66)", padding="10")
        preview_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        canvas_frame = ttk.Frame(preview_frame)
        canvas_frame.grid(row=0, column=0, padx=10, pady=10)
        
        self.preview_canvas = tk.Canvas(canvas_frame, width=200, height=132, bg='white', relief=tk.SUNKEN, bd=1)
        self.preview_canvas.grid(row=0, column=0)
        
        self.preview_label = ttk.Label(preview_frame, text="No preview available", anchor=tk.CENTER)
        self.preview_label.grid(row=1, column=0, pady=5)
        
        # Console log section
        console_frame = ttk.LabelFrame(preview_frame, text="Console Log", padding="5")
        console_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        
        self.console_text = scrolledtext.ScrolledText(
            console_frame, 
            wrap=tk.WORD, 
            width=30, 
            height=8, 
            state=tk.DISABLED,
            bg='#1e1e1e',
            fg='white',
            insertbackground='white'
        )
        self.console_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        credits_label = ttk.Label(preview_frame, text="Made by Jumper & Daikirai", anchor=tk.CENTER, font=("Arial", 8))
        credits_label.grid(row=3, column=0, pady=(5, 0))
        
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(2, weight=1)
    
    def configure_grid_weights(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        main_frame = self.root.grid_slaves()[0]
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        left_frame = main_frame.grid_slaves()[1]
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(2, weight=1)
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select PNG Image",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
    
    def convert_image_async(self):
        thread = threading.Thread(target=self.convert_image)
        thread.daemon = True
        thread.start()
    
    def convert_image(self):
        png_path = self.file_path_var.get().strip()
        
        if not png_path:
            self.root.after(0, lambda: messagebox.showerror("Error", "Please select a PNG file first."))
            return
        
        if not os.path.exists(png_path):
            self.root.after(0, lambda: messagebox.showerror("Error", "Selected file does not exist."))
            return
        
        self.root.after(0, lambda: self.set_converting_state(True))
        self.root.after(0, lambda: self.clear_console())
        self.root.after(0, lambda: self.log_to_console(f"Loading PNG image: {os.path.basename(png_path)}"))
        
        try:
            self.grid_data = self.converter.convert_png_to_pixel_grid(
                png_path,
                save_to_registry=self.save_registry_var.get(),
                save_to_file=False,
                preserve_colors=self.preserve_colors_var.get()
            )
            
            if self.grid_data:
                self.root.after(0, lambda: self.log_to_console("Image resized to 100x66"))
                self.root.after(0, lambda: self.log_to_console("Converting to UV coordinates..."))
                self.root.after(0, lambda: self.log_to_console("Serializing grid data..."))
                self.root.after(0, lambda: self.log_to_console("Conversion completed successfully!"))
                self.root.after(0, self.show_conversion_success)
            else:
                self.root.after(0, lambda: self.log_to_console("ERROR: Failed to convert image"))
                self.root.after(0, lambda: self.show_conversion_error("Failed to convert image."))
                
        except Exception as e:
            error_msg = f"Conversion failed: {str(e)}"
            self.root.after(0, lambda: self.log_to_console(f"ERROR: {error_msg}"))
            self.root.after(0, lambda: self.show_conversion_error(error_msg))
    
    def set_converting_state(self, converting):
        if converting:
            self.convert_btn.config(state=tk.DISABLED, text="Converting...")
            self.status_var.set("Converting image...")
        else:
            self.convert_btn.config(state=tk.NORMAL, text="Convert to Pixel Grid")
    
    def show_conversion_success(self):
        self.showing_full = False
        self.update_output_display()
        self.update_preview()
        
        self.show_more_btn.config(state=tk.NORMAL)
        self.copy_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.NORMAL)
        
        pixel_count = len(self.grid_data.split(','))
        self.status_var.set(f"Conversion completed! Grid size: {pixel_count} pixels")
        self.set_converting_state(False)
        messagebox.showinfo("Success", "Image converted successfully!")
    
    def update_output_display(self):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        
        if not self.grid_data:
            self.output_text.config(state=tk.DISABLED)
            return
        
        if self.showing_full or len(self.grid_data) <= self.preview_length:
            display_text = self.grid_data
            self.show_more_btn.config(text="Show Less" if self.showing_full else "Show More", 
                                     state=tk.DISABLED if len(self.grid_data) <= self.preview_length else tk.NORMAL)
        else:
            display_text = self.grid_data[:self.preview_length] + f"\n\n... ({len(self.grid_data) - self.preview_length} more characters) ..."
            self.show_more_btn.config(text="Show More", state=tk.NORMAL)
        
        self.output_text.insert(1.0, display_text)
        self.output_text.config(state=tk.DISABLED)
    
    def update_preview(self):
        try:
            if os.path.exists("resized_image.png"):
                img = Image.open("resized_image.png")
                img = img.resize((200, 132), Image.NEAREST)
                self.preview_image = ImageTk.PhotoImage(img)
                
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(100, 66, image=self.preview_image)
                self.preview_label.config(text="Quantized preview (scaled 2x)")
            else:
                self.preview_label.config(text="Preview not available")
        except Exception as e:
            self.preview_label.config(text="Error loading preview")
    
    def toggle_output_view(self):
        if len(self.grid_data) <= self.preview_length:
            return
        
        self.showing_full = not self.showing_full
        self.update_output_display()
    
    def show_conversion_error(self, error_message):
        self.status_var.set("Conversion failed.")
        self.set_converting_state(False)
        messagebox.showerror("Error", error_message)
    
    def copy_to_clipboard(self):
        if not self.grid_data:
            messagebox.showerror("Error", "No data to copy.")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(self.grid_data)
        self.status_var.set("Data copied to clipboard!")
        messagebox.showinfo("Success", "Grid data copied to clipboard!")
    
    def export_data(self):
        if not self.grid_data:
            messagebox.showerror("Error", "No data to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Pixel Grid Data",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.grid_data)
                
                self.status_var.set(f"Data exported to: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"Data exported successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def log_to_console(self, message):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, message + "\n")
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)
    
    def clear_console(self):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.delete(1.0, tk.END)
        self.console_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()