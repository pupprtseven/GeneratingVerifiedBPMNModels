"""
Generate SSDT (Shortest Successor Distance Matrix) similarity-based BPMN comparison.

This module compares two BPMN 2.0 models (non-collaboration diagrams only) using SSDT matrix
and outputs a percentage value. SSDT measures the shortest distance between activity nodes.
"""

import xml.etree.ElementTree as ET
import json
import os
from typing import Dict, List, Set, Tuple, Optional, Any,Union
from collections import defaultdict, deque
from utils.configure import get_workplace


# Output file configuration
SSDT_OUTPUT_FILE = "ssdt_similarity.json"


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


def extract_activity_nodes(bpmn_xml_content: str) -> Dict[str, str]:
    """
    Extract activity nodes from BPMN 2.0 XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        Dictionary mapping node ID to node name
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        activities = {}

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
                    activities[activity_id] = activity_name or activity_id

        return activities

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML for activities: {e}")
        return {}


def extract_gateways(bpmn_xml_content: str) -> Dict[str, str]:
    """
    Extract gateway nodes from BPMN 2.0 XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        Dictionary mapping gateway ID to gateway type
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        gateways = {}

        # Extract all gateway types
        gateway_types = [
            'exclusiveGateway', 'inclusiveGateway', 'parallelGateway', 'eventBasedGateway'
        ]

        for gateway_type in gateway_types:
            for gateway in root.findall(f'.//bpmn:{gateway_type}', bpmn_ns):
                gateway_id = gateway.get('id', '')
                if gateway_id:
                    gateways[gateway_id] = gateway_type

        return gateways

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML for gateways: {e}")
        return {}


