# -*- coding: utf-8 -*-
# Author: Yi Wang
# this module build input dataframes using input excel files

import os
import pandas as pd
import numpy as np
import input_dataframes

# dataframe <==> xlsx
# write dataframe templates to spreadsheets:
    
def write_dataframes_to_xlxs(xlsx_file_path, dfs):
    with pd.ExcelWriter(xlsx_file_path) as writer:
        for k, v in dfs.items():
            v.to_excel(writer, sheet_name = k, index=False)
    

def create_template_xlsx(xlsx_file_path):
    dfs = input_dataframes.create_element_collections_dataframes_template()
    dfs = dfs | input_dataframes.create_res1d_files_dataframe_template()
    dfs = dfs | input_dataframes.create_output_files_dataframe_template()
    write_dataframes_to_xlxs(xlsx_file_path, dfs)


# read dataframes from spreadsheets
def read_element_collections_dataframes_from_xlsx(xlsx_file_path):
    dfs = pd.read_excel(xlsx_file_path, 
                        sheet_name = ['catchment', 'node', 'link', 'orifice', 'pump', 'regulation', 'weir', 'valve'],
                        dtype = {'alias': object, 
                                 'quantity': object, 
                                 'muid': object,
                                 'chainage': np.float64})
    return dfs


def read_output_files_dataframes_from_xlsx(xlsx_file_path):
    dfs = pd.read_excel(xlsx_file_path, 
                        sheet_name = ['output_files'],
                        dtype = {'type': object, 
                                 'value': object})
    return dfs


def read_res1d_files_dataframes_from_xlsx(xlsx_file_path):
    dfs = pd.read_excel(xlsx_file_path, 
                        sheet_name = ['res1d_files'],
                        dtype = {'result_type': object, 
                                 'short_name': object,
                                 'res1d_file_path': object})
    return dfs


def read_dataframes_from_xlsx(xlsx_file_path):
    
    res1d_file_dfs = read_res1d_files_dataframes_from_xlsx(xlsx_file_path)
    element_collections_dfs = read_element_collections_dataframes_from_xlsx(xlsx_file_path)
    output_files_dfs = read_output_files_dataframes_from_xlsx(xlsx_file_path)
    
    return [res1d_file_dfs, element_collections_dfs, output_files_dfs]
    

def main():
    xlsx_file_path = os.path.join(os.getcwd(), "res1d2excel_template.xlsx")
    create_template_xlsx(xlsx_file_path)
    dfs_list = read_dataframes_from_xlsx(xlsx_file_path)
    print(dfs_list[0])

if __name__ == '__main__':
    main()
