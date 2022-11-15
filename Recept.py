# Created on Mon Mar 29 20:02:24 2021
# author: Rasmus Eklund

import os
import pickle
from copy import deepcopy
from datetime import datetime
from os.path import splitext

import numpy as np
import pandas as pd
from tabulate import tabulate


class ReceptKontainer:

    def __init__(self):
        self.recept = list()
        self.butiker = dict()
        self.meny = list()
        self.shopping_list = list()
        self.read_recipes()
        self.read_stores()

    def __repr__(self):
        s = 'Antal recept: %i' % len(self.recept)
        class_name = self.__class__.__name__
        return '<%s | %s>' % (class_name, s)

    def read_stores(self):
        for store in os.listdir('butiker'):
            self.butiker.update(self.read_store(store))

    def read_store(self, store):
        return {splitext(store)[0].replace('_',' '): pd.read_csv(os.path.join('butiker', store), sep='\t', encoding='cp1252')}

    def read_recipes(self):
        for rec in os.listdir('recept'):
            self.recept.append(self.read_recipe(rec))

    def read_recipe(self, rec):
        with open(os.path.join('recept', rec), 'r', encoding='utf-8') as f:
            portioner, ingredienser, *instruktion = f.read().split('\n\n')
        receptnamn = splitext(rec)[0].replace('_', ' ').capitalize()
        instruktion = '\n\n'.join(instruktion)
        ings = []
        for ing in ingredienser.split('\n'):
            kvantitet, enhet, namn = ing.split('\t')
            if ' ' in enhet:
                print(f'{namn}s enhet i {receptnamn} innehåller mellanslag!')
                quit()
            if ',' in kvantitet:
                print(f'{namn}s kvantitet i {receptnamn} innehåller , istället för .')
                quit()
            if enhet=='rec':
                r = self.read_recipe(namn.capitalize().replace(' ', '_')+'.txt')
                r.rescale(float(kvantitet))
                r.kopplat_recept=receptnamn
                for ing in r.ingredienser:
                    ing.kopplat=receptnamn
                ings.append(r)
            else:
                ings.append(Ingrediens(namn, enhet, kvantitet, recept=receptnamn))
        return Recept(namn=receptnamn, portioner=portioner, ingredienser=ings, instruktion=instruktion)

    def add_recipes(self, recipes, log=True):
        for recipe in recipes:
            if log:
                self.logger(recipe, 'recept')
            self.meny.append(deepcopy(recipe))
            self.add_recipe_to_shopping_list(self.meny[-1])

    def add_recipe_to_shopping_list(self, recipe):
        for ing in recipe.ingredienser:
            if ing.__class__.__name__=='Recept':
                self.add_recipe_to_shopping_list(ing)
            else:
                self.shopping_list.append(ing)

    def search_recipes(self, search_mode, search, database):
        '''Find recipes by searching for recipe names or ingredients. Multiple search terms are divided by ,

        Parameters
        ----------
        search_mode : str
            "Recept", "Ingrediens", or "ExactName". Searching by Ingrediens finds recipes containing all search terms.
        search : list of str
            A list of search terms
        database : list
            A list of Ingrediens class instances

        Retuns
        ----------
        list
            Returns list of recipe instances depending on `search_mode`.
        '''
        if search_mode == 'Recept':
            results = list(filter(lambda recept: any(i.lower() in recept.namn.lower() for i in search), database))
        elif search_mode == 'Ingrediens':
            results = list(filter(lambda recept: all(any([s.lower() in i for i in [ing.namn.lower() for ing in recept.ingredienser if ing.__class__.__name__=='Ingrediens']]) for s in search), database))
        elif search_mode == 'ExactName':
            results = list(filter(lambda recept: any(recept.namn.lower() == i.lower() for i in search), database))
        return results

    def search_ingredient(self, search, database, ingrediens=False):
        """Search for an ingredience by its name.

        Parameters
        ----------
        search : str
            Name of ingredient
        db : list
            A list populated by instances of `Recept`

        Returns
        -------
        list
            List containing ingredients matching the search term.
        """
        if ingrediens:
            results = list(filter(lambda ing: ing==ingrediens, [ing for recipe in database for ing in recipe.ingredienser]))
        else:
            results = list(filter(lambda ing: any(s.lower() in ing.namn.lower() for s in search), [ing for recipe in database for ing in recipe.ingredienser]))
        return results

    def remove_recipe(self, recipes):
        for recipe in recipes:
            del self.meny[self.meny.index(recipe)]
            self.remove_items(recipe.ingredienser)

    def remove_items(self, items):
        for item in items:
            if item.__class__.__name__=='Recept':
                self.remove_items(item.ingredienser)
            else:
                del self.shopping_list[self.shopping_list.index(item)]

    def add_items_to_shopping_list(self, ings):
        for ing in ings:
            ing = deepcopy(ing)
            self.shopping_list.append(self.logger(ing, 'item'))

    def update_categories(self, ing_names):
        all_ings = [ing for recept in self.recept for ing in recept.ingredienser if not is_rec(ing)] + self.shopping_list
        needs_update = list(filter(lambda ing: (not is_rec(ing)) and (ing.namn in ing_names), all_ings))
        for ing in needs_update:
            ing.get_category()

    def save_item_category(self, items):
        database = pd.read_csv('mat_kategori.tsv', sep='\t', encoding='cp1252')
        new_items = {k: [] for k in items}
        for i, namn in enumerate(items['namn']):
            if namn in database.namn.to_list():
                database.loc[database.namn==namn, ['kategori', 'underkategori']] = (items['kategori'][i], items['underkategori'][i])
            else:
                for k in items:
                    new_items[k].append(items[k][i])
                new_items.update({'hemma': [0]*len(new_items['namn'])})
        database = pd.concat([database, pd.DataFrame(new_items)], ignore_index=True).sort_values(by=['kategori', 'underkategori', 'namn'])
        database.to_csv('mat_kategori.tsv', sep='\t', header=True, index=False, encoding='cp1252')
        print(f'Saved categories of {len(new_items["namn"])} items!')

    def print_shopping_list(self, store, group=False, separate_hemma=False, sortby=['butiksordning', 'namn', 'recept'], recept=True, tofile=False):
        if recept:
            columns = ['namn', 'kvant', 'recept']
        else:
            columns = ['namn', 'kvant']
        if len(self.shopping_list) == 0:
            out = 'Tom'
        else:
            df = pd.DataFrame([pd.Series(item.__dict__) for item in self.shopping_list])
            df['butiksordning'] = 0
            all_cols = df.columns
            for i, (kategori, underkategori) in self.butiker[store].iterrows():
                df.loc[df['underkategori']==underkategori.lower(), 'butiksordning'] = i
            if group:
                df = pd.DataFrame([[namn, enhet, d.kvantitet.sum()] + [d[c].unique()[0] for c in all_cols[3:]] for (namn, enhet), d in list(df.groupby(['namn','enhet']))],
                columns=all_cols)
            df['kvant'] = df[['kvantitet', 'enhet']].apply(lambda r: ' '.join(map(str, r)), 1)
            df['namn'] = df['namn'].apply(lambda r: r.capitalize())
            if separate_hemma and (df.hemma.sum()!=0):
                df = df.sort_values(by=['hemma']+sortby)
                out = tabulate(df[columns], showindex=False, tablefmt='plain')
                divided = out.split('\n')
                divided.insert(int(-sum(df.hemma)), '-'*len(max(divided, key=lambda x: len(x))))
                out = '\n'.join(divided)
            else:
                df = df.sort_values(by=sortby)
                out = tabulate(df[columns], showindex=False, tablefmt='plain')
            if tofile:
                df[columns].to_csv('inköpslista.tsv', sep='\t', encoding='cp1252', index=False, header=False)
        return out

    def most_common(self, filt='item'):
        df = pd.read_csv('most_common.tsv', sep='\t', encoding='cp1252')
        unique_names = np.unique(df[df['event']==filt][['namn']], return_counts=True)
        common = pd.DataFrame(np.array(unique_names).T, columns=['namn', 'nr']).sort_values(by='nr', ascending=False)
        for name in unique_names[0]:
            for i in ['kvantitet', 'enhet']:
                common.loc[common['namn']==name, i] = pd.DataFrame(np.array(np.unique(df[(df['event']==filt) & (df['namn']==name)][i], return_counts=True)).T, columns=[i, 'nr']).sort_values(by='nr', ascending=False).iloc[0,0]
        ings = [Ingrediens(**dict(ing)) for _, ing in common[['namn','kvantitet','enhet']].iterrows()]
        return ings

    def save_state(self):
        with open(os.path.join('save', 'menu.pkl'), "wb") as f:
            pickle.dump(self.meny, f, protocol=-1)
        with open(os.path.join('save', 'items.pkl'), "wb") as f:
            pickle.dump([i for i in self.shopping_list if i.recept=='Egna'], f, protocol=-1)

    def load_state(self):
        if os.path.isfile(os.path.join('save', 'items.pkl')):
            with open(os.path.join('save', 'items.pkl'), "rb") as f:
                self.shopping_list = pickle.load(f)
        if os.path.isfile(os.path.join('save', 'menu.pkl')):
            with open(os.path.join('save', 'menu.pkl'), "rb") as f:
                self.add_recipes(pickle.load(f), log=False)

    @staticmethod
    def update_hemma(namn, hemma):
        df = pd.read_csv('mat_kategori.tsv', sep='\t', encoding='cp1252')
        df.loc[df.namn.isin(namn), 'hemma'] = hemma*1
        df.to_csv('mat_kategori.tsv', sep='\t', header=True, index=False, encoding='cp1252')

    @staticmethod
    def format_recipe_for_ingredience_search_result(results, search):
        return [f'{recept.namn.capitalize()} innehåller {", ".join([ing.namn for ing in list(filter(lambda ing: any(i in ing.namn for i in search), recept.ingredienser))])}' for recept in results]

    def format_ingredience_search_result(self, ingredienser):
        return self.tabify([[ing.namn.capitalize(), str(ing.kvantitet), ing.enhet] for ing in ingredienser], 1)

    def format_recipe_search_result(self, results):
        return self.tabify([[recept.namn, '|', f'{recept.portioner} port {"+" if any(is_rec(i) for i in recept.ingredienser) else ""}'] for recept in results], 1)

    @staticmethod
    def strip_search(search):
        return [i.strip() for i in search.split(',')]

    @staticmethod
    def logger(item, item_type):
        date = datetime.now().strftime("%y-%m-%d %H:%M:%S")
        df = pd.read_csv('most_common.tsv', sep='\t', encoding='cp1252')
        if item_type=='recept':
            d = pd.DataFrame({'namn':[item.namn.lower()], 'datum':[date], 'event':[item_type], 'kvantitet':[item.portioner], 'enhet':['port']})
        else:
            d = pd.DataFrame({'namn':[item.namn.lower()], 'datum':[date], 'event':[item_type], 'kvantitet':[item.kvantitet], 'enhet':[item.enhet]})
        df = pd.concat([df, d], ignore_index=True)
        df.to_csv('most_common.tsv', sep='\t', header=True, index=False, encoding='cp1252')
        return item

    @staticmethod
    def tabify(s, extra=0):
        sizes = [len(max(np.array(s)[:,i], key=lambda x: len(x)))+extra for i in range(len(s[0]))]
        return [''.join(['%s%s'%(v," "*(sizes[i]-len(v))) for i, v in enumerate(l)]) for l in s]

