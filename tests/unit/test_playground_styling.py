"""Unit tests for Vibehuntr playground styling.

Tests verify that Vibehuntr branding and CSS styling are properly applied
to all UI elements in the playground interface.

Requirements: 6.1, 6.2, 6.3, 6.4
"""

import pytest
import re
from app.playground_style import VIBEHUNTR_STYLE, VIBEHUNTR_HEADER


class TestVibehuntrStyleConstants:
    """Test that style constants are properly defined."""
    
    def test_vibehuntr_style_exists(self):
        """Test that VIBEHUNTR_STYLE constant is defined and non-empty."""
        assert VIBEHUNTR_STYLE is not None
        assert isinstance(VIBEHUNTR_STYLE, str)
        assert len(VIBEHUNTR_STYLE) > 0
    
    def test_vibehuntr_header_exists(self):
        """Test that VIBEHUNTR_HEADER constant is defined and non-empty."""
        assert VIBEHUNTR_HEADER is not None
        assert isinstance(VIBEHUNTR_HEADER, str)
        assert len(VIBEHUNTR_HEADER) > 0
    
    def test_style_is_valid_html(self):
        """Test that VIBEHUNTR_STYLE contains valid HTML style tags."""
        assert "<style>" in VIBEHUNTR_STYLE
        assert "</style>" in VIBEHUNTR_STYLE
    
    def test_header_is_valid_html(self):
        """Test that VIBEHUNTR_HEADER contains valid HTML."""
        assert "<div" in VIBEHUNTR_HEADER
        assert "</div>" in VIBEHUNTR_HEADER


class TestBrandingElements:
    """Test that core branding elements are present.
    
    Requirements: 6.1, 6.3
    """
    
    def test_vibehuntr_logo_present(self):
        """Test that Vibehuntr logo/name is present in header."""
        assert "Vibehuntr" in VIBEHUNTR_HEADER
    
    def test_vibehuntr_tagline_present(self):
        """Test that Vibehuntr tagline is present in header."""
        # Check for tagline text
        assert "Discover" in VIBEHUNTR_HEADER or "Plan" in VIBEHUNTR_HEADER or "Vibe" in VIBEHUNTR_HEADER
    
    def test_vibehuntr_emoji_present(self):
        """Test that branding emoji is present in header."""
        assert "🎉" in VIBEHUNTR_HEADER
    
    def test_header_has_branding_classes(self):
        """Test that header contains Vibehuntr-specific CSS classes."""
        assert "vibehuntr-header" in VIBEHUNTR_HEADER
        assert "vibehuntr-logo" in VIBEHUNTR_HEADER
        assert "vibehuntr-tagline" in VIBEHUNTR_HEADER


class TestBrandColors:
    """Test that Vibehuntr brand colors are applied.
    
    Requirements: 6.1, 6.2
    """
    
    def test_primary_brand_color_present(self):
        """Test that primary brand color (#FF6B6B) is used in styles."""
        # Primary coral/red color
        assert "#FF6B6B" in VIBEHUNTR_STYLE or "255, 107, 107" in VIBEHUNTR_STYLE
    
    def test_secondary_brand_color_present(self):
        """Test that secondary brand color (#FF8E8E) is used in styles."""
        # Lighter coral color
        assert "#FF8E8E" in VIBEHUNTR_STYLE or "255, 142, 142" in VIBEHUNTR_STYLE
    
    def test_dark_background_colors_present(self):
        """Test that dark background colors are used for theme."""
        # Dark theme colors
        assert "#0F0F1E" in VIBEHUNTR_STYLE or "#1A1A2E" in VIBEHUNTR_STYLE
    
    def test_gradient_styling_present(self):
        """Test that gradient styling is applied for brand effect."""
        assert "linear-gradient" in VIBEHUNTR_STYLE
        assert "gradient" in VIBEHUNTR_STYLE.lower()


class TestFontStyling:
    """Test that Lexend font (Vibehuntr brand font) is applied.
    
    Requirements: 6.1, 6.2
    """
    
    def test_lexend_font_import(self):
        """Test that Lexend font is imported from Google Fonts."""
        assert "Lexend" in VIBEHUNTR_STYLE
        assert "fonts.googleapis.com" in VIBEHUNTR_STYLE
    
    def test_lexend_font_applied_globally(self):
        """Test that Lexend font is set as default font family."""
        assert "font-family: 'Lexend'" in VIBEHUNTR_STYLE or "font-family:'Lexend'" in VIBEHUNTR_STYLE
    
    def test_font_weights_defined(self):
        """Test that multiple font weights are imported."""
        # Check for font weight range in import
        font_import_match = re.search(r'wght@[\d;]+', VIBEHUNTR_STYLE)
        assert font_import_match is not None


