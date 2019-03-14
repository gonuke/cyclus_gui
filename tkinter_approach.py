from tkinter import *
from PIL import Image, ImageTk
from tkinter import messagebox

class Cygui(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.init_window()


    def init_window(self):
        self.master.title('GUI')
        self.pack(fill=BOTH, expand=1)

        # menu instance
        menu = Menu(self.master)
        self.master.config(menu=menu)

        file = Menu(menu)
        file.add_command(label='Exit', command=self.client_exit)
        menu.add_cascade(label='File', menu=file)

        edit = Menu(menu)
        edit.add_command(label='undo')
        edit.add_command(label='copy')
        # this cascade will have all the commands in edit
        menu.add_cascade(label='Edit', menu=edit)



        sim_button = Button(root, text='Simulation', command=lambda : self.open_window('simulation'))
        sim_button.pack()

        library_button = Button(root, text='Libraries', command=lambda : self.open_window('library'))
        library_button.pack()

        prototype_button = Button(root, text='Prototypes', command=lambda : self.open_window('prototype'))
        prototype_button.pack()

        region_button = Button(root, text='Regions', command=lambda : self.open_window('region'))
        region_button.pack()

        recipe_button = Button(root, text='Recipes', command=lambda : self.open_window('recipe'))
        recipe_button.pack()



    def client_exit(self):
        exit()

    def showImg(self, image_path):
        load = Image.open(image_path)
        render = ImageTk.PhotoImage(load)

        img = Label(self, image=render)
        img.image = render
        img.place(x=0, y=0)

    def showTxt(self, text):
        text = Label(self, text=text)
        text.pack()

    def open_window(self, name):        
        self.newWindow = Toplevel(self.master)

        if name == 'simulation':
            self.app = SimulationWindow(self.newWindow)
        if name == 'library':

            self.app = LibraryWindow(self.newWindow)
        if name == 'prototype':
            self.app = PrototypeWindow(self.newWindow)
        if name == 'region':
            self.app = RegionWindow(self.newWindow)
        if name == 'recipe':
            self.app = RecipeWindow(self.newWindow)


class SimulationWindow(Frame):
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)
        master.geometry('800x600')
        inputs = ['Duration', 'Start Month', 'Start Year', 'Decay',
                  'explicit_inventory', 'explicit_inventory_compact',
                  'dt']
        dscr = ['Duration of the simulation in dt (default is months)',
                'Starting month of the simulation[1-12]',
                'Starting year of the simulation',
                'Decay solver - [never, lazy, manual]',
                'create ExplicitInventory table',
                'create ExplicitInventoryCompact table',
                'Duration of single timestep in seconds']
        for i, txt in enumerate(inputs):
            Label(master, text=dscr[i]).grid(row=2*i)
            Label(master, text=txt).grid(row=(2*i +1))

        """
        Label(master, text='Duration').grid(row=0)
        Label(master, text='Start Month').grid(row=1)
        Label(master, text='Start Year').grid(row=2)
        Label(master, text='Decay').grid(row=3)

        self.e1 = Entry(master)
        self.e2 = Entry(master)

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)

        """
        self.entry_dict = {}
        for row, txt in enumerate(inputs):
            self.entry_dict[txt] = Entry(master)
            self.entry_dict[txt].grid(row=row*2+1, column=1)
        
        # default values
        self.entry_dict['Start Year'].insert(END, 2019)
        self.entry_dict['Decay'].insert(END, 'lazy')
        self.entry_dict['dt'].insert(END, 2629846)
        self.entry_dict['explicit_inventory'].insert(END, 0)
        self.entry_dict['explicit_inventory_compact'].insert(END, 0)



        done_button = Button(self.master, text='Done', command=lambda: self.done())
        done_button.grid(row=len(inputs)*2+1, column=1)
        Label(master, text='For more info:\nhttp://fuelcycle.org/user/input_specs/control.html').grid(row=len(inputs)*2+2, column=0)


    def done(self):
        self.entry_dict = {key: val.get() for key, val in self.entry_dict.items()}

        print(self.entry_dict)
        print(self.entry_dict.values())
        # check input:
        if '' in self.entry_dict.values():
            messagebox.showerror('Error', 'You omitted some parameters')




    def close_window(self):
        self.master.destroy()


class LibraryWindow(Frame):
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)

    def close_window(self):
        self.master.destroy()

class PrototypeWindow(Frame):
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)

    def close_window(self):
        self.master.destroy()

class RegionWindow(Frame):
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)

    def close_window(self):
        self.master.destroy()

class RecipeWindow(Frame):
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)

    def close_window(self):
        self.master.destroy()



root = Tk()
root.geometry('400x300')
app = Cygui(root)
root.mainloop()



