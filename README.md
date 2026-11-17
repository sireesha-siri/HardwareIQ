# 💻 HardwareIQ: Premium Linux Hardware Intelligence Suite

**HardwareIQ** is an offline-first Linux Hardware Monitoring Dashboard and Conversational Assistant designed for Ubuntu systems. It combines deep kernel-level hardware inspection (`lscpu`, `psutil`, `/proc/meminfo`, `lsblk`, `lspci`) with a commercial-grade, dark-tech desktop monitoring interface.

Every specification and metric displayed originates directly from verified local system telemetry. The system **never invents, extrapolates, or hallucinates missing specifications**.

---

## 🎨 Design Identity & Visual System

HardwareIQ features a dark, futuristic hardware intelligence interface inspired by modern desktop diagnostic suites (NZXT CAM, Corsair iCUE, Grafana Hardware dashboards):

* **Color Palette**:
  * **Backgrounds**: `#080B12` (Primary), `#0D1422` (Secondary), `#0B1220` (Sidebar), `#111F32` (Cards), `#16263A` (Elevated Cards), `#243B53` (Borders).
  * **Primary Accents**: `#2563EB` (Electric Blue), `#3B82F6` (Bright Blue), `#06B6D4` (Cyan), `#22D3EE` (Neon Cyan), `#67E8F9` (Light Cyan).
  * **Text**: `#F8FAFC` (Primary), `#CBD5E1` (Secondary), `#94A3B8` (Muted).
  * **Status**: `#22C55E` (Online/Success), `#F59E0B` (Warning/Virtual), `#EF4444` (Error).
* **Layered Radial Gradients**:
  ```css
  radial-gradient(ellipse at 15% 0%, rgba(37,99,235,0.16), transparent 42%),
  radial-gradient(ellipse at 85% 15%, rgba(6,182,212,0.10), transparent 38%),
  linear-gradient(135deg, #080B12 0%, #0D1422 55%, #080B12 100%)
  ```
* **Lucide Icon System (`ui/icons.py`)**:
  * 22 locally embedded SVG icons (`cpu`, `memory-stick`, `hard-drive`, `monitor`, `bot`, `activity`, `terminal`, `refresh-cw`, `message-square`, `send`, `shield-check`, `alert-triangle`, `settings`, `layout-dashboard`, `chevron-right`, `circle-check`, `circle-help`, `chart-no-axes-combined`, `gauge`, `database`, `clock`, `server`).
  * 100% offline with zero CDN dependencies at runtime. Stroke width 1.9, scalable, and styled with cyan accents.
* **Hardware Visualizations (`ui/components.py`)**:
  * **Semicircular Gauges**: SVG arc indicators with gradient stroke and real-time percentage text.
  * **Per-Core CPU Distribution**: Multi-bar Altair chart reporting individual logical core loads (`psutil.cpu_percent(percpu=True)`).
  * **Session Runtime Telemetry**: Multi-series line chart tracking timestamped CPU vs. RAM samples across the session.
  * **Filesystem & Mount Usage**: Disk partition bars distinguishing raw hardware disk size from formatted mount available space.

---

## 🏗️ Architecture & Component Overview

HardwareIQ utilizes a clean, layered architecture separating diagnostic execution, local query routing, and visual presentation:

```
┌─────────────────────────────────────────────────────────────┐
│                 Streamlit Web UI (app.py)                   │
│   - Multi-view navigation (Dashboard, Monitor, Chat, Guard) │
│   - Hero banner with live kernel status pills               │
│   - Sidebar telemetry cards & suggested query chips         │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│    UI Layer (ui/)            │ │   Services Layer (services/)│
│  - ui/icons.py (Lucide SVGs) │ │  - tool_router.py (Local)   │
│  - ui/styles.py (CSS Theme)  │ │  - ai_service.py (Gemini)   │
│  - ui/components.py (Gauges) │ └──────────────┬──────────────┘
└──────────────────────────────┘                │
                                                ▼
┌─────────────────────────────────────────────────────────────┐
│               Hardware Subsystems (hardware/)               │
│  - hardware/cpu.py      (lscpu parser)                      │
│  - hardware/memory.py   (psutil + /proc/meminfo reconciler) │
│  - hardware/storage.py  (lsblk block & partition inspector) │
│  - hardware/gpu.py      (lspci graphics & hypervisor check) │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              utils/command_executor.py                      │
│   - Strict binary & argument allow-list                     │
│   - shell=False strictly enforced (No shell injection)      │
│   - Enforced 5.0s subprocess timeouts                       │
│   - Structured error handling & graceful degradation        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Linux System & Kernel Interfaces             │
│   - /usr/bin/lscpu          - /proc/meminfo                 │
│   - /usr/bin/lsblk          - /usr/bin/lspci                │
│   - psutil virtual_memory   - psutil disk_partitions        │
└─────────────────────────────────────────────────────────────┘
```

### File Hierarchy

