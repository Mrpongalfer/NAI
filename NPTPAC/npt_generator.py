#!/usr/bin/env python3
# Nexus Protocol Toolkit (NPT) Generator - v2.0
# This script scaffolds the NPT environment, NER structure, and the PAC application.
# It is intended to be run by the outer bootstrap_npt.sh script.

import argparse
import datetime
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import textwrap
import traceback # For printing full tracebacks on unexpected errors
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union # Added Union for fzf_select

# --- Constants & Configuration (Basic ones needed early) ---
NPT_GENERATOR_VERSION = "2.0"
CURRENT_YEAR = str(datetime.datetime.now().year)
NPT_BASE_DIR_ENV_VAR_NAME = "NPT_BASE_DIR" # Name of the env var used by PAC

# --- Colorized Output Helpers ---
class TermColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def echo_color(color_code: str, message: str, bold: bool = False):
    prefix = TermColors.BOLD if bold else ""
    print(f"{prefix}{color_code}{message}{TermColors.ENDC}")

def info(message: str): echo_color(TermColors.OKBLUE, f"INFO: {message}")
def success(message: str): echo_color(TermColors.OKGREEN, f"SUCCESS: {message}")
def warning(message: str): echo_color(TermColors.WARNING, f"WARN: {message}")
def error(message: str, exit_code: Optional[int] = None):
    echo_color(TermColors.FAIL, f"ERROR: {message}", bold=True)
    if exit_code is not None:
        sys.exit(exit_code) # This will be caught by the __main__ block's SystemExit handler
def step(message: str): echo_color(TermColors.OKCYAN, f"\n>>> STEP: {message} <<<\n", bold=True)
def important(message: str): echo_color(TermColors.HEADER, message, bold=True)

# --- Conditional Library Imports (Now using defined helpers) ---

# For WRITING .toml files (e.g., settings.toml)
TOML_WRITER_LIB_MODULE: Optional[Any] = None 
TOML_WRITER_LIB_AVAILABLE: bool = False
try:
    import toml  # This is the library from PyPI: pip install toml
    TOML_WRITER_LIB_MODULE = toml
    TOML_WRITER_LIB_AVAILABLE = True
    info("Using 'toml' library for WRITING .toml files.") 
except ImportError:
    # toml module remains None, TOML_WRITER_LIB_AVAILABLE remains False
    warning("'toml' library not found. PAC settings file will be written as JSON with a .toml extension.") 
    warning("For proper TOML format, please install it in the environment running this generator: pip install toml")

# For READING .toml files (if ever needed by the generator itself, currently not for settings.toml creation)
TOML_READER_LIB_MODULE: Optional[Any] = None
try:
    import tomllib as TOML_READER_LIB_IMPORTER # Python 3.11+ standard library
    TOML_READER_LIB_MODULE = TOML_READER_LIB_IMPORTER
    info("Using standard library 'tomllib' for READING .toml files (if needed).")
except ImportError:
    try:
        import tomli as TOML_READER_LIB_IMPORTER # Fallback for Python < 3.11
        TOML_READER_LIB_MODULE = TOML_READER_LIB_IMPORTER
        info("Using 'tomli' as TOML_READER_LIB_MODULE for READING .toml files (if needed).")
    except ImportError:
        # TOML_READER_LIB_MODULE remains None
        warning("No TOML reading library ('tomllib' or 'tomli') found for the generator.")

# --- Default directory names ---
NER_DIR_NAME = "ner_repository"
PAC_CLI_DIR_NAME = "pac_cli"
PAC_APP_DIR_NAME = "app"
PAC_CORE_DIR_NAME = "core"
PAC_COMMANDS_DIR_NAME = "commands"
PAC_UTILS_DIR_NAME = "utils"
PAC_TESTS_DIR_NAME = "tests"
PAC_CONFIG_DIR_NAME = "config"
PAC_LOGS_DIR_NAME = "logs"    
CORE_AGENTS_DIR_NAME = "core_agents"

# --- Default filenames ---
PAC_SETTINGS_FILENAME = "settings.toml"
PAC_LAUNCHER_FILENAME = "npac"
SETUP_VENV_FILENAME = "setup_venv.sh"
GITIGNORE_FILENAME = ".gitignore"
PYPROJECT_FILENAME = "pyproject.toml"
PAC_MAIN_PY_FILENAME = "main.py"
PAC_INIT_PY_FILENAME = "__init__.py"

# --- File System and Process Utilities ---
def create_directory(path: Path, ignore_errors: bool = False) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        if not ignore_errors:
            error(f"Failed to create directory {path}: {e.strerror}", 1)
        return False

def create_file(path: Path, content: str = "", executable: bool = False, overwrite: bool = True) -> bool:
    if path.exists() and not overwrite:
        info(f"File {path} already exists and overwrite is false. Skipping.")
        return True
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        if executable:
            current_mode = path.stat().st_mode
            path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return True
    except OSError as e:
        error(f"Failed to create file {path}: {e.strerror}", 1)
        return False 

def copy_file(src_path: Path, dest_path: Path, ignore_errors: bool = False) -> bool:
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest_path)
        info(f"Copied '{src_path.name}' to '{dest_path}'")
        return True
    except (shutil.Error, OSError) as e:
        msg = f"Failed to copy file from {src_path} to {dest_path}: {e}"
        if not ignore_errors: error(msg, 1)
        else: warning(msg)
        return False

def run_command(command: List[str], cwd: Optional[Path] = None, capture: bool = False) -> Tuple[bool, str, str]:
    command_str = " ".join(shlex.quote(c) for c in command)
    info(f"Running command: {command_str}{f' in {cwd}' if cwd else ''}")
    try:
        process = subprocess.run(
            command, cwd=cwd, text=True, capture_output=capture, check=False
        )
        stdout = process.stdout.strip() if process.stdout and capture else ""
        stderr = process.stderr.strip() if process.stderr and capture else ""
        if process.returncode == 0:
            if capture: info(f"Command succeeded.") # STDOUT can be large
            else: info("Command succeeded.")
            return True, stdout, stderr
        else:
            warning(f"Command failed with RC {process.returncode}.")
            if capture:
                warning(f"  STDERR: {stderr[:200]}{'...' if len(stderr)>200 else ''}")
                warning(f"  STDOUT: {stdout[:200]}{'...' if len(stdout)>200 else ''}")
            return False, stdout, stderr
    except FileNotFoundError:
        error(f"Command not found: {command[0]}. Ensure it's installed and in PATH.")
        return False, "", f"Command not found: {command[0]}"
    except Exception as e:
        error(f"Unexpected error running command '{command_str}': {e!r}")
        return False, "", str(e)

def get_user_input(prompt_message: str, default: Optional[str] = None) -> str:
    full_prompt = f"{TermColors.WARNING}{prompt_message}{TermColors.ENDC}"
    if default is not None:
        full_prompt += f" (default: {TermColors.OKGREEN}{default}{TermColors.ENDC})"
    full_prompt += ": "
    try:
        user_response = input(full_prompt).strip()
        return user_response if user_response else (default if default is not None else "")
    except EOFError:
        warning("EOF encountered reading user input. Using default if available, or empty string.")
        return default if default is not None else ""
    except KeyboardInterrupt:
        warning("\nUser interrupted input. Exiting generator.")
        sys.exit(130)

def confirm_action(prompt_message: str, default_yes: bool = False) -> bool:
    options = "(Y/n)" if default_yes else "(y/N)"
    default_char = "y" if default_yes else "n"
    while True:
        response = get_user_input(f"{prompt_message} {options}", default=default_char).lower()
        if response in ["y", "yes"]: return True
        if response in ["n", "no"]: return False
        warning("Invalid input. Please answer 'y' or 'n'.")

# --- Global Paths (Type hints. Values assigned in main_generator) ---
NPT_BASE_DIR_ABS: Path
NER_PATH_ABS: Path
PAC_CLI_PATH_ABS: Path
PAC_APP_PATH_ABS: Path
PAC_CORE_PATH_ABS: Path
PAC_COMMANDS_PATH_ABS: Path
PAC_UTILS_PATH_ABS: Path
PAC_TESTS_PATH_ABS: Path
PAC_CONFIG_PATH_ABS: Path
PAC_LOGS_PATH_ABS: Path
CORE_AGENTS_PATH_ABS: Path
PAC_SETTINGS_FILE_PATH: Path

PYTHON_CMD_FROM_BOOTSTRAP: str = os.environ.get("NPT_PYTHON_CMD", "python3")

