"""
HardwareIQ - UI Component Library
Renders visual hardware cards, semicircular gauges, donut indicators,
per-core utilization bars, and monitoring charts.
Strictly compatible with Python 3.8+ and Streamlit 1.39.0.
"""

import math
import re
from typing import Any, Dict, List, Optional
import altair as alt
import pandas as pd
import streamlit as st

from ui.icons import get_icon


def clean_html(html_str: str) -> str:
    """
    Strips all leading indentation from every line.
    Prevents Streamlit CommonMark parser from misinterpreting indented lines
    as 4-space indented code blocks.
    """
    return re.sub(r"^\s+", "", html_str.strip(), flags=re.MULTILINE)


def render_html(html_str: str) -> None:
    """
    Renders raw HTML safely.
    Uses st.html when available in Streamlit 1.39.0 to bypass Markdown code block parsing.
    """
    cleaned = clean_html(html_str)
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


def render_semicircular_gauge(
    percent: float,
    label: str = "UTILIZATION",
    subtext: str = "",
    color_type: str = "cyan"
) -> str:
    """
    Generates an SVG semicircular gauge with zero leading indentation.
    Calculates exact stroke-dashoffset for smooth arc filling.
    """
    clamped_pct = max(0.0, min(100.0, float(percent)))
    radius = 70.0
    circumference = math.pi * radius  # ~219.91
    dash_offset = circumference * (1.0 - (clamped_pct / 100.0))

    if color_type == "blue":
        start_color = "#2563EB"
        stop_color = "#3B82F6"
        glow_color = "rgba(59, 130, 246, 0.4)"
    elif color_type == "warning":
        start_color = "#F59E0B"
        stop_color = "#EF4444"
        glow_color = "rgba(245, 158, 11, 0.4)"
    else:  # cyan default
        start_color = "#2563EB"
        stop_color = "#22D3EE"
        glow_color = "rgba(6, 182, 212, 0.4)"

    subtext_html = (
        f'<div style="font-size: 0.78rem; color: #94A3B8; text-align: center; margin-top: -6px;">{subtext}</div>'
        if subtext else ""
    )

    svg_content = f"""<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;">
<svg viewBox="0 0 180 108" width="160" height="96" style="overflow: visible;">
<defs>
<linearGradient id="gaugeGrad_{color_type}" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="{start_color}" />
<stop offset="100%" stop-color="{stop_color}" />
</linearGradient>
<filter id="gaugeGlow_{color_type}" x="-20%" y="-20%" width="140%" height="140%">
<feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="{glow_color}" />
</filter>
</defs>
<path d="M 20 95 A 70 70 0 0 1 160 95" fill="none" stroke="#16263A" stroke-width="12" stroke-linecap="round" />
<path d="M 20 95 A 70 70 0 0 1 160 95" fill="none" stroke="url(#gaugeGrad_{color_type})" stroke-width="12" stroke-linecap="round" stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{dash_offset:.2f}" filter="url(#gaugeGlow_{color_type})" style="transition: stroke-dashoffset 0.8s ease;" />
<text x="90" y="80" text-anchor="middle" fill="#F8FAFC" font-size="22" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">{clamped_pct:.1f}%</text>
<text x="90" y="98" text-anchor="middle" fill="#94A3B8" font-size="10" font-weight="600" letter-spacing="0.08em" font-family="-apple-system, BlinkMacSystemFont, sans-serif">{label}</text>
</svg>
{subtext_html}
</div>"""
    return clean_html(svg_content)


