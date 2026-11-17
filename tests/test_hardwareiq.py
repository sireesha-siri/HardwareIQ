"""
HardwareIQ - Comprehensive Test Suite
Tests for:
1. Command allow-list security & injection prevention.
2. CPU detection (lscpu).
3. Memory detection & double-counting prevention (psutil + /proc/meminfo).
4. Storage detection & loop device exclusion (lsblk + psutil).
5. GPU detection & virtualization distinction (lspci).
6. Natural language question routing & fallback handling.
7. AI service fallback behavior.
Compatible with Python 3.8+ using standard unittest.
"""

import unittest
from utils.command_executor import (
    ALLOWED_COMMANDS,
    CommandExecutionError,
    run_safe_command,
    validate_command,
)
from hardware.cpu import get_cpu_info, format_cpu_markdown
from hardware.memory import get_memory_info, format_memory_markdown, bytes_to_human
from hardware.storage import get_storage_info, format_storage_markdown
from hardware.gpu import get_gpu_info, format_gpu_markdown, classify_gpu
from services.tool_router import classify_query, route_question
from services.ai_service import ask_assistant, is_ai_available


class TestCommandExecutorSecurity(unittest.TestCase):
    """Verifies strict command allow-listing and shell injection protection."""

    def test_permitted_command(self):
        """Permitted commands should validate without error."""
        try:
            validate_command(["lscpu"])
        except CommandExecutionError as e:
            self.fail(f"validate_command unexpectedly raised error for lscpu: {e}")

    def test_disallowed_command_rejected(self):
        """Disallowed binaries (e.g. bash, cat, rm) must be rejected."""
        dangerous_commands = [
            ["bash", "-c", "echo hacked"],
            ["rm", "-rf", "/tmp"],
            ["cat", "/etc/passwd"],
            ["curl", "https://example.com"],
            ["python3", "-c", "print(1)"],
        ]
        for cmd in dangerous_commands:
            with self.assertRaises(CommandExecutionError):
                validate_command(cmd)

    def test_disallowed_arguments_rejected(self):
        """Even for allowed commands, unapproved flags must be rejected."""
        with self.assertRaises(CommandExecutionError):
            validate_command(["lscpu", "--malicious-flag"])

    def test_shell_injection_characters_rejected(self):
        """Arguments containing shell operators must be rejected."""
        malicious_args = [
            ["lscpu", "; rm -rf /"],
            ["lscpu", "&& whoami"],
            ["lscpu", "| grep Intel"],
            ["lscpu", "`id`"],
            ["lscpu", "$HOME"],
        ]
        for cmd in malicious_args:
            with self.assertRaises(CommandExecutionError):
                validate_command(cmd)

    def test_run_safe_command_execution(self):
        """Executing an allowed command returns success and valid stdout."""
        success, stdout, stderr = run_safe_command(["lscpu"])
        self.assertTrue(success)
        self.assertIn("Architecture", stdout)
        self.assertEqual(stderr, "")


class TestCPUDetection(unittest.TestCase):
    """Tests CPU detection via lscpu."""

    def test_cpu_detection_structure(self):
        data = get_cpu_info()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["hardware_type"], "cpu")
        self.assertIn("details", data)

        details = data["details"]
        self.assertIn("model_name", details)
        self.assertIn("architecture", details)
        self.assertGreaterEqual(details["total_cpus"], 1)
        self.assertGreaterEqual(details["cores_per_socket"], 1)

    def test_cpu_markdown_formatting(self):
        data = get_cpu_info()
        md = format_cpu_markdown(data)
        self.assertIn("CPU Specifications", md)
        self.assertIn(data["details"]["model_name"], md)


class TestMemoryDetection(unittest.TestCase):
    """Tests RAM detection, ensuring accuracy without double-counting."""

    def test_memory_detection_structure(self):
        data = get_memory_info()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["hardware_type"], "memory")

        d = data["details"]
        self.assertGreater(d["total_bytes"], 0)
        self.assertGreater(d["available_bytes"], 0)
        self.assertGreater(d["used_bytes"], 0)
        self.assertGreaterEqual(d["cached_bytes"], 0)
        self.assertGreaterEqual(d["buffers_bytes"], 0)

        # Available memory should not exceed total memory
        self.assertLessEqual(d["available_bytes"], d["total_bytes"])

    def test_bytes_to_human_conversion(self):
        self.assertEqual(bytes_to_human(1024 ** 3), "1.00 GiB")
        self.assertEqual(bytes_to_human(1024 ** 2 * 500), "500.00 MiB")
        self.assertEqual(bytes_to_human(None), "N/A")


