"""
HardwareIQ - CPU Detection Module
Safely retrieves and parses CPU hardware information using lscpu.
Compatible with Python 3.8+.
"""

from typing import Any, Dict, Optional
from utils.command_executor import run_safe_command


def parse_lscpu_output(raw_output: str) -> Dict[str, str]:
    """
    Parses key-value pairs from standard lscpu output.
    Format is typically: 'Key:    Value'
    """
    data = {}
    for line in raw_output.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, sep, val = line.partition(":")
        data[key.strip()] = val.strip()
    return data


def get_cpu_info() -> Dict[str, Any]:
    """
    Retrieves detailed CPU specifications using lscpu.
    Returns a consistent structured dictionary.
    """
    success, stdout, stderr = run_safe_command(["lscpu"])

    if not success:
        return {
            "status": "unavailable",
            "hardware_type": "cpu",
            "summary": "CPU information is currently unavailable.",
            "details": {},
            "error_message": f"Failed to execute lscpu: {stderr}"
        }

    raw = parse_lscpu_output(stdout)

    # Extract primary fields safely with fallbacks
    model_name = raw.get("Model name", "Unknown CPU Model")
    architecture = raw.get("Architecture", "Unknown Architecture")
    
    # Core & Thread counts
    try:
        total_cpus = int(raw.get("CPU(s)", "1"))
    except ValueError:
        total_cpus = 1

    try:
        threads_per_core = int(raw.get("Thread(s) per core", "1"))
    except ValueError:
        threads_per_core = 1

    try:
        cores_per_socket = int(raw.get("Core(s) per socket", "1"))
    except ValueError:
        cores_per_socket = 1

    try:
        sockets = int(raw.get("Socket(s)", "1"))
    except ValueError:
        sockets = 1

    # Clock speeds
    cpu_mhz = raw.get("CPU MHz")
    cpu_max_mhz = raw.get("CPU max MHz")
    cpu_min_mhz = raw.get("CPU min MHz")

    # Cache sizes
    l1d = raw.get("L1d cache")
    l1i = raw.get("L1i cache")
    l2 = raw.get("L2 cache")
    l3 = raw.get("L3 cache")

    # Virtualization & Hypervisor
    virt_type = raw.get("Virtualization type")
    hypervisor = raw.get("Hypervisor vendor")
    bogomips = raw.get("BogoMIPS")

    # Build human-readable summary
    summary_parts = [f"**{model_name}**"]
    summary_parts.append(f"({architecture}, {total_cpus} Logical CPU(s)")
    if cores_per_socket:
        summary_parts.append(f"- {cores_per_socket} Core(s)")
    summary_parts.append(")")
    summary = " ".join(summary_parts)

    details = {
        "model_name": model_name,
        "architecture": architecture,
        "total_cpus": total_cpus,
        "cores_per_socket": cores_per_socket,
        "threads_per_core": threads_per_core,
        "sockets": sockets,
        "cpu_mhz": float(cpu_mhz) if cpu_mhz else None,
        "cpu_max_mhz": float(cpu_max_mhz) if cpu_max_mhz else None,
        "cpu_min_mhz": float(cpu_min_mhz) if cpu_min_mhz else None,
        "l1d_cache": l1d or "Not reported",
        "l1i_cache": l1i or "Not reported",
        "l2_cache": l2 or "Not reported",
        "l3_cache": l3 or "Not reported",
        "virtualization_type": virt_type or "None/Bare-metal",
        "hypervisor_vendor": hypervisor or "None (Bare-metal)",
        "bogomips": bogomips or "Not reported",
        "raw_fields": raw
    }

    return {
        "status": "success",
        "hardware_type": "cpu",
        "summary": summary,
        "details": details,
        "error_message": None
    }


def format_cpu_markdown(cpu_data: Dict[str, Any]) -> str:
    """Formats CPU details into clean Markdown."""
    if cpu_data.get("status") != "success":
        return f"⚠️ **CPU Detection**: {cpu_data.get('error_message', 'Data unavailable')}"

    d = cpu_data["details"]
    lines = [
        f"### 🖥️ CPU Specifications",
        f"- **Model**: `{d['model_name']}`",
        f"- **Architecture**: `{d['architecture']}`",
        f"- **Total Logical CPUs**: `{d['total_cpus']}`",
        f"- **Physical Cores per Socket**: `{d['cores_per_socket']}`",
        f"- **Threads per Core**: `{d['threads_per_core']}`",
        f"- **Sockets**: `{d['sockets']}`",
    ]

    if d["cpu_mhz"]:
        lines.append(f"- **Current Frequency**: `{d['cpu_mhz']} MHz`")
    if d["cpu_max_mhz"]:
        lines.append(f"- **Max Frequency**: `{d['cpu_max_mhz']} MHz`")
    if d["cpu_min_mhz"]:
        lines.append(f"- **Min Frequency**: `{d['cpu_min_mhz']} MHz`")

    caches = []
    if d["l1d_cache"] != "Not reported":
        caches.append(f"L1d: {d['l1d_cache']}")
    if d["l1i_cache"] != "Not reported":
        caches.append(f"L1i: {d['l1i_cache']}")
    if d["l2_cache"] != "Not reported":
        caches.append(f"L2: {d['l2_cache']}")
    if d["l3_cache"] != "Not reported":
        caches.append(f"L3: {d['l3_cache']}")
    if caches:
        lines.append(f"- **Cache Hierarchy**: `{', '.join(caches)}`")

    if d["hypervisor_vendor"] != "None (Bare-metal)":
        lines.append(f"- **Hypervisor**: `{d['hypervisor_vendor']}` (Virtualization: `{d['virtualization_type']}`)")

    return "\n".join(lines)
