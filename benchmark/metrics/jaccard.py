"""
Generate Jaccard similarity-based BPMN comparison.

This module compares two BPMN 2.0 models after unification step (using unification.py)
and outputs a percentage value. Jaccard similarity is mainly based on sequences,
including sequence flows and message flows.
"""

import xml.etree.ElementTree as ET
import json
import os
from typing import Dict, List, Set, Tuple, Optional,Union
from utils.configure import get_workplace


# Output file configuration
JACCARD_OUTPUT_FILE = "jaccard_similarity.json"


def extract_sequence_flows(bpmn_xml_content: str) -> Set[str]:
    """
    Extract sequence flows from BPMN 2.0 XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        Set of sequence flow identifiers
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        sequence_flows = set()

        # Extract sequence flows
        for flow in root.findall('.//bpmn:sequenceFlow', bpmn_ns):
            flow_id = flow.get('id', '')
            source_ref = flow.get('sourceRef', '')
            target_ref = flow.get('targetRef', '')

            if flow_id and source_ref and target_ref:
                # Create flow identifier: source->target
                flow_identifier = f"{source_ref}->{target_ref}"
                sequence_flows.add(flow_identifier)

        return sequence_flows

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML for sequence flows: {e}")
        return set()


def extract_message_flows(bpmn_xml_content: str) -> Set[str]:
    """
    Extract message flows from BPMN 2.0 XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        Set of message flow identifiers
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        message_flows = set()

        # Extract message flows
        for flow in root.findall('.//bpmn:messageFlow', bpmn_ns):
            flow_id = flow.get('id', '')
            source_ref = flow.get('sourceRef', '')
            target_ref = flow.get('targetRef', '')

            if flow_id and source_ref and target_ref:
                # Create flow identifier: source->target
                flow_identifier = f"{source_ref}->{target_ref}"
                message_flows.add(flow_identifier)

        return message_flows

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML for message flows: {e}")
        return set()


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


def extract_all_flows(bpmn_xml_content: str) -> Dict[str, Set[str]]:
    """
    Extract all flow types from BPMN 2.0 XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        Dictionary containing sequence_flows and message_flows sets
    """
    sequence_flows = extract_sequence_flows(bpmn_xml_content)
    message_flows = extract_message_flows(bpmn_xml_content)

    return {
        'sequence_flows': sequence_flows,
        'message_flows': message_flows,
        'all_flows': sequence_flows.union(message_flows)
    }


def get_bpmn_type(bpmn_xml_content: str) -> str:
    """
    Get BPMN type from XML content.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        'collaboration' if collaboration diagram, 'process' if process diagram
    """
    return detect_bpmn_type(bpmn_xml_content)


