configure window snippet:

def configure_window(self):
    self.config_window = Toplevel(self.master)
    self.config_window.title('Configuration')
    self.config_window.geometry('+700+1000')
    parent = self.config_window

    columnspan = 4
    self.config_dict = {}
    Label(parent, text='Configurations').grid(row=0, columnspan=columnspan)
    # n_isos, plotting scale, nuclide notation
    Label(parent, text='Plot top n isos:').grid(row=1, column=0)
    self.config_dict['n_isos'] = Entry(parent)
    self.config_dct['n_isos'].grid(row=1, column=1)
    Label(parent, text='Leave it blank to plot/export mass').grid(row=1, column=2)

    Label(parent, text='plot y scale').grid(row=2, column=0)
    self.config_dict['yscale'] = Entry(parent)
    self.config_dict['yscale'].grid(row=2, column=1)
    Label(parent, text='Scale of y scale')
