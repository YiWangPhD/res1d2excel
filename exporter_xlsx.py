# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 13:28:20 2024

@author: YWANG
"""

import pandas as pd

def export_excel(dfs, xlsx_file_path, resample_t = None):

    #get the index page
    pdIndexPage = {}
    for k, v in enumerate(dfs):
        pdIndexPage['Sh_'+str(k)] = v
    pdIndexPage = pd.DataFrame.from_dict(pdIndexPage, orient='index', columns=['ElementName'])
    
    with pd.ExcelWriter(xlsx_file_path) as writer:
        pdIndexPage.to_excel(writer, sheet_name = 'IndexPage')
        for k, v in enumerate(dfs):
            df = dfs[v]
            # resample
            if resample_t is not None and df.shape[0] > 1:
                df = df.resample(resample_t).interpolate('index')
            df.to_excel(writer, sheet_name = f'Sh_{str(k)}')
            print(f'"{v}" is exported to sheet sh_{k}')
            
    if resample_t is not None:
        print(f"Data is resampled to {resample_t} interval. ")