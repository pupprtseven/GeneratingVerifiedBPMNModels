"""
Generate CTL constraints from requirements.

This module generates CTL (Computational Tree Logic) constraints from business requirements
and existing symbol and flow data for formal verification.
"""

import json
import os
import xml.etree.ElementTree as ET
from utils.agent import generate_prompt_from_config
from utils.configure import get_workplace
from utils.load_requirement import get_reqstring
from utils.dump import get_data_from_file_or_generate, save_result
from generation.symbol import get_symbol_data
from generation.seq import generate_sequence


# Configuration paths loaded from configure.yml
from utils.configure import get_verification_config_path, get_output_file_name

CTL_CONFIG_PATH = get_verification_config_path(
    "CTL_CONFIG_PATH") or "verification/config/ctl.json"
CTL_OUTPUT_FILE = get_output_file_name("CTL_OUTPUT_FILE") or "ctl_output.json"
SYMBOL_OUTPUT_FILE = get_output_file_name(
    "SYMBOL_OUTPUT_FILE") or "symbol_output.json"
SEQ_OUTPUT_FILE = get_output_file_name("SEQ_OUTPUT_FILE") or "seq_output.json"
STANDARD_CTL_CONSTRAINTS_FILE = get_output_file_name(
    "STANDARD_CTL_CONSTRAINTS_FILE") or "standard_ctl_constraints.json"
DEFAULT_PETRI_NET_FILE = get_verification_config_path(
    "DEFAULT_PETRI_NET_FILE") or "bpmn_output_petri_net.pnml"
ENABLE_DUMP = True


def get_ctl_data():
    """
    Get CTL data either from file or by generating.

    Returns:
        Dictionary containing CTL constraints data
    """
    return get_data_from_file_or_generate(CTL_OUTPUT_FILE, generate_ctl, "CTL data")


