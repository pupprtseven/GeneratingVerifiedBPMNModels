# BPMN2.0 Processing Guide

This guide explains how to use the SAPSAM toolchain to process BPMN2.0 files, including data parsing, filtering, and conversion to standard BPMN2.0 XML format.

## SAPSAM Project

**GitHub Repository**: [SAPSAM Project](https://github.com/sapsam/sapsam)

## Directory Structure

```
sap-sam/
├── data/
│   ├── raw/
│   │   └── models/          # Raw CSV files directory
│   └── interim/             # Intermediate processing files directory
├── src/
│   └── sapsam/             # SAPSAM toolkit
├── notebooks/              # Jupyter notebooks examples
├── BPMN2.0_LOCAL/         # Exported BPMN2.0 XML files
│   ├── standard/          # Standard flowcharts
│   └── collaboration/     # Collaboration diagrams
└── export_bpmn.js         # BPMN2.0 XML export script
```

## 1. Environment Setup

### 1.1 Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or use conda
conda env create -f environment.yml
conda activate sap-sam

# Install Node.js dependencies (for export_bpmn.js)
npm install
```

### 1.2 Data Preparation

Ensure that the `data/raw/models/` directory contains CSV files, each containing the following columns:
- `model_id`: Model ID
- `name`: Model name
- `namespace`: Namespace
- `Model JSON`: Model JSON data

## 2. Using SAPSAM to Parse Data

### 2.1 Basic Data Parsing

```python
import sys
sys.path.append("src")

from sapsam import parser, constants
import pandas as pd

# Get CSV file paths
csv_paths = parser.get_csv_paths()
print(f"Found {len(csv_paths)} CSV files")

# Parse model metadata (without Model JSON, fast)
df_meta = parser.parse_model_metadata()
print(f"Parsed {len(df_meta)} models")

# Parse complete data (with Model JSON)
df_full = parser.parse_model()
print(f"Parsed {len(df_full)} complete models")
```

### 2.2 Filter BPMN2.0 Files

```python
# Filter BPMN2.0 models
bpmn2_models = df_full[df_full['namespace'] == 'http://b3mn.org/stencilset/bpmn2.0#']
print(f"Found {len(bpmn2_models)} BPMN2.0 models")

# View basic information of BPMN2.0 models
print(bpmn2_models[['name', 'type', 'namespace']].head())
```

### 2.3 Parse BPMN Model Elements

```python
# Create BPMN model parser
bpmn_parser = parser.BpmnModelParser(parse_outgoing=True, parse_parent=True)

# Parse all BPMN model elements
df_elements = bpmn_parser.parse_model_elements()
print(f"Parsed {len(df_elements)} BPMN elements")

# View element type distribution
element_counts = df_elements['category'].value_counts()
print("BPMN element type distribution:")
print(element_counts.head(10))

# Save parsing results
df_elements.to_pickle(constants.DATA_INTERIM / "bpmn_elements.pkl")
```

## 3. Extract Data from Model JSON

### 3.1 Extract Single Model JSON

```python
import json

# Get the first BPMN2.0 model
first_model = bpmn2_models.iloc[0]
model_json = json.loads(first_model['Model JSON'])

# View model structure
print("Model ID:", model_json['resourceId'])
print("Model type:", model_json['stencil']['id'])
print("Number of child elements:", len(model_json.get('childShapes', [])))

# Save single model JSON
with open('single_model.json', 'w', encoding='utf-8') as f:
    json.dump(model_json, f, ensure_ascii=False, indent=2)
```

### 3.2 Batch Extract JSON Files

```python
import os
from pathlib import Path

# Create output directory
output_dir = Path("extracted_models")
output_dir.mkdir(exist_ok=True)

# Batch extract JSON files
for idx, model in bpmn2_models.iterrows():
    model_id = model['model_id']
    model_name = model['name']
    model_json = json.loads(model['Model JSON'])
    
    # Clean filename
    safe_name = "".join(c for c in str(model_name) if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name[:50]  # Limit length
    
    # Save JSON file
    filename = f"{model_id}_{safe_name}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(model_json, f, ensure_ascii=False, indent=2)
    
    if idx % 100 == 0:
        print(f"Processed {idx} models...")

print(f"Complete! Extracted {len(bpmn2_models)} JSON files to {output_dir}")
```

## 4. Convert to Standard BPMN2.0 XML using export_bpmn.js

### 4.1 Run JavaScript Script Directly

```bash
# Run export script
node export_bpmn.js
```

The script will automatically:
1. Read all CSV files in the `data/raw/models/` directory
2. Filter BPMN2.0 models
3. Skip models containing Subprocess
4. Distinguish between standard flowcharts and collaboration diagrams
5. Generate standard BPMN2.0 XML files

### 4.2 Output File Structure

```
BPMN2.0_LOCAL/
├── standard/              # Standard flowcharts
│   ├── 1_Process1.bpmn
│   ├── 2_Process2.bpmn
│   └── ...
└── collaboration/         # Collaboration diagrams
    ├── 1001_Collab1.bpmn
    ├── 1002_Collab2.bpmn
    └── ...
```

### 4.3 Custom Export Parameters

You can modify parameters in `export_bpmn.js`:

```javascript
// Limit the number of models to process (for testing)
const maxModels = 10;

// Custom output directory
const outputDir = 'custom_output';

// Custom file naming rules
const filename = `${index}_${safeName}_${modelId}.bpmn`;
```

## 5. Python Script Example

Create `python_export_bpmn.py` script:

```python
#!/usr/bin/env python3
"""
Python script: Extract JSON from CSV files and call export_bpmn.js to convert to BPMN2.0 XML
"""

import json
import subprocess
import pandas as pd
from pathlib import Path
import sys

# Add src path
sys.path.append("src")
from sapsam import parser

def extract_bpmn2_models():
    """Extract BPMN2.0 model data"""
    print("Parsing CSV files...")
    
    # Parse complete data
    df_full = parser.parse_model()
    
    # Filter BPMN2.0 models
    bpmn2_models = df_full[df_full['namespace'] == 'http://b3mn.org/stencilset/bpmn2.0#']
    
    print(f"Found {len(bpmn2_models)} BPMN2.0 models")
    return bpmn2_models

def save_models_to_json(bpmn2_models, output_file="bpmn2_models.json"):
    """Save model data to JSON file"""
    print(f"Saving model data to {output_file}...")
    
    models_data = []
    for idx, model in bpmn2_models.iterrows():
        model_data = {
            'model_id': model['model_id'],
            'name': model['name'],
            'namespace': model['namespace'],
            'model_json': model['Model JSON']
        }
        models_data.append(model_data)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(models_data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(models_data)} models to {output_file}")

def run_export_script():
    """Run export_bpmn.js script"""
    print("Running export_bpmn.js...")
    
    try:
        result = subprocess.run(['node', 'export_bpmn.js'], 
                              capture_output=True, text=True, check=True)
        print("Export successful!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Export failed!")
        print("Error message:", e.stderr)
        return False
    
    return True

def main():
    """Main function"""
    print("=== BPMN2.0 Processing Pipeline ===")
    
    # 1. Extract BPMN2.0 models
    bpmn2_models = extract_bpmn2_models()
    
    # 2. Save as JSON file (optional)
    save_models_to_json(bpmn2_models)
    
    # 3. Run export script
    success = run_export_script()
    
    # if success:
    #     print("\n=== Processing Complete ===")
    #     print("Output file locations:")
    #     print("- Standard flowcharts: BPMN2.0_LOCAL/standard/")
    #     print("- Collaboration diagrams: BPMN2.0_LOCAL/collaboration/")
    # else:
    #     print("\n=== Processing Failed ===")

if __name__ == "__main__":
    main()
```

Run the Python script:

```bash
python python_export_bpmn.py
```

## 6. Validate Generated BPMN2.0 XML

### 6.1 Validate using bpmn.io

1. Open https://bpmn.io/
2. Click "Create new BPMN diagram"
3. Drag the generated .bpmn file to the page
4. Check if it displays correctly

### 6.2 Use XML Validation Tools

```python
import xml.etree.ElementTree as ET

def validate_bpmn_xml(xml_file):
    """Validate BPMN XML file"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Check root element
        if root.tag.endswith('definitions'):
            print(f"✓ {xml_file}: Valid BPMN2.0 XML")
            return True
        else:
            print(f"✗ {xml_file}: Invalid BPMN2.0 XML")
            return False
    except Exception as e:
        print(f"✗ {xml_file}: Parsing error - {e}")
        return False

# Validate all generated XML files
bpmn_dir = Path("BPMN2.0_LOCAL")
for xml_file in bpmn_dir.rglob("*.bpmn"):
    validate_bpmn_xml(xml_file)
```