#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this is the res1d network class module

import res1d
import utilities
import pandas as pd

class Res1DNetwork(res1d.Res1D):
    
    _node_quantity_IDs = []
    _reach_quantity_IDs = []
    _orifice_quantity_IDs = []
    _pump_quantity_IDs = []
    _regulation_quantity_IDs = []
    _weir_quantity_IDs = []
    _valve_quantity_IDs = []
    
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
        self.node_IDs, self.reach_IDs, self.weir_IDs,\
            self.pump_IDs, self.orifice_IDs, self.valve_IDs, \
                self.regulation_IDs = self._get_element_IDs()
        self.node_count = len(self.node_IDs)
        self.reach_count = len(self.reach_IDs)
        self.weir_count = len(self.weir_IDs)
        self.pump_count = len(self.pump_IDs)
        self.orifice_count = len(self.orifice_IDs)
        self.valve_count = len(self.valve_IDs)
        self.regulation_count = len(self.regulation_IDs)
        self._node_quantity_IDs = self._get_structure_quantities(
            self.result_data.Nodes, self.node_IDs)
        self._reach_quantity_IDs = self._get_structure_quantities(
            self.result_data.Reaches, self.reach_IDs)
        self._orifice_quantity_IDs = self._get_structure_quantities(
                self.result_data.Reaches, self.orifice_IDs)
        self._pump_quantity_IDs = self._get_structure_quantities(
                    self.result_data.Reaches, self.pump_IDs)
        self._regulation_quantity_IDs = self._get_structure_quantities(
            self.result_data.Reaches, self.regulation_IDs)
        self._weir_quantity_IDs = self._get_structure_quantities(
            self.result_data.Reaches, self.weir_IDs)
        self._valve_quantity_IDs = self._get_structure_quantities(
            self.result_data.Reaches, self.valve_IDs)
        
        
    def _get_structure_quantities(self, elements, element_IDs):
        """
        collect structure quantity types

        Parameters
        ----------
        elements : Res1D elements
            can be Nodes, Catchments, Reaches
            
        element_IDs : dict
            Dictionary, pair of element ID and position

        Returns
        -------
        list of quantitiy IDs

        """
        qs = []
        if len(element_IDs) == 0:
            return qs
        for eid in element_IDs.values():
            for di in elements.get_Item(eid).DataItems:
                qs.append(di.Quantity.Id)
        return list(set(qs))
        
        
    def _get_element_IDs(self):
        """
        extract element IDs to lists

        Returns
        -------
        list
            list of lists. each list contains IDs of a type of element. 

        """
        
        # node ids as a dict
        node_IDs = {node.Id: k for k, node 
                    in enumerate(self.result_data.Nodes)}
        # reach and strucutre ids as dictionaries
        reach_IDs = {}
        weir_IDs = {}
        pump_IDs = {}
        orifice_IDs = {}
        valve_IDs = {}
        regulation_IDs = {}
        list_options = {
            'Weir': weir_IDs,
            'Pump': pump_IDs,
            'Orifice': orifice_IDs,
            'Valve': valve_IDs,
            'Regulation': regulation_IDs
        }
        reaches = self.result_data.Reaches
        for k, reach in enumerate(reaches):
            # remove index suffix from id
            r_ID = '-'.join(reach.Id.split('-')[:-1])
            if any([
                    di.Quantity.Id in 
                    ['DischargeInStructure', 'CrestLevel', 'ValveOpening', 
                     'GateLevel', 'ControlStrategyId'] 
                    for di in reach.DataItems
                    ]):
                # for HD result file
                if any([
                        di.Quantity.Description.endswith(
                            '(Regulating structure)') 
                        for di in reach.DataItems
                        ]):
                    # regulation link
                    reach_IDs[r_ID] = k
                    list_options['Regulation'][r_ID] = k
                else:
                    list_options[r_ID.split(':')[0]]\
                        [':'.join(r_ID.split(':')[1:])] = k
            elif any([
                    r_ID.startswith(tag) 
                      for tag in ['Weir:', 'Pump:', 'Orifice:', 'Valve:']
                      ]):
                # for AD result file
                list_options[r_ID.split(':')[0]]\
                    [':'.join(r_ID.split(':')[1:])] = k
            else:
                reach_IDs[r_ID] = k
                
        return [node_IDs, reach_IDs, weir_IDs, 
                pump_IDs, orifice_IDs, valve_IDs, regulation_IDs]
    
    
    def get_node_data_frames(self, extraction_IDs, 
                quantity_IDs = _node_quantity_IDs):
        """
        extract time series from nodes.

        Parameters
        ----------
        extraction_IDs : list
            list of node IDs to extract time series from.
        quantity_IDs : list, optional
            quantities to be extracted. The default is all quantities

        Returns
        -------
        dfs : dict
            dictionary of pandas data frames. one df per quantity.

        """
        
        dfs = self._get_element_data_frame(self.result_data.Nodes, 
                                           self.node_IDs, 
                                          extraction_IDs, quantity_IDs)
        
        return dfs


    def get_reach_data_frames(self, extraction_IDs, 
                 quantity_IDs = _reach_quantity_IDs):
        """
        extract time series from reaches.

        Parameters
        ----------
        extraction_IDs : list
            list of reach IDs to extract time series from.
        quantity_IDs : list, optional
            quantities to be extracted. The default is all quantities

        Returns
        -------
        dfs : dict
            dictionary of pandas data frames. one df per quantity.

        """
        
        dfs = self._get_element_data_frame(self.result_data.Reaches, 
                                           self.reach_IDs, 
                                          extraction_IDs, quantity_IDs)
        
        return dfs


    def get_orifice_data_frames(self, extraction_IDs, 
                 quantity_IDs = _orifice_quantity_IDs):
        """
        extract time series from reaches.

        Parameters
        ----------
        extraction_IDs : list
            list of orifice IDs to extract time series from.
        quantity_IDs : list, optional
            quantities to be extracted. The default is all quantities

        Returns
        -------
        dfs : dict
            dictionary of pandas data frames. one df per quantity.

        """
        
        dfs = self._get_element_data_frame(self.result_data.Reaches, 
                                           self.orifice_IDs, 
                                          extraction_IDs, quantity_IDs)
        
        return dfs


    def get_pump_data_frames(self, extraction_IDs, 
                 quantity_IDs = _pump_quantity_IDs):
        """
        extract time series from reaches.

        Parameters
        ----------
        extraction_IDs : list
            list of pump IDs to extract time series from.
        quantity_IDs : list, optional
            quantities to be extracted. The default is all quantities

        Returns
        -------
        dfs : dict
            dictionary of pandas data frames. one df per quantity.

        """
        
        dfs = self._get_element_data_frame(self.result_data.Reaches, 
                                           self.pump_IDs, 
                                          extraction_IDs, quantity_IDs)
        
        return dfs


    def get_regulation_data_frames(self, extraction_IDs, 
                 quantity_IDs = _regulation_quantity_IDs):
        """
        extract time series from reaches.

        Parameters
        ----------
        extraction_IDs : list
            list of regulation IDs to extract time series from.
        quantity_IDs : list, optional
            quantities to be extracted. The default is all quantities

        Returns
        -------
        dfs : dict
            dictionary of pandas data frames. one df per quantity.

        """
        
        dfs = self._get_element_data_frame(self.result_data.Reaches, 
                                           self.regulation_IDs, 
                                          extraction_IDs, quantity_IDs)
        
        return dfs


    def get_weir_data_frames(self, extraction_IDs, 
                 quantity_IDs = _weir_quantity_IDs):
        """
        extract time series from reaches.

        Parameters
        ----------
        extraction_IDs : list
            list of weir IDs to extract time series from.
        quantity_IDs : list, optional
            quantities to be extracted. The default is all quantities

        Returns
        -------
        dfs : dict
            dictionary of pandas data frames. one df per quantity.

        """
        
        dfs = self._get_element_data_frame(self.result_data.Reaches, 
                                           self.weir_IDs, 
                                          extraction_IDs, quantity_IDs)
        
        return dfs


    def get_valve_data_frames(self, extraction_IDs, 
                 quantity_IDs = _valve_quantity_IDs):
        """
        extract time series from reaches.

        Parameters
        ----------
        extraction_IDs : list
            list of valve IDs to extract time series from.
        quantity_IDs : list, optional
            quantities to be extracted. The default is all quantities

        Returns
        -------
        dfs : dict
            dictionary of pandas data frames. one df per quantity.

        """
        
        dfs = self._get_element_data_frame(self.result_data.Reaches, 
                                           self.valve_IDs, 
                                          extraction_IDs, quantity_IDs)
        
        return dfs


    def get_structure_data_frames(self, extraction_IDs, 
                     quantity_IDs = ['WaterLevel', 'Discharge', 
                                     'DischargeInStructure', 
                                     'ControlStrategyId']):
        """
        extract time series from structures.

        Parameters
        ----------
        extraction_IDs : list
            list of structure IDs to extract time series from.
        quantity_IDs : list, optional
            quantities to be extracted. The default is all common quantities

        Returns
        -------
        dfs : dict
            dictionary of pandas data frames. one df per quantity.
            column names are modified by adding type of structure as prefix

        """
        extraction_IDs = utilities.list_cleanup(extraction_IDs)
        dfs = {}
        
        dfs['orifice'] = self.get_orifice_data_frames(extraction_IDs, quantity_IDs)
        dfs['pump'] = self.get_pump_data_frames(extraction_IDs, quantity_IDs)
        dfs['regulation'] = self.get_regulation_data_frames(extraction_IDs, quantity_IDs)
        dfs['weir'] = self.get_weir_data_frames(extraction_IDs, quantity_IDs)
        dfs['valve'] = self.get_valve_data_frames(extraction_IDs, quantity_IDs)
            
        
        quantity_IDs = list(
            set.union(
                *[set(list(df.keys())) for df in dfs.values()]
                )
            )
        
        return {
            qID: pd.concat(
                [df[qID] for df in dfs.values() if qID in df.keys()], axis = 1
                ) 
            for qID in quantity_IDs
            }
    

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
        
        df = self.get_node_data_frames(extraction_IDs, ['WaterSpillDischarge'])
        dfs.append(df['WaterSpillDischarge'])
        
        df = self.get_structure_data_frames(extraction_IDs, ['Discharge'])
        dfs.append(df['Discharge'])
        
        df = self.get_reach_data_frames(extraction_IDs, ['Discharge'])
        dfs.append(df['Discharge'])
        
        return pd.concat(dfs, axis=1)
    
    
    def get_link_coordinates_data_frame(self, grid_point_H = True):
        """
        extract coordinates of links to pandas data frame

        Parameters
        ----------
        grid_point_H : bool, optional
            should gr_ID points coordinates be extracted. The default is True.

        Returns
        -------
        pd.DataFrame
            pandas data frame of coordinates.

        """
        #use grid_point_H = True for H points and False for Q points
        df = {'Type':[], 'MUID':[], 'Chainage':[], 'X':[], 'Y':[], 'Z':[]}
        reaches = self.result_data.Reaches
        
        for elem_type, elem_dict in zip(
                ['Orifice', 'Pump', 'Link', 'Regulation', 'Valve', 'Weir'], 
                [self.orifice_IDs, self.pump_IDs, self.reach_IDs, 
                 self.regulation_IDs, self.valve_IDs, self.weir_IDs]):
            for k, v in elem_dict.items():
                reach = reaches.get_Item(v)
                for gp in reach.GridPoints:
                    df['Type'].append(elem_type)
                    df['MUID'].append(k)
                    df['Chainage'].append(round(gp.get_Chainage(), 2))
                    df['X'].append(gp.get_X())
                    df['Y'].append(gp.get_Y())
                    df['Z'].append(gp.get_Z())
        
        return pd.DataFrame(data = df)


