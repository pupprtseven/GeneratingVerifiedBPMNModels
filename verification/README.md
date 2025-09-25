# verification Module Usage Guide

The verification module is used for formal verification of BPMN models and includes the following main functionalities:

## 1. CTL Generation (ctl.py)

- This script reads `workplace/req.txt` and automatically generates CTL (Computation Tree Logic) properties based on the requirements, for use in subsequent model checking.
- Example usage (assuming the script is implemented):
  ```bash
  python -m verification.ctl
  ```
- Output: Generated CTL property file for use with model checking tools.

> future work: consider bpmn2constraints

## 2. BPMN to Petri Net Conversion (bpmn_to_pt.py)

- This script converts a BPMN file (e.g., `workplace/bpmn_output.bpmn`) into a Petri net model, supporting both single-process and multi-lane collaboration diagrams.
- Example usage:
  ```bash
  python -m verification.bpmn_to_pt
  ```
- Output: Structured data of the Petri net (e.g., JSON), which can be used for further verification.

## 3. External Model Checking Tools

- This project does not include specific model checking tools (such as NuSMV, LoLA, etc.); users need to integrate them separately.
- Recommended workflow: Use the Petri net and CTL properties as input, and invoke external model checkers for verification.

## 4. Results and Revision Suggestions

- For unsatisfied CTL properties, the model checker will output the violated CTL formulas, corresponding counterexample traces, and analysis results.
- It is recommended to organize this information into `workplace/revision.json`, for example:
  ```json
  {
    "violated_ctl": ["AG(task1 -> AF task2)", ...],
    "counterexample_paths": [
      ["task1", "task3", "task4"],
      ...
    ],
    "analysis": "task3 does not necessarily occur after task1. Consider adjusting the process."
  }
  ```

## 5. Automatic BPMN Refinement

- `generation/refine_seq.py` will read `workplace/revision.json`, combine the original requirements and task flows, and automatically invoke an LLM to generate an improved BPMN process that eliminates CTL violations.
- The refined process will be saved as `workplace/revised_seq_output.json`.

---

## Recommended Workflow

1. Generate BPMN (see the generation module).
2. Convert to Petri net using `bpmn_to_pt.py`.
3. Automatically generate CTL properties from requirements (if ctl.py is implemented).
4. Use external tools to verify the Petri net and CTL properties.
5. Write violations, counterexample traces, and analysis results to `workplace/revision.json`.
6. Run `python -m generation.refine_seq` to automatically refine the BPMN process.

To further extend verification capabilities, you can add custom Petri net conversion or CTL generation scripts under the verification module.
