"""
Generate sequence flows from requirements and tasks.

This module analyzes business requirements and task data to generate
sequence flows and message flows for BPMN generation.
"""

import json
import os
from utils.agent import generate_prompt_from_config
from utils.configure import get_workplace
from utils.load_requirement import get_reqstring
from utils.combine import combine_results
from generation.task import generate_task_with_extra, get_full_task_data
from generation.symbol import get_symbol_data


# Configuration paths loaded from configure.yml
from utils.configure import get_generation_config_path, get_output_file_name

SEQ_CONFIG_PATH = get_generation_config_path(
    "SEQ_CONFIG_PATH") or "generation/config/seq.json"
GATE_CONFIG_PATH = get_generation_config_path(
    "GATE_CONFIG_PATH") or "generation/config/gate.json"
SEQ_OUTPUT_FILE = get_output_file_name("SEQ_OUTPUT_FILE") or "seq_output.json"
GATE_OUTPUT_FILE = get_output_file_name(
    "GATE_OUTPUT_FILE") or "gate_output.json"
TASK_OUTPUT_FILE = get_output_file_name(
    "TASK_OUTPUT_FILE") or "task_output.json"
SYMBOL_OUTPUT_FILE = get_output_file_name(
    "SYMBOL_OUTPUT_FILE") or "symbol_output.json"
ENABLE_DUMP = True  # Toggle switch for dump functionality


def generate_sequence():
    """
    Generate sequence flows from requirements and task data.

    Returns:
        Dictionary containing extracted sequence flows and message flows
    """
    # Get requirement string
    requirement = get_reqstring()

    # Get and format task data based on dump switch
    if ENABLE_DUMP:
        # Read from existing files and combine all extracted_output
        print("Dump enabled: Reading from symbol_output.json and task_output.json...")
        symbol_data = get_symbol_data()
        task_data = get_full_task_data()

        # Combine main task extracted_output with symbol data
        combined_data = combine_results(
            symbol_data, task_data.get('extracted_output', {}))

        # Add all extra sections
        if 'extra' in task_data:
            for _, extra_data in task_data['extra'].items():
                if isinstance(extra_data, dict) and 'extracted_output' in extra_data:
                    combined_data = combine_results(
                        combined_data, extra_data['extracted_output'])

        formatted_tasks = json.dumps(
            combined_data, ensure_ascii=False, indent=2)
    else:
        # Generate new data using generate_task_with_extra
        print("Dump disabled: Generating new task data...")
        task_data = generate_task_with_extra()
        formatted_tasks = json.dumps(
            task_data, ensure_ascii=False, indent=2)

    # Prepare input variables
    input_vars = {
        "REQUIREMENT": requirement,
        "FORMATTASK": formatted_tasks
    }

    # Generate sequence output using agent
    result = generate_prompt_from_config(SEQ_CONFIG_PATH, input_vars)

    # Extract the output and return directly
    extracted_output = result.get('extracted_output', {})

    # Save full results for debugging (if enabled)
    if ENABLE_DUMP:
        workplace = get_workplace()
        output_path = os.path.join(workplace, SEQ_OUTPUT_FILE)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(
            f"Sequence generation completed. Results saved to: {output_path}")

    print("Extracted output:")
    print(json.dumps(extracted_output, ensure_ascii=False, indent=2))

    return extracted_output


