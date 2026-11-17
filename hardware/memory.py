"""
HardwareIQ - RAM & Memory Detection Module
Accurately detects system memory and swap specifications using psutil and /proc/meminfo.
Avoids double-counting between used, available, and cached/buffer memory.
Compatible with Python 3.8+.
"""

import os
from typing import Any, Dict, Optional
import psutil


def parse_proc_meminfo() -> Dict[str, int]:
    """
    Parses /proc/meminfo directly from the Linux kernel.
    Values are converted from kB to bytes for consistency.
    """
    meminfo = {}
    if not os.path.exists("/proc/meminfo"):
        return meminfo

    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val_parts = parts[1].strip().split()
                    val_kb = int(val_parts[0])
                    # Convert kB to bytes (1 kB in /proc/meminfo = 1024 bytes)
                    meminfo[key] = val_kb * 1024
    except Exception:
        # Gracefully handle file read or permission errors
        pass
    return meminfo


def bytes_to_human(n_bytes: Optional[int]) -> str:
    """Formats bytes into human-readable representation (GiB, MiB, etc.)."""
    if n_bytes is None:
        return "N/A"
    gib = n_bytes / (1024 ** 3)
    if gib >= 1.0:
        return f"{gib:.2f} GiB"
    mib = n_bytes / (1024 ** 2)
    return f"{mib:.2f} MiB"


def get_memory_info() -> Dict[str, Any]:
    """
    Retrieves accurate RAM and Swap metrics.
    Reconciles psutil virtual_memory with /proc/meminfo.
    Ensures total, used, available, and cached/buffers are reported accurately
    without double-counting.
    """
    try:
        vm = psutil.virtual_memory()
        sm = psutil.swap_memory()
        meminfo = parse_proc_meminfo()

        total_bytes = vm.total
        available_bytes = vm.available
        used_bytes = vm.used
        free_bytes = vm.free
        buffers_bytes = getattr(vm, "buffers", meminfo.get("Buffers", 0))
        cached_bytes = getattr(vm, "cached", meminfo.get("Cached", 0))
        shared_bytes = getattr(vm, "shared", meminfo.get("Shmem", 0))

        # Swap metrics
        swap_total = sm.total
        swap_used = sm.used
        swap_free = sm.free
        swap_percent = sm.percent

        # Summary string
        summary = (
            f"**Total RAM**: {bytes_to_human(total_bytes)} | "
            f"**Used**: {bytes_to_human(used_bytes)} ({vm.percent}%) | "
            f"**Available**: {bytes_to_human(available_bytes)} | "
            f"**Cached/Buffers**: {bytes_to_human(cached_bytes + buffers_bytes)}"
        )

        details = {
            "total_bytes": total_bytes,
            "total_human": bytes_to_human(total_bytes),
            "used_bytes": used_bytes,
            "used_human": bytes_to_human(used_bytes),
            "available_bytes": available_bytes,
            "available_human": bytes_to_human(available_bytes),
            "free_bytes": free_bytes,
            "free_human": bytes_to_human(free_bytes),
            "cached_bytes": cached_bytes,
            "cached_human": bytes_to_human(cached_bytes),
            "buffers_bytes": buffers_bytes,
            "buffers_human": bytes_to_human(buffers_bytes),
            "cached_and_buffers_human": bytes_to_human(cached_bytes + buffers_bytes),
            "shared_bytes": shared_bytes,
            "shared_human": bytes_to_human(shared_bytes),
            "percent_used": vm.percent,
            "swap_total_bytes": swap_total,
            "swap_total_human": bytes_to_human(swap_total),
            "swap_used_bytes": swap_used,
            "swap_used_human": bytes_to_human(swap_used),
            "swap_free_bytes": swap_free,
            "swap_free_human": bytes_to_human(swap_free),
            "swap_percent": swap_percent,
            "proc_meminfo_present": len(meminfo) > 0,
        }

        return {
            "status": "success",
            "hardware_type": "memory",
            "summary": summary,
            "details": details,
            "error_message": None
        }

    except Exception as exc:
        return {
            "status": "error",
            "hardware_type": "memory",
            "summary": "Memory information is currently unavailable.",
            "details": {},
            "error_message": f"Error querying memory status: {str(exc)}"
        }


def format_memory_markdown(mem_data: Dict[str, Any]) -> str:
    """Formats Memory details into clean Markdown."""
    if mem_data.get("status") != "success":
        return f"⚠️ **Memory Detection**: {mem_data.get('error_message', 'Data unavailable')}"

    d = mem_data["details"]
    lines = [
        "### 🧠 RAM & Memory Specifications",
        f"- **Total Physical RAM**: `{d['total_human']}`",
        f"- **Actively Used**: `{d['used_human']}` (`{d['percent_used']}%`) *(active process allocations)*",
        f"- **Available for Applications**: `{d['available_human']}` *(free + reclaimable page cache)*",
        f"- **Completely Free**: `{d['free_human']}` *(unallocated memory)*",
        f"- **Page Cache & Buffers**: `{d['cached_and_buffers_human']}` (`{d['cached_human']}` cached, `{d['buffers_human']}` buffers)",
    ]

    if d["swap_total_bytes"] > 0:
        lines.append(
            f"- **Swap Memory**: `{d['swap_total_human']}` total "
            f"(`{d['swap_used_human']}` used, `{d['swap_free_human']}` free, `{d['swap_percent']}%` utilized)"
        )
    else:
        lines.append("- **Swap Memory**: No swap partition configured or active.")

    lines.append(
        "\n> ℹ️ *Note: Under Linux, Available memory includes reclaimable cache and buffers. "
        "Used memory reflects active processes to prevent double-counting.*"
    )

    return "\n".join(lines)
