#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this class configurates one element and quantity to be extracted from res1d
# this class also contains time series and statistics, tagged by res1d file names


import pandas as pd

class SimpleElement():
    
    
    def __init__(self, element_id, element_alias, element_type, quantity_id, chainage = 0.0):
        self._element_id = element_id
        self._element_alias = element_alias
        self._element_type = element_type.lower()
        self._quantity_id = quantity_id
        self._chainage = chainage
        self._timeseries = {}
        self._statistics = {}
    
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self._element_id == other._element_id) and \
                (self._element_alias == other._element_alias) and \
                (self._element_type == other._element_type) and \
                (self._quantity_id == other._quantity_id) and \
                (self._chainage == other._chainage)
        else:
            return False
    
    
    def __lt__(self, other):
        return ((self._element_type, self._quantity_id, self._element_alias, self._element_id, self._chainage) <
                (other._element_type, other._quantity_id, other._element_alias, other._element_id, other._chainage))


    def __hash__(self):
          return hash((self._element_type, self._quantity_id, self._element_id, self._element_alias, self._chainage))
      
      
    def __str__(self):
        str1 = f'Type: {self._element_type}, ID: {self._element_id}, '
        if self._element_alias is not None:
            str1 += f'Alias: {self._element_alias}, '
        str1 += f'Quantity: {self._quantity_id}, Chainage {self._chainage}'
        return str1

        
    def get_element_id(self):
        return self._element_id
    
    def get_element_alias(self):
        return self._element_alias
    
    
    def get_element_string(self):
        return f'{self._element_type}-{self._quantity_id}-{self._element_id}-{self._chainage}'
    
    def get_element_type(self):
        return self._element_type
    
    
    def get_quantity_id(self):
        return self._quantity_id
    
    
    def get_chainage(self):
        return self._chainage
    
    
    def add_ts(self, ts_name, ts):
        self._timeseries[ts_name] = ts.copy()
        
        
    def get_ts(self, ts_name):
        return self._timeseries.get(ts_name, None)
    
    
    def get_ts_dataframe(self):
        return pd.DataFrame(self._timeseries)
    
        
    def get_ts_dict(self):
        return self._timeseries
    
    
    def get_ts_names(self):
        return list(self._timeseries.keys())
    
    
    def remove_ts(self, ts_name):
        self._timeseries.pop(ts_name, None)
        
        
    def reset_ts(self):
        self._timeseries = {}
    
    
    def add_stats(self, ts_name, stats):
        self._statistics[ts_name] = stats
        
        
    def get_stats(self, ts_name):
        return self._statistics.get(ts_name, None)
    
    
    def get_stats_dataframe(self):
        return pd.DataFrame(self._statistics)
    
    
    def get_stats_dict(self):
        return self._statistics
    
    
    def remove_stats(self, ts_name):
        self._statistics.pop(ts_name, None)
        
        
    def reset_stats(self):
        self._statistics = {}
        
    
def test_element():
    node1 = SimpleElement('10001', '1001_level', 'node', 'WaterLevel')
    print(node1)
    node1.add_ts('file1', pd.Series(data={'a': 1, 'b': 2, 'c': 3}))
    node1.add_ts('file2', pd.Series(data={'a': 12, 'b': 13, 'c': 14}))
    print(node1.get_ts('file1'))
    node1.add_stats('file1', pd.Series(data={'mean': 1, 'std': 1, 'max': 3}))
    node1.add_stats('file2', pd.Series(data={'mean': 13, 'std': 1, 'max': 14}))
    print(node1.get_stats('file1'))
    print(node1.get_ts_dataframe())
    print(node1.get_stats_dataframe())

def main():
    print("in simple_element.py!")
    test_element()


if __name__ == '__main__':
    main()