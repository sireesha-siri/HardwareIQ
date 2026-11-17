"""
HardwareIQ - Premium Linux Hardware Intelligence Suite
Modern dark-themed hardware monitoring dashboard with integrated AI assistant.
Grounded exclusively in real Linux kernel and system diagnostics.
Compatible with Python 3.8+ and Streamlit 1.39.0.
"""

from datetime import datetime
from typing import Any, Dict, List
import psutil
import streamlit as st

# Configure page layout and title
st.set_page_config(
    page_title="HardwareIQ — Hardware Intelligence Dashboard",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

from hardware.cpu import get_cpu_info, format_cpu_markdown
from hardware.memory import get_memory_info, format_memory_markdown
from hardware.storage import get_storage_info, format_storage_markdown
from hardware.gpu import get_gpu_info, format_gpu_markdown
from services.ai_service import ask_assistant, is_ai_available
from services.tool_router import route_question
from utils.command_executor import ALLOWED_COMMANDS
from ui.icons import get_icon
from ui.styles import get_theme_css
from ui.components import (
    render_html,
    render_hero_header,
    render_overview_cards,
    render_semicircular_gauge,
    render_per_core_chart,
    render_cpu_telemetry_panel,
    render_memory_breakdown_panel,
    render_runtime_history_chart,
    render_filesystem_table,
)

# Initialize CPU measurement baseline for non-blocking telemetry
psutil.cpu_percent(interval=None)


def initialize_session_state() -> None:
    """Initializes session state variables for chat history, telemetry, and hardware cache."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "hardware_cache" not in st.session_state:
        st.session_state.hardware_cache = None
    if "last_refreshed" not in st.session_state:
        st.session_state.last_refreshed = datetime.now().strftime("%H:%M:%S")
    if "session_history" not in st.session_state:
        st.session_state.session_history = []
    if "active_nav" not in st.session_state:
        st.session_state.active_nav = "System Dashboard"


def load_hardware_summary() -> Dict[str, Any]:
    """Caches and returns current hardware specifications for quick display."""
    return {
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "storage": get_storage_info(),
        "gpu": get_gpu_info()
    }


def record_telemetry_sample(mem_data: Dict[str, Any]) -> None:
    """Records a single timestamped real runtime telemetry sample into session history."""
    cpu_val = psutil.cpu_percent(interval=None)
    ram_pct = mem_data.get("details", {}).get("percent_used", 0.0)
    current_time = datetime.now().strftime("%H:%M:%S")

    st.session_state.session_history.append({
        "timestamp": current_time,
        "cpu_percent": float(cpu_val),
        "ram_percent": float(ram_pct)
    })

    # Keep latest 30 samples to prevent unbounded memory growth
    if len(st.session_state.session_history) > 30:
        st.session_state.session_history = st.session_state.session_history[-30:]


def main():
    initialize_session_state()

    # Apply CSS Theme System
    st.markdown(get_theme_css(), unsafe_allow_html=True)

    # Initial hardware load if needed
    if st.session_state.hardware_cache is None:
        st.session_state.hardware_cache = load_hardware_summary()
        record_telemetry_sample(st.session_state.hardware_cache["memory"])

    hw = st.session_state.hardware_cache
    ai_active = is_ai_available()
    last_refreshed = st.session_state.last_refreshed

    # Measure current non-blocking CPU utilization
    current_cpu_percent = psutil.cpu_percent(interval=None)
    per_cpu_cores = psutil.cpu_percent(percpu=True)

    # --- SIDEBAR NAVIGATION & TELEMETRY ---
    with st.sidebar:
        # App Branding Header
        branding_html = f"""<div style="display: flex; align-items: center; gap: 12px; padding: 12px 6px; border-bottom: 1px solid #1E2D42; margin-bottom: 16px;">
<div class="hw-card-icon-badge" style="width: 42px; height: 42px; background: rgba(37, 99, 235, 0.2); border-color: #22D3EE;">
{get_icon("server", size=24, color="#22D3EE")}
</div>
<div>
<div style="font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em; color: #F8FAFC;">HardwareIQ</div>
<div style="font-size: 0.72rem; font-weight: 600; color: #06B6D4; letter-spacing: 0.08em; text-transform: uppercase;">v2.0 • Linux Diagnostics</div>
</div>
</div>"""
        render_html(branding_html)

        render_html('<div style="font-size: 0.75rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">Navigation</div>')
        
        # Sleek Radio Navigation with Lucide SVG Icons (Zero Emojis)
        nav_options = [
            "System Dashboard",
            "Real-Time Monitoring",
            "AI Hardware Assistant",
            "Subprocess Security"
        ]
        
        curr_index = nav_options.index(st.session_state.active_nav) if st.session_state.active_nav in nav_options else 0
        nav_selection = st.radio(
            "Select Dashboard View",
            nav_options,
            index=curr_index,
            label_visibility="collapsed"
        )
        st.session_state.active_nav = nav_selection

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Quick Telemetry Sidebar Card
        cpu_details = hw["cpu"].get("details", {})
        mem_details = hw["memory"].get("details", {})
        gpu_details = hw["gpu"].get("details", {})
        has_ded_gpu = gpu_details.get("has_dedicated_gpu", False)

        telemetry_sidebar_html = f"""<div style="background: rgba(17, 31, 50, 0.7); border: 1px solid #1E2D42; border-radius: 10px; padding: 14px; margin-bottom: 16px;">
<div style="font-size: 0.75rem; font-weight: 700; color: #06B6D4; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">Quick Telemetry</div>
<div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px;">
<span style="color: #94A3B8;">CPU Architecture:</span>
<span style="font-weight: 600; color: #F8FAFC;">{cpu_details.get('architecture', 'x86_64')}</span>
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px;">
<span style="color: #94A3B8;">Logical Cores:</span>
<span style="font-weight: 600; color: #22D3EE;">{cpu_details.get('total_cpus', 'N/A')} Threads</span>
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px;">
<span style="color: #94A3B8;">Total RAM:</span>
<span style="font-weight: 600; color: #38BDF8;">{mem_details.get('total_human', 'N/A')}</span>
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
<span style="color: #94A3B8;">GPU Type:</span>
<span style="font-weight: 600; color: {'#4ADE80' if has_ded_gpu else '#FBBF24'};">{'Dedicated' if has_ded_gpu else 'Virtual Adapter'}</span>
</div>
</div>"""
        render_html(telemetry_sidebar_html)

        # Action Buttons
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Refresh Telemetry", use_container_width=True):
                st.session_state.hardware_cache = load_hardware_summary()
                st.session_state.last_refreshed = datetime.now().strftime("%H:%M:%S")
                record_telemetry_sample(st.session_state.hardware_cache["memory"])
                st.rerun()
        with col_btn2:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Suggested Questions Quick Launch (Clean, No Emojis)
        render_html('<div style="font-size: 0.75rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">Quick Queries</div>')
        quick_questions = [
            "What CPU is installed?",
            "How many CPU cores are available?",
            "How much RAM is available?",
            "Show memory utilization",
            "What physical disks are connected?",
            "Do I have a dedicated GPU?",
            "Show my complete hardware overview"
        ]

        for q in quick_questions:
            if st.button(q, key=f"sidebar_q_{q}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": q})
                response = ask_assistant(q)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["answer"],
                    "tool_used": response.get("tool_used"),
                    "intent": response.get("intent"),
                    "structured_data": response.get("structured_data", {})
                })
                st.session_state.active_nav = "AI Hardware Assistant"
                st.rerun()

    # --- TOP HERO BANNER ---
    render_hero_header(ai_active, last_refreshed)

    # --- VIEW 1: SYSTEM DASHBOARD ---
    if st.session_state.active_nav == "System Dashboard":
        # 4 Core Hardware Overview Cards with Visual Semicircular Gauges
        render_overview_cards(
            hw["cpu"],
            hw["memory"],
            hw["storage"],
            hw["gpu"],
            current_cpu_percent
        )

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Two-Column Performance & Telemetry Preview (Symmetric Layout)
        dash_col1, dash_col2 = st.columns([1, 1])

        with dash_col1:
            render_cpu_telemetry_panel(per_cpu_cores, cpu_details)

        with dash_col2:
            render_memory_breakdown_panel(mem_details)

        # Quick Assistant Input from Dashboard
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        dash_card_html = f"""<div class="hw-card" style="margin-bottom: 12px;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
{get_icon("message-square", size=20, color="#22D3EE")}
<span style="font-weight: 700; color: #F8FAFC;">Ask HardwareIQ Assistant Directly</span>
</div>
<div style="font-size: 0.85rem; color: #94A3B8;">
Type any natural-language query to query your hardware specifications instantly.
</div>
</div>"""
        render_html(dash_card_html)

        dash_query = st.chat_input("Ask a hardware question (e.g. 'How much RAM is free?' or 'What CPU is installed?')...", key="dash_input")
        if dash_query:
            st.session_state.messages.append({"role": "user", "content": dash_query})
            response = ask_assistant(dash_query)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "tool_used": response.get("tool_used"),
                "intent": response.get("intent"),
                "structured_data": response.get("structured_data", {})
            })
            st.session_state.active_nav = "AI Hardware Assistant"
            st.rerun()

    # --- VIEW 2: REAL-TIME MONITORING ---
    elif st.session_state.active_nav == "Real-Time Monitoring":
        rt_header = f"""<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
<div style="display: flex; align-items: center; gap: 10px;">
{get_icon("activity", size=24, color="#22D3EE")}
<h2 style="margin: 0; font-size: 1.35rem; color: #F8FAFC;">Live System Monitoring Telemetry</h2>
</div>
<span class="hw-status-pill">Sampling: <b>Real Kernel Telemetry</b></span>
</div>"""
        render_html(rt_header)

        # Semicircular Gauges Row
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            gauge_cpu_html = f"""<div class="hw-card-elevated" style="text-align: center;">
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("cpu", size=20, color="#22D3EE")}</div>
<div class="hw-card-title">Real-Time CPU Load</div>
</div>
<span class="hw-card-badge badge-live">{cpu_details.get('total_cpus', '2')} Cores</span>
</div>
{render_semicircular_gauge(current_cpu_percent, label="OVERALL CPU", subtext=f"Clock: {cpu_details.get('cpu_mhz', 'N/A')} MHz", color_type="cyan")}
</div>"""
            render_html(gauge_cpu_html)

        with g_col2:
            gauge_ram_html = f"""<div class="hw-card-elevated" style="text-align: center;">
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("memory-stick", size=20, color="#3B82F6")}</div>
<div class="hw-card-title">Real-Time RAM Usage</div>
</div>
<span class="hw-card-badge badge-live">{mem_details.get('total_human', 'N/A')} Total</span>
</div>
{render_semicircular_gauge(mem_details.get('percent_used', 0.0), label="RAM USED", subtext=f"Available: {mem_details.get('available_human', 'N/A')}", color_type="blue")}
</div>"""
            render_html(gauge_ram_html)

        # Per-Core Utilization Chart Panel
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        render_cpu_telemetry_panel(per_cpu_cores, cpu_details)

        # Session Time-Series Line Chart Panel
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        history_header = f"""<div class="hw-card-elevated" style="margin-bottom: 0px;">
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("chart-no-axes-combined", size=20, color="#38BDF8")}</div>
<div class="hw-card-title">Session Telemetry History (CPU vs. RAM)</div>
</div>
<span class="hw-card-badge badge-live">{len(st.session_state.session_history)} Samples Recorded</span>
</div>"""
        render_html(history_header)
        render_runtime_history_chart(st.session_state.session_history)
        render_html("</div>")

        # Storage & Filesystem Utilization Table Panel
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        storage_header = f"""<div class="hw-card-elevated" style="margin-bottom: 0px;">
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("hard-drive", size=20, color="#22D3EE")}</div>
<div class="hw-card-title">Mounted Filesystems & Storage Partitions</div>
</div>
<span class="hw-card-badge badge-live">{len(hw['storage'].get('details', {}).get('mounted_filesystems', []))} Mounts</span>
</div>"""
        render_html(storage_header)
        render_filesystem_table(hw["storage"].get("details", {}).get("mounted_filesystems", []))
        render_html("</div>")

    # --- VIEW 3: AI ASSISTANT CHAT ---
    elif st.session_state.active_nav == "AI Hardware Assistant":
        assistant_header = f"""<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
