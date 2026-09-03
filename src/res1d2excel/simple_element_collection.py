#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this class manages elements to be extracted from res1d
# quantities is dictionary of list, in format:
#    quantity_id: [elements]

# added Feb 13, 2025:
# 1. check for duplicates before adding element
# 2. get_elements_by_quantity_and_id

# updated May 2025:
# 1. changed _quantities structure. it now has dictionary of elements as values, instead of list of elements
# 2. updated the find column function to accomodate new res1d dataframe (multi index for muid and chainage)

# update Aug 2026:
# replaced by element_collection.py

from typing import Dict, List, Optional, Union
from . import simple_element
from . import statistics_calculator
import os
import pandas as pd

class SimpleElementCollection():
    
    
    def __init__(self, element_type: str) -> None:
        self._element_type: str = element_type # e.g. Node, Link, Weir...
        # quantity_id -> {element: element}
        self._quantities: Dict[str, Dict[simple_element.SimpleElement, simple_element.SimpleElement]] = {}
        
        
    def add_element(self, element: simple_element.SimpleElement) -> None:
        if not isinstance(element, simple_element.SimpleElement):
            raise TypeError("element must be SimpleElement")
        if element.get_element_type() != self._element_type:
            raise ValueError("Element type mismatch")
        quantity_id = element.get_quantity_id()
        if quantity_id in self._quantities:
            self._quantities[quantity_id][element] = element
        else:
            self._quantities[quantity_id] = {element: element}

    
    def get_element_type(self) -> str:
        return self._element_type
        
        
    def get_all_element_ids(self) -> List[str]:
        ids = set([])
        for qid in self._quantities:
            ids.update(self.get_element_ids_by_quantity(qid))
        return sorted(list(ids))
        
    
    def get_element_ids_by_quantity(self, quantity_id: str) -> List[str]:
        elements = self._quantities.get(quantity_id, {})
        ids = [element.get_element_id() for element in elements.values()]
        return sorted(set(ids))
    
    
    def get_all_elements(self) -> List[simple_element.SimpleElement]:
        all_elements = []
        for elements in self._quantities.values():
                all_elements.extend(elements.values())
        return all_elements
    
    
    def get_elements_by_quantity(self, quantity_id: str) -> List[simple_element.SimpleElement]:
        return list(self._quantities.get(quantity_id, {}).values())
        
    
    def get_elements_by_quantity_and_id(
            self,
            quantity_id: str,
            element_id: str
            ) -> List[simple_element.SimpleElement]:
        elements = self.get_elements_by_quantity(quantity_id)
        return [elem for elem in elements if elem.get_element_id() == element_id]
        
        
    def get_quantity_ids(self) -> List[str]:
        return list(self._quantities.keys())
        

    def update_ts(
            self,
            dfs: Dict[str, pd.DataFrame],
            filename: str
            ) -> None:
        # dfs has to be a dictionary. pair of quantity ID and data frames.        
        if not isinstance(dfs, dict):
                raise TypeError("dfs must be a dict")
                
        for quantity_id, df in dfs.items():
            if not isinstance(df, pd.DataFrame):
                raise TypeError(f"{quantity_id} must map to a DataFrame")
            if quantity_id not in self._quantities:
                continue
            for element in self._quantities[quantity_id].values():
                element_col = self._find_column_in_dataframe(element, df)
                if element_col is not None:
                    element.add_ts(filename, df[element_col])
                        

    def update_statistics(self) -> None:
        for qid, elements in self._quantities.items():
            for element in elements.values():
                ts_dict = element.get_ts_dict()
                for ts_name, ts in ts_dict.items():
                    element.add_stats(ts_name, statistics_calculator.get_all_stats(ts))
                    
    
    def __str__(self) -> str:
        str1 = 'Element type: ' + self._element_type + os.linesep
        for element in self.get_all_elements():
            str1 += str(element) + os.linesep
        return str1
    
    
    def __repr__(self) -> str:
        return f"<SimpleElementCollection type={self._element_type}, quantities={len(self._quantities)}>"
    
    
    def _find_column_in_dataframe(
            self,
            element: simple_element.SimpleElement,
            df: pd.DataFrame
            ) -> Optional[Union[str, tuple[str, float]]]:
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
            - str (for single-level columns)
            - (element_id, chainage) tuple for MultiIndex
            - None if not found

        """
        CHAINAGE_LAST = -1
        
        cols = df.columns
        
        element_id = element.get_element_id()
        element_chainage = element.get_chainage()
        
        if not isinstance(cols, pd.MultiIndex):
            # simple column, element_id only
            return element_id if element_id in cols else None
        
        # multi index, (element_id, chainage)
        level0 = cols.get_level_values(0)
        if element_id not in level0:
            return None
        
        sub_df = df[element_id]
        chainages = sub_df.columns
    
        if element_chainage == CHAINAGE_LAST:
            return (element_id, chainages[-1])
    
        closest = min(chainages, key=lambda c: abs(c - element_chainage))
        return (element_id, closest)

    
def test_element_manager():
    node_ts_manager = SimpleElementCollection('node')
    node_ts_manager.add_element(simple_element.SimpleElement('C14150801', '', 'node', 'WaterLevel'))
    node_ts_manager.add_element(simple_element.SimpleElement('C14150801', '', 'node', 'Spill'))
    node_ts_manager.add_element(simple_element.SimpleElement('C15155101', '', 'node', 'WaterLevel'))
    node_ts_manager.add_element(simple_element.SimpleElement('C15155101', '', 'node', 'Spill'))
    
    print('\nshowing all element IDs:')
    print(node_ts_manager.get_all_element_ids())
    print('\nshowing all spill element IDs :')
    print(node_ts_manager.get_element_ids_by_quantity('Spill'))
    print(node_ts_manager.get_element_ids_by_quantity('Discharge'))
    print('\nshowing all quantity IDs:')
    print(node_ts_manager.get_quantity_ids())
    
    print('\nshowing all elements:')
    print(node_ts_manager)
    print('\nshowing all spill elements:')
    for element in node_ts_manager.get_elements_by_quantity('Spill'):
        print(element)
    for element in node_ts_manager.get_all_elements():
        print(repr(element))
     
    
def main():
    print("in res1d_element.py!")
    test_element_manager()


if __name__ == '__main__':
    main()
        
