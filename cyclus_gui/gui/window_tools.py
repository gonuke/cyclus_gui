from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText



def assess_scroll_deny(length, window_obj):
    view_hard_limit = 3e3
    scroll_limit = 25
    if length > view_hard_limit:
        messagebox.showinfo('Too much', 'You have %s distinct values. Too much to show here.' %length)
        window_obj.destroy()
        return -1
    elif length > scroll_limit:
        return add_scrollbar(window_obj)
    else:
        return window_obj

def add_scrollbar(window_obj):
    #geom = window_obj.geometry().split('+')
    #width = geom[-2]
    #height = geom[-1]
    canvas = Canvas(window_obj, width=800, height=1000)
    frame = Frame(canvas)
    scrollbar = Scrollbar(window_obj, command=canvas.yview)
    scrollbar.pack(side=RIGHT, fill='y')
    canvas.pack(side=LEFT, fill='both', expand=True)        
    def on_configure(event):
        canvas.configure(scrollregion=canvas.bbox('all'))
    canvas.configure(yscrollcommand=scrollbar.set)
    frame.bind('<Configure>', on_configure)
    canvas.create_window((4,4), window=frame, anchor='nw')
    return frame

