# BPMN Generator

A comprehensive BPMN (Business Process Model and Notation) generation and verification framework powered by Large Language Models (LLMs).

## Features

- **🔄 BPMN Generation**: Automatically generate BPMN diagrams from natural language requirements
- **🤖 LLM Integration**: Leverage OpenAI GPT models for intelligent process modeling
- **🏗️ Multi-lane Support**: Generate both single-process and collaboration diagrams
- **🔍 Model Verification**: Convert BPMN to Petri nets for formal verification
- **📊 Structured Output**: Generate symbol tables, task definitions, and sequence flows
- **⚙️ Configurable**: Flexible configuration system for different use cases

## Project Structure

```
BPMNGenerator/
├── generation/           # BPMN generation modules
│   ├── config/          # Configuration files for LLM prompts
│   │   ├── symbol.json  # Symbol table generation config
│   │   ├── task.json    # Task generation config
│   │   ├── seq.json     # Sequence flow generation config
│   │   └── gate.json    # Gateway generation config
│   ├── symbol.py        # Symbol table generation
│   ├── task.py          # Task generation
│   ├── seq.py           # Sequence flow generation
│   ├── gate.py          # Gateway generation
│   └── bpmn.py          # BPMN XML generation
├── verification/         # Model verification tools
│   └── bpmn_to_ctl.py   # BPMN to Petri net converter
├── utils/               # Utility modules
│   ├── agent.py         # LLM interaction utilities
│   ├── configure.py     # Configuration management
│   ├── dump.py          # Data persistence utilities
│   └── prompt.py        # Prompt generation utilities
├── workplace/           # Output directory for generated files
├── benchmark/           # Test cases and benchmarks
├── configure.yml        # Main configuration file
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd BPMNGenerator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API key**
   Create a `.secret.yml` file in the project root:
   ```yaml
   OPENAI_API_KEY: your_openai_api_key_here
   ```

4. **Configure workplace directory**
   Update `configure.yml` to set your output directory:
   ```yaml
   WORKPLACE: workplace/
   GENERATOR_PROMPT: "You are a BPMN modeling expert..."
   ```

## Usage

### Basic BPMN Generation

1. **Generate symbol table**
   ```bash
   python -m generation.symbol
   ```

2. **Generate tasks**
   ```bash
   python -m generation.task
   ```

3. **Generate sequence flows**
   ```bash
   python -m generation.seq
   ```

4. **Generate BPMN XML**
   ```bash
   python -m generation.bpmn
   ```

### Advanced Usage

**Generate complete BPMN workflow:**
```bash
python -m generation.bpmn
```

**Convert BPMN to Petri net for verification:**
```bash
python verification/bpmn_to_ctl.py workplace/bpmn_output.bpmn
```

## Configuration

### LLM Prompt Configuration

Each generation step uses JSON configuration files in `generation/config/`:

- **symbol.json**: Defines how to extract actors and tasks from requirements
- **task.json**: Configures task generation with message flow support
- **seq.json**: Defines sequence flow and gateway generation
- **gate.json**: Configures gateway logic and conditions

### Output Configuration

Generated files are saved in the `workplace/` directory:
- `symbol_output.json`: Extracted actors and tasks
- `task_output.json`: Generated tasks with message flows
- `seq_output.json`: Sequence flows and gateways
- `bpmn_output.bpmn`: Final BPMN XML file

## Features in Detail

### Multi-lane BPMN Support
- Automatically detects collaboration diagrams
- Generates participant lanes and message flows
- Supports complex inter-process communication

### LLM Integration
- Configurable prompt templates
- Variable injection system
- Structured output parsing
- Error handling and retry logic

### Verification Tools
- BPMN to Petri net conversion
- Support for both single-process and collaboration diagrams
- Formal verification capabilities

## Development

### Adding New Generation Steps

1. Create a new configuration file in `generation/config/`
2. Implement the generation logic in `generation/`
3. Update the main workflow in `generation/bpmn.py`

### Extending Verification

The verification module supports custom Petri net conversion algorithms and can be extended for additional formal verification methods.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please open an issue on the GitHub repository.
