# -*- coding: utf-8 -*-

# Author: Yi Wang
# this module includes functions to calculate statistics for data frames

import numpy as np
import pandas as pd

default_window = '1h'

def mean(s):
    """
    returns mean of the pandas series

    Parameters
    ----------
    s : pandas series
        Input time series.

    Returns
    -------
    float
        Mean of input series.

    """    
    return s.mean()

def max(s):
    return s.max()

def min(s):
    return s.min()

def sum(s):
    return s.sum()

def max_block(s, window = default_window):
    """
    returns the maximums of a rolling block. eg. maximum 24 h average flow
    it assumes equal intervals along time axis

    Parameters
    ----------
    s : pd.Series
        Time series.
    window : int, timedelta, str, offset, optional
        Pandas time window. The default is '1H'. 
        e.g. 1 hour is '1H', 5 min is '5T' or '5min'

    Returns
    -------
    Float
        Maximums of series, rolling averaged.

    """
    s = s.rolling(window).mean()
    s = s[(s.index[0] + pd.Timedelta(window)):]
    return s.max()

def min_block(s, window = default_window):
    s = s.rolling(window).mean()
    s = s[(s.index[0] + pd.Timedelta(window)):]
    return s.min()

def integral_block(s, window = default_window):
    """
    This function calculate integrals of each column using index as time
    This function assumes the columns are in unit of quantity per second
    
    Parameters
    ----------
    s : pd.Series
        Time series.
    window : int, timedelta, str, offset, optional
        Pandas time window. The default is '1H'. 
        e.g. 1 hour is '1H', 5 min is '5T' or '5min'

    Returns
    -------
    s : pd.Series
        time series of integrals

    """
    if type(s.index) == pd.core.indexes.datetimes.DatetimeIndex:
        original_index = s.index
        s_index = s.reset_index(level=0)
        s_index = s_index - s_index.shift(1)
        s_index = s_index.iloc[:, 0].apply(lambda x: x.total_seconds())
        s = (s + s.shift(1))/2
        s = s.reset_index(drop=True)
        s = s.multiply(s_index, fill_value=0)
        s.index = original_index
        s = s.resample(window, closed = 'right').sum()
        return s.iloc[1:]
    else:
        return np.NaN

def integral(s):
    if s.size == 0:
        return np.NaN
    s = integral_block(s)
    return np.NaN if s is np.NaN else s.sum()

def last_timestep(s):
    return s.iloc[-1]

def positive_duration(s):
    """
    the duration when the values are positive, in seconds
    if two adjacent values have different signs, half of the time interval 
    is included. 

    Parameters
    ----------
    s : pd.Series
        Time series.

    Returns
    -------
    float
        time in seconds.

    """
    s = s.map(lambda x: 1 if x > 0 else 0)
    return integral(s)

def negative_duration(s):
    s = s.map(lambda x: 1 if x < 0 else 0)
    return integral(s)
    
def get_all_stats(s):
    return {
        'mean': mean(s), 
        'max': max(s),
        'min': min(s),
        'sum': sum(s),
        'max_1H': max_block(s),
        'max_24H': max_block(s, '1D'),
        'min_1H': min_block(s),
        'min_24H': min_block(s, '1D'),
        'integral': integral(s),
        'last_timestep': last_timestep(s),
        'positive_duration': positive_duration(s),
        'negative_duration': negative_duration(s)
        }
    
