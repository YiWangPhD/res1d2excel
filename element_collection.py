#!/usr/bin/env python
# coding: utf-8

# Author: copilot 
# Supervisor: Yi Wang

from __future__ import annotations

from typing import Dict, List, Optional, Type, Union
import pandas as pd
import os

from base_element import BaseElement


class ElementCollection:
    
    CHAINAGE_LAST: int = -1

    def __init__(self, element_type: str) -> None:
        self._element_type: str = element_type
        # quantity_id -> {element: element}
        self._quantities: Dict[str, Dict[BaseElement, BaseElement]] = {}

    # -------------------------
    # Element management
    # -------------------------

    def add_element(self, element: BaseElement) -> None:
        if not isinstance(element, BaseElement):
            raise TypeError("element must be BaseElement")

        if element.get_element_type() != self._element_type:
            raise ValueError("Element type mismatch")

        quantity_id = element.get_quantity_id()

        if quantity_id not in self._quantities:
            self._quantities[quantity_id] = {}

        self._quantities[quantity_id][element] = element

    def get_element_type(self) -> str:
        return self._element_type

    # -------------------------
    # Query - IDs
    # -------------------------

    def get_all_element_ids(self) -> List[str]:
        ids: set[str] = set()

        for elements in self._quantities.values():
            ids.update(e.get_element_id() for e in elements.values())

        return sorted(ids)

    def get_element_ids_by_quantity(self, quantity_id: str) -> List[str]:
        elements = self._quantities.get(quantity_id, {})
        return sorted(set(e.get_element_id() for e in elements.values()))

    # -------------------------
    # Query - elements
    # -------------------------

    def get_all_elements(self) -> List[BaseElement]:
        result: List[BaseElement] = []
        for elements in self._quantities.values():
            result.extend(elements.values())
        return result

    def get_elements_by_quantity(self, quantity_id: str) -> List[BaseElement]:
        return list(self._quantities.get(quantity_id, {}).values())

    def get_elements_by_quantity_and_id(
        self,
        quantity_id: str,
        element_id: str
    ) -> List[BaseElement]:

        return [
            e for e in self.get_elements_by_quantity(quantity_id)
            if e.get_element_id() == element_id
        ]

    def get_quantity_ids(self) -> List[str]:
        return list(self._quantities.keys())
        
    def iter_elements(self):
        for elements in self._quantities.values():
            yield from elements.values()
            
    def __len__(self):
        return sum(len(e) for e in self._quantities.values())

    # -------------------------
    # Add time series (only for SimpleElement)
    # -------------------------

    def add_ts(self, dfs: Dict[str, pd.DataFrame], filename: str) -> None:
        """
        add time series from raw dataframes.
        Only applicable to elements that support external data injection.
        """

        if not isinstance(dfs, dict):
            raise TypeError("dfs must be a dict")

        if not filename:
            raise ValueError("filename must be provided")

        for quantity_id, df in dfs.items():

            if not isinstance(df, pd.DataFrame):
                raise TypeError(f"{quantity_id} must map to a DataFrame")

            if quantity_id not in self._quantities:
                continue

            for element in self._quantities[quantity_id].values():

                col = self._find_column_in_dataframe(element, df)

                if col is not None:
                    element.add_ts(filename, df[col])

    # -------------------------
    # Update derived elements (CombinedElement)
    # -------------------------

    def update_ts(self) -> None:
        """
        Call update_ts() for combined elements that compute their own time series.
        """

        for element in self.get_all_elements():
            element.update_ts()

    # -------------------------
    # Statistics
    # -------------------------

    def update_statistics(self, calculator=None) -> None:
        for element in self.get_all_elements():
            element.update_statistics(calculator)

    # -------------------------
    # String
    # -------------------------

    def __str__(self) -> str:
        str1 = 'Element type: ' + self._element_type + os.linesep
        for element in self.get_all_elements():
            str1 += str(element) + os.linesep
        return str1

    def __repr__(self) -> str:
        return f"<ElementCollection type={self._element_type}, quantities={len(self._quantities)}>"

    # -------------------------
    # Internal helpers
    # -------------------------

    def _find_column_in_dataframe(
        self,
        element: BaseElement,
        df: pd.DataFrame
    ) -> Optional[Union[str, tuple[str, float]]]:

        cols = df.columns

        element_id = element.get_element_id()
        element_chainage = element.get_chainage()

        # Simple columns
        if not isinstance(cols, pd.MultiIndex):
            return element_id if element_id in cols else None

        # MultiIndex case
        level0 = cols.get_level_values(0)
        if element_id not in level0:
            return None

        sub_df = df[element_id]
        chainages = sub_df.columns

        if element_chainage == self.CHAINAGE_LAST:
            return (element_id, chainages[-1])

        closest = min(chainages, key=lambda c: abs(c - element_chainage))
        return (element_id, closest)