"""
Geometry reporter — builds all 6 mold pieces and prints a JSON summary.

Useful for LLM iteration: run after a geometry change and paste the output
into the conversation to verify dimensions without opening PrusaSlicer.

Usage:
    python -m hollow_idol.reporter
    python -m hollow_idol.reporter --outer-x 120 --outer-y 100 --outer-z 50
    python -m hollow_idol.reporter --json          # machine-readable JSON only
"""

import argparse
import json
import sys

from hollow_idol.config import MoldConfig
from hollow_idol.mold_case import PANEL_HEIGHT, build_wall_piece, build_bottom


def _bbox_dict(part) -> dict:
    bb = part.bounding_box()
    sx = round(bb.max.X - bb.min.X, 3)
    sy = round(bb.max.Y - bb.min.Y, 3)
    sz = round(bb.max.Z - bb.min.Z, 3)
    return {
        "size_x": sx,
        "size_y": sy,
        "size_z": sz,
        "volume_mm3": round(part.volume, 1),
        "min": {"x": round(bb.min.X, 3), "y": round(bb.min.Y, 3), "z": round(bb.min.Z, 3)},
        "max": {"x": round(bb.max.X, 3), "y": round(bb.max.Y, 3), "z": round(bb.max.Z, 3)},
    }


def _expected(cfg: MoldConfig) -> dict:
    """Derived dimension expectations from config math."""
    panel_x = cfg.outer_x - 2 * cfg.wall - cfg.tongue_clearance
    panel_y = cfg.outer_y - 2 * cfg.wall - cfg.tongue_clearance
    key_x   = (panel_x / 2) - cfg.hemi_offset
    key_y   = (panel_y / 2) - cfg.hemi_offset
    return {
        "wall_x_expected":   round(cfg.outer_x + 2 * cfg.flange_width, 3),
        "wall_y_expected":   round(cfg.outer_y / 2, 3),
        "wall_z_expected":   round(cfg.outer_z, 3),
        "panel_x_expected":  round(panel_x, 3),
        "panel_y_expected":  round(panel_y, 3),
        "slab_h_expected":   round(PANEL_HEIGHT, 3),
        "hemi_centre_x":     round(key_x, 3),
        "hemi_centre_y":     round(key_y, 3),
        "hemi_fits_x_margin": round(key_x - cfg.hemi_r, 3),
        "hemi_fits_y_margin": round(key_y - cfg.hemi_r, 3),
    }


def run_report(cfg: MoldConfig, json_only: bool = False) -> dict:
    pieces = {
        "wall_piece":       build_wall_piece(cfg),
        "bottom_convex":    build_bottom(cfg, convex_keys=True,  has_notch=True),
        "bottom_concave":   build_bottom(cfg, convex_keys=False, has_notch=False),
    }

    report = {
        "config": {
            "outer_x":          cfg.outer_x,
            "outer_y":          cfg.outer_y,
            "outer_z":          cfg.outer_z,
            "wall":             cfg.wall,
            "tongue_clearance": cfg.tongue_clearance,
            "hemi_r":           cfg.hemi_r,
            "hemi_height":      cfg.hemi_height,
            "hemi_offset":      cfg.hemi_offset,
            "flange_width":     cfg.flange_width,
            "flange_thickness": cfg.flange_thickness,
        },
        "expected": _expected(cfg),
        "geometry": {name: _bbox_dict(part) for name, part in pieces.items()},
    }

    # Add pass/fail flags comparing actual vs expected
    exp = report["expected"]
    geo = report["geometry"]
    tol = 0.5
    checks = {
        "wall_x_ok":    abs(geo["wall_piece"]["size_x"]    - exp["wall_x_expected"])  < tol,
        "wall_y_ok":    abs(geo["wall_piece"]["size_y"]    - exp["wall_y_expected"])  < tol,
        "wall_z_ok":    abs(geo["wall_piece"]["size_z"]    - exp["wall_z_expected"])  < tol,
        "panel_x_ok":   abs(geo["bottom_convex"]["size_x"] - exp["panel_x_expected"]) < tol,
        "panel_y_ok":   abs(geo["bottom_convex"]["size_y"] - exp["panel_y_expected"]) < tol,
        "panel_z_ok":   geo["bottom_convex"]["size_z"] >= exp["slab_h_expected"] - tol,
        "hemi_fits_x":  exp["hemi_fits_x_margin"] > 0,
        "hemi_fits_y":  exp["hemi_fits_y_margin"] > 0,
    }
    report["checks"] = checks
    report["all_checks_pass"] = all(checks.values())

    if json_only:
        print(json.dumps(report, indent=2))
    else:
        _pretty_print(report)

    return report