<div style="display: flex; align-items: center; gap: 10px;">
{get_icon("bot", size=26, color="#22D3EE")}
<div>
<h2 style="margin: 0; font-size: 1.35rem; color: #F8FAFC;">HardwareIQ Natural-Language Assistant</h2>
<div style="font-size: 0.82rem; color: #94A3B8;">Grounded strictly in local hardware diagnostics. Never invents missing specifications.</div>
</div>
</div>
<span class="hw-status-pill">{get_icon("shield-check", size=14, color="#4ADE80")} <b>100% Grounded</b></span>
</div>"""
        render_html(assistant_header)

        # Suggested Query Chips (Clean, No Emojis)
        render_html('<div style="font-size: 0.8rem; font-weight: 600; color: #94A3B8; margin-bottom: 8px;">Suggested Questions:</div>')
        chip_col1, chip_col2, chip_col3 = st.columns(3)
        with chip_col1:
            if st.button("What CPU is installed?", key="chip_cpu", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "What CPU is installed?"})
                res = ask_assistant("What CPU is installed?")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": res["answer"],
                    "tool_used": res.get("tool_used"),
                    "intent": res.get("intent"),
                    "structured_data": res.get("structured_data", {})
                })
                st.rerun()
            if st.button("Do I have a dedicated GPU?", key="chip_gpu", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Do I have a dedicated GPU?"})
                res = ask_assistant("Do I have a dedicated GPU?")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": res["answer"],
                    "tool_used": res.get("tool_used"),
                    "intent": res.get("intent"),
                    "structured_data": res.get("structured_data", {})
                })
                st.rerun()

        with chip_col2:
            if st.button("How much RAM is available?", key="chip_ram", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "How much RAM is available?"})
                res = ask_assistant("How much RAM is available?")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": res["answer"],
                    "tool_used": res.get("tool_used"),
                    "intent": res.get("intent"),
                    "structured_data": res.get("structured_data", {})
                })
                st.rerun()
            if st.button("What physical disks are connected?", key="chip_storage", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "What physical disks are connected?"})
                res = ask_assistant("What physical disks are connected?")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": res["answer"],
                    "tool_used": res.get("tool_used"),
                    "intent": res.get("intent"),
                    "structured_data": res.get("structured_data", {})
                })
                st.rerun()

        with chip_col3:
            if st.button("How many cores do I have?", key="chip_cores", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "How many cores do I have?"})
                res = ask_assistant("How many cores do I have?")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": res["answer"],
                    "tool_used": res.get("tool_used"),
                    "intent": res.get("intent"),
                    "structured_data": res.get("structured_data", {})
                })
                st.rerun()
            if st.button("Show complete hardware overview", key="chip_overview", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Show complete hardware overview"})
                res = ask_assistant("Show complete hardware overview")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": res["answer"],
                    "tool_used": res.get("tool_used"),
                    "intent": res.get("intent"),
                    "structured_data": res.get("structured_data", {})
                })
                st.rerun()

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # Empty State Welcome Card if No Messages
        if not st.session_state.messages:
            empty_welcome_html = f"""<div class="hw-card" style="padding: 28px; text-align: center;">
