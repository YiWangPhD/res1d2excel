# -*- coding: utf-8 -*-
# Author: Yi Wang
# this module build input dataframes using input excel files

import os
import pandas as pd
import numpy as np
from . import input_dataframes


ELEMENT_SHEETS = [
    'catchment', 'node', 'link', 'orifice', 'pump', 'regulation',
    'weir', 'valve', 'bridge', 'direct_discharge', 'gate'
]

OPTIONAL_ELEMENT_SHEETS = ['bridge', 'direct_discharge', 'gate']

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
    dfs = dfs | input_dataframes.create_combined_dataframe_template()
    write_dataframes_to_xlxs(xlsx_file_path, dfs)


# read dataframes from spreadsheets
def read_element_collections_dataframes_from_xlsx(xlsx_file_path):
    dfs = {}
    with pd.ExcelFile(xlsx_file_path) as workbook:
        for sheet_name in ELEMENT_SHEETS:
            if sheet_name not in workbook.sheet_names:
                if sheet_name in OPTIONAL_ELEMENT_SHEETS:
                    dfs[sheet_name] = pd.DataFrame({
                        'alias': [],
                        'quantity': [],
                        'muid': []
                    })
                    continue
                raise ValueError(f"Worksheet named '{sheet_name}' not found")

            dfs[sheet_name] = pd.read_excel(
                            workbook,
                            sheet_name=sheet_name,
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


def read_combined_dataframe_from_xlsx(xlsx_file_path):
    try:
        dfs = pd.read_excel(xlsx_file_path,
                            sheet_name=['combined'],
                            dtype={'combined_alias': object,
                                   'quantity': object,
                                   'op': object,
                                   'source': object,
                                   'source_alias': object})
    except ValueError as exc:
        if "Worksheet named 'combined' not found" in str(exc):
            return pd.DataFrame()
        raise

    return dfs['combined']


def read_dataframes_from_xlsx(xlsx_file_path):

    res1d_file_dfs = read_res1d_files_dataframes_from_xlsx(xlsx_file_path)
    element_collections_dfs = read_element_collections_dataframes_from_xlsx(xlsx_file_path)
    output_files_dfs = read_output_files_dataframes_from_xlsx(xlsx_file_path)
    combined_df = read_combined_dataframe_from_xlsx(xlsx_file_path)
    combined = input_dataframes.create_combined_from_dataframe(combined_df)

    return [res1d_file_dfs, element_collections_dfs, output_files_dfs, combined]
    

def main():
    xlsx_file_path = os.path.join(os.getcwd(), "res1d2excel_template.xlsx")
    create_template_xlsx(xlsx_file_path)
    dfs_list = read_dataframes_from_xlsx(xlsx_file_path)
    print(dfs_list[0])

if __name__ == '__main__':
    main()