def render_gpu_status_visual(is_dedicated: bool, raw_name: str, pci_slot: str) -> str:
    """
    Renders an SVG visual status indicator for the GPU card to balance the top-4 card row.
    """
    accent_color = "#4ADE80" if is_dedicated else "#FBBF24"
    status_label = "DEDICATED" if is_dedicated else "VIRTUAL"

    svg = f"""<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; min-height: 96px;">
<svg viewBox="0 0 180 88" width="160" height="80">
<circle cx="90" cy="40" r="32" fill="none" stroke="#16263A" stroke-width="6" />
<circle cx="90" cy="40" r="32" fill="none" stroke="{accent_color}" stroke-width="6" stroke-dasharray="140 60" stroke-linecap="round" />
<text x="90" y="38" text-anchor="middle" fill="#F8FAFC" font-size="11" font-weight="700" letter-spacing="0.06em">{status_label}</text>
<text x="90" y="52" text-anchor="middle" fill="#94A3B8" font-size="9" font-weight="600">CONTROLLER</text>
</svg>
<div style="font-size: 0.78rem; color: #94A3B8; text-align: center; margin-top: -6px;">PCI Slot: {pci_slot}</div>
</div>"""
    return clean_html(svg)


def render_hero_header(ai_active: bool, last_refreshed: str) -> None:
    """Renders the executive title banner with system telemetry pills."""
    engine_badge = (
        f'<span class="hw-status-pill">'
        f'{get_icon("bot", size=15, color="#22D3EE")} '
        f'<span style="color: #22D3EE; font-weight: 600;">Gemini Enhanced</span>'
        f'</span>'
        if ai_active else
        f'<span class="hw-status-pill">'
        f'{get_icon("shield-check", size=15, color="#4ADE80")} '
        f'<span style="color: #4ADE80; font-weight: 600;">Offline Local Engine</span>'
        f'</span>'
    )

    guard_pill = (
        f'<span class="hw-status-pill">'
        f'{get_icon("terminal", size=15, color="#67E8F9")} '
        f'<span>Subprocess Guard: <b>allow-list + shell=False</b></span>'
        f'</span>'
    )

    time_pill = (
        f'<span class="hw-status-pill">'
        f'{get_icon("clock", size=15, color="#94A3B8")} '
        f'<span>Refreshed: <b>{last_refreshed}</b></span>'
        f'</span>'
    )

    html = f"""<div class="hw-hero-banner">
<div>
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
<div class="hw-card-icon-badge" style="width: 44px; height: 44px; background: rgba(37,99,235,0.15); border-color: rgba(6,182,212,0.4);">
{get_icon("layout-dashboard", size=26, color="#22D3EE")}
</div>
<div>
<h1 class="hw-hero-title" style="margin: 0; padding: 0;">HardwareIQ</h1>
<div style="font-size: 0.8rem; font-weight: 600; color: #06B6D4; letter-spacing: 0.08em; text-transform: uppercase;">
Local Linux Hardware Intelligence Suite
</div>
</div>
</div>
<div class="hw-hero-subtitle">
Real-time kernel telemetry and verified hardware inspection. Answers queries strictly based on detected local specifications.
</div>
</div>
<div style="display: flex; flex-direction: column; gap: 8px; align-items: flex-end;">
<div style="display: flex; align-items: center; gap: 8px;">
<span class="pulse-dot"></span>
<span style="font-size: 0.82rem; font-weight: 600; color: #4ADE80; letter-spacing: 0.04em;">SYSTEM ONLINE</span>
</div>
<div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end;">
{engine_badge}
{guard_pill}
{time_pill}
</div>
</div>
</div>"""
    render_html(html)


