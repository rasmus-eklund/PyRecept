import operator
import os
import tkinter as tk
from copy import deepcopy

import pandas as pd
from PIL import Image, ImageTk

from Recept import Ingrediens, Recept, ReceptKontainer, is_rec

# rad 558:
# kolla efter bugg som tar bort menyn om man lägger till egna items

# BG = '#C6353C' # brown-red
BG = '#333F50' # blue-gray

class MainMenu:
    def __init__(self, master, recept, kws):
        self.master = master
        self.recept = recept
        self.kws = kws
        self.master.title("Skapa en inköpslista")
        self.master.geometry('{}x{}'.format(610, 640))
        self.master.configure(background=BG)

        self.top = tk.Frame(self.master, bg=BG)
        self.bottom = tk.Frame(self.master, bg=BG)
        #self.middle = tk.Frame(self.master, bg=BG)
        self.img = ImageTk.PhotoImage(Image.open('logo.jpg').resize((600, 315), Image.ANTIALIAS))
        self.img_lab = tk.Label(self.top, image=self.img, bg=BG)
        # Left side
        self.L_frame = tk.Frame(self.bottom, bg=BG)
        self.L_lab = tk.Label(self.L_frame, text='Inköpslista', **kws['lab'])
        self.add_rec = tk.Button(self.L_frame, text='Maträtter', command=self.add_recipe_window, **kws['btn'])
        self.handle_items = tk.Button(self.L_frame, text='Varor', command=self.items_window, **kws['btn'])
        self.show_menu = tk.Button(self.L_frame, text='Inköpslista', command=self.view_shopping_list_window, **kws['btn'])
        self.button_stores = tk.Button(self.L_frame, text='Butiker', command=self.view_stores_window, **kws['btn'])
        self.save_and_quit = tk.Button(self.L_frame, text='Spara och stäng', command=self.save_quit, **kws['btn'])
        # Right side
        self.R_frame = tk.Frame(self.bottom, bg=BG)
        self.R_lab = tk.Label(self.R_frame, text='Meny', **kws['lab'])
        self.menu_frame = tk.Frame(self.R_frame, bg=BG)
        self.scrollbar = tk.Scrollbar(self.menu_frame, orient='vertical')
        self.menu_items = tk.StringVar()
        self.menu = tk.Listbox(self.menu_frame, listvariable=self.menu_items, selectmode='multiple',
         yscrollcommand=self.scrollbar.set, exportselection=False, **kws['lb'])
        self.menu.bind("<Delete>", self.remove_recipe)
        self.menu.bind('<<ListboxSelect>>', self.on_select)
        self.delete = tk.Button(self.R_frame, text='Ta bort', command=self.remove_recipe, **kws['btn'])
        self.show = tk.Button(self.R_frame, text='Visa', command=self.show_recipe, **kws['btn'])
        self.antal_portioner = tk.DoubleVar()
        self.port_entry = tk.Entry(self.R_frame, textvariable=self.antal_portioner, **kws['ent'])
        self.port_entry.bind("<Return>", self.change_portions)
        port_ttp = CreateToolTip(self.port_entry, 'Ändra antal portioner för markerade recept.')

        # pack
        pad = {'padx':5, 'pady':5}
        self.top.pack(fill='both')
        self.bottom.pack(fill='both')
        self.img_lab.pack(side='top', **kws['pack'])
        # Left side
        self.L_frame.pack(side='left', **kws['pack'])
        self.L_lab.pack(fill='both', **pad)
        self.add_rec.pack(**pad, **kws['pack'])
        self.handle_items.pack(**pad, **kws['pack'])
        self.button_stores.pack(**pad, **kws['pack'])
        self.show_menu.pack(**pad, **kws['pack'])
        self.save_and_quit.pack(**pad, **kws['pack'])
        # Right side
        self.R_frame.pack(side='right', **kws['pack'])
        self.R_lab.pack(fill='both', **pad)
        self.menu_frame.pack(**pad, **kws['pack'])
        self.scrollbar.pack(side='right', fill='y')
        self.menu.pack(side='left', **kws['pack'])
        self.delete.pack(side='left', **pad, **kws['pack'])
        self.show.pack(side='left', **pad, **kws['pack'])
        self.port_entry.pack(side='left', fill='both', **pad)

        self.update_lb()

    def update_lb(self, *event):
        if self.recept.meny:
            self.menu_items.set(self.recept.format_recipe_search_result(self.recept.meny))

    def on_select(self, *event):
        selection = self.menu.curselection()
        recipes_matching_visible_menu = [recept for recept in self.recept.meny if not recept.kopplat_recept]
        recipes_selected = [recipes_matching_visible_menu[i] for i in selection]
        n = sum(recept.portioner for recept in recipes_selected)
        self.antal_portioner.set(n)

    def add_recipe_window(self):
        self.newWindow = tk.Toplevel(self.master)
        self.app = add_recipe(self.newWindow, self.recept, self.menu_items, self.kws)

    def remove_recipe(self, *event):
        selection = self.menu.curselection()
        recipes_matching_visible_menu = [recept for recept in self.recept.meny if not recept.kopplat_recept]
        recipes_to_remove = [recipes_matching_visible_menu[i] for i in selection]
        self.recept.remove_recipe(recipes_to_remove)
        if self.recept.meny:
            self.menu_items.set(self.recept.format_recipe_search_result(self.recept.meny))
        else:
            self.menu.delete(0,'end')
        self.menu.selection_clear(0, 'end')

    def show_recipe(self, *event):
        selection = self.menu.curselection()
        recipes_matching_visible_menu = [recept for recept in self.recept.meny if not recept.kopplat_recept]
        recipes = [recipes_matching_visible_menu[i] for i in selection]
        for recipe in recipes:
            self.newWindow = tk.Toplevel(self.master)
            self.app = ViewRecipe(self.newWindow, recipe, self.recept, self.kws)
        self.menu.selection_clear(0, 'end')

    def change_portions(self, *event):
        selection = self.menu.curselection()
        recipes_matching_visible_menu = [recept for recept in self.recept.meny if not recept.kopplat_recept]
        recipes_to_rescale = [recipes_matching_visible_menu[i] for i in selection]
        for recipe in recipes_to_rescale:
            recipe.rescale(self.antal_portioner.get())
        self.menu_items.set(self.recept.format_recipe_search_result(self.recept.meny))

    def items_window(self):
        self.newWindow = tk.Toplevel(self.master)
        self.app = HanteraVaror(self.newWindow, self.recept, self.menu_items, self.kws)

    def view_shopping_list_window(self):
        self.newWindow = tk.Toplevel(self.master)
        self.app = view_shopping_list(self.newWindow, self.recept, self.kws)

    def view_stores_window(self):
        self.newWindow = tk.Toplevel(self.master)
        self.app = ConfigureStores(self.newWindow, self.recept, self.kws)

    def save_quit(self):
        self.recept.save_state()
        quit()

