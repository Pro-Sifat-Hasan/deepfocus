"""
Unit tests for colors module.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.colors import (
    PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT,
    BLOCKED, UNBLOCKED, WARNING, SUCCESS, ERROR,
    WHITE, BLACK, GREY_600, TRANSPARENT
)


class TestColors:
    """Test color constants."""

    def test_primary_colors_are_hex(self):
        """Test primary colors are valid hex strings."""
        assert PRIMARY.startswith("#")
        assert PRIMARY_DARK.startswith("#")
        assert PRIMARY_LIGHT.startswith("#")

    def test_status_colors_are_hex(self):
        """Test status colors are valid hex strings."""
        assert BLOCKED.startswith("#")
        assert WARNING.startswith("#")
        assert ERROR.startswith("#")

    def test_neutral_colors_are_hex(self):
        """Test neutral colors are valid hex strings."""
        assert WHITE == "#ffffff"
        assert BLACK == "#000000"
        assert GREY_600.startswith("#")

    def test_transparent_is_string(self):
        """Test transparent is correct string."""
        assert TRANSPARENT == "transparent"

    def test_primary_color_is_niagara(self):
        """Test primary color is Niagara theme."""
        # Niagara color should be in teal/green range
        assert PRIMARY == "#08b69d"

    def test_success_equals_primary(self):
        """Test success color equals primary."""
        assert SUCCESS == PRIMARY

    def test_unblocked_equals_primary(self):
        """Test unblocked color equals primary."""
        assert UNBLOCKED == PRIMARY
