#!/usr/bin/env python
# coding: utf-8

# Author: copilot 
# Supervisor: Yi Wang

from __future__ import annotations

from typing import Dict, Optional
import pandas as pd
import math


class BaseElement():
    
    CHAINAGE_PRECISION: int = 6

    def __init__(
        self,
        element_id: str,
        element_alias: Optional[str],
        element_type: str,
        quantity_id: str,
        chainage: float = 0.0,
    ) -> None:

        self._element_id: str = element_id
        self._element_alias: Optional[str] = element_alias
        self._element_type: str = element_type.lower()
        self._quantity_id: Optional[str] = quantity_id
        self._chainage: float = chainage

        self._timeseries: Dict[str, pd.Series] = {}
        self._statistics: Dict[str, pd.Series] = {}

    # -------------------------
    # Identity
    # -------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseElement):
            return False
        return (
            self._element_id == other._element_id
            and self._element_alias == other._element_alias
            and self._element_type == other._element_type
            and self._quantity_id == other._quantity_id
            and math.isclose(self._chainage, other._chainage)
        )

    def __hash__(self) -> int:
        return hash(
            (
                self._element_type,
                self._quantity_id,
                self._element_id,
                self._element_alias,
                round(self._chainage, self.CHAINAGE_PRECISION),
            )
        )

    def __lt__(self, other: object):
        if not isinstance(other, BaseElement):
            return NotImplemented

        return (
            self._element_type,
            self._quantity_id,
            self._element_alias,
            self._element_id,
            self._chainage,
        ) < (
            other._element_type,
            other._quantity_id,
            other._element_alias,
            other._element_id,
            other._chainage,
        )

    # -------------------------
    # Metadata getters
    # -------------------------

    def get_element_id(self) -> str:
        return self._element_id

    def get_element_alias(self) -> Optional[str]:
        return self._element_alias

    def get_element_type(self) -> str:
        return self._element_type

    def get_quantity_id(self) -> Optional[str]:
        return self._quantity_id

    def get_chainage(self) -> float:
        return self._chainage

    def get_element_string(self) -> str:
        return f"{self._element_type}-{self._quantity_id}-{self._element_id}-{self._chainage}"

    # -------------------------
    # Time series
    # -------------------------

    def get_ts(self, ts_name: str) -> Optional[pd.Series]:
        return self._timeseries.get(ts_name)

    def get_ts_dataframe(self) -> pd.DataFrame:
        if not self._timeseries:
            return pd.DataFrame()
        return pd.concat(self._timeseries, axis=1).sort_index()

    def get_ts_dict(self) -> Dict[str, pd.Series]:
        return self._timeseries.copy()

    def get_ts_names(self) -> list[str]:
        return list(self._timeseries.keys())

    def remove_ts(self, ts_name: str) -> None:
        self._timeseries.pop(ts_name, None)

    def reset_ts(self) -> None:
        self._timeseries.clear()

    def add_ts(self, *args, **kwargs):
        raise NotImplementedError
    
    def update_ts(self, *args, **kwargs):
        raise NotImplementedError
        
    # -------------------------
    # Statistics
    # -------------------------

    def add_stats(self, ts_name: str, stats: pd.Series, overwrite: bool = True) -> None:
        if not isinstance(stats, pd.Series):
            raise TypeError("stats must be a pandas Series")

        if ts_name in self._statistics and not overwrite:
            raise ValueError(f"Statistics '{ts_name}' already exists")

        self._statistics[ts_name] = stats.copy()

    def get_stats(self, ts_name: str) -> Optional[pd.Series]:
        return self._statistics.get(ts_name)

    def get_stats_dataframe(self) -> pd.DataFrame:
        if not self._statistics:
            return pd.DataFrame()
        return pd.concat(self._statistics, axis=1)

    def get_stats_dict(self) -> Dict[str, pd.Series]:
        return self._statistics.copy()

    def remove_stats(self, ts_name: str) -> None:
        self._statistics.pop(ts_name, None)

    def reset_stats(self) -> None:
        self._statistics.clear()

    def update_statistics(self, calculator) -> None:
        """
        calculator: module or object providing get_all_stats(ts: Series) -> Series
        """
        for ts_name, ts in self._timeseries.items():
            stats = calculator.get_all_stats(ts)
            self._statistics[ts_name] = stats

    # -------------------------
    # String
    # -------------------------

    def __str__(self) -> str:
        return f"{self.get_element_string()}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._element_id}>"
