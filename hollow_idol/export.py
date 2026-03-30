"""STL / STEP export and flat-lay print arrangement.

Flat-lay arranges all mold halves so each part sits with its largest flat face
on the build plate (Z=0), then spaces them apart along X for easy slicing.
"""
from __future__ import annotations

import os
from pathlib import Path

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


def flat_lay_arrange(halves: list[cq.Workplane]) -> list[cq.Workplane]:
    """Orient each mold half flat on the build plate and space along X.

    - Translates each half so its lowest Z sits at Z=0 (print bed level).
    - For the bottom mold half (which extends into negative Z) this naturally
      flips the orientation so the parting face prints face-down — which is the
      desired orientation (flat face down, open cavity up).
    - Spaces parts along X with a 10 mm gap between bounding boxes.

    Returns a new list of Workplanes; does not modify the originals.
    """
    arranged: list[cq.Workplane] = []
    cursor_x = 0.0
    gap = 10.0

    for half in halves:
        bb = half.val().BoundingBox()
        # Lift so the lowest Z is at Z=0
        lifted = half.translate((0.0, 0.0, -bb.zmin))

        # Centre each part's bounding box along X starting from cursor_x
        bb2 = lifted.val().BoundingBox()
        part_width = bb2.xmax - bb2.xmin
        x_offset = cursor_x - bb2.xmin  # shift so xmin → cursor_x
        placed = lifted.translate((x_offset, 0.0, 0.0))
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
    laid = flat_lay_arrange(halves)
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