class add_recipe:
    def __init__(self, master, recept, menu, kws):
        self.master = master
        self.recept = recept
        self.menu = menu
        self.master.title("Hantera maträtter")
        self.master.geometry('{}x{}'.format(1000, 600))
        self.master.configure(background=BG)
        self.master.grid_columnconfigure(0,  weight=1,uniform='group1')
        self.master.grid_columnconfigure(1,weight=1,uniform='group1')
        self.master.grid_rowconfigure(0, weight=1)
        self.selected_file_name=None
        self.connected_recipe=None

        self.results = []
        self.results_formatted = tk.StringVar()

        # LEFT
        self.left = tk.Frame(self.master, bg=BG)
        self.label1 = tk.Label(self.left, text='Lägg till maträtter:', **kws['lab'])
        self.frame_buttons = tk.Frame(self.left, bg=BG)
        self.search_text = tk.StringVar(value='Sök')
        self.entry = tk.Entry(self.frame_buttons, textvariable=self.search_text, **kws['ent'])
        self.entry.bind("<KeyRelease>", self.search_recipes)
        self.entry.bind("<Button-1>", lambda x: self.entry.delete(0, 'end') if self.search_text.get()=='Sök' else None)
        ent_ttp = CreateToolTip(self.entry,\
        'Sök recept på namn eller på vilka ingredienser receptet innehåller.\n'
        'Separera flera söktermer med kommatecken\n')
        self.search_mode = tk.StringVar(value='Recept')
        self.drop = tk.OptionMenu(self.frame_buttons, self.search_mode, *['Recept', 'Ingrediens'])
        self.drop.config(width=10, **kws['drop'])
        drop_ttp = CreateToolTip(self.drop,\
        'Recept: sök recept vars namn innehåller någon av söktermerna.\n'
        'Ingredienser: sök recept som innehåller alla söktermer.')
        self.frame_buttons1 = tk.Frame(self.left, bg=BG)
        self.btn_add = tk.Button(self.frame_buttons1, text='Lägg till', command=self.add, **kws['btn'])
        self.btn_new_recipe = tk.Button(self.frame_buttons1, text='Nytt recept', command=self.create_new_recipe, **kws['btn'])

        self.listbox_frame = tk.Frame(self.left)
        self.scrollbar = tk.Scrollbar(self.listbox_frame, orient='vertical')
        self.scrollbar_x = tk.Scrollbar(self.listbox_frame, orient='horizontal')
        self.listbox = tk.Listbox(self.listbox_frame, listvariable=self.results_formatted,
         selectmode='extended', exportselection=False, yscrollcommand=self.scrollbar.set, **kws['lb'])
        self.listbox.bind("<Return>", self.add)
        self.listbox.bind('<<ListboxSelect>>', self.left_lb_selected)
        self.listbox.bind('<Button-3>', self.r_clk_lb)

        # RIGHT
        self.right = tk.Frame(self.master, bg=BG)
        self.port_lab = tk.LabelFrame(self.right, text='Ändra recept', **kws['labf'])
        self.recept_namn_var = tk.StringVar(value='Receptnamn')
        self.recept_namn = tk.Entry(self.port_lab, textvariable=self.recept_namn_var, **kws['ent'])
        self.recept_namn.bind("<Button-1>", lambda x: self.recept_namn.delete(0, 'end') if self.recept_namn.get()=='Receptnamn' else None)
        self.recept_namn.bind("<KeyRelease>", self.update_button)
        self.port_lab2 = tk.Frame(self.port_lab, bg=BG)
        self.recept_port_lab = tk.Label(self.port_lab2, text='Portioner', anchor='w', **{k: "consolas 12" if k=='font' else v for k, v in kws['lab'].items()})
        self.port_var = tk.DoubleVar(value=0.0)
        self.port = tk.Entry(self.port_lab2, textvariable=self.port_var, width=3, **kws['ent'])
        self.port.bind("<KeyRelease>", self.update_button)
        self.save = tk.Button(self.port_lab2, text='Skapa recept', state='disabled', command=self.save_recipe, width=12, **kws['btn'])

        self.ing_lab = tk.LabelFrame(self.right, text='Ingredienser', **kws['labf'])
        self.btn_frame = tk.Frame(self.ing_lab, bg=BG)
        self.namn_var = tk.StringVar(value='Namn')
        self.edit = tk.Button(self.btn_frame, text='Ändra', command=self.edit_ing, state='disabled', **kws['btn'])
        self.add_connected_btn = tk.Button(self.btn_frame, text='Lägg till recept', command=self.add_connected, state='disabled', **kws['btn'])
        self.antal_var = tk.DoubleVar(value=0)
        self.antal_entry = tk.Entry(self.btn_frame, textvariable=self.antal_var, width=6, **kws['ent'])
        self.antal_entry.bind("<Button-1>", lambda x: self.antal_entry.delete(0, 'end') if self.antal_entry.get()=='0' else None)
        self.enhet_var = tk.StringVar(value='st')
        self.enheter_drop = tk.OptionMenu(self.btn_frame, self.enhet_var, *filter(lambda x: x != 'rec', list(Recept.enheter)))
        self.enheter_drop.config(width=5, **kws['drop'])
        self.namn_entry = tk.Entry(self.btn_frame, textvariable=self.namn_var, width=10, **kws['ent'])
        self.namn_entry.bind("<Button-1>", lambda x: self.namn_entry.delete(0, 'end') if self.namn_entry.get()=='Namn' else None)
        self.namn_entry.bind("<Return>", self.add_ing)

        self.lb_frame = tk.Frame(self.ing_lab, bg=BG)
        self.ings = list()
        self.lb_var = tk.StringVar()
        self.lb_scrollbar = tk.Scrollbar(self.lb_frame, orient='vertical')
        self.lb = tk.Listbox(self.lb_frame, listvariable=self.lb_var, selectmode='single',
         exportselection=False, yscrollcommand=self.lb_scrollbar.set, width=0, **kws['lb'])
        self.lb.bind('<<ListboxSelect>>', self.lb_selected)
        self.lb.bind('<Delete>', self.del_ing)
        self.lb.bind("<Button-3>", self.reset)

        self.instr_frame = tk.LabelFrame(self.right, text=f'Instruktion:', **kws['labf'])
        self.instruktion = tk.Text(self.instr_frame, wrap='word', **kws['txt'])
        self.instruktion.bind("<KeyRelease>", self.update_button)

        # Pack
        self.left.grid(row=0, column=0, sticky='news')#pack(side='left', **kws['pack'])
        self.right.grid(row=0, column=1, sticky='news')#pack(side='left', **kws['pack'])
        # left
        pad = {'padx':5, 'pady':5}
        self.label1.pack(fill='both', **pad)
        self.frame_buttons.pack(fill='both')
        self.entry.pack(side='left', **kws['pack'], **pad)
        self.drop.pack(side='left', **kws['pack'], **pad)
        self.frame_buttons1.pack(fill='both')
        self.btn_add.pack(side='left', fill='both', **pad)
        self.btn_new_recipe.pack(side='left', fill='both', **pad)
        self.listbox_frame.pack(side='left', **kws['pack'], **pad)
        self.scrollbar.pack(side='right', fill='y')
        self.listbox.pack(**kws['pack'])
        self.scrollbar_x.pack(side='bottom', fill='x')
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar_x.config(command=self.listbox.xview)

        self.list_all()

        self.port_lab.pack(**kws['pack'])
        self.recept_namn.pack(**kws['pack'], **pad)
        self.port_lab2.pack(**kws['pack'])
        self.recept_port_lab.pack(side='left', **kws['pack'], **pad)
        self.port.pack(side='left', fill='both', **pad)
        self.save.pack(side='left', **pad)

        self.ing_lab.pack(**kws['pack'])
        self.btn_frame.pack(fill='x', expand=True)
        self.antal_entry.pack(side='left', fill='both', **pad)
        self.enheter_drop.pack(side='left', fill='both', **pad)
        self.namn_entry.pack(side='left', fill='both', **pad)
        self.edit.pack(side='left', fill='both', **pad)
        self.add_connected_btn.pack(side='left', fill='both', **pad)
        self.lb_frame.pack(**kws['pack'], **pad)
        self.lb.pack(side='left', **kws['pack'])
        self.lb_scrollbar.pack(side='right', fill='y')
        self.lb_scrollbar.config(command=self.lb.yview)
        self.instr_frame.pack(**kws['pack'])
        self.instruktion.pack(**kws['pack'], **pad)

    def search_recipes(self, *event):
        user_input = self.search_text.get()
        if len(user_input)>0:
            search = self.recept.strip_search(user_input)
            search_mode = self.search_mode.get()
            self.results = self.recept.search_recipes(search_mode, search, self.recept.recept)
            if search_mode=='Recept':
                self.results_formatted.set(self.recept.format_recipe_search_result(self.results))
            elif search_mode=='Ingrediens':
                self.results_formatted.set(self.recept.format_recipe_for_ingredience_search_result(self.results, search))
        else:
            self.list_all()

    def list_all(self):
        self.search_text.set('Sök')
        self.listbox.selection_clear(0, 'end')
        self.results = self.recept.recept
        self.results_formatted.set(self.recept.format_recipe_search_result(self.recept.recept))
        self.clear_right()
        self.update_button()

    def add(self, *event):
        chosen = [self.results[i] for i in self.listbox.curselection()]
        self.recept.add_recipes(chosen)
        self.menu.set(self.recept.format_recipe_search_result(self.recept.meny))
        self.list_all()

    def left_lb_selected(self, *event):
        self.connected_recipe=None
        self.add_connected_btn['state'] = 'disabled'
        chosen = [self.results[i] for i in self.listbox.curselection()]
        if len(chosen)==1:
            recipe = chosen[0]
            self.selected_file_name = recipe.namn.replace(' ', '_')+'.txt'
            self.recept_namn_var.set(recipe.namn.capitalize())
            self.port_var.set(recipe.portioner)
            self.ings = recipe.ingredienser
            self.instruktion.delete(1.0, 'end')
            self.instruktion.insert(1.0, recipe.instruktion)
            self.update_lb()
            self.save['text'] = 'Spara ändring'
            self.update_button()
        else:
            self.clear_right()
            self.save['text'] = 'Skapa recept'
            self.update_button()
            self.selected_file_name=None

    def r_clk_lb(self, event):
        self.listbox.selection_clear(0, 'end')
        self.listbox.selection_set(self.listbox.nearest(event.y))
        self.listbox.activate(self.listbox.nearest(event.y))
        selected = self.listbox.curselection()
        if selected:
            self.connected_recipe = self.results[selected[0]]
            self.add_connected_btn['state'] = 'normal'
        else:
            self.connected_recipe=None
            self.add_connected_btn['state'] = 'disabled'

    def add_connected(self, *event):
        self.ings.append(deepcopy(self.connected_recipe))
        for ing in self.ings[-1].ingredienser:
            ing.kopplat = self.recept_namn_var.get()
        self.update_lb()

    def reset(self, *event):
        self.namn_var.set('Namn')
        self.enhet_var.set('st')
        self.antal_var.set(0)
        self.edit['state']='disabled'
        self.namn_entry['state']='normal'
        self.enheter_drop['state']='normal'
        self.lb.selection_clear(0, 'end')

    def clear_right(self, *event):
        self.recept_namn_var.set('Receptnamn')
        self.port_var.set(0)
        self.reset()
        self.instruktion.delete("1.0", 'end')
        self.ings = list()
        self.update_lb()

    def add_ing(self, *event):
        namn, enhet, kvantitet = self.namn_var.get(), self.enhet_var.get(), self.antal_var.get()
        self.ings.append(Ingrediens(namn, enhet, kvantitet, recept=self.recept_namn_var.get()))
        self.update_lb()
        self.reset()
        self.update_button()

    def edit_ing(self):
        namn, enhet, kvantitet = self.namn_var.get(), self.enhet_var.get(), self.antal_var.get()
        ing = self.ings[self.lb.curselection()[0]]
        if is_rec(ing):
            ing.rescale(kvantitet)
        else:
            ing.update_ing(namn, enhet, kvantitet, recept='To be added')
        self.update_lb()
        self.reset()
        self.update_button()

    def del_ing(self, *event):
        del self.ings[self.lb.curselection()[0]]
        self.update_lb()
        self.reset()
        self.update_button()

    def lb_selected(self, *event):
        selection = self.lb.curselection()
        if selection:
            self.edit['state']='normal'
            ing = self.ings[selection[0]]
            if is_rec(ing):
                self.namn_entry['state']='disabled'
                self.enheter_drop['state']='disabled'
                self.antal_var.set(ing.portioner)
                self.enhet_var.set('rec')
            else:
                self.namn_entry['state']='normal'
                self.enheter_drop['state']='normal'
                self.antal_var.set(ing.kvantitet)
                self.enhet_var.set(ing.enhet)
            self.namn_var.set(ing.namn)

    def update_lb(self):
        if self.ings:
            self.lb_var.set(self.format_list())
        else:
            self.lb.delete(0, 'end')

    def format_list(self):
        return self.recept.tabify([list(self.rec_to_ing(c)) for c in self.ings], 1)

    def create_new_recipe(self):
        self.listbox.selection_clear(0, 'end')
        self.clear_right()
        self.save['text'] = 'Skapa recept'
        self.update_button()

    def update_button(self, *event):
        e = [self.recept_namn_var.get(), self.ings, self.instruktion.get(1.0, 'end-1c')]
        if all(len(i)>0 for i in e) and (self.port_var.get()!=0):
            self.save['state'] = 'normal'
        else:
            self.save['state'] = 'disabled'

    def save_recipe(self):
        wd = os.path.dirname(os.path.abspath(__file__))
        receptnamn = self.recept_namn_var.get()
        if receptnamn != 'Receptnamn':
            ings = "\n".join(['%s\t%s\t%s' % self.rec_to_ing(ing) for ing in self.ings])
            s = f'{self.port_var.get():.0f}'
            s += '\n\n' + ings + '\n\n'
            s += self.instruktion.get("1.0",'end-1c')
            filename = receptnamn.capitalize().replace(' ', '_')+'.txt'
            if self.save['text']=='Spara ändring':
                recipe = [self.results[i] for i in self.listbox.curselection()][0]
                recipe.update_content(namn=self.recept_namn_var.get(), portioner=self.port_var.get(),
                ingredienser=self.ings, instruktion=self.instruktion.get(1.0, 'end-1c'))
                for ing in recipe.ingredienser:
                    ing.recept = self.recept_namn_var.get()
                if self.selected_file_name != filename:
                    os.rename(os.path.join(wd, 'recept', self.selected_file_name), os.path.join(wd, 'recept', filename))
                    print(f'{self.selected_file_name} renamed to {filename}.')
                with open(os.path.join(wd, 'recept', filename), 'w', encoding='utf-8') as f:
                    f.write(s)
            elif self.save['text']=='Skapa recept':
                with open(os.path.join(wd, 'recept', filename), 'w', encoding='utf-8') as f:
                    f.write(s)
                self.recept.recept.append(self.recept.read_recipe(filename))
                self.recept.recept.sort(key=lambda x: x.namn)
            self.clear_right()
        self.list_all()

    @staticmethod
    def rec_to_ing(x):
        enhet = x.enhet if x.__class__.__name__=='Ingrediens' else 'rec'
        kvantitet = x.kvantitet if x.__class__.__name__=='Ingrediens' else x.portioner
        return (str(kvantitet), enhet, x.namn.lower())

