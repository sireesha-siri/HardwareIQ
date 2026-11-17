"""
HardwareIQ - CSS Design System & Theme Styles
Custom styling for the Streamlit hardware monitoring dashboard and assistant.
Strictly implements the specified dark-tech color palette, layered radial gradients,
card elevations, responsive typography, locally embedded Lucide icon navigation,
and eliminates all white backgrounds in any browser environment.
Compatible with Python 3.8+ and Streamlit 1.39.0.
"""

import urllib.parse
from ui.icons import LUCIDE_PATHS


def make_svg_data_uri(name: str, color: str = "#22D3EE") -> str:
    """Encodes a local Lucide SVG path into a CSS data URI."""
    path = LUCIDE_PATHS.get(name, "")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f'{path}'
        f'</svg>'
    )
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)


def get_theme_css() -> str:
    """Returns the complete CSS stylesheet for HardwareIQ with Lucide SVG navigation and theme overrides."""
    # Navigation icons
    uri_dashboard = make_svg_data_uri("layout-dashboard", "#22D3EE")
    uri_monitoring = make_svg_data_uri("activity", "#22D3EE")
    uri_assistant = make_svg_data_uri("bot", "#22D3EE")
    uri_security = make_svg_data_uri("shield-check", "#22D3EE")

    # Action button icons
    uri_refresh = make_svg_data_uri("refresh-cw", "#22D3EE")
    uri_clear = make_svg_data_uri("trash-2", "#EF4444")

    # Quick query button icons
    uri_q_cpu = make_svg_data_uri("cpu", "#38BDF8")
    uri_q_cores = make_svg_data_uri("gauge", "#38BDF8")
    uri_q_ram = make_svg_data_uri("memory-stick", "#38BDF8")
    uri_q_mem_util = make_svg_data_uri("database", "#38BDF8")
    uri_q_disks = make_svg_data_uri("hard-drive", "#38BDF8")
    uri_q_gpu = make_svg_data_uri("monitor", "#38BDF8")
    uri_q_overview = make_svg_data_uri("layout-dashboard", "#38BDF8")

    return f"""
<style>
/* ==========================================================================
   HARDWAREIQ THEME SYSTEM & CSS RESET
   Strict Dark Tech Identity: Corsair iCUE / NZXT CAM / Grafana Aesthetic
   ========================================================================== */

:root {{
    --bg-primary: #080B12;
    --bg-secondary: #0D1422;
    --bg-sidebar: #0B1220;
    --bg-card: #111F32;
    --bg-card-elevated: #16263A;
    --border-subtle: #243B53;
    --border-highlight: rgba(6, 182, 212, 0.4);
    
    --accent-blue-deep: #2563EB;
    --accent-blue-bright: #3B82F6;
    --accent-cyan-core: #06B6D4;
    --accent-cyan-neon: #22D3EE;
    --accent-cyan-light: #67E8F9;
    
    --text-primary: #F8FAFC;
    --text-secondary: #CBD5E1;
    --text-muted: #94A3B8;
    
    --status-success: #22C55E;
    --status-warning: #F59E0B;
    --status-error: #EF4444;
}}

/* Universal Dark Background Across Entire Window */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background-color: var(--bg-primary) !important;
    background:
        radial-gradient(ellipse at 15% 0%, rgba(37, 99, 235, 0.16), transparent 42%),
        radial-gradient(ellipse at 85% 15%, rgba(6, 182, 212, 0.10), transparent 38%),
        linear-gradient(135deg, #080B12 0%, #0D1422 55%, #080B12 100%) !important;
    color: var(--text-primary) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    overflow-x: hidden !important;
}}

/* Main Centered Layout with Safe Bottom Padding (Prevents overlap with fixed chat input) */
.main .block-container {{
    max-width: 1380px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 7.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    margin-left: auto !important;
    margin-right: auto !important;
}}

/* Hide Default Streamlit Header/Footer/Decoration */
#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stDecoration"] {{
    visibility: hidden !important;
    display: none !important;
    height: 0 !important;
}}

/* ==========================================================================
   ELIMINATE EVERY WHITE BACKGROUND (ALTAIR CHARTS & BOTTOM CONTAINERS)
   ========================================================================== */

/* Vega-Lite / Altair Chart Transparency Overrides */
.vega-embed,
.vega-embed svg,
.vega-embed canvas,
.vega-embed rect.background,
div[data-testid="stVegaLiteChart"] {{
    background: transparent !important;
    background-color: transparent !important;
    fill: transparent !important;
}}

/* Streamlit Floating Bottom Container (Fixes white bar in Microsoft Edge / Light Mode) */
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
.stChatFloatingInputContainer {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
}}

[data-testid="stBottom"] > div {{
    background: linear-gradient(180deg, rgba(8, 11, 18, 0) 0%, rgba(8, 11, 18, 0.94) 28%, #080B12 100%) !important;
    padding-bottom: 1.25rem !important;
}}

/* Chat Input Styling */
[data-testid="stChatInput"] {{
    background-color: var(--bg-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.6) !important;
    transition: all 0.25s ease !important;
}}

[data-testid="stChatInput"]:focus-within {{
    border-color: var(--accent-cyan-core) !important;
    box-shadow: 0 0 18px rgba(6, 182, 212, 0.25) !important;
}}

[data-testid="stChatInput"] textarea {{
    background-color: transparent !important;
    color: var(--text-primary) !important;
    font-size: 0.92rem !important;
}}

[data-testid="stChatInput"] textarea::placeholder {{
    color: var(--text-muted) !important;
}}

[data-testid="stChatInput"] button {{
    background: transparent !important;
    color: var(--accent-cyan-core) !important;
    border: none !important;
}}

[data-testid="stChatInput"] button:hover {{
    color: var(--accent-cyan-neon) !important;
}}

/* ==========================================================================
   SIDEBAR NAVIGATION: LUCIDE ICONS & SLEEK PILLS (NO EMOJIS / NO RADIO DOTS)
   ========================================================================== */

/* Sidebar Customization (Clean Original Appearance) */
[data-testid="stSidebar"] {{
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-subtle) !important;
    box-shadow: none !important;
}}

[data-testid="stSidebar"] .block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
}}

/* Hide default circular radio input dots */
div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {{
    display: none !important;
}}

div[data-testid="stRadio"] div[role="radiogroup"] {{
    display: flex !important;
    flex-direction: column !important;
    gap: 6px !important;
}}

div[data-testid="stRadio"] div[role="radiogroup"] > label {{
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    background: #0D1726 !important;
    border: 1px solid #1E2D42 !important;
    border-radius: 9px !important;
    padding: 10px 14px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    width: 100% !important;
}}

div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {{
    background: #16263A !important;
    border-color: #06B6D4 !important;
    transform: translateX(2px) !important;
}}

div[data-testid="stRadio"] div[role="radiogroup"] > label p,
div[data-testid="stRadio"] div[role="radiogroup"] > label span {{
    color: var(--text-secondary) !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
}}

div[data-testid="stRadio"] div[role="radiogroup"] > label:hover p,
div[data-testid="stRadio"] div[role="radiogroup"] > label:hover span {{
    color: var(--text-primary) !important;
}}

/* Active state styling */
div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"],
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {{
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.25) 0%, rgba(6, 182, 212, 0.18) 100%) !important;
    border: 1px solid #06B6D4 !important;
    box-shadow: 0 4px 16px rgba(6, 182, 212, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
}}

div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] p,
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p {{
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}}

/* Navigation Prefix Icons */
div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1)::before {{
    content: "";
    display: inline-block;
    width: 20px;
    height: 20px;
    background: url("{uri_dashboard}") no-repeat center;
    background-size: contain;
    flex-shrink: 0;
}}

div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(2)::before {{
    content: "";
    display: inline-block;
    width: 20px;
    height: 20px;
    background: url("{uri_monitoring}") no-repeat center;
    background-size: contain;
    flex-shrink: 0;
}}

div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(3)::before {{
    content: "";
    display: inline-block;
    width: 20px;
    height: 20px;
    background: url("{uri_assistant}") no-repeat center;
    background-size: contain;
    flex-shrink: 0;
}}

div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(4)::before {{
    content: "";
    display: inline-block;
    width: 20px;
    height: 20px;
    background: url("{uri_security}") no-repeat center;
    background-size: contain;
    flex-shrink: 0;
}}

/* ==========================================================================
   SIDEBAR ACTION & QUICK QUERY BUTTONS (WITH LOCALLY EMBEDDED LUCIDE ICONS)
   ========================================================================== */

/* Common Sidebar Button Styling */
[data-testid="stSidebar"] div.stButton > button {{
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-size: 0.82rem !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    background: rgba(13, 20, 34, 0.7) !important;
    border: 1px solid #1E2D42 !important;
    color: var(--text-secondary) !important;
    width: 100% !important;
    margin-bottom: 4px !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}

[data-testid="stSidebar"] div.stButton > button:hover {{
    background: rgba(22, 38, 58, 0.95) !important;
    border-color: var(--accent-cyan-core) !important;
    color: var(--text-primary) !important;
    transform: translateX(3px) !important;
    box-shadow: 0 4px 14px rgba(6, 182, 212, 0.18) !important;
}}

/* Sidebar Refresh & Clear Action Buttons */
[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] div.stButton > button {{
    justify-content: center !important;
    font-size: 0.78rem !important;
    padding: 8px 6px !important;
    font-weight: 600 !important;
}}

/* Refresh Telemetry Button Icon */
[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] div[data-testid="column"]:first-child button::before {{
    content: "";
    display: inline-block;
    width: 15px;
    height: 15px;
    background: url("{uri_refresh}") no-repeat center;
    background-size: contain;
    margin-right: 4px;
    flex-shrink: 0;
}}

/* Clear Chat Button Icon */
[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] div[data-testid="column"]:last-child button::before {{
    content: "";
    display: inline-block;
    width: 15px;
    height: 15px;
    background: url("{uri_clear}") no-repeat center;
    background-size: contain;
    margin-right: 4px;
    flex-shrink: 0;
}}

/* Quick Query 7 Buttons: Sequential Lucide Icons */
.sidebar-queries div.stButton:nth-of-type(1) button::before,
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div.stButton:nth-of-type(1) button::before {{
    content: "";
    display: inline-block;
    width: 16px;
    height: 16px;
    background: url("{uri_q_cpu}") no-repeat center;
    background-size: contain;
    flex-shrink: 0;
}}

.sidebar-queries div.stButton:nth-of-type(2) button::before,
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div.stButton:nth-of-type(2) button::before {{
    content: "";
    display: inline-block;
    width: 16px;
    height: 16px;
    background: url("{uri_q_cores}") no-repeat center;
    background-size: contain;
    flex-shrink: 0;
}}

.sidebar-queries div.stButton:nth-of-type(3) button::before,
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div.stButton:nth-of-type(3) button::before {{
    content: "";
    display: inline-block;
    width: 16px;
    height: 16px;
    background: url("{uri_q_ram}") no-repeat center;
    background-size: contain;
    flex-shrink: 0;
}}

.sidebar-queries div.stButton:nth-of-type(4) button::before,
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div.stButton:nth-of-type(4) button::before {{
    content: "";
    display: inline-block;
    width: 16px;
    height: 16px;
    background: url("{uri_q_mem_util}") no-repeat center;
    background-size: contain;
    flex-shrink: 0;
}}

.sidebar-queries div.stButton:nth-of-type(5) button::before,
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div.stButton:nth-of-type(5) button::before {{
    content: "";
    display: inline-block;
    width: 16px;
    height: 16px;
    background: url("{uri_q_disks}") no-repeat center;
    background-size: contain;
    flex-shrink: 0;
}}

.sidebar-queries div.stButton:nth-of-type(6) button::before,
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div.stButton:nth-of-type(6) button::before {{
    content: "";
    display: inline-block;
    width: 16px;
    height: 16px;
    background: url("{uri_q_gpu}") no-repeat center;
    background-size: contain;
    flex-shrink: 0;
}}

.sidebar-queries div.stButton:nth-of-type(7) button::before,
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div.stButton:nth-of-type(7) button::before {{
    content: "";
    display: inline-block;
    width: 16px;
    height: 16px;
    background: url("{uri_q_overview}") no-repeat center;
    background-size: contain;
    flex-shrink: 0;
}}

/* ==========================================================================
   CUSTOM CARDS & CONTAINERS
   Responsive Layout & Bulletproof Badge Wrapping
   ========================================================================== */

.hw-card {{
    background: linear-gradient(145deg, #111F32 0%, #0D1726 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 16px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
    box-sizing: border-box;
    width: 100%;
}}

.hw-card:hover {{
    border-color: var(--accent-cyan-core);
    box-shadow: 0 12px 32px rgba(6, 182, 212, 0.14), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    transform: translateY(-2px);
}}

/* Balanced Overview Card Flex Layout */
.hw-overview-card {{
    min-height: 295px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    box-sizing: border-box !important;
}}

.hw-card-elevated {{
    background: linear-gradient(145deg, #16263A 0%, #101B2B 100%);
    border: 1px solid rgba(6, 182, 212, 0.25);
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 14px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    width: 100%;
    box-sizing: border-box;
}}

/* Top Subtle Glowing Border Line */
.hw-card::before, .hw-card-elevated::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 15%;
    right: 15%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.6), transparent);
}}

/* Card Header Structure with Responsive Wrapping (Never Clips or Overflows) */
.hw-card-header {{
    display: flex !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 6px 8px !important;
    margin-bottom: 10px !important;
    width: 100% !important;
}}

.hw-card-title-group {{
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
}}

.hw-card-icon-badge {{
    width: 34px !important;
    height: 34px !important;
    border-radius: 8px !important;
    background: rgba(6, 182, 212, 0.1) !important;
    border: 1px solid rgba(6, 182, 212, 0.25) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}}

.hw-card-title {{
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.01em !important;
    line-height: 1.25 !important;
}}

.hw-card-badge {{
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    padding: 2px 8px !important;
    border-radius: 9999px !important;
    letter-spacing: 0.03em !important;
    text-transform: uppercase !important;
    white-space: nowrap !important;
    flex-shrink: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1.25 !important;
    box-sizing: border-box !important;
    max-width: 100% !important;
}}

.badge-virtual {{
    background: rgba(245, 158, 11, 0.15) !important;
    color: #FBBF24 !important;
    border: 1px solid rgba(245, 158, 11, 0.35) !important;
}}

.badge-dedicated {{
    background: rgba(34, 197, 94, 0.15) !important;
    color: #4ADE80 !important;
    border: 1px solid rgba(34, 197, 94, 0.35) !important;
}}

.badge-live {{
    background: rgba(6, 182, 212, 0.15) !important;
    color: var(--accent-cyan-neon) !important;
    border: 1px solid rgba(6, 182, 212, 0.35) !important;
}}

/* Hero Banner */
.hw-hero-banner {{
    background: linear-gradient(135deg, rgba(17, 31, 50, 0.85) 0%, rgba(13, 20, 34, 0.95) 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}}

.hw-hero-title {{
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #F8FAFC 0%, #CBD5E1 40%, #22D3EE 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}}

.hw-hero-subtitle {{
    font-size: 0.90rem;
    color: var(--text-secondary);
    max-width: 650px;
    line-height: 1.45;
}}

.hw-status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: rgba(11, 18, 32, 0.85);
    border: 1px solid var(--border-subtle);
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-secondary);
}}

.pulse-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--status-success);
    box-shadow: 0 0 10px var(--status-success);
    animation: pulseGlow 2s infinite;
}}

@keyframes pulseGlow {{
    0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }}
    70% {{ transform: scale(1.05); box-shadow: 0 0 0 7px rgba(34, 197, 94, 0); }}
    100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
}}

/* ==========================================================================
   CHAT MESSAGES, EXPANDERS & GENERAL CONTAINERS
   ========================================================================== */

/* Chat Messages */
[data-testid="stChatMessage"] {{
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    margin-bottom: 12px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.18) 0%, rgba(17, 31, 50, 0.95) 100%) !important;
    border-color: rgba(37, 99, 235, 0.45) !important;
}}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.12) 0%, rgba(17, 31, 50, 0.95) 100%) !important;
    border-color: rgba(6, 182, 212, 0.35) !important;
}}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {{
    color: var(--text-primary) !important;
}}

/* Expanders */
[data-testid="stExpander"] {{
    background-color: #0D1726 !important;
    border: 1px solid #1E2D42 !important;
    border-radius: 10px !important;
    margin-top: 8px !important;
    overflow: hidden !important;
}}

[data-testid="stExpander"] summary {{
    color: var(--text-secondary) !important;
    padding: 10px 14px !important;
}}

[data-testid="stExpander"] summary:hover {{
    color: var(--accent-cyan-neon) !important;
}}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    background-color: var(--bg-primary) !important;
    border-top: 1px solid #1E2D42 !important;
    padding: 14px !important;
}}

/* JSON Display */
div.react-json-view,
[data-testid="stJson"] {{
    background-color: var(--bg-primary) !important;
    border-radius: 8px !important;
}}

/* General Buttons */
.stButton > button {{
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}

.stButton > button:hover {{
    background: var(--bg-card-elevated) !important;
    border-color: var(--accent-cyan-core) !important;
    color: var(--accent-cyan-neon) !important;
    box-shadow: 0 4px 14px rgba(6, 182, 212, 0.2) !important;
    transform: translateY(-1px) !important;
}}

/* Progress Track and Fill */
.hw-progress-track {{
    width: 100%;
    height: 7px;
    background: rgba(36, 59, 83, 0.6);
    border-radius: 9999px;
    margin: 8px 0 6px 0;
    overflow: hidden;
}}

.hw-progress-fill {{
    height: 100%;
    border-radius: 9999px;
    background: linear-gradient(90deg, #2563EB 0%, #06B6D4 100%);
    transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}}

.hw-progress-fill-warning {{
    background: linear-gradient(90deg, #F59E0B 0%, #EF4444 100%) !important;
}}

/* Responsive Adjustments */
@media (max-width: 1080px) {{
    .main .block-container {{
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
    }}
    .hw-hero-banner {{
        flex-direction: column;
        align-items: flex-start;
        gap: 16px;
    }}
}}

@media (max-width: 640px) {{
    .main .block-container {{
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }}
    .hw-card {{
        padding: 14px 16px;
    }}
    .hw-hero-title {{
        font-size: 1.35rem;
    }}
}}

@media (prefers-reduced-motion: reduce) {{
    * {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }}
}}
</style>
"""