<div style="margin-bottom: 12px;">{get_icon("bot", size=42, color="#22D3EE")}</div>
<h3 style="margin: 0 0 8px 0; color: #F8FAFC; font-weight: 700;">HardwareIQ Assistant Ready</h3>
<p style="color: #94A3B8; max-width: 580px; margin: 0 auto 16px auto; line-height: 1.5; font-size: 0.9rem;">
Ask questions in plain English about your CPU, RAM, physical disks, mounted filesystems,
or graphics controllers. Responses are verified through local system commands.
</p>
<div style="display: inline-flex; gap: 8px; flex-wrap: wrap; justify-content: center;">
<span class="hw-card-badge badge-live">CPU Specs</span>
<span class="hw-card-badge badge-live">Free Memory</span>
<span class="hw-card-badge badge-live">Disk Capacity</span>
<span class="hw-card-badge badge-live">GPU Status</span>
</div>
</div>"""
            render_html(empty_welcome_html)

        # Render Conversation History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and msg.get("tool_used"):
                    with st.expander(f"Diagnostic Inspection: `{msg.get('tool_used')}` (Intent: `{msg.get('intent')}`)"):
                        st.json(msg.get("structured_data", {}))

        # Main Chat Input
        assistant_query = st.chat_input("Ask a hardware question (e.g. 'How much RAM is free?' or 'What CPU is installed?')...", key="chat_page_input")
        if assistant_query:
            st.session_state.messages.append({"role": "user", "content": assistant_query})
            with st.chat_message("user"):
                st.markdown(assistant_query)

            with st.chat_message("assistant"):
                with st.spinner("Querying system diagnostics..."):
                    response = ask_assistant(assistant_query)
                    st.markdown(response["answer"])
                    if response.get("tool_used"):
                        with st.expander(f"Diagnostic Inspection: `{response.get('tool_used')}` (Intent: `{response.get('intent')}`)"):
                            st.json(response.get("structured_data", {}))

            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "tool_used": response.get("tool_used"),
                "intent": response.get("intent"),
                "structured_data": response.get("structured_data", {})
            })

    # --- VIEW 4: SUBPROCESS SECURITY & DIAGNOSTICS ---
    elif st.session_state.active_nav == "Subprocess Security":
        sec_header = f"""<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
