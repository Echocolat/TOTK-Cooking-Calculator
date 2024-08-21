import traceback
import customtkinter as ctk
import tkinter as tk
from totk_cook_logic import TotKCookSim, InvalidMaterialException, EmptyMaterialListException

# credits
INFO = "TotK Cooking Simulator v2 | Cooking code retrived by dt12345, Base code made by KingFoo, Improved code by Echocolat, web part by Glitchtest, additional testing by Doge229"

# initialize the sim
sim = TotKCookSim()

class InputFrame(ctk.CTkFrame):
    """Frame containing the five text inputs as well as the Cook button"""
    def __init__(self, master, title, amount):
        super().__init__(master)
        self.amount = amount
        self.entries = []
        self.title = title
        self.grid_columnconfigure(0, weight=1)

        # title (Materials)
        self.title = ctk.CTkLabel(self, text = self.title, fg_color = "gray13", corner_radius = 6, font = ('Helvetica', 25), height = 50)
        self.title.grid(row = 0, column = 0, padx = 10, pady = (10, 10), sticky = "nwe")

        self.text_list = []
        for _ in range(amount):
            # creating the StringVars containing each material
            self.text_list.append( tk.StringVar())

        for index in range(amount):
            # creating each CTkEntry (textbox to put the input in)
            entry = ctk.CTkEntry(self, state = 'normal', width = 300, height = 40, justify = 'center', textvariable = self.text_list[index], font = ('Helvetica', 20))
            entry.grid(row = index + 1, column = 0, padx = 10, pady = (10, 10), sticky = "nw")
            self.entries.append(entry)

        # Cook button
        self.cook_button = ctk.CTkButton(self, text = 'Cook', command = master.cook, width = 300, height = 50, fg_color = "#696969", hover_color = "#383838", font = ('Helvetica', 25))
        self.cook_button.grid(row = 6, column = 0, padx = 10, pady = 10, sticky = "nw")

    def get(self):
        # returns the list of materials inside the 5 input boxes
        self.materials = []
        for text in self.text_list:
            if text.get().strip():
                self.materials.append(text.get().strip())
        return self.materials
    
class OutputFrame(ctk.CTkFrame):
    """Frame containing the output textbox"""
    def __init__(self, master, title):
        super().__init__(master)
        self.texts = []
        self.title = title
        self.grid_columnconfigure(0, weight=1)

        # title (Cooked Meal)
        self.title = ctk.CTkLabel(self, text = self.title, fg_color = "gray13", corner_radius = 6, font = ('Helvetica', 25), height = 50, width = 620)
        self.title.grid(row = 0, column = 1, padx = 10, pady = (10, 10), sticky = "nwe")

        # output textbox
        self.output_text = ctk.CTkTextbox(self, height = 355, font = ('Helvetica', 15), spacing3 = 8, wrap = tk.WORD)
        self.output_text.grid(row = 1, column = 1, padx = 10, pady = (10, 10), sticky = "nwe")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # setup
        self.title("TotK Cooking Simulator v2")
        self.geometry("1000x465")
        self.grid_columnconfigure(0, weight=1)
        self.iconbitmap('assets/icon.ico')
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        self.resizable(False, False)

        # initializing InputFrame
        self.entryframe = InputFrame(self, "Materials", 5)
        self.entryframe.grid(row = 0, column = 0, padx = 10, pady = (10, 0), sticky = "nw")

        # initializing OutputFrame
        self.outputframe = OutputFrame(self, 'Cooked Meal')
        self.outputframe.grid(row = 0, column = 1, padx = 0, pady = (10, 0), sticky = "nw")

        # credits text box
        self.text = ctk.CTkLabel(self, text = INFO, font = ('Helvetica', 11), height = 12, width = 1000)
        self.text.grid(row = 2, column = 0, padx = 10, pady = (0, 0), sticky = "se", columnspan = 2)

    def cook(self):
        # cooks the inputted materials when the Cook button is pressed
        result_txt = ""
        try:
            # gets the materials list
            materials = self.entryframe.get()
            # get cooking result
            result = sim.cook(materials)
            # formatting
            for k, v in result.items():
                result_txt += f'{k}: {v}\n'
                self.outputframe.output_text.delete('1.0', tk.END)
                self.outputframe.output_text.insert('1.0', result_txt)
        except EmptyMaterialListException:
            # means the list is empty
            traceback.print_exc()
            self.outputframe.output_text.delete('1.0', tk.END)
            self.outputframe.output_text.insert('1.0', 'Material list is empty.')
        except InvalidMaterialException:
            # means one of the materials have an invalid name
            traceback.print_exc()
            self.outputframe.output_text.delete('1.0', tk.END)
            self.outputframe.output_text.insert('1.0', 'Invalid material detected.')
        except Exception:
            # any other exception
            traceback.print_exc()
            self.outputframe.output_text.delete('1.0', tk.END)
            self.outputframe.output_text.insert('1.0', 'Something went wrong.')

# initialize app
app = App()
# run app
app.mainloop()