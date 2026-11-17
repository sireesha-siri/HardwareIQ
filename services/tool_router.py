"""
HardwareIQ - Local Question Routing Service
Parses natural language hardware questions and routes them to the appropriate
hardware tools without requiring Gemini or external network access.
Compatible with Python 3.8+.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from hardware.cpu import get_cpu_info, format_cpu_markdown
from hardware.memory import get_memory_info, format_memory_markdown
from hardware.storage import get_storage_info, format_storage_markdown
from hardware.gpu import get_gpu_info, format_gpu_markdown


# Keyword sets for intent classification
CPU_KEYWORDS = {
    "cpu", "processor", "core", "cores", "thread", "threads", "socket", "sockets",
    "mhz", "ghz", "clock", "frequency", "speed", "architecture", "x86", "x86_64",
    "arm", "cache", "l1", "l2", "l3", "lscpu", "bogomips", "hypervisor", "virtualization",
    "intel", "amd", "pentium", "ryzen", "xeon", "i3", "i5", "i7", "i9"
}

MEMORY_KEYWORDS = {
    "ram", "memory", "swap", "meminfo", "free memory", "used memory", "available memory",
    "cached", "buffers", "virtual_memory", "psutil", "gib of ram", "gb of ram",
    "oom", "paging"
}

STORAGE_KEYWORDS = {
    "storage", "disk", "disks", "drive", "drives", "harddrive", "hard drive", "ssd",
    "hdd", "nvme", "partition", "partitions", "mount", "mounts", "mountpoint", "lsblk",
    "filesystem", "sda", "sdb", "vda", "space", "capacity", "volume"
}

GPU_KEYWORDS = {
    "gpu", "gpus", "graphics", "video", "display", "vga", "3d", "card",
    "nvidia", "radeon", "geforce", "rtx", "gtx", "lspci", "cuda", "vram",
    "dedicated gpu", "discrete gpu", "integrated gpu", "igpu", "svga"
}

OVERVIEW_KEYWORDS = {
    "all", "system", "specs", "specifications", "summary", "overview",
    "hardware", "full", "everything", "pc", "machine", "device", "info", "report"
}


def classify_query(query: str) -> str:
    """
    Classifies a natural language query into one of:
    'cpu', 'memory', 'storage', 'gpu', 'overview', or 'unknown'.
    Uses tokenization, keyword matching, and regex scoring.
    """
    q = query.lower().strip()
    words = set(re.findall(r"\b[a-z0-9_-]+\b", q))

    # Check for direct overview intent
    overview_phrases = [
        "system specs", "hardware summary", "system info", "system overview",
        "full specs", "full hardware", "all specs", "about this machine",
        "tell me about this system", "specs of this pc", "what hardware"
    ]
    if any(phrase in q for phrase in overview_phrases) and not any(k in words for k in ["cpu only", "just ram"]):
        return "overview"

    # Score each hardware category
    cpu_score = len(words & CPU_KEYWORDS)
    mem_score = len(words & MEMORY_KEYWORDS)
    storage_score = len(words & STORAGE_KEYWORDS)
    gpu_score = len(words & GPU_KEYWORDS)
    overview_score = len(words & OVERVIEW_KEYWORDS)

    # Extra weight for key distinguishing phrases
    if any(k in q for k in ["processor", "lscpu", "clock speed", "how many cores", "cpu model"]):
        cpu_score += 3
    if any(k in q for k in ["how much ram", "memory usage", "free ram", "swap space"]):
        mem_score += 3
    if any(k in q for k in ["disk space", "hard drive", "how much storage", "show partitions", "lsblk"]):
        storage_score += 3
    if any(k in q for k in ["graphics card", "dedicated gpu", "display adapter", "what gpu"]):
        gpu_score += 3

    scores = [
        ("cpu", cpu_score),
        ("memory", mem_score),
        ("storage", storage_score),
        ("gpu", gpu_score),
    ]

    # Sort descending by score
    scores.sort(key=lambda x: x[1], reverse=True)
    best_intent, best_score = scores[0]

    if best_score > 0:
        return best_intent

    if overview_score > 0 or "what is this machine" in q:
        return "overview"

    return "unknown"


def synthesize_specific_answer(query: str, intent: str, data: Dict[str, Any]) -> str:
    """
    Constructs a direct, grounded answer addressing the specific query,
    followed by the formatted technical specifications.
    """
    q = query.lower()

    if intent == "cpu":
        d = data.get("details", {})
        cores = d.get("cores_per_socket", "Unknown")
        total_cpus = d.get("total_cpus", "Unknown")
        model = d.get("model_name", "Unknown CPU")
        arch = d.get("architecture", "Unknown")
        mhz = d.get("cpu_mhz", "Unknown")

        if any(w in q for w in ["core", "cores", "how many cores"]):
            direct_ans = f"This system is equipped with **{cores} physical core(s)** and **{total_cpus} logical thread(s)** on an **{model}**."
        elif any(w in q for w in ["frequency", "speed", "mhz", "ghz", "clock"]):
            direct_ans = f"The CPU **{model}** is currently operating at **{mhz} MHz**."
        elif any(w in q for w in ["architecture", "arch", "64-bit", "32-bit"]):
            direct_ans = f"The CPU architecture is **{arch}**."
        else:
            direct_ans = f"Detected CPU: **{model}** ({total_cpus} logical CPUs, {arch})."

        return f"{direct_ans}\n\n{format_cpu_markdown(data)}"

    elif intent == "memory":
        d = data.get("details", {})
        total = d.get("total_human", "Unknown")
        available = d.get("available_human", "Unknown")
        used = d.get("used_human", "Unknown")
        pct = d.get("percent_used", "Unknown")
        free = d.get("free_human", "Unknown")
        swap_total = d.get("swap_total_human", "0 B")
        swap_used = d.get("swap_used_human", "0 B")

        if any(w in q for w in ["available", "how much ram is available", "available ram"]):
            direct_ans = f"There is currently **{available} of memory available** for applications out of **{total} total physical RAM**."
        elif any(w in q for w in ["free", "how much free", "free memory"]):
            direct_ans = f"There is **{free} of completely free memory** and **{available} available memory** (which includes reclaimable cache) out of **{total} total RAM**."
        elif any(w in q for w in ["swap"]):
            direct_ans = f"Total swap space is **{swap_total}** (currently **{swap_used} used**)."
        elif any(w in q for w in ["used", "usage"]):
            direct_ans = f"Active memory usage is **{used} ({pct}%)** out of **{total} total RAM**."
        else:
            direct_ans = f"Total installed RAM is **{total}**, with **{used} ({pct}%) actively used** and **{available} available**."

        return f"{direct_ans}\n\n{format_memory_markdown(data)}"

    elif intent == "storage":
        d = data.get("details", {})
        total_disk = d.get("total_physical_disk_human", "Unknown")
        num_disks = len(d.get("physical_disks", []))
        fs_list = d.get("mounted_filesystems", [])
        free_fs = fs_list[0].get("free_human", "Unknown") if fs_list else "Unknown"

        if any(w in q for w in ["free", "available", "how much space"]):
            direct_ans = f"Total physical disk capacity is **{total_disk}**. Main filesystem currently has **{free_fs} free space**."
        elif any(w in q for w in ["physical", "drive", "disks", "hardware"]):
            direct_ans = f"The system has **{num_disks} physical disk(s)** totaling **{total_disk}** in raw storage capacity (excluding virtual loop devices)."
        else:
            direct_ans = f"Detected **{total_disk}** total physical disk capacity across **{num_disks}** drive(s)."

        return f"{direct_ans}\n\n{format_storage_markdown(data)}"

    elif intent == "gpu":
        d = data.get("details", {})
        has_ded = d.get("has_dedicated_gpu", False)
        devices = d.get("detected_devices", [])

        if not devices:
            direct_ans = "No GPU or display adapter was detected on the PCI bus."
        elif not has_ded and d.get("has_virtual_gpu", False):
            vname = devices[0]["raw_name"]
            direct_ans = (
                f"**No dedicated physical GPU is detected.** The system is using a virtual/emulated "
                f"display adapter (**{vname}**) under hypervisor virtualization (VirtualBox/VMware/KVM)."
            )
        elif has_ded:
            gname = devices[0]["raw_name"]
            direct_ans = f"Detected dedicated physical GPU: **{gname}**."
        else:
            direct_ans = f"Detected display adapter: **{devices[0]['raw_name']}** ({devices[0]['classification']})."

        return f"{direct_ans}\n\n{format_gpu_markdown(data)}"

    return ""


def handle_overview_query() -> Dict[str, Any]:
    """Aggregates all hardware components into a single comprehensive system overview."""
    cpu = get_cpu_info()
    mem = get_memory_info()
    storage = get_storage_info()
    gpu = get_gpu_info()

    content = [
        "## 📋 Comprehensive System Hardware Overview\n",
        format_cpu_markdown(cpu),
        "\n---\n",
        format_memory_markdown(mem),
        "\n---\n",
        format_storage_markdown(storage),
        "\n---\n",
        format_gpu_markdown(gpu),
    ]

    return {
        "intent": "overview",
        "tool_used": "all_hardware_tools",
        "answer": "\n".join(content),
        "structured_data": {
            "cpu": cpu,
            "memory": mem,
            "storage": storage,
            "gpu": gpu
        },
        "status": "success"
    }


def route_question(query: str) -> Dict[str, Any]:
    """
    Main entry point for local question routing.
    Determines intent, calls appropriate hardware detector, and synthesizes
    an accurate, grounded answer. Completely offline and deterministic.
    """
    if not query or not query.strip():
        return {
            "intent": "unknown",
            "tool_used": None,
            "answer": "Please ask a question about your system's hardware (CPU, RAM, Storage, GPU, or System Overview).",
            "structured_data": {},
            "status": "unavailable"
        }

    intent = classify_query(query)

    if intent == "cpu":
        data = get_cpu_info()
        answer = synthesize_specific_answer(query, "cpu", data)
        return {
            "intent": "cpu",
            "tool_used": "hardware.cpu.get_cpu_info",
            "answer": answer,
            "structured_data": data,
            "status": data.get("status", "success")
        }

    elif intent == "memory":
        data = get_memory_info()
        answer = synthesize_specific_answer(query, "memory", data)
        return {
            "intent": "memory",
            "tool_used": "hardware.memory.get_memory_info",
            "answer": answer,
            "structured_data": data,
            "status": data.get("status", "success")
        }

    elif intent == "storage":
        data = get_storage_info()
        answer = synthesize_specific_answer(query, "storage", data)
        return {
            "intent": "storage",
            "tool_used": "hardware.storage.get_storage_info",
            "answer": answer,
            "structured_data": data,
            "status": data.get("status", "success")
        }

    elif intent == "gpu":
        data = get_gpu_info()
        answer = synthesize_specific_answer(query, "gpu", data)
        return {
            "intent": "gpu",
            "tool_used": "hardware.gpu.get_gpu_info",
            "answer": answer,
            "structured_data": data,
            "status": data.get("status", "success")
        }

    elif intent == "overview":
        return handle_overview_query()

    else:
        # Graceful fallback with clear examples
        msg = (
            "I am **HardwareIQ**, your local Linux hardware assistant. I can only provide "
            "information about this machine's actual detected hardware specifications.\n\n"
            "I couldn't map your query to a supported hardware component. Try asking:\n"
            "- 🖥️ **CPU**: *'What CPU is installed?'*, *'How many cores do I have?'*, *'What is the clock frequency?'*\n"
            "- 🧠 **Memory**: *'How much RAM is installed?'*, *'How much memory is available?'*, *'What is the swap usage?'*\n"
            "- 💾 **Storage**: *'What disks are connected?'*, *'What is my physical disk capacity?'*, *'Show mounted partitions'*\n"
            "- 🎮 **GPU**: *'Is there a dedicated GPU?'*, *'What graphics controller is detected?'*\n"
            "- 📋 **Overview**: *'Show full system specs'*, *'Give me a hardware summary'*"
        )
        return {
            "intent": "unknown",
            "tool_used": None,
            "answer": msg,
            "structured_data": {},
            "status": "unavailable"
        }
