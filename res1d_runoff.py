#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this is the res1d runoff class module

import res1d
import utilities
import pandas as pd

class Res1DRunoff(res1d.Res1D):
    
    _runoffSubCatchSuffix = ['', ' - RDI', ' - Kinematic wave (B)']
       
    _catchment_quantity_IDs = []
    
    
    def __init__(self, file_path):
        """
        initiate instance. read from res1d file and load properties

        Parameters
        ----------
        file_path : str
            path to res1d file.

        Returns
        -------
        None.

        """
        super().__init__(file_path)
        self.catchment_IDs = self._get_element_IDs()
        self.catchment_count = len(self.catchment_IDs)
        self._catchment_quantity_IDs = [
            q.Id for q in self.result_data.Quantities]
        
        
    def _get_element_IDs(self):
        """
        extract element IDs to lists

        Returns
        -------
        list
            list of lists. each list contains IDs of a type of element. 

        """
        # catchment ids as a dict
        catchment_IDs = {catchment.Id: k for k, catchment 
                         in enumerate(self.result_data.Catchments)}
                
        return catchment_IDs
    
    
    def get_catchment_data_frames(self, extraction_IDs, 
                     quantity_IDs = _catchment_quantity_IDs, 
                     include_sub_catchments = True):
        """
        extract time series from catchments.

        Parameters
        ----------
        extraction_IDs : list
            list of catchment IDs to extract time series from.
        quantity_IDs : list, optional
            quantities to be extracted. The default is all quantities
        include_sub_catchments : bool, optional
            include sub catchments between modules. The default is True.

        Returns
        -------
        dfs : dict
            dictionary of pandas data frames. one df per quantity.

        """
        
        if include_sub_catchments:
            extraction_IDs = [
                cId + suffix for cId in extraction_IDs 
                for suffix in self._runoffSubCatchSuffix]
        
        dfs = self._get_element_data_frame(self.result_data.Catchments, 
                                           self.catchment_IDs, 
                                          extraction_IDs, quantity_IDs)
                
        return dfs


    def get_discharge_data_frame(self, extraction_IDs):
        """
        extract time series of discharges, regardless of element types.

        Parameters
        ----------
        extraction_IDs : list
            list of element IDs to extract time series from.

        Returns
        -------
        df : pd.DataFrame
            one pandas dataframe of all time series.

        """
        extraction_IDs = utilities.list_cleanup(extraction_IDs)
        
        dfs = []
        
        df = self.get_catchment_data_frames(extraction_IDs, ['TotalRunOff'], False)
        dfs.append(df['TotalRunOff'])
        
        return pd.concat(dfs, axis=1)
    

# test
def test_runoff():
    res1d_file_path = r"J:\SEWER_AREA_MODELS\VSA\04_ANALYSIS_WORK\21. SYSTEM_ASSESSMENT\Incremental_rainfall_runs\Runoff Results\VSA_Runoff_EX-24h-VA73-50mm-SCS1A_BaseRR.res1d"
    res1d = Res1DRunoff(res1d_file_path)
    print(f'Number of catchments: {res1d.catchment_count}')
    print(', '.join(res1d._catchment_quantity_IDs))
    utilities_plotly.draw_graph([
        res1d.get_catchment_data_frames(
            ['1035', '1036'], ['TotalRunOff'], False)['TotalRunOff']
        ])
    
    
def main():
    print("in res1d_runoff.py!")
    test_runoff()


if __name__ == '__main__':
    import utilities_plotly
    main()