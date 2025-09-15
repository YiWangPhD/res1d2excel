# -*- coding: utf-8 -*-
# Author: Yi Wang
# this module build input collections/dictionaries using input dataframes


import os
import pandas as pd
import simple_element_collection
import simple_element


# create dataframe templates
def create_element_collections_dataframes_template():
    dfs = {}
    dfs['catchment'] = pd.DataFrame({
        'alias': ['S21201401_TotalRunOff', 'S15155401_TotalRunOff', 
                  'S17171302_TotalRunOff', None, 
                  None, 'S17171302_NetRainfall'],
        'quantity':['TotalRunOff', 'TotalRunOff', 'TotalRunOff', 
                    'NetRainfall', 'NetRainfall', 'NetRainfall'],
        'muid':['S21201401', 'S15155401', 'S17171302',
                'S21201401', 'S15155401', 'S17171302']
        })
    dfs['node'] = pd.DataFrame({
        'alias': ['C14150801_WaterLevel', 'C16169801_WaterLevel', None],
        'quantity': ['WaterLevel', 'WaterLevel', 'WaterLevel'],
        'muid': ['C14150801', 'C16169801', 'Inflow to_WWTP_Basin']
        })
    dfs['link'] = pd.DataFrame({
        'alias': ['C15152001.2_WaterLevel', 'C19203901.2_WaterLevel', 
                  None, 'C15152001.2_Discharge', None, 'C20203301.2_Discharge', 
                   'C15152001.2_Velocity', 'C19203901.2_Velocity', None],
        'quantity': ['WaterLevel', 'WaterLevel', 'WaterLevel', 
                     'Discharge', 'Discharge', 'Discharge',
                     'FlowVelocity', 'FlowVelocity', 'FlowVelocity'],
        'muid': ['C15152001.2', 'C19203901.2', 'C20203301.2', 
                 'C15152001.2', 'C19203901.2', 'C20203301.2',
                 'C15152001.2', 'C19203901.2', 'C20203301.2'],
        'chainage': [None, 66.30, 62.965,
                     None, None, 29.75,
                     None, None, None]
        })    
    dfs['orifice'] = pd.DataFrame({
        'alias': ['Sir40.1_O_Discharge', 'Orifice_6_Discharge', 
                  None, 'Sir40.1_O_WaterLevel', 'Orifice_6_WaterLevel', None, 
                  'Sir40.1_O_GateLevel', 'Orifice_6_GateLevel', 
                  'Sir5.1_O_GateLevel', None, None, 'Sir5.1_O_ControlStrategyId'],
        'quantity': ['Discharge', 'Discharge', 'Discharge',
                     'WaterLevel', 'WaterLevel', 'WaterLevel', 
                     'GateLevel', 'GateLevel', 'GateLevel',
                     'ControlStrategyId', 'ControlStrategyId', 
                     'ControlStrategyId'],
        'muid': ['Sir40.1_O', 'Orifice_6', 'Sir5.1_O', 
                 'Sir40.1_O', 'Orifice_6', 'Sir5.1_O', 
                 'Sir40.1_O', 'Orifice_6', 'Sir5.1_O', 
                 'Sir40.1_O', 'Orifice_6', 'Sir5.1_O']
        })    
    dfs['pump'] = pd.DataFrame({
        'alias': ['Pump_1_to_WWTP_Discharge', 'Pump_3_to_WWTP_Discharge', 
                  None, 'Pump_1_to_WWTP_ControlStrategyId', 
                  'Pump_3_to_WWTP_ControlStrategyId', None],
        'quantity': ['Discharge', 'Discharge', 'Discharge',
                     'ControlStrategyId', 'ControlStrategyId', 
                     'ControlStrategyId'],
        'muid': ['Pump_1_to_WWTP', 'Pump_3_to_WWTP', 'SirPump20.1', 
                 'Pump_1_to_WWTP', 'Pump_3_to_WWTP', 'SirPump20.1']
        })    
    dfs['regulation'] = pd.DataFrame({
        'alias': ['C14150801.2_Discharge', 'C14150801.2_WaterLevel', None],
        'quantity': ['Discharge', 'WaterLevel', 'FlowVelocity'],
        'muid': ['C14150801.2', 'C14150801.2', 'C14150801.2'],
        'chainage': [None, None, None]
        })    
    dfs['weir'] = pd.DataFrame({
        'alias': ['Weir_to WWTP_Discharge', 'Weir_to_river_Discharge', 
                  'Weir_to WWTP_CrestLevel', None, None, None],
        'quantity': ['Discharge', 'Discharge', 
                     'CrestLevel', 'CrestLevel', 
                     'ControlStrategyId', 'ControlStrategyId'],
        'muid': ['Weir_to WWTP', 'Weir_to_river', 
                 'Weir_to WWTP', 'Weir_to_river',  
                 'Weir_to WWTP', 'Weir_to_river']
        })    
    dfs['valve'] = pd.DataFrame({
        'alias': [],
        'quantity': [],
        'muid': []
        })
    return dfs


