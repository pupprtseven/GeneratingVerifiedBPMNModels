"""
Generate tasks from requirements.

This module extracts and generates tasks from business requirements
for BPMN generation.
"""

import json
import os
import tempfile
from utils.agent import generate_prompt_from_config
from utils.configure import get_workplace
from utils.load_requirement import get_reqstring
from utils.combine import combine_results
from utils.dump import get_data_from_file_or_generate, save_result, save_result_with_extra, ENABLE_DUMP
from generation.symbol import get_symbol_data


# Configuration paths loaded from configure.yml
from utils.configure import get_generation_config_path, get_output_file_name

TASK_CONFIG_PATH = get_generation_config_path(
    "TASK_CONFIG_PATH") or "generation/config/task.json"
TASK_OUTPUT_FILE = get_output_file_name(
    "TASK_OUTPUT_FILE") or "task_output.json"


def get_task_data():
    """
    Get task data either from file or by generating.

    Returns:
        Dictionary containing task data
    """
    return get_data_from_file_or_generate(TASK_OUTPUT_FILE, generate_task, "task data")


def get_full_task_data():
    """
    Get complete task data including extra sections from file.

    Returns:
        Dictionary containing complete task data with extra sections
    """
    workplace = get_workplace()
    task_file_path = os.path.join(workplace, TASK_OUTPUT_FILE)

    try:
        with open(task_file_path, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
            print(f"Loaded full task data from: {task_file_path}")
            return task_data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Failed to load full task data from file: {e}")
        return {}


def generate_task():
    """
    Generate tasks from requirements and symbol table.

    Returns:
        Dictionary containing extracted tasks
    """
    # Get requirement string
    requirement = get_reqstring()

    # Get symbol data
    symbol_result = get_symbol_data()

    # Prepare input variables
    input_vars = {
        "REQUIREMENT": requirement,
        "SYMBOL": symbol_result
    }

    # Generate task output using agent
    result = generate_prompt_from_config(TASK_CONFIG_PATH, input_vars)

    # Extract the output and return directly
    extracted_output = result.get('extracted_output', {})

    # Save results
    save_result(result, TASK_OUTPUT_FILE, "Task generation")

    print("Extracted output:")
    print(json.dumps(extracted_output, ensure_ascii=False, indent=2))

    return extracted_output


def generate_message_task(tasks_data=None, symbol_data=None):
    """
    Generate message tasks from requirements and symbol table using extra.message config.

    Args:
        tasks_data: Pre-generated task data to avoid duplicate calls
        symbol_data: Pre-generated symbol data to avoid duplicate calls

    Returns:
        Dictionary containing extracted message tasks
    """
    # Get requirement string
    requirement = get_reqstring()

    # Get symbol data - use provided data or get from file/generate
    if symbol_data is not None:
        symbol_result = symbol_data
    else:
        symbol_result = get_symbol_data()

    # Get task data - use provided data or get from file/generate
    if tasks_data is not None:
        tasks = tasks_data
    else:
        tasks = get_task_data()

    # Prepare input variables
    input_vars = {
        "REQUIREMENT": requirement,
        "SYMBOL": symbol_result,
        "ALREADY_GENERATED_TASKS": tasks,
    }

    # Load the main config and extract the message config
    with open(TASK_CONFIG_PATH, 'r', encoding='utf-8') as f:
        main_config = json.load(f)

    message_config = main_config.get('extra', {}).get('message', {})
    if not message_config:
        raise ValueError(
            "Message configuration not found in task.json extra.message field")

    # Create a temporary config file for the message config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
        json.dump(message_config, temp_file, ensure_ascii=False, indent=2)
        temp_config_path = temp_file.name

    try:
        # Generate message task output using agent with the extracted config
        result = generate_prompt_from_config(temp_config_path, input_vars)
    finally:
        # Clean up temporary file
        os.unlink(temp_config_path)

    # Extract the output and return directly
    extracted_output = result.get('extracted_output', {})

    # Save results with message data in extra.message field
    save_result_with_extra(
        {}, TASK_OUTPUT_FILE, "Message task generation", "message", result)

    print("Extracted output:")
    print(json.dumps(extracted_output, ensure_ascii=False, indent=2))

    return extracted_output


def generate_and_combine_data():
    """
    Generate symbol, tasks and message tasks, combining results appropriately.

    This function implements the common pattern of generating all required data
    and combining the results, with different strategies based on dump setting.

    Returns:
        Dictionary containing combined symbol, task and message task results
    """
    if ENABLE_DUMP:
        # When dump is enabled, call all functions sequentially
        print("Dump enabled: Generating symbol, tasks and message tasks sequentially...")
        symbol_output = get_symbol_data()
        tasks_output = generate_task()
        message_result = generate_message_task()
    else:
        # When dump is disabled, generate symbol and tasks once and pass to message task
        print("Dump disabled: Generating symbol and tasks once and combining results...")

        # Generate symbol and tasks first (only once)
        symbol_output = get_symbol_data()
        tasks_output = generate_task()

        # Generate message tasks using the same symbol and task data
        message_result = generate_message_task(
            tasks_data=tasks_output, symbol_data=symbol_output)

    # Combine all results using the combine function
    combined_result = combine_results(symbol_output, tasks_output)
    combined_result = combine_results(combined_result, message_result)

    print("Combined result:")
    print(json.dumps(combined_result, ensure_ascii=False, indent=2))

    return combined_result


def generate_task_with_extra():
    """
    Generate symbol, tasks and message tasks, combining results appropriately.

    Returns:
        Dictionary containing combined symbol, task and message task results
    """
    return generate_and_combine_data()


if __name__ == '__main__':
    try:
        print("Starting task generation...")
        task_result = generate_task_with_extra()
        print("Task generation successful!")
        print(task_result)
    except (FileNotFoundError, ValueError, json.JSONDecodeError, KeyError) as e:
        print(f"Task generation failed: {e}")