def render_overview_cards(
    cpu_data: Dict[str, Any],
    mem_data: Dict[str, Any],
    storage_data: Dict[str, Any],
    gpu_data: Dict[str, Any],
    cpu_percent: float
) -> None:
    """Renders the 4 primary hardware cards with gauges and real specifications."""
    col1, col2, col3, col4 = st.columns(4)

    # 1. CPU CARD
    with col1:
        cd = cpu_data.get("details", {})
        cpu_model = cd.get("model_name", "Unknown CPU")
        display_model = cpu_model.replace("Intel(R) ", "").replace("Core(TM) ", "").replace("CPU ", "")
        cores = cd.get("cores_per_socket", "N/A")
        threads = cd.get("total_cpus", "N/A")
        arch = cd.get("architecture", "x86_64")
        freq = f"{cd.get('cpu_mhz', 'N/A')} MHz" if cd.get("cpu_mhz") else "Base Clock"
        gauge_html = render_semicircular_gauge(cpu_percent, label="CPU LOAD", subtext=f"{threads} Threads Active", color_type="cyan")

        card_cpu = f"""<div class="hw-card hw-overview-card">
<div>
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("cpu", size=20, color="#22D3EE")}</div>
<div class="hw-card-title">Processor</div>
</div>
<span class="hw-card-badge badge-live">{arch}</span>
</div>
<div style="margin: 6px 0;">{gauge_html}</div>
</div>
<div style="border-top: 1px solid #1E2D42; padding-top: 8px; margin-top: 6px;">
<div style="font-size: 0.86rem; font-weight: 600; color: #F8FAFC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{cpu_model}">{display_model}</div>
<div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 0.78rem; color: #94A3B8;">
<span>{cores} Cores / {threads} Threads</span>
<span style="color: #38BDF8;">{freq}</span>
</div>
</div>
</div>"""
        render_html(card_cpu)

    # 2. MEMORY CARD
    with col2:
        md = mem_data.get("details", {})
        total_ram = md.get("total_human", "N/A")
        used_ram = md.get("used_human", "N/A")
        avail_ram = md.get("available_human", "N/A")
        cached_ram = md.get("cached_and_buffers_human", "N/A")
        mem_pct = md.get("percent_used", 0.0)
        gauge_html = render_semicircular_gauge(mem_pct, label="RAM USAGE", subtext=f"{used_ram} / {total_ram}", color_type="blue")

        card_mem = f"""<div class="hw-card hw-overview-card">
<div>
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("memory-stick", size=20, color="#3B82F6")}</div>
<div class="hw-card-title">System Memory</div>
</div>
<span class="hw-card-badge badge-live">{total_ram}</span>
</div>
<div style="margin: 6px 0;">{gauge_html}</div>
</div>
<div style="border-top: 1px solid #1E2D42; padding-top: 8px; margin-top: 6px;">
<div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 2px;">
<span style="color: #94A3B8;">Available:</span>
<span style="font-weight: 600; color: #34D399;">{avail_ram}</span>
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
<span style="color: #94A3B8;">Cached/Buffers:</span>
<span style="font-weight: 600; color: #67E8F9;">{cached_ram}</span>
</div>
</div>
</div>"""
        render_html(card_mem)

    # 3. STORAGE CARD
    with col3:
        sd = storage_data.get("details", {})
        total_disk = sd.get("total_physical_disk_human", "N/A")
        disks = sd.get("physical_disks", [])
        disk_model = disks[0].get("model", "Generic Disk") if disks else "No Disk"
        loop_count = sd.get("loop_devices_excluded_count", 0)
        mounted_fs = sd.get("mounted_filesystems", [])
        fs_free = mounted_fs[0].get("free_human", "N/A") if mounted_fs else "N/A"
        fs_pct = mounted_fs[0].get("percent_used", 0.0) if mounted_fs else 0.0
        gauge_html = render_semicircular_gauge(fs_pct, label="DISK USED", subtext=f"{fs_free} Free", color_type="cyan")

        card_storage = f"""<div class="hw-card hw-overview-card">
<div>
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("hard-drive", size=20, color="#06B6D4")}</div>
<div class="hw-card-title">Storage Disks</div>
</div>
<span class="hw-card-badge badge-live">{len(disks)} DISK</span>
</div>
<div style="margin: 6px 0;">{gauge_html}</div>
</div>
<div style="border-top: 1px solid #1E2D42; padding-top: 8px; margin-top: 6px;">
<div style="font-size: 0.86rem; font-weight: 600; color: #F8FAFC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{disk_model}">/dev/sda ({total_disk})</div>
<div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 0.78rem; color: #94A3B8;">
<span>{disk_model}</span>
<span style="color: #67E8F9;">{loop_count} Loops Ignored</span>
</div>
</div>
</div>"""
        render_html(card_storage)

    # 4. GPU CARD
    with col4:
        gd = gpu_data.get("details", {})
        has_ded = gd.get("has_dedicated_gpu", False)
        devices = gd.get("detected_devices", [])
        dev_name = devices[0].get("raw_name", "No GPU Detected") if devices else "None"
        pci_slot = devices[0].get("pci_slot", "00:02.0") if devices else "N/A"
        badge_class = "badge-dedicated" if has_ded else "badge-virtual"
        badge_text = "DEDICATED" if has_ded else "VIRTUAL ADAPTER"
        status_visual = render_gpu_status_visual(has_ded, dev_name, pci_slot)

        card_gpu = f"""<div class="hw-card hw-overview-card">
<div>
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("monitor", size=20, color="#4ADE80" if has_ded else "#F59E0B")}</div>
<div class="hw-card-title">Graphics (GPU)</div>
</div>
<span class="hw-card-badge {badge_class}">{badge_text}</span>
</div>
<div style="margin: 6px 0;">{status_visual}</div>
</div>
<div style="border-top: 1px solid #1E2D42; padding-top: 8px; margin-top: 6px;">
<div style="font-size: 0.86rem; font-weight: 600; color: #F8FAFC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{dev_name}">{dev_name}</div>
<div style="font-size: 0.75rem; color: #FBBF24; margin-top: 4px;">
{"Physical graphics accelerator active." if has_ded else "VirtualBox/VMware emulated. No dedicated GPU."}
</div>
</div>
</div>"""
        render_html(card_gpu)