def generate_gate():
    """
    Generate gate conditions from requirements and task data.

    Returns:
        Dictionary containing extracted gate conditions
    """
    # Get requirement string
    requirement = get_reqstring()

    # Get sequence data first to extract pairs
    print("Getting sequence data to extract pairs...")
    seq_result = generate_sequence()

    # Extract pairs from control_flow
    pairs = extract_pairs_from_control_flow(seq_result.get('control_flow', []))

    if not pairs:
        print("No pairs found. Skipping gateway generation.")
        return {}

    # Get and format task data based on dump switch
    if ENABLE_DUMP:
        # Read from existing files and combine all extracted_output
        print("Dump enabled: Reading from symbol_output.json and task_output.json for gate generation...")
        symbol_data = get_symbol_data()
        task_data = get_full_task_data()

        # Combine main task extracted_output with symbol data
        combined_data = combine_results(
            symbol_data, task_data.get('extracted_output', {}))

        # Add all extra sections
        if 'extra' in task_data:
            for _, extra_data in task_data['extra'].items():
                if isinstance(extra_data, dict) and 'extracted_output' in extra_data:
                    combined_data = combine_results(
                        combined_data, extra_data['extracted_output'])

        formatted_tasks = json.dumps(
            combined_data, ensure_ascii=False, indent=2)
    else:
        # Generate new data using generate_task_with_extra
        print("Dump disabled: Generating new task data for gate generation...")
        task_data = generate_task_with_extra()
        formatted_tasks = json.dumps(
            task_data, ensure_ascii=False, indent=2)

    # Prepare input variables
    input_vars = {
        "REQUIREMENT": requirement,
        "PAIRS": pairs,
        "FORMATTASK": formatted_tasks
    }

    # Generate gate output using agent
    result = generate_prompt_from_config(GATE_CONFIG_PATH, input_vars)

    # Extract the output and return directly
    extracted_output = result.get('extracted_output', {})

    # Save full results for debugging (if enabled)
    if ENABLE_DUMP:
        workplace = get_workplace()
        output_path = os.path.join(workplace, GATE_OUTPUT_FILE)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(
            f"Gate generation completed. Results saved to: {output_path}")

    print("Extracted output:")
    print(json.dumps(extracted_output, ensure_ascii=False, indent=2))

    return extracted_output


def extract_pairs_from_control_flow(control_flow):
    """
    Extract pairs from control flow based on multiple from/to relationships.

    Args:
        control_flow: List of control flow objects with actor, from, to fields

    Returns:
        List of pairs grouped by multiple from/to relationships
    """
    pairs = []

    # Group by 'to' field to find multiple 'from' -> one 'to' (convergent)
    to_groups = {}
    for flow in control_flow:
        to_task = flow['to']
        if to_task not in to_groups:
            to_groups[to_task] = []
        to_groups[to_task].append(flow['from'])

    # Find convergent pairs (multiple from -> one to)
    for to_task, from_tasks in to_groups.items():
        if len(from_tasks) > 1:
            # Remove duplicates and sort for consistency
            unique_from_tasks = sorted(list(set(from_tasks)))
            pairs.append({
                "type": "convergent",
                "from_tasks": unique_from_tasks,
                "to_task": to_task
            })

    # Group by 'from' field to find one 'from' -> multiple 'to' (divergent)
    from_groups = {}
    for flow in control_flow:
        from_task = flow['from']
        if from_task not in from_groups:
            from_groups[from_task] = []
        from_groups[from_task].append(flow['to'])

    # Find divergent pairs (one from -> multiple to)
    for from_task, to_tasks in from_groups.items():
        if len(to_tasks) > 1:
            # Remove duplicates and sort for consistency
            unique_to_tasks = sorted(list(set(to_tasks)))
            pairs.append({
                "type": "divergent",
                "from_task": from_task,
                "to_tasks": unique_to_tasks
            })

    return pairs


