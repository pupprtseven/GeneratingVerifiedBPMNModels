"""
Generate complete BPMN data by integrating all components.

This module provides the main function to generate complete BPMN data
by integrating actors, tasks, control flows, and gateways.
"""

import json
import os
import datetime
from utils.configure import get_workplace
from generation.symbol import generate_symbol, get_symbol_data
from generation.task import generate_task_with_extra, get_full_task_data
from generation.seq import generate_updated_flow
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Configuration constants
ENABLE_DUMP = True  # Toggle switch for dump functionality
# BPMN output file configuration (customize file name and path as needed)
BPMN_OUTPUT_FILE = os.path.join(
    get_workplace(), "bpmn_output.json")  # BPMN data output file
BPMN_XML_OUTPUT_FILE = os.path.join(
    get_workplace(), "bpmn_output.bpmn")  # BPMN XML output file


def generate_bpmn_data():
    """
    Generate complete BPMN data by integrating all components.

    This function:
    1. Gets actors from symbol generation
    2. Gets tasks and task types from task generation
    3. Gets updated control flow with gateways
    4. Decides whether to generate collaboration diagram based on actor count

    Returns:
        Dictionary containing complete BPMN data
    """
    print("=" * 60)
    print("Starting BPMN generation...")
    print("=" * 60)

    # 1. Get actors from symbol generation
    print("\n1. Getting actors from symbol generation...")
    if ENABLE_DUMP:
        # Use existing get_symbol_data function
        symbol_result = get_symbol_data()
        actors = symbol_result.get('actor', [])
        print(f"Loaded actors using get_symbol_data()")
        print(f"Number of actors: {len(actors)}")
    else:
        # Generate new symbol data
        symbol_result = generate_symbol()
        actors = symbol_result.get('actor', [])
        print(f"Generated {len(actors)} actors")

    if not actors:
        print("No actors found!")
        return None

    # 2. Get tasks and task types from task generation
    print("\n2. Getting tasks and task types from task generation...")
    if ENABLE_DUMP:
        # Use existing get_task_data function for tasks
        tasks = get_symbol_data().get('tasks', [])

        # Use existing get_full_task_data function for task types
        full_task_data = get_full_task_data()
        task_types = full_task_data.get(
            'extracted_output', {}).get('task_types', [])

        # Get additional task_types from extra.message if exists
        if 'extra' in full_task_data and 'message' in full_task_data['extra']:
            message_data = full_task_data['extra']['message']
            if 'extracted_output' in message_data:
                message_task_types = message_data['extracted_output'].get(
                    'task_types', [])
                # Merge task_types
                task_types.extend(message_task_types)

        print(f"Loaded tasks using get_symbol_data()")
        print(f"Loaded task types using get_full_task_data()")
        print(f"Number of tasks: {len(tasks)}")
        print(f"Number of task types: {len(task_types)}")
    else:
        # Generate new task data
        task_result = generate_task_with_extra()
        tasks = task_result.get('tasks', [])
        task_types = task_result.get('task_types', [])
        print(f"Generated {len(tasks)} tasks")
        print(f"Generated {len(task_types)} task types")

    if not tasks:
        print("No tasks found!")
        return None

    # 3. Get updated control flow with gateways
    print("\n3. Getting updated control flow with gateways...")
    updated_flow_result = generate_updated_flow()
    if not updated_flow_result:
        print("Failed to get updated control flow! Using empty defaults.")
        # return None
        updated_control_flow = []
        gateways = []
    else:
        updated_control_flow = updated_flow_result['updated_control_flow']
        gateways = updated_flow_result['gateways']
    print(f"Got {len(updated_control_flow)} updated control flows")
    print(f"Got {len(gateways)} gateways")

    # 4. Decide whether to generate collaboration diagram
    print("\n4. Analyzing actor count for collaboration decision...")
    actor_count = len(actors)
    is_collaboration = actor_count > 1

    print(f"Actor count: {actor_count}")
    print(f"Collaboration diagram needed: {is_collaboration}")

    if is_collaboration:
        print("Multiple actors detected - will generate collaboration diagram")
    else:
        print("Single actor detected - will generate process diagram")

    # 5. Assemble complete BPMN data
    print("\n5. Assembling complete BPMN data...")
    bpmn_data = {
        "actors": actors,
        "tasks": tasks,
        "task_types": task_types,
        "control_flow": updated_control_flow or [],
        "gateways": gateways or [],
        "is_collaboration": is_collaboration,
        "actor_count": actor_count,
        "generation_info": {
            "dump_enabled": ENABLE_DUMP,
            "generation_timestamp": str(datetime.datetime.now()),
            "source_files": {
                "symbol": "symbol_output.json" if ENABLE_DUMP else "generated",
                "task": "task_output.json" if ENABLE_DUMP else "generated",
                "sequence": "seq_output.json" if ENABLE_DUMP else "generated",
                "gate": "gate_output.json" if ENABLE_DUMP else "generated"
            }
        }
    }

    # 6. Save complete BPMN data if dump is enabled
    if ENABLE_DUMP:
        with open(BPMN_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(bpmn_data, f, ensure_ascii=False, indent=2)
        print(f"Complete BPMN data saved to: {BPMN_OUTPUT_FILE}")

    print("\n" + "=" * 60)
    print("BPMN generation completed successfully!")
    print("=" * 60)
    print(f"Summary:")
    print(f"- Actors: {len(actors)}")
    print(f"- Tasks: {len(tasks)}")
    print(f"- Task Types: {len(task_types)}")
    print(f"- Control Flows: {len(updated_control_flow)}")
    print(f"- Gateways: {len(gateways)}")
    print(f"- Collaboration: {is_collaboration}")
    print(f"- Dump Mode: {ENABLE_DUMP}")

    return bpmn_data


def prettify_xml(elem):
    """Format XML with proper indentation."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def generate_collaboration_bpmn(bpmn_data):
    """
    Generate BPMN 2.0 XML for collaboration diagram (multiple actors).

    Args:
        bpmn_data: Dictionary containing BPMN data from generate_bpmn()

    Returns:
        XML string in BPMN 2.0 format
    """
    # BPMN namespaces
    ns = {
        'bpmn': "http://www.omg.org/spec/BPMN/20100524/MODEL",
        'bpmndi': "http://www.omg.org/spec/BPMN/20100524/DI",
        'omgdc': "http://www.omg.org/spec/DD/20100524/DC",
        'omgdi': "http://www.omg.org/spec/DD/20100524/DI"
    }

    # Register namespaces
    for prefix, uri in ns.items():
        ET.register_namespace(prefix, uri)

    # Create root element
    definitions = ET.Element('definitions', {
        'xmlns': ns['bpmn'],
        'xmlns:bpmndi': ns['bpmndi'],
        'xmlns:omgdc': ns['omgdc'],
        'xmlns:omgdi': ns['omgdi'],
        'id': 'Definitions_1',
        'targetNamespace': 'http://example.com/bpmn'
    })

    # Create collaboration element
    collaboration = ET.SubElement(definitions, 'collaboration', {
        'id': 'Collaboration_1'
    })

    # Create processes for each actor
    processes = {}
    participants = {}

    for i, actor in bpmn_data['actors']:
        actor_symbol = actor['symbol']
        actor_name = actor['actor_name']
        process_id = f"Process_{actor_symbol}"

        # Create participant
        participant = ET.SubElement(collaboration, 'participant', {
            'id': f"Participant_{actor_symbol}",
            'name': actor_name,
            'processRef': process_id
        })
        participants[actor_symbol] = participant

        # Create process
        process = ET.SubElement(definitions, 'process', {
            'id': process_id,
            'name': f"{actor_name} Process",
            'isExecutable': 'true'
        })
        processes[actor_symbol] = process

    # Add tasks/start/end events to processes
    for task in bpmn_data['tasks']:
        actor_symbol = task['actor_symbol']
        task_symbol = task['task_symbol']
        task_description = task.get('task_description', '')

        if actor_symbol in processes:
            if task_symbol.startswith('S'):
                ET.SubElement(processes[actor_symbol], 'startEvent', {
                    'id': task_symbol,
                    'name': task_description
                })
            elif task_symbol.startswith('E'):
                ET.SubElement(processes[actor_symbol], 'endEvent', {
                    'id': task_symbol,
                    'name': task_description
                })
            else:
                ET.SubElement(processes[actor_symbol], 'task', {
                    'id': task_symbol,
                    'name': task_description
                })

    # Add gateways to processes
    gateways = bpmn_data.get("gateways", [])
    # if 'gateways' in bpmn_data:
    if gateways:
        for gateway in bpmn_data['gateways']:
            gateway_symbol = gateway['gateway_symbol']
            gateway_type = gateway['gateway_type']

            # For simplicity, add to first process (can be improved later)
            first_process = list(processes.values())[0]

            # Map gateway types to BPMN elements
            if 'Parallel' in gateway_type:
                ET.SubElement(first_process, 'parallelGateway', {
                    'id': gateway_symbol,
                    'name': gateway_type
                })
            elif 'Exclusive' in gateway_type:
                ET.SubElement(first_process, 'exclusiveGateway', {
                    'id': gateway_symbol,
                    'name': gateway_type
                })
            elif 'Inclusive' in gateway_type:
                ET.SubElement(first_process, 'inclusiveGateway', {
                    'id': gateway_symbol,
                    'name': gateway_type
                })
            else:
                ET.SubElement(first_process, 'exclusiveGateway', {
                    'id': gateway_symbol,
                    'name': gateway_type
                })
        else:
            print("Gateways data missing - skipping gateway creation")
    else:
        print("No gateways provided - skipping gateway creation")
    # Add sequence flows
    for flow in bpmn_data['control_flow']:
        from_task = flow['from']
        to_task = flow['to']
        actor = flow['actor']

        # Find the process for this actor
        target_process = None
        if actor == 'GATEWAY':
            target_process = list(processes.values())[0]
        else:
            for actor_data in bpmn_data['actors']:
                if actor_data['symbol'] == actor:
                    target_process = processes[actor]
                    break

        if target_process:
            ET.SubElement(target_process, 'sequenceFlow', {
                'id': f"Flow_{from_task}_to_{to_task}",
                'sourceRef': from_task,
                'targetRef': to_task
            })

    # Add message flows based on seq_output.json message_flow data
    print("Adding message flows from seq_output.json message_flow data...")
    message_flows_added = 0

    # Get message flows from seq_output.json
    workplace = get_workplace()
    seq_file_path = os.path.join(workplace, "seq_output.json")

    # Store existing message flows to avoid duplicates
    existing_message_flows = set()

    try:
        with open(seq_file_path, 'r', encoding='utf-8') as f:
            seq_data = json.load(f)
            message_flows = seq_data.get(
                'extracted_output', {}).get('message_flow', [])
            print(
                f"Found {len(message_flows)} message flows in seq_output.json")

            for msg_flow in message_flows:
                from_actor = msg_flow['from_actor']
                to_actor = msg_flow['to_actor']
                from_task = msg_flow['from']
                to_task = msg_flow['to']

                # Store this flow to avoid duplicates
                existing_message_flows.add((from_task, to_task))

                # Create message flow in collaboration
                ET.SubElement(collaboration, 'messageFlow', {
                    'id': f"MessageFlow_{from_task}_to_{to_task}",
                    'sourceRef': from_task,
                    'targetRef': to_task
                })
                message_flows_added += 1
                print(
                    f"Added message flow: {from_task} ({from_actor}) -> {to_task} ({to_actor})")

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Failed to load message flows from seq_output.json: {e}")

    # Add message flows based on task and extra.message correspondence rule
    print("Adding message flows based on task and extra.message correspondence...")

    # Get full task data to access extra.message
    full_task_data = get_full_task_data()
    extra = full_task_data.get('extra', {})

    if 'message' in extra:
        message_tasks = extra['message'].get(
            'extracted_output', {}).get('tasks', [])
        print(f"Found {len(message_tasks)} message tasks in extra.message")

        # Create a set of original task symbols for quick lookup
        original_task_symbols = {task['task_symbol']
                                 for task in bpmn_data['tasks']}

        for msg_task in message_tasks:
            msg_task_symbol = msg_task['task_symbol']

            # Check if this is a -r1, -r2, etc. task
            if '-r' in msg_task_symbol:
                # Extract the base task symbol (e.g., "T5-r1" -> "T5")
                base_task_symbol = msg_task_symbol.split('-r')[0]

                # Check if the base task exists in original tasks
                if base_task_symbol in original_task_symbols:
                    # Find the original task to get its actor
                    original_task = None
                    for task in bpmn_data['tasks']:
                        if task['task_symbol'] == base_task_symbol:
                            original_task = task
                            break

                    if original_task:
                        from_actor = original_task['actor_symbol']
                        to_actor = msg_task['actor_symbol']

                        # Only create message flow if actors are different
                        if from_actor != to_actor:
                            # Check if this message flow already exists
                            if (base_task_symbol, msg_task_symbol) not in existing_message_flows:
                                # Create message flow in collaboration
                                ET.SubElement(collaboration, 'messageFlow', {
                                    'id': f"MessageFlow_{base_task_symbol}_to_{msg_task_symbol}",
                                    'sourceRef': base_task_symbol,
                                    'targetRef': msg_task_symbol
                                })
                                message_flows_added += 1
                                print(
                                    f"Added correspondence message flow: {base_task_symbol} ({from_actor}) -> {msg_task_symbol} ({to_actor})")
                            else:
                                print(
                                    f"Skipped duplicate message flow: {base_task_symbol} -> {msg_task_symbol}")

    print(f"Total message flows added: {message_flows_added}")
    return prettify_xml(definitions)


def generate_process_bpmn(bpmn_data):
    """
    Generate BPMN 2.0 XML for process diagram (single actor).

    Args:
        bpmn_data: Dictionary containing BPMN data from generate_bpmn()

    Returns:
        XML string in BPMN 2.0 format
    """
    # BPMN namespaces
    ns = {
        'bpmn': "http://www.omg.org/spec/BPMN/20100524/MODEL",
        'bpmndi': "http://www.omg.org/spec/BPMN/20100524/DI",
        'omgdc': "http://www.omg.org/spec/DD/20100524/DC",
        'omgdi': "http://www.omg.org/spec/DD/20100524/DI"
    }

    # Register namespaces
    for prefix, uri in ns.items():
        ET.register_namespace(prefix, uri)

    # Create root element
    definitions = ET.Element('definitions', {
        'xmlns': ns['bpmn'],
        'xmlns:bpmndi': ns['bpmndi'],
        'xmlns:omgdc': ns['omgdc'],
        'xmlns:omgdi': ns['omgdi'],
        'id': 'Definitions_1',
        'targetNamespace': 'http://example.com/bpmn'
    })

    # Get the single actor
    actor = bpmn_data['actors'][0]
    actor_symbol = actor['symbol']
    actor_name = actor['actor_name']

    # Create process
    process = ET.SubElement(definitions, 'process', {
        'id': f"Process_{actor_symbol}",
        'name': f"{actor_name} Process",
        'isExecutable': 'true'
    })

    # Add tasks/start/end events
    for task in bpmn_data['tasks']:
        task_symbol = task['task_symbol']
        task_description = task.get('task_description', '')

        if task_symbol.startswith('S'):
            ET.SubElement(process, 'startEvent', {
                'id': task_symbol,
                'name': task_description
            })
        elif task_symbol.startswith('E'):
            ET.SubElement(process, 'endEvent', {
                'id': task_symbol,
                'name': task_description
            })
        else:
            # Determine task type
            task_type = 'task'  # default
            for task_type_info in bpmn_data['task_types']:
                if task_type_info.get('task_symbol') == task_symbol:
                    task_type = task_type_info.get('task_type', 'task')
                    break

            if task_type == 'message receiver':
                # Create intermediate catch event for message receiver
                task_element = ET.SubElement(process, 'intermediateCatchEvent', {
                    'id': task_symbol,
                    'name': task_description
                })
                # Add message event definition
                ET.SubElement(task_element, 'messageEventDefinition')
            else:
                # Create regular task
                ET.SubElement(process, 'task', {
                    'id': task_symbol,
                    'name': task_description
                })

    # Add gateways
    gateways = bpmn_data.get("gateways", [])
    if gateways:
        for gateway in gateways:
            gateway_symbol = gateway['gateway_symbol', 'Go']
            gateway_type = gateway['gateway_type', 'Exclusive Gateway']

            # Map gateway types to BPMN elements
            if 'Parallel' in gateway_type:
                ET.SubElement(process, 'parallelGateway', {
                    'id': gateway_symbol,
                    'name': gateway_type
                })
            elif 'Exclusive' in gateway_type:
                ET.SubElement(process, 'exclusiveGateway', {
                    'id': gateway_symbol,
                    'name': gateway_type
                })
            elif 'Inclusive' in gateway_type:
                ET.SubElement(process, 'inclusiveGateway', {
                    'id': gateway_symbol,
                    'name': gateway_type
                })
            else:
                # Default to exclusive gateway
                ET.SubElement(process, 'exclusiveGateway', {
                    'id': gateway_symbol,
                    'name': gateway_type
                })
    else:
        print("No gateways provided - skipping gateway creation")

    # Add sequence flows
    control_flow = bpmn_data.get("control_flow", [])
    for flow in control_flow:
        from_task = flow['from', '']
        to_task = flow['to', '']

        ET.SubElement(process, 'sequenceFlow', {
            'id': f"Flow_{from_task}_to_{to_task}",
            'sourceRef': from_task,
            'targetRef': to_task
        })

    if not control_flow:
        print("No sequence flows added - no connections between tasks")

    return prettify_xml(definitions)


def generate_bpmn_xml(bpmn_data, output_file=None):
    """
    Generate BPMN 2.0 XML file based on the BPMN data.

    Args:
        bpmn_data: Dictionary containing BPMN data from generate_bpmn()
        output_file: Optional output file path. If None, saves to workplace.

    Returns:
        Path to the generated XML file
    """
    workplace = get_workplace()

    # is_collaboration = bpmn_data.get("is_collaboration", False)
    # # Determine which function to use based on collaboration flag
    # if bpmn_data['is_collaboration']:
    #     print("Generating collaboration BPMN XML...")
    #     xml_content = generate_collaboration_bpmn(bpmn_data)
    #     diagram_type = "collaboration"
    # else:
    #     print("Generating process BPMN XML...")
    #     xml_content = generate_process_bpmn(bpmn_data)
    #     diagram_type = "process"

    is_collaboration = bpmn_data.get("is_collaboration", False)
    if is_collaboration:
        print("Generating collaboration BPMN XML...")
        try:
            xml_content = generate_collaboration_bpmn(bpmn_data)
        except Exception as e:
            print(f"❌ Failed to generate collaboration BPMN: {e}")
            xml_content = "<definitions xmlns='http://www.omg.org/spec/BPMN/20100524/MODEL'/>"
    else:
        print("Generating process BPMN XML...")
        try:
            xml_content = generate_process_bpmn(bpmn_data)
        except Exception as e:
            print(f"❌ Failed to generate process BPMN: {e}")
            xml_content = "<definitions xmlns='http://www.omg.org/spec/BPMN/20100524/MODEL'/>"
    diagram_type = "collaboration" if is_collaboration else "process"

    # Determine output file path
    if output_file is None:
        output_file = BPMN_XML_OUTPUT_FILE

    # Write XML to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    print(f"BPMN XML file generated: {output_file}")
    print(f"Diagram type: {diagram_type}")

    return output_file


if __name__ == '__main__':
    try:
        print("Testing BPMN generation...")
        bpmn_result = generate_bpmn_data()
        if bpmn_result:
            print("\nBPMN data summary:")
            print(f"- Actors: {len(bpmn_result['actors'])}")
            print(f"- Tasks: {len(bpmn_result['tasks'])}")
            print(f"- Task Types: {len(bpmn_result['task_types'])}")
            print(f"- Control Flows: {len(bpmn_result['control_flow'])}")
            print(f"- Gateways: {len(bpmn_result['gateways'])}")
            print(f"- Collaboration: {bpmn_result['is_collaboration']}")
            print(
                f"- Dump Mode: {bpmn_result['generation_info']['dump_enabled']}")

            # Generate BPMN XML file
            print("\n" + "=" * 50)
            print("Generating BPMN XML file...")
            print("=" * 50)
            xml_file = generate_bpmn_xml(bpmn_result)
            print(f"XML file generated successfully: {xml_file}")

        else:
            print("Failed to generate BPMN data!")
    except (FileNotFoundError, ValueError, json.JSONDecodeError, KeyError) as e:
        print(f"BPMN generation failed: {e}")
