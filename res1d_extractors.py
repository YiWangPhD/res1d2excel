#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this module extracts time seris from one Res1D class and add to
# SimpleElementCollection instances

import element_collection
import pandas as pd
import combined_element
import res1d_network
import res1d_runoff


def batch_res1d_extractor(
        res1d_dict,
        elem_collection_list,
        skip_time=None,
        trunc_time=None
        ):
    """
    enumerate through res1d file dictionary and extract data according
    to simple element collection list
    
    Parameters
    ----------
    res1d_dict : dictionary {short_name: file_path}
        this dictionary holds collection of res1d file paths
    elem_collection_list : list of element collections
        list of element collections
    skip_time : str, optional
        pandas-compatible duration to remove from the beginning of each result
        file, e.g. '24h' or '30min'. The default is None.
    trunc_time : str, optional
        pandas-compatible duration to remove from the end of each result file,
        e.g. '6h' or '30min'. The default is None.

    Returns
    -------
    None.

    """
    if 'network' in res1d_dict:
        for short_name, res1d_file_path in res1d_dict['network'].items():
            print(f'Loading res1d file {res1d_file_path} ...')
            res1d = res1d_network.Res1DNetwork(res1d_file_path)
            apply_time_range(res1d, skip_time, trunc_time)
            print(f'Extracting data from res1d file {short_name} ...')
            res1d_extractor(short_name, res1d, elem_collection_list)
    if 'runoff' in res1d_dict:
        for short_name, res1d_file_path in res1d_dict['runoff'].items():
            print(f'Loading res1d file {res1d_file_path} ...')
            res1d = res1d_runoff.Res1DRunoff(res1d_file_path)
            apply_time_range(res1d, skip_time, trunc_time)
            print(f'Extracting data from res1d file {short_name} ...')
            res1d_extractor(short_name, res1d, elem_collection_list)