class HanteraVaror:
    def __init__(self, master, recept, menu, kws):
        self.master = master
        self.recept = recept
        self.menu = menu
        self.master.title("Hantera varor")
        self.master.geometry('{}x{}'.format(1010, 600))
        self.master.configure(background=BG)
        self.kategorier = pd.read_csv('alla_kategorier.tsv', sep='\t', encoding='cp1252')

        # left
        self.left = tk.LabelFrame(self.master, text='Varor i inköpslistan', **kws['labf'])
        self.L_btn_frame = tk.Frame(self.left, bg=BG)
        self.shoplist = []
        self.L_btn_frame1 = tk.Label(self.left, bg=BG)
        self.antal_var = tk.DoubleVar()
        self.antal_entry = tk.Entry(self.L_btn_frame1, textvariable=self.antal_var, width=6, **kws['ent'])
        antal_entry_ttp = CreateToolTip(self.antal_entry, 'Ange ny kvantitet på valda varor.')
        self.enhet_var = tk.StringVar()
        self.enheter_drop = tk.OptionMenu(self.L_btn_frame1, self.enhet_var, *filter(lambda x: x != 'rec', list(Recept.enheter)))
        self.enheter_drop.config(width=5, **kws['drop'])
        enhet_drop_ttp = CreateToolTip(self.enheter_drop, 'Ange ny enhet på valda varor.')
        self.items = tk.StringVar(value='Alla')
        self.select_items = tk.OptionMenu(self.L_btn_frame1, self.items, *['Alla', 'Egna', 'Kopplat recept', 'Okategoriserade', 'Hemma'], command=self.update_L_lb)
        self.select_items.config(width=12, **kws['drop'])
        select_items_drop_ttp = CreateToolTip(self.select_items, 'Välj vilka varor som ska visas.')

        self.L_btn_frame2 = tk.Label(self.left, bg=BG)
        self.L_btn_edit = tk.Button(self.L_btn_frame2, text='Ändra', command=self.edit, **kws['btn'])
        self.L_btn_delete = tk.Button(self.L_btn_frame2, text='Ta bort', command=self.delete_items, **kws['btn'])
        self.L_sort_var = tk.StringVar(value='Recept')
        self.L_sort_drop = tk.OptionMenu(self.L_btn_frame2, self.L_sort_var, *['Namn', 'Recept'], command=self.update_L_lb)
        self.L_sort_drop.config(width=6, **kws['drop'])
        L_sort_drop_ttp = CreateToolTip(self.L_sort_drop, 'Sortera varor.')
        self.L_filter_hemma_var = tk.BooleanVar(value=True)
        self.L_filter_hemma = tk.Checkbutton(self.L_btn_frame2, text='Hemma', variable=self.L_filter_hemma_var, command=self.update_L_lb, width=6, **kws['cb'])
        L_filter_ttp = CreateToolTip(self.L_filter_hemma, 'Dölj varor som du har hemma.')
        self.L_lb_frame = tk.Frame(self.left, bg=BG)
        self.L_lb_var = tk.StringVar()#value=self.format_shoplist()
        self.L_lb_scrollbar = tk.Scrollbar(self.L_lb_frame, orient='vertical')
        self.L_lb = tk.Listbox(self.L_lb_frame, listvariable=self.L_lb_var, selectmode='extended', width=60,
         exportselection=False, yscrollcommand=self.L_lb_scrollbar.set, **kws['lb'])
        self.L_lb.bind('<<ListboxSelect>>', self.L_lb_selected)
        self.L_lb.bind('<Delete>', self.delete_items)

        # center
        self.center = tk.LabelFrame(self.master, text='Kategorisera varor', **{'bg': BG, 'fg': 'black', 'font': 'calibri 20'})
        self.M_btn_frame = tk.Frame(self.center, bg=BG)
        self.M_drop_var = tk.StringVar(value='Kategori')
        self.M_drop = tk.OptionMenu(self.M_btn_frame, self.M_drop_var, *self.kategorier['Kategori'].unique(),
         command=self.update_underkategorier)
        M_drop_ttp = CreateToolTip(self.M_drop, 'Välj kategori.')
        self.M_drop.config(width=14, **kws['drop'])
        self.M_btn_kat = tk.Button(self.M_btn_frame, text='Kategorisera', command=self.categorize, **kws['btn'])
        self.M_cb_hemma_var = tk.BooleanVar()
        self.M_cb_hemma = tk.Checkbutton(self.M_btn_frame, text='Hemma', variable=self.M_cb_hemma_var, command=self.update_hemma, width=6, **kws['cb'])
        M_cb_ttp = CreateToolTip(self.M_cb_hemma, 'Markerar att varan finns hemma.')

        self.M_lb_frame = tk.Frame(self.center, bg=BG)
        self.M_lb_scrollbar = tk.Scrollbar(self.M_lb_frame, orient='vertical')
        self.M_lb_list = []
        self.M_lb_var = tk.StringVar()
        self.M_lb = tk.Listbox(self.M_lb_frame, listvariable=self.M_lb_var, selectmode='single',
         exportselection=False,  yscrollcommand=self.M_lb_scrollbar.set, **kws['lb'])

        # right
        self.right = tk.LabelFrame(self.master, text='Lägg till varor', **{'bg': BG, 'fg': 'black', 'font': 'calibri 20'})
        self.ing_names = self.get_all_names()
        self.search_ings = tk.StringVar()
        self.R_btn_frame = tk.Frame(self.right, bg=BG)
        self.R_ent_var = tk.StringVar(value='Egen / Sök vara')
        self.R_ent = tk.Entry(self.R_btn_frame, textvariable=self.R_ent_var, **kws['ent'])
        self.R_ent.bind("<Return>", self.add_search)
        self.R_ent.bind("<KeyRelease>", self.search_item)
        self.R_ent.bind("<Button-1>", lambda x: self.R_ent.delete(0, 'end') if self.R_ent.get()=='Egen / Sök vara' else None)
        R_ent_ttp = CreateToolTip(self.R_ent, 'Fyll i namn på vara och tryck enter för att lägga till.')
        self.R_btn_commmon = tk.Button(self.R_btn_frame, text='Vanliga varor', command=self.show_common, **kws['btn'])
        R_btn_common_ttp = CreateToolTip(self.R_btn_commmon, 'Visa de varor som du vanligtvis lägger till.')

        self.R_lb_frame = tk.Frame(self.right, bg=BG)
        self.R_lb_scrollbar = tk.Scrollbar(self.R_lb_frame, orient='vertical')
        self.R_lb = tk.Listbox(self.R_lb_frame, listvariable=self.search_ings, selectmode='multiple', exportselection=False, yscrollcommand=self.R_lb_scrollbar.set, **kws['lb'])
        self.R_lb.bind("<Return>", self.add_selection)
        R_lb_ttp = CreateToolTip(self.R_lb_frame, 'Markera varor och tyck enter för att lägga till dem.')

        # START PACK
        pad = {'padx':5, 'pady':5}
        self.left.pack(side='left', fill='both')
        self.center.pack(side='left', fill='both')
        self.right.pack(side='left', fill='both')
        # left
        self.L_btn_frame1.pack(fill='both')
        self.L_btn_frame2.pack(fill='both')
        self.antal_entry.pack(side='left', fill='y', **pad)
        self.enheter_drop.pack(side='left', fill='both', **pad)
        self.select_items.pack(side='left', fill='both', **pad)
        self.L_btn_edit.pack(side='left', fill='both', **pad)
        self.L_btn_delete.pack(side='left', fill='both', **pad)
        self.L_sort_drop.pack(side='left', fill='both', **pad)
        self.L_filter_hemma.pack(side='left', fill='both', **pad)
        self.L_lb_frame.pack(**kws['pack'], **pad)
        self.L_lb.pack(side='left', **kws['pack'])
        self.L_lb_scrollbar.pack(side='right', fill='y')
        self.L_lb_scrollbar.config(command=self.L_lb.yview)
        # center
        self.M_btn_frame.pack(fill='both')
        self.M_drop.pack(fill='both', **pad)
        self.M_btn_kat.pack(side='left', fill='both', **pad)
        self.M_cb_hemma.pack(side='left', fill='both', **pad)
        self.M_lb_frame.pack(**kws['pack'], **pad)
        self.M_lb.pack(side='left', **kws['pack'])
        self.M_lb_scrollbar.pack(side='right', fill='y')
        self.M_lb_scrollbar.config(command=self.M_lb.yview)
        # right
        self.R_btn_frame.pack(fill='both')
        self.R_ent.pack(fill='both', **pad)
        self.R_btn_commmon.pack(**kws['pack'], **pad)
        self.R_lb_frame.pack(**kws['pack'], **pad)
        self.R_lb.pack(side='left', **kws['pack'])
        self.R_lb_scrollbar.pack(side='right', fill='y')
        self.R_lb_scrollbar.config(command=self.R_lb.yview)

        self.update_L_lb()
        self.clear_reset()

    def update_L_lb(self, *event):
        item_select = {'Alla': lambda ing: ing,
               'Egna': lambda ing: ing.recept == 'Egna',
               'Kopplat recept': lambda ing: ing.recept != 'Egna',
               'Okategoriserade': lambda ing: not ing.underkategori,
               'Hemma': lambda ing: ing.hemma==1}
        selected_items = list(filter(item_select[self.items.get()], self.recept.shopping_list))
        self.shoplist = sorted(selected_items, key=operator.attrgetter(self.L_sort_var.get().lower()))
        if not self.L_filter_hemma_var.get():
            self.shoplist = list(filter(lambda x: x.hemma==0, self.shoplist))
        if self.shoplist:
            self.L_lb_var.set(self.format_shoplist())
            for r in self.recept.meny: # kolla bugg
                if r.namn not in list(set([ing.recept for ing in self.recept.shopping_list])):
                    del self.recept.meny[self.recept.meny.index(r)]
                    self.menu.set(self.recept.format_recipe_search_result(self.recept.meny))
        else:
            self.L_lb.delete(0, 'end')

    def L_lb_selected(self, *event):
        if self.L_lb.curselection():
            if len(self.L_lb.curselection())==1:
                item = self.shoplist[self.L_lb.curselection()[0]]
                self.antal_var.set(item.kvantitet)
                self.enhet_var.set(item.enhet)
                self.M_drop_var.set('Saknas' if not item.kategori else item.kategori)
                self.M_cb_hemma['bg'] = 'gray'
                self.M_cb_hemma_var.set(bool(item.hemma))
                self.update_underkategorier()
                if self.M_drop_var.get() != 'Saknas':
                    self.M_lb_list = self.kategorier['Underkategori'][self.kategorier['Kategori'].map(lambda x: x.lower())==self.M_drop_var.get()].to_list()
                    self.M_lb.selection_set(self.M_lb_list.index(item.underkategori))
            else:
                self.M_lb.delete(0, 'end')
                if len(set(ing.hemma for ing in [self.shoplist[i] for i in self.L_lb.curselection()])) > 1:
                    self.M_cb_hemma['bg'] = 'orange'
        else:
            self.clear_reset()

    def clear_reset(self, *event):
        self.antal_var.set('Antal')
        self.enhet_var.set('st')
        self.M_drop_var.set('Kategori')
        self.M_cb_hemma['bg'] = 'gray'
        self.M_lb.delete(0, 'end')
        self.L_lb.selection_clear(0, 'end')

    def format_shoplist(self):
        return self.recept.tabify([[c.namn.capitalize(), f'({c.kvantitet} {c.enhet})', f'{c.recept}{" *" if not c.underkategori else ""}{" (hemma)" if c.hemma==1 else ""}'] for c in self.shoplist], 1)

    def edit(self):
        for i in self.L_lb.curselection():
            self.shoplist[i].rescale(kvantitet=self.antal_var.get(), enhet=self.enhet_var.get())
        self.update_L_lb()

    def delete_items(self, *event):
        self.recept.remove_items([self.shoplist[i] for i in self.L_lb.curselection()])
        self.update_L_lb()
        self.clear_reset()

    def categorize(self):
        kategori = self.M_drop_var.get()
        if kategori != 'Välj kategori':
            names = [self.shoplist[i].namn for i in self.L_lb.curselection()]
            self.recept.save_item_category({'namn':[namn.lower() for namn in names],
                                            'kategori':[kategori.lower()]*len(names),
                                            'underkategori': [self.M_lb_list[self.M_lb.curselection()[0]].lower()]*len(names)})
            self.recept.update_categories(names)
            self.update_underkategorier()
            self.update_L_lb()
            self.clear_reset()

    def update_hemma(self):
        self.M_cb_hemma['bg'] = 'gray'
        selection = self.L_lb.curselection()
        if selection:
            names = [self.shoplist[i].namn for i in selection]
            self.recept.update_hemma(names, self.M_cb_hemma_var.get())
            self.recept.update_categories(names)
            self.update_L_lb()

    def update_underkategorier(self, *event):
        self.kategorier = pd.read_csv('alla_kategorier.tsv', sep='\t', encoding='cp1252')
        self.M_lb.delete(0,'end')
        self.M_lb_list = self.kategorier['Underkategori'][self.kategorier['Kategori']==self.M_drop_var.get()].to_list()
        self.M_lb_var.set(self.M_lb_list)

    def add_search(self, *event):
        name_from_ent = self.R_ent_var.get()
        if name_from_ent != '':
            chosen = [Ingrediens(namn=namn, enhet='st', kvantitet=1) for namn in self.recept.strip_search(name_from_ent)]
            self.recept.add_items_to_shopping_list(chosen)
            self.update_L_lb()
            self.R_lb.selection_clear(0, 'end')
            self.ing_names = self.get_all_names()
            self.R_ent_var.set(value='Egen / Sök vara')

    def add_selection(self, *event):
        chosen = [Ingrediens(namn=namn, enhet='st', kvantitet=1) for namn in [self.R_lb.get(i) for i in self.R_lb.curselection()]]
        self.recept.add_items_to_shopping_list(chosen)
        self.update_L_lb()
        self.R_lb.selection_clear(0, 'end')

    def show_common(self):
        self.search_ings.set([i.namn for i in self.recept.most_common()])
        self.R_ent_var.set('Egen / Sök vara')

    def search_item(self, *event):
        user_input = self.R_ent_var.get()
        if len(user_input)>0:
            search = self.recept.strip_search(user_input)
            self.search_ings.set(list(filter(lambda ing: any(s in ing for s in search), self.ing_names)))
        else:
            self.R_lb.delete(0, 'end')

    def get_all_names(self):
        return list(set([ing.namn for recept in self.recept.recept for ing in recept.ingredienser if not is_rec(ing)] + [i.namn for i in self.recept.most_common()]))

