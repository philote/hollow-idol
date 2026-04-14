"""
Smoke + dimension tests for mold_case geometry.

Layer 1 — Smoke: each builder produces a non-empty Part.
Layer 2 — Dimensions: bounding boxes match config math within tolerance.

Run with:  pytest tests/test_mold_case.py -v
"""

import math
import pytest
from build123d import Part

from hollow_idol.config import MoldConfig, PrinterConfig
from hollow_idol.mold_case import (
    PANEL_HEIGHT,
    build_wall_piece,
    build_bottom,
    build_half_a,
    build_half_b,
    generate,
)

TOL = 0.5  # mm tolerance for bounding-box checks


# ── Fixtures / parametrize configs ────────────────────────────────────────────

DEFAULT_CFG = MoldConfig()  # all defaults

SMALL_CFG = MoldConfig(
    outer_x=80.0,
    outer_y=60.0,
    outer_z=30.0,
    wall=4.0,
    hemi_r=5.0,
    hemi_height=2.5,
    hemi_offset=12.0,
    flange_width=8.0,
    flange_thickness=2.5,
)

LARGE_CFG = MoldConfig(
    outer_x=150.0,
    outer_y=120.0,
    outer_z=60.0,
    wall=6.0,
    hemi_r=8.0,
    hemi_height=4.0,
    hemi_offset=20.0,
    flange_width=12.0,
    flange_thickness=4.0,
)

ALL_CONFIGS = [
    pytest.param(DEFAULT_CFG, id="default"),
    pytest.param(SMALL_CFG,   id="small"),
    pytest.param(LARGE_CFG,   id="large"),
]

PRINTER = PrinterConfig("test-bed", bed_x=300, bed_y=300, bed_z=300)


# ── Helpers ────────────────────────────────────────────────────────────────────

def bbox_size(part: Part) -> tuple[float, float, float]:
    """Return (size_x, size_y, size_z) of a part's bounding box."""
    bb = part.bounding_box()
    return (
        bb.max.X - bb.min.X,
        bb.max.Y - bb.min.Y,
        bb.max.Z - bb.min.Z,
    )


def is_valid_part(part) -> bool:
    return isinstance(part, Part) and part.volume > 0


# ── Layer 1: Smoke tests ───────────────────────────────────────────────────────

class TestSmoke:
    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_wall_piece_builds(self, cfg):
        part = build_wall_piece(cfg)
        assert is_valid_part(part), "wall piece has zero or negative volume"

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_bottom_convex_builds(self, cfg):
        part = build_bottom(cfg, convex_keys=True, has_notch=True)
        assert is_valid_part(part)

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_bottom_concave_builds(self, cfg):
        part = build_bottom(cfg, convex_keys=False, has_notch=False)
        assert is_valid_part(part)

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_half_a_builds(self, cfg):
        wl, wr, bot = build_half_a(cfg)
        for part in (wl, wr, bot):
            assert is_valid_part(part)

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_half_b_builds(self, cfg):
        wl, wr, bot = build_half_b(cfg)
        for part in (wl, wr, bot):
            assert is_valid_part(part)

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_generate_returns_six_parts(self, cfg):
        parts = generate(cfg, PRINTER)
        assert len(parts) == 6
        for p in parts:
            assert is_valid_part(p)


# ── Layer 2: Dimension invariants ─────────────────────────────────────────────

class TestWallPieceDimensions:
    """
    Wall piece bounding box expectations:
      X:  outer_x + 2 * flange_width   (back wall + both flanges)
      Y:  outer_y / 2                  (back wall to open arm tips at Y=0)
      Z:  outer_z
    """

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_wall_x_extent(self, cfg):
        part = build_wall_piece(cfg)
        sx, _, _ = bbox_size(part)
        expected = cfg.outer_x + 2 * cfg.flange_width
        assert abs(sx - expected) < TOL, (
            f"wall X={sx:.3f}, expected {expected:.3f} "
            f"(outer_x={cfg.outer_x} + 2*flange_width={cfg.flange_width})"
        )

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_wall_y_extent(self, cfg):
        part = build_wall_piece(cfg)
        _, sy, _ = bbox_size(part)
        expected = cfg.outer_y / 2
        assert abs(sy - expected) < TOL, (
            f"wall Y={sy:.3f}, expected {expected:.3f} (outer_y/2)"
        )

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_wall_z_extent(self, cfg):
        part = build_wall_piece(cfg)
        _, _, sz = bbox_size(part)
        assert abs(sz - cfg.outer_z) < TOL, (
            f"wall Z={sz:.3f}, expected {cfg.outer_z:.3f}"
        )