def calculate_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Calculate Jaccard similarity between two sets.

    Args:
        set1: First set of elements
        set2: Second set of elements

    Returns:
        Jaccard similarity value between 0 and 1
    """
    if not set1 and not set2:
        return 1.0  # Both empty sets are considered identical

    intersection = set1.intersection(set2)
    union = set1.union(set2)

    if not union:
        return 0.0

    return len(intersection) / len(union)


def calculate_bpmn_jaccard_similarity(benchmark_bpmn_xml: str, target_bpmn_xml: str) -> Dict[str, Union[float,str ,list]]:
    """
    Calculate Jaccard similarity between two BPMN models.

    Args:
        benchmark_bpmn_xml: Benchmark BPMN 2.0 XML string
        target_bpmn_xml: Target BPMN 2.0 XML string

    Returns:
        Dictionary containing similarity scores for different flow types
    """
    print("Calculating BPMN Jaccard similarity...")

    # Extract flows from both models
    benchmark_flows = extract_all_flows(benchmark_bpmn_xml)
    target_flows = extract_all_flows(target_bpmn_xml)

    # Get BPMN types
    benchmark_type = get_bpmn_type(benchmark_bpmn_xml)
    target_type = get_bpmn_type(target_bpmn_xml)

    print(f"Benchmark model ({benchmark_type}): {len(benchmark_flows['sequence_flows'])} sequence flows, "
          f"{len(benchmark_flows['message_flows'])} message flows")
    print(f"Target model ({target_type}): {len(target_flows['sequence_flows'])} sequence flows, "
          f"{len(target_flows['message_flows'])} message flows")

    # Calculate similarities
    sequence_similarity = calculate_jaccard_similarity(
        benchmark_flows['sequence_flows'],
        target_flows['sequence_flows']
    )

    message_similarity = calculate_jaccard_similarity(
        benchmark_flows['message_flows'],
        target_flows['message_flows']
    )

    overall_similarity = calculate_jaccard_similarity(
        benchmark_flows['all_flows'],
        target_flows['all_flows']
    )

    # Calculate weighted similarity (sequence flows typically more important)
    weighted_similarity = (sequence_similarity * 0.7) + \
        (message_similarity * 0.3)

    result = {
        'sequence_flow_similarity': sequence_similarity,
        'message_flow_similarity': message_similarity,
        'overall_similarity': overall_similarity,
        'weighted_similarity': weighted_similarity,
        'sequence_flow_similarity_percentage': round(sequence_similarity * 100, 2),
        'message_flow_similarity_percentage': round(message_similarity * 100, 2),
        'overall_similarity_percentage': round(overall_similarity * 100, 2),
        'weighted_similarity_percentage': round(weighted_similarity * 100, 2),
        'benchmark_sequence_flows': list(benchmark_flows['sequence_flows']),
        'benchmark_message_flows': list(benchmark_flows['message_flows']),
        'target_sequence_flows': list(target_flows['sequence_flows']),
        'target_message_flows': list(target_flows['message_flows']),
        'benchmark_bpmn_type': benchmark_type,
        'target_bpmn_type': target_type
    }

    print(f"Jaccard similarity calculation completed:")
    print(
        f"  Sequence flow similarity: {result['sequence_flow_similarity_percentage']}%")
    print(
        f"  Message flow similarity: {result['message_flow_similarity_percentage']}%")
    print(f"  Overall similarity: {result['overall_similarity_percentage']}%")
    print(
        f"  Weighted similarity: {result['weighted_similarity_percentage']}%")

    return result


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


def save_jaccard_result(result: Dict[str, Union[float,str ,list]], output_file: Optional[str] = None):
    """
    Save Jaccard similarity result to file.

    Args:
        result: Jaccard similarity result dictionary
        output_file: Output file path (optional)
    """
    if output_file is None:
        workplace = get_workplace()
        output_file = os.path.join(workplace, JACCARD_OUTPUT_FILE)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Jaccard similarity result saved: {output_file}")
    except Exception as e:
        print(f"Failed to save Jaccard similarity result: {e}")


def compare_bpmn_models(benchmark_bpmn_file: Optional[str] = None, target_bpmn_file: Optional[str] = None,
                        benchmark_bpmn_xml: Optional[str] = None, target_bpmn_xml: Optional[str] = None) -> Optional[Dict[str, Union[float,str ,list]]]:
    """
    Compare two BPMN models using Jaccard similarity.

    Args:
        benchmark_bpmn_file: Benchmark BPMN file path
        target_bpmn_file: Target BPMN file path
        benchmark_bpmn_xml: Benchmark BPMN XML content (if already loaded)
        target_bpmn_xml: Target BPMN XML content (if already loaded)

    Returns:
        Jaccard similarity result dictionary
    """
    # Load benchmark BPMN
    if benchmark_bpmn_xml is None:
        if benchmark_bpmn_file is None:
            workplace = get_workplace()
            benchmark_bpmn_file = os.path.join(
                workplace, "benchmark_bpmn.bpmn")

        benchmark_bpmn_xml = load_bpmn_from_file(benchmark_bpmn_file)
        if not benchmark_bpmn_xml:
            return None

    # Load target BPMN
    if target_bpmn_xml is None:
        if target_bpmn_file is None:
            workplace = get_workplace()
            target_bpmn_file = os.path.join(workplace, "unified_bpmn.bpmn")

        target_bpmn_xml = load_bpmn_from_file(target_bpmn_file)
        if not target_bpmn_xml:
            return None

    # Calculate similarity
    result = calculate_bpmn_jaccard_similarity(
        benchmark_bpmn_xml, target_bpmn_xml)

    # Save result
    save_jaccard_result(result)

    return result


if __name__ == '__main__':
    try:
        print("Starting BPMN Jaccard similarity calculation...")

        # Compare BPMN models
        result = compare_bpmn_models()

        if result:
            print("\n=== Jaccard Similarity Results ===")
            print(f"Benchmark BPMN Type: {result['benchmark_bpmn_type']}")
            print(f"Target BPMN Type: {result['target_bpmn_type']}")
            print(
                f"Sequence Flow Similarity: {result['sequence_flow_similarity_percentage']}%")
            print(
                f"Message Flow Similarity: {result['message_flow_similarity_percentage']}%")
            print(
                f"Overall Similarity: {result['overall_similarity_percentage']}%")
            print(
                f"Weighted Similarity: {result['weighted_similarity_percentage']}%")
            print(f"Results saved to: {get_workplace()}/{JACCARD_OUTPUT_FILE}")
        else:
            print("Jaccard similarity calculation failed")

    except Exception as e:
        print(f"Jaccard similarity calculation failed: {e}")
