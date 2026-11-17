"""
HardwareIQ - UI Module Tests
Validates the Lucide icon system, theme stylesheet, and SVG gauge components.
Compatible with Python 3.8+ using standard unittest.
"""

import unittest
from ui.icons import get_icon, LUCIDE_PATHS
from ui.styles import get_theme_css
from ui.components import render_semicircular_gauge


class TestUIIcons(unittest.TestCase):
    """Tests that the locally embedded Lucide icon system generates valid SVGs."""

    def test_all_specified_icons_exist(self):
        expected_icons = [
            "cpu", "memory-stick", "hard-drive", "monitor", "bot",
            "activity", "terminal", "refresh-cw", "message-square", "send",
            "shield-check", "alert-triangle", "settings", "layout-dashboard",
            "chevron-right", "circle-check", "circle-help",
            "chart-no-axes-combined", "gauge", "database", "clock", "server"
        ]
        for name in expected_icons:
            self.assertIn(name, LUCIDE_PATHS, f"Icon '{name}' missing from Lucide dictionary")

    def test_icon_svg_generation(self):
        svg = get_icon("cpu", size=28, color="#06B6D4")
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.endswith("</svg>"))
        self.assertIn('width="28"', svg)
        self.assertIn('height="28"', svg)
        self.assertIn('stroke="#06B6D4"', svg)
        self.assertIn('stroke-width="1.9"', svg)

    def test_fallback_icon(self):
        svg = get_icon("non_existent_icon_name")
        self.assertTrue(svg.startswith("<svg"))


class TestUIThemeStyles(unittest.TestCase):
    """Tests that the CSS theme stylesheet contains the required design system tokens."""

    def test_css_color_tokens(self):
        css = get_theme_css()
        self.assertIn("#080B12", css)  # Primary background
        self.assertIn("#0D1422", css)  # Secondary background
        self.assertIn("#111F32", css)  # Main card background
        self.assertIn("#06B6D4", css)  # Cyan accent
        self.assertIn("#2563EB", css)  # Electric blue accent
        self.assertIn("radial-gradient", css)
        self.assertIn("prefers-reduced-motion", css)


class TestUIGauges(unittest.TestCase):
    """Tests the semicircular gauge SVG generator."""

    def test_semicircular_gauge_generation(self):
        gauge_html = render_semicircular_gauge(45.5, label="CPU LOAD", subtext="2 Cores")
        self.assertIn("<svg", gauge_html)
        self.assertIn("45.5%", gauge_html)
        self.assertIn("CPU LOAD", gauge_html)
        self.assertIn("2 Cores", gauge_html)

    def test_semicircular_gauge_clamping(self):
        gauge_over = render_semicircular_gauge(150.0)
        self.assertIn("100.0%", gauge_over)

        gauge_under = render_semicircular_gauge(-25.0)
        self.assertIn("0.0%", gauge_under)


if __name__ == "__main__":
    unittest.main()