class view_shopping_list:
    def __init__(self, master, recept, kws):
        self.master = master
        self.recept = recept
        self.kws = kws
        self.master.title("Inköpslista")
        self.master.geometry('{}x{}'.format(600, 900))
        self.master.configure(background=BG)

        self.meny = tk.StringVar()
        self.store = tk.StringVar(value='Lidl Vallentuna')
        self.group_var = tk.BooleanVar(value=False)
        self.sep_var = tk.BooleanVar(value=False)
        self.recipe_var = tk.BooleanVar(value=True)

        self.frame = tk.LabelFrame(self.master, text='Inköpslista', **kws['labf'])
        self.drop = tk.OptionMenu(self.master, self.store, *[i.replace('_',' ') for i in list(self.recept.butiker)], command=self.click)
        self.drop.config(**kws['drop'])
        self.group = tk.Checkbutton(self.master, text='Gruppera ingredienser', variable=self.group_var, command=self.click, **kws['cb'])
        self.separate_hemma = tk.Checkbutton(self.master, text='Separera varor som finns hemma', variable=self.sep_var, command=self.click, **kws['cb'])
        self.show_recipe = tk.Checkbutton(self.master, text='Visa receptkolumn', variable=self.recipe_var, command=self.click, **kws['cb'])
        self.text = tk.Text(self.frame, bg='white', height=30)

        pad = {'padx':5, 'pady':5}
        self.drop.pack(**pad)
        self.group.pack(**pad)
        self.separate_hemma.pack(**pad)
        self.show_recipe.pack(**pad)
        self.frame.pack(fill='both', expand=True, **pad)
        self.text.pack(fill='both', expand=True)
        self.text.configure(inactiveselectbackground=self.text.cget("selectbackground"))
        self.click()

    def click(self, *event):
        self.text.delete(1.0, 'end')
        self.text.insert(1.0, self.recept.print_shopping_list(store=self.store.get(), group=self.group_var.get(), separate_hemma=self.sep_var.get(), recept=self.recipe_var.get()))

