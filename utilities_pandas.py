#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this is utilities for plotly and pandas

# to do
"""
mean_block()
sum_block()
last_timestep()
"""


import pandas as pd

def mean(df, rounding = 8):
    """
    average, regardless to index time intervals
    e.g. average level

    Parameters
    ----------
    df : pandas dataframe
        data frame for mean
    rounding : int, optional
        The default is 8.
        
    Returns
    -------
    list of double
        average of each column
    """
    if df.shape[0] == 0:
        return [0] * df.shape[1]
    if df.shape[1] == 0:
        return []
    return list(df.mean(axis = 0).round(rounding))

def sum(df, rounding = 8):
    """
    sum, regardless to index time intervals

    Parameters
    ----------
    df : pandas dataframe
        data frame for mean
    rounding : int, optional
        The default is 8.
        
    Returns
    -------
    list of double
        sum of each column
    """
    if df.shape[0] == 0:
        return [0] * df.shape[1]
    if df.shape[1] == 0:
        return []
    return list(df.sum(axis = 0).round(rounding))

def max(df, rounding = 8):
    """
    max, regardless to index time intervals
    e.g. maximum level or flow rate

    Parameters
    ----------
    df : pandas dataframe
        data frame for mean
    rounding : int, optional
        The default is 8.
        
    Returns
    -------
    list of double
        max of each column
    """
    if df.shape[0] == 0:
        return [0] * df.shape[1]
    if df.shape[1] == 0:
        return []
    return list(df.max(axis = 0).round(rounding))

def min(df, rounding = 8):
    """
    min, regardless to index time intervals
    e.g. minimum level or flow rate

    Parameters
    ----------
    df : pandas dataframe
        data frame for mean
    rounding : int, optional
        The default is 8.
        
    Returns
    -------
    list of double
        min of each column
    """
    if df.shape[0] == 0:
        return [0] * df.shape[1]
    if df.shape[1] == 0:
        return []
    return list(df.min(axis = 0).round(rounding))

def block_max(df, timedelta = '1D', rounding = 8):
    """
    this function calculate block maximum. 
    e.g. maximum 1 hour average level
    this function assumes the columns are in unit of quantity per second

    Parameters
    ----------
    df : pandas dataframe
        data frame for integration.
    timedelta : pandas.Timedelta, optional
        time block for integration. The default is '1D'.
    rounding : int, optional
        The default is 8.

    Returns
    -------
    list of double
        block maximum of each column

    """
    if df.shape[0] == 0:
        return [0] * df.shape[1]
    if df.shape[1] == 0:
        return []
    df = df.rolling(timedelta, closed = 'right').mean() #include 24:00 not 0:00
    return max(df, rounding)
       
def block_min(df, timedelta = '1D', rounding = 8):
    """
    this function calculate block minimum. 
    e.g. minimum 1 hour average level
    this function assumes the columns are in unit of quantity per second

    Parameters
    ----------
    df : pandas dataframe
        data frame for integration.
    timedelta : pandas.Timedelta, optional
        time block for integration. The default is '1D'.
    rounding : int, optional
        The default is 8.

    Returns
    -------
    list of double
        block minimum of each column

    """
    if df.shape[0] == 0:
        return [0] * df.shape[1]
    if df.shape[1] == 0:
        return []
    df = df.rolling(timedelta, closed = 'right').mean() #include 24:00 not 0:00
    return min(df, rounding)

def step_accumulated(df):
    """
    this function calculate integrals using index as time
    this function assumes the columns are in unit of quantity per second

    Parameters
    ----------
    df : pandas dataframe
        data frame for integration.

    Returns
    -------
    df : pandas dataframe
        integrals by original time index.

    """
    if type(df.index) == pd.core.indexes.datetimes.DatetimeIndex:
        original_index = df.index
        df_index = df.reset_index(level=0)
        df_index = df_index - df_index.shift(1)
        df_index = df_index.iloc[:, 0].apply(lambda x: x.total_seconds())
        df = (df + df.shift(1))/2
        df = df.reset_index(drop=True)
        for icol in range(df.shape[1]):
            df.iloc[:, icol] = df.iloc[:, icol].multiply(df_index, fill_value=0)
        
        df.index = original_index

        return df
    else:
        return None