def update_seq_with_gate(control_flow, gateways):
    """
    Update sequence flows with gateway information based on the algorithm.

    This function implements the algorithm to:
    1. Build input and output closures for all gateways
    2. Remove flows that are now handled by gateways
    3. Add new flows connecting tasks to gateways

    Args:
        control_flow: List of control flow objects with actor, from, to fields
        gateways: List of gateway objects with gateway_symbol, from_tasks, to_tasks fields

    Returns:
        Updated control flow list with gateway connections
    """
    # Initialize: input closure IC = {}, output closure OC = {}, flow set F' = F
    IC = set()  # Input closure
    OC = set()  # Output closure
    F_prime = control_flow.copy()  # Flow set F'

    # Create a mapping of gateway symbols to their gateway objects
    gateway_map = {gw['gateway_symbol']: gw for gw in gateways}

    def add_input_actions_to_closure(element, closure):
        """
        Recursively add input actions to closure.

        Args:
            element: Either a task symbol or gateway symbol
            closure: The closure set to add actions to
        """
        if element in gateway_map:
            # If element is a gateway, recursively process its inputs
            gateway = gateway_map[element]
            for input_task in gateway['from_tasks']:
                add_input_actions_to_closure(input_task, closure)
        else:
            # If element is a task, add it to closure
            closure.add(element)

    def add_output_actions_to_closure(element, closure):
        """
        Recursively add output actions to closure.

        Args:
            element: Either a task symbol or gateway symbol
            closure: The closure set to add actions to
        """
        if element in gateway_map:
            # If element is a gateway, recursively process its outputs
            gateway = gateway_map[element]
            for output_task in gateway['to_tasks']:
                add_output_actions_to_closure(output_task, closure)
        else:
            # If element is a task, add it to closure
            closure.add(element)

    # For each gateway (g, I, O) in G
    for gateway in gateways:
        gateway_symbol = gateway['gateway_symbol']
        from_tasks = gateway['from_tasks']
        to_tasks = gateway['to_tasks']

        # For each input e in I
        for input_task in from_tasks:
            add_input_actions_to_closure(input_task, IC)

        # Similarly for all outputs o in O, add actions to OC
        for output_task in to_tasks:
            add_output_actions_to_closure(output_task, OC)

    # For each flow (f_in, f_out) in F
    flows_to_remove = []
    for flow in F_prime:
        f_in = flow['from']
        f_out = flow['to']

        # If f_in is in IC and f_out is in OC
        if f_in in IC and f_out in OC:
            # Remove this flow from F'
            flows_to_remove.append(flow)

    # Remove the identified flows
    for flow in flows_to_remove:
        F_prime.remove(flow)

    # For each gateway (g, I, O) in G
    for gateway in gateways:
        gateway_symbol = gateway['gateway_symbol']
        from_tasks = gateway['from_tasks']
        to_tasks = gateway['to_tasks']

        # For each input i in I
        for input_task in from_tasks:
            # If (i, g) is not in F
            if not any(flow['from'] == input_task and flow['to'] == gateway_symbol for flow in F_prime):
                # Add (i, g) to F'
                F_prime.append({
                    'actor': 'GATEWAY',  # Use a special actor for gateway connections
                    'from': input_task,
                    'to': gateway_symbol
                })

        # Similarly for all outputs o in O, add (g, o) to F'
        for output_task in to_tasks:
            # If (g, o) is not in F
            if not any(flow['from'] == gateway_symbol and flow['to'] == output_task for flow in F_prime):
                # Add (g, o) to F'
                F_prime.append({
                    'actor': 'GATEWAY',  # Use a special actor for gateway connections
                    'from': gateway_symbol,
                    'to': output_task
                })

    return F_prime


