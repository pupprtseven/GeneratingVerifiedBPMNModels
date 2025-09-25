"""
Read BPMN collaboration and process diagrams, generate simplified structural descriptions,
and use LLM to generate corresponding BPMN requirement descriptions.

This module extracts structural information from BPMN files and generates user requirement
descriptions that explain what the BPMN model represents.
"""

import xml.etree.ElementTree as ET
import json
import os
from typing import Dict, List, Set, Optional, Any
from utils.agent import generate_prompt_from_config
from utils.configure import get_workplace, get_verification_config_path, get_output_file_name


# Configuration paths loaded from configure.yml
REQUIREMENT_CONFIG_PATH = get_verification_config_path(
    "REQUIREMENT_CONFIG_PATH") or "benchmark/config/requirement.json"
REQUIREMENT_OUTPUT_FILE = get_output_file_name(
    "REQUIREMENT_OUTPUT_FILE") or "requirement_description.json"


def detect_bpmn_type(bpmn_xml_content: str) -> str:
    """
    Detect whether the BPMN model is a collaboration diagram or process diagram.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        'collaboration' if collaboration diagram, 'process' if process diagram
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        # Check for collaboration elements
        collaboration = root.find('.//bpmn:collaboration', bpmn_ns)
        if collaboration is not None:
            return 'collaboration'

        # Check for process elements
        process = root.find('.//bpmn:process', bpmn_ns)
        if process is not None:
            return 'process'

        # Default to process if neither is found
        return 'process'

    except ET.ParseError as e:
        print(f"Error detecting BPMN type: {e}")
        return 'process'


def extract_lanes(bpmn_xml_content: str) -> List[Dict[str, str]]:
    """
    Extract lane information from BPMN XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        List of lane dictionaries with id and name
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        lanes = []

        # Extract lanes
        for lane in root.findall('.//bpmn:lane', bpmn_ns):
            lane_id = lane.get('id', '')
            lane_name = lane.get('name', '')
            if lane_id:
                lanes.append({
                    'id': lane_id,
                    'name': lane_name or lane_id
                })

        return lanes

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML for lanes: {e}")
        return []


def extract_participants(bpmn_xml_content: str) -> List[Dict[str, str]]:
    """
    Extract participant information from BPMN XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        List of participant dictionaries with id and name
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        participants = []

        # Extract participants
        for participant in root.findall('.//bpmn:participant', bpmn_ns):
            participant_id = participant.get('id', '')
            participant_name = participant.get('name', '')
            if participant_id:
                participants.append({
                    'id': participant_id,
                    'name': participant_name or participant_id
                })

        return participants

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML for participants: {e}")
        return []


def extract_activities(bpmn_xml_content: str) -> List[Dict[str, str]]:
    """
    Extract activity information from BPMN XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        List of activity dictionaries with id, name, and type
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        activities = []

        # Extract all activity types
        activity_types = [
            'task', 'userTask', 'serviceTask', 'scriptTask', 'businessRuleTask',
            'manualTask', 'sendTask', 'receiveTask', 'subProcess'
        ]

        for activity_type in activity_types:
            for activity in root.findall(f'.//bpmn:{activity_type}', bpmn_ns):
                activity_id = activity.get('id', '')
                activity_name = activity.get('name', '')
                if activity_id:
                    activities.append({
                        'id': activity_id,
                        'name': activity_name or activity_id,
                        'type': activity_type
                    })

        return activities

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML for activities: {e}")
        return []


def extract_gateways(bpmn_xml_content: str) -> List[Dict[str, str]]:
    """
    Extract gateway information from BPMN XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        List of gateway dictionaries with id, name, and type
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        gateways = []

        # Extract all gateway types
        gateway_types = [
            'exclusiveGateway', 'inclusiveGateway', 'parallelGateway', 'eventBasedGateway'
        ]

        for gateway_type in gateway_types:
            for gateway in root.findall(f'.//bpmn:{gateway_type}', bpmn_ns):
                gateway_id = gateway.get('id', '')
                gateway_name = gateway.get('name', '')
                if gateway_id:
                    gateways.append({
                        'id': gateway_id,
                        'name': gateway_name or gateway_id,
                        'type': gateway_type
                    })

        return gateways

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML for gateways: {e}")
        return []


def extract_events(bpmn_xml_content: str) -> List[Dict[str, str]]:
    """
    Extract event information from BPMN XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        List of event dictionaries with id, name, and type
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        events = []

        # Extract all event types
        event_types = [
            'startEvent', 'endEvent', 'intermediateThrowEvent', 'intermediateCatchEvent',
            'boundaryEvent'
        ]

        for event_type in event_types:
            for event in root.findall(f'.//bpmn:{event_type}', bpmn_ns):
                event_id = event.get('id', '')
                event_name = event.get('name', '')
                if event_id:
                    events.append({
                        'id': event_id,
                        'name': event_name or event_id,
                        'type': event_type
                    })

        return events

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML for events: {e}")
        return []


