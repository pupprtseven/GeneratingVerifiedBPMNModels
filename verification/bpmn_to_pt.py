"""
BPMN to Petri Net Converter

This module provides functionality to convert BPMN diagrams to Petri nets,
supporting both single process and multi-lane collaboration diagrams.
"""

from typing import Dict, List, Tuple, Set, Any
import xml.etree.ElementTree as ET
import json


def save_petri_net_as_pnml(petri_net: Dict[str, Any], output_file: str):
    """
    Save Petri net data as PNML (Petri Net Markup Language) format.

    Args:
        petri_net: Petri net data structure
        output_file: Output file path
    """
    # Import configuration functions
    from utils.configure import get_petri_net_config, get_naming_convention

    # Create PNML XML structure
    root = ET.Element('pnml')

    # Add net element
    net = ET.SubElement(root, 'net')
    net_id = get_petri_net_config('NET_ID')
    net.set('id', str(net_id) if net_id is not None else 'bpmn_converted_net')
    net_type = get_petri_net_config('NET_TYPE')
    net.set('type', str(net_type)
            if net_type is not None else 'http://www.pnml.org/version-2009/grammar/pnmlcoremodel')

    # Add page element
    page = ET.SubElement(net, 'page')
    page_id = get_petri_net_config('PAGE_ID')
    page.set('id', str(page_id) if page_id is not None else 'page1')

    # Add places
    for place_id in petri_net['places']:
        place = ET.SubElement(page, 'place')
        place.set('id', place_id)

        # Add name
        name = ET.SubElement(place, 'name')
        text = ET.SubElement(name, 'text')
        text.text = place_id

        # Add initial marking if present
        if place_id in petri_net['initial_marking']:
            marking = ET.SubElement(place, 'initialMarking')
            text = ET.SubElement(marking, 'text')
            text.text = str(petri_net['initial_marking'][place_id])

    # Add transitions
    for transition_id in petri_net['transitions']:
        transition = ET.SubElement(page, 'transition')
        transition.set('id', transition_id)

        # Add name
        name = ET.SubElement(transition, 'name')
        text = ET.SubElement(name, 'text')
        text.text = transition_id

    # Add arcs
    arc_prefix = get_naming_convention('ARC_PREFIX')
    for i, arc in enumerate(petri_net['arcs']):
        arc_elem = ET.SubElement(page, 'arc')
        arc_elem.set('id', f'{arc_prefix}{i}')
        arc_elem.set('source', arc['source'])
        arc_elem.set('target', arc['target'])

    # Write to file
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(output_file, encoding='utf-8', xml_declaration=True)