class ConfigureStores:
    def __init__(self, master, recept, kws):
        self.master = master
        self.recept = recept
        self.master.title("Kategorisera ingredienser")
        self.master.geometry('{}x{}'.format(800, 600))
        self.master.configure(background=BG)
        self.kategorier = pd.read_csv('alla_kategorier.tsv', sep='\t', encoding='cp1252')

        self.store_val = tk.StringVar(value=list(self.recept.butiker))

        self.kat_order = list()
        self.underkat_order = dict()
        self.kat_var = tk.StringVar(value=self.kat_order)
        self.underkat_var = tk.StringVar()
        self.entry_var = tk.StringVar(value='Ny affär')
        self.underkat_var_move = []

        # buttons
        self.btn_frame = tk.Frame(self.master, bg=BG)
        self.btn_lab = tk.Label(self.btn_frame, text='Hantera affärer', **kws['lab'])
        self.entry = tk.Entry(self.btn_frame, textvariable=self.entry_var, **kws['ent'])
        self.create_store_btn = tk.Button(self.btn_frame, text='Skapa ny affär', command=self.create_new_store, **kws['btn'])
        self.store_lb = tk.Listbox(master=self.btn_frame, listvariable=self.store_val,  selectmode='single', exportselection=False, **kws['lb'])
        self.store_lb.bind('<<ListboxSelect>>', self.set_store)
        self.save_btn = tk.Button(self.btn_frame, text='Spara', command=self.save, **kws['btn'])

        # Left listbox
        self.L_frame = tk.Frame(self.master, bg=BG)
        self.L_lab = tk.Label(self.L_frame, text='Kategori', **kws['lab'])
        self.kategori_lb = tk.Listbox(master=self.L_frame, listvariable=self.kat_var, selectmode='single', exportselection=False, **kws['lb'])
        self.kategori_lb.bind('<Up>', self.k_up)
        self.kategori_lb.bind('<Down>', self.k_down)
        self.kategori_lb.bind('<<ListboxSelect>>', self.click_kategori)
        kategori_lb_ttp = CreateToolTip(self.L_frame, 'Använd upp och nedpil för att ändra ordningen på kategorierna.')

        # Right listbox
        self.R_frame = tk.Frame(self.master, bg=BG)
        self.R_lab = tk.Label(self.R_frame, text='Underkategori', **kws['lab'])
        self.underkategori_lb = tk.Listbox(master=self.R_frame, listvariable=self.underkat_var, selectmode='single', exportselection=False, **kws['lb'])
        self.underkategori_lb.bind('<Up>', self.u_up)
        self.underkategori_lb.bind('<Down>', self.u_down)
        self.underkategori_lb.bind('<Button-3>', self.move)
        self.underkategori_lb.bind('<<ListboxSelect>>', self.click_underkategori)
        self.kategori_lb.selection_set(0)
        underkategori_lb_ttp = CreateToolTip(self.R_frame, \
        'Byta kategori för underkategori:\n'
        'Markera en underkategori.\n'
        'Markera den nya kategorin.\n'
        'Högerklicka i fältet underkategorier.\n')

        self.btn_frame.pack(side='left',fill='both', expand=False, pady=5, padx=5)
        self.L_frame.pack(side='left',fill='both', expand=True, pady=5, padx=5)
        self.R_frame.pack(side='right',fill='both', expand=True, pady=5, padx=5)

        self.btn_lab.pack(pady=5, padx=5)
        self.L_lab.pack(pady=5, padx=5)
        self.R_lab.pack(pady=5, padx=5)
        self.kategori_lb.pack(fill='both', expand=True)
        self.store_lb.pack(fill='both', expand=True)
        self.underkategori_lb.pack(fill='both', expand=True)
        self.save_btn.pack(fill='both', pady=5)
        self.entry.pack(fill='both', pady=5)
        self.create_store_btn.pack(fill='both', pady=5)

    def click_underkategori(self, event):
        self.underkat_var_move = {'kategori': self.kategori_lb.get(self.kategori_lb.curselection()),
                                  'under_index': self.underkategori_lb.curselection()[0]}

    def move(self, *event):
        if len(list(self.underkat_var_move))!=0:
            item = self.underkat_order[self.underkat_var_move['kategori']].pop(self.underkat_var_move['under_index'])
            kategori = self.kategori_lb.get(self.kategori_lb.curselection())
            self.underkat_order[kategori].append(item)
            self.kat_var.set(self.kat_order)
            self.click_kategori(0)
            self.save_btn['bg'] = 'red'

    def set_store(self, *event):
        self.kategori_lb.delete(0,'end')
        self.kategori_lb.selection_clear(0, 'end')
        self.underkategori_lb.selection_clear(0, 'end')
        store = self.store_lb.get(self.store_lb.curselection())
        self.kat_order = list(self.recept.butiker[store]['Kategori'].unique())
        self.kat_var.set(self.kat_order)
        self.underkat_order = {name: self.recept.butiker[store]['Underkategori'][self.recept.butiker[store]['Kategori']==name].unique().tolist() for name in self.kat_order}

    def save(self):
        wd = os.path.dirname(os.path.abspath(__file__))
        pd.DataFrame({'Kategori': [i for kat in self.kat_order for i in [kat]*len(self.underkat_order[kat])],
                      'Underkategori': [i for kat in self.kat_order for i in self.underkat_order[kat]]}).to_csv(os.path.join(wd, 'butiker',
                       f'{self.format_store_name(self.store_lb.get(self.store_lb.curselection())).replace(" ", "_")}.tsv'),
                       sep='\t', index=False, encoding='cp1252', header=True)
        self.recept.read_stores()
        self.save_btn['bg'] = 'green'

    def create_new_store(self):
        name = self.entry_var.get()
        if name!='Ny affär':
            new = self.format_store_name(name)
            self.recept.butiker.update({new: self.kategorier.copy()})
            self.store_val.set(value=list(self.recept.butiker))
            self.entry_var.set('Ny affär')
            self.store_lb.selection_set(0)
            self.set_store()
            self.save_btn['bg'] = 'red'

    def k_up(self, *event):
        i = self.kategori_lb.curselection()[0]
        name = self.kategori_lb.get(i)
        if i != 0:
            above = self.kategori_lb.get(i-1)
            self.kat_order[i]=above
            self.kat_order[i-1]=name
            self.kategori_lb.selection_clear(0, 'end')
            self.kategori_lb.selection_set(i-1 if i-1 > 0 else 0)
            self.kat_var.set(self.kat_order)
            self.save_btn['bg'] = 'red'

    def k_down(self, event):
        i = self.kategori_lb.curselection()[0]
        name = self.kategori_lb.get(i)
        if i != len(self.kat_order)-1:
            below = self.kategori_lb.get(i+1)
            self.kat_order[i]=below
            self.kat_order[i+1]=name
            self.kategori_lb.selection_clear(0, 'end')
            self.kategori_lb.selection_set(i+1 if i+1 < len(self.kat_order)-1 else len(self.kat_order)-1)
            self.kat_var.set(self.kat_order)
            self.save_btn['bg'] = 'red'


    def u_up(self, event):
        i = self.underkategori_lb.curselection()[0]
        name = self.underkategori_lb.get(i)
        kat = self.kategori_lb.get(self.kategori_lb.curselection()[0])
        if i != 0:
            above = self.underkategori_lb.get(i-1)
            self.underkat_order[kat][i]=above
            self.underkat_order[kat][i-1]=name
            self.underkategori_lb.selection_clear(0, 'end')
            self.underkategori_lb.selection_set(i-1 if i-1 > 0 else 0)
            self.underkat_var.set(self.underkat_order[kat])
            self.save_btn['bg'] = 'red'

    def u_down(self, event):
        i = self.underkategori_lb.curselection()[0]
        name = self.underkategori_lb.get(i)
        kat = self.kategori_lb.get(self.kategori_lb.curselection()[0])
        if i != len(self.underkat_order[kat])-1:
            below = self.underkategori_lb.get(i+1)
            self.underkat_order[kat][i]=below
            self.underkat_order[kat][i+1]=name
            self.underkategori_lb.selection_clear(0, 'end')
            self.underkategori_lb.selection_set(i+1 if i+1 < len(self.underkat_order[kat])-1 else len(self.underkat_order[kat])-1)
            self.underkat_var.set(self.underkat_order[kat])
            self.save_btn['bg'] = 'red'

    def click_kategori(self, event):
        name = self.kategori_lb.get(self.kategori_lb.curselection()[0])
        self.underkat_var.set(self.underkat_order[name])
        self.underkategori_lb.selection_clear(0, 'end')

    @staticmethod
    def format_store_name(x):
        return ' '.join([i.capitalize() for i in x.lower().split(' ')])