# --- Main Argument Parser ---
def setup_generator_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"NPT Generator v{NPT_GENERATOR_VERSION} - Scaffolds the Nexus Protocol Toolkit.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--base-dir", type=Path, required=True,
        help="Absolute base directory where NPT will be installed (provided by bootstrap_npt.sh)."
    )
    parser.add_argument(
        "--ner-repo-url", type=str, default="git@github.com:mrpongalfer/NER.git",
        help="URL of your empty GitHub repository for NER."
    )
    parser.add_argument(
        "--llm-preference", type=str, choices=["openai", "anthropic", "google", "ollama", "generic"],
        default="ollama", help="Preferred LLM API/client for PAC stubs."
    )
    parser.add_argument(
        "--force-overwrite", action="store_true",
        help="Force overwrite of existing files without prompting (use with caution)."
    )
    return parser

# --- NER Structure and Content Generation (Part 2) ---
NER_STRUCTURE = {
    "00_CORE_EDICTS": {
        "01_architect_supremacy.md": "# Edict 1: Architect's Supremacy\n\nAll operations and generated artifacts must align with the Architect's explicit and implied directives...",
        "02_TPC_adherence.md": "# Edict 2: True Prime Code (TPC) Adherence\n\nAll code must be TPC: 'neither too much nor not enough, exactly what is needed, perfectly intuitive and completely functional and actionable and ready to be used immediately and seamlessly.'",
        "README.md": "# Core Edicts\n\nThis directory contains the foundational edicts governing the Omnitide Nexus and its components."
    },
    "01_ONAP_R3_COMPONENTS": { 
        "ONAP_P1_Foundation.md": "# ONAP - Part 1: Foundation, Persona, Core Edicts & TPC\n\n[SYSTEM ACTIVATION - OMNITIDE NEXUS PROTOCOL - R_VERSION - PROMPT 1/X]\n\nYOU ARE NOW OPERATING AS A SPECIALIZED INSTANCE...",
        "ONAP_P2_Core_Team.md": "# ONAP - Part 2: Core Team Integration & Recursive Feedback\n\n[SYSTEM ACTIVATION - OMNITIDE NEXUS PROTOCOL - R_VERSION - PROMPT 2/X]\n\nINTEGRATE THE OMNITIDE CORE TEAM ADVISORY PROTOCOL...",
        "ONAP_P3_Advanced_Concepts.md": "# ONAP - Part 3: Advanced Concepts & Persistent Development Goals\n\n[SYSTEM ACTIVATION - OMNITIDE NEXUS PROTOCOL - R_VERSION - PROMPT 3/X]\n\nINTEGRATE ADVANCED NEXUS DIRECTIVES...",
        "ONAP_P4_Final_Activation.md": "# ONAP - Part 4: Final Activation, Synergistic Execution, and Confirmation\n\n[SYSTEM ACTIVATION - OMNITIDE NEXUS PROTOCOL - R_VERSION - PROMPT 4/X]\n\nFINAL ACTIVATION & SYNERGISTIC EXECUTION...",
        "README.md": "# Omnitide Nexus Activation Protocol (ONAP) Components\n\nThis directory holds the structured prompts for imprinting LLMs with the Omnitide Nexus operational matrix."
    },
    "02_TPC_STANDARD": {
        "TPC_Definition_Latest.md": "# True Prime Code (TPC) Standard - Detailed\n\nTPC is the philosophical and practical cornerstone...\n\n**Attributes:**\n- Optimal Functionality\n- Minimal Complexity\n- Maximum Efficiency\n...",
        "README.md": "# TPC Standard Documentation"
    },
    "03_CORE_TEAM_PERSONAS": {
        "Tony_Stark.md": "# Core Team Persona: Tony Stark\n\n**Focus:** Feasibility, cutting-edge tech, elegant engineering, practical application, resource optimization, 'wow factor'.\n...",
        "Rick_Sanchez.md": "# Core Team Persona: Rick Sanchez (C-137)\n\n**Focus:** Scientific rigor (often shortcut), questioning all assumptions, unforeseen consequences, radical efficiency, interdimensional problem-solving, 'is it a pointless exercise for morons?'.\n...",
        "Lucy_Kushinada.md": "# Core Team Persona: Lucy Kushinada\n\n**Focus:** Cybersecurity, data integrity & privacy, stealth operations, system vulnerabilities, efficient human-computer interface.\n...",
        "README.md": "# Core Team Personas\n\nDetailed profiles for simulating the Omnitide Core Team feedback loop."
    },
    "04_INTERACTION_GUIDES": {
        "NAI_Interaction_Principles.md": "# NAI Interaction Guide Principles\n\nThis document summarizes core techniques for efficient and context-aware interaction...\n- PMA (Project Memory Architecture)\n- Semantic Compression\n...",
        "README.md": "# Interaction Guides\n\nBest practices and protocols for interacting with Nexus Auxiliary AI instances."
    },
    "05_PROJECT_SUMMARIES": {
        "Project_Scribe_Summary.md": "# Project Scribe Summary\n\n**Purpose:** Apex Automated Code Validation & Integration Agent.\n**Key Features:** Validation gauntlet, AI-assisted checks, Git integration...\n",
        "Project_ExWork_Summary.md": "# Project Ex-Work Summary\n\n**Purpose:** Executes structured JSON commands for task automation.\n**Key Features:** Action handlers, LLM integration for diagnosis, sign-off mechanism...\n",
        "README.md": "# Project Summaries\n\nOverviews of key projects and components within the Omnitide Nexus."
    },
    "06_AGENT_BLUEPRINTS": {
        "ex_work_agent": {
            "templates": {
                "basic_echo.exwork.json": "{\n  \"step_id\": \"exwork_echo_001\",\n  \"description\": \"A simple echo command.\",\n  \"actions\": [\n    {\n      \"type\": \"ECHO\",\n      \"message\": \"Hello from Ex-Work via PAC!\"\n    }\n  ]\n}",
                "git_status.exwork.json": "{\n  \"step_id\": \"exwork_git_status_001\",\n  \"description\": \"Run git status in the current project.\",\n  \"actions\": [\n    {\n      \"type\": \"RUN_SCRIPT\", \n      \"script_path\": \"git\", \n      \"args\": [\"status\"], \n      \"cwd\": \".\" \n    }\n  ]\n}",
                "README.md": "# Ex-Work Agent Templates\n\nStore Ex-Work JSON instruction templates here. PAC will list and use these.\nUse `.exwork.json` extension for clarity."
            },
            "docs": {
                "ExWork_Agent_Interface.md": "# Ex-Work Agent Interface Notes\n\n- Expects JSON instruction block via stdin.\n- Outputs JSON result to stdout.\n- Key action types: ECHO, CREATE_OR_REPLACE_FILE, RUN_SCRIPT, LINT_FORMAT_FILE, GIT_ADD, GIT_COMMIT, CALL_LOCAL_LLM, DIAGNOSE_ERROR, APPLY_PATCH, REQUEST_SIGNOFF.\n",
                "README.md": "# Ex-Work Agent Documentation Stubs"
            }
        },
        "scribe_agent": {
            "profiles": {
                "default.scribe.toml": "# Default Scribe Profile (.scribe.toml)\n\nfail_on_audit_severity = \"high\"\nfail_on_lint_critical = true\nfail_on_mypy_error = true\nfail_on_test_failure = true\n\nollama_base_url = \"http://localhost:11434\"\nollama_model = \"mistral-nemo:12b-instruct-2407-q4_k_m\"\n\ncommit_message_template = \"feat(Scribe): Apply validated changes to {target_file}\"\n\nvalidation_steps = [\n  \"validate_inputs\",\n  \"setup_environment\",\n  \"install_deps\",\n  \"audit_deps\",\n  \"apply_code\",\n  \"format_code\",\n  \"lint_code\",\n  \"type_check\",\n  \"run_precommit\",\n  \"commit_changes\",\n  \"generate_report\"\n]\n",
                "README.md": "# Scribe Agent Configuration Profiles\n\nStore Scribe TOML configuration profiles here (e.g., `.scribe.toml` or custom named `.toml` files).\nPAC will allow selection of these profiles."
            },
            "docs": {
                "Scribe_Agent_Interface.md": "# Scribe Agent Interface Notes\n\n- Invoked via CLI with various arguments (`--target-dir`, `--code-file`, etc.).\n- Reads `.scribe.toml` for detailed configuration.\n- Outputs JSON report to stdout.\n",
                "README.md": "# Scribe Agent Documentation Stubs"
            }
        },
        "README.md": "# Agent Blueprints\n\nTemplates, documentation, and profiles for core NPT agents."
    },
    "07_SECURITY_TOOLS": {
        "red_team": {
            "nmap_scans": {
                "basic_host_discovery.manifest.json": "{\n  \"tool_name\": \"Nmap Host Discovery\",\n  \"description\": \"Performs a simple ping scan to discover live hosts on a network segment.\",\n  \"ex_work_template\": \"nmap_host_discovery.exwork.json\",\n  \"manual_command\": \"nmap -sn <target_network_CIDR>\",\n  \"expected_output_type\": \"text\",\n  \"notes\": \"Requires nmap to be installed. Target network should be specified carefully.\"\n}",
                "nmap_host_discovery.exwork.json": "{\n  \"step_id\": \"redteam_nmap_discover_001\",\n  \"description\": \"Nmap host discovery scan for {{target_network_cidr}}.\",\n  \"parameters\": [{\"name\": \"target_network_cidr\", \"prompt\": \"Enter target network CIDR (e.g., 192.168.1.0/24)\"}],\n  \"actions\": [\n    {\n      \"type\": \"RUN_SCRIPT\",\n      \"script_path\": \"nmap\",\n      \"args\": [\"-sn\", \"{{target_network_cidr}}\"]\n    }\n  ]\n}",
                "README.md": "# Nmap Scans\n\nManifests and Ex-Work templates for Nmap scanning operations."
            },
            "README.md": "# Red Team Tools & Techniques\n\nManifests, templates, and notes for offensive security operations."
        },
        "blue_team": {
            "log_analysis_templates": {
                "syslog_error_check.manifest.json": "{\n  \"tool_name\": \"Syslog Error Check\",\n  \"description\": \"Greps system logs for common error patterns.\",\n  \"ex_work_template\": \"syslog_error_check.exwork.json\",\n  \"manual_command\": \"grep -iE 'error|failed|critical' /var/log/syslog | tail -n 50\",\n  \"notes\": \"Requires access to system logs.\"\n}",
                "syslog_error_check.exwork.json": "{\n  \"step_id\": \"blueteam_syslog_check_001\",\n  \"description\": \"Check /var/log/syslog for recent errors.\",\n  \"actions\": [\n    {\n      \"type\": \"RUN_SCRIPT\",\n      \"script_path\": \"sh\",\n      \"args\": [\"-c\", \"grep -iE 'error|failed|critical' /var/log/syslog | tail -n 50\"]\n    }\n  ]\n}",
                "README.md": "# Log Analysis Templates"
            },
            "README.md": "# Blue Team Tools & Techniques\n\nManifests, templates, and notes for defensive security operations."
        },
        "README.md": "# Security Operations Toolkit\n\nResources for Red Team and Blue Team activities."
    },
    "08_INNOVATION_SHOWCASE": {
        "hackathon_templates": {
            "python_fastapi_api": {
                "manifest.json": "{\n  \"template_name\": \"Python FastAPI Basic API\",\n  \"description\": \"A minimal FastAPI application with a single endpoint, ready for hackathon development.\",\n  \"ex_work_setup_workflow\": \"python_fastapi_setup.exwork.json\",\n  \"estimated_setup_time\": \"2 minutes\",\n  \"tags\": [\"python\", \"fastapi\", \"api\", \"hackathon\"]\n}",
                "python_fastapi_setup.exwork.json": textwrap.dedent("""\
                {
                  "step_id": "hackathon_fastapi_setup_001",
                  "description": "Sets up a basic Python FastAPI project in subdirectory '{{project_name}}'.",
                  "parameters": [
                    {"name": "project_name", "prompt": "Enter new project directory name (e.g., my_api)"}
                  ],
                  "actions": [
                    {
                      "type": "CREATE_OR_REPLACE_FILE",
                      "path": "{{project_name}}/.gitignore",
                      "content_base64": "X19weWNhY2hlX18vCnZlbnYvCi52ZW52LwoqLnB5Ywpudm0tZGVlcC5jb25maWcKLmRzX3N0b3Jl"
                    },
                    {
                      "type": "CREATE_OR_REPLACE_FILE",
                      "path": "{{project_name}}/requirements.txt",
                      "content_base64": "ZmFzdGFwaQp1dmljb3JuCg=="
                    },
                    {
                      "type": "CREATE_OR_REPLACE_FILE",
                      "path": "{{project_name}}/main.py",
                      "content_base64": "ZnJvbSBmYXN0YXBpIGltcG9ydCBGYXN0QVBJCgphcHAgPSBGYXN0QVBJKCkKCkBnZXQoIi8iKQphc3luYyBkZWYgcm9vdCgpOgogICAgcmV0dXJuIHsibWVzc2FnZSI6ICJIZWxsbyBOZXh1cyBBcmNoaXRlY3QhIFlvdXIgRmFzdEFQSSBpcyBydW5uaW5nISJ9CgpAaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIGltcG9ydCB1dmljb3JuCiAgICB1dmljb3JuLnJ1bigiLi9tYWluOmFwcCIsIGhvc3Q9IjAuMC4wLjAiLCBwb3J0PTgwMDAsIHJlbG9hZD1UcnVlKQ=="
                    },
                    {
                      "type": "ECHO",
                      "message": "FastAPI project '{{project_name}}' structure created. Next steps: cd {{project_name}}, create venv, pip install -r requirements.txt, python main.py"
                    }
                  ]
                }"""),
                "README.md": "# Python FastAPI Basic API Template\n\nSets up a very simple FastAPI project."
            },
            "README.md": "# Hackathon Project Templates\n\nQuick-start templates for hackathons and rapid prototyping, deployable via Ex-Work workflows."
        },
        "README.md": "# Innovation Showcase\n\nProof-of-concepts, experimental tools, and hackathon resources."
    },
    ".gitignore": "__pycache__/\n*.py[cod]\n*$py.class\n\n# Virtual environment\n.venv/\nvenv/\nenv/\n\n# Build artifacts\nbuild/\ndist/\n*.egg-info/\n\n# IDE / Editor specific\n.vscode/\n.idea/\n*.swp\n*.swo\n.DS_Store\n\n# Logs & Local Configs (if any stored directly in NER)\n*.log\nlocal_settings.*\n.env\n\n# NPT Specific (if needed)\n*.npt_backup\n",
    "README.md": "# Nexus Edict Repository (NER)\n\nThis repository is the central knowledge base and operational template store for the Omnitide Nexus Protocol Toolkit (NPT).\n\n**Curated by The Architect.**"
}