def extract_sequence_flows(bpmn_xml_content: str) -> List[Tuple[str, str]]:
    """
    Extract sequence flows from BPMN 2.0 XML.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        List of (source_id, target_id) tuples
    """
    try:
        root = ET.fromstring(bpmn_xml_content)
        bpmn_ns = {'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}

        flows = []

        # Extract sequence flows
        for flow in root.findall('.//bpmn:sequenceFlow', bpmn_ns):
            source_ref = flow.get('sourceRef', '')
            target_ref = flow.get('targetRef', '')

            if source_ref and target_ref:
                flows.append((source_ref, target_ref))

        return flows

    except ET.ParseError as e:
        print(f"Error parsing BPMN XML for sequence flows: {e}")
        return []


def build_graph_with_gateways(activities: Dict[str, str], gateways: Dict[str, str], flows: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    """
    Build adjacency list representation of the BPMN graph with gateway awareness.

    Args:
        activities: Dictionary of activity nodes
        gateways: Dictionary of gateway nodes
        flows: List of sequence flows

    Returns:
        Adjacency list representation of the graph
    """
    graph = defaultdict(list)

    # Add all nodes to the graph
    all_nodes = set(activities.keys()) | set(gateways.keys())

    for node in all_nodes:
        graph[node] = []

    # Add edges from sequence flows
    for source, target in flows:
        if source in all_nodes and target in all_nodes:
            graph[source].append(target)

    return dict(graph)


def build_graph(activities: Dict[str, str], gateways: Dict[str, str], flows: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    """
    Build adjacency list representation of the BPMN graph.

    Args:
        activities: Dictionary of activity nodes
        gateways: Dictionary of gateway nodes
        flows: List of sequence flows

    Returns:
        Adjacency list representation of the graph
    """
    return build_graph_with_gateways(activities, gateways, flows)


def calculate_shortest_paths(graph: Dict[str, List[str]], nodes: List[str]) -> Dict[str, Dict[str, int]]:
    """
    Calculate shortest paths between all pairs of nodes using BFS.

    Args:
        graph: Adjacency list representation of the graph
        nodes: List of node IDs

    Returns:
        Dictionary mapping (source, target) to shortest path length
    """
    shortest_paths = {}

    for source in nodes:
        shortest_paths[source] = {}

        # BFS to find shortest paths from source
        distances = {node: float('inf') for node in nodes}
        distances[source] = 0

        queue = deque([source])
        visited = {source}

        while queue:
            current = queue.popleft()

            for neighbor in graph.get(current, []):
                if neighbor in nodes and neighbor not in visited:
                    distances[neighbor] = distances[current] + 1
                    visited.add(neighbor)
                    queue.append(neighbor)

        # Store results
        for target in nodes:
            if distances[target] == float('inf'):
                shortest_paths[source][target] = float('inf')
            else:
                shortest_paths[source][target] = distances[target]

    return shortest_paths


def calculate_shortest_paths_with_gateways(graph: Dict[str, List[str]], nodes: List[str], gateways: Dict[str, str]) -> Dict[str, Dict[str, int]]:
    """
    Calculate shortest paths between all pairs of nodes using BFS with gateway constraints.

    Args:
        graph: Adjacency list representation of the graph
        nodes: List of node IDs
        gateways: Dictionary mapping gateway ID to gateway type

    Returns:
        Dictionary mapping (source, target) to shortest path length
    """
    shortest_paths = {}

    for source in nodes:
        shortest_paths[source] = {}

        # BFS to find shortest paths from source
        distances = {node: float('inf') for node in nodes}
        distances[source] = 0

        queue = deque([source])
        visited = {source}

        while queue:
            current = queue.popleft()

            for neighbor in graph.get(current, []):
                if neighbor in nodes and neighbor not in visited:
                    # Check gateway constraints
                    if current in gateways:
                        gateway_type = gateways[current]
                        if gateway_type == 'exclusiveGateway':
                            # For exclusive gateways, only one path is taken
                            # This is handled by the graph structure
                            pass
                        elif gateway_type == 'parallelGateway':
                            # For parallel gateways, all paths are taken with distance 1
                            pass

                    distances[neighbor] = distances[current] + 1
                    visited.add(neighbor)
                    queue.append(neighbor)

        # Store results
        for target in nodes:
            if distances[target] == float('inf'):
                shortest_paths[source][target] = float('inf')
            else:
                shortest_paths[source][target] = distances[target]

    return shortest_paths


def align_ssdt_matrices(matrix1: List[List[float]], matrix2: List[List[float]],
                        nodes1: List[str], nodes2: List[str]) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Align two SSDT matrices to the same dimension by padding with infinity.

    Args:
        matrix1: First SSDT matrix
        matrix2: Second SSDT matrix
        nodes1: Node IDs for first matrix
        nodes2: Node IDs for second matrix

    Returns:
        Tuple of (aligned_matrix1, aligned_matrix2) with same dimensions
    """
    n1, m1 = len(matrix1), len(matrix1[0]) if matrix1 else 0
    n2, m2 = len(matrix2), len(matrix2[0]) if matrix2 else 0

    # Use the larger dimension
    max_dim = max(n1, n2)

    # Create aligned matrices
    aligned_matrix1 = [[0.0] * max_dim for _ in range(max_dim)]
    aligned_matrix2 = [[0.0] * max_dim for _ in range(max_dim)]

    # Copy original matrices
    for i in range(n1):
        for j in range(m1):
            aligned_matrix1[i][j] = matrix1[i][j]

    for i in range(n2):
        for j in range(m2):
            aligned_matrix2[i][j] = matrix2[i][j]

        # Fill remaining positions with infinity for the smaller matrix
    if n1 < max_dim or m1 < max_dim:
        for i in range(n1, max_dim):
            for j in range(max_dim):
                if i == j:
                    aligned_matrix1[i][j] = 0.0  # Self-distance is 0
                else:
                    aligned_matrix1[i][j] = float('inf')
        for i in range(n1):
            for j in range(m1, max_dim):
                if i == j:
                    aligned_matrix1[i][j] = 0.0  # Self-distance is 0
                else:
                    aligned_matrix1[i][j] = float('inf')

    if n2 < max_dim or m2 < max_dim:
        for i in range(n2, max_dim):
            for j in range(max_dim):
                if i == j:
                    aligned_matrix2[i][j] = 0.0  # Self-distance is 0
                else:
                    aligned_matrix2[i][j] = float('inf')
        for i in range(n2):
            for j in range(m2, max_dim):
                if i == j:
                    aligned_matrix2[i][j] = 0.0  # Self-distance is 0
                else:
                    aligned_matrix2[i][j] = float('inf')

    return aligned_matrix1, aligned_matrix2


def build_ssdt_matrix(shortest_paths: Dict[str, Dict[str, int]], nodes: List[str]) -> List[List[float]]:
    """
    Build SSDT matrix from shortest paths.

    Args:
        shortest_paths: Dictionary of shortest path distances
        nodes: List of node IDs in order

    Returns:
        SSDT matrix as 2D list
    """
    n = len(nodes)
    ssdt_matrix = [[0.0] * n for _ in range(n)]

    for i, source in enumerate(nodes):
        for j, target in enumerate(nodes):
            if i == j:
                ssdt_matrix[i][j] = 0.0  # Self-distance is 0
            else:
                distance = shortest_paths[source][target]
                if distance == float('inf'):
                    ssdt_matrix[i][j] = float('inf')
                else:
                    ssdt_matrix[i][j] = float(distance)

    return ssdt_matrix


def calculate_ssdt_similarity(matrix1: List[List[float]], matrix2: List[List[float]]) -> float:
    """
    Calculate SSDT similarity between two matrices.

    Args:
        matrix1: First SSDT matrix
        matrix2: Second SSDT matrix

    Returns:
        SSDT similarity value between 0 and 1
    """
    if not matrix1 or not matrix2:
        return 0.0

    n1, m1 = len(matrix1), len(matrix1[0]) if matrix1 else 0
    n2, m2 = len(matrix2), len(matrix2[0]) if matrix2 else 0

    # Use the smaller matrix size for comparison
    n = min(n1, n2)
    m = min(m1, m2)

    if n == 0 or m == 0:
        return 0.0

    matching_elements = 0
    total_elements = n * m

    for i in range(n):
        for j in range(m):
            if matrix1[i][j] == matrix2[i][j]:
                matching_elements += 1

    return matching_elements / total_elements


def extract_bpmn_graph_data(bpmn_xml_content: str) -> Dict[str, Any]:
    """
    Extract all necessary data from BPMN XML for SSDT calculation.

    Args:
        bpmn_xml_content: BPMN 2.0 XML string

    Returns:
        Dictionary containing graph data
    """
    activities = extract_activity_nodes(bpmn_xml_content)
    gateways = extract_gateways(bpmn_xml_content)
    flows = extract_sequence_flows(bpmn_xml_content)
    bpmn_type = detect_bpmn_type(bpmn_xml_content)

    return {
        'activities': activities,
        'gateways': gateways,
        'flows': flows,
        'bpmn_type': bpmn_type
    }


def calculate_bpmn_ssdt_similarity(benchmark_bpmn_xml: str, target_bpmn_xml: str) -> Dict[str, Union[float,str ,list]]:
    """
    Calculate SSDT similarity between two BPMN models.

    Args:
        benchmark_bpmn_xml: Benchmark BPMN 2.0 XML string
        target_bpmn_xml: Target BPMN 2.0 XML string

    Returns:
        Dictionary containing SSDT similarity scores
    """
    print("Calculating BPMN SSDT similarity...")

    # Extract graph data from both models
    benchmark_data = extract_bpmn_graph_data(benchmark_bpmn_xml)
    target_data = extract_bpmn_graph_data(target_bpmn_xml)

    # Force requirement: both models must be process diagrams (non-collaboration)
    if benchmark_data['bpmn_type'] == 'collaboration':
        raise ValueError(
            "Benchmark model must be a process diagram (non-collaboration). SSDT is only applicable to process diagrams.")

    if target_data['bpmn_type'] == 'collaboration':
        raise ValueError(
            "Target model must be a process diagram (non-collaboration). SSDT is only applicable to process diagrams.")

    print(f"Benchmark model ({benchmark_data['bpmn_type']}): {len(benchmark_data['activities'])} activities, "
          f"{len(benchmark_data['gateways'])} gateways, {len(benchmark_data['flows'])} flows")
    print(f"Target model ({target_data['bpmn_type']}): {len(target_data['activities'])} activities, "
          f"{len(target_data['gateways'])} gateways, {len(target_data['flows'])} flows")

    # Build graphs with gateway-aware path calculation
    benchmark_graph = build_graph_with_gateways(
        benchmark_data['activities'], benchmark_data['gateways'], benchmark_data['flows'])
    target_graph = build_graph_with_gateways(
        target_data['activities'], target_data['gateways'], target_data['flows'])

    # Get all nodes sorted by ID
    benchmark_nodes = sorted(list(
        benchmark_data['activities'].keys()) + list(benchmark_data['gateways'].keys()))
    target_nodes = sorted(
        list(target_data['activities'].keys()) + list(target_data['gateways'].keys()))

    # Calculate shortest paths with gateway constraints
    benchmark_shortest_paths = calculate_shortest_paths_with_gateways(
        benchmark_graph, benchmark_nodes, benchmark_data['gateways'])
    target_shortest_paths = calculate_shortest_paths_with_gateways(
        target_graph, target_nodes, target_data['gateways'])

    # Build SSDT matrices
    benchmark_ssdt = build_ssdt_matrix(
        benchmark_shortest_paths, benchmark_nodes)
    target_ssdt = build_ssdt_matrix(target_shortest_paths, target_nodes)

    # Align matrices to same dimension
    aligned_benchmark_ssdt, aligned_target_ssdt = align_ssdt_matrices(
        benchmark_ssdt, target_ssdt, benchmark_nodes, target_nodes)

    # Calculate similarity
    ssdt_similarity = calculate_ssdt_similarity(
        aligned_benchmark_ssdt, aligned_target_ssdt)

    result = {
        'ssdt_similarity': ssdt_similarity,
        'ssdt_similarity_percentage': round(ssdt_similarity * 100, 2),
        'benchmark_bpmn_type': benchmark_data['bpmn_type'],
        'target_bpmn_type': target_data['bpmn_type'],
        'benchmark_activities': benchmark_data['activities'],
        'target_activities': target_data['activities'],
        'benchmark_gateways': benchmark_data['gateways'],
        'target_gateways': target_data['gateways'],
        'benchmark_ssdt_matrix': benchmark_ssdt,
        'target_ssdt_matrix': target_ssdt,
        'aligned_benchmark_ssdt_matrix': aligned_benchmark_ssdt,
        'aligned_target_ssdt_matrix': aligned_target_ssdt,
        'benchmark_nodes': benchmark_nodes,
        'target_nodes': target_nodes
    }

    print(f"SSDT similarity calculation completed:")
    print(f"  SSDT Similarity: {result['ssdt_similarity_percentage']}%")

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


def save_ssdt_result(result: Dict[str, Union[float,str ,list]], output_file: Optional[str] = None):
    """
    Save SSDT similarity result to file.

    Args:
        result: SSDT similarity result dictionary
        output_file: Output file path (optional)
    """
    if output_file is None:
        workplace = get_workplace()
        output_file = os.path.join(workplace, SSDT_OUTPUT_FILE)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"SSDT similarity result saved: {output_file}")
    except Exception as e:
        print(f"Failed to save SSDT similarity result: {e}")


def compare_bpmn_models(benchmark_bpmn_file: Optional[str] = None, target_bpmn_file: Optional[str] = None,
                        benchmark_bpmn_xml: Optional[str] = None, target_bpmn_xml: Optional[str] = None) -> Optional[Dict[str, Union[float,str ,list]]]:
    """
    Compare two BPMN models using SSDT similarity.

    Args:
        benchmark_bpmn_file: Benchmark BPMN file path
        target_bpmn_file: Target BPMN file path
        benchmark_bpmn_xml: Benchmark BPMN XML content (if already loaded)
        target_bpmn_xml: Target BPMN XML content (if already loaded)

    Returns:
        SSDT similarity result dictionary
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
    result = calculate_bpmn_ssdt_similarity(
        benchmark_bpmn_xml, target_bpmn_xml)

    # Save result
    save_ssdt_result(result)

    return result


if __name__ == '__main__':
    try:
        print("Starting BPMN SSDT similarity calculation...")

        # Compare BPMN models
        result = compare_bpmn_models()

        if result:
            print("\n=== SSDT Similarity Results ===")
            print(f"Benchmark BPMN Type: {result['benchmark_bpmn_type']}")
            print(f"Target BPMN Type: {result['target_bpmn_type']}")
            print(f"SSDT Similarity: {result['ssdt_similarity_percentage']}%")
            print(f"Results saved to: {get_workplace()}/{SSDT_OUTPUT_FILE}")
        else:
            print("SSDT similarity calculation failed")

    except Exception as e:
        print(f"SSDT similarity calculation failed: {e}")