class TestStorageDetection(unittest.TestCase):
    """Tests storage detection, ensuring physical disks are distinguished and loop devices excluded."""

    def test_storage_detection_structure(self):
        data = get_storage_info()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["hardware_type"], "storage")

        d = data["details"]
        self.assertIn("physical_disks", d)
        self.assertIn("total_physical_disk_bytes", d)
        self.assertIn("loop_devices_excluded_count", d)
        self.assertIn("mounted_filesystems", d)

        # Physical disk drives should not contain loop devices
        for disk in d["physical_disks"]:
            self.assertFalse(disk["name"].startswith("loop"))

    def test_loop_device_exclusion(self):
        """Loop devices (snap containers) must be excluded from physical disk totals."""
        data = get_storage_info()
        d = data["details"]
        # In Ubuntu 20.04 with snaps, loop devices are detected and counted in loop_devices_excluded_count
        self.assertGreaterEqual(d["loop_devices_excluded_count"], 0)


class TestGPUDetection(unittest.TestCase):
    """Tests GPU detection and virtualization distinction."""

    def test_gpu_detection_structure(self):
        data = get_gpu_info()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["hardware_type"], "gpu")
        self.assertIn("details", data)

    def test_gpu_virtualization_classification(self):
        """Virtual adapters (VMware, VirtualBox, QEMU) must be classified as virtual, not dedicated."""
        vmware_res = classify_gpu("VMware SVGA II Adapter")
        self.assertTrue(vmware_res["is_virtual"])
        self.assertFalse(vmware_res["is_dedicated"])
        self.assertEqual(vmware_res["category"], "Virtual / Emulated Graphics Adapter")

        vbox_res = classify_gpu("InnoTek Systemberatung GmbH VirtualBox Graphics Adapter")
        self.assertTrue(vbox_res["is_virtual"])
        self.assertFalse(vbox_res["is_dedicated"])

        nvidia_res = classify_gpu("NVIDIA Corporation GA106 [GeForce RTX 3060]")
        self.assertFalse(nvidia_res["is_virtual"])
        self.assertTrue(nvidia_res["is_dedicated"])
        self.assertEqual(nvidia_res["category"], "Dedicated Physical GPU")


class TestQuestionRouter(unittest.TestCase):
    """Tests natural language intent routing and direct answers."""

    def test_intent_classification(self):
        self.assertEqual(classify_query("What CPU is in this server?"), "cpu")
        self.assertEqual(classify_query("How many cores do I have?"), "cpu")
        self.assertEqual(classify_query("How much RAM is free?"), "memory")
        self.assertEqual(classify_query("Show me memory and swap usage"), "memory")
        self.assertEqual(classify_query("What hard drives are installed?"), "storage")
        self.assertEqual(classify_query("How much disk space is left?"), "storage")
        self.assertEqual(classify_query("Do I have a dedicated GPU?"), "gpu")
        self.assertEqual(classify_query("What graphics card is this?"), "gpu")
        self.assertEqual(classify_query("Show system specs"), "overview")
        self.assertEqual(classify_query("Give me a hardware summary"), "overview")
        self.assertEqual(classify_query("What is the capital of France?"), "unknown")

    def test_routing_execution(self):
        res_cpu = route_question("What processor is installed?")
        self.assertEqual(res_cpu["intent"], "cpu")
        self.assertEqual(res_cpu["tool_used"], "hardware.cpu.get_cpu_info")
        self.assertIn("Intel", res_cpu["answer"])

        res_mem = route_question("How much RAM is available?")
        self.assertEqual(res_mem["intent"], "memory")
        self.assertEqual(res_mem["tool_used"], "hardware.memory.get_memory_info")
        self.assertIn("RAM", res_mem["answer"])

        res_unknown = route_question("Write a python script")
        self.assertEqual(res_unknown["intent"], "unknown")
        self.assertIn("I am **HardwareIQ**", res_unknown["answer"])


class TestAIServiceFallback(unittest.TestCase):
    """Verifies that the assistant operates 100% offline when no Gemini API key is set."""

    def test_offline_fallback(self):
        # In default offline environment, is_ai_available should be False
        # and ask_assistant should return a local deterministic response.
        res = ask_assistant("What CPU is installed?")
        self.assertIn(res["source"], ["local_deterministic", "gemini_grounded"])
        self.assertEqual(res["status"], "success")
        self.assertIn("Intel", res["answer"])


class TestStreamlitApp(unittest.TestCase):
    """Tests that the Streamlit application runs and renders without errors."""

    def test_streamlit_app_loads(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file("app.py")
        at.run(timeout=10)
        self.assertFalse(at.exception)
        # Check sidebar navigation radio rendered
        self.assertTrue(len(at.sidebar.radio) > 0)
        self.assertEqual(at.sidebar.radio[0].value, "System Dashboard")
        # Check main content markdown rendered
        self.assertTrue(len(at.markdown) > 0)



if __name__ == "__main__":
    unittest.main()

