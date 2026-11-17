"""
HardwareIQ - GPU Detection Module
Detects graphics hardware using lspci.
Clearly distinguishes virtual/emulated display adapters (e.g., VirtualBox, VMware, QEMU)
from dedicated physical GPUs and integrated graphics (iGPUs). Never invents missing specs.
Compatible with Python 3.8+.
"""

import re
from typing import Any, Dict, List, Optional
from utils.command_executor import run_safe_command


# Known virtual/hypervisor display signatures
VIRTUAL_GPU_SIGNATURES = [
    "vmware",
    "virtualbox",
    "innotek",
    "qemu",
    "virtio",
    "bochs",
    "cirrus logic",
    "hyper-v",
    "qxl",
    "vbox",
    "svga",
    "red hat, inc. virtio gpu",
]

# Dedicated physical GPU manufacturer / model signatures
DEDICATED_GPU_SIGNATURES = [
    "nvidia",
    "geforce",
    "quadro",
    "tesla",
    "rtx",
    "gtx",
    "titan",
    "radeon rx",
    "radeon pro",
    "radeon vii",
    "firepro",
    "intel arc",
]


def classify_gpu(device_name: str) -> Dict[str, Any]:
    """
    Classifies a display controller string into Virtual, Dedicated Physical, or Integrated.
    """
    name_lower = device_name.lower()

    # Check for virtual/hypervisor adapters
    is_virtual = any(sig in name_lower for sig in VIRTUAL_GPU_SIGNATURES)

    # Check for dedicated physical GPUs
    is_dedicated = any(sig in name_lower for sig in DEDICATED_GPU_SIGNATURES)

    # Check for integrated graphics (e.g. Intel UHD/HD, AMD Renoir/Cezanne integrated)
    is_integrated = False
    if not is_virtual and not is_dedicated:
        if "intel" in name_lower and ("hd graphics" in name_lower or "uhd graphics" in name_lower or "iris" in name_lower):
            is_integrated = True
        elif "amd" in name_lower or "ati" in name_lower:
            is_integrated = True

    if is_virtual:
        category = "Virtual / Emulated Graphics Adapter"
        notes = "Running inside a virtual machine (e.g. VirtualBox, VMware, KVM). This is not a physical dedicated GPU."
    elif is_dedicated:
        category = "Dedicated Physical GPU"
        notes = "Discrete physical hardware accelerator detected."
    elif is_integrated:
        category = "Integrated Processor Graphics (iGPU)"
        notes = "Processor-integrated graphics controller sharing system memory."
    else:
        category = "Generic Display Adapter"
        notes = "Unclassified display controller."

    return {
        "is_virtual": is_virtual,
        "is_dedicated": is_dedicated,
        "is_integrated": is_integrated,
        "category": category,
        "notes": notes
    }


def get_gpu_info() -> Dict[str, Any]:
    """
    Retrieves graphics controller information using lspci.
    Returns consistent structured dictionary.
    """
    success, stdout, stderr = run_safe_command(["lspci"])

    if not success:
        return {
            "status": "unavailable",
            "hardware_type": "gpu",
            "summary": "GPU information is currently unavailable.",
            "details": {},
            "error_message": f"Failed to execute lspci: {stderr}"
        }

    detected_devices: List[Dict[str, Any]] = []

    # Filter lines for VGA, 3D, and Display controllers
    pattern = re.compile(r"([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-9a-fA-F])\s+(VGA compatible controller|3D controller|Display controller):\s+(.*)", re.IGNORECASE)

    for line in stdout.splitlines():
        match = pattern.search(line.strip())
        if match:
            pci_slot = match.group(1)
            controller_type = match.group(2)
            device_str = match.group(3).strip()

            classification = classify_gpu(device_str)

            detected_devices.append({
                "pci_slot": pci_slot,
                "controller_type": controller_type,
                "raw_name": device_str,
                "classification": classification["category"],
                "is_virtual": classification["is_virtual"],
                "is_dedicated": classification["is_dedicated"],
                "is_integrated": classification["is_integrated"],
                "notes": classification["notes"]
            })

    if not detected_devices:
        return {
            "status": "success",
            "hardware_type": "gpu",
            "summary": "No GPU or display adapter detected via PCI bus.",
            "details": {
                "detected_devices": [],
                "has_dedicated_gpu": False,
                "has_virtual_gpu": False,
                "total_gpus": 0
            },
            "error_message": None
        }

    has_dedicated = any(d["is_dedicated"] for d in detected_devices)
    has_virtual = any(d["is_virtual"] for d in detected_devices)

    # Build clear, non-misleading summary
    first_dev = detected_devices[0]
    if has_virtual and not has_dedicated:
        summary = (
            f"**Virtual Graphics Adapter**: {first_dev['raw_name']} "
            f"(VirtualBox/VMware/KVM emulated; No dedicated physical GPU)"
        )
    elif has_dedicated:
        summary = f"**Dedicated GPU**: {first_dev['raw_name']}"
    else:
        summary = f"**Display Adapter**: {first_dev['raw_name']} ({first_dev['classification']})"

    details = {
        "detected_devices": detected_devices,
        "has_dedicated_gpu": has_dedicated,
        "has_virtual_gpu": has_virtual,
        "total_gpus": len(detected_devices)
    }

    return {
        "status": "success",
        "hardware_type": "gpu",
        "summary": summary,
        "details": details,
        "error_message": None
    }


def format_gpu_markdown(gpu_data: Dict[str, Any]) -> str:
    """Formats GPU details into clean Markdown."""
    if gpu_data.get("status") != "success":
        return f"⚠️ **GPU Detection**: {gpu_data.get('error_message', 'Data unavailable')}"

    d = gpu_data["details"]
    devices = d.get("detected_devices", [])

    if not devices:
        return "### 🎮 GPU & Graphics\n- *No display adapters or graphics devices found on the PCI bus.*"

    lines = ["### 🎮 Graphics & Display Hardware"]
    for idx, dev in enumerate(devices, 1):
        lines.append(f"#### Device #{idx}: `{dev['raw_name']}`")
        lines.append(f"- **Controller Type**: `{dev['controller_type']}`")
        lines.append(f"- **PCI Slot**: `{dev['pci_slot']}`")
        lines.append(f"- **Hardware Classification**: `{dev['classification']}`")
        lines.append(f"- **Status / Notes**: {dev['notes']}")

    if d["has_virtual_gpu"] and not d["has_dedicated_gpu"]:
        lines.append(
            "\n> ⚠️ **Important Virtualization Note**: This system is running under virtualization. "
            "The detected display controller is an emulated virtual graphics device provided by the hypervisor "
            "(e.g., VirtualBox / VMware / KVM). There is **no dedicated physical GPU** attached to this machine."
        )

    return "\n".join(lines)
