"""
Unify symbol mappings between benchmark and target BPMN models.

This module analyzes two symbol maps (benchmark and target) and identifies
corresponding pairs between them for actors and tasks using semantic similarity.
"""

from copy import deepcopy
import xml.etree.ElementTree as ET
import json
import os
from utils.agent import generate_prompt_from_config
from utils.configure import get_workplace
from utils.dump import get_data_from_file_or_generate, save_result


# Configuration paths loaded from configure.yml
from utils.configure import get_verification_config_path, get_output_file_name

UNIFICATION_CONFIG_PATH = get_verification_config_path(
    "UNIFICATION_CONFIG_PATH") or "benchmark/config/unification.json"
UNIFICATION_OUTPUT_FILE = get_output_file_name(
    "UNIFICATION_OUTPUT_FILE") or "unification_output.json"
BENCHMARK_SYMBOL_OUTPUT_FILE = get_output_file_name(
    "BENCHMARK_SYMBOL_OUTPUT_FILE") or "benchmark_symbol_output.json"
TARGET_SYMBOL_OUTPUT_FILE = get_output_file_name(
    "TARGET_SYMBOL_OUTPUT_FILE") or "target_symbol_output.json"


def validate_mapping_quality(extracted_output):
    """
    Validate the quality of mappings in the extracted output.

    Args:
        extracted_output: Dictionary containing actor_mappings, task_mappings, and reasoning

    Returns:
        Modified extracted_output with quality validation
    """
    if 'actor_mappings' in extracted_output and 'task_mappings' in extracted_output:
        actor_mappings = extracted_output['actor_mappings']
        task_mappings = extracted_output['task_mappings']

        # Validate confidence scores
        for mapping in actor_mappings:
            if isinstance(mapping, dict) and 'confidence' in mapping:
                confidence = mapping['confidence']
                if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                    # Default confidence if invalid
                    mapping['confidence'] = 0.5

        for mapping in task_mappings:
            if isinstance(mapping, dict) and 'confidence' in mapping:
                confidence = mapping['confidence']
                if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                    # Default confidence if invalid
                    mapping['confidence'] = 0.5

        # Add quality metrics
        high_confidence_actors = [
            m for m in actor_mappings if m.get('confidence', 0) >= 0.8]
        high_confidence_tasks = [
            m for m in task_mappings if m.get('confidence', 0) >= 0.8]

        extracted_output['quality_metrics'] = {
            'total_actor_mappings': len(actor_mappings),
            'high_confidence_actor_mappings': len(high_confidence_actors),
            'total_task_mappings': len(task_mappings),
            'high_confidence_task_mappings': len(high_confidence_tasks),
            'actor_mapping_quality': len(high_confidence_actors) / len(actor_mappings) if actor_mappings else 0,
            'task_mapping_quality': len(high_confidence_tasks) / len(task_mappings) if task_mappings else 0
        }

    return extracted_output


def get_unification_data():
    """
    Get unification data either from file or by generating.

    Returns:
        Dictionary containing unification data
    """
    return get_data_from_file_or_generate(UNIFICATION_OUTPUT_FILE, generate_unification, "unification data")


def generate_unification(bench_symbol_data=None, target_symbol_data=None):
    """
    Generate symbol mappings between benchmark and target models.

    Args:
        bench_symbol_data: Benchmark symbol data (optional, will be loaded if not provided)
        target_symbol_data: Target symbol data (optional, will be loaded if not provided)

    Returns:
        Dictionary containing actor_mappings, task_mappings, and reasoning
    """
    # Load symbol data if not provided
    if bench_symbol_data is None:
        workplace = get_workplace()
        bench_file_path = os.path.join(
            workplace, BENCHMARK_SYMBOL_OUTPUT_FILE)
        try:
            with open(bench_file_path, 'r', encoding='utf-8') as f:
                bench_symbol_data = json.load(f)
                print(f"Loaded benchmark symbol data from: {bench_file_path}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Failed to load benchmark symbol data: {e}")
            bench_symbol_data = {"actor": [], "tasks": []}

    if target_symbol_data is None:
        workplace = get_workplace()
        target_file_path = os.path.join(workplace, TARGET_SYMBOL_OUTPUT_FILE)
        try:
            with open(target_file_path, 'r', encoding='utf-8') as f:
                target_symbol_data = json.load(f)
                print(f"Loaded target symbol data from: {target_file_path}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Failed to load target symbol data: {e}")
            target_symbol_data = {"actor": [], "tasks": []}

    # Prepare input variables
    input_vars = {
        "BENCHSYMBOL": json.dumps(bench_symbol_data, ensure_ascii=False, indent=2),
        "TARGETSYMBOL": json.dumps(target_symbol_data, ensure_ascii=False, indent=2)
    }

    # Generate unification output using agent
    result = generate_prompt_from_config(UNIFICATION_CONFIG_PATH, input_vars)

    # Extract the output
    extracted_output = result.get('extracted_output', {})

    # Validate mapping quality
    extracted_output = validate_mapping_quality(extracted_output)

    # Save full results for debugging
    save_result(result, UNIFICATION_OUTPUT_FILE, "Unification generation")

    print("Extracted output:")
    print(json.dumps(extracted_output, ensure_ascii=False, indent=2))

    return extracted_output


