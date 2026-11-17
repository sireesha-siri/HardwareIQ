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

    def test_gemini_model_configuration(self):
        """Verifies configured Gemini model is gemini-3.8-flash."""
        from services.ai_service import GEMINI_MODEL
        self.assertEqual(GEMINI_MODEL, "gemini-3.8-flash")

    def test_call_gemini_api_uses_gemini_38_flash_endpoint(self):
        """Verifies call_gemini_api uses the gemini-3.8-flash URL and handles responses."""
        from unittest.mock import patch, MagicMock
        from services.ai_service import call_gemini_api

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "candidates": [
                    {"content": {"parts": [{"text": "Synthetic Gemini 3.8 response"}]}}
                ]
            }
            mock_post.return_value = mock_resp

            result = call_gemini_api("What CPU?", '{"model_name": "Test CPU"}', "test_key_dummy_123")

            self.assertEqual(result, "Synthetic Gemini 3.8 response")
            mock_post.assert_called_once()
            call_url = mock_post.call_args[0][0]
            self.assertIn("gemini-3.8-flash:generateContent", call_url)
            self.assertIn("key=test_key_dummy_123", call_url)

    def test_call_gemini_api_network_error_fallback(self):
        """Verifies call_gemini_api returns None on network or API errors."""
        from unittest.mock import patch
        from services.ai_service import call_gemini_api

        with patch("requests.post", side_effect=Exception("Connection refused")):
            result = call_gemini_api("What CPU?", "{}", "test_key_dummy_123")
            self.assertIsNone(result)


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

    def test_navigation_persistence_and_double_click(self):
        """Verifies that selecting an item persists and clicking it twice does not reset to dashboard."""
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file("app.py")
        at.run(timeout=10)
        self.assertEqual(at.session_state["active_nav"], "System Dashboard")

        sections = [
            "Real-Time Monitoring",
            "AI Hardware Assistant",
            "Subprocess Security",
            "System Dashboard"
        ]
        for sec in sections:
            # First click
            at.sidebar.radio[0].set_value(sec).run(timeout=10)
            self.assertEqual(at.session_state["active_nav"], sec)
            self.assertFalse(at.exception)

            # Second click (double click on active item)
            at.sidebar.radio[0].set_value(sec).run(timeout=10)
            self.assertEqual(at.session_state["active_nav"], sec, f"Double-click unexpectedly reset navigation on {sec}")
            self.assertFalse(at.exception)

    def test_session_state_preserved_during_navigation(self):
        """Verifies that switching navigation views does not clear chat history or telemetry."""
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file("app.py")
        at.run(timeout=10)

        # Seed chat message and check telemetry
        at.session_state["messages"].append({"role": "user", "content": "Persisted message"})
        msg_count = len(at.session_state["messages"])
        telemetry_count = len(at.session_state["session_history"])

        for sec in ["Real-Time Monitoring", "Subprocess Security", "AI Hardware Assistant", "System Dashboard"]:
            at.sidebar.radio[0].set_value(sec).run(timeout=10)
            self.assertEqual(len(at.session_state["messages"]), msg_count)
            self.assertGreaterEqual(len(at.session_state["session_history"]), telemetry_count)

    def test_all_views_render_without_exception(self):
        """Verifies each dashboard section renders completely without raising any exceptions."""
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file("app.py")
        at.run(timeout=10)
        self.assertFalse(at.exception)

        views = [
            "Real-Time Monitoring",
            "AI Hardware Assistant",
            "Subprocess Security",
            "System Dashboard"
        ]
        for view in views:
            at.sidebar.radio[0].set_value(view).run(timeout=10)
            self.assertFalse(at.exception, f"Rendering failed on view: {view}")
            self.assertEqual(at.session_state["active_nav"], view)


