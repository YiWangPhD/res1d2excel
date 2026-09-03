# -*- coding: utf-8 -*-
# Author: Yi Wang
# version: 1.4.1
# purpos: main function to extract res1d results to excel files

import os
import sys
from . import input_dataframes
from . import input_xlsx
from . import input_json
from . import res1d_extractors
from . import exporter
from . import exporter_xlsx
from . import exporter_html
from . import element_collection
import pickle
from typing import Any, List


# [res1d_file_dfs, element_collections_dfs, output_files_dfs, combined]
InputDataframes = List[Any]


# read input files to dataframes
def read_input_files(args: List[str]) -> InputDataframes:
    if len(args) == 1 and os.path.isfile(args[0]):
        # one input file
        if os.path.splitext(args[0])[1].lower() == '.json':
            return input_json.read_dataframes_from_json(args[0])
        return input_xlsx.read_dataframes_from_xlsx(args[0])
    raise ValueError('Please provide one input file.')


# build collections from dataframes
def create_collections(
        dfs_list: InputDataframes
        ) -> list[object]:
    [res1d_file_dfs, element_collections_dfs, output_files_dfs, combined] = dfs_list

    res1d_dict = input_dataframes.create_res1d_collections_from_dataframes(res1d_file_dfs)
    element_collections = input_dataframes.create_element_collections_from_dataframes(element_collections_dfs)
    combined_collection = element_collection.ElementCollection.create_combined_collection(
        combined,
        element_collections,
        input_json.DISCHARGE_QUANTITIES
    )
    if len(combined_collection) > 0:
        element_collections.append(combined_collection)
    xlsx_dict = input_dataframes.create_excel_collection_from_dataframes(output_files_dfs)

    return [res1d_dict, element_collections, xlsx_dict]


def export_results(
        element_collections: List[element_collection.ElementCollection],
        xlsx_dict: dict,
        export_pickles: bool = True
        ) -> None:
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
            if export_pickles:
                pickle_file_path = xlsx_file_path.replace('.xlsx', '.pkl')
                pickle.dump(dfs, open(pickle_file_path, 'wb'))

    if xlsx_dict['to_html']:
        output_folder = xlsx_dict['output_folder']

        print(os.linesep + 'Exporting HTML plots by element ...')
        dfs = exporter.dataframe_by_element(element_collections)
        html_file_path = os.path.join(output_folder, 'plots_by_element.html')
        exporter_html.export_plot_page(
            dfs,
            html_file_path,
            'Plots by Element',
            'Element',
            resample_t
        )
        print(f'HTML plots exported to file: {html_file_path}')

        print(os.linesep + 'Exporting HTML plots by file ...')
        dfs = exporter.dataframe_by_file(element_collections)
        html_file_path = os.path.join(output_folder, 'plots_by_file.html')
        exporter_html.export_plot_page(
            dfs,
            html_file_path,
            'Plots by File',
            'File',
            resample_t
        )
        print(f'HTML plots exported to file: {html_file_path}')

def main(argv: List[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) == 0:
        #create templates
        xlsx_file_path = os.path.join(os.getcwd(), "res1d2excel_template.xlsx")
        json_file_path = os.path.join(os.getcwd(), "res1d2excel_template.json")
        input_xlsx.create_template_xlsx(xlsx_file_path)
        input_json.create_template_json(json_file_path)
        print(f'Spreadsheet template has been created and saved at: {xlsx_file_path}')
        print(f'JSON template has been created and saved at: {json_file_path}')
        return
    
    #process input files
    print("Reading configuration files ...")
    dfs_list = read_input_files(argv)
    [res1d_dict, element_collections, xlsx_dict] = create_collections(dfs_list)
    print("Finished reading configuration files.")
    
    # extract ts
    print("Extracting result files ...")
    res1d_extractors.batch_res1d_extractor(
        res1d_dict,
        element_collections,
        xlsx_dict['skip_time'],
        xlsx_dict['trunc_time']
        )
    res1d_extractors.update_combined_element_collections(element_collections)
    print("Finished extracting result files. ")
    
    # # export dataframes
    print("Exporting excel files ...")
    export_results(element_collections, xlsx_dict)


if __name__ == '__main__':
    main()


