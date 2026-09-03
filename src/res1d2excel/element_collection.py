#!/usr/bin/env python
# coding: utf-8

# Author: copilot 
# Supervisor: Yi Wang

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional, Union
import pandas as pd
import os
import warnings

from .base_element import BaseElement
from . import combined_element
from . import simple_element


ElementDataFrames = Dict[str, pd.DataFrame]
CombinedItem = Dict[str, Any]
AliasLookup = Dict[str, Dict[str, BaseElement]]


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
        
    def iter_elements(self) -> Iterator[BaseElement]:
        for elements in self._quantities.values():
            yield from elements.values()
            
    def __len__(self) -> int:
        return sum(len(e) for e in self._quantities.values())

    # -------------------------
    # Factory methods
    # -------------------------

    @classmethod
    def create_simple_collections_from_dataframes(
        cls,
        dfs: ElementDataFrames
    ) -> List["ElementCollection"]:
        element_collections: List[ElementCollection] = []

        for element_type, element_df in dfs.items():
            element_collections.append(
                cls.create_simple_collection_from_dataframe(
                    element_type,
                    element_df
                )
            )

        return element_collections

    @classmethod
    def create_simple_collection_from_dataframe(
        cls,
        element_type: str,
        element_df: pd.DataFrame
    ) -> "ElementCollection":
        collection = cls(element_type)

        if element_df.empty:
            return collection

        element_df = element_df.fillna(0)
        for _, row in element_df.iterrows():
            collection.add_element(cls._row_to_simple_element(element_type, row))

        return collection

    @classmethod
    def create_combined_collection(
        cls,
        combined: List[CombinedItem],
        element_collections: List["ElementCollection"],
        discharge_quantities: Iterable[str]
    ) -> "ElementCollection":
        combined_collection = cls("combined")
        if not combined:
            return combined_collection

        alias_lookup = cls._create_element_alias_lookup(element_collections)

        for item in combined:
            alias = item.get("alias")
            if not alias:
                raise ValueError("Combined item missing alias")
            if combined_collection.get_elements_by_quantity_and_id(
                    combined_element.CALCULATED_DISCHARGE,
                    alias):
                raise ValueError(f"Duplicate combined alias: {alias}")
            if not item.get("terms"):
                raise ValueError(f"Combined element '{alias}' has no terms")

            element = combined_element.CombinedElement(alias)
            seen_terms: set[tuple[str, Optional[str]]] = set()

            for term in item.get("terms", []):
                source = term.get("source", "").lower()
                term_alias = term.get("alias")
                op = term.get("op", "+")
                term_key = (source, term_alias)

                if term_key in seen_terms:
                    warnings.warn(
                        f"Combined element '{alias}': duplicate term "
                        f"{source}.{term_alias} ignored"
                    )
                    continue
                seen_terms.add(term_key)

                source_element = cls._get_combined_source_element(
                    alias_lookup,
                    source,
                    term_alias,
                    discharge_quantities
                )
                sign = 1 if op != "-" else -1
                element.add_element(source_element, sign)

            combined_collection.add_element(element)

        return combined_collection

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

    def update_statistics(self, calculator: Optional[Any] = None) -> None:
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

    @staticmethod
    def _row_to_simple_element(
        element_type: str,
        row: pd.Series
    ) -> simple_element.SimpleElement:
        alias = row.get("alias")
        if alias == 0:
            alias = None

        quantity = row.get("quantity")
        muid = str(row.get("muid"))
        chainage = row.get("chainage", 0.0)

        return simple_element.SimpleElement(
            muid,
            alias,
            element_type,
            quantity,
            chainage
        )

    @staticmethod
    def _create_element_alias_lookup(
        element_collections: Iterable["ElementCollection"]
    ) -> AliasLookup:
        alias_lookup: AliasLookup = {}

        for collection in element_collections:
            source = collection.get_element_type().lower()
            alias_lookup[source] = {}

            for element in collection.get_all_elements():
                alias = element.get_element_alias()
                if not alias:
                    continue
                if alias in alias_lookup[source]:
                    raise ValueError(f"Duplicate alias in {source}: {alias}")
                alias_lookup[source][alias] = element

        return alias_lookup

    @staticmethod
    def _get_combined_source_element(
        alias_lookup: AliasLookup,
        source: str,
        alias: Optional[str],
        discharge_quantities: Iterable[str]
    ) -> BaseElement:
        if source not in alias_lookup:
            raise ValueError(f"Invalid combined source: {source}")

        if not alias or alias not in alias_lookup[source]:
            raise ValueError(f"Combined alias not found: {source}.{alias}")

        element = alias_lookup[source][alias]
        if element.get_quantity_id() not in discharge_quantities:
            raise ValueError(f"{source}.{alias} is not a discharge-like quantity")

        return element
