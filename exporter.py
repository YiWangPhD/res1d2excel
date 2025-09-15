# -*- coding: utf-8 -*-

# Author: Yi Wang
# it takes Simple element Collections and extracts dataframes
# it also takes combined elements and extracts dataframes
# it extracts by element (one dataframe per element, it has data from all res1d files)
# it extracts by res1d file (one dataframe per res1d file, it has data from all elements)
# it extracts statistics (one dataframe per stat)

import pandas as pd

def dataframe_by_element(elem_collection_list):
    """
    iterate through list of simple element collections and 
    extract data frames of time series to a dictionary with:
        key: Type-Quantity-ID-Chainage or Alias if it is not None
        value: dataframe
    
    Parameters
    ----------
    elem_collection_list : list of simple element collections
        list of simple element collections

    Returns
    -------
    dfs: dict of dataframes
    """
    dfs = {}
    for elem_collection in elem_collection_list:
        for elem in elem_collection.get_all_elements():
            key = elem.get_element_alias()
            if key is None:
                key = elem.get_element_string()
            dfs[key] = elem.get_ts_dataframe()
    
    return dfs

def dataframe_by_file(elem_collection_list):
    """
    take dict of dataframes from 'dataframe_by_element' method
    transfer to a new dict of dataframes organized by file (or short name)
        key: short name
        value: dataframe

    Parameters
    ----------
    elem_collection_list : list of simple element collections
        list of simple element collections

    Returns
    -------
    dfs : dictionary of dataframes

    """
    dfs2 = dataframe_by_element(elem_collection_list)
    dfs = {}
    
    # collect all short names from elements
    short_names = []
    for k, v in dfs2.items():
        if v.shape[1] > 0:
            short_names.extend(list(v.columns))
    short_names = list(set(short_names))
    short_names.sort()
    
    for short_name in short_names:
        dfs[short_name] = pd.DataFrame({
            k : v[short_name] for k, v in dfs2.items() if v.shape[1] > 0 and short_name in v
            })
    
    return dfs

def dataframes_stats(elem_collection_list):
    """
    iterate through list of simple element collections and 
    extract data frames of statostocs to a dictionary with:
        key: statistic name
        value: dataframe of statistics

    Parameters
    ----------
    elem_collection_list : list of simple element collections
        list of simple element collections

    Returns
    -------
    dfs : dictionary of dataframes

    """
    dfs = {} # key: element alias or string, value: element stats dictionary
    for elem_collection in elem_collection_list:
        for elem in elem_collection.get_all_elements():
            key = elem.get_element_alias()
            if key is None:
                key = elem.get_element_string()
            dfs[key] = elem.get_stats_dict()
    
    stat_names = [k for elem_dict in dfs.values() for tag_dict in elem_dict.values() for k in tag_dict.keys()]
    stat_names = list(set(stat_names))
    stat_names.sort()
    
    dfs2 = {stat_name:{} for stat_name in stat_names}
    
    for elem_str, elem_dict in dfs.items():
        for tag, tag_dict in elem_dict.items():
            for stat_name, stat in tag_dict.items():
                if stat_name not in dfs2:
                    dfs2[stat_name] = {}
                if elem_str not in dfs2[stat_name]:
                    dfs2[stat_name][elem_str] = {}
                dfs2[stat_name][elem_str][tag] = stat
    
    dfs = {stat_name: pd.DataFrame(stat_dict).transpose() for stat_name, stat_dict in dfs2.items()}
    
    return dfs
    