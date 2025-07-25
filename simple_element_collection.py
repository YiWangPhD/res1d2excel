#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this class manages elements to be extracted from res1d
# quantities is dictionary of list, in format:
#    quantity_id: [elements]

# added Feb 13, 2025:
# 1. check for duplicates before adding element
# 2. get_elements_by_quantity_and_id


import simple_element
import statistics_calculator
import os

class SimpleElementCollection():
    
    
    def __init__(self, element_type):
        self._element_type = element_type # e.g. Node, Link, Weir...
        self._quantities = {} # pairs of quantity ID and [elements]
        
        
    def add_element(self, element):
        if isinstance(element, simple_element.SimpleElement)\
            and element.get_element_type() == self._element_type:
            quantity_id = element.get_quantity_id()
            if quantity_id in self._quantities:
                if element not in self._quantities[quantity_id]:
                    self._quantities[quantity_id].append(element)
            else:
                self._quantities[quantity_id] = [element]

    
    def get_element_type(self):
        return self._element_type
        
        
    def get_all_element_ids(self):
        ids = set([])
        for qid, elements in self._quantities.items():
            ids.update([element.get_element_id() for element in elements])
        return sorted(list(ids))
        
    
    def get_element_ids_by_quantity(self, quantity_id):
        elements = self._quantities.get(quantity_id, [])
        return [element.get_element_id() for element in elements]
    
    
    def get_all_elements(self):
        all_elements = []
        for elements in self._quantities.values():
            all_elements.extend(elements)
        return all_elements
    
    
    def get_elements_by_quantity(self, quantity_id):
        return self._quantities.get(quantity_id, [])
        
    
    def get_elements_by_quantity_and_id(self, quantity_id, element_id):
        elements = self.get_elements_by_quantity(quantity_id)
        return [elem for elem in elements if elem.get_element_id() == element_id]
        
        
    def get_quantity_ids(self):
        return list(self._quantities.keys())
        

    def update_ts(self, dfs, filename):
        # dfs has to be a dictionary. pair of quantity ID and data frames.
        for quantity_id, df in dfs.items():
            if quantity_id in self._quantities:
                for element in self._quantities[quantity_id]:
                    element_col = self._find_column_in_dataframe(element, df)
                    if element_col is not None:
                        element.add_ts(filename, df[element_col])
                        

    def update_statistics(self):
        for qid, elements in self._quantities.items():
            for element in elements:
                for ts_name in element.get_ts_names():
                    element.add_stats(ts_name, statistics_calculator.
                                   get_all_stats(element.get_ts(ts_name)))
    
    
    def __str__(self):
        str1 = 'Element type: ' + self._element_type + os.linesep
        for element in self.get_all_elements():
            str1 += str(element) + os.linesep
        return str1
    
    
    def _find_column_in_dataframe(self, element, df):
        """
        find the dataframe column based on the element id

        Parameters
        ----------
        element : simple_element
            An element reference
        df : dataframe
            dataframe of results

        Returns
        -------
        col : string
            column  in data frame. None if not found

        """
        
        cols = list(df.columns)
        
        element_id = element.get_element_id()
        element_chainage = element.get_chainage()
        
        if element_id in cols:
            # found column without chainage
            return element_id
        
        sub_cols = [col for col in cols if (' ' in col) and (col[:col.rfind(' ')] == element_id)]
        if len(sub_cols) == 0:
            # element id not in columns
            return None
        
        if element_chainage == -1:
            # return the largest chainage
            return sub_cols[-1]
        
        chainages = [float(col.split(' ')[-1]) for col in sub_cols]
        chainages_diff = [abs(chainage - element_chainage) for chainage in chainages]
        # return the closest chainage
        return sub_cols[chainages_diff.index(min(chainages_diff))]
    
    
def test_element_manager():
    node_ts_manager = SimpleElementCollection('node')
    node_ts_manager.add_element(simple_element.SimpleElement('10001', 'node', 'WaterLevel'))
    node_ts_manager.add_element(simple_element.SimpleElement('10001', 'node', 'Spill'))
    node_ts_manager.add_element(simple_element.SimpleElement('10002', 'node', 'WaterLevel'))
    node_ts_manager.add_element(simple_element.SimpleElement('10002', 'node', 'Spill'))
    node_ts_manager.add_element(simple_element.SimpleElement('10003', 'node', 'WaterLevel'))
    
    print('\nshowing all element IDs:')
    print(node_ts_manager.get_all_element_ids())
    print('\nshowing all spill element IDs :')
    print(node_ts_manager.get_element_ids_by_quantity('Spill'))
    print('\nshowing all quantity IDs:')
    print(node_ts_manager.get_quantity_ids())
    
    print('\nshowing all elements:')
    print(node_ts_manager)
    print('\nshowing all spill elements:')
    for element in node_ts_manager.get_elements_by_quantity('Spill'):
        print(element)
     
    
def main():
    print("in res1d_element.py!")
    test_element_manager()


if __name__ == '__main__':
    main()
        