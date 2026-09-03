#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this is the res1d class module

import os
import sys
import pandas as pd
import numpy as np

from . import utilities

from mikeio1d.mikepath import MikePath
MikePath.setup_mike_installation(sys.path)

import clr

clr.AddReference("DHI.Mike1D.ResultDataAccess")
from DHI.Mike1D.ResultDataAccess import ResultData

clr.AddReference("DHI.Mike1D.Generic")
from DHI.Mike1D.Generic import Connection


class Res1D:
    
    def _res1d_time_to_pd_timestamp(self, t):
        """
        convert res1d time stamp to pandas time stamp

        Parameters
        ----------
        t : result data time

        Returns
        -------
        pandas timestamp

        """
        return pd.Timestamp(year=t.get_Year(), 
                            month=t.get_Month(), 
                            day=t.get_Day(), 
                            hour=t.get_Hour(), 
                            minute=t.get_Minute(), 
                            second=t.get_Second())
    
    
    def _get_time(self, from_time_stamp=None, to_time_stamp=None):
        """
        get indices and time stamps from res1d file. options to limit start 
        and end time

        Parameters
        ----------
        from_time_stamp : pd.Timestamp, optional
            start time. The default is None.
        to_time_stamp : pd.Timestamp, optional
            end time. The default is None.

        Returns
        -------
        list
            lists of indices and pd.Timestamp.

        """
        time_stamps = [self._res1d_time_to_pd_timestamp(t) 
                       for t in list(self.result_data.TimesList)]
        if not time_stamps:
            return [], pd.DatetimeIndex([])

        from_time_stamp = from_time_stamp or time_stamps[0]
        to_time_stamp = to_time_stamp or time_stamps[-1]

        indices_time_stamp = [i for i, t in enumerate(time_stamps) 
                              if from_time_stamp <= t <= to_time_stamp]
        return indices_time_stamp, pd.DatetimeIndex(
            [time_stamps[i] for i in indices_time_stamp]
            )


    def _validate_file_path(self, file_path):
        """
        validate if file exists

        Parameters
        ----------
        file_path : str
            path fo res1d file.

        Raises
        ------
        FileNotFoundError
            File does not exist

        Returns
        -------
        None.

        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File does not exist: {file_path}")


    def __init__(self, file_path):
        """
        initiate instance. read from res1d file and load properties

        Parameters
        ----------
        file_path : str
            path to res1d file.

        Returns
        -------
        None.

        """
        self._validate_file_path(file_path)
        self.result_data = ResultData()
        self.result_data.Connection = Connection.Create(file_path)
        self.result_data.Load()
        self.from_time_stamp = self._res1d_time_to_pd_timestamp(
            self.result_data.StartTime)
        self.to_time_stamp = self._res1d_time_to_pd_timestamp(
            self.result_data.EndTime)
        self.time_stamp_indices, self.df_time_stamps = self._get_time()


    def setTimeRange(self, from_time_stamp, to_time_stamp):
        """
        update start and end time. time series extracted will be limited to
        this period

        Parameters
        ----------
        from_time_stamp : pd.Timestamp
            start time.
        to_time_stamp : pd.Timestamp
            end time.

        Returns
        -------
        None.

        """
        self.time_stamp_indices, \
        self.df_time_stamps = self._get_time(from_time_stamp, to_time_stamp)
        self.from_time_stamp = self.df_time_stamps[0]
        self.to_time_stamp = self.df_time_stamps[-1]


    def _get_element_data_frame(self, elements, element_IDs, extraction_IDs,
                            quantity_IDs):
        """
        generic method to extract data from elements. 

        Parameters
        ----------
        elements : Res1D elements
            can be Nodes, Catchments, Reaches
        element_IDs : dict
            Dictionary, pair of element ID and position
        extraction_IDs : list
            list of element IDs to extract data
        quantity_IDs : list
            list of quantities to extract data

        Returns
        -------
        df_elem : dict
            dictionary of pandas data frames. one df per quantity.

        """
        extraction_IDs = utilities.list_cleanup(extraction_IDs)
        extraction_IDs = [eId for eId in extraction_IDs if eId in element_IDs]
        
        df_elem = {}
        for quantity_ID in quantity_IDs:
            df_elem[quantity_ID] = []
        for name in extraction_IDs:
            element_ref = self._create_default_element_ref(
                name, elements, element_IDs[name])
            for di in element_ref.data_items:
                quantity_ID = di.Quantity.Id
                if quantity_ID in quantity_IDs:
                    data = self._get_data_item_array(di)
                    column_count = self._get_data_column_count(data)
                    chainages = None
                    if column_count > 1:
                        chainages = self._get_element_chainages(
                            element_ref.element, column_count, name)
                    d = self._data_array_to_frame(
                        name, data, chainages, strict_chainages=True)
                    df_elem[quantity_ID].append(d)
        return self._finalize_quantity_frames(df_elem)


    def _create_default_element_ref(self, name, elements, element_index):
        element = elements.get_Item(element_index)
        return type('DefaultElementRef', (), {
            'muid': name,
            'element': element,
            'data_items': element.DataItems
        })()


    def _get_data_item_array(self, data_item, element_index=None):
        """
        Get a numpy-compatible time-series array from a res1d data item.
        """
        if element_index is not None:
            try:
                data = np.asarray(data_item.CreateTimeSeriesData(element_index))
                if data.ndim > 0:
                    return data
            except Exception:
                pass
        data = np.asarray(data_item.CreateDataArray())
        if element_index is not None and data.ndim > 1:
            return data[:, element_index]
        return data


    def _get_data_column_count(self, data):
        data = np.asarray(data)
        if data.ndim <= 1:
            return 1
        return data.shape[1]


    def _get_element_chainages(self, elem, column_count, element_name):
        if not hasattr(elem, 'get_GridPoints'):
            return None
        chainages = [gp.get_Chainage() for gp in elem.get_GridPoints()]
        if column_count * 2 == len(chainages) + 3:
            # all Q points plus first and last H points, e.g. AD
            return [chainages[0], *chainages[1::2], chainages[-1]]
        if column_count * 2 == len(chainages) + 1:
            # H points only
            return chainages[0::2]
        if column_count * 2 == len(chainages) - 1:
            # Q points only
            return chainages[1::2]
        raise Exception(
            f"At Reach {element_name}, we cannot match chainages with data "
            f"items. There are {column_count} columns and "
            f"{len(chainages)} chainages")


    def _data_array_to_frame(
            self, name, data, chainages=None, strict_chainages=False):
        data = np.asarray(data)
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        d = pd.DataFrame(data)
        if d.shape[1] == 1:
            d.columns = [name]
            return d

        if chainages is None or len(chainages) != d.shape[1]:
            if strict_chainages:
                chainage_count = 0 if chainages is None else len(chainages)
                raise Exception(
                    f"At {name}, we cannot match chainages with data items. "
                    f"There are {d.shape[1]} columns and "
                    f"{chainage_count} chainages")
            chainages = range(d.shape[1])

        d.columns = pd.MultiIndex.from_tuples(
            [(name, chainage) for chainage in chainages])
        d.columns = d.columns.set_names(['muid', 'chainage'])
        return d


    def _data_item_to_frame(
            self, name, data_item, chainages=None, element_index=None,
            strict_chainages=False):
        data = self._get_data_item_array(data_item, element_index)
        return self._data_array_to_frame(
            name, data, chainages, strict_chainages)


    def _finalize_quantity_frames(self, df_elem):
        for df in df_elem:
            if len(df_elem[df]) > 0:
                df_elem[df] = pd.concat(df_elem[df], axis = 1)
                if df_elem[df].size > 0:
                    df_elem[df] = df_elem[df].iloc[self.time_stamp_indices]
                    df_elem[df].index = self.df_time_stamps
            else:
                df_elem[df] = pd.DataFrame(index = self.df_time_stamps)
        return df_elem
    