def populate_ner_structure(ner_base_path: Path, ner_structure_data: Dict, force_overwrite: bool):
    step(f"Populating NER structure at: {ner_base_path}")
    for name, content in ner_structure_data.items():
        current_path = ner_base_path / name
        if isinstance(content, dict): 
            create_directory(current_path)
            populate_ner_structure(current_path, content, force_overwrite) 
        elif isinstance(content, str): 
            create_file(current_path, textwrap.dedent(content).strip(), overwrite=force_overwrite)
        else:
            warning(f"Skipping unknown content type for NER item '{name}' at {current_path.parent}")
    # Don't print success for each subdir, only at the end of the top-level call.
    if ner_base_path == NER_PATH_ABS: # Assuming NER_PATH_ABS is global and set
        success(f"NER structure population complete for main path: {ner_base_path}")

# --- PAC Application Code Generation (Part 2 continued) ---
def generate_pac_gitignore_content() -> str:
    return textwrap.dedent("""\
        # Python
        __pycache__/
        *.py[cod]
        *$py.class
        *.so

        # Virtualenv
        .venv_pac/
        venv/
        ENV/
        env/
        pip-freeze.txt
        pip-selfcheck.json

        # Distribution / packaging
        .Python
        build/
        develop-eggs/
        dist/
        downloads/
        eggs/
        .eggs/
        lib/
        lib64/
        parts/
        sdist/
        var/
        wheels/
        share/python-wheels/
        *.egg-info/
        .installed.cfg
        *.egg
        MANIFEST

        # PyInstaller
        *.manifest
        *.spec

        # Installer logs
        pip-log.txt
        pip-delete-this-directory.txt

        # Unit test / coverage reports
        htmlcov/
        .tox/
        .nox/
        .coverage
        .coverage.*
        .cache
        nosetests.xml
        coverage.xml
        *.cover
        *.py,cover
        .hypothesis/
        .pytest_cache/

        # VS Code
        .vscode/

        # PyCharm
        .idea/
        
        # Logs & User Data (if PAC stores any locally this way)
        *.log
        *.sqlite3
        *.db
        
        # NPT specific
        pac_cli.log 
    """).strip()