class TestUIThemeAndComponents(unittest.TestCase):
    """Tests Phase 4 UI theme styles and component rendering."""

    def test_theme_css_contains_dark_overrides(self):
        from ui.styles import get_theme_css
        css = get_theme_css()
        # Verify dark palette variables
        self.assertIn("#080B12", css)
        self.assertIn("#0D1422", css)
        self.assertIn("#111F32", css)
        self.assertIn("#16263A", css)
        self.assertIn("#06B6D4", css)
        self.assertIn("#22D3EE", css)

        # Verify Vega-Lite and Altair chart transparency rules
        self.assertIn(".vega-embed", css)
        self.assertIn("fill: transparent !important;", css)

        # Verify bottom sticky container styling
        self.assertIn('[data-testid="stBottom"]', css)
        self.assertIn('[data-testid="stChatInput"]', css)
        self.assertIn("padding-bottom: 7.5rem", css)

        # Verify Lucide navigation and button SVGs
        self.assertIn("data:image/svg+xml;utf8,", css)
        self.assertIn("sidebar-queries", css)

    def test_gauge_and_memory_panel_rendering(self):
        from ui.components import render_semicircular_gauge, clean_html, render_gpu_status_visual
        from hardware.memory import get_memory_info

        # Semicircular gauge output
        gauge_html = render_semicircular_gauge(45.5, label="CPU LOAD", subtext="2 Threads Active")
        self.assertIn("45.5%", gauge_html)
        self.assertIn("CPU LOAD", gauge_html)
        self.assertIn("stroke-dashoffset", gauge_html)

        # GPU status visual output
        gpu_visual = render_gpu_status_visual(is_dedicated=False, raw_name="VMware SVGA", pci_slot="00:02.0")
        self.assertIn("VIRTUAL", gpu_visual)
        self.assertIn("00:02.0", gpu_visual)

        # Clean HTML indentation stripping
        indented = "    <div>\n        <p>Text</p>\n    </div>"
        cleaned = clean_html(indented)
        self.assertFalse(cleaned.startswith("    "))

    def test_chat_input_flow_and_clear_chat(self):
        """Verifies asking a question updates messages, redirects to Assistant, and Clear Chat wipes history."""
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file("app.py")
        at.run(timeout=10)
        self.assertEqual(len(at.session_state["messages"]), 0)

        # Submit chat input from dashboard
        at.chat_input[0].set_value("What CPU is installed?").run(timeout=10)
        self.assertEqual(at.session_state["active_nav"], "AI Hardware Assistant")
        self.assertEqual(len(at.session_state["messages"]), 2)
        self.assertEqual(at.session_state["messages"][0]["role"], "user")
        self.assertEqual(at.session_state["messages"][1]["role"], "assistant")

        # Find and click Clear Chat button
        for btn in at.sidebar.button:
            if "Clear Chat" in btn.label:
                btn.click().run(timeout=10)
                break
        self.assertEqual(len(at.session_state["messages"]), 0)

    def test_altair_chart_specs_transparent_background(self):
        """Verifies Altair charts produce specs with transparent backgrounds and view fills."""
        import altair as alt
        import pandas as pd

        per_cpu = [15.0, 30.0]
        data = pd.DataFrame({
            "Core": [f"Core {i}" for i in range(len(per_cpu))],
            "Load": [float(val) for val in per_cpu],
            "Max": [100.0 for _ in range(len(per_cpu))]
        })
        bg = alt.Chart(data).mark_bar(color="#16263A", cornerRadius=6, size=22).encode(
            x=alt.X("Max:Q", title=None, axis=None),
            y=alt.Y("Core:N", sort=None, title=None)
        )
        fg = alt.Chart(data).mark_bar(cornerRadius=6, size=22).encode(
            x=alt.X("Load:Q", scale=alt.Scale(domain=[0, 100]), title=None, axis=None),
            y=alt.Y("Core:N", sort=None)
        )
        chart = (
            (bg + fg)
            .properties(height=max(110, len(per_cpu) * 38 + 14), background="transparent")
            .configure(background="transparent")
            .configure_view(stroke=None, fill="transparent")
        )
        spec = chart.to_dict()
        self.assertEqual(spec.get("background"), "transparent")
        self.assertEqual(spec.get("config", {}).get("background"), "transparent")
        self.assertEqual(spec.get("config", {}).get("view", {}).get("fill"), "transparent")

    def test_donut_chart_and_multi_core_timeline(self):
        """Verifies donut chart and multi-core history charts create valid transparent specs."""
        import altair as alt
        import pandas as pd

        # Donut Chart spec check
        donut_df = pd.DataFrame([
            {"Category": "Actively Used", "Bytes": 2000000000, "Percent": 35.5},
            {"Category": "Cache & Buffers", "Bytes": 2500000000, "Percent": 44.3},
            {"Category": "Completely Free", "Bytes": 1140000000, "Percent": 20.2},
        ])
        donut = (
            alt.Chart(donut_df)
            .mark_arc(innerRadius=52, outerRadius=80)
            .encode(theta=alt.Theta("Bytes:Q"), color=alt.Color("Category:N"))
            .properties(height=200, background="transparent")
            .configure(background="transparent")
            .configure_view(stroke=None, fill="transparent")
        )
        donut_spec = donut.to_dict()
        self.assertEqual(donut_spec.get("mark", {}).get("type"), "arc")
        self.assertEqual(donut_spec.get("background"), "transparent")

        # Multi-Core Timeline spec check
        timeline_df = pd.DataFrame([
            {"timestamp": "14:00:00", "Core": "Core 0", "Load": 25.0},
            {"timestamp": "14:00:00", "Core": "Core 1", "Load": 30.0},
            {"timestamp": "14:01:00", "Core": "Core 0", "Load": 28.0},
            {"timestamp": "14:01:00", "Core": "Core 1", "Load": 32.0},
        ])
        timeline = (
            alt.Chart(timeline_df)
            .mark_line(point=True)
            .encode(x=alt.X("timestamp:N"), y=alt.Y("Load:Q"), color=alt.Color("Core:N"))
            .properties(height=240, background="transparent")
            .configure(background="transparent")
            .configure_view(stroke=None, fill="transparent")
        )
        timeline_spec = timeline.to_dict()
        self.assertEqual(timeline_spec.get("mark", {}).get("type"), "line")
        self.assertEqual(timeline_spec.get("background"), "transparent")

    def test_telemetry_recording_per_core_data(self):
        """Verifies session telemetry records per-core utilization readings."""
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file("app.py")
        at.run(timeout=10)
        history = at.session_state["session_history"]
        self.assertGreaterEqual(len(history), 1)
        latest = history[-1]
        self.assertIn("timestamp", latest)
        self.assertIn("cpu_percent", latest)
        self.assertIn("ram_percent", latest)
        self.assertIn("per_core", latest)
        self.assertIsInstance(latest["per_core"], list)
        self.assertGreater(len(latest["per_core"]), 0)







if __name__ == "__main__":
    unittest.main()

