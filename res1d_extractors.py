#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this module extracts time seris from one Res1D class and add to
# SimpleElementCollection instances

import simple_element_collection
import res1d_network
import res1d_runoff

def batch_res1d_extractor(res1d_dict, elem_collection_list):
    """
    enumerate through res1d file dictionary and extract data according
    to simple element collection list
    
    Parameters
    ----------
    res1d_dict : dictionary {short_name: file_path}
        this dictionary holds collection of res1d file paths
    elem_collection_list : list of simple element collections
        list of simple element collections

    Returns
    -------
    None.

    """
    if 'network' in res1d_dict:
        for short_name, res1d_file_path in res1d_dict['network'].items():
            print(f'Loading res1d file {res1d_file_path} ...')
            res1d = res1d_network.Res1DNetwork(res1d_file_path)
            print(f'Extracting data from res1d file {short_name} ...')
            res1d_extractor(short_name, res1d, elem_collection_list)
    if 'runoff' in res1d_dict:
        for short_name, res1d_file_path in res1d_dict['runoff'].items():
            print(f'Loading res1d file {res1d_file_path} ...')
            res1d = res1d_runoff.Res1DRunoff(res1d_file_path)
            print(f'Extracting data from res1d file {short_name} ...')
            res1d_extractor(short_name, res1d, elem_collection_list)
            
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
    elem_collection_list : list of simple element collections
        list of simple element collections

    Returns
    -------
    None.

    """
    for elem_collection in elem_collection_list:
        print(f'Extracting {elem_collection.get_element_type()} data ...')
        dfs = extract_element_ts(res1d, elem_collection)
        if dfs is not None:
            elem_collection.update_ts(dfs, short_name)
            elem_collection.update_statistics()


def extract_element_ts(res1d, elem_collection):
    """
    extract data from res1d according to the simple element collection

    Parameters
    ----------
    res1d : Res1DNetwork or Res1DRunoff
        instance of res1d class.
    elem_collection : SimpleElementCollection
        collection of SimpleElement.

    Returns
    -------
    dfs : TYPE
        DESCRIPTION.

    """
    if not isinstance(elem_collection, 
                      simple_element_collection.SimpleElementCollection):
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
    
    if isinstance(res1d, res1d_runoff.Res1DRunoff):
        dfs = res1d.get_catchment_data_frames(element_ids, quantity_ids)
    
    return dfs
    
    
def test_network():
    import os
    import collection_builder_res1d_xlsx
    import collection_builder_element_xlsx
    
    xlsx_file_path = os.path.join(os.getcwd(), "res1d_config_template.xlsx")
    res1d_dict = collection_builder_res1d_xlsx.create_res1d_collections_from_xlsx(xlsx_file_path)
    
    xlsx_file_path = os.path.join(os.getcwd(), "elements_config_template.xlsx")
    elem_collection_list = collection_builder_element_xlsx.create_element_collections_from_xlsx(xlsx_file_path)
        
    # extract ts
    batch_res1d_extractor(res1d_dict, elem_collection_list)
    
    # show results        
    for elements in [elem_collection_list[0].get_elements_by_quantity(qId) for qId in ['WaterLevel']]:
        utilities_plotly.draw_sub_graphs([[element.get_ts_dataframe()] for element in elements])
        
    for elements in [elem_collection_list[1].get_elements_by_quantity(qId) for qId in ['WaterLevel', 'Discharge', 'FlowVelocity']]:
        utilities_plotly.draw_sub_graphs([[element.get_ts_dataframe()] for element in elements])
    
    for elements in [elem_collection_list[2].get_elements_by_quantity(qId) for qId in ['Discharge', 'GateLevel', 'ControlStrategyId']]:
        utilities_plotly.draw_sub_graphs([[element.get_ts_dataframe()] for element in elements])
        
    for elements in [elem_collection_list[3].get_elements_by_quantity(qId) for qId in ['Discharge', 'ControlStrategyId']]:
        utilities_plotly.draw_sub_graphs([[element.get_ts_dataframe()] for element in elements])
        
    for elements in [elem_collection_list[4].get_elements_by_quantity(qId) for qId in ['Discharge', 'WaterLevel', 'FlowVelocity']]:
        utilities_plotly.draw_sub_graphs([[element.get_ts_dataframe()] for element in elements])
        
    for elements in [elem_collection_list[5].get_elements_by_quantity(qId) for qId in ['Discharge', 'CrestLevel', 'ControlStrategyId']]:
        utilities_plotly.draw_sub_graphs([[element.get_ts_dataframe()] for element in elements])


def main():
    print("in res1d_extractor.py!")
    test_network()


if __name__ == '__main__':
    import utilities_plotly
    import plotly.io as pio
    pio.renderers.default='browser'
    main()