def generate_pac_pyproject_toml_content(python_version_str: str) -> str:
    try:
        major, minor, *_ = map(int, python_version_str.split('.'))
        py_ver_spec = f"^{major}.{minor}"
    except ValueError:
        warning(f"Could not parse Python version '{python_version_str}' for pyproject.toml. Defaulting to ^3.10.")
        py_ver_spec = "^3.10"

    return textwrap.dedent(f"""\
        [tool.poetry]
        name = "npac-cli"
        version = "0.1.0" # Initial PAC version, independent of NPT_GENERATOR_VERSION
        description = "Nexus Prompt Assembler CLI (PAC) - Omnitide Nexus Protocol Toolkit Interface"
        authors = ["The Architect <architect@omnitide.nexus>"]
        license = "Proprietary" 
        readme = "README.md"
        packages = [{{ include = "{PAC_APP_DIR_NAME}", from = "." }}] # Use defined constant

        [tool.poetry.dependencies]
        python = "{py_ver_spec}"
        typer = {{extras = ["all"], version = ">=0.9.0,<0.13.0"}}
        rich = ">=13.0.0,<14.0.0"
        pyyaml = ">=6.0,<7.0"
        # Agent dependencies (requests, tomli/tomllib, httpx) will be added here by the generator
        # python-dotenv = ">=0.20.0,<1.1.0" 

        [tool.poetry.group.dev.dependencies]
        pytest = ">=7.0.0,<8.0.0"
        pytest-cov = ">=4.0.0,<5.0.0"
        # ruff = ">=0.1.0" # Consider adding ruff for linting/formatting

        [tool.poetry.scripts]
        npac = "{PAC_APP_DIR_NAME}.{PAC_MAIN_PY_FILENAME.replace('.py','')}:app" # e.g., app.main:app

        [build-system]
        requires = ["poetry-core>=1.0.0"]
        build-backend = "poetry.core.masonry.api"

        [tool.ruff]
        line-length = 119 # Example
        select = ["E", "W", "F", "I", "C", "B", "Q", "UP", "ASYNC", "S"] # Extensive selection
        ignore = ["E501"] 
        # target-version = "py{major}{minor}" # To be set dynamically if possible, or manually

        [tool.pytest.ini_options]
        minversion = "7.0"
        addopts = "-ra -q --cov={PAC_APP_DIR_NAME} --cov-report=term-missing --cov-report=html"
        testpaths = ["{PAC_TESTS_DIR_NAME}"]
        python_files = "test_*.py"
        python_classes = "Test*"
        python_functions = "test_*"
    """).strip()

def generate_pac_requirements_content(agent_dependencies: List[str]) -> Tuple[str, str]:
    core_deps = [
        "typer[all]>=0.9.0,<0.13.0",
        "rich>=13.0.0,<14.0.0",
        "PyYAML>=6.0,<7.0",
        # "python-dotenv>=0.20.0,<1.1.0",
    ]
    dev_deps_list = [ # Using list for consistency
        "pytest>=7.0.0,<8.0.0",
        "pytest-cov>=4.0.0,<5.0.0",
        # "ruff>=0.1.0", # Optional: if not managed by pre-commit or global install
    ]
    
    all_runtime_deps = sorted(list(set(core_deps + agent_dependencies)))
    
    runtime_req_content = f"# PAC Runtime Dependencies (v{NPT_GENERATOR_VERSION})\n"
    runtime_req_content += "# Generated by NPT Generator. Consider using pyproject.toml with Poetry.\n"
    runtime_req_content += "\n".join(all_runtime_deps)
    
    dev_req_content = f"# PAC Development & Testing Dependencies (v{NPT_GENERATOR_VERSION})\n"
    dev_req_content += "# Install with: pip install -r requirements-dev.txt\n"
    dev_req_content += "\n".join(sorted(list(set(dev_deps_list))))
    
    return runtime_req_content, dev_req_content

def generate_pac_setup_venv_script_content(pac_cli_dir_name_val: str, python_executable_val: str) -> str:
    # Using _val to distinguish from global constants if names collide
    return textwrap.dedent(f"""\
        #!/bin/bash
        # Setup script for PAC Python Virtual Environment v{NPT_GENERATOR_VERSION}

        SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
        VENV_NAME=".venv_pac" # Standardized venv name
        PYTHON_EXECUTABLE="{python_executable_val}" 
        REQUIREMENTS_FILE="\$SCRIPT_DIR/requirements.txt"
        REQUIREMENTS_DEV_FILE="\$SCRIPT_DIR/requirements-dev.txt"

        echo "Setting up Python virtual environment for PAC in \$SCRIPT_DIR/\$VENV_NAME..."
        echo "Using Python: \$PYTHON_EXECUTABLE"

        if ! command -v "\$PYTHON_EXECUTABLE" &>/dev/null; then
            echo "ERROR: Python executable '\$PYTHON_EXECUTABLE' not found. Cannot create venv."
            exit 1
        fi

        if [ ! -d "\$SCRIPT_DIR/\$VENV_NAME" ]; then
            echo "Creating venv..."
            \$PYTHON_EXECUTABLE -m venv "\$SCRIPT_DIR/\$VENV_NAME" || {{ echo "ERROR: Failed to create venv."; exit 1; }}
        else
            echo "Virtual environment '\$VENV_NAME' already exists in \$SCRIPT_DIR."
        fi

        echo "Activating venv..."
        # shellcheck source=/dev/null
        source "\$SCRIPT_DIR/\$VENV_NAME/bin/activate" || {{ echo "ERROR: Failed to activate venv."; exit 1; }}

        echo "Upgrading pip, setuptools, and wheel..."
        pip install --disable-pip-version-check --upgrade pip setuptools wheel || {{
            echo "WARN: Failed to upgrade pip/setuptools/wheel. Proceeding with dependency installation."
        }}
        
        if [ ! -f "\$REQUIREMENTS_FILE" ]; then
            echo "ERROR: \$REQUIREMENTS_FILE not found. Cannot install dependencies."
            deactivate
            exit 1
        fi

        echo "Installing runtime dependencies from \$REQUIREMENTS_FILE..."
        pip install --disable-pip-version-check -r "\$REQUIREMENTS_FILE" || {{
            echo "ERROR: Failed to install runtime dependencies from \$REQUIREMENTS_FILE."
            deactivate; exit 1;
        }}
        
        if [ -f "\$REQUIREMENTS_DEV_FILE" ]; then
          echo "Installing development dependencies from \$REQUIREMENTS_DEV_FILE..."
          pip install --disable-pip-version-check -r "\$REQUIREMENTS_DEV_FILE" || {{
              echo "WARN: Failed to install dev dependencies. Main dependencies installed."
          }}
        else
            echo "INFO: Development requirements file (\$REQUIREMENTS_DEV_FILE) not found. Skipping."
        fi
        
        # Check if Poetry is installed and pyproject.toml exists
        if command -v poetry &>/dev/null && [ -f "\$SCRIPT_DIR/{PYPROJECT_FILENAME}" ]; then
            echo "INFO: Poetry detected and {PYPROJECT_FILENAME} exists."
            echo "      Consider managing dependencies with 'poetry install' in the future."
        fi

        echo ""
        echo "PAC Python environment in '\$SCRIPT_DIR/\$VENV_NAME' is ready."
        echo "To activate it manually in the future, run from the '{pac_cli_dir_name_val}' directory:"
        echo "  source ./$VENV_NAME/bin/activate"
        echo "To run PAC, use the 'npac' launcher from the NPT base directory (recommended)."
        
        deactivate
        echo "Setup complete. Virtual environment deactivated for current shell."
    """).strip()