def generate_updated_flow():
    """
    Generate updated flow with gateway information based on ENABLE_DUMP setting.

    This function intelligently decides whether to:
    - Read from existing files (when ENABLE_DUMP=True)
    - Generate new data and update flow (when ENABLE_DUMP=False)

    Returns:
        Dictionary containing updated control flow with gateway connections
    """
    workplace = get_workplace()

    if ENABLE_DUMP:
        # Read from existing files to avoid duplicate LLM calls
        print("Dump enabled: Reading from existing seq_output.json and gate_output.json...")

        # Read control flow from seq_output.json
        seq_file_path = os.path.join(workplace, SEQ_OUTPUT_FILE)
        try:
            with open(seq_file_path, 'r', encoding='utf-8') as f:
                seq_data = json.load(f)
                control_flow = seq_data.get(
                    'extracted_output', {}).get('control_flow', [])
                print(f"Loaded control flow from: {seq_file_path}")
                print(f"Number of control flows: {len(control_flow)}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Failed to load control flow from {seq_file_path}: {e}")
            return None

        # Read gateways from gate_output.json
        gate_file_path = os.path.join(workplace, GATE_OUTPUT_FILE)
        try:
            with open(gate_file_path, 'r', encoding='utf-8') as f:
                gate_data = json.load(f)
                gateways = gate_data.get(
                    'extracted_output', {}).get('gateways', [])
                print(f"Loaded gateways from: {gate_file_path}")
                print(f"Number of gateways: {len(gateways)}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Failed to load gateways from {gate_file_path}: {e}")
            return None

        if not control_flow:
            print("No control flow data found!")
            return None

        if not gateways:
            print("No gateway data found!")
            return None

    else:
        # Generate new data without saving intermediate files
        print("Dump disabled: Generating new sequence and gate data...")

        # Generate sequence data
        print("Generating sequence data...")
        seq_result = generate_sequence()
        control_flow = seq_result.get('control_flow', [])
        print(f"Generated {len(control_flow)} control flows")

        # Generate gate data
        print("Generating gate data...")
        gate_data = generate_gate()
        gateways = gate_data.get('gateways', [])
        print(f"Generated {len(gateways)} gateways")

        if not control_flow:
            print("No control flow data generated!")
            return None

        if not gateways:
            print("No gateway data generated!")
            return None

    # Update flow with gateway information
    print("Updating flow with gateway information...")
    updated_flow = update_seq_with_gate(control_flow, gateways)

    # Save results if dump is enabled
    if ENABLE_DUMP:
        updated_flow_file = os.path.join(workplace, "updated_flow_output.json")
        with open(updated_flow_file, 'w', encoding='utf-8') as f:
            json.dump({
                "original_control_flow": control_flow,
                "gateways": gateways,
                "updated_control_flow": updated_flow
            }, f, ensure_ascii=False, indent=2)

        print(f"Updated flow saved to: {updated_flow_file}")

    print("Updated flow generation completed!")
    print(f"Original flows: {len(control_flow)}")
    print(f"Gateways: {len(gateways)}")
    print(f"Updated flows: {len(updated_flow)}")

    return {
        "original_control_flow": control_flow,
        "gateways": gateways,
        "updated_control_flow": updated_flow
    }


def test_extract_pairs():
    """
    Test function to verify extract_pairs_from_control_flow function using real data from seq_output.json.
    """
    workplace = get_workplace()

    # Read control flow from seq_output.json
    seq_file_path = os.path.join(workplace, SEQ_OUTPUT_FILE)
    try:
        with open(seq_file_path, 'r', encoding='utf-8') as f:
            seq_data = json.load(f)
            control_flow = seq_data.get(
                'extracted_output', {}).get('control_flow', [])
            print(f"Loaded control flow from: {seq_file_path}")
            print(f"Number of control flows: {len(control_flow)}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Failed to load control flow from {seq_file_path}: {e}")
        return None

    if not control_flow:
        print("No control flow data found!")
        return None

    print("\nControl flow data:")
    print(json.dumps(control_flow, ensure_ascii=False, indent=2))

    # Test the extract_pairs_from_control_flow function
    pairs = extract_pairs_from_control_flow(control_flow)

    print("\nExtracted pairs:")
    print(json.dumps(pairs, ensure_ascii=False, indent=2))

    # Save the extracted pairs to a file for reference
    pairs_file = os.path.join(workplace, "extracted_pairs_output.json")
    with open(pairs_file, 'w', encoding='utf-8') as f:
        json.dump({
            "control_flow": control_flow,
            "extracted_pairs": pairs
        }, f, ensure_ascii=False, indent=2)

    print(f"\nExtracted pairs saved to: {pairs_file}")

    return pairs