class ViewRecipe():
    def __init__(self, master, recipe, recept, kws):
        self.master = master
        self.recept = recept
        self.recipe = recipe
        self.master.title("Visa recept")
        self.master.geometry('{}x{}'.format(600, 600))
        self.master.configure(background=BG)

        self.rec_name = tk.Label(self.master, text=f'{recipe.namn} | {recipe.portioner}', **kws['lab'])

        self.ingr_frame = tk.LabelFrame(self.master, text=f'Ingredienser:', **kws['labf'])
        self.ingredients = tk.Text(self.ingr_frame, height=len(self.recipe.ingredienser), **kws['txt'])
        self.ingredients.insert(1.0, '\n'.join(self.recept.tabify([[c.namn.capitalize(), str(c.kvantitet), c.enhet] for c in self.recipe.ingredienser if not is_rec(c)], 1)))

        self.instr_frame = tk.LabelFrame(self.master, text=f'Instruktion:', **kws['labf'])
        self.instruktion = tk.Text(self.instr_frame, wrap='word', **kws['txt'])
        self.instruktion.insert(1.0, recipe.instruktion)

        # Pack
        pad = {'padx':5, 'pady':5}
        self.rec_name.pack(fill='both', **pad)
        self.ingr_frame.pack()
        self.ingredients.pack()
        self.instr_frame.pack()
        self.instruktion.pack()

