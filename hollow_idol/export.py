"""STL / STEP export and flat-lay print arrangement.

Flat-lay arranges all mold halves so each part sits with its floor on the
build plate (Z=0) and its open parting face pointing up, then spaces them
apart along X for easy slicing.

For Y-axis parting (default): each tray has its floor in the -Y direction and
its open face at Y=0.  Rotating 90° around the X-axis brings the floor to
Z=0 and the open face to the top — the correct print orientation.
"""
from __future__ import annotations

import os

import cadquery as cq

from hollow_idol.config import PrinterConfig


def export_stl(solid: cq.Workplane, path: str) -> None:
    """Export solid to STL at the given path (directories created as needed)."""
    _ensure_dir(path)
    cq.exporters.export(solid, path)


def export_step(solid: cq.Workplane, path: str) -> None:
    """Export solid to STEP at the given path (directories created as needed)."""
    _ensure_dir(path)
    cq.exporters.export(solid, path)


def flat_lay_arrange(
    halves: list[cq.Workplane],
    split_axis: str = "Y",
) -> list[cq.Workplane]:
    """Orient each mold tray half for printing and space along X.

    For Y-axis parting (default):
        Each tray has its floor in the -Y direction and open face at Y=0.
        Rotating 90° around X brings the floor to Z=0 and open face up —
        the correct print orientation (open cavity up, no supports needed).

    For Z-axis parting (legacy):
        Translates each half so its lowest Z sits at Z=0.

    Spaces parts along X with a 10 mm gap between bounding boxes.

    Returns a new list of Workplanes; does not modify the originals.
    """
    arranged: list[cq.Workplane] = []
    cursor_x = 0.0
    gap = 10.0

    for half in halves:
        if split_axis == "Y":
            # Rotate 90° around X-axis: Y→Z, Z→-Y
            # This brings the tray floor (was at -Y) down to -Z, then we lift to Z=0
            rotated = half.rotate((0, 0, 0), (1, 0, 0), -90)
            bb = rotated.val().BoundingBox()
            oriented = rotated.translate((0.0, 0.0, -bb.zmin))
        else:
            bb = half.val().BoundingBox()
            oriented = half.translate((0.0, 0.0, -bb.zmin))

        bb2 = oriented.val().BoundingBox()
        part_width = bb2.xmax - bb2.xmin
        x_offset = cursor_x - bb2.xmin
        placed = oriented.translate((x_offset, 0.0, 0.0))
        arranged.append(placed)

        cursor_x += part_width + gap

    return arranged


def export_mold(
    result: dict,
    output_dir: str,
    base_name: str,
    printer: PrinterConfig,
) -> None:
    """Export all mold halves and the assembled preview to the output directory.

    Writes:
        {output_dir}/{base_name}_half_0.stl   — bottom half, flat-lay oriented
        {output_dir}/{base_name}_half_1.stl   — top half, flat-lay oriented
        {output_dir}/{base_name}_assembled.step — full assembly for preview
        {output_dir}/{base_name}_assembled.stl  — full assembly (STL preview)

    Args:
        result:     Return value from build_blank_mold() or build_model_mold().
        output_dir: Directory to write files into (created if absent).
        base_name:  Filename prefix.
        printer:    Used to annotate the summary print.
    """
    halves: list[cq.Workplane] = result["halves"]
    assembled: cq.Workplane = result["assembled"]
    summary: dict = result["summary"]

    os.makedirs(output_dir, exist_ok=True)
    base = os.path.join(output_dir, base_name)

    # Flat-lay individual halves for printing
    split_axis = summary.get("split_axis", "Y")
    laid = flat_lay_arrange(halves, split_axis=split_axis)
    for i, half in enumerate(laid):
        path = f"{base}_half_{i}.stl"
        export_stl(half, path)
        print(f"  Exported: {path}")

    # Assembled preview
    export_step(assembled, f"{base}_assembled.step")
    print(f"  Exported: {base}_assembled.step")

    export_stl(assembled, f"{base}_assembled.stl")
    print(f"  Exported: {base}_assembled.stl")

    print(f"\nAll files written to: {os.path.abspath(output_dir)}/")


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _ensure_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
