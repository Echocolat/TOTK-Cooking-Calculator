import os, sys
import traceback
import customtkinter as ctk
import tkinter as tk
from Cooking import TotKCookSim
from PIL import Image

try:
    os.chdir(sys._MEIPASS)
except:
    pass

INFO = "Cooking code retrived by dt12345, Base code made by KingFoo, Improved code and UI by Echocolat, additional research by Doge229, dt12345 and Echocolat"

sim = TotKCookSim()

class InputFrame(ctk.CTkFrame):
    def __init__(self, master, title, amount):
        super().__init__(master)
        self.amount = amount
        self.entries = []
        self.title = title
        self.grid_columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(self, text = self.title, fg_color = "gray13", corner_radius = 6, font = ('Helvetica', 25), height = 50)
        self.title.grid(row = 0, column = 0, padx = 10, pady = (10, 10), sticky = "nwe")

        self.text_list = []
        for _ in range(5):
            self.text_list.append( tk.StringVar())

        for index in range(amount):
            entry = ctk.CTkEntry(self, state = 'normal', width = 300, height = 40, justify = 'center', textvariable = self.text_list[index], font = ('Helvetica', 20))
            entry.grid(row = index + 1, column = 0, padx = 10, pady = (10, 10), sticky = "nw")
            self.entries.append(entry)

        self.cook_button = ctk.CTkButton(self, text = 'Cook', command = master.cook, width = 300, height = 50, fg_color = "#696969", hover_color = "#383838", font = ('Helvetica', 25))
        self.cook_button.grid(row = 6, column = 0, padx = 10, pady = 10, sticky = "nw")

    def get(self):
        self.materials = []
        for text in self.text_list:
            if text.get().strip():
                self.materials.append(text.get().strip())
        return self.materials
    
class OutputFrame(ctk.CTkFrame):
    def __init__(self, master, title):
        super().__init__(master)
        self.texts = []
        self.title = title
        self.grid_columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(self, text = self.title, fg_color = "gray13", corner_radius = 6, font = ('Helvetica', 25), height = 50, width = 620)
        self.title.grid(row = 0, column = 1, padx = 10, pady = (10, 10), sticky = "nwe")

        self.output_text = ctk.CTkTextbox(self, height = 355, font = ('Helvetica', 18), spacing3 = 8, wrap = tk.WORD)
        self.output_text.grid(row = 1, column = 1, padx = 10, pady = (10, 10), sticky = "nwe")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TotK Cooking Simulator v1")
        self.geometry("1000x465")
        self.grid_columnconfigure(0, weight=1)
        self.iconbitmap('assets/icon.ico')
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        self.resizable(False, False)

        self.entryframe = InputFrame(self, "Materials", 5)
        self.entryframe.grid(row = 0, column = 0, padx = 10, pady = (10, 0), sticky = "nw")

        self.outputframe = OutputFrame(self, 'Cooked Meal')
        self.outputframe.grid(row = 0, column = 1, padx = 0, pady = (10, 0), sticky = "nw")

        self.text = ctk.CTkLabel(self, text = INFO, font = ('Helvetica', 11), height = 12, width = 1000)
        self.text.grid(row = 2, column = 0, padx = 10, pady = (0, 0), sticky = "se", columnspan = 2)

    def cook(self):
        result_txt = ""
        try:
            materials = self.entryframe.get()
            if len(materials) == 0:
                result_txt = "No material selected."
                self.outputframe.output_text.delete('1.0', tk.END)
                self.outputframe.output_text.insert('1.0', result_txt)
            else:
                result = sim.cook(materials)
                for k, v in result.items():
                    result_txt += f'{k}: {v}\n'
                    self.outputframe.output_text.delete('1.0', tk.END)
                    self.outputframe.output_text.insert('1.0', result_txt)
        except KeyError:
            traceback.print_exc()
            self.outputframe.output_text.delete('1.0', tk.END)
            self.outputframe.output_text.insert('1.0', 'Invalid material detected.')
        except Exception:
            traceback.print_exc()
            self.outputframe.output_text.delete('1.0', tk.END)
            self.outputframe.output_text.insert('1.0', 'Something went wrong.')

app = App()
app.mainloop()