class CreateToolTip():
    """
    Credit to crxguy52 and Stevoisiak from stackoverflow
    https://stackoverflow.com/a/36221216
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

def main():
    root = tk.Tk()
    recept = ReceptKontainer()
    recept.load_state()
    font = 'consolas'
    small = 12
    large = 18
    kws={'btn': {'bg': 'gray', 'fg': 'black', 'font': f'{font} {small}', 'justify':'left'},
         'ent': {'bg': 'white', 'fg': 'black', 'font': f'{font} {small}', 'justify':'left'},
         'lab': {'bg': BG, 'fg': 'black', 'font': f'{font} {large}', 'justify':'left'},
         'labf': {'bg': BG, 'fg': 'black', 'font':  f'{font} {large}'},
         'lb': {'bg':'white', 'fg':'black', 'font': f'{font} {small}', 'justify':'left', 'selectbackground':'gray', 'activestyle':'none', 'borderwidth':0, 'highlightthickness':0},
         'drop': {'bg': 'white', 'fg':'black', 'font': f'{font} {small}', 'justify':'left', 'anchor':'w'},
         'cb': {'bg': 'gray', 'fg':'black', 'font': f'{font} {small}', 'justify':'left', 'anchor':'w', 'activebackground':BG},
         'txt': {'bg': 'white', 'fg': 'black', 'font': f'{font} {small}'},
         'pack': {'expand':True, 'fill':'both'}}
    app = MainMenu(root, recept, kws)
    root.mainloop()

if __name__ == '__main__':
    main()