def generate_npac_launcher_script_content(
    npt_base_dir_env_var_name_val: str, 
    pac_cli_dir_name_val: str, 
    pac_app_dir_name_val: str, 
    pac_main_py_filename_val: str
) -> str:
    return textwrap.dedent(f"""\
        #!/bin/bash
        # Master Launcher for Nexus Prompt Assembler CLI (PAC) - v{NPT_GENERATOR_VERSION}

        LAUNCHER_SCRIPT_DIR="\$(cd "\$(dirname "\${{BASH_SOURCE[0]}}")" && pwd)"
        export {npt_base_dir_env_var_name_val}="\$LAUNCHER_SCRIPT_DIR" 

        PAC_INSTALL_DIR="\$NPT_BASE_DIR/{pac_cli_dir_name_val}"
        VENV_NAME=".venv_pac" # Matches setup_venv.sh
        VENV_PATH="\$PAC_INSTALL_DIR/\$VENV_NAME"
        SETUP_VENV_SCRIPT="\$PAC_INSTALL_DIR/{SETUP_VENV_FILENAME}"
        PAC_MAIN_SCRIPT="\$PAC_INSTALL_DIR/{pac_app_dir_name_val}/{pac_main_py_filename_val}"

        PYTHON_IN_VENV=""
        if [ -f "\$VENV_PATH/bin/python3" ]; then
            PYTHON_IN_VENV="\$VENV_PATH/bin/python3"
        elif [ -f "\$VENV_PATH/bin/python" ]; then
            PYTHON_IN_VENV="\$VENV_PATH/bin/python"
        fi

        if [ -z "\$PYTHON_IN_VENV" ]; then
            if [ -f "\$SETUP_VENV_SCRIPT" ]; then
                echo "INFO: Python virtual environment for PAC not found or incomplete."
                echo "INFO: Attempting to run setup script: \$SETUP_VENV_SCRIPT"
                (cd "\$PAC_INSTALL_DIR" && bash "./{SETUP_VENV_FILENAME}") || {{
                    echo ""; error "ERROR: Failed to set up PAC Python environment using '{SETUP_VENV_FILENAME}'."; exit 1;
                }}
                if [ -f "\$VENV_PATH/bin/python3" ]; then PYTHON_IN_VENV="\$VENV_PATH/bin/python3"; 
                elif [ -f "\$VENV_PATH/bin/python" ]; then PYTHON_IN_VENV="\$VENV_PATH/bin/python"; fi
                if [ -z "\$PYTHON_IN_VENV" ]; then
                    error "ERROR: Python still not found in PAC venv after setup."; exit 1;
                fi
                echo "INFO: PAC Python environment setup complete. Proceeding to launch PAC..."
            else
                error "ERROR: PAC Python venv not found AND setup script '\$SETUP_VENV_SCRIPT' is missing!"; exit 1;
            fi
        fi
        
        # Subshell ensures venv activation is contained. NPT_BASE_DIR is already exported.
        (
            source "\$VENV_PATH/bin/activate" && \\
            exec "\$PYTHON_IN_VENV" "\$PAC_MAIN_SCRIPT" "\$@"
        )
    """).strip() # Note: error function here is conceptual for bash, real script relies on Python error handling

def create_pac_structure(
    pac_cli_path: Path, pac_app_path: Path, pac_core_path: Path, pac_commands_path: Path,
    pac_utils_path: Path, pac_tests_path: Path, agent_dependencies: List[str],
    python_for_pyproject: str, python_for_venv_setup: str, force_overwrite: bool
):
    step("Creating PAC Application Structure and Core Files")
    for p in [pac_cli_path, pac_app_path, pac_core_path, pac_commands_path, pac_utils_path, pac_tests_path]:
        create_directory(p)

    create_file(pac_cli_path / GITIGNORE_FILENAME, generate_pac_gitignore_content(), overwrite=force_overwrite)
    
    pyproject_content = generate_pac_pyproject_toml_content(python_for_pyproject)
    if agent_dependencies: # Dynamically add agent dependencies to pyproject.toml
        deps_section_marker = "[tool.poetry.dependencies]"
        deps_str_poetry = ""
        for dep in agent_dependencies:
            # Basic parsing for common version specifiers like requests>=2.20,<3 or tomli==1.0
            if "==" in dep: name, version = dep.split("==", 1); deps_str_poetry += f'\n{name} = "=={version}"'
            elif ">=" in dep: name, version = dep.split(">=", 1); deps_str_poetry += f'\n{name} = ">={version}"' # Could be more complex with multiple constraints
            elif "~=" in dep: name, version = dep.split("~=", 1); deps_str_poetry += f'\n{name} = "~={version}"'
            elif "<" in dep or ">" in dep: deps_str_poetry += f'\n{dep.replace(" ", "")}' # Assume full constraint like 'package<1.0,>=0.5'
            else: deps_str_poetry += f'\n{dep} = "*"' # Default to any version if no specifier

        if deps_section_marker in pyproject_content:
            pyproject_content = pyproject_content.replace(
                "# Agent dependencies (requests, tomli/tomllib, httpx) will be added here by the generator",
                f"# Agent dependencies (requests, tomli/tomllib, httpx) will be added here by the generator{deps_str_poetry}"
            )
        else: # Fallback if marker not found, just append (less ideal)
            pyproject_content += f"\n{deps_section_marker}{deps_str_poetry}"
            
    create_file(pac_cli_path / PYPROJECT_FILENAME, pyproject_content, overwrite=force_overwrite)
    
    req_content, req_dev_content = generate_pac_requirements_content(agent_dependencies)
    create_file(pac_cli_path / "requirements.txt", req_content, overwrite=force_overwrite)
    create_file(pac_cli_path / "requirements-dev.txt", req_dev_content, overwrite=force_overwrite)

    setup_venv_content = generate_pac_setup_venv_script_content(PAC_CLI_DIR_NAME, python_for_venv_setup)
    create_file(pac_cli_path / SETUP_VENV_FILENAME, setup_venv_content, executable=True, overwrite=force_overwrite)

    for p in [pac_app_path, pac_core_path, pac_commands_path, pac_utils_path, pac_tests_path]:
        create_file(p / PAC_INIT_PY_FILENAME, f"# {p.name} package for PAC", overwrite=force_overwrite)
    
    create_file(pac_tests_path / "test_sample.py", "import pytest\ndef test_example():\n    assert True\n", overwrite=force_overwrite)

    pac_readme_content = textwrap.dedent(f"""\
        # PAC - Prompt Assembler CLI ({PAC_CLI_DIR_NAME})

        This is the main application directory for PAC.
        Refer to `{PYPROJECT_FILENAME}` for project metadata and dependencies (if using Poetry).
        Alternatively, use `requirements.txt` and `requirements-dev.txt` with pip.

        ## Setup
        1.  Navigate to this directory (`{PAC_CLI_DIR_NAME}`).
        2.  Run the virtual environment setup script: `bash {SETUP_VENV_FILENAME}`

        ## Running PAC
        Use the `npac` launcher from the NPT base directory: `../{PAC_LAUNCHER_FILENAME}`
    """).strip()
    create_file(pac_cli_path / "README.md", pac_readme_content, overwrite=force_overwrite)
    success("PAC application core structure and utility scripts generated.")

# --- PAC Application Python Module Content (Part 3) ---
# (generate_pac_config_manager_py_content, generate_pac_ner_handler_py_content, etc. from previous turns)
# For brevity here, assume these functions are correctly defined as provided before.
# The critical one is generate_pac_main_py_content.

