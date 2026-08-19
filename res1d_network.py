#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this is the res1d network class module

import res1d
import utilities
import pandas as pd
import numpy as np
import re
from dataclasses import dataclass, field


@dataclass
class StructureRef:
    structure_id: str
    structure_type: str
    reach_index: int
    reach_name: str
    chainage: float | None = None
    gridpoint_index: int | None = None
    source_kind: str = ""
    raw_type_text: str | None = None
    data_items_by_quantity: dict[str, object] = field(default_factory=dict)

class Res1DNetwork(res1d.Res1D):
    
    _node_quantity_IDs = []
    _reach_quantity_IDs = []
    _orifice_quantity_IDs = []
    _pump_quantity_IDs = []
    _regulation_quantity_IDs = []
    _weir_quantity_IDs = []
    _valve_quantity_IDs = []
    _bridge_quantity_IDs = []
    _direct_discharge_quantity_IDs = []
    _gate_quantity_IDs = []
    
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
                self.regulation_IDs, self.bridge_IDs, \
                self.direct_discharge_IDs, self.gate_IDs, \
                self.structure_IDs = self._get_element_IDs()
        self.node_count = len(self.node_IDs)
        self.reach_count = len(self.reach_IDs)
        self.weir_count = len(self.weir_IDs)
        self.pump_count = len(self.pump_IDs)
        self.orifice_count = len(self.orifice_IDs)
        self.valve_count = len(self.valve_IDs)
        self.regulation_count = len(self.regulation_IDs)
        self.bridge_count = len(self.bridge_IDs)
        self.direct_discharge_count = len(self.direct_discharge_IDs)
        self.gate_count = len(self.gate_IDs)
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
        self._bridge_quantity_IDs = self._get_structure_quantities(
            self.result_data.Reaches, self.bridge_IDs)
        self._direct_discharge_quantity_IDs = self._get_structure_quantities(
            self.result_data.Reaches, self.direct_discharge_IDs)
        self._gate_quantity_IDs = self._get_structure_quantities(
            self.result_data.Reaches, self.gate_IDs)
        
        
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
        if all(isinstance(e, StructureRef) for e in element_IDs.values()):
            for ref in element_IDs.values():
                qs.extend(ref.data_items_by_quantity.keys())
            return list(set(qs))
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
        # reach and structure ids as dictionaries
        reach_IDs = {}
        weir_IDs = {}
        pump_IDs = {}
        orifice_IDs = {}
        valve_IDs = {}
        regulation_IDs = {}
        bridge_IDs = {}
        direct_discharge_IDs = {}
        gate_IDs = {}
        structure_IDs = {}
        list_options = {
            'Weir': weir_IDs,
            'Pump': pump_IDs,
            'Orifice': orifice_IDs,
            'Valve': valve_IDs,
            'Regulation': regulation_IDs,
            'Bridge': bridge_IDs,
            'Direct_discharge': direct_discharge_IDs,
            'Gate': gate_IDs,
        }
        reaches = self.result_data.Reaches
        for k, reach in enumerate(reaches):
            # remove index suffix from id
            r_ID = '-'.join(reach.Id.split('-')[:-1])
            has_structure_quantity = any([
                    di.Quantity.Id in
                    ['DischargeInStructure', 'CrestLevel', 'ValveOpening',
                     'GateLevel', 'ControlStrategyId']
                    for di in reach.DataItems
                    ])
            has_regulation_description = any([
                    (di.Quantity.Description or '').endswith(
                        '(Regulating structure)')
                    for di in reach.DataItems
                    ])
            has_sewer_structure_prefix = any([
                    r_ID.startswith(tag)
                    for tag in ['Weir:', 'Pump:', 'Orifice:', 'Valve:']
                    ])
            is_structure_reach = (
                has_structure_quantity and
                (has_regulation_description or has_sewer_structure_prefix)
                )
            if is_structure_reach:
                # for HD result file
                if has_regulation_description:
                    # regulation link
                    reach_IDs[r_ID] = k
                    ref = self._create_structure_ref(
                        r_ID, 'regulation', k, reach,
                        'sewer_regulation_reach')
                    self._add_structure_ref(
                        regulation_IDs, structure_IDs, ref)
                else:
                    structure_type = r_ID.split(':')[0]
                    structure_id = ':'.join(r_ID.split(':')[1:])
                    ref = self._create_structure_ref(
                        structure_id, structure_type, k, reach,
                        'sewer_structure_reach')
                    self._add_structure_ref(
                        list_options.get(
                            self._structure_type_key(ref.structure_type)),
                        structure_IDs,
                        ref)
            elif any([
                    r_ID.startswith(tag)
                      for tag in ['Weir:', 'Pump:', 'Orifice:', 'Valve:']
                      ]):
                # for AD result file
                structure_type = r_ID.split(':')[0]
                structure_id = ':'.join(r_ID.split(':')[1:])
                ref = self._create_structure_ref(
                    structure_id, structure_type, k, reach,
                    'sewer_structure_reach')
                self._add_structure_ref(
                    list_options.get(
                        self._structure_type_key(ref.structure_type)),
                    structure_IDs,
                    ref)
            else:
                reach_IDs[r_ID] = k
            self._add_river_structure_refs(
                k, reach, list_options, structure_IDs)

        return [node_IDs, reach_IDs, weir_IDs,
                pump_IDs, orifice_IDs, valve_IDs, regulation_IDs,
                bridge_IDs, direct_discharge_IDs, gate_IDs,
                structure_IDs]


    def _add_river_structure_refs(
            self, reach_index, reach, list_options, structure_IDs):
        for data_item in reach.DataItems:
            if not self._is_river_structure_data_item(data_item):
                continue
            structure_id = data_item.ItemId
            if not structure_id:
                structure_id = self._parse_structure_id_from_description(
                    data_item.Quantity.Description)
            if not structure_id:
                continue
            raw_type = self._parse_structure_type_from_description(
                data_item.Quantity.Description)
            structure_type = self._normalize_structure_type(raw_type)
            ref = self._create_structure_ref(
                structure_id, structure_type, reach_index, reach,
                'river_structure_data_item', data_item, raw_type)
            self._add_structure_ref(
                list_options.get(self._structure_type_key(ref.structure_type)),
                structure_IDs,
                ref)


    def _is_river_structure_data_item(self, data_item):
        quantity_id = data_item.Quantity.Id
        description = data_item.Quantity.Description or ''
        description_lower = description.lower()
        is_structure_quantity = (
            'InStructure' in quantity_id or
            quantity_id == 'ControlStrategyId' or
            ' in structure:' in description_lower or
            description_lower.startswith('control strategy id:')
        )
        return data_item.ItemId is not None and is_structure_quantity


    def _create_structure_ref(
            self, structure_id, structure_type, reach_index, reach,
            source_kind, initial_data_item=None, raw_type_text=None):
        structure_type = self._normalize_structure_type(structure_type)
        gridpoint_index, chainage = self._get_data_item_gridpoint_info(
            reach, initial_data_item)
        ref = StructureRef(
            structure_id=structure_id,
            structure_type=structure_type,
            reach_index=reach_index,
            reach_name=reach.Id,
            chainage=chainage,
            gridpoint_index=gridpoint_index,
            source_kind=source_kind,
            raw_type_text=raw_type_text)
        if initial_data_item is None:
            for data_item in reach.DataItems:
                ref.data_items_by_quantity[data_item.Quantity.Id] = data_item
        else:
            ref.data_items_by_quantity[
                initial_data_item.Quantity.Id] = initial_data_item
        return ref


    def _add_structure_ref(self, type_dict, structure_IDs, ref):
        if type_dict is not None:
            if ref.structure_id in type_dict:
                type_dict[ref.structure_id].data_items_by_quantity.update(
                    ref.data_items_by_quantity)
            else:
                type_dict[ref.structure_id] = ref
        if ref.structure_type not in structure_IDs:
            structure_IDs[ref.structure_type] = {}
        if ref.structure_id in structure_IDs[ref.structure_type]:
            structure_IDs[ref.structure_type][ref.structure_id]\
                .data_items_by_quantity.update(ref.data_items_by_quantity)
        else:
            structure_IDs[ref.structure_type][ref.structure_id] = ref


    def _get_data_item_gridpoint_info(self, reach, data_item):
        if data_item is None or data_item.IndexList is None:
            return None, None
        index_list = list(data_item.IndexList)
        if not index_list:
            return None, None
        gridpoint_index = index_list[0]
        gridpoints = list(reach.GridPoints)
        if gridpoint_index >= len(gridpoints):
            return gridpoint_index, None
        return gridpoint_index, gridpoints[gridpoint_index].Chainage


    def _parse_structure_id_from_description(self, description):
        if not description or ':' not in description:
            return None
        text = description.split(':', 1)[1].strip()
        return text.split('(', 1)[0].strip() or None


    def _parse_structure_type_from_description(self, description):
        if not description:
            return None
        match = re.search(r'\(([^()]*)\)\s*$', description)
        if match is None:
            return None
        return match.group(1).strip()


    def _normalize_structure_type(self, structure_type):
        if not structure_type:
            return 'unknown'
        text = structure_type.strip().lower()
        text = text.replace('-', ' ').replace('_', ' ')
        if 'villemonte' in text or text == 'weir' or ' weir' in text:
            return 'weir'
        if 'discharge' in text:
            return 'direct_discharge'
        if 'bridge' in text:
            return 'bridge'
        if 'gate' in text:
            return 'gate'
        if 'pump' in text:
            return 'pump'
        if 'orifice' in text:
            return 'orifice'
        if 'valve' in text:
            return 'valve'
        if 'regulating structure' in text or text == 'regulation':
            return 'regulation'
        return re.sub(r'\W+', '_', text).strip('_') or 'unknown'


    def _structure_type_key(self, structure_type):
        if structure_type == 'direct_discharge':
            return 'Direct_discharge'
        return structure_type[:1].upper() + structure_type[1:]


    def _get_structure_data_frame(
            self, structure_IDs, extraction_IDs, quantity_IDs):
        """
        Extract time series from structure references.

        Structure references can point to sewer structure reaches or river
        structure data items nested in regular reaches. Returned data frames
        keep the same shape as _get_element_data_frame: one data frame per
        quantity, with simple MUID columns for one-column structure data.
        """
        extraction_IDs = utilities.list_cleanup(extraction_IDs)
        extraction_IDs = [
            eId for eId in extraction_IDs if eId in structure_IDs]

        df_elem = {}
        for quantity_ID in quantity_IDs:
            df_elem[quantity_ID] = []

        for name in extraction_IDs:
            ref = structure_IDs[name]
            for quantity_ID in quantity_IDs:
                data_item = ref.data_items_by_quantity.get(quantity_ID)
                if data_item is None:
                    continue
                d = self._structure_data_item_to_frame(
                    name, ref, data_item)
                df_elem[quantity_ID].append(d)

        for df in df_elem:
            if len(df_elem[df]) > 0:
                df_elem[df] = pd.concat(df_elem[df], axis=1)
                if df_elem[df].size > 0:
                    df_elem[df] = df_elem[df].iloc[self.time_stamp_indices]
                    df_elem[df].index = self.df_time_stamps
            else:
                df_elem[df] = pd.DataFrame(index=self.df_time_stamps)
        return df_elem


    def _structure_data_item_to_frame(self, name, ref, data_item):
        data = np.asarray(data_item.CreateDataArray())
        d = pd.DataFrame(data)
        if d.shape[1] == 1:
            d.columns = [name]
            return d

        chainages = self._get_structure_data_item_chainages(ref, data_item)
        if len(chainages) == d.shape[1]:
            d.columns = pd.MultiIndex.from_tuples(
                [(name, chainage) for chainage in chainages])
            d.columns = d.columns.set_names(['muid', 'chainage'])
            return d

        d.columns = pd.MultiIndex.from_tuples(
            [(name, i) for i in range(d.shape[1])])
        d.columns = d.columns.set_names(['muid', 'chainage'])
        return d


    def _get_structure_data_item_chainages(self, ref, data_item):
        reach = self.result_data.Reaches.get_Item(ref.reach_index)
        gridpoints = list(reach.GridPoints)
        if data_item.IndexList is not None:
            chainages = []
            for gridpoint_index in list(data_item.IndexList):
                if gridpoint_index < len(gridpoints):
                    chainages.append(gridpoints[gridpoint_index].Chainage)
            return chainages
        return [gp.Chainage for gp in gridpoints]
    
    
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
        
        dfs = self._get_structure_data_frame(
            self.orifice_IDs, extraction_IDs, quantity_IDs)
        
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
        
        dfs = self._get_structure_data_frame(
            self.pump_IDs, extraction_IDs, quantity_IDs)
        
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
        
        dfs = self._get_structure_data_frame(
            self.regulation_IDs, extraction_IDs, quantity_IDs)
        
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
        
        dfs = self._get_structure_data_frame(
            self.weir_IDs, extraction_IDs, quantity_IDs)
        
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
        
        dfs = self._get_structure_data_frame(
            self.valve_IDs, extraction_IDs, quantity_IDs)

        return dfs


    def get_bridge_data_frames(self, extraction_IDs,
                 quantity_IDs = _bridge_quantity_IDs):
        """
        extract time series from bridges.
        """

        dfs = self._get_structure_data_frame(
            self.bridge_IDs, extraction_IDs, quantity_IDs)

        return dfs


    def get_direct_discharge_data_frames(self, extraction_IDs,
                 quantity_IDs = _direct_discharge_quantity_IDs):
        """
        extract time series from direct discharge structures.
        """

        dfs = self._get_structure_data_frame(
            self.direct_discharge_IDs, extraction_IDs, quantity_IDs)

        return dfs


    def get_gate_data_frames(self, extraction_IDs,
                 quantity_IDs = _gate_quantity_IDs):
        """
        extract time series from gates.
        """

        dfs = self._get_structure_data_frame(
            self.gate_IDs, extraction_IDs, quantity_IDs)

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
        dfs['bridge'] = self.get_bridge_data_frames(extraction_IDs, quantity_IDs)
        dfs['direct_discharge'] = self.get_direct_discharge_data_frames(
            extraction_IDs, quantity_IDs)
        dfs['gate'] = self.get_gate_data_frames(extraction_IDs, quantity_IDs)
            
        
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
                ['Orifice', 'Pump', 'Link', 'Regulation', 'Valve', 'Weir',
                 'Bridge', 'Direct_discharge', 'Gate'],
                [self.orifice_IDs, self.pump_IDs, self.reach_IDs,
                 self.regulation_IDs, self.valve_IDs, self.weir_IDs,
                 self.bridge_IDs, self.direct_discharge_IDs, self.gate_IDs]):
            for k, v in elem_dict.items():
                reach_index = v.reach_index if isinstance(v, StructureRef) else v
                reach = reaches.get_Item(reach_index)
                gridpoints = list(reach.GridPoints)
                if isinstance(v, StructureRef) and v.gridpoint_index is not None:
                    if v.gridpoint_index < len(gridpoints):
                        gridpoints = [gridpoints[v.gridpoint_index]]
                for gp in gridpoints:
                    df['Type'].append(elem_type)
                    df['MUID'].append(k)
                    df['Chainage'].append(round(gp.get_Chainage(), 2))
                    df['X'].append(gp.get_X())
                    df['Y'].append(gp.get_Y())
                    df['Z'].append(gp.get_Z())
        
        return pd.DataFrame(data = df)


def test_network():
    res1d_file_path = r".\test_data\Rainfall_CDS_1yearHDBaseDefault_Network_HD.res1d"
    res1d = Res1DNetwork(res1d_file_path)
    # test node counts
    print(f'Number of nodes: {res1d.node_count}')
    # test node data frame
    print('Node water levels: C14150801, C15155101')
    df = res1d.get_node_data_frames(['C14150801A', 'C15155101'], ['WaterLevel'])['WaterLevel']
    print(df.head())
    # test reach data frame
    print('link discharge: C16164102.2, Link_35')
    df = res1d.get_reach_data_frames(['C16164102.2', 'Link_35'], ['Discharge', 'WaterLevel'])
    print(df['Discharge'].head())
    print(df['WaterLevel'].head())
    # test structure data frame
    print('structure discharges: Weir_to_river, Orifice_7', 'Pump_2_to_WWTP')
    df = res1d.get_structure_data_frames(['Weir_to_river', 'Orifice_7', 'Pump_2_to_WWTP'])
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