def render_per_core_chart(per_cpu: List[float]) -> None:
    """
    Renders an Altair multi-layer bar chart for per-core utilization.
    Displays clear background tracks, thick active load bars, and numeric labels.
    """
    if not per_cpu:
        return

    data = pd.DataFrame({
        "Core": [f"Core {i}" for i in range(len(per_cpu))],
        "Load": [float(val) for val in per_cpu],
        "Max": [100.0 for _ in range(len(per_cpu))]
    })

    # Background track bar (100% capacity)
    bg = alt.Chart(data).mark_bar(
        color="#16263A",
        cornerRadius=6,
        size=22
    ).encode(
        x=alt.X("Max:Q", title=None, axis=None),
        y=alt.Y("Core:N", sort=None, title=None, axis=alt.Axis(
            labelColor="#F8FAFC",
            labelFontSize=12,
            labelFontWeight="bold"
        ))
    )

    # Active foreground load bar
    fg = alt.Chart(data).mark_bar(
        cornerRadius=6,
        size=22
    ).encode(
        x=alt.X("Load:Q", scale=alt.Scale(domain=[0, 100]), title=None, axis=None),
        y=alt.Y("Core:N", sort=None),
        color=alt.Color(
            "Load:Q",
            scale=alt.Scale(
                domain=[0, 50, 100],
                range=["#2563EB", "#06B6D4", "#F59E0B"]
            ),
            legend=None
        )
    )

    # Numeric text label beside bar
    txt = alt.Chart(data).mark_text(
        align="left",
        baseline="middle",
        dx=8,
        color="#F8FAFC",
        fontSize=11,
        fontWeight=600
    ).encode(
        x=alt.X("Load:Q"),
        y=alt.Y("Core:N", sort=None),
        text=alt.Text("Load:Q", format=".1f")
    )

    chart = (
        (bg + fg + txt)
        .properties(height=len(per_cpu) * 40 + 20)
        .configure_view(stroke=None)
    )
    st.altair_chart(chart, use_container_width=True)