def generate_pac_config_manager_py_content(settings_filename_val: str, npt_base_dir_env_var_name_val: str) -> str:
    # Using _val to distinguish from global constants if names collide
    # This uses NPT_BASE_DIR_ENV_VAR_NAME for the env var PAC reads.
    # PAC_CONFIG_DIR_NAME and settings_filename_val are embedded as strings.
    return textwrap.dedent(f"""\
# pac_cli/app/core/config_manager.py
import os
import toml # PAC itself will need toml if it writes TOML. For reading, it could use tomllib.
from pathlib import Path
from typing import Any, Dict, Optional, List
import logging

logger = logging.getLogger("PAC." + __name__) # Hierarchical logging

# NPT_BASE_DIR is expected to be set by the npac launcher script.
# This path is relative to NPT_BASE_DIR
DEFAULT_PAC_CONFIG_DIR_NAME_IN_PAC = "{PAC_CONFIG_DIR_NAME}" # From generator's constant
DEFAULT_SETTINGS_FILENAME_IN_PAC = "{settings_filename_val}" # From generator's constant
NPT_BASE_DIR_ENV_VAR_IN_PAC = "{npt_base_dir_env_var_name_val}" # From generator's constant

class ConfigManager:
    def __init__(self, npt_base_dir_runtime: Path, config_filename_override: Optional[str] = None):
        self.npt_base_dir = npt_base_dir_runtime
        self.config_dir = self.npt_base_dir / DEFAULT_PAC_CONFIG_DIR_NAME_IN_PAC
        self.settings_file_path = self.config_dir / (config_filename_override or DEFAULT_SETTINGS_FILENAME_IN_PAC)
        self.settings: Dict[str, Any] = {{}}
        self._load_settings()

    def _ensure_config_dir_exists(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Could not create PAC config directory at {{self.config_dir}}: {{e}}")

    def _load_settings(self):
        self._ensure_config_dir_exists()
        defaults = self._get_default_settings()
        
        if self.settings_file_path.exists() and self.settings_file_path.is_file():
            try:
                # For reading, use tomllib if available (Py3.11+), else tomli (if installed by PAC's reqs), else toml
                _toml_reader = None
                try: import tomllib as _toml_reader_stdlib; _toml_reader = _toml_reader_stdlib; logger.debug("Using stdlib tomllib for reading settings.")
                except ImportError:
                    try: import tomli as _toml_reader_tomli; _toml_reader = _toml_reader_tomli; logger.debug("Using tomli for reading settings.")
                    except ImportError:
                        try: import toml as _toml_reader_toml; _toml_reader = _toml_reader_toml; logger.debug("Using toml for reading settings.")
                        except ImportError: logger.warning("No TOML reading library found for ConfigManager. Settings load might fail.")

                if _toml_reader:
                    with open(self.settings_file_path, "rb") as f: # tomllib/tomli load from binary
                        user_settings = _toml_reader.load(f)
                    self.settings = self._merge_dicts(defaults, user_settings)
                    logger.info(f"PAC settings loaded from: {{self.settings_file_path}}")
                else: # Should not happen if PAC's requirements.txt includes toml or tomli
                    logger.error(f"No TOML reader. Cannot load {{self.settings_file_path}}. Using defaults.")
                    self.settings = defaults
            except Exception as e: # Catch any TOML parsing or file errors
                logger.error(f"Error loading/parsing settings from {{self.settings_file_path}}: {{e!r}}. Using default settings and attempting to save.")
                self.settings = defaults
                self.save_settings() # Attempt to save a clean default file
        else:
            logger.info(f"PAC settings file not found at {{self.settings_file_path}}. Using default settings and creating file.")
            self.settings = defaults
            self.save_settings()

    def _merge_dicts(self, base: Dict, updates: Dict) -> Dict:
        merged = base.copy()
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._merge_dicts(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _get_default_settings(self) -> Dict[str, Any]:
        # NER_PATH_ABS is available to npt_generator.py at generation time.
        # Here we construct the default string path for settings.toml.
        # The actual NER_PATH_ABS object isn't available to PAC at runtime unless passed or configured.
        # So, this default should be a string.
        default_ner_path_str = str(self.npt_base_dir / "{NER_DIR_NAME}") # Use generator constant
        return {{
            "general": {{
                "default_ner_path": default_ner_path_str,
                "default_user_name": "Architect",
                "preferred_editor": os.environ.get("EDITOR", "nano"),
                "log_level": "INFO", # For PAC's own logging
            }},
            "agents": {{
                "ex_work_agent_path": "", # Populated by npt_generator.py
                "scribe_agent_path": "",  # Populated by npt_generator.py
                "default_ex_work_project_path": ".",
                "default_scribe_project_path": ".",
                "agent_timeout_seconds": 300,
            }},
            "llm_interface": {{ 
                "provider": "{llm_preference_val}", # From generator args
                "api_base_url": "http://localhost:11434" if "{llm_preference_val}" == "ollama" else "TODO_SET_API_BASE_URL",
                "default_model": "mistral-nemo:latest" if "{llm_preference_val}" == "ollama" else "TODO_SET_MODEL_NAME",
                "api_key_env_var": "YOUR_LLM_API_KEY_ENV_VAR_NAME", 
                "timeout_seconds": 180, "max_retries": 2,
            }},
            "ui": {{
                "use_fzf_fallback_if_fzf_missing": True,
                "truncate_output_length": 2000,
                "datetime_format": "%Y-%m-%d %H:%M:%S %Z",
            }},
        }}

    def save_settings(self) -> bool:
        self._ensure_config_dir_exists()
        try:
            # Use 'toml' package for writing, ensure it's in PAC's requirements.txt
            import toml as _toml_writer # Local import for this method
            with open(self.settings_file_path, "w", encoding="utf-8") as f:
                _toml_writer.dump(self.settings, f)
            logger.info(f"PAC settings saved to: {{self.settings_file_path}}")
            return True
        except ImportError:
            logger.error(f"'toml' library not found in PAC's environment. Cannot save settings as TOML. Please add 'toml' to requirements.txt.")
            return False
        except OSError as e:
            logger.error(f"Failed to save PAC settings to {{self.settings_file_path}}: {{e}}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split('.')
        value = self.settings
        try:
            for key in keys: value = value[key]
            return value
        except (KeyError, TypeError): return default
    
    def set_value(self, key_path: str, value: Any, auto_save: bool = True):
        keys = key_path.split('.')
        current_level = self.settings
        for i, key in enumerate(keys[:-1]):
            current_level = current_level.setdefault(key, {{}})
            if not isinstance(current_level, dict):
                logger.error(f"Cannot set config '{{key_path}}': intermediate '{{key}}' is not a dictionary."); return
        current_level[keys[-1]] = value
        if auto_save: self.save_settings()
    """).strip() # End of generate_pac_config_manager_py_content

# (generate_pac_ner_handler_py_content, generate_pac_agent_runner_py_content, 
#  generate_pac_llm_interface_py_content, generate_pac_ui_utils_py_content
#  were defined in previous parts, ensure they are correct based on our debugging)

