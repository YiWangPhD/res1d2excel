#!/usr/bin/env python
# coding: utf-8

# Author: copilot 
# Supervisor: Yi Wang

# this class configurates one element and quantity to be extracted from res1d
# this class also contains time series and statistics, tagged by res1d file names

import pandas as pd
from typing import Optional
from .base_element import BaseElement
from . import statistics_calculator


class SimpleElement(BaseElement):
    
    def __init__(
        self,
        element_id: str,
        element_alias: Optional[str],
        element_type: str,
        quantity_id: str,
        chainage: float = 0.0,
    ) -> None:

        super().__init__(
            element_id=element_id,
            element_alias=element_alias,
            element_type=element_type,
            quantity_id=quantity_id,
            chainage=chainage,
        )

    # -------------------------
    # Time series (SimpleElement owns raw data)
    # -------------------------

    def add_ts(self, ts_name: str, ts: pd.Series, overwrite: bool = True) -> None:
        if not isinstance(ts, pd.Series):
            raise TypeError("ts must be a pandas Series")

        if ts_name in self._timeseries and not overwrite:
            raise ValueError(f"Timeseries '{ts_name}' already exists")

        self._timeseries[ts_name] = ts.copy()

    def update_ts(self, *args, **kwargs) -> None:
        """
        For SimpleElement, time series are externally provided.
        This method is a no-op (or can be used for validation later).
        """
        pass

    # -------------------------
    # String
    # -------------------------

    def __str__(self) -> str:
        base = f"Type: {self._element_type}, ID: {self._element_id}, "

        if self._element_alias:
            base += f"Alias: {self._element_alias}, "

        base += f"Quantity: {self._quantity_id}, Chainage: {self._chainage}"
        return base
        
    # -------------------------
    # Statistics (reuse base)
    # -------------------------

    def update_statistics(self, calculator=None) -> None:
        super().update_statistics(calculator or statistics_calculator)

    
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