def render_cpu_telemetry_panel(per_cpu: List[float], cpu_details: Dict[str, Any]) -> None:
    """
    Renders the Multi-Core Processor Load card cleanly without breaking HTML across Streamlit calls.
    """
    header_html = f"""<div class="hw-card-elevated" style="margin-bottom: 0px;">
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("gauge", size=20, color="#22D3EE")}</div>
<div class="hw-card-title">Multi-Core Processor Load</div>
</div>
<span class="hw-card-badge badge-live">{len(per_cpu)} Logical Cores</span>
</div>"""
    render_html(header_html)

    # Render Altair per-core chart
    render_per_core_chart(per_cpu)

    # Telemetry badges at bottom of card
    footer_html = f"""<div style="border-top: 1px solid #1E2D42; padding-top: 10px; margin-top: 12px; display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; font-size: 0.8rem;">
<div><span style="color: #94A3B8;">Clock:</span> <b style="color: #38BDF8;">{cpu_details.get('cpu_mhz', 'N/A')} MHz</b></div>
<div><span style="color: #94A3B8;">L3 Cache:</span> <b style="color: #F8FAFC;">{cpu_details.get('l3_cache', 'Not reported')}</b></div>
<div><span style="color: #94A3B8;">Hypervisor:</span> <b style="color: #22D3EE;">{cpu_details.get('hypervisor_vendor', 'Bare-metal')}</b></div>
</div>
</div>"""
    render_html(footer_html)


def render_memory_breakdown_panel(mem_details: Dict[str, Any]) -> None:
    """
    Renders the Memory Allocation Breakdown card cleanly with visual distribution and metrics.
    """
    pct = mem_details.get("percent_used", 0.0)
    avail_pct = 100.0 - pct
    
    html = f"""<div class="hw-card-elevated" style="margin-bottom: 0px;">
<div class="hw-card-header">
<div class="hw-card-title-group">
<div class="hw-card-icon-badge">{get_icon("database", size=20, color="#38BDF8")}</div>
<div class="hw-card-title">Memory Allocation Breakdown</div>
</div>
<span class="hw-card-badge badge-live">Linux Kernel Accounting</span>
</div>

<div style="margin: 10px 0 16px 0;">
<div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px;">
<span style="color: #94A3B8;">Active Utilization vs. Available</span>
<span style="font-weight: 700; color: #F8FAFC;">{pct}% Used</span>
</div>
<div class="hw-progress-track" style="height: 10px;">
<div class="hw-progress-fill" style="width: {pct}%;"></div>
</div>
</div>

<div style="display: flex; flex-direction: column; gap: 8px;">
<div style="display: flex; justify-content: space-between; align-items: center; padding: 7px 12px; background: rgba(11, 18, 32, 0.6); border-radius: 8px; font-size: 0.82rem;">
<span style="color: #94A3B8;">Actively Used (Applications):</span>
<span style="font-weight: 700; color: #38BDF8;">{mem_details.get('used_human', 'N/A')} ({pct}%)</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; padding: 7px 12px; background: rgba(11, 18, 32, 0.6); border-radius: 8px; font-size: 0.82rem;">
<span style="color: #94A3B8;">Available for New Apps:</span>
<span style="font-weight: 700; color: #34D399;">{mem_details.get('available_human', 'N/A')}</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; padding: 7px 12px; background: rgba(11, 18, 32, 0.6); border-radius: 8px; font-size: 0.82rem;">
<span style="color: #94A3B8;">Reclaimable Cache & Buffers:</span>
<span style="font-weight: 700; color: #67E8F9;">{mem_details.get('cached_and_buffers_human', 'N/A')}</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; padding: 7px 12px; background: rgba(11, 18, 32, 0.6); border-radius: 8px; font-size: 0.82rem;">
<span style="color: #94A3B8;">Completely Free RAM:</span>
<span style="font-weight: 700; color: #F8FAFC;">{mem_details.get('free_human', 'N/A')}</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; padding: 7px 12px; background: rgba(11, 18, 32, 0.6); border-radius: 8px; font-size: 0.82rem;">
<span style="color: #94A3B8;">Active Swap Utilization:</span>
<span style="font-weight: 700; color: #A78BFA;">{mem_details.get('swap_used_human', '0 B')} / {mem_details.get('swap_total_human', '0 B')} ({mem_details.get('swap_percent', 0)}%)</span>
</div>
</div>
</div>"""
    render_html(html)