class TestChatMessageStyling:
    """Test that chat messages have Vibehuntr styling applied.
    
    Requirements: 6.1, 6.2
    """
    
    def test_chat_message_styling_present(self):
        """Test that .stChatMessage styling is defined."""
        assert ".stChatMessage" in VIBEHUNTR_STYLE
    
    def test_chat_message_has_background(self):
        """Test that chat messages have styled background."""
        # Find the .stChatMessage block and check for background
        chat_msg_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stChatMessage"):]
        assert "background" in chat_msg_section[:500]
    
    def test_chat_message_has_border_radius(self):
        """Test that chat messages have rounded corners."""
        chat_msg_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stChatMessage"):]
        assert "border-radius" in chat_msg_section[:500]
    
    def test_chat_message_has_border(self):
        """Test that chat messages have styled borders."""
        chat_msg_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stChatMessage"):]
        assert "border" in chat_msg_section[:500]
    
    def test_user_message_styling_distinct(self):
        """Test that user messages have distinct styling."""
        assert "user-message" in VIBEHUNTR_STYLE
    
    def test_assistant_message_styling_distinct(self):
        """Test that assistant messages have distinct styling."""
        assert "assistant-message" in VIBEHUNTR_STYLE


class TestButtonStyling:
    """Test that buttons have Vibehuntr styling applied.
    
    Requirements: 6.1, 6.2
    """
    
    def test_button_styling_present(self):
        """Test that .stButton styling is defined."""
        assert ".stButton" in VIBEHUNTR_STYLE
    
    def test_button_has_gradient_background(self):
        """Test that buttons use gradient background with brand colors."""
        button_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stButton"):]
        assert "gradient" in button_section[:500].lower()
        assert "#FF6B6B" in button_section[:500] or "255, 107, 107" in button_section[:500]
    
    def test_button_has_hover_effect(self):
        """Test that buttons have hover effects defined."""
        assert ":hover" in VIBEHUNTR_STYLE
        # Check for hover in button context
        button_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stButton"):]
        assert "hover" in button_section[:1000].lower()
    
    def test_button_has_border_radius(self):
        """Test that buttons have rounded corners."""
        button_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stButton"):]
        assert "border-radius" in button_section[:500]


class TestErrorMessageStyling:
    """Test that error messages use styled containers.
    
    Requirements: 6.2, 6.4
    """
    
    def test_error_styling_present(self):
        """Test that .stError styling is defined."""
        assert ".stError" in VIBEHUNTR_STYLE
    
    def test_error_has_background(self):
        """Test that error messages have styled background."""
        error_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stError"):]
        assert "background" in error_section[:300]
    
    def test_error_has_border(self):
        """Test that error messages have styled border."""
        error_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stError"):]
        assert "border" in error_section[:300]
    
    def test_error_has_border_radius(self):
        """Test that error messages have rounded corners."""
        error_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stError"):]
        assert "border-radius" in error_section[:300]
    
    def test_success_styling_present(self):
        """Test that .stSuccess styling is defined."""
        assert ".stSuccess" in VIBEHUNTR_STYLE
    
    def test_warning_styling_present(self):
        """Test that .stWarning styling is defined."""
        assert ".stWarning" in VIBEHUNTR_STYLE
    
    def test_info_styling_present(self):
        """Test that .stInfo styling is defined."""
        assert ".stInfo" in VIBEHUNTR_STYLE


class TestInputStyling:
    """Test that input fields have Vibehuntr styling.
    
    Requirements: 6.1, 6.2
    """
    
    def test_text_input_styling_present(self):
        """Test that text input styling is defined."""
        assert ".stTextInput" in VIBEHUNTR_STYLE
    
    def test_text_area_styling_present(self):
        """Test that text area styling is defined."""
        assert ".stTextArea" in VIBEHUNTR_STYLE
    
    def test_input_has_background(self):
        """Test that inputs have styled background."""
        input_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stTextInput"):]
        assert "background" in input_section[:500]
    
    def test_input_has_border(self):
        """Test that inputs have styled border with brand color."""
        input_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stTextInput"):]
        assert "border" in input_section[:500]
        assert "#FF6B6B" in input_section[:500] or "255, 107, 107" in input_section[:500]
    
    def test_input_has_focus_state(self):
        """Test that inputs have focus state styling."""
        input_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stTextInput"):]
        assert "focus" in input_section[:800].lower()


