# BPMN Benchmark Tools

## Overview

This directory contains tools for BPMN model unification and similarity measurement:

- **`unification.py`**: Normalizes BPMN 2.0 models by mapping symbols (actors and tasks) between two different BPMN files using semantic similarity
- **`metrics/`**: Contains similarity measurement algorithms for comparing BPMN models

## Tools

### 1. Symbol Unification Tool (`unification.py`)

The `unification.py` tool normalizes BPMN 2.0 models by mapping symbols (actors and tasks) between two different BPMN files using semantic similarity. It generates BPMN files with unified symbol identifiers for easier model comparison.

## What is Confidence?

Confidence is a score between 0 and 1 that indicates how certain the tool is about a symbol mapping:
- **0.8-1.0**: High confidence - symbols are very similar
- **0.5-0.7**: Medium confidence - symbols are somewhat similar  
- **0.0-0.4**: Low confidence - symbols may not match well

## Usage

### Method 1: Direct Execution

```bash
cd benchmark
python unification.py
```

This will:
1. Look for `workplace/benchmark_symbol_output.json` as benchmark data
2. Look for `workplace/target_bpmn.bpmn` as target BPMN file
3. Generate unified BPMN file as `workplace/unified_bpmn.bpmn`

### Method 2: Programmatic Usage

```python
from benchmark.unification import unify_bpmn_models

# Specify file paths
result = unify_bpmn_models(
    bench_symbol_file="path/to/benchmark_symbol_output.json",
    target_bpmn_file="path/to/target.bpmn"
)

if result:
    print("Unification successful!")
    print(f"Unified BPMN saved to: workplace/unified_bpmn.bpmn")
```

### Method 3: Step by Step

```python
from benchmark.unification import generate_unification, unification_algorithm

# Generate symbol mappings
mapping_result = generate_unification(bench_data, target_data)

# Apply unification algorithm
result = unification_algorithm(bench_data, target_bpmn_xml)
```

## Input Files

### Benchmark Symbol Data (JSON)

```json
{
  "actor": [
    {
      "actor_name": "User",
      "symbol": "A1"
    }
  ],
  "tasks": [
    {
      "actor_symbol": "A1", 
      "task_description": "Submit application",
      "task_symbol": "T1"
    }
  ]
}
```

### Target BPMN File (BPMN 2.0 XML)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="Process_1">
    <bpmn:userTask id="UserTask_1" name="Submit application" />
  </bpmn:process>
</bpmn:definitions>
```

## Output

### Unified BPMN File

The generated BPMN file will have the same symbol IDs as the benchmark, making it easier to compare models.

### Mapping Results

```python
{
    'actor_mappings': [
        {
            'bench_symbol': 'A1',
            'target_symbol': 'Participant_1', 
            'confidence': 0.9
        }
    ],
    'task_mappings': [
        {
            'bench_symbol': 'T1',
            'target_symbol': 'UserTask_1',
            'confidence': 0.8
        }
    ]
}
```

## Configuration

All file paths are configurable in `configure.yml`:

```yaml
OUTPUT_FILES:
  BENCHMARK_SYMBOL_OUTPUT_FILE: "benchmark_symbol_output.json"
  TARGET_SYMBOL_OUTPUT_FILE: "target_symbol_output.json"
  UNIFICATION_OUTPUT_FILE: "unification_output.json"
```

## Simple Example

```python
# Load benchmark data
with open("benchmark_symbol_output.json", "r") as f:
    bench_data = json.load(f)

# Load target BPMN
with open("target.bpmn", "r") as f:
    target_bpmn = f.read()

# Unify symbols
result = unification_algorithm(bench_data, target_bpmn)

# Save unified BPMN
with open("unified.bpmn", "w") as f:
    f.write(result['unified_bpmn_xml'])
```

### 2. Similarity Metrics (`metrics/`)

The `metrics/` folder contains algorithms for measuring similarity between BPMN models:

#### Jaccard Similarity (`metrics/jaccard.py`)

Measures similarity based on sequence flows and message flows between two BPMN models.

**Features:**
- Supports both collaboration and process diagrams
- Calculates separate similarity for sequence flows and message flows
- Provides weighted similarity (70% sequence + 30% message)
- Outputs percentage values

**Usage:**
```bash
cd benchmark/metrics
python jaccard.py
```

**Output:**
```json
{
  "sequence_flow_similarity_percentage": 85.5,
  "message_flow_similarity_percentage": 72.0,
  "overall_similarity_percentage": 81.2,
  "weighted_similarity_percentage": 82.1
}
```

#### SSDT Similarity (`metrics/ssdt.py`)

Measures similarity using Shortest Successor Distance Matrix for process diagrams only.

**Features:**
- **Only applicable to process diagrams (non-collaboration)**
- Calculates shortest distances between all activity nodes
- Handles gateway constraints (exclusive/parallel gateways)
- Automatically aligns matrices to same dimension
- Returns similarity percentage

**Gateway Handling:**
- **Exclusive Gateways**: Different paths are considered unreachable
- **Parallel Gateways**: All paths have distance 1
- Multiple paths: Takes minimum distance

**Usage:**
```bash
cd benchmark/metrics
python ssdt.py
```

**Output:**
```json
{
  "ssdt_similarity_percentage": 78.5,
  "benchmark_bpmn_type": "process",
  "target_bpmn_type": "process",
  "aligned_benchmark_ssdt_matrix": [...],
  "aligned_target_ssdt_matrix": [...]
}
```

**Requirements:**
- Both BPMN models must be process diagrams
- Nodes are sorted by ID for consistent matrix ordering
- Smaller matrices are padded with infinity values

## Notes

- Ensure all files use UTF-8 encoding
- BPMN files must be in BPMN 2.0 format
- Symbol IDs in benchmark data must be unique
- Mapping quality depends on semantic similarity of symbol names
- Jaccard similarity works with both collaboration and process diagrams
- SSDT similarity requires process diagrams only 