def test_update_seq_with_gate():
    """
    Test function to verify update_seq_with_gate function using real data from files.
    """
    workplace = get_workplace()

    # Read control flow from seq_output.json
    seq_file_path = os.path.join(workplace, SEQ_OUTPUT_FILE)
    try:
        with open(seq_file_path, 'r', encoding='utf-8') as f:
            seq_data = json.load(f)
            control_flow = seq_data.get(
                'extracted_output', {}).get('control_flow', [])
            print(f"Loaded control flow from: {seq_file_path}")
            print(f"Number of control flows: {len(control_flow)}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Failed to load control flow from {seq_file_path}: {e}")
        return None

    # Read gateways from gate_output.json
    gate_file_path = os.path.join(workplace, GATE_OUTPUT_FILE)
    try:
        with open(gate_file_path, 'r', encoding='utf-8') as f:
            gate_data = json.load(f)
            gateways = gate_data.get(
                'extracted_output', {}).get('gateways', [])
            print(f"Loaded gateways from: {gate_file_path}")
            print(f"Number of gateways: {len(gateways)}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Failed to load gateways from {gate_file_path}: {e}")
        return None

    if not control_flow:
        print("No control flow data found!")
        return None

    if not gateways:
        print("No gateway data found!")
        return None

    print("\nOriginal control flow:")
    print(json.dumps(control_flow, ensure_ascii=False, indent=2))

    print("\nGateways:")
    print(json.dumps(gateways, ensure_ascii=False, indent=2))

    # Test the function
    print("\nTesting update_seq_with_gate function...")
    updated_flow = update_seq_with_gate(control_flow, gateways)

    print("\nUpdated control flow:")
    print(json.dumps(updated_flow, ensure_ascii=False, indent=2))

    # Save the updated flow to a new file for comparison
    updated_flow_file = os.path.join(workplace, "updated_flow_output.json")
    with open(updated_flow_file, 'w', encoding='utf-8') as f:
        json.dump({
            "original_control_flow": control_flow,
            "gateways": gateways,
            "updated_control_flow": updated_flow
        }, f, ensure_ascii=False, indent=2)

    print(f"\nUpdated flow saved to: {updated_flow_file}")

    return updated_flow


if __name__ == '__main__':
    try:
        print("Starting sequence generation...")
        sequence_result = generate_sequence()
        print("Sequence generation successful!")
        print(sequence_result)

        print("\nStarting gate generation...")
        gate_result = generate_gate()
        print("Gate generation successful!")
        print(gate_result)

        # Test extract_pairs_from_control_flow function
        print("\n" + "="*50)
        print("Testing extract_pairs_from_control_flow function...")
        print("="*50)
        test_extract_pairs()

        # Test update_seq_with_gate function
        print("\n" + "="*50)
        print("Testing update_seq_with_gate function...")
        print("="*50)
        test_update_seq_with_gate()

        # Test the new generate_updated_flow function
        print("\n" + "="*50)
        print("Testing generate_updated_flow function...")
        print("="*50)
        updated_flow_result = generate_updated_flow()
        if updated_flow_result:
            print("\nUpdated flow result summary:")
            print(
                f"- Original control flows: {len(updated_flow_result['original_control_flow'])}")
            print(f"- Gateways: {len(updated_flow_result['gateways'])}")
            print(
                f"- Updated control flows: {len(updated_flow_result['updated_control_flow'])}")

            # Show some examples of the updated flows
            print("\nSample updated flows:")
            for i, flow in enumerate(updated_flow_result['updated_control_flow'][:5]):
                print(
                    f"  {i+1}. {flow['from']} -> {flow['to']} (actor: {flow['actor']})")
            if len(updated_flow_result['updated_control_flow']) > 5:
                print(
                    f"  ... and {len(updated_flow_result['updated_control_flow']) - 5} more flows")
        else:
            print("Failed to generate updated flow!")

    except (FileNotFoundError, ValueError, json.JSONDecodeError, KeyError) as e:
        print(f"Generation failed: {e}")