def test_network():
    res1d_file_path = r"C:\Users\YWANG\Documents\Python Scripts\res1d\test_data\VSA_2024_SCS1A_15_50mmDefault_Network_HD.res1d"
    res1d = Res1DNetwork(res1d_file_path)
    # test node counts
    print(f'Number of nodes: {res1d.node_count}')
    # test node data frame
    print('Node water levels: 7430A, 10034')
    df = res1d.get_node_data_frames(['7430A', '10034'], ['WaterLevel'])['WaterLevel']
    print(df.head())
    # test reach data frame
    print('link discharge: 480740, 40863_1')
    df = res1d.get_reach_data_frames(['480740', '40664C'], ['Discharge', 'WaterLevel'])
    print(df['Discharge'].head())
    print(df['WaterLevel'].head())
    # test structure data frame
    print('structure discharges: Weir_HAC_MH3B, Orifice_NAI_MH57', 'WILLINGDON 1', 'Yukon Radial Gate (T-C)')
    df = res1d.get_structure_data_frames(['Weir_HAC_MH3B', 'Orifice_NAI_MH57', 'WILLINGDON 1', 'Yukon Radial Gate (T-C)'])
    print(df['DischargeInStructure'].head())
    print(df['WaterLevel'].iloc[0,:])
    utilities_plotly.draw_graph([df['DischargeInStructure']])
    # test link coordinates
    df = res1d.get_link_coordinates_data_frame()
    print(df.head())
    
    
def main():
    print("in res1d_network.py!")
    test_network()


if __name__ == '__main__':
    import utilities_plotly
    main()