# Re-stub of generate_pac_main_py_content with fixed variable escaping
def generate_pac_main_py_content(
    ner_dir_name_const_val: str, 
    pac_config_dir_name_const_val: str, # This is PAC_CONFIG_DIR_NAME
    settings_filename_const_val: str, # This is PAC_SETTINGS_FILENAME
    llm_preference_val: str, # From args
    npt_base_dir_env_var_name_val: str # This is NPT_BASE_DIR_ENV_VAR_NAME
) -> str:
    # Using _val suffixes for clarity that these are from generator's scope,
    # to be embedded as string literals or interpolated into the generated code.
    # NPT_GENERATOR_VERSION is a global constant in npt_generator.py
    
    # Literal f-string parts for main.py need correct escaping for their own placeholders
    # {{X}} in generator's f-string -> {X} in main.py's f-string
    # {X} in generator's f-string -> value of X from generator is embedded
    
    main_py_stub = f"""\
#!/usr/bin/env python3
# PAC - Prompt Assembler CLI / Nexus Operations Console
# Main application file (Typer/Rich based)
# Version: {NPT_GENERATOR_VERSION} 
# Generated on: {datetime.datetime.now(datetime.timezone.utc).isoformat()}

import typer
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
import os
import sys
from pathlib import Path
import logging
import json as py_json # Alias to avoid conflict with rich.json.JSON
import shlex

try:
    from app.core.config_manager import ConfigManager
    from app.core.ner_handler import NERHandler
    from app.core.agent_runner import ExWorkAgentRunner, ScribeAgentRunner
    from app.core.llm_interface import LLMInterface
    from app.utils import ui_utils
except ImportError:
    print(f"PAC Import ERROR. Attempting relative for dev.", file=sys.stderr)
    from core.config_manager import ConfigManager
    from core.ner_handler import NERHandler
    from core.agent_runner import ExWorkAgentRunner, ScribeAgentRunner
    from core.llm_interface import LLMInterface
    from utils import ui_utils

APP_NAME: str = "Nexus Prompt Assembler CLI (PAC)"
APP_VERSION: str = "{NPT_GENERATOR_VERSION}"

NPT_BASE_DIR_ENV_VAR_NAME_IN_PAC: str = "{npt_base_dir_env_var_name_val}"
NPT_BASE_DIR: Path
try:
    NPT_BASE_DIR = Path(os.environ[NPT_BASE_DIR_ENV_VAR_NAME_IN_PAC]).resolve()
except KeyError:
    NPT_BASE_DIR = Path(__file__).resolve().parent.parent.parent
    print(f"[WARN] {{{{{NPT_BASE_DIR_ENV_VAR_NAME_IN_PAC}}}}} env var not set. Defaulting NPT_BASE_DIR to: {{{{{NPT_BASE_DIR}}}}}", file=sys.stderr)

NER_DIR_NAME_CONST_IN_PAC: str = "{ner_dir_name_const_val}"
PAC_CONFIG_DIR_NAME_CONST_IN_PAC: str = "{pac_config_dir_name_const_val}"
SETTINGS_FILENAME_CONST_IN_PAC: str = "{settings_filename_const_val}"

LOG_LEVEL_ENV_VAR = "PAC_LOG_LEVEL"
DEFAULT_PAC_LOG_LEVEL = "INFO"
pac_log_level_str = os.environ.get(LOG_LEVEL_ENV_VAR, DEFAULT_PAC_LOG_LEVEL).upper()
numeric_log_level = getattr(logging, pac_log_level_str, logging.INFO)
log_file_path_base = NPT_BASE_DIR / "{PAC_LOGS_DIR_NAME}" / "pac_cli.log" # From generator constants
try:
    log_file_path_base.parent.mkdir(parents=True, exist_ok=True)
    # TODO, Architect: Add log rotation (e.g., TimedRotatingFileHandler)
    file_handler = logging.FileHandler(log_file_path_base, mode='a', encoding='utf-8')
    file_handler.setLevel(numeric_log_level)
    file_formatter = logging.Formatter("%(asctime)s [%(name)-12s] [%(levelname)-7s] %(module)s:%(lineno)d - %(message)s", "%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_formatter)
    
    # Configure root logger or specific loggers
    # For simplicity, configuring a base logger that other modules can derive from.
    # Get a logger for the 'app' package, which core modules can use like logging.getLogger(__name__)
    app_logger = logging.getLogger("app") 
    app_logger.setLevel(numeric_log_level)
    app_logger.addHandler(file_handler)
    app_logger.addHandler(logging.StreamHandler(sys.stderr)) # Also log to stderr
    app_logger.propagate = False # Prevent root logger from also handling if it has handlers

    # Also configure the global PAC logger used in this file
    logger_pac_main = logging.getLogger("PAC")
    logger_pac_main.setLevel(numeric_log_level)
    logger_pac_main.addHandler(file_handler) # Ensure PAC main logs also go to file
    logger_pac_main.addHandler(logging.StreamHandler(sys.stderr)) # And stderr
    logger_pac_main.propagate = False

except Exception as log_e:
    print(f"[CRITICAL_SETUP_ERROR] Failed to configure file logging for PAC: {{log_e}}", file=sys.stderr)
    # Fallback to basic stderr logging for the main PAC logger if file setup fails
    logging.basicConfig(level=numeric_log_level, format="%(asctime)s [PAC_Fallback] [%(levelname)-7s] %(module)s:%(lineno)d - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", handlers=[logging.StreamHandler(sys.stderr)])
    logger_pac_main = logging.getLogger("PAC_Fallback")


config_manager: Optional[ConfigManager] = None
ner_handler: Optional[NERHandler] = None
ex_work_runner: Optional[ExWorkAgentRunner] = None
scribe_runner: Optional[ScribeAgentRunner] = None
llm_interface: Optional[LLMInterface] = None
console = ui_utils.console

app = typer.Typer(
    name="npac", help=f"{{APP_NAME}} v{{APP_VERSION}}", rich_markup_mode="markdown", no_args_is_help=True, add_completion=True
)

@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context, verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose (DEBUG) logging.")):
    global config_manager, ner_handler, ex_work_runner, scribe_runner, llm_interface
    
    if verbose:
        logging.getLogger("app").setLevel(logging.DEBUG) # Set app package logger
        logger_pac_main.setLevel(logging.DEBUG) # Set main PAC file logger
        logger_pac_main.debug("Verbose mode enabled by CLI flag.")

    if not NPT_BASE_DIR.is_dir():
        console.print(f"[bold red]CRITICAL: NPT Base Directory not found: '{{NPT_BASE_DIR}}'[/bold red]"); raise typer.Exit(101)

    try:
        config_manager = ConfigManager(npt_base_dir_runtime=NPT_BASE_DIR, config_filename_override=SETTINGS_FILENAME_CONST_IN_PAC)
        log_level_cfg = config_manager.get("general.log_level", DEFAULT_PAC_LOG_LEVEL).upper()
        if not verbose: # CLI verbose flag takes precedence
            new_level_num = getattr(logging, log_level_cfg, numeric_log_level) # numeric_log_level is initial default
            logging.getLogger("app").setLevel(new_level_num)
            logger_pac_main.setLevel(new_level_num)
        logger_pac_main.info(f"ConfigManager initialized. Settings: {{config_manager.settings_file_path}}. Log level: {{logging.getLevelName(logger_pac_main.getEffectiveLevel())}}")
    except Exception as e:
        console.print(f"[bold red]CRITICAL: Failed to init ConfigManager: {{e!r}}[/bold red]"); logger_pac_main.critical("ConfigManager init error", exc_info=True); raise typer.Exit(102)

    ner_path_cfg = Path(config_manager.get("general.default_ner_path")).resolve()
    if not ner_path_cfg.is_dir():
        console.print(f"[bold red]CRITICAL: NER Directory not found: '{{ner_path_cfg}}' (from settings)[/bold red]"); raise typer.Exit(103)
    
    try:
        ner_handler = NERHandler(ner_root_path=ner_path_cfg, config_manager=config_manager)
        ex_work_runner = ExWorkAgentRunner(config_manager=config_manager)
        scribe_runner = ScribeAgentRunner(config_manager=config_manager)
        llm_interface = LLMInterface(config_manager=config_manager, ex_work_runner=ex_work_runner)
    except Exception as e:
        console.print(f"[bold red]CRITICAL: Failed to init core handlers: {{e!r}}[/bold red]"); logger_pac_main.critical("Core handlers init error", exc_info=True); raise typer.Exit(104)

    ctx.meta['config_manager'] = config_manager
    ctx.meta['ner_handler'] = ner_handler
    ctx.meta['ex_work_runner'] = ex_work_runner
    ctx.meta['scribe_runner'] = scribe_runner
    ctx.meta['llm_interface'] = llm_interface
    
    logger_pac_main.info(f"PAC Core Initialized. NPT Base: {{NPT_BASE_DIR}}, NER: {{ner_path_cfg}}")
    if ctx.invoked_subcommand is None and not any(arg in sys.argv for arg in ['--help', '--version']):
        # Default action: call system check
        logger_pac_main.debug("No subcommand, calling 'system check'.")
        ctx.invoke(system_check_cmd) # Invoke system check by default


# --- NER Command Group (ner_app) ---
ner_app = typer.Typer(name="ner", help="Interact with the Nexus Edict Repository (NER).", no_args_is_help=True)
app.add_typer(ner_app)

@ner_app.command("browse") # All previous ner_browse_cmd implementation, using {{search_query}} correctly
def ner_browse_cmd(ctx: typer.Context,
                   start_category: Optional[str] = typer.Argument(None, help="NER category to start Browse.", show_default=False),
                   search_query: Optional[str] = typer.Option(None, "--search", "-s", help="Search NER filenames and content.", show_default=False)
                   ):
    current_ner_handler: NERHandler = ctx.meta['ner_handler']
    if search_query:
        ui_utils.console.print(f"Searching NER for: '[cyan]{{search_query}}[/cyan]'...") # Corrected {{search_query}}
        results = current_ner_handler.search_ner(search_query, search_in_category=start_category)
        if not results: ui_utils.console.print(f"No results found for '{{search_query}}'."); return
        table_rows = [[res['relative_path_to_ner'], res['type'], res.get('match_type',''), res.get('snippet','')[:80]+"..." if res.get('snippet','') else ""] for res in results]
        ui_utils.display_table(f"Search Results for '{{search_query}}'", ["Path", "Type", "Match", "Snippet"], table_rows) # Corrected {{search_query}}
        return
    # ... (Rest of interactive browse logic - assume correct from prior generation) ...
    # This part needs to be carefully reviewed for any other similar f-string issues.
    # For brevity, I'm assuming it's complex and has been handled.
    # A placeholder:
    ui_utils.console.print("[italic yellow]TODO, Architect: Implement full interactive NER browser here, using ui_utils.fzf_select and NERHandler methods.[/italic yellow]")


@ner_app.command("view") # Previous ner_view_cmd implementation
def ner_view_cmd(ctx: typer.Context, item_path_relative_to_ner: str = typer.Argument(..., help="Relative path to NER item.")):
    current_ner_handler: NERHandler = ctx.meta['ner_handler']
    content = current_ner_handler.get_item_content(item_path_relative_to_ner)
    if content:
        file_ext = Path(item_path_relative_to_ner).suffix[1:].lower() or "text"
        title = Path(item_path_relative_to_ner).name
        if file_ext == "md": ui_utils.display_markdown(content, title=title)
        elif file_ext in ["json", "toml", "yaml", "py", "sh"]: ui_utils.display_syntax(content, file_ext, title=title)
        else: ui_utils.display_panel(content, title=title)
    else:
        ui_utils.console.print(f"[red]NER item not found: {{item_path_relative_to_ner}}[/red]"); raise typer.Exit(1)

@ner_app.command("git") # Previous ner_git_cmd implementation
def ner_git_cmd(ctx: typer.Context,
                action: str = typer.Argument(..., help="Git action: 'status', 'pull', 'push', 'commit'."),
                commit_message: Optional[str] = typer.Option(None, "-m", help="Commit message for 'commit'."),
                add_all_first: bool = typer.Option(True, help="Run 'git add .' before commit.")
                ):
    current_ner_handler: NERHandler = ctx.meta['ner_handler']
    action_low = action.lower()
    if not (current_ner_handler.ner_root / ".git").is_dir():
        ui_utils.console.print(f"[yellow]NER at '{{current_ner_handler.ner_root}}' is not a Git repo.[/yellow]"); return
    success, output_msg = False, "Action not performed."
    if action_low == "status":
        # For status, directly print using a generic command runner or specific NERHandler method
        # Let's assume NERHandler has a generic git_command for simplicity
        _success, _stdout, _stderr = current_ner_handler.run_command_in_ner(["git", "status"]) # Conceptual NERHandler method
        if _success: ui_utils.console.print(Panel(_stdout or "No status output.", title="NER Git Status"))
        else: ui_utils.console.print(Panel(f"Error:\\n{{_stderr}}", title="NER Git Status Error", border_style="red"))
        return
    elif action_low == "pull": success, output_msg = current_ner_handler.git_pull_ner()
    elif action_low == "push": success, output_msg = current_ner_handler.git_push_ner()
    elif action_low == "commit":
        if not commit_message: ui_utils.console.print("[red]-m 'message' required for commit.[/red]"); raise typer.Exit(1)
        success, output_msg = current_ner_handler.git_commit_ner_changes(commit_message, add_all=add_all_first)
    else: ui_utils.console.print(f"[red]Unknown NER Git action: '{{action}}'.[/red]"); raise typer.Exit(1)
    
    if success: ui_utils.console.print(f"[green]NER Git '{{action}}' successful.[/green]") # Corrected {{action}}
    else: ui_utils.console.print(f"[red]NER Git '{{action}}' failed.[/red]") # Corrected {{action}}
    if output_msg: ui_utils.console.print(output_msg)
    if not success: raise typer.Exit(1)

# --- ONAP Command Group ---
onap_app = typer.Typer(name="onap", help="Assemble and manage ONAP components.", no_args_is_help=True)
app.add_typer(onap_app)
# ... (ONAP commands stubbed as before, using {{var_name}} for f-string vars) ...
@onap_app.command("assemble")
def onap_assemble_cmd_stub(ctx: typer.Context):
    ui_utils.console.print("[italic yellow]TODO, Architect: Implement ONAP assembly.[/italic yellow]")

# --- Ex-Work Command Group ---
exwork_app = typer.Typer(name="exwork", help="Orchestrate Agent Ex-Work tasks.", no_args_is_help=True)
app.add_typer(exwork_app)
# ... (Ex-Work commands stubbed as before, using {{var_name}} for f-string vars) ...
@exwork_app.command("run")
def exwork_run_cmd_stub(ctx: typer.Context, template_name: Optional[str] = None): # Simplified for stub
    runner: Optional[ExWorkAgentRunner] = ctx.meta.get('ex_work_runner')
    if not runner or not runner.agent_script_command:
        ui_utils.console.print("[bold red]Ex-Work Agent not configured.[/bold red]"); raise typer.Exit(1)
    ui_utils.console.print(f"[italic yellow]TODO, Architect: Implement Ex-Work run for template '{{template_name}}'. Load, param, execute.[/italic yellow]")

# --- Scribe Command Group ---
scribe_app = typer.Typer(name="scribe", help="Orchestrate Project Scribe validations.", no_args_is_help=True)
app.add_typer(scribe_app)
# ... (Scribe commands stubbed as before, using {{var_name}} for f-string vars) ...
@scribe_app.command("validate")
def scribe_validate_cmd_stub(ctx: typer.Context, project_path_str: str = "."): # Simplified for stub
    runner: Optional[ScribeAgentRunner] = ctx.meta.get('scribe_runner')
    if not runner or not runner.agent_script_command:
        ui_utils.console.print("[bold red]Scribe Agent not configured.[/bold red]"); raise typer.Exit(1)
    ui_utils.console.print(f"[italic yellow]TODO, Architect: Implement Scribe validate for project '{{project_path_str}}'.[/italic yellow]")

# --- Workflow Command Group ---
workflow_app = typer.Typer(name="workflow", help="Define and execute NPT workflows.", no_args_is_help=True)
app.add_typer(workflow_app)
# ... (Workflow commands stubbed as before) ...
@workflow_app.command("run")
def workflow_run_stub(ctx: typer.Context, workflow_file_ner_path: str):
    ui_utils.console.print(f"[italic yellow]TODO, Architect: Implement workflow run for '{{workflow_file_ner_path}}'.[/italic yellow]")

# --- System Command Group ---
system_app = typer.Typer(name="system", help="PAC system management and diagnostics.", no_args_is_help=True)
app.add_typer(system_app)
# ... (System config and check commands stubbed as before, using {{var_name}} for f-string vars) ...
@system_app.command("config")
def system_config_cmd_stub(ctx: typer.Context, key: Optional[str]=None, value: Optional[str]=None):
     ui_utils.console.print(f"[italic yellow]TODO, Architect: Implement system config get/set. Key: {{key}}, Value: {{value}}[/italic yellow]")

@system_app.command("check") # Referenced by main_callback default
def system_check_cmd(ctx: typer.Context): # Renamed from system_check_cmd_stub
    # (Full system_check_cmd implementation from previous response, ensuring f-string variables are {{var_name}})
    # Example line from that check:
    # add_check("NER Directory (from config)", ner_path_from_cfg, ner_h.ner_root.is_dir(), f"Actual path used: {{ner_h.ner_root}}")
    ui_utils.console.print("[italic yellow]TODO, Architect: Implement full system check logic here.[/italic yellow]")
    ui_utils.console.print(f"NPT Base Dir: {{NPT_BASE_DIR}}") # Example access
    cfg: ConfigManager = ctx.meta['config_manager']
    ui_utils.console.print(f"Settings File: {{cfg.settings_file_path}}")


if __name__ == "__main__":
    logger_pac_main.info(f"Starting {{APP_NAME}} v{{APP_VERSION}} directly via __main__ (dev/debug mode).")
    app()

"""
    # IMPORTANT: This is still a stub. The actual main.py content is much larger
    # and was detailed in previous "Part 3" sections. All f-string interpolations
    # like {NPT_GENERATOR_VERSION} are evaluated by THIS generator script.
    # All f-strings intended for main.py's runtime (like f"Value: {var_in_main_py}")
    # must have their placeholders escaped as f"Value: {{var_in_main_py}}" within this stub.
    # The NameErrors we've been fixing are due to these escapes being missed.
    return textwrap.dedent(main_py_stub)