```text
/home/siri/HardwareIQ/
├── app.py                      # Multi-view Streamlit dashboard & assistant
├── requirements.txt            # Project dependencies
├── .env.example                # Sample environment configuration
├── .gitignore                  # Git ignore rules for Python & venv
├── README.md                   # Complete documentation
├── ui/
│   ├── __init__.py             # UI module exports
│   ├── icons.py                # 22 locally embedded Lucide SVG icons
│   ├── styles.py               # Complete CSS theme & responsive design system
│   └── components.py           # Semicircular gauges, cards & telemetry charts
├── hardware/
│   ├── __init__.py             # Hardware module exports
│   ├── cpu.py                  # CPU detection via lscpu
│   ├── memory.py               # RAM & Swap detection via psutil + /proc/meminfo
│   ├── storage.py              # Physical disk & filesystem detection via lsblk
│   └── gpu.py                  # Display & graphics detection via lspci
├── services/
│   ├── __init__.py             # Service exports
│   ├── tool_router.py          # Deterministic local query routing & synthesis
│   └── ai_service.py           # Optional Gemini API integration with offline fallback
├── utils/
│   ├── __init__.py             # Utility exports
│   └── command_executor.py     # Safe allow-listed subprocess executor
└── tests/
    ├── __init__.py             # Tests package
    ├── test_hardwareiq.py      # Core subsystem unit tests (35 tests)
    └── test_ui.py              # Lucide icons, theme, & gauge tests (6 tests)
```

---

## 🎯 Engineering & Diagnostic Guarantees