def extract_flows(bpmn_xml_content: str) -> List[Dict[str, str]]:
    """
    Extract flow information from BPMN XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        List of flow dictionaries with id, source, target, and type
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        flows = []

        # Extract sequence flows
        for flow in root.findall('.//bpmn:sequenceFlow', bpmn_ns):
            flow_id = flow.get('id', '')
            source_ref = flow.get('sourceRef', '')
            target_ref = flow.get('targetRef', '')
            if flow_id and source_ref and target_ref:
                flows.append({
                    'id': flow_id,
                    'source': source_ref,
                    'target': target_ref,
                    'type': 'sequenceFlow'
                })

        # Extract message flows
        for flow in root.findall('.//bpmn:messageFlow', bpmn_ns):
            flow_id = flow.get('id', '')
            source_ref = flow.get('sourceRef', '')
            target_ref = flow.get('targetRef', '')
            if flow_id and source_ref and target_ref:
                flows.append({
                    'id': flow_id,
                    'source': source_ref,
                    'target': target_ref,
                    'type': 'messageFlow'
                })

        return flows

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML for flows: {e}")
        return []


def extract_bpmn_structure(bpmn_xml_content: str) -> Dict[str, Any]:
    """
    Extract complete structural information from BPMN XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        Dictionary containing all structural information
    """
    bpmn_type = detect_bpmn_type(bpmn_xml_content)

    structure = {
        'bpmn_type': bpmn_type,
        'lanes': extract_lanes(bpmn_xml_content),
        'participants': extract_participants(bpmn_xml_content),
        'activities': extract_activities(bpmn_xml_content),
        'gateways': extract_gateways(bpmn_xml_content),
        'events': extract_events(bpmn_xml_content),
        'flows': extract_flows(bpmn_xml_content)
    }

    return structure


def generate_requirement_description(bpmn_structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate requirement description using LLM based on BPMN structure.

    Args:
        bpmn_structure: Dictionary containing BPMN structural information

    Returns:
        Dictionary containing requirement description
    """
    # Prepare input variables for LLM
    input_vars = {
        "BPMN_STRUCTURE": json.dumps(bpmn_structure, ensure_ascii=False, indent=2)
    }

    # Generate requirement description using agent
    result = generate_prompt_from_config(REQUIREMENT_CONFIG_PATH, input_vars)

    # Extract the output
    extracted_output = result.get('extracted_output', {})

    # Save full results for debugging
    save_requirement_result(result, "requirement_generation")

    return extracted_output


def save_requirement_result(result: Dict[str, Any], operation: str):
    """
    Save requirement generation result to file.

    Args:
        result: Requirement generation result
        operation: Operation description
    """
    workplace = get_workplace()
    output_file = os.path.join(workplace, REQUIREMENT_OUTPUT_FILE)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Requirement result saved: {output_file}")
    except Exception as e:
        print(f"Failed to save requirement result: {e}")


def load_bpmn_from_file(file_path: str) -> str:
    """
    Load BPMN XML content from file.

    Args:
        file_path: Path to BPMN file

    Returns:
        BPMN XML content as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Loaded BPMN file: {file_path}")
            return content
    except FileNotFoundError as e:
        print(f"Failed to load BPMN file {file_path}: {e}")
        return ""
    except Exception as e:
        print(f"Error reading BPMN file {file_path}: {e}")
        return ""


def process_bpmn_file(bpmn_file_path: str) -> Optional[Dict[str, Any]]:
    """
    Process a single BPMN file to generate requirement description.

    Args:
        bpmn_file_path: Path to BPMN file

    Returns:
        Dictionary containing requirement description and structure
    """
    # Load BPMN content
    bpmn_xml_content = load_bpmn_from_file(bpmn_file_path)
    if not bpmn_xml_content:
        return None

    # Extract structure
    bpmn_structure = extract_bpmn_structure(bpmn_xml_content)

    print(f"Extracted structure from {bpmn_file_path}:")
    print(f"  BPMN Type: {bpmn_structure['bpmn_type']}")
    print(f"  Lanes: {len(bpmn_structure['lanes'])}")
    print(f"  Participants: {len(bpmn_structure['participants'])}")
    print(f"  Activities: {len(bpmn_structure['activities'])}")
    print(f"  Gateways: {len(bpmn_structure['gateways'])}")
    print(f"  Events: {len(bpmn_structure['events'])}")
    print(f"  Flows: {len(bpmn_structure['flows'])}")

    # Generate requirement description
    requirement_description = generate_requirement_description(bpmn_structure)

    result = {
        'bpmn_file': bpmn_file_path,
        'bpmn_structure': bpmn_structure,
        'requirement_description': requirement_description
    }

    return result


def process_bpmn_directory(directory_path: str) -> List[Dict[str, Any]]:
    """
    Process all BPMN files in a directory.

    Args:
        directory_path: Path to directory containing BPMN files

    Returns:
        List of results for each BPMN file
    """
    results = []

    try:
        for filename in os.listdir(directory_path):
            if filename.endswith('.bpmn') or filename.endswith('.xml'):
                file_path = os.path.join(directory_path, filename)
                result = process_bpmn_file(file_path)
                if result:
                    results.append(result)
    except Exception as e:
        print(f"Error processing directory {directory_path}: {e}")

    return results


if __name__ == '__main__':
    try:
        print("Starting BPMN requirement description generation...")

        # Example: Process a single BPMN file
        workplace = get_workplace()
        bpmn_file = os.path.join(workplace, "target_bpmn.bpmn")

        if os.path.exists(bpmn_file):
            result = process_bpmn_file(bpmn_file)
            if result:
                print("\n=== Requirement Description ===")
                print(json.dumps(
                    result['requirement_description'], ensure_ascii=False, indent=2))
                print(
                    f"Results saved to: {get_workplace()}/{REQUIREMENT_OUTPUT_FILE}")
            else:
                print("Requirement generation failed")
        else:
            print(f"BPMN file not found: {bpmn_file}")
            print("Please place a BPMN file in the workplace directory")

    except Exception as e:
        print(f"Requirement generation failed: {e}")