<div style="display: flex; align-items: center; gap: 10px;">
{get_icon("shield-check", size=26, color="#4ADE80")}
<div>
<h2 style="margin: 0; font-size: 1.35rem; color: #F8FAFC;">Subprocess Security & Execution Guard</h2>
<div style="font-size: 0.82rem; color: #94A3B8;">Explicit command allow-list enforcement and injection mitigation architecture.</div>
</div>
</div>
<span class="hw-card-badge badge-dedicated">ENFORCED</span>
</div>"""
        render_html(sec_header)

        sec_col1, sec_col2 = st.columns(2)
        with sec_col1:
            sec_card1 = f"""<div class="hw-card-elevated">
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("terminal", size=20, color="#22D3EE")}</div>
<div class="hw-card-title">Security Policies Enforced</div>
</div>
</div>
<ul style="color: #CBD5E1; font-size: 0.88rem; line-height: 1.8; margin: 0; padding-left: 20px;">
<li><b>Strict Binary Allow-List:</b> Only permitted system diagnostic binaries are allowed to execute.</li>
<li><b>Argument Whitelisting:</b> Each binary has an explicit set of allowable flag arguments.</li>
<li><b>shell=False Enforcement:</b> Commands are invoked directly via vector arguments, never passed to a shell interpreter.</li>
<li><b>Subprocess Timeout:</b> Maximum execution time capped at 5.0 seconds to prevent denial of service.</li>
<li><b>Zero Arbitrary Code:</b> User queries are processed strictly by the router and are never passed to the shell.</li>
</ul>
</div>"""
            render_html(sec_card1)

        with sec_col2:
            sec_card2 = f"""<div class="hw-card-elevated">
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("settings", size=20, color="#38BDF8")}</div>
<div class="hw-card-title">Approved Allow-List Inventory</div>
</div>
</div>
<div style="font-size: 0.85rem; color: #CBD5E1;">
<div style="margin-bottom: 10px;">
<span style="font-weight: 700; color: #22D3EE;">1. lscpu</span>:
<code style="background: rgba(11, 18, 32, 0.8); color: #94A3B8;">Flags: -J, -e, -p, -b, -c, -y</code>
</div>
<div style="margin-bottom: 10px;">
<span style="font-weight: 700; color: #22D3EE;">2. lsblk</span>:
<code style="background: rgba(11, 18, 32, 0.8); color: #94A3B8;">Flags: -J, -b, -o, -a, -l, -p</code>
</div>
<div style="margin-bottom: 10px;">
<span style="font-weight: 700; color: #22D3EE;">3. lspci</span>:
<code style="background: rgba(11, 18, 32, 0.8); color: #94A3B8;">Flags: -v, -nn, -mm, -k, -D</code>
</div>
</div>
</div>"""
            render_html(sec_card2)

        # Full System Raw Diagnostics Expander
        raw_header = f"""<div class="hw-card">
<div style="font-size: 0.95rem; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">Raw Diagnostic Data Inspector</div>
<div style="font-size: 0.82rem; color: #94A3B8;">Inspect the exact JSON outputs returned by the underlying hardware detection modules.</div>
</div>"""
        render_html(raw_header)

        with st.expander("CPU Diagnostics (lscpu)"):
            st.json(hw["cpu"])
        with st.expander("Memory Diagnostics (psutil + /proc/meminfo)"):
            st.json(hw["memory"])
        with st.expander("Storage Diagnostics (lsblk + psutil)"):
            st.json(hw["storage"])
        with st.expander("GPU Diagnostics (lspci)"):
            st.json(hw["gpu"])


if __name__ == "__main__":
    main()
