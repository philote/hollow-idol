"""Tests for config dataclasses and printer presets.

These tests do not import CadQuery — they only exercise pure-Python logic.
"""
import pytest

from hollow_idol.config import MoldConfig, PrinterConfig
from hollow_idol.printers import get_printer, list_printers


class TestPrinterConfig:
    def test_defaults(self):
        p = PrinterConfig()
        assert p.printer_name == "generic"
        assert p.bed_x == 200.0
        assert p.bed_y == 200.0
        assert p.bed_z == 200.0

    def test_custom_values(self):
        p = PrinterConfig(printer_name="my_printer", bed_x=300, bed_y=300, bed_z=400)
        assert p.printer_name == "my_printer"
        assert p.bed_x == 300
        assert p.bed_z == 400

    def test_frozen(self):
        p = PrinterConfig()
        with pytest.raises(Exception):
            p.bed_x = 999  # type: ignore[misc]


class TestMoldConfig:
    def test_defaults(self):
        m = MoldConfig()
        assert m.model_file is None
        assert m.shrink_factor == 1.13
        assert m.case_wall == 4.0
        assert m.plaster_wall_min == 30.0
        assert m.split_axis == "Y"
        assert m.split_positions == [0.0]
        assert m.num_parts == 2
        assert m.natch_radius == 6.0
        assert m.natch_depth == 3.0
        assert m.natches_per_edge == 2
        assert m.slip_well_diameter == 40.0
        assert m.slip_well_height == 20.0
        assert m.draft_angle_deg == 3.0
        assert m.bounding_box_padding == 10.0
        assert m.clip_width == 15.0
        assert m.clip_height == 10.0
        assert m.clip_depth == 6.0
        assert m.blank_width == 100.0
        assert m.blank_depth == 100.0
        assert m.blank_height == 120.0
        assert m.chamfer_size == 3.0
        assert m.orientation_notch_size == 8.0

    def test_custom_values(self):
        m = MoldConfig(blank_width=80, blank_depth=60, shrink_factor=1.10)
        assert m.blank_width == 80
        assert m.blank_depth == 60
        assert m.shrink_factor == 1.10

    def test_split_positions_default_is_independent(self):
        # Each instance gets its own list
        m1 = MoldConfig()
        m2 = MoldConfig()
        m1.split_positions.append(10.0)
        assert m2.split_positions == [0.0]


class TestGetPrinter:
    def test_known_printer(self):
        p = get_printer("bambu_x1c")
        assert p.bed_x == 256
        assert p.bed_y == 256
        assert p.bed_z == 256
        assert "Bambu" in p.printer_name

    def test_case_insensitive(self):
        p1 = get_printer("bambu_x1c")
        p2 = get_printer("BAMBU_X1C")
        assert p1.printer_name == p2.printer_name

    def test_override(self):
        p = get_printer("prusa_mk4", bed_z=300)
        assert p.bed_z == 300
        # Other fields unchanged
        assert p.bed_x == 250

    def test_unknown_printer_raises(self):
        with pytest.raises(KeyError, match="Unknown printer preset"):
            get_printer("does_not_exist")

    def test_list_printers(self):
        names = list_printers()
        assert isinstance(names, list)
        assert "bambu_x1c" in names
        assert "prusa_mk4" in names
        assert "elegoo_saturn3" in names
        # Returned sorted
        assert names == sorted(names)