def generate_unification_with_dependencies():
    """
    Generate unification mappings with proper dependency handling.

    Returns:
        Dictionary containing unification results
    """
    print("Generating unification mappings...")

    # This function can be extended to handle dependencies
    # For now, it just calls the main generation function
    result = generate_unification()

    return {
        'extracted_output': result,
        'status': 'success',
        'message': 'Unification mappings generated successfully'
    }


def extract_symbols_from_bpmn(bpmn_xml_content):
    """
    Extract symbol table from BPMN 2.0 XML

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        Dictionary containing actors and tasks extracted from BPMN
    """
    try:
        root = ET.fromstring(bpmn_xml_content)

        # BPMN 2.0 namespace
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        actors = []
        tasks = []

        # Extract participants (Lane, Participant)
        for lane in root.findall('.//bpmn:lane', bpmn_ns):
            lane_id = lane.get('id', '')
            lane_name = lane.get('name', '')
            if lane_id and lane_name:
                actors.append({
                    'id': lane_id,
                    'name': lane_name,
                    'type': 'lane'
                })

        for participant in root.findall('.//bpmn:participant', bpmn_ns):
            participant_id = participant.get('id', '')
            participant_name = participant.get('name', '')
            if participant_id and participant_name:
                actors.append({
                    'id': participant_id,
                    'name': participant_name,
                    'type': 'participant'
                })

        # Extract tasks (Task, UserTask, ServiceTask, etc.)
        task_types = [
            'task', 'userTask', 'serviceTask', 'scriptTask', 'businessRuleTask',
            'manualTask', 'sendTask', 'receiveTask', 'subProcess'
        ]

        for task_type in task_types:
            for task in root.findall(f'.//bpmn:{task_type}', bpmn_ns):
                task_id = task.get('id', '')
                task_name = task.get('name', '')
                if task_id and task_name:
                    tasks.append({
                        'id': task_id,
                        'desc': task_name,
                        'type': task_type
                    })

        return {
            'actor': actors,
            'tasks': tasks
        }

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML: {e}")
        return {'actor': [], 'tasks': []}