class TestBottomDimensions:
    """
    Panel bounding box expectations:
      X:  outer_x - 2*wall - tongue_clearance
      Y:  outer_y - 2*wall - tongue_clearance
      Z:  static panel height                      (slab height, before keys/notch)

    Keys and notch protrude above the slab — Z total will be larger.
    We check the floor-to-groove height via the minimum Z span of the slab body,
    approximated by checking Z total is >= slab_h and <= slab_h + key headroom.
    """

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_panel_x_extent(self, cfg):
        part = build_bottom(cfg, convex_keys=True, has_notch=False)
        sx, _, _ = bbox_size(part)
        expected = cfg.outer_x - 2 * cfg.wall - cfg.tongue_clearance
        assert abs(sx - expected) < TOL, (
            f"panel X={sx:.3f}, expected {expected:.3f}"
        )

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_panel_y_extent(self, cfg):
        part = build_bottom(cfg, convex_keys=True, has_notch=False)
        _, sy, _ = bbox_size(part)
        expected = cfg.outer_y - 2 * cfg.wall - cfg.tongue_clearance
        assert abs(sy - expected) < TOL, (
            f"panel Y={sy:.3f}, expected {expected:.3f}"
        )

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_panel_slab_height_lower_bound(self, cfg):
        """Z must be at least the static panel height (5.0mm)."""
        part = build_bottom(cfg, convex_keys=True, has_notch=False)
        _, _, sz = bbox_size(part)
        slab_h = PANEL_HEIGHT
        assert sz >= slab_h - TOL, (
            f"panel Z={sz:.3f} is less than slab height {slab_h:.3f}"
        )

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_panel_slab_height_upper_bound(self, cfg):
        """Z must not exceed slab + key height + notch headroom."""
        part = build_bottom(cfg, convex_keys=True, has_notch=True)
        _, _, sz = bbox_size(part)
        slab_h = PANEL_HEIGHT
        max_z = slab_h + cfg.hemi_height + cfg.notch_h + TOL
        assert sz <= max_z, (
            f"panel Z={sz:.3f} exceeds max expected {max_z:.3f}"
        )

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_concave_panel_not_taller_than_convex(self, cfg):
        """Concave (divot) panel must be <= convex (bump) panel Z height."""
        convex = build_bottom(cfg, convex_keys=True,  has_notch=False)
        concave = build_bottom(cfg, convex_keys=False, has_notch=False)
        _, _, sz_convex  = bbox_size(convex)
        _, _, sz_concave = bbox_size(concave)
        assert sz_concave <= sz_convex + TOL, (
            f"concave panel Z={sz_concave:.3f} taller than convex Z={sz_convex:.3f}"
        )


class TestFitInvariants:
    """
    Cross-piece fit checks: the panel must be narrower than the wall interior.
    """

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_panel_fits_inside_wall_x(self, cfg):
        wall = build_wall_piece(cfg)
        panel = build_bottom(cfg, convex_keys=True, has_notch=False)
        inner_x = cfg.outer_x - 2 * cfg.wall
        sx_panel, _, _ = bbox_size(panel)
        assert sx_panel < inner_x + TOL, (
            f"panel X={sx_panel:.3f} does not fit in wall interior X={inner_x:.3f}"
        )

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_panel_fits_inside_wall_y(self, cfg):
        panel = build_bottom(cfg, convex_keys=True, has_notch=False)
        inner_y = cfg.outer_y - 2 * cfg.wall
        _, sy_panel, _ = bbox_size(panel)
        assert sy_panel < inner_y + TOL, (
            f"panel Y={sy_panel:.3f} does not fit in wall interior Y={inner_y:.3f}"
        )

    @pytest.mark.parametrize("cfg", ALL_CONFIGS)
    def test_hemi_offset_within_panel(self, cfg):
        """Key centres must be inside the panel footprint."""
        panel_half_x = (cfg.outer_x - 2 * cfg.wall - cfg.tongue_clearance) / 2
        panel_half_y = (cfg.outer_y - 2 * cfg.wall - cfg.tongue_clearance) / 2
        key_x = panel_half_x - cfg.hemi_offset
        key_y = panel_half_y - cfg.hemi_offset
        assert key_x > cfg.hemi_r, (
            f"hemi centre X={key_x:.3f} too close to panel edge (hemi_r={cfg.hemi_r})"
        )
        assert key_y > cfg.hemi_r, (
            f"hemi centre Y={key_y:.3f} too close to panel edge (hemi_r={cfg.hemi_r})"
        )
