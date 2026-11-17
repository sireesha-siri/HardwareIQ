"""
HardwareIQ - CSS Design System & Theme Styles
Custom styling for the Streamlit hardware monitoring dashboard and assistant.
Strictly implements the specified color palette, gradients, card elevations,
responsive typography, and locally embedded Lucide icon navigation.
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
    """Returns the complete CSS stylesheet for HardwareIQ with Lucide SVG navigation."""
    uri_dashboard = make_svg_data_uri("layout-dashboard", "#22D3EE")
    uri_monitoring = make_svg_data_uri("activity", "#22D3EE")
    uri_assistant = make_svg_data_uri("bot", "#22D3EE")
    uri_security = make_svg_data_uri("shield-check", "#22D3EE")

    return f"""
<style>
/* ==========================================================================
   HARDWAREIQ THEME SYSTEM & CSS RESET
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

/* Global Background with Layered Radial Gradients */
.stApp {{
    background:
        radial-gradient(ellipse at 15% 0%, rgba(37,99,235,0.16), transparent 42%),
        radial-gradient(ellipse at 85% 15%, rgba(6,182,212,0.10), transparent 38%),
        linear-gradient(135deg, #080B12 0%, #0D1422 55%, #080B12 100%) !important;
    color: var(--text-primary) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    overflow-x: hidden !important;
}}

/* Centered Main Layout Container (Fixes Horizontal Stretch & Excessive Empty Space) */
.main .block-container {{
    max-width: 1380px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    margin-left: auto !important;
    margin-right: auto !important;
}}

/* Sidebar Customization */
[data-testid="stSidebar"] {{
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-subtle) !important;
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.6) !important;
}}

[data-testid="stSidebar"] .block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
}}

/* Hide Default Streamlit Header/Footer */
#MainMenu, footer, header[data-testid="stHeader"] {{
    visibility: hidden !important;
    height: 0 !important;
}}

/* ==========================================================================
   SIDEBAR NAVIGATION: LUCIDE ICONS & SLEEK PILLS (NO EMOJIS / NO RADIO DOTS)
   ========================================================================== */

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
    background: linear-gradient(135deg, rgba(37,99,235,0.25) 0%, rgba(6,182,212,0.18) 100%) !important;
    border: 1px solid #06B6D4 !important;
    box-shadow: 0 4px 16px rgba(6, 182, 212, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
}}

div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] p,
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p {{
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}}

/* Inject Lucide SVGs as aligned prefix icons */
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

/* Sidebar Quick Query Buttons */
[data-testid="stSidebar"] div.stButton > button {{
    text-align: left !important;
    justify-content: flex-start !important;
    font-size: 0.82rem !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    background: rgba(13, 20, 34, 0.7) !important;
    border: 1px solid #1E2D42 !important;
    color: var(--text-secondary) !important;
    width: 100% !important;
    margin-bottom: 2px !important;
}}

[data-testid="stSidebar"] div.stButton > button:hover {{
    background: rgba(22, 38, 58, 0.95) !important;
    border-color: var(--accent-cyan-core) !important;
    color: var(--text-primary) !important;
    transform: translateX(3px) !important;
    box-shadow: 0 4px 12px rgba(6, 182, 212, 0.15) !important;
}}

/* ==========================================================================
   CUSTOM CARDS & CONTAINERS
   ========================================================================== */

.hw-card {{
    background: linear-gradient(145deg, #111F32 0%, #0D1726 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 18px 20px;
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
    min-height: 295px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}

.hw-card-elevated {{
    background: linear-gradient(145deg, #16263A 0%, #101B2B 100%);
    border: 1px solid rgba(6, 182, 212, 0.25);
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    width: 100%;
    box-sizing: border-box;
}}

/* Card Top Glowing Border Line */
.hw-card::before, .hw-card-elevated::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 15%;
    right: 15%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.6), transparent);
}}

/* Card Header Structure */
.hw-card-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}}

.hw-card-title-group {{
    display: flex;
    align-items: center;
    gap: 10px;
}}

.hw-card-icon-badge {{
    width: 38px;
    height: 38px;
    border-radius: 8px;
    background: rgba(6, 182, 212, 0.1);
    border: 1px solid rgba(6, 182, 212, 0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}}

.hw-card-title {{
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.01em;
}}

.hw-card-badge {{
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 9999px;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}}

.badge-virtual {{
    background: rgba(245, 158, 11, 0.15);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.35);
}}

.badge-dedicated {{
    background: rgba(34, 197, 94, 0.15);
    color: #4ADE80;
    border: 1px solid rgba(34, 197, 94, 0.35);
}}

.badge-live {{
    background: rgba(6, 182, 212, 0.15);
    color: var(--accent-cyan-neon);
    border: 1px solid rgba(6, 182, 212, 0.35);
}}

.hw-primary-value {{
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    margin: 4px 0 6px 0;
}}

/* ==========================================================================
   PROGRESS BARS & HERO BANNER
   ========================================================================== */

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

.hw-hero-banner {{
    background: linear-gradient(135deg, rgba(17, 31, 50, 0.85) 0%, rgba(13, 20, 34, 0.95) 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}}

.hw-hero-title {{
    font-size: 1.7rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #F8FAFC 0%, #CBD5E1 40%, #22D3EE 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}}

.hw-hero-subtitle {{
    font-size: 0.92rem;
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

/* Chat & Form Overrides */
[data-testid="stChatInput"] {{
    border-color: var(--border-subtle) !important;
    background-color: var(--bg-secondary) !important;
    border-radius: 12px !important;
}}

[data-testid="stChatInput"]:focus-within {{
    border-color: var(--accent-cyan-core) !important;
    box-shadow: 0 0 16px rgba(6, 182, 212, 0.2) !important;
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
