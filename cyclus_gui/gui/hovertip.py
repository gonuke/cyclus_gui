from tkinter import *
class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = Toplevel(self.widget)
        # this should get rid of title bar
        # but somehow does not work
        #self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tipwindow, text=self.text, justify=CENTER,
                      background="#ffffff", relief=SOLID, borderwidth=1)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        print('ITS IN')
        toolTip.showtip(text)
    def leave(event):
        print('ITS OUT')
        toolTip.hidetip()
    def click(event):
        widget.invoke()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)
    try: widget.bind('<Button-1>', click)
    except: z=0