def parse_time_delta(value, name):
    """
    Convert a user-provided duration to a non-negative pandas Timedelta.

    Parameters
    ----------
    value : str
        pandas-compatible duration, e.g. '24h' or '30min'.
    name : str
        name of the configuration field.

    Returns
    -------
    pd.Timedelta

    """
    if value is None or pd.isna(value) or value == 0:
        return pd.Timedelta(0)

    if isinstance(value, str) and not value.strip():
        return pd.Timedelta(0)

    try:
        delta = pd.Timedelta(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {name}: {value}") from exc

    if delta < pd.Timedelta(0):
        raise ValueError(f"{name} must be non-negative: {value}")

    return delta


def apply_time_range(res1d, skip_time=None, trunc_time=None):
    """
    Update a Res1D extraction window to trim the beginning and end.

    Parameters
    ----------
    res1d : Res1DNetwork or Res1DRunoff
        instance of res1d class.
    skip_time : str, optional
        pandas-compatible duration to remove from the beginning.
    trunc_time : str, optional
        pandas-compatible duration to remove from the end.

    Returns
    -------
    None.

    """
    skip_delta = parse_time_delta(skip_time, 'skip_time')
    trunc_delta = parse_time_delta(trunc_time, 'trunc_time')

    if skip_delta == pd.Timedelta(0) and trunc_delta == pd.Timedelta(0):
        return

    original_from_time_stamp = res1d.from_time_stamp
    original_to_time_stamp = res1d.to_time_stamp
    result_time_span = original_to_time_stamp - original_from_time_stamp

    if skip_delta + trunc_delta > result_time_span:
        raise ValueError(
            f"skip_time + trunc_time ({skip_delta + trunc_delta}) exceeds "
            f"res1d result time span ({result_time_span}). "
            f"skip_time={skip_time}, trunc_time={trunc_time}"
        )

    from_time_stamp = original_from_time_stamp + skip_delta
    to_time_stamp = original_to_time_stamp - trunc_delta

    res1d.setTimeRange(from_time_stamp, to_time_stamp)


def res1d_extractor(short_name, res1d, elem_collection_list):
    """
    enumerate through list of simple element collections and extract data
    from res1d instance
    update to simple element collection
    
    Parameters
    ----------
    short_name : String
        short name for the res1d file, e.g. 50mm, double_pipe, ...
    res1d : Res1DNetwork or Res1DRunoff
        instance of res1d class.
    elem_collection_list : list of element collections
        list of element collections

    Returns
    -------
    None.

    """
    for elem_collection in elem_collection_list:
        if is_calculated_collection(elem_collection):
            continue
        print(f'Extracting {elem_collection.get_element_type()} data ...')
        dfs = extract_element_ts(res1d, elem_collection)
        if dfs is not None:
            elem_collection.add_ts(dfs, short_name)
            elem_collection.update_statistics()


def is_calculated_collection(elem_collection):
    if not isinstance(elem_collection,
                      element_collection.ElementCollection):
        return False
    return combined_element.CALCULATED_DISCHARGE in elem_collection.get_quantity_ids()


def update_combined_element_collections(elem_collection_list):
    """
    Update calculated element collections after native res1d extraction.
    """
    for elem_collection in elem_collection_list:
        if not is_calculated_collection(elem_collection):
            continue
        print(f'Updating {elem_collection.get_element_type()} data ...')
        print_combined_equations(elem_collection)
        elem_collection.update_ts()
        elem_collection.update_statistics()


def print_combined_equations(elem_collection):
    for element in elem_collection.get_all_elements():
        print(f"{element.get_element_id()} =")
        print(element.print_equation())


def extract_element_ts(res1d, elem_collection):
    """
    extract data from res1d according to the simple element collection

    Parameters
    ----------
    res1d : Res1DNetwork or Res1DRunoff
        instance of res1d class.
    elem_collection : ElementCollection
        collection of Element.

    Returns
    -------
    dfs : TYPE
        DESCRIPTION.

    """
    if not isinstance(elem_collection,
                      element_collection.ElementCollection):
        return None
    if is_calculated_collection(elem_collection):
        return None
    element_type = elem_collection.get_element_type()
    quantity_ids = elem_collection.get_quantity_ids()
    element_ids = elem_collection.get_all_element_ids()
    
    dfs = None

    if isinstance(res1d, res1d_network.Res1DNetwork):
        match element_type.lower():
            case 'node':
                dfs = res1d.get_node_data_frames(element_ids, quantity_ids)
            case 'link':
                dfs = res1d.get_reach_data_frames(element_ids, quantity_ids)
            case'orifice':
                dfs = res1d.get_orifice_data_frames(element_ids, quantity_ids)
            case 'pump':
                dfs = res1d.get_pump_data_frames(element_ids, quantity_ids)
            case 'regulation':
                dfs = res1d.get_regulation_data_frames(element_ids, quantity_ids)
            case 'weir':
                dfs = res1d.get_weir_data_frames(element_ids, quantity_ids)
            case 'valve':
                dfs = res1d.get_valve_data_frames(element_ids, quantity_ids)
            case 'bridge':
                dfs = res1d.get_bridge_data_frames(element_ids, quantity_ids)
            case 'direct_discharge':
                dfs = res1d.get_direct_discharge_data_frames(
                    element_ids, quantity_ids)
            case 'gate':
                dfs = res1d.get_gate_data_frames(element_ids, quantity_ids)
    
    if isinstance(res1d, res1d_runoff.Res1DRunoff):
        dfs = res1d.get_catchment_data_frames(element_ids, quantity_ids)
    
    return dfs
    
    
def test_network():
    import os
    import input_xlsx
    import input_dataframes

    res1d_file_dfs = input_dataframes.create_res1d_files_dataframe_template()
    element_collections_dfs = input_dataframes.create_element_collections_dataframes_template()
    
    res1d_dict = input_dataframes.create_res1d_collections_from_dataframes(res1d_file_dfs)
    element_collections = input_dataframes.create_element_collections_from_dataframes(element_collections_dfs)
        
    # extract ts
    batch_res1d_extractor(res1d_dict, element_collections)
    
    # show results        
    for elements in [element_collections[0].get_elements_by_quantity(qId) for qId in ['TotalRunOff']]:
        utilities_plotly.draw_sub_graphs([[element.get_ts_dataframe()] for element in elements])
        
    for elements in [element_collections[1].get_elements_by_quantity(qId) for qId in ['WaterLevel']]:
        utilities_plotly.draw_sub_graphs([[element.get_ts_dataframe()] for element in elements])
    
    for elements in [element_collections[2].get_elements_by_quantity(qId) for qId in ['Discharge', 'WaterLevel']]:
        utilities_plotly.draw_sub_graphs([[element.get_ts_dataframe()] for element in elements])

def main():
    print("in res1d_extractor.py!")
    test_network()


if __name__ == '__main__':
    import utilities_plotly
    import plotly.io as pio
    pio.renderers.default='browser'
    main()