def integral(df, rounding = 8):
    """
    this function calculate integrals using index as time. 
    e.g. total volumes
    this function assumes the columns are in unit of quantity per second
    Parameters
    ----------
    df : pandas dataframe
        data frame for integration.
    rounding : int, optional
        The default is 8.

    Returns
    -------
    list of double
        integrals of selected columns.

    """
    if df.shape[0] == 0:
        return [0] * df.shape[1]
    if df.shape[1] == 0:
        return []
    if type(df.index) == pd.core.indexes.datetimes.DatetimeIndex:
        df = step_accumulated(df)
        sums = df.sum(0)
    else:
        sums = df.sum(0)
    return [i for i in sums.round(rounding)]

def block_integral_max(df, timedelta = '1D', rounding = 8):
    """
    this function calculate block integral maximum. 
    e.g. maximum daily total volume
    this function assumes the columns are in unit of quantity per second

    Parameters
    ----------
    df : pandas dataframe
        data frame for integration.
    timedelta : pandas.Timedelta, optional
        time block for integration. The default is '1D'.
    rounding : int, optional
        The default is 8.

    Returns
    -------
    list of double
        block integral maximum of each column

    """
    if type(df.index) == pd.core.indexes.datetimes.DatetimeIndex:
        df = step_accumulated(df)
        df = df.rolling(timedelta, closed = 'right').mean() #include 24:00 not 0:00
        return max(df, rounding)
    else:
        return None

def block_integral_min(df, timedelta = '1D', rounding = 8):
    """
    this function calculate block integral minimum.
    e.g. minimum daily total volume
    this function assumes the columns are in unit of quantity per second

    Parameters
    ----------
    df : pandas dataframe
        data frame for integration.
    timedelta : pandas.Timedelta, optional
        time block for integration. The default is '1D'.
    rounding : int, optional
        The default is 8.

    Returns
    -------
    list of double
        block integral minimum of each column

    """
    if type(df.index) == pd.core.indexes.datetimes.DatetimeIndex:
        df = step_accumulated(df)
        df = df.rolling(timedelta, closed = 'right').mean() #include 24:00 not 0:00
        return min(df, rounding)
    else:
        return None

def block_integral(df, timedelta = '1D'):
    """
    this function calculate integrals using index as time
    e.g. daily total volumes
    this function assumes the columns are in unit of quantity per second

    Parameters
    ----------
    df : pandas dataframe
        data frame for integration.
    timedelta : pandas.Timedelta, optional
        time block for integration. The default is '1D'.

    Returns
    -------
    df : pandas dataframe
        integrals by given time delta.

    """
    if type(df.index) == pd.core.indexes.datetimes.DatetimeIndex:
        df = step_accumulated(df)
        df = df.resample(timedelta, closed = 'right').sum() #include 24:00 not 0:00
        return df
    else:
        return None
    
def block_integral_mean(df, timedelta = '1D', rounding = 8):
    """
    this function calculate average block integrals using index as time
    e.g. average daily total volume
    this function assumes the columns are in unit of quantity per second

    Parameters
    ----------
    df : pandas dataframe
        data frame for integration.
    timedelta : pandas.Timedelta, optional
        time block for integration. The default is '1D'.
    rounding : int, optional
        The default is 8.

    Returns
    -------
    df : pandas dataframe
        integrals by given time delta.

    """
    df = block_integral(df, timedelta)
    if df is None:
        return None
    else:
        if df.sum(axis = 1)[0] == 0:
            df = df.iloc[1:, :]
        return mean(df, rounding = rounding)

def main():
    print("in utilities_pandas.py!")


if __name__ == '__main__' and '__file__' not in globals():
    main()

