class XmlWindow():
    def __init__(self, master, output_path):
        self.master = Toplevel(master)

    def xml_window(self, master):
        try:
            self.xml_window_.destroy()
        except:
            t=0

        self.xml_window_ = Toplevel(self.master)
        self.xml_window_.title('XML rendering')
        self.xml_window_.geometry('+500+0')

        tab_parent = ttk.Notebook(self.xml_window_)
        file_paths = [os.path.join(output_path, x) for x in self.file_list]
        tab_dict = {}
        for indx, file in enumerate(file_paths):
            try: 
                with open(file, 'r') as f:
                    s = f.read().replace('<root>', '').replace('</root>', '')
                key = self.file_list[indx].replace('.xml', '')
                tab_dict[key] = Frame(tab_parent)
                tab_parent.add(tab_dict[key], text=key)
                #tab_dict[key] = assess_scroll_deny(100, tab_dict[key])
                q = Text(tab_dict[key], width=100, height=30)
                q.pack()
                q.insert(END, s)
            except Exception as e:
                print(e)
                print('Could not find %s' %file)
                t=0
        tab_parent.pack(expand=1, fill='both')