def render_runtime_history_chart(history_records: List[Dict[str, Any]]) -> None:
    """
    Renders real session time-series line chart.
    Never fabricates historical data. If only 1 sample exists, displays a helpful empty state.
    """
    if len(history_records) < 2:
        html = f"""<div style="background: rgba(13, 20, 34, 0.6); border: 1px dashed #243B53; border-radius: 10px; padding: 24px; text-align: center; color: #94A3B8;">
<div style="margin-bottom: 8px;">{get_icon("activity", size=28, color="#06B6D4")}</div>
<div style="font-weight: 600; color: #CBD5E1; margin-bottom: 4px;">Session Telemetry Recorder Active</div>
<div style="font-size: 0.85rem;">HardwareIQ is recording real-time runtime samples. Refresh hardware data or execute queries to accumulate historical time-series points.</div>
</div>"""
        render_html(html)
        return

    df = pd.DataFrame(history_records)

    melted = df.melt(
        id_vars=["timestamp"],
        value_vars=["cpu_percent", "ram_percent"],
        var_name="Metric",
        value_name="Percentage"
    )
    melted["Metric"] = melted["Metric"].replace({
        "cpu_percent": "CPU Utilization (%)",
        "ram_percent": "RAM Utilization (%)"
    })

    chart = (
        alt.Chart(melted)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("timestamp:N", title="Sample Time", axis=alt.Axis(labelAngle=-25)),
            y=alt.Y("Percentage:Q", scale=alt.Scale(domain=[0, 100]), title="Utilization (%)"),
            color=alt.Color(
                "Metric:N",
                scale=alt.Scale(
                    domain=["CPU Utilization (%)", "RAM Utilization (%)"],
                    range=["#38BDF8", "#06B6D4"]
                ),
                legend=alt.Legend(orient="top", title=None, labelColor="#F8FAFC")
            ),
            tooltip=["timestamp:N", "Metric:N", alt.Tooltip("Percentage:Q", format=".1f")]
        )
        .properties(height=260)
        .configure_view(stroke=None)
        .configure_axis(
            gridColor="#1E2D42",
            domainColor="#243B53",
            labelColor="#94A3B8",
            titleColor="#CBD5E1",
            labelFontSize=11,
            titleFontSize=12
        )
    )
    st.altair_chart(chart, use_container_width=True)


def render_filesystem_table(mounted_fs: List[Dict[str, Any]]) -> None:
    """Renders mounted filesystems with progress bars and free space metrics."""
    if not mounted_fs:
        st.info("No active non-loop filesystem mounts detected.")
        return

    items_html = []
    for fs in mounted_fs:
        pct = fs.get("percent_used", 0.0)
        bar_color = "hw-progress-fill" if pct < 85 else "hw-progress-fill hw-progress-fill-warning"
        items_html.append(f"""<div style="background: rgba(17, 31, 50, 0.6); border: 1px solid #1E2D42; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
<div>
<span style="font-weight: 700; color: #F8FAFC; font-size: 0.95rem;">{fs.get('mountpoint', '/')}</span>
<span style="color: #94A3B8; font-size: 0.8rem; margin-left: 8px;">({fs.get('device', 'dev')} - {fs.get('fstype', 'ext4')})</span>
</div>
<div style="font-size: 0.85rem; font-weight: 600; color: #34D399;">
{fs.get('free_human', 'N/A')} Free
</div>
</div>
<div class="hw-progress-track">
<div class="{bar_color}" style="width: {min(100.0, pct)}%;"></div>
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #94A3B8;">
<span>Used: {fs.get('used_human', 'N/A')}</span>
<span>Total Capacity: {fs.get('total_human', 'N/A')} ({pct}% used)</span>
</div>
</div>""")

    render_html("\n".join(items_html))
