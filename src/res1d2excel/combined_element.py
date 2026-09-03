#!/usr/bin/env python
# coding: utf-8

# Author: copilot 
# Supervisor: Yi Wang

# this class configurates a combination of many elements and quantity to be extracted from res1d
# this class also contains time series and statistics, tagged by res1d file names
from __future__ import annotations

from typing import Dict, Optional, List
import pandas as pd
import warnings

from .base_element import BaseElement
from . import statistics_calculator


CALCULATED_DISCHARGE = "CalculatedDischarge"


class CombinedElement(BaseElement):
    
    def __init__(
        self, 
        name: str, 
        quantity_id: str = CALCULATED_DISCHARGE,
        fill_outside: Optional[float] = 0,
        interpolation_method: str = "time",
        ) -> None:
        super().__init__(
            element_id=name,
            element_alias=name,
            element_type="combined",
            quantity_id=quantity_id,
            chainage=0.0,
        )

        # element -> element (hash-based)
        self._positive_elements: Dict[BaseElement, BaseElement] = {}
        self._negative_elements: Dict[BaseElement, BaseElement] = {}
        
        # interpolation and fill
        self._fill_outside: Optional[float] = fill_outside
        self._interpolation_method: str = interpolation_method

    # -------------------------
    # Element management
    # -------------------------

    def add_element(self, element: BaseElement, sign: int = 1) -> None:
        if not isinstance(element, BaseElement):
            raise TypeError("element must be a BaseElement")

        if sign >= 0:
            self._positive_elements[element] = element
        else:
            self._negative_elements[element] = element

    def remove_element(self, element: BaseElement) -> None:
        self._positive_elements.pop(element, None)
        self._negative_elements.pop(element, None)

    def reset_elements(self) -> None:
        self._positive_elements.clear()
        self._negative_elements.clear()

    def get_elements(self) -> List[BaseElement]:
        result = list(self._positive_elements.values())
        result.extend(self._negative_elements.values())
        return result

    # -------------------------
    # Equation
    # -------------------------

    def print_equation(self) -> str:
        lines: List[str] = []

        for e in self._positive_elements:
            lines.append(f"+ {self._get_element_reference(e)}")

        for e in self._negative_elements:
            lines.append(f"- {self._get_element_reference(e)}")

        return "\n".join(lines) if lines else "0"

    # -------------------------
    # Time series (derived)
    # -------------------------

    def update_ts(self) -> None:
        """
        Compute time series from component elements.
        """

        ts_names = set()

        for e in self.get_elements():
            ts_names.update(e.get_ts_names())

        for ts_name in ts_names:

            pos_series: List[pd.Series] = []
            neg_series: List[pd.Series] = []
            missing: List[BaseElement] = []

            # positive elements
            for e in self._positive_elements:
                ts = e.get_ts(ts_name)
                if ts is None:
                    missing.append(e)
                else:
                    pos_series.append(ts)

            # negative elements
            for e in self._negative_elements:
                ts = e.get_ts(ts_name)
                if ts is None:
                    missing.append(e)
                else:
                    neg_series.append(ts)

            # warning if missing
            if missing:
                warnings.warn(
                    f"CombinedElement '{self._element_id}': "
                    f"missing timeseries '{ts_name}' for {len(missing)} element(s)"
                )

            if not pos_series and not neg_series:
                return 
                        
            aligned_pos, aligned_neg = self._prepare_series(pos_series, neg_series)
            
            result = self._compute_result(aligned_pos, aligned_neg)

            if result is not None:
                self._timeseries[ts_name] = result

    def add_ts(self, *args, **kwargs):
        """
        For CombinedElement, time series are updated from elements.
        This method is a no-op (or can be used for validation later).
        """
        warnings.warn(
            f"Skipped: adding time series to CombinedElement '{self._element_id}'"
        )
        pass

    # -------------------------
    # Statistics (reuse base)
    # -------------------------

    def update_statistics(self, calculator=None) -> None:
        super().update_statistics(calculator or statistics_calculator)

    # -------------------------
    # String
    # -------------------------

    def __str__(self) -> str:
        lines: List[str] = []

        for e in self._positive_elements:
            lines.append(f"+ {e.get_element_string()}")

        for e in self._negative_elements:
            lines.append(f"- {e.get_element_string()}")

        equation = "\n".join(lines) if lines else "0"
        return f"{self._element_id} =\n{equation}"

    def __repr__(self) -> str:
        return f"<CombinedElement {self._element_id}>"
    
    # -------------------------
    # Internal helpers
    # -------------------------

    def _get_element_reference(self, element: BaseElement) -> str:
        alias = element.get_element_alias()
        if alias:
            return f"{element.get_element_type()}.{alias}"
        return element.get_element_string()
    
    def _get_common_index(self, series_list: List[pd.Series]) -> pd.Index:
        index = series_list[0].index
        for s in series_list[1:]:
            index = index.union(s.index)
        return index

    def _infer_min_frequency(self, series_list: List[pd.Series]) -> Optional[pd.Timedelta]:
        deltas = []
    
        for s in series_list:
            diffs = s.index.to_series().diff().dropna()
            if not diffs.empty:
                deltas.append(diffs.min())
    
        return min(deltas) if deltas else None

    def _build_target_index(self, series_list: List[pd.Series]) -> pd.DatetimeIndex:
        common_index = self._get_common_index(series_list)
        freq = self._infer_min_frequency(series_list)
    
        if freq is not None:
            return pd.date_range(
                start=common_index.min(),
                end=common_index.max(),
                freq=freq,
            )
    
        return common_index

    def _align_series(
        self,
        s: pd.Series,
        index: pd.DatetimeIndex,
        fill_outside: Optional[float] = None
    ) -> pd.Series:
    
        # Reindex first
        s2 = s.reindex(index)
    
        # Interpolate only where possible
        s2 = s2.interpolate(method=self._interpolation_method)
    
        # Identify valid range
        start = s.first_valid_index()
        end = s.last_valid_index()
    
        if start is None or end is None:
            return s2 * 0 if fill_outside == 0 else s2
    
        # Mask outside region
        outside_mask = (s2.index < start) | (s2.index > end)
    
        if fill_outside is None:
            # keep NaN outside
            s2[outside_mask] = pd.NA
        else:
            s2[outside_mask] = fill_outside
    
        return s2
    
    def _prepare_series(
        self,
        pos_series: List[pd.Series],
        neg_series: List[pd.Series],
    ) -> tuple[List[pd.Series], List[pd.Series]]:
    
        series_list = pos_series + neg_series
        if not series_list:
            return [], []
    
        target_index = self._build_target_index(series_list)
    
        aligned_pos = [self._align_series(s, target_index, self._fill_outside) for s in pos_series]
        aligned_neg = [self._align_series(s, target_index, self._fill_outside) for s in neg_series]
    
        return aligned_pos, aligned_neg

    def _sum_series(self, series_list: List[pd.Series]) -> Optional[pd.Series]:
        if not series_list:
            return None
    
        result = series_list[0]
        for s in series_list[1:]:
            result = result.add(s, fill_value=0)
    
        return result
    
    def _compute_result(
        self,
        pos_series: List[pd.Series],
        neg_series: List[pd.Series],
    ) -> Optional[pd.Series]:
    
        pos_result = self._sum_series(pos_series)
        neg_result = self._sum_series(neg_series)
    
        if pos_result is None and neg_result is None:
            return None
    
        if pos_result is None:
            return -neg_result
    
        if neg_result is None:
            return pos_result
    
        return pos_result - neg_result