1. **Subprocess Safety (`utils/command_executor.py`)**:
   - Commands are validated against an explicit allow-list of approved binaries (`lscpu`, `lsblk`, `lspci`) and predetermined flag arguments.
   - `shell=False` is strictly enforced.
   - Special shell operators (`;`, `&`, `|`, `` ` ``, `$`, `>`, `<`) are rejected instantly.
   - User inputs are never passed to the command line.

2. **Accurate Memory Accounting without Double-Counting (`hardware/memory.py`)**:
   - Accurately reconciles `psutil.virtual_memory()` with `/proc/meminfo`.
   - Distinctly presents **Total**, **Actively Used** (active application memory: `Total - Free - Buffers - Cached`), **Available** (memory ready for allocation including reclaimable cache), **Completely Free**, and **Cached/Buffers**.

3. **Physical Disk vs. Filesystem Distinction (`hardware/storage.py`)**:
   - Distinguishes raw hardware block devices (`lsblk` disks like `/dev/sda`) from mounted filesystem partitions (`/etc`, `/var`).
   - **Excludes loop devices** (e.g., Snap container mounts) and optical drives (`sr0`) from physical disk capacity calculations.

4. **Honest GPU & Virtualization Distinction (`hardware/gpu.py`)**:
   - Parses PCI display controllers (`lspci`).
   - Emulated hypervisor adapters (e.g. VMware SVGA II, VirtualBox Graphics Adapter) are explicitly labeled as **Virtual / Emulated Graphics Adapters**.
   - Clarifies that no physical dedicated GPU is present rather than misrepresenting virtual adapters.

5. **100% Offline-First Functionality (`services/tool_router.py`)**:
   - Natural-language routing runs locally using keyword scoring and regex pattern matching.
   - Zero external API dependencies and zero network access required.
   - Optional Gemini integration (`services/ai_service.py`) activates only when `GEMINI_API_KEY` is provided; otherwise, it seamlessly defaults to the deterministic local engine.

---

## 🚀 Setup & Launch Instructions

### Prerequisites
* **Operating System**: Ubuntu 20.04 LTS
* **Python Runtime**: Python 3.8.10
* **Pre-existing Virtual Environment**: `./venv`

### Step 1: Navigate to Project Directory & Activate Virtual Environment
```bash
cd /home/siri/HardwareIQ
source venv/bin/activate
```

### Step 2: (Optional) Configure Gemini API Key
To use the optional Gemini synthesis layer, copy `.env.example` to `.env` and insert your key:
```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key_here
```
> *Note: If `.env` is omitted or `GEMINI_API_KEY` is blank, HardwareIQ runs in 100% offline local mode.*

### Step 3: Launch the Dashboard Application
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Access the dashboard in your browser at:
`http://localhost:8501` (or your remote server IP on port `8501`).

---

## 🧪 Automated Testing

HardwareIQ includes an automated test suite covering command allow-listing, hardware detection, memory calculation, disk filtering, GPU virtualization checks, natural-language routing, Lucide icons, theme styles, and Streamlit rendering.

### Run All Tests
```bash
./venv/bin/python -m unittest discover tests
```

### Test Results
```text
Ran 35 tests in tests/test_hardwareiq.py: OK
Ran 6 tests in tests/test_ui.py: OK
Total: 41 tests passed
```

All 41 tests passed (35 in `test_hardwareiq.py`, 6 in `test_ui.py`):

**Core Subsystem, Architecture & Gemini Tests (`tests/test_hardwareiq.py` — 35 tests):**
- `test_permitted_command`: Verifies allow-listed binaries pass validation.
- `test_disallowed_command_rejected`: Verifies unauthorized binaries (`rm`, `bash`, `cat`) are rejected.
- `test_disallowed_arguments_rejected`: Blocks unapproved flags.
- `test_shell_injection_characters_rejected`: Blocks shell operators (`;`, `|`, `&`).
- `test_run_safe_command_execution`: Verifies subprocess execution with timeout.
- `test_cpu_detection_structure`: Validates CPU specifications parsed from `lscpu`.
- `test_cpu_markdown_formatting`: Verifies CPU Markdown summary generation.
- `test_memory_detection_structure`: Validates RAM metrics from `psutil` and `/proc/meminfo`.
- `test_bytes_to_human_conversion`: Verifies byte conversion to GiB/MiB.
- `test_storage_detection_structure`: Validates storage detection via `lsblk`.
- `test_loop_device_exclusion`: Confirms loopback devices are excluded from physical disk totals.
- `test_gpu_detection_structure`: Validates PCI bus graphics scanning.
- `test_gpu_virtualization_classification`: Confirms VMware/VirtualBox adapters are classified as virtual.
- `test_intent_classification`: Tests natural-language intent classification across all components.
- `test_routing_execution`: Verifies accurate responses to specific questions.
- `test_offline_fallback`: Verifies graceful operation when offline without an API key.
- `test_gemini_model_configuration`: Verifies configured Gemini model is `gemini-3.8-flash`.
- `test_call_gemini_api_uses_gemini_38_flash_endpoint`: Verifies `call_gemini_api` sends requests to the `gemini-3.8-flash` endpoint with grounded diagnostic context.
- `test_call_gemini_api_network_error_fallback`: Verifies graceful fallback to offline mode on network or API exceptions.
- `test_streamlit_app_loads`: Uses Streamlit's `AppTest` to verify that the UI renders without exceptions.
- `test_navigation_persistence_and_double_click`: Verifies double-clicking active navigation never resets the view.
- `test_session_state_preserved_during_navigation`: Verifies messages and telemetry persist across view switches.
- `test_all_views_render_without_exception`: Verifies all 4 dashboard sections render cleanly.
- `test_view_system_dashboard`: Validates clean rendering of the System Dashboard overview.
- `test_view_real_time_monitoring`: Validates live telemetry graphs and metrics rendering.
- `test_view_ai_hardware_assistant`: Validates conversational assistant interface and history rendering.
- `test_view_subprocess_security`: Validates allow-list audit table and command execution viewer.
- `test_chat_input_flow_and_clear_chat`: Verifies asking a question redirects to Assistant and Clear Chat resets history.
- `test_altair_chart_specs_transparent_background`: Verifies Altair chart specifications have transparent backgrounds and fills.
- `test_donut_chart_and_multi_core_timeline`: Verifies donut chart and multi-core history charts create valid transparent specs.
- `test_telemetry_recording_per_core_data`: Verifies session telemetry records per-core utilization readings.
- `test_theme_css_contains_dark_overrides`: Confirms all dark theme tokens, bottom containers, and Vega transparency.
- `test_gauge_and_memory_panel_rendering`: Verifies SVG semicircular gauge output, GPU visual, and HTML cleaning.
- `test_unknown_intent_polite_fallback`: Verifies out-of-scope query routing returns helpful guidance.
- `test_overview_intent_synthesis`: Verifies complete system specification breakdown on overview questions.

**UI, Theme & Visual Component Tests (`tests/test_ui.py` — 6 tests):**
- `test_all_specified_icons_exist`: Verifies all 22 required Lucide icons exist in the local SVG dictionary.
- `test_icon_svg_generation`: Verifies SVG markup, size, stroke color, and accessibility attributes.
- `test_fallback_icon`: Verifies graceful fallback for unknown icon names.
- `test_css_color_tokens`: Confirms all specified color system hex codes exist in the theme stylesheet.
- `test_semicircular_gauge_generation`: Verifies SVG gauge arc calculation and text labels.
- `test_semicircular_gauge_clamping`: Confirms gauges clamp inputs to [0%, 100%].

---

## 💬 Sample Questions & Answers

| Category | Sample Question | Sample Response Summary |
|---|---|---|
| **CPU** | *"How many cores does my CPU have?"* | *"This system is equipped with **2 physical core(s)** and **2 logical thread(s)** on an **Intel(R) Pentium(R) CPU 5405U @ 2.30GHz**."* |
| **RAM** | *"How much RAM is free and available?"* | *"There is **779.70 MiB of completely free memory** and **3.07 GiB available memory** (which includes reclaimable cache) out of **5.64 GiB total RAM**."* |
| **Storage** | *"What hard drives are installed?"* | *"The system has **1 physical disk(s)** totaling **25.00 GiB** in raw storage capacity (Drive `/dev/sda`, Model: `VBOX HARDDISK`, 15 loop devices excluded)."* |
| **GPU** | *"Do I have a dedicated GPU?"* | *"**No dedicated physical GPU is detected.** The system is using a virtual/emulated display adapter (**VMware SVGA II Adapter**) under hypervisor virtualization."* |
| **Overview** | *"Show system specs"* | Displays a complete system hardware breakdown with CPU, RAM, Storage, and GPU sections. |
| **Out-of-Scope**| *"What is the weather in Paris?"* | Politeness fallback explaining that HardwareIQ is a local hardware assistant, with suggested valid queries. |