def _pretty_print(r: dict) -> None:
    cfg = r["config"]
    exp = r["expected"]
    geo = r["geometry"]
    chk = r["checks"]

    def tick(ok): return "PASS" if ok else "FAIL"

    print("=" * 60)
    print("  MOLD GEOMETRY REPORT")
    print("=" * 60)
    print(f"\nConfig: {cfg['outer_x']} x {cfg['outer_y']} x {cfg['outer_z']} mm  "
          f"(wall={cfg['wall']}, panel clearance={cfg['tongue_clearance']})")

    print("\n-- Wall piece (C-frame) --")
    w = geo["wall_piece"]
    print(f"  Actual:    X={w['size_x']}  Y={w['size_y']}  Z={w['size_z']}  vol={w['volume_mm3']} mm³")
    print(f"  Expected:  X={exp['wall_x_expected']}  Y={exp['wall_y_expected']}  Z={exp['wall_z_expected']}")
    print(f"  Checks:    X [{tick(chk['wall_x_ok'])}]  Y [{tick(chk['wall_y_ok'])}]  Z [{tick(chk['wall_z_ok'])}]")

    print("\n-- Bottom panel (convex keys + notch) --")
    b = geo["bottom_convex"]
    print(f"  Actual:    X={b['size_x']}  Y={b['size_y']}  Z={b['size_z']}  vol={b['volume_mm3']} mm³")
    print(f"  Expected:  X={exp['panel_x_expected']}  Y={exp['panel_y_expected']}  slab_h>={exp['slab_h_expected']}")
    print(f"  Checks:    X [{tick(chk['panel_x_ok'])}]  Y [{tick(chk['panel_y_ok'])}]  Z>slab_h [{tick(chk['panel_z_ok'])}]")

    print("\n-- Bottom panel (concave keys) --")
    c = geo["bottom_concave"]
    print(f"  Actual:    X={c['size_x']}  Y={c['size_y']}  Z={c['size_z']}  vol={c['volume_mm3']} mm³")

    print("\n-- Registration key fit --")
    print(f"  Hemi centre X margin from edge: {exp['hemi_fits_x_margin']} mm [{tick(chk['hemi_fits_x'])}]")
    print(f"  Hemi centre Y margin from edge: {exp['hemi_fits_y_margin']} mm [{tick(chk['hemi_fits_y'])}]")

    status = "ALL PASS" if r["all_checks_pass"] else "FAILURES DETECTED"
    print(f"\n{'=' * 60}")
    print(f"  {status}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m hollow_idol.reporter",
        description="Geometry reporter — dimensions and sanity checks for all mold pieces.",
    )
    parser.add_argument("--outer-x",          type=float, default=100.0)
    parser.add_argument("--outer-y",          type=float, default=80.0)
    parser.add_argument("--outer-z",          type=float, default=40.0)
    parser.add_argument("--wall",             type=float, default=5.0)
    parser.add_argument("--tongue-clearance", type=float, default=0.25)
    parser.add_argument("--hemi-r",           type=float, default=6.0)
    parser.add_argument("--hemi-height",      type=float, default=3.0)
    parser.add_argument("--hemi-offset",      type=float, default=15.0)
    parser.add_argument("--flange-width",     type=float, default=10.0)
    parser.add_argument("--flange-thickness", type=float, default=3.0)
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON only")
    args = parser.parse_args()

    cfg = MoldConfig(
        outer_x=args.outer_x,
        outer_y=args.outer_y,
        outer_z=args.outer_z,
        wall=args.wall,
        tongue_clearance=args.tongue_clearance,
        hemi_r=args.hemi_r,
        hemi_height=args.hemi_height,
        hemi_offset=args.hemi_offset,
        flange_width=args.flange_width,
        flange_thickness=args.flange_thickness,
    )

    report = run_report(cfg, json_only=args.json)
    sys.exit(0 if report["all_checks_pass"] else 1)


if __name__ == "__main__":
    main()