def apply_symbol_mappings_to_bpmn(bpmn_xml_content, actor_mappings, task_mappings):
    """
    Apply symbol mappings to BPMN 2.0 XML

    Args:
        bpmn_xml_content: Original BPMN 2.0 XML string
        actor_mappings: Actor mapping list [{'bench_symbol': 'A1', 'target_symbol': 'A2', 'confidence': 0.9}]
        task_mappings: Task mapping list [{'bench_symbol': 'T1', 'target_symbol': 'T2', 'confidence': 0.8}]

    Returns:
        Modified BPMN 2.0 XML string
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        # Create mapping dictionaries
        actor_map = {mapping['target_symbol']: mapping['bench_symbol']
                     for mapping in actor_mappings}
        task_map = {mapping['target_symbol']: mapping['bench_symbol']
                    for mapping in task_mappings}

        # Replace actor IDs
        for lane in root.findall('.//bpmn:lane', bpmn_ns):
            lane_id = lane.get('id', '')
            if lane_id in actor_map:
                lane.set('id', actor_map[lane_id])

        for participant in root.findall('.//bpmn:participant', bpmn_ns):
            participant_id = participant.get('id', '')
            if participant_id in actor_map:
                participant.set('id', actor_map[participant_id])

        # Replace task IDs
        task_types = [
            'task', 'userTask', 'serviceTask', 'scriptTask', 'businessRuleTask',
            'manualTask', 'sendTask', 'receiveTask', 'subProcess'
        ]

        for task_type in task_types:
            for task in root.findall(f'.//bpmn:{task_type}', bpmn_ns):
                task_id = task.get('id', '')
                if task_id in task_map:
                    task.set('id', task_map[task_id])

        # Replace flow references
        for flow in root.findall('.//bpmn:sequenceFlow', bpmn_ns):
            source_ref = flow.get('sourceRef', '')
            target_ref = flow.get('targetRef', '')

            if source_ref in task_map:
                flow.set('sourceRef', task_map[source_ref])
            if target_ref in task_map:
                flow.set('targetRef', task_map[target_ref])

        # Replace gateway references
        for gateway in root.findall('.//bpmn:gateway', bpmn_ns):
            gateway_id = gateway.get('id', '')
            if gateway_id in task_map:
                gateway.set('id', task_map[gateway_id])

        # Return modified XML
        return ET.tostring(root, encoding='unicode')

    except ET.ParseError as e:
        print(f"Error applying mappings to BPMN XML: {e}")
        return bpmn_xml_content


def unification_algorithm(bench_symbol_data, target_bpmn_xml):
    """
    BPMN symbol unification algorithm

    Args:
        bench_symbol_data: Benchmark symbol table S = (A=(id_a, name), T=(id_t, desc))
        target_bpmn_xml: Target BPMN diagram B (BPMN 2.0 XML string)

    Returns:
        Target BPMN model B' unified with benchmark BPMN symbols
    """
    print("Starting BPMN symbol unification algorithm...")

    # Initialize: B' = B
    unified_bpmn = deepcopy(target_bpmn_xml)

    # Extract S' from B = (A'=(id_a', name'), T=(id_t', desc'))
    target_symbol_data = extract_symbols_from_bpmn(target_bpmn_xml)
    print(
        f"Extracted {len(target_symbol_data['actor'])} actors, {len(target_symbol_data['tasks'])} tasks from target BPMN")

    # Use BenchSymbolPrompt to submit S and S' to LLM, return mappings
    # α = {(id_a, id_a')}, τ = {(id_t, id_t')}
    mapping_result = generate_unification(
        bench_symbol_data, target_symbol_data)

    actor_mappings = mapping_result.get('actor_mappings', [])
    task_mappings = mapping_result.get('task_mappings', [])

    print(
        f"LLM generated mappings: {len(actor_mappings)} actor mappings, {len(task_mappings)} task mappings")

    # For each (id_a, id_a') ∈ α, replace id_a with id_a' in B'
    # For each (id_t, id_t') ∈ τ, replace id_t with id_t' in B'
    unified_bpmn = apply_symbol_mappings_to_bpmn(
        unified_bpmn, actor_mappings, task_mappings)

    print("BPMN symbol unification completed")

    return {
        'unified_bpmn_xml': unified_bpmn,
        'mapping_result': mapping_result,
        'target_symbol_data': target_symbol_data
    }


def unify_bpmn_models(bench_symbol_file=None, target_bpmn_file=None, bench_symbol_data=None, target_bpmn_xml=None):
    """
    Main function for unifying BPMN models

    Args:
        bench_symbol_file: Benchmark symbol file path
        target_bpmn_file: Target BPMN file path
        bench_symbol_data: Benchmark symbol data (if already loaded)
        target_bpmn_xml: Target BPMN XML content (if already loaded)

    Returns:
        Unification result
    """
    # Load benchmark symbol data
    if bench_symbol_data is None:
        if bench_symbol_file is None:
            workplace = get_workplace()
            bench_symbol_file = os.path.join(
                workplace, BENCHMARK_SYMBOL_OUTPUT_FILE)

        try:
            with open(bench_symbol_file, 'r', encoding='utf-8') as f:
                bench_symbol_data = json.load(f)
                print(f"Loaded benchmark symbol data: {bench_symbol_file}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Failed to load benchmark symbol data: {e}")
            return None

    # Load target BPMN data
    if target_bpmn_xml is None:
        if target_bpmn_file is None:
            workplace = get_workplace()
            target_bpmn_file = os.path.join(workplace, "target_bpmn.bpmn")

        try:
            with open(target_bpmn_file, 'r', encoding='utf-8') as f:
                target_bpmn_xml = f.read()
                print(f"Loaded target BPMN file: {target_bpmn_file}")
        except FileNotFoundError as e:
            print(f"Failed to load target BPMN file: {e}")
            return None

    # Execute unification algorithm
    result = unification_algorithm(bench_symbol_data, target_bpmn_xml)

    # Save results
    workplace = get_workplace()
    unified_bpmn_file = os.path.join(workplace, "unified_bpmn.bpmn")
    try:
        with open(unified_bpmn_file, 'w', encoding='utf-8') as f:
            f.write(result['unified_bpmn_xml'])
        print(f"Unified BPMN saved: {unified_bpmn_file}")
    except Exception as e:
        print(f"Failed to save unified BPMN: {e}")

    return result


if __name__ == '__main__':
    try:
        print("Starting BPMN unification process...")

        # Example: Using unification algorithm
        # 1. Generate mappings only (no BPMN file processing)
        print("\n=== Generate Symbol Mappings ===")
        mapping_result = generate_unification_with_dependencies()
        print("Mapping generation successful!")

        # 2. Complete BPMN unification (if BPMN file exists)
        print("\n=== BPMN Unification ===")
        try:
            unification_result = unify_bpmn_models()
            if unification_result:
                print("BPMN unification successful!")
                print(
                    f"Unified BPMN saved to: {get_workplace()}/unified_bpmn.bpmn")
            else:
                print("BPMN unification skipped (no BPMN file found)")
        except Exception as e:
            print(f"BPMN unification failed: {e}")

    except (FileNotFoundError, ValueError, json.JSONDecodeError, KeyError) as e:
        print(f"Unification process failed: {e}")