def get_symbol_data_for_ctl():
    """
    Get symbol data for CTL generation.

    Returns:
        Dictionary containing symbol data
    """
    if ENABLE_DUMP:
        # Read from existing file
        workplace = get_workplace()
        symbol_file_path = os.path.join(workplace, SYMBOL_OUTPUT_FILE)

        try:
            with open(symbol_file_path, 'r', encoding='utf-8') as f:
                symbol_data = json.load(f)
                print(f"Loaded symbol data from: {symbol_file_path}")
                return symbol_data.get('extracted_output', symbol_data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Failed to load symbol data from file: {e}")
            return {}
    else:
        # Generate new symbol data
        return get_symbol_data()


def get_flow_data_for_ctl():
    """
    Get flow data for CTL generation.

    Returns:
        Dictionary containing flow data
    """
    if ENABLE_DUMP:
        # Read from existing file
        workplace = get_workplace()
        seq_file_path = os.path.join(workplace, SEQ_OUTPUT_FILE)

        try:
            with open(seq_file_path, 'r', encoding='utf-8') as f:
                seq_data = json.load(f)
                print(f"Loaded flow data from: {seq_file_path}")
                return seq_data.get('extracted_output', seq_data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Failed to load flow data from file: {e}")
            return {}
    else:
        # Generate new flow data
        return generate_sequence()


def validate_and_format_ctl_constraints(ctl_constraints, symbol_data):
    """
    Validate and format CTL constraints according to standard format.

    Args:
        ctl_constraints: List of CTL constraints from LLM
        symbol_data: Symbol data for validation

    Returns:
        List of validated and formatted CTL constraints
    """
    if not isinstance(ctl_constraints, list):
        print("Warning: ctl_constraints is not a list, converting...")
        ctl_constraints = [ctl_constraints] if ctl_constraints else []

    # Extract valid symbols from symbol data
    valid_symbols = set()
    if 'tasks' in symbol_data:
        for task in symbol_data['tasks']:
            if 'task_symbol' in task:
                valid_symbols.add(task['task_symbol'])

    # Standard CTL operators
    ctl_operators = {'AG', 'AF', 'EF', 'EG', 'AU', 'EU', 'AX', 'EX'}

    # Valid constraint types
    valid_constraint_types = {
        'safety_properties', 'liveness_properties',
        'response_properties', 'precedence_properties'
    }

    formatted_constraints = []

    for i, constraint in enumerate(ctl_constraints):
        if not isinstance(constraint, dict):
            print(f"Warning: Constraint {i} is not a dictionary, skipping...")
            continue

        # Ensure all required fields are present
        constraint_id = constraint.get('constraint_id', f'C{i+1:03d}')
        ctl_formula = constraint.get('ctl_formula', '')
        description = constraint.get('description', '')
        requirement_reference = constraint.get('requirement_reference', '')
        constraint_type = constraint.get(
            'constraint_type', 'safety_properties')

        # Validate constraint type
        if constraint_type not in valid_constraint_types:
            print(
                f"Warning: Invalid constraint type '{constraint_type}' for {constraint_id}, using 'safety_properties'")
            constraint_type = 'safety_properties'

        # Validate CTL formula syntax (basic validation)
        if ctl_formula:
            # Check for basic CTL syntax
            formula_valid = True
            # Add more sophisticated validation here if needed

            if formula_valid:
                formatted_constraint = {
                    'constraint_id': constraint_id,
                    'ctl_formula': ctl_formula.strip(),
                    'description': description.strip(),
                    'requirement_reference': requirement_reference.strip(),
                    'constraint_type': constraint_type
                }
                formatted_constraints.append(formatted_constraint)
            else:
                print(
                    f"Warning: Invalid CTL formula in constraint {constraint_id}: {ctl_formula}")
        else:
            print(f"Warning: Empty CTL formula in constraint {constraint_id}")

    print(
        f"Validated and formatted {len(formatted_constraints)} CTL constraints")
    return formatted_constraints


def generate_ctl():
    """
    Generate CTL constraints from requirements, symbol table, and flow data.

    Returns:
        Dictionary containing extracted CTL constraints
    """
    # Get requirement string
    requirement = get_reqstring()

    # Get symbol data
    symbol_result = get_symbol_data_for_ctl()

    # Get flow data
    flow_result = get_flow_data_for_ctl()

    # Prepare input variables
    input_vars = {
        "REQUIREMENT": requirement,
        "SYMBOL": json.dumps(symbol_result, ensure_ascii=False, indent=2),
        "FLOW": json.dumps(flow_result, ensure_ascii=False, indent=2)
    }

    # Generate CTL output using agent
    result = generate_prompt_from_config(CTL_CONFIG_PATH, input_vars)

    # Extract the output and validate format
    extracted_output = result.get('extracted_output', {})

    # Validate and format CTL constraints
    if 'ctl_constraints' in extracted_output:
        extracted_output['ctl_constraints'] = validate_and_format_ctl_constraints(
            extracted_output['ctl_constraints'], symbol_result
        )

    # Save results
    save_result(result, CTL_OUTPUT_FILE, "CTL generation")

    print("Extracted output:")
    print(json.dumps(extracted_output, ensure_ascii=False, indent=2))

    return extracted_output


def generate_ctl_with_dependencies():
    """
    Generate CTL constraints with proper dependency handling.

    This function ensures that all required data (symbols and flows) are available
    before generating CTL constraints.

    Returns:
        Dictionary containing CTL constraints
    """
    print("Starting CTL generation with dependencies...")

    # Ensure symbol data is available
    print("Checking symbol data...")
    symbol_data = get_symbol_data_for_ctl()
    if not symbol_data:
        print("Warning: No symbol data available")

    # Ensure flow data is available
    print("Checking flow data...")
    flow_data = get_flow_data_for_ctl()
    if not flow_data:
        print("Warning: No flow data available")

    # Generate CTL constraints
    print("Generating CTL constraints...")
    ctl_result = generate_ctl()

    print("CTL generation completed!")
    return ctl_result


def transform_ctl_on_pt(petri_net_path=None):
    """
    Transform CTL constraints to work with Petri net places.

    This function implements the BPMN symbol to Petri net place mapping algorithm.
    It maps BPMN symbols to Petri net places and generates variable substitution expressions.

        This function is designed to work with the output of bpmn_to_pt.py, which generates
    a PNML file with standard Petri net markup language format.

    Args:
        petri_net_path: Path to the Petri net PNML file (output of bpmn_to_pt.py). 
                       If None, uses default path: workplace/bpmn_output_petri_net.pnml

    Returns:
        Dictionary containing variable substitution expressions E = {(s_k, e_k)}
    """
    # Initialize substitution expressions set
    E = {}

    # Load Petri net data
    if petri_net_path is None:
        workplace = get_workplace()
        petri_net_path = os.path.join(workplace, DEFAULT_PETRI_NET_FILE)

    # Load Petri net structure (assuming it's in a structured format)
    petri_net_data = load_petri_net(petri_net_path)

    # Get BPMN symbols from symbol data
    symbol_data = get_symbol_data_for_ctl()
    bpmn_symbols = extract_bpmn_symbols(symbol_data)

    # For each BPMN symbol s_k
    for s_k in bpmn_symbols:
        # Map BPMN symbol to transition: t_k = M(s_k)
        t_k = map_symbol_to_transition(s_k, petri_net_data)

        if t_k is None:
            print(f"Warning: Could not map symbol {s_k} to transition")
            continue

        # Get post-places of transition: P = Post(t_k)
        P = get_post_places(t_k, petri_net_data)

        # Generate substitution expression
        if len(P) == 1:
            # If only one post-place: e_k = p_1
            e_k = P[0]
        else:
            # If multiple post-places: e_k = AND(p_1, p_2, ..., p_n)
            e_k = f"({' AND '.join(P)})"

        # Add to substitution set: E = E ∪ {(s_k, e_k)}
        E[s_k] = e_k

    return E


def load_petri_net(petri_net_path):
    """
    Load Petri net data from PNML file (output of bpmn_to_pt.py).

    Args:
        petri_net_path: Path to the Petri net PNML file

    Returns:
        Dictionary containing Petri net structure compatible with bpmn_to_pt.py output
    """
    try:
        # Parse PNML XML file
        tree = ET.parse(petri_net_path)
        root = tree.getroot()

        # Define PNML namespace from configuration
        from utils.configure import get_petri_net_config
        pnml_namespace = get_petri_net_config('PNML_NAMESPACE')
        if pnml_namespace is None:
            pnml_namespace = 'http://www.pnml.org/version-2009/grammar/pnmlcoremodel'
        pnml_ns: dict[str, str] = {'pnml': str(pnml_namespace)}

        converted_data = {
            'transitions': {},
            'places': {},
            'arcs': {}
        }

        # Find the net element
        net = root.find('.//pnml:net', pnml_ns)
        if net is None:
            net = root.find('.//net')  # Fallback without namespace

        if net is not None:
            # Find the page element
            page = net.find('.//pnml:page', pnml_ns)
            if page is None:
                page = net.find('.//page')  # Fallback without namespace

            if page is not None:
                # Parse places
                for place in page.findall('.//pnml:place', pnml_ns) or page.findall('.//place'):
                    place_id = place.get('id')
                    if place_id:
                        converted_data['places'][place_id] = {
                            'id': place_id, 'name': place_id}

                # Parse transitions
                for transition in page.findall('.//pnml:transition', pnml_ns) or page.findall('.//transition'):
                    transition_id = transition.get('id')
                    if transition_id:
                        converted_data['transitions'][transition_id] = {
                            'id': transition_id, 'name': transition_id}

                # Parse arcs
                for i, arc in enumerate(page.findall('.//pnml:arc', pnml_ns) or page.findall('.//arc')):
                    arc_id = arc.get('id', f"arc_{i}")
                    source = arc.get('source')
                    target = arc.get('target')
                    if source and target:
                        converted_data['arcs'][arc_id] = {
                            'id': arc_id,
                            'source': source,
                            'target': target
                        }

        return converted_data

    except FileNotFoundError:
        print(f"Petri net file not found: {petri_net_path}")
        return {}
    except ET.ParseError as e:
        print(f"Error parsing PNML file: {e}")
        return {}


def extract_bpmn_symbols(symbol_data):
    """
    Extract BPMN symbols from symbol data.

    Args:
        symbol_data: Symbol data from generation module

    Returns:
        List of BPMN symbols
    """
    symbols = []
    if 'tasks' in symbol_data:
        for task in symbol_data['tasks']:
            if 'task_symbol' in task:
                symbols.append(task['task_symbol'])
    return symbols


def map_symbol_to_transition(symbol, petri_net_data):
    """
    Map BPMN symbol to Petri net transition.

    Args:
        symbol: BPMN symbol
        petri_net_data: Petri net structure

    Returns:
        Transition ID or None if not found
    """
    transitions = petri_net_data.get('transitions', {})

    # Get naming convention from configuration
    from utils.configure import get_naming_convention
    transition_prefix = get_naming_convention('TRANSITION_PREFIX') or 't_'

    # bpmn_to_pt.py uses naming convention: t_{task_id}
    # For example: T1 -> t_T1, T2 -> t_T2
    expected_transition_id = f"{transition_prefix}{symbol}"

    # Try to find transition by the expected naming convention
    if expected_transition_id in transitions:
        return expected_transition_id

    # Fallback: try to find by symbol name in transition data
    for t_id, t_data in transitions.items():
        if t_data.get('name') == symbol:
            return t_id

    return None


def get_post_places(transition_id, petri_net_data):
    """
    Get post-places of a transition.

    Args:
        transition_id: ID of the transition
        petri_net_data: Petri net structure

    Returns:
        List of post-place IDs
    """
    arcs = petri_net_data.get('arcs', {})
    post_places = []

    # Get naming convention from configuration
    from utils.configure import get_naming_convention
    place_prefix = get_naming_convention('PLACE_PREFIX') or 'p_'

    # Find all arcs from this transition to places
    # bpmn_to_pt.py creates arcs with 'source' and 'target' fields
    for arc_id, arc_data in arcs.items():
        if arc_data.get('source') == transition_id:
            target = arc_data.get('target')
            # Only include if target is a place (not another transition)
            if target and target.startswith(place_prefix):
                post_places.append(target)

    return post_places


def apply_ctl_transformation(ctl_constraints, petri_net_path=None):
    """
    Apply CTL transformation to work with Petri net places.

    Args:
        ctl_constraints: Original CTL constraints (list of dictionaries)
        petri_net_path: Path to Petri net PNML file

    Returns:
        Transformed CTL constraints suitable for Petri net verification
    """
    # Get variable substitution expressions
    substitutions = transform_ctl_on_pt(petri_net_path)

    # Transform CTL constraints by replacing BPMN symbols with Petri net places
    transformed_constraints = []

    for constraint in ctl_constraints:
        if isinstance(constraint, dict):
            # Handle new standard format
            ctl_formula = constraint.get('ctl_formula', '')
            transformed_formula = ctl_formula

            for symbol, expression in substitutions.items():
                # Replace BPMN symbols with Petri net place expressions
                transformed_formula = transformed_formula.replace(
                    symbol, expression)

            transformed_constraints.append(transformed_formula)
        else:
            # Handle legacy string format
            transformed_constraint = str(constraint)
            for symbol, expression in substitutions.items():
                transformed_constraint = transformed_constraint.replace(
                    symbol, expression)
            transformed_constraints.append(transformed_constraint)

    return transformed_constraints


def save_standard_ctl_constraints(constraints_list, output_file=None):
    """
    Save CTL constraints in standard format to file.

    Args:
        constraints_list: List of CTL constraints in standard format
        output_file: Output file path (optional, uses default if None)
    """
    import datetime

    if output_file is None:
        workplace = get_workplace()
        output_file = os.path.join(workplace, STANDARD_CTL_CONSTRAINTS_FILE)

    standard_output = {
        "metadata": {
            "format_version": "1.0",
            "generation_timestamp": str(datetime.datetime.now()),
            "constraint_count": len(constraints_list),
            "format": "standard_ctl"
        },
        "ctl_constraints": constraints_list
    }

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(standard_output, f, ensure_ascii=False, indent=2)
        print(f"Standard CTL constraints saved to: {output_file}")
    except Exception as e:
        print(f"Error saving standard CTL constraints: {e}")


if __name__ == '__main__':
    try:
        print("Starting CTL generation...")
        result = generate_ctl_with_dependencies()
        print("CTL generation successful!")
        print(result)

        # Example of CTL transformation for Petri net verification
        print("\n" + "="*50)
        print("Example: CTL transformation for Petri net verification")
        print("="*50)

        # Get CTL constraints
        ctl_data = result.get('extracted_output', {})
        ctl_constraints = ctl_data.get('ctl_constraints', [])

        if ctl_constraints:
            print("Original CTL constraints:")
            for i, constraint in enumerate(ctl_constraints):
                constraint_id = constraint.get('constraint_id', f'C{i+1}')
                ctl_formula = constraint.get('ctl_formula', 'N/A')
                description = constraint.get('description', '')
                constraint_type = constraint.get('constraint_type', 'unknown')
                print(
                    f"  {i+1}. [{constraint_id}] {constraint_type}: {ctl_formula}")
                if description:
                    print(f"     Description: {description}")

            # Save standard format CTL constraints
            save_standard_ctl_constraints(ctl_constraints)

            # Transform CTL constraints for Petri net verification
            # Uses the same output file as bpmn_to_pt.py
            workplace = get_workplace()
            petri_net_path = os.path.join(workplace, DEFAULT_PETRI_NET_FILE)

            print(f"\nLooking for Petri net file: {petri_net_path}")
            if os.path.exists(petri_net_path):
                transformed_constraints = apply_ctl_transformation(
                    ctl_constraints, petri_net_path)

                print("\nTransformed CTL constraints for Petri net verification:")
                for i, constraint in enumerate(transformed_constraints):
                    print(f"  {i+1}. {constraint}")
            else:
                print(
                    f"Petri net file not found. Please run bpmn_to_pt.py first to generate: {petri_net_path}")
        else:
            print("No CTL constraints found in the result.")

    except (FileNotFoundError, ValueError, json.JSONDecodeError, KeyError) as e:
        print(f"CTL generation failed: {e}")