def rec_to_ing(x):
    enhet = x.enhet if x.__class__.__name__=='Ingrediens' else 'rec'
    kvantitet = x.kvantitet if x.__class__.__name__=='Ingrediens' else x.portioner
    return (str(kvantitet), enhet, x.namn)

def is_rec(x):
    return True if x.__class__.__name__=='Recept' else False

class Recept:
    enheter = {'dl': 'deciliter', 'g': 'gram', 'klyfta': 'klyfta', 'l': 'liter',
               'krm': 'kryddmått', 'msk': 'matsked', 'port': 'portion', 'pkt': 'paket',
               'rec': 'recept', 'st': 'stycken', 'tsk': 'tesked', 'kg': 'kilogram'}

    def __init__(self, namn, portioner, ingredienser, instruktion, kopplat_recept=False):
        self.namn = namn
        self.portioner = float(portioner)
        self.ingredienser = ingredienser
        self.instruktion = instruktion
        self.kopplat_recept = kopplat_recept

    def __repr__(self):
        s = f'{self.namn}\n\n'
        s += f'Mat till {self.portioner:.0f} portioner\n\n'
        s += f'Ingredienser:\n{tabulate([list(rec_to_ing(ing)) for ing in self.ingredienser], tablefmt="psql")}\n\n'
        s += f'Instruktion:\n{self.instruktion}'
        if self.kopplat_recept:
            s += f'\n\nReceptet är till {self.kopplat_recept}'
        class_name = self.__class__.__name__
        return '<%s | %s>' % (class_name, s)

    def rescale(self, portioner):
        scale_factor = portioner/self.portioner
        for ing in self.ingredienser:
            if ing.__class__.__name__=='Ingrediens':
                ing.rescale(ing.kvantitet * scale_factor, ing.enhet)
            else:
                ing.rescale(ing.portioner * scale_factor)
        self.portioner = portioner
        # print(f'{self.namn} changed portions to {portioner}')

    def update_content(self, namn, portioner, ingredienser, instruktion, kopplat_recept=False):
        self.namn = namn
        self.portioner = portioner
        self.ingredienser = ingredienser
        for ing in self.ingredienser:
            ing.recept = self.namn
        self.instruktion = instruktion
        self.kopplat_recept = kopplat_recept
        print(f'{self.namn} content updated.')

