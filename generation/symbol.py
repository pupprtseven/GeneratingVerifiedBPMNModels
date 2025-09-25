"""
Generate symbol table from requirements.

This module extracts actors and tasks from business requirements
and generates a structured symbol table for BPMN generation.
"""
import openai
import json
import os
from utils.agent import generate_prompt_from_config
from utils.configure import get_workplace
from utils.load_requirement import get_reqstring
from utils.dump import get_data_from_file_or_generate, save_result


# Configuration paths loaded from configure.yml
from utils.configure import get_generation_config_path, get_output_file_name

SYMBOL_CONFIG_PATH = get_generation_config_path(
    "SYMBOL_CONFIG_PATH") or "generation/config/symbol.json"
SYMBOL_OUTPUT_FILE = get_output_file_name(
    "SYMBOL_OUTPUT_FILE") or "symbol_output.json"


def add_start_end_tasks(extracted_output):
    """
    Add start and end tasks for each actor in the extracted output.

    Args:
        extracted_output: Dictionary containing actor and tasks data

    Returns:
        Modified extracted_output with start and end tasks added
    """
    if 'actor' in extracted_output and 'tasks' in extracted_output:
        actors = extracted_output['actor']
        tasks = extracted_output['tasks']

        # Add start and end tasks for each actor
        for i, actor in enumerate(actors):
            if isinstance(actor, dict) and 'actor_name' in actor:
                actor_symbol = actor.get('symbol', f'A{i+1}')

                # Add start task
                start_task = {
                    "actor_symbol": actor_symbol,
                    "task_description": f"initial of {actor['actor_name']}",
                    "task_symbol": f"S{i+1}"
                }
                tasks.append(start_task)

                # Add end task
                end_task = {
                    "actor_symbol": actor_symbol,
                    "task_description": f"end of {actor['actor_name']}",
                    "task_symbol": f"E{i+1}"
                }
                tasks.append(end_task)

        # Update the extracted_output with modified tasks
        extracted_output['tasks'] = tasks

    return extracted_output


def get_symbol_data():
    """
    Get symbol data either from file or by generating.

    Returns:
        Dictionary containing symbol data
    """
    return get_data_from_file_or_generate(SYMBOL_OUTPUT_FILE, generate_symbol, "symbol data")


def generate_symbol():
    """
    Generate symbol table from requirements.

    Returns:
        Dictionary containing extracted actors and tasks
    """
    # Get requirement string
    requirement = get_reqstring()

    # Prepare input variables
    input_vars = {
        "REQUIREMENT": requirement
    }

    # Generate symbol output using agent
    result = generate_prompt_from_config(SYMBOL_CONFIG_PATH, input_vars)

    # Extract the output and return directly
    extracted_output = result.get('extracted_output', {})

    # Add start and end tasks for each actor
    extracted_output = add_start_end_tasks(extracted_output)

    # Save full results for debugging (if enabled)
    save_result(result, SYMBOL_OUTPUT_FILE, "Symbol generation")

    print("Extracted output:")
    print(json.dumps(extracted_output, ensure_ascii=False, indent=2))

    return extracted_output


if __name__ == '__main__':
    try:
        print("Starting symbol generation...")
        symbol_result = generate_symbol()
        print("Symbol generation successful!")
        print(symbol_result)
    except (FileNotFoundError, ValueError, json.JSONDecodeError, KeyError) as e:
        print(f"Symbol generation failed: {e}")
