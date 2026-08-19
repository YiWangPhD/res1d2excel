#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this is the res1d network class module

import re
from dataclasses import dataclass, field

import pandas as pd

import res1d
import utilities


@dataclass
class DataItemRef:
    data_item: object
    element_index: int | None = None
    gridpoint_index: int | None = None
    chainage: float | None = None


@dataclass
class ElementRef:
    muid: str
    element_type: str
    collection_name: str
    collection_index: int
    source_kind: str
    data_items_by_quantity: dict[str, DataItemRef] = field(default_factory=dict)
    chainage: float | None = None
    gridpoint_index: int | None = None
    raw_type_text: str | None = None


class Res1DNetwork(res1d.Res1D):

    STRUCTURE_TYPE_RULES = {
        'weir': ['villemonte', 'weir'],
        'direct_discharge': ['discharge structure', 'direct discharge',
                             'discharge'],
        'bridge': ['bridge'],
        'gate': ['gate'],
        'pump': ['pump'],
        'orifice': ['orifice'],
        'valve': ['valve'],
        'regulation': ['regulating structure', 'regulation'],
    }

    STRUCTURE_REACH_PREFIXES = ['Weir:', 'Pump:', 'Orifice:', 'Valve:']
    STRUCTURE_REACH_QUANTITIES = [
        'DischargeInStructure', 'CrestLevel', 'ValveOpening',
        'GateLevel', 'ControlStrategyId'
    ]
    DEFAULT_STRUCTURE_QUANTITIES = [
        'WaterLevel', 'Discharge', 'DischargeInStructure',
        'ControlStrategyId'
    ]

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
        self.node_IDs = {}
        self.reach_IDs = {}
        self.weir_IDs = {}
        self.pump_IDs = {}
        self.orifice_IDs = {}
        self.valve_IDs = {}
        self.regulation_IDs = {}
        self.bridge_IDs = {}
        self.direct_discharge_IDs = {}
        self.gate_IDs = {}
        self.structure_IDs = {}
        self.unknown_structure_IDs = {}

        self._build_node_index()
        self._build_reach_and_structure_index()
        self._collect_quantity_ids()

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

    def _build_node_index(self):
        for k, node in enumerate(self.result_data.Nodes):
            self.node_IDs[node.Id] = self._create_element_ref(
                node.Id, 'node', 'Nodes', k, node, 'node')

    def _build_reach_and_structure_index(self):
        for k, reach in enumerate(self.result_data.Reaches):
            reach_id = self._reach_id_without_index(reach.Id)
            handled_as_structure = self._add_sewer_structure_ref(
                reach_id, k, reach)
            if not handled_as_structure:
                self.reach_IDs[reach_id] = self._create_element_ref(
                    reach_id, 'link', 'Reaches', k, reach, 'reach')
            self._add_river_structure_refs(k, reach)

    def _collect_quantity_ids(self):
        self._node_quantity_IDs = self._get_ref_quantities(self.node_IDs)
        self._reach_quantity_IDs = self._get_ref_quantities(self.reach_IDs)
        self._orifice_quantity_IDs = self._get_ref_quantities(self.orifice_IDs)
        self._pump_quantity_IDs = self._get_ref_quantities(self.pump_IDs)
        self._regulation_quantity_IDs = self._get_ref_quantities(
            self.regulation_IDs)
        self._weir_quantity_IDs = self._get_ref_quantities(self.weir_IDs)
        self._valve_quantity_IDs = self._get_ref_quantities(self.valve_IDs)
        self._bridge_quantity_IDs = self._get_ref_quantities(self.bridge_IDs)
        self._direct_discharge_quantity_IDs = self._get_ref_quantities(
            self.direct_discharge_IDs)
        self._gate_quantity_IDs = self._get_ref_quantities(self.gate_IDs)

    def _get_ref_quantities(self, element_IDs):
        qs = []
        for ref in element_IDs.values():
            qs.extend(ref.data_items_by_quantity.keys())
        return list(set(qs))

    def _get_structure_quantities(self, elements, element_IDs):
        """
        collect structure quantity types

        Kept for compatibility with older internal callers. The redesigned
        network index stores quantity lookup directly in ElementRef objects.
        """
        return self._get_ref_quantities(element_IDs)

    def _reach_id_without_index(self, reach_id):
        return '-'.join(reach_id.split('-')[:-1])

    def _add_sewer_structure_ref(self, reach_id, reach_index, reach):
        has_structure_quantity = any([
            di.Quantity.Id in self.STRUCTURE_REACH_QUANTITIES
            for di in reach.DataItems
        ])
        has_regulation_description = any([
            (di.Quantity.Description or '').endswith('(Regulating structure)')
            for di in reach.DataItems
        ])
        has_structure_prefix = any([
            reach_id.startswith(tag)
            for tag in self.STRUCTURE_REACH_PREFIXES
        ])

        if has_structure_quantity and has_regulation_description:
            ref = self._create_element_ref(
                reach_id, 'regulation', 'Reaches', reach_index, reach,
                'sewer_regulation_reach')
            self.reach_IDs[reach_id] = ref
            self._add_structure_ref(ref)
            return True

        if has_structure_quantity and has_structure_prefix:
            structure_type, structure_id = self._parse_structure_reach_id(
                reach_id)
            ref = self._create_element_ref(
                structure_id, structure_type, 'Reaches', reach_index, reach,
                'sewer_structure_reach')
            self._add_structure_ref(ref)
            return True

        if has_structure_prefix:
            structure_type, structure_id = self._parse_structure_reach_id(
                reach_id)
            ref = self._create_element_ref(
                structure_id, structure_type, 'Reaches', reach_index, reach,
                'sewer_structure_reach')
            self._add_structure_ref(ref)
            return True

        return False

    def _parse_structure_reach_id(self, reach_id):
        structure_type = reach_id.split(':')[0]
        structure_id = ':'.join(reach_id.split(':')[1:])
        return structure_type, structure_id

    def _add_river_structure_refs(self, reach_index, reach):
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
            data_ref = self._create_data_item_ref(reach, data_item, 0)
            ref = ElementRef(
                muid=structure_id,
                element_type=structure_type,
                collection_name='Reaches',
                collection_index=reach_index,
                source_kind='river_structure_data_item',
                data_items_by_quantity={data_item.Quantity.Id: data_ref},
                chainage=data_ref.chainage,
                gridpoint_index=data_ref.gridpoint_index,
                raw_type_text=raw_type)
            self._add_structure_ref(ref)

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

    def _create_element_ref(
            self, muid, element_type, collection_name, collection_index,
            element, source_kind, raw_type_text=None):
        data_items = {
            data_item.Quantity.Id: DataItemRef(data_item=data_item)
            for data_item in element.DataItems
        }
        return ElementRef(
            muid=muid,
            element_type=self._normalize_structure_type(element_type),
            collection_name=collection_name,
            collection_index=collection_index,
            source_kind=source_kind,
            data_items_by_quantity=data_items,
            raw_type_text=raw_type_text)

    def _create_data_item_ref(self, reach, data_item, element_index=None):
        gridpoint_index, chainage = self._get_data_item_gridpoint_info(
            reach, data_item, element_index)
        return DataItemRef(
            data_item=data_item,
            element_index=element_index,
            gridpoint_index=gridpoint_index,
            chainage=chainage)

    def _get_data_item_gridpoint_info(
            self, reach, data_item, element_index=None):
        if data_item is None or data_item.IndexList is None:
            return None, None
        index_list = list(data_item.IndexList)
        if not index_list:
            return None, None
        if element_index is None:
            element_index = 0
        if element_index >= len(index_list):
            return None, None
        gridpoint_index = index_list[element_index]
        gridpoints = list(reach.GridPoints)
        if gridpoint_index >= len(gridpoints):
            return gridpoint_index, None
        return gridpoint_index, gridpoints[gridpoint_index].Chainage

    def _add_structure_ref(self, ref):
        type_dict = self._get_structure_type_dict(ref.element_type)
        if type_dict is not None:
            self._merge_ref(type_dict, ref)
        self.structure_IDs.setdefault(ref.element_type, {})
        self._merge_ref(self.structure_IDs[ref.element_type], ref)
        if type_dict is None:
            self._merge_ref(self.unknown_structure_IDs, ref)

    def _merge_ref(self, target, ref):
        if ref.muid in target:
            target[ref.muid].data_items_by_quantity.update(
                ref.data_items_by_quantity)
            if target[ref.muid].chainage is None:
                target[ref.muid].chainage = ref.chainage
            if target[ref.muid].gridpoint_index is None:
                target[ref.muid].gridpoint_index = ref.gridpoint_index
            return
        target[ref.muid] = ref

    def _get_structure_type_dict(self, structure_type):
        return {
            'weir': self.weir_IDs,
            'pump': self.pump_IDs,
            'orifice': self.orifice_IDs,
            'valve': self.valve_IDs,
            'regulation': self.regulation_IDs,
            'bridge': self.bridge_IDs,
            'direct_discharge': self.direct_discharge_IDs,
            'gate': self.gate_IDs,
        }.get(structure_type)

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
        for normalized_type, tokens in self.STRUCTURE_TYPE_RULES.items():
            if any(token in text for token in tokens):
                return normalized_type
        return re.sub(r'\W+', '_', text).strip('_') or 'unknown'

    def _get_ref_element(self, ref):
        collection = getattr(self.result_data, ref.collection_name)
        return collection.get_Item(ref.collection_index)

    def _get_ref_data_frames(self, element_IDs, extraction_IDs, quantity_IDs):
        extraction_IDs = utilities.list_cleanup(extraction_IDs)
        extraction_IDs = [eId for eId in extraction_IDs if eId in element_IDs]

        df_elem = {}
        for quantity_ID in quantity_IDs:
            df_elem[quantity_ID] = []

        for name in extraction_IDs:
            ref = element_IDs[name]
            for quantity_ID in quantity_IDs:
                data_ref = ref.data_items_by_quantity.get(quantity_ID)
                if data_ref is None:
                    continue
                d = self._ref_data_item_to_frame(name, ref, data_ref)
                df_elem[quantity_ID].append(d)

        return self._finalize_quantity_frames(df_elem)

    def _ref_data_item_to_frame(self, name, ref, data_ref):
        chainages = None
        if data_ref.element_index is None:
            element = self._get_ref_element(ref)
            data = self._get_data_item_array(data_ref.data_item)
            column_count = self._get_data_column_count(data)
            if column_count > 1:
                if ref.source_kind != 'river_structure_data_item':
                    chainages = self._get_element_chainages(
                        element, column_count, name)
                else:
                    chainages = self._get_structure_data_item_chainages(
                        ref, data_ref.data_item)
            return self._data_array_to_frame(
                name,
                data,
                chainages,
                strict_chainages=(
                    ref.source_kind != 'river_structure_data_item'))
        return self._data_item_to_frame(
            name,
            data_ref.data_item,
            element_index=data_ref.element_index)

    def _get_structure_data_item_chainages(self, ref, data_item):
        element = self._get_ref_element(ref)
        gridpoints = list(element.GridPoints)
        if data_item.IndexList is not None:
            chainages = []
            for gridpoint_index in list(data_item.IndexList):
                if gridpoint_index < len(gridpoints):
                    chainages.append(gridpoints[gridpoint_index].Chainage)
            return chainages
        return [gp.Chainage for gp in gridpoints]

    def _get_combined_frames(self, extraction_IDs, source_specs):
        frames = []
        for getter, quantities in source_specs:
            dfs = getter(extraction_IDs, quantities)
            for quantity in quantities:
                if quantity in dfs:
                    frames.append(dfs[quantity])
        if not frames:
            return pd.DataFrame(index=self.df_time_stamps)
        return pd.concat(frames, axis=1)

    def get_node_data_frames(self, extraction_IDs,
                quantity_IDs = _node_quantity_IDs):
        """
        extract time series from nodes.
        """
        return self._get_ref_data_frames(
            self.node_IDs, extraction_IDs, quantity_IDs)

    def get_reach_data_frames(self, extraction_IDs,
                 quantity_IDs = _reach_quantity_IDs):
        """
        extract time series from reaches.
        """
        return self._get_ref_data_frames(
            self.reach_IDs, extraction_IDs, quantity_IDs)

    def get_orifice_data_frames(self, extraction_IDs,
                 quantity_IDs = _orifice_quantity_IDs):
        """
        extract time series from orifices.
        """
        return self._get_ref_data_frames(
            self.orifice_IDs, extraction_IDs, quantity_IDs)

    def get_pump_data_frames(self, extraction_IDs,
                 quantity_IDs = _pump_quantity_IDs):
        """
        extract time series from pumps.
        """
        return self._get_ref_data_frames(
            self.pump_IDs, extraction_IDs, quantity_IDs)

    def get_regulation_data_frames(self, extraction_IDs,
                 quantity_IDs = _regulation_quantity_IDs):
        """
        extract time series from regulations.
        """
        return self._get_ref_data_frames(
            self.regulation_IDs, extraction_IDs, quantity_IDs)

    def get_weir_data_frames(self, extraction_IDs,
                 quantity_IDs = _weir_quantity_IDs):
        """
        extract time series from weirs.
        """
        return self._get_ref_data_frames(
            self.weir_IDs, extraction_IDs, quantity_IDs)

    def get_valve_data_frames(self, extraction_IDs,
                 quantity_IDs = _valve_quantity_IDs):
        """
        extract time series from valves.
        """
        return self._get_ref_data_frames(
            self.valve_IDs, extraction_IDs, quantity_IDs)

    def get_bridge_data_frames(self, extraction_IDs,
                 quantity_IDs = _bridge_quantity_IDs):
        """
        extract time series from bridges.
        """
        return self._get_ref_data_frames(
            self.bridge_IDs, extraction_IDs, quantity_IDs)

    def get_direct_discharge_data_frames(self, extraction_IDs,
                 quantity_IDs = _direct_discharge_quantity_IDs):
        """
        extract time series from direct discharge structures.
        """
        return self._get_ref_data_frames(
            self.direct_discharge_IDs, extraction_IDs, quantity_IDs)

    def get_gate_data_frames(self, extraction_IDs,
                 quantity_IDs = _gate_quantity_IDs):
        """
        extract time series from gates.
        """
        return self._get_ref_data_frames(
            self.gate_IDs, extraction_IDs, quantity_IDs)

    def get_structure_data_frames(
            self, extraction_IDs, quantity_IDs = DEFAULT_STRUCTURE_QUANTITIES):
        """
        extract time series from structures.
        """
        extraction_IDs = utilities.list_cleanup(extraction_IDs)
        dfs = {}

        for structure_type, getter in [
                ('orifice', self.get_orifice_data_frames),
                ('pump', self.get_pump_data_frames),
                ('regulation', self.get_regulation_data_frames),
                ('weir', self.get_weir_data_frames),
                ('valve', self.get_valve_data_frames),
                ('bridge', self.get_bridge_data_frames),
                ('direct_discharge', self.get_direct_discharge_data_frames),
                ('gate', self.get_gate_data_frames)]:
            dfs[structure_type] = getter(extraction_IDs, quantity_IDs)

        quantity_IDs = list(
            set.union(*[set(list(df.keys())) for df in dfs.values()])
        )

        return {
            qID: pd.concat(
                [df[qID] for df in dfs.values() if qID in df.keys()], axis=1
            )
            for qID in quantity_IDs
        }

    def get_discharge_data_frame(self, extraction_IDs):
        """
        extract time series of discharges, regardless of element types.
        """
        extraction_IDs = utilities.list_cleanup(extraction_IDs)
        return self._get_combined_frames(
            extraction_IDs,
            [
                (self.get_node_data_frames, ['WaterSpillDischarge']),
                (self.get_structure_data_frames,
                 ['Discharge', 'DischargeInStructure']),
                (self.get_reach_data_frames, ['Discharge']),
            ])

    def get_link_coordinates_data_frame(self, grid_point_H = True):
        """
        extract coordinates of links to pandas data frame
        """
        #use grid_point_H = True for H points and False for Q points
        df = {'Type':[], 'MUID':[], 'Chainage':[], 'X':[], 'Y':[], 'Z':[]}

        for elem_type, elem_dict in [
                ('Orifice', self.orifice_IDs),
                ('Pump', self.pump_IDs),
                ('Link', self.reach_IDs),
                ('Regulation', self.regulation_IDs),
                ('Valve', self.valve_IDs),
                ('Weir', self.weir_IDs),
                ('Bridge', self.bridge_IDs),
                ('Direct_discharge', self.direct_discharge_IDs),
                ('Gate', self.gate_IDs)]:
            for k, ref in elem_dict.items():
                reach = self._get_ref_element(ref)
                gridpoints = list(reach.GridPoints)
                if ref.gridpoint_index is not None:
                    if ref.gridpoint_index < len(gridpoints):
                        gridpoints = [gridpoints[ref.gridpoint_index]]
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