def create_output_files_dataframe_template():
    output_specifications_df = pd.DataFrame({
        'type': ['folder_path', 'resample_t', 'by_elements', 'by_file', 'stats'],
        'value': [os.getcwd(), '5min', 
                  r"by_element.xlsx", r"by_file.xlsx", r"stats.xlsx"]
        })
    return {'output_files': output_specifications_df}


def create_res1d_files_dataframe_template():
    res1d_files_df = pd.DataFrame({
        'result_type': ['network', 'runoff'],
        'short_name': ['HD', 'RR'],
        'res1d_file_path': [os.path.join(os.getcwd(), 'test_data', 'Rainfall_CDS_1yearHDBaseDefault_Network_HD.res1d'), 
                            os.path.join(os.getcwd(), 'test_data', 'Rainfall_CDS_1_yearRRBaseDefault_Surface_runoff.res1d')]
        })
    return {'res1d_files': res1d_files_df}


# create collections from dataframes
def create_element_collections_from_dataframes(dfs):
    element_collections = []
    for element_type, element_df in dfs.items():
        ts_manager = simple_element_collection.SimpleElementCollection(element_type)
        element_df = element_df.fillna(0)
        for index, row in element_df.iterrows():
            alias = row.iloc[0]
            if alias == 0:
                alias = None
            quantity = row.iloc[1]
            muid = str(row.iloc[2])
            if len(row) > 3:
                chainage = row.iloc[3]
                ts_manager.add_element(simple_element.SimpleElement(muid, alias, element_type, quantity, chainage))
            else:
                ts_manager.add_element(simple_element.SimpleElement(muid, alias, element_type, quantity))
        element_collections.append(ts_manager)
    return element_collections


def create_excel_collection_from_dataframes(dfs):
    xlsx_dict = {}
    for sheet_name, sheet_df in dfs.items():
        sheet_df = sheet_df.fillna(0)
        for index, row in sheet_df.iterrows():
            xlsx_dict[row.iloc[0]] = row.iloc[1]
    
    folder_path = xlsx_dict.pop('folder_path')
    if 'resample_t' in xlsx_dict:
        resample_t = xlsx_dict.pop('resample_t')
    else:
        resample_t = None
        
    if resample_t == 0:
        resample_t = None

    for k, v in xlsx_dict.items():
        xlsx_dict[k] = os.path.join(folder_path, xlsx_dict[k])
        
    xlsx_dict['resample_t'] = resample_t
    
    return xlsx_dict


def create_res1d_collections_from_dataframes(dfs):
    
    res1d_dict = {}
    for sheet_name, sheet_df in dfs.items():
        for index, row in sheet_df.iterrows():
            result_type = row.iloc[0]
            short_name = row.iloc[1]
            res1d_file_path = row.iloc[2]

            if result_type in res1d_dict:
                res1d_dict[result_type][short_name] = res1d_file_path
            else:
                if result_type in res1d_dict:
                    if short_name in res1d_dict[result_type]:
                        print("Cannot have two files with same short name!")
                        exit()
                    else:
                        res1d_dict[result_type][short_name] = res1d_file_path
                else:
                    res1d_dict[result_type] = {short_name: res1d_file_path}
    return res1d_dict


def main():
    element_collections_dataframes = create_element_collections_dataframes_template()
    element_collections = create_element_collections_from_dataframes(element_collections_dataframes)
    for ec in element_collections:
        print(ec.get_all_element_ids())
    
    res1d_files_dataframe = create_res1d_files_dataframe_template()
    res1d_dict = create_res1d_collections_from_dataframes(res1d_files_dataframe)
    print(res1d_dict)
    
    output_files_dataframe = create_output_files_dataframe_template()
    xlsx_dict = create_excel_collection_from_dataframes(output_files_dataframe)
    print(xlsx_dict)

if __name__ == '__main__':
    main()

