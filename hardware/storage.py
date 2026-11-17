"""
HardwareIQ - Storage Detection Module
Detects physical storage devices using lsblk and filesystem capacity via psutil.
Distinguishes physical disk capacity from filesystem available space, and explicitly
excludes loop devices and optical drives from physical disk totals.
Compatible with Python 3.8+.
"""

import json
from typing import Any, Dict, List, Optional
import psutil

from utils.command_executor import run_safe_command


def bytes_to_human(n_bytes: Optional[int]) -> str:
    """Formats bytes into human-readable representation (GiB, MiB, etc.)."""
    if n_bytes is None:
        return "N/A"
    gib = n_bytes / (1024 ** 3)
    if gib >= 1.0:
        return f"{gib:.2f} GiB"
    mib = n_bytes / (1024 ** 2)
    return f"{mib:.2f} MiB"


def get_mounted_filesystems() -> List[Dict[str, Any]]:
    """
    Retrieves mounted real filesystems, reporting total, used, and available space.
    Filters out pseudo-filesystems and duplicate mounts of the same partition.
    """
    filesystems = []
    seen_devices = set()

    for part in psutil.disk_partitions(all=False):
        # Exclude loop devices, squashfs, or duplicate device mounts
        if part.device.startswith("/dev/loop") or part.fstype in ("squashfs", "tmpfs", "overlay"):
            continue
        if part.device in seen_devices:
            continue

        try:
            usage = psutil.disk_usage(part.mountpoint)
            seen_devices.add(part.device)
            filesystems.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_bytes": usage.total,
                "total_human": bytes_to_human(usage.total),
                "used_bytes": usage.used,
                "used_human": bytes_to_human(usage.used),
                "free_bytes": usage.free,
                "free_human": bytes_to_human(usage.free),
                "percent_used": usage.percent
            })
        except (PermissionError, FileNotFoundError):
            continue

    return filesystems


def get_storage_info() -> Dict[str, Any]:
    """
    Retrieves physical disk capacity using lsblk and filesystem usage.
    Returns consistent structured dictionary.
    """
    cmd = ["lsblk", "-b", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL"]
    success, stdout, stderr = run_safe_command(cmd)

    if not success:
        return {
            "status": "unavailable",
            "hardware_type": "storage",
            "summary": "Storage information is currently unavailable.",
            "details": {},
            "error_message": f"Failed to execute lsblk: {stderr}"
        }

    try:
        raw_data = json.loads(stdout)
        devices = raw_data.get("blockdevices", [])
    except Exception as exc:
        return {
            "status": "error",
            "hardware_type": "storage",
            "summary": "Failed to parse lsblk output.",
            "details": {},
            "error_message": f"JSON parsing error: {str(exc)}"
        }

    physical_disks = []
    loop_devices_count = 0
    total_physical_bytes = 0

    for dev in devices:
        dev_type = dev.get("type", "").lower()
        dev_name = dev.get("name", "")
        size_bytes = dev.get("size")

        # Exclude loop devices (snap / container mounts)
        if dev_type == "loop" or dev_name.startswith("loop"):
            loop_devices_count += 1
            continue

        # Exclude optical ROM drives from hard drive totals
        if dev_type == "rom" or dev_name.startswith("sr"):
            continue

        # Only count top-level physical block disks (e.g. sda, nvme0n1, vda)
        if dev_type == "disk":
            try:
                b_val = int(size_bytes) if size_bytes is not None else 0
            except (ValueError, TypeError):
                b_val = 0

            total_physical_bytes += b_val
            model = dev.get("model")
            model_clean = model.strip() if model else "Generic Disk"

            # Parse children partitions
            partitions = []
            for child in dev.get("children", []):
                try:
                    p_bytes = int(child.get("size", 0))
                except (ValueError, TypeError):
                    p_bytes = 0
                partitions.append({
                    "name": child.get("name"),
                    "size_bytes": p_bytes,
                    "size_human": bytes_to_human(p_bytes),
                    "mountpoint": child.get("mountpoint"),
                    "fstype": child.get("fstype")
                })

            physical_disks.append({
                "name": dev_name,
                "model": model_clean,
                "size_bytes": b_val,
                "size_human": bytes_to_human(b_val),
                "partitions": partitions
            })

    # Get mounted filesystem usage
    mounted_fs = get_mounted_filesystems()

    # Build clear summary
    disk_names = [f"{d['name']} ({d['size_human']})" for d in physical_disks]
    summary = (
        f"**Physical Disk Capacity**: {bytes_to_human(total_physical_bytes)} "
        f"across {len(physical_disks)} drive(s) [{', '.join(disk_names) if disk_names else 'None'}] | "
        f"**Mounted Filesystems**: {len(mounted_fs)} active mount(s)"
    )

    details = {
        "physical_disks": physical_disks,
        "total_physical_disk_bytes": total_physical_bytes,
        "total_physical_disk_human": bytes_to_human(total_physical_bytes),
        "loop_devices_excluded_count": loop_devices_count,
        "mounted_filesystems": mounted_fs
    }

    return {
        "status": "success",
        "hardware_type": "storage",
        "summary": summary,
        "details": details,
        "error_message": None
    }


def format_storage_markdown(storage_data: Dict[str, Any]) -> str:
    """Formats Storage details into clean Markdown."""
    if storage_data.get("status") != "success":
        return f"⚠️ **Storage Detection**: {storage_data.get('error_message', 'Data unavailable')}"

    d = storage_data["details"]
    lines = [
        "### 💾 Storage & Disk Specifications",
        f"- **Total Physical Disk Capacity**: `{d['total_physical_disk_human']}` *(excludes {d['loop_devices_excluded_count']} loopback devices)*",
    ]

    lines.append("\n#### 💽 Physical Drives (Hardware Block Devices):")
    if not d["physical_disks"]:
        lines.append("- *No physical hard drives detected.*")
    for disk in d["physical_disks"]:
        lines.append(f"- **/dev/{disk['name']}**: `{disk['size_human']}` (Model: `{disk['model']}`)")
        if disk["partitions"]:
            for part in disk["partitions"]:
                mount_info = f" -> Mount: `{part['mountpoint']}`" if part['mountpoint'] else " (unmounted)"
                fs_info = f" [{part['fstype']}]" if part['fstype'] else ""
                lines.append(f"  - `└─ {part['name']}`: `{part['size_human']}`{fs_info}{mount_info}")

    lines.append("\n#### 📂 Mounted Filesystems (Available Space):")
    if not d["mounted_filesystems"]:
        lines.append("- *No real mounted filesystems detected.*")
    for fs in d["mounted_filesystems"]:
        lines.append(
            f"- `{fs['mountpoint']}` (`{fs['device']}`, `{fs['fstype']}`): "
            f"`{fs['used_human']}` used of `{fs['total_human']}` (`{fs['percent_used']}%`) | "
            f"**Free Space**: `{fs['free_human']}`"
        )

    lines.append(
        "\n> ℹ️ *Note: Physical disk capacity is the raw storage hardware size reported by lsblk. "
        "Filesystem space reflects formatted partitions and available data storage.*"
    )

    return "\n".join(lines)