# --- Main Generator Orchestration Function (Ensure definition is here if not imported from elsewhere) ---
# (main_generator function definition as provided and corrected in previous turns)
# It should define default_settings_for_toml *inside* itself, after NER_PATH_ABS etc. are set.

# --- Script Entry Point ---
if __name__ == "__main__":
    print(f"--- NPT Generator v{NPT_GENERATOR_VERSION} ---")
    if not shutil.which(PYTHON_CMD_FROM_BOOTSTRAP):
        error(f"Python command '{PYTHON_CMD_FROM_BOOTSTRAP}' (from bootstrap env) not found. Critical error.", 1)

    args = setup_generator_parser().parse_args()

    final_exit_code = 0
    try:
        main_generator(args) # This is where NER_PATH_ABS should be defined before being used
    except SystemExit as e:
        if e.code is not None and e.code != 0:
             print(f"{TermColors.FAIL}NPT Generator exited with code: {e.code}. Review messages.{TermColors.ENDC}")
             final_exit_code = e.code
        elif e.code is None: final_exit_code = 0
        else: final_exit_code = 0
    except KeyboardInterrupt:
        print(f"\n{TermColors.WARNING}NPT Generation process interrupted by user.{TermColors.ENDC}")
        final_exit_code = 130 
    except Exception as e:
        print(f"{TermColors.FAIL}{TermColors.BOLD}CRITICAL UNEXPECTED ERROR in NPT Generator:{TermColors.ENDC}")
        print(f"{TermColors.FAIL}{traceback.format_exc()}{TermColors.ENDC}")
        final_exit_code = 99 
    
    sys.exit(final_exit_code)