class MultiLaneBpmnToPetriNetConverter:
    """
    Multi-lane BPMN to Petri Net Converter

    Supports multi-lane collaboration diagrams and message flow conversion
    """

    def __init__(self):
        self.lanes = {}  # Lane information
        self.message_flows = []  # Message flows
        self.petri_nets = {}  # Petri nets for each lane
        self.merged_petri_net = None  # Merged Petri net

    def parse_bpmn_collaboration(self, bpmn_file_path: str) -> Dict[str, Any]:
        """
        Parse BPMN collaboration diagram, extract lane and message flow information

        Args:
            bpmn_file_path: BPMN file path

        Returns:
            Dictionary containing lane and message flow information
        """
        tree = ET.parse(bpmn_file_path)
        root = tree.getroot()

        # Define BPMN namespace
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        collaboration_info = {
            'lanes': {},
            'message_flows': [],
            'processes': {}
        }

        # Find collaboration element
        collaboration = root.find('.//bpmn:collaboration', bpmn_ns)
        if collaboration is not None:
            # Parse lanes
            for participant in collaboration.findall('.//bpmn:participant', bpmn_ns):
                participant_id = participant.get('id')
                participant_name = participant.get('name', participant_id)
                process_ref = participant.get('processRef')

                collaboration_info['lanes'][participant_id] = {
                    'name': participant_name,
                    'process_ref': process_ref,
                    'tasks': [],
                    'start_events': [],
                    'end_events': [],
                    'gateways': []
                }

            # Parse message flows
            for message_flow in collaboration.findall('.//bpmn:messageFlow', bpmn_ns):
                source_ref = message_flow.get('sourceRef')
                target_ref = message_flow.get('targetRef')

                collaboration_info['message_flows'].append({
                    'source': source_ref,
                    'target': target_ref,
                    'id': message_flow.get('id', f"mf_{source_ref}_{target_ref}")
                })

        # Parse processes
        for process in root.findall('.//bpmn:process', bpmn_ns):
            process_id = process.get('id')
            collaboration_info['processes'][process_id] = {
                'tasks': [],
                'start_events': [],
                'end_events': [],
                'gateways': [],
                'sequence_flows': []
            }

            # Parse tasks
            for task in process.findall('.//bpmn:task', bpmn_ns):
                collaboration_info['processes'][process_id]['tasks'].append({
                    'id': task.get('id'),
                    'name': task.get('name', task.get('id')),
                    'type': 'task'
                })

            # Parse start events
            for start_event in process.findall('.//bpmn:startEvent', bpmn_ns):
                collaboration_info['processes'][process_id]['start_events'].append({
                    'id': start_event.get('id'),
                    'name': start_event.get('name', start_event.get('id')),
                    'type': 'startEvent'
                })

            # Parse end events
            for end_event in process.findall('.//bpmn:endEvent', bpmn_ns):
                collaboration_info['processes'][process_id]['end_events'].append({
                    'id': end_event.get('id'),
                    'name': end_event.get('name', end_event.get('id')),
                    'type': 'endEvent'
                })

            # Parse gateways
            for gateway in process.findall('.//bpmn:*', bpmn_ns):
                if 'Gateway' in gateway.tag:
                    collaboration_info['processes'][process_id]['gateways'].append({
                        'id': gateway.get('id'),
                        'name': gateway.get('name', gateway.get('id')),
                        'type': gateway.tag.split('}')[-1]
                    })

            # Parse sequence flows
            for seq_flow in process.findall('.//bpmn:sequenceFlow', bpmn_ns):
                collaboration_info['processes'][process_id]['sequence_flows'].append({
                    'id': seq_flow.get('id'),
                    'source': seq_flow.get('sourceRef'),
                    'target': seq_flow.get('targetRef')
                })

        return collaboration_info

    def convert_lane_to_petri_net(self, lane_info: Dict[str, Any], process_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert single lane to Petri net

        Args:
            lane_info: Lane information
            process_info: Corresponding process information

        Returns:
            Petri net representation of the lane
        """
        petri_net = {
            'places': [],
            'transitions': [],
            'arcs': [],
            'initial_marking': {},
            'final_markings': []
        }

        # Import configuration functions
        from utils.configure import get_naming_convention

        # Add start and end places
        start_prefix = get_naming_convention(
            'START_PLACE_PREFIX') or 'p_start_'
        end_prefix = get_naming_convention('END_PLACE_PREFIX') or 'p_end_'
        start_place = f"{start_prefix}{lane_info['name']}"
        end_place = f"{end_prefix}{lane_info['name']}"

        petri_net['places'].extend([start_place, end_place])
        petri_net['initial_marking'][start_place] = 1

        # Create transitions and places for each task
        pre_prefix = get_naming_convention('PRE_PLACE_PREFIX') or 'p_pre_'
        post_prefix = get_naming_convention('POST_PLACE_PREFIX') or 'p_post_'
        transition_prefix = get_naming_convention('TRANSITION_PREFIX') or 't_'

        for task in process_info['tasks']:
            task_id = task['id']
            pre_place = f"{pre_prefix}{task_id}"
            post_place = f"{post_prefix}{task_id}"
            transition = f"{transition_prefix}{task_id}"

            petri_net['places'].extend([pre_place, post_place])
            petri_net['transitions'].append(transition)
            petri_net['arcs'].extend([
                {'source': pre_place, 'target': transition},
                {'source': transition, 'target': post_place}
            ])

        # Create transitions and places for each gateway
        for gateway in process_info['gateways']:
            gateway_id = gateway['id']
            gateway_type = gateway['type']

            if 'Exclusive' in gateway_type or 'Inclusive' in gateway_type:
                # Exclusive or inclusive gateway
                pre_place = f"{pre_prefix}{gateway_id}"
                post_place = f"{post_prefix}{gateway_id}"
                transition = f"{transition_prefix}{gateway_id}"

                petri_net['places'].extend([pre_place, post_place])
                petri_net['transitions'].append(transition)
                petri_net['arcs'].extend([
                    {'source': pre_place, 'target': transition},
                    {'source': transition, 'target': post_place}
                ])
            elif 'Parallel' in gateway_type:
                # Parallel gateway
                pre_place = f"{pre_prefix}{gateway_id}"
                post_place = f"{post_prefix}{gateway_id}"
                transition = f"{transition_prefix}{gateway_id}"

                petri_net['places'].extend([pre_place, post_place])
                petri_net['transitions'].append(transition)
                petri_net['arcs'].extend([
                    {'source': pre_place, 'target': transition},
                    {'source': transition, 'target': post_place}
                ])

        # Connect places according to sequence flows
        for seq_flow in process_info['sequence_flows']:
            source = seq_flow['source']
            target = seq_flow['target']

            # Find corresponding places for source and target
            source_place = None
            target_place = None

            # Check if it's a start event
            if any(start['id'] == source for start in process_info['start_events']):
                source_place = start_place
            else:
                source_place = f"{post_prefix}{source}"

            # Check if it's an end event
            if any(end['id'] == target for end in process_info['end_events']):
                target_place = end_place
            else:
                target_place = f"{pre_prefix}{target}"

            # Add connection arc
            if source_place in petri_net['places'] and target_place in petri_net['places']:
                petri_net['arcs'].append({
                    'source': source_place,
                    'target': target_place
                })

        return petri_net

    def merge_petri_nets_with_message_flows(self, lane_petri_nets: Dict[str, Dict],
                                            message_flows: List[Dict]) -> Dict[str, Any]:
        """
        Merge multiple Petri nets and handle message flows

        Args:
            lane_petri_nets: Petri nets for each lane
            message_flows: List of message flows

        Returns:
            Merged Petri net
        """
        merged_net = {
            'places': [],
            'transitions': [],
            'arcs': [],
            'initial_marking': {},
            'final_markings': []
        }

        # Merge Petri nets from all lanes
        for lane_id, petri_net in lane_petri_nets.items():
            merged_net['places'].extend(petri_net['places'])
            merged_net['transitions'].extend(petri_net['transitions'])
            merged_net['arcs'].extend(petri_net['arcs'])
            merged_net['initial_marking'].update(petri_net['initial_marking'])

        # Import configuration functions
        from utils.configure import get_naming_convention

        # Handle message flows
        message_prefix = get_naming_convention(
            'MESSAGE_PLACE_PREFIX') or 'p_msg_'
        transition_prefix = get_naming_convention('TRANSITION_PREFIX') or 't_'

        for msg_flow in message_flows:
            source = msg_flow['source']
            target = msg_flow['target']

            # Create message place for each message flow
            message_place = f"{message_prefix}{msg_flow['id']}"
            merged_net['places'].append(message_place)

            # Connect source transition to message place
            source_transition = f"{transition_prefix}{source}"
            if source_transition in merged_net['transitions']:
                merged_net['arcs'].append({
                    'source': source_transition,
                    'target': message_place
                })

            # Connect message place to target transition
            target_transition = f"{transition_prefix}{target}"
            if target_transition in merged_net['transitions']:
                merged_net['arcs'].append({
                    'source': message_place,
                    'target': target_transition
                })

        return merged_net

    def convert_collaboration_bpmn_to_petri_net(self, bpmn_file_path: str) -> Dict[str, Any]:
        """
        Convert collaboration BPMN to Petri net

        Args:
            bpmn_file_path: BPMN file path

        Returns:
            Merged Petri net
        """
        # Parse BPMN collaboration
        collaboration_info = self.parse_bpmn_collaboration(bpmn_file_path)

        # Create Petri net for each lane
        lane_petri_nets = {}
        for lane_id, lane_info in collaboration_info['lanes'].items():
            process_ref = lane_info['process_ref']
            if process_ref in collaboration_info['processes']:
                process_info = collaboration_info['processes'][process_ref]
                petri_net = self.convert_lane_to_petri_net(
                    lane_info, process_info)
                lane_petri_nets[lane_id] = petri_net

        # Merge Petri nets and handle message flows
        merged_petri_net = self.merge_petri_nets_with_message_flows(
            lane_petri_nets,
            collaboration_info['message_flows']
        )

        return merged_petri_net


def convert_bpmn_to_petri_net(bpmn_file_path: str):
    """
    Convert BPMN to Petri net (supports single process and multi-lane collaboration)

    Args:
        bpmn_file_path: BPMN file path
    """
    # Check if it's a collaboration diagram
    tree = ET.parse(bpmn_file_path)
    root = tree.getroot()
    bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

    collaboration = root.find('.//bpmn:collaboration', bpmn_ns)

    if collaboration is not None:
        # Multi-lane collaboration diagram
        print("Collaboration diagram detected, using multi-lane conversion algorithm...")
        converter = MultiLaneBpmnToPetriNetConverter()
        petri_net = converter.convert_collaboration_bpmn_to_petri_net(
            bpmn_file_path)

        print("Conversion completed!")
        print(f"Number of places: {len(petri_net['places'])}")
        print(f"Number of transitions: {len(petri_net['transitions'])}")
        print(f"Number of arcs: {len(petri_net['arcs'])}")
        print(f"Initial marking: {petri_net['initial_marking']}")

        # Save results as PNML
        output_file = bpmn_file_path.replace('.bpmn', '_petri_net.pnml')
        save_petri_net_as_pnml(petri_net, output_file)
        print(f"Petri net saved to: {output_file}")

    else:
        # Single process BPMN
        print("Single process BPMN detected, using simplified conversion...")
        # Implement simplified single process conversion logic
        converter = MultiLaneBpmnToPetriNetConverter()
        # Treat single process as collaboration with one lane
        petri_net = converter.convert_collaboration_bpmn_to_petri_net(
            bpmn_file_path)

        print("Conversion completed!")
        print(f"Number of places: {len(petri_net['places'])}")
        print(f"Number of transitions: {len(petri_net['transitions'])}")
        print(f"Number of arcs: {len(petri_net['arcs'])}")
        print(f"Initial marking: {petri_net['initial_marking']}")

        # Save results as PNML
        output_file = bpmn_file_path.replace('.bpmn', '_petri_net.pnml')
        save_petri_net_as_pnml(petri_net, output_file)
        print(f"Petri net saved to: {output_file}")


if __name__ == "__main__":
    # Get BPMN file path from workplace configuration
    from utils.configure import get_workplace, get_petri_net_config
    import os

    workplace = get_workplace()

    # Look for BPMN file in workplace directory
    # Get possible BPMN file names from configuration
    possible_bpmn_files = get_petri_net_config('BPMN_INPUT_FILES') or [
        "bpmn_output.bpmn",
        "workflow.bpmn",
        "process.bpmn",
        "model.bpmn"
    ]

    bpmn_file_path = None

    # First check if there's a specific BPMN file mentioned in configuration
    # You can add BPMN_INPUT_FILE to configure.yml if needed
    for filename in possible_bpmn_files:
        file_path = os.path.join(workplace, filename)
        if os.path.exists(file_path):
            bpmn_file_path = file_path
            print(f"Found BPMN file: {bpmn_file_path}")
            break

    if bpmn_file_path is None:
        # If no BPMN file found, look for any .bpmn file in workplace
        for file in os.listdir(workplace):
            if file.endswith('.bpmn'):
                bpmn_file_path = os.path.join(workplace, file)
                print(f"Found BPMN file: {bpmn_file_path}")
                break

    if bpmn_file_path is None:
        print("No BPMN file found in workplace directory.")
        print("Please ensure a BPMN file exists in the workplace directory.")
        print("Expected file names: bpmn_output.bpmn, workflow.bpmn, process.bpmn, or any .bpmn file")
        exit(1)

    try:
        convert_bpmn_to_petri_net(bpmn_file_path)
        print("BPMN to Petri net conversion completed successfully!")
    except Exception as e:
        print(f"Error during conversion: {e}")
        exit(1)