class Ingrediens:
    """Creates a ingredience
    """
    def __init__(self, namn, enhet, kvantitet, kategori=False, underkategori=False, recept='Egna', hemma=False, kopplat=False):
        self.namn = namn.lower()
        self.enhet = enhet.lower()
        self.kvantitet = float(kvantitet)
        self.kategori = kategori
        self.underkategori = underkategori
        self.recept = recept
        self.hemma = hemma
        self.kopplat = kopplat
        self.get_category()

    def __repr__(self):
        s = self.namn
        s += f' ({self.kvantitet} {self.enhet}) '
        if self.kategori:
            s += 'vid ' + self.kategori
        if self.underkategori:
            s += ', ' + self.underkategori + ' '
        if self.recept != 'Egna':
            s += 'tillhör ' + \
                self.recept.replace('_', ' ').lower() + ' '
        if self.kopplat:
            s += 'som är kopplat till ' + self.kopplat.replace('_', ' ').lower()
        class_name = self.__class__.__name__
        return '<%s | %s>' % (class_name, s.strip())

    def rescale(self, kvantitet, enhet):
        """Change ingredience quantity and unit

        Parameters
        ----------
        kvantitet : float
            Quantity
        enhet : str
            Unit
        """
        self.kvantitet = kvantitet
        self.enhet = enhet

    def get_category(self):
        """Get category from database"""
        database = pd.read_csv('mat_kategori.tsv', sep='\t', encoding='cp1252')
        if self.enhet != 'rec':
            if self.namn in database.namn.to_list():
                self.kategori, self.underkategori, self.hemma = database.loc[database.namn==self.namn, ['kategori', 'underkategori', 'hemma']].iloc[0]

    def update_ing(self, namn, enhet, kvantitet, recept, kopplat=False):
        self.namn, self.enhet, self.kvantitet, self.recept, self.kopplat = namn, enhet, kvantitet, recept, kopplat

# self = ReceptKontainer()
# i = Ingrediens('Mjölk', 'l', 1)
# i.get_category()
# self.add_items_to_shopping_list([i])

# recipes = self.search_recipes(search_mode='Ingrediens', search=['mjöl'], database=self.recept)
# recipe = recipes[0]
# ing = recipe.ingredienser

# self.add_recipes(self.search_recipes(search_mode='Recept', search=['test1'], database=self.recept))
# [i.namn for i in self.meny]
# [i.namn for i in self.shopping_list]

# self.save_state()
