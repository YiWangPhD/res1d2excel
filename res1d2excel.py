# -*- coding: utf-8 -*-
# Author: Yi Wang
# version: 1.0
# purpos: main function to extract res1d results to excel files

import os
import sys
import input_dataframes
import input_xlsx
import res1d_extractors
import exporter
import exporter_xlsx


# read input files to dataframes
def read_input_files(args):
    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        # one input file
        return input_xlsx.read_dataframes_from_xlsx(sys.argv[1])
    if len(sys.argv) == 4 and os.path.isfile(sys.argv[1]) and os.path.isfile(sys.argv[2]) and os.path.isfile(sys.argv[3]):
        return input_xlsx.read_dataframes_from_xlsx(sys.argv[1], sys.argv[2], sys.argv[3])
    print('Please provide one or three input files.')
    exit()


# build collections from dataframes
def create_collections(dfs_list):
    [res1d_file_dfs, element_collections_dfs, output_files_dfs] = dfs_list
    
    res1d_dict = input_dataframes.create_res1d_collections_from_dataframes(res1d_file_dfs)
    element_collections = input_dataframes.create_element_collections_from_dataframes(element_collections_dfs)
    xlsx_dict = input_dataframes.create_excel_collection_from_dataframes(output_files_dfs)

    return [res1d_dict, element_collections, xlsx_dict]


def export_results(element_collections, xlsx_dict):
    resample_t = xlsx_dict['resample_t']
    
    for file_tag in ['by_elements', 'by_file', 'stats']:
        if file_tag in xlsx_dict:
            print(os.linesep + f'Exporting data {file_tag} ...')
            match file_tag.lower():
                case 'by_elements':
                    dfs = exporter.dataframe_by_element(element_collections)
                case 'by_file':
                    dfs = exporter.dataframe_by_file(element_collections)
                case 'stats':
                    dfs = exporter.dataframes_stats(element_collections)
            xlsx_file_path = xlsx_dict[file_tag]
            if file_tag == 'stats':
                exporter_xlsx.export_excel(dfs, xlsx_file_path, None)
            else:
                exporter_xlsx.export_excel(dfs, xlsx_file_path, resample_t)
            print(f'Data exported to file: {xlsx_file_path}')

def main():
    if len(sys.argv) == 1:
        #create templates
        xlsx_file_path = os.path.join(os.getcwd(), "res1d2excel_template.xlsx")
        input_xlsx.create_template_xlsx(xlsx_file_path)
        print(f'Spreadsheet template has been created and saved at: {xlsx_file_path}')
        exit()
    
    #process input files
    print("Reading configuration files ...")
    dfs_list = read_input_files(sys.argv)
    [res1d_dict, element_collections, xlsx_dict] = create_collections(dfs_list)
    print("Finished reading configuration files.")
    
    # extract ts
    print("Extracting res1d files ...")
    res1d_extractors.batch_res1d_extractor(res1d_dict, element_collections)
    print("Finished extracting res1d files. ")
    
    # # export dataframes
    print("Exporting excel files ...")
    export_results(element_collections, xlsx_dict)


if __name__ == '__main__':
    main()