class TestLayoutStyling:
    """Test that layout elements have Vibehuntr styling.
    
    Requirements: 6.1, 6.3
    """
    
    def test_app_background_styled(self):
        """Test that main app background is styled."""
        assert ".stApp" in VIBEHUNTR_STYLE
        app_section = VIBEHUNTR_STYLE[VIBEHUNTR_STYLE.find(".stApp"):]
        assert "background" in app_section[:300]
    
    def test_sidebar_styling_present(self):
        """Test that sidebar has Vibehuntr styling."""
        assert "stSidebar" in VIBEHUNTR_STYLE
    
    def test_header_styling_present(self):
        """Test that header has styling defined."""
        assert "header" in VIBEHUNTR_STYLE.lower()
    
    def test_expander_styling_present(self):
        """Test that expander (for older messages) has styling."""
        assert "expander" in VIBEHUNTR_STYLE.lower()


class TestResponsiveDesign:
    """Test that responsive design elements are present.
    
    Requirements: 6.1, 6.3
    """
    
    def test_border_radius_for_modern_look(self):
        """Test that border-radius is used throughout for modern appearance."""
        # Count occurrences of border-radius
        border_radius_count = VIBEHUNTR_STYLE.count("border-radius")
        assert border_radius_count >= 5, "Should have border-radius on multiple elements"
    
    def test_padding_defined(self):
        """Test that padding is defined for proper spacing."""
        padding_count = VIBEHUNTR_STYLE.count("padding")
        assert padding_count >= 3, "Should have padding on multiple elements"
    
    def test_scrollbar_styling_present(self):
        """Test that custom scrollbar styling is defined."""
        assert "scrollbar" in VIBEHUNTR_STYLE.lower()


class TestAccessibility:
    """Test that styling maintains accessibility.
    
    Requirements: 6.2
    """
    
    def test_color_contrast_for_text(self):
        """Test that text colors are defined for readability."""
        assert "color:" in VIBEHUNTR_STYLE or "color :" in VIBEHUNTR_STYLE
    
    def test_focus_states_defined(self):
        """Test that focus states are defined for keyboard navigation."""
        assert ":focus" in VIBEHUNTR_STYLE
    
    def test_hover_states_defined(self):
        """Test that hover states are defined for interactive elements."""
        assert ":hover" in VIBEHUNTR_STYLE


class TestSpecialEffects:
    """Test that special visual effects are applied.
    
    Requirements: 6.1, 6.2
    """
    
    def test_glassmorphism_effect_present(self):
        """Test that glassmorphism effect is defined."""
        assert "glass-card" in VIBEHUNTR_STYLE or "backdrop-filter" in VIBEHUNTR_STYLE
    
    def test_box_shadow_present(self):
        """Test that box shadows are used for depth."""
        assert "box-shadow" in VIBEHUNTR_STYLE
    
    def test_transitions_present(self):
        """Test that transitions are defined for smooth animations."""
        assert "transition" in VIBEHUNTR_STYLE
    
    def test_gradient_text_effect(self):
        """Test that gradient text effect is used for branding."""
        assert "background-clip: text" in VIBEHUNTR_STYLE or "-webkit-background-clip: text" in VIBEHUNTR_STYLE


class TestConsistency:
    """Test that styling is consistent across components.
    
    Requirements: 6.1, 6.2, 6.3
    """
    
    def test_important_flag_usage(self):
        """Test that !important is used to override Streamlit defaults."""
        important_count = VIBEHUNTR_STYLE.count("!important")
        assert important_count >= 10, "Should use !important to override Streamlit styles"
    
    def test_rgba_transparency_usage(self):
        """Test that rgba colors are used for transparency effects."""
        assert "rgba(" in VIBEHUNTR_STYLE
    
    def test_consistent_border_radius_values(self):
        """Test that border-radius values are consistent (8px, 12px, 16px)."""
        assert "12px" in VIBEHUNTR_STYLE
        assert "16px" in VIBEHUNTR_STYLE
    
    def test_brand_color_consistency(self):
        """Test that brand colors appear multiple times throughout."""
        # Primary brand color should appear in multiple places
        ff6b6b_count = VIBEHUNTR_STYLE.count("#FF6B6B") + VIBEHUNTR_STYLE.count("255, 107, 107")
        assert ff6b6b_count >= 3, "Primary brand color should be used consistently"


class TestMarkdownRendering:
    """Test that markdown rendering is styled.
    
    Requirements: 6.2
    """
    
    def test_header_styling_defined(self):
        """Test that h1, h2, h3 headers have styling."""
        assert "h1" in VIBEHUNTR_STYLE
        assert "h2" in VIBEHUNTR_STYLE
        assert "h3" in VIBEHUNTR_STYLE
    
    def test_link_styling_defined(self):
        """Test that links have Vibehuntr styling."""
        # Check for 'a' tag styling
        assert " a " in VIBEHUNTR_STYLE or " a{" in VIBEHUNTR_STYLE or "\na " in VIBEHUNTR_STYLE
    
    def test_code_block_styling_defined(self):
        """Test that code blocks have styling."""
        assert "Code" in VIBEHUNTR_STYLE or "code" in VIBEHUNTR_STYLE.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
