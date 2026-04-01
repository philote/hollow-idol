"""
Step 1 geometry — single mold half tray.

Spec:
- Outer box: 100 × 80 × 40 mm
- 5 mm walls, open top
- 3 mm chamfer on all interior edges (vertical corners + floor-wall junctions)
- 4× 6 mm-radius hemisphere bumps on interior floor, centred 15 mm from each corner
- 1× 10 × 5 × 5 mm rectangular notch on one long interior wall at floor level
"""

from build123d import *
import os

# ── Parameters ────────────────────────────────────────────────────────────────
OUTER_X, OUTER_Y, OUTER_Z = 100, 80, 40
WALL = 5
CHAMFER_L = 3
HEMI_R = 6
HEMI_OFFSET = 15        # distance from interior corner to hemisphere centre
NOTCH_L, NOTCH_W, NOTCH_H = 10, 5, 5

# ── Derived values ─────────────────────────────────────────────────────────────
inner_x = OUTER_X - 2 * WALL   # 90
inner_y = OUTER_Y - 2 * WALL   # 70
inner_z = OUTER_Z - WALL       # 35  (no ceiling — open top)
inner_cx = inner_x / 2         # 45  (half inner width in X)
inner_cy = inner_y / 2         # 35  (half inner depth in Y)
inner_floor_z = WALL           # 5   (Z level of interior floor)
mid_z = inner_floor_z + inner_z / 2   # 22.5 — midpoint of inner vertical edges

# ── Build ──────────────────────────────────────────────────────────────────────
with BuildPart() as mold:

    # 1. Outer box sitting on the XY plane
    Box(OUTER_X, OUTER_Y, OUTER_Z,
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # 2. Subtract interior volume → 5 mm floor + walls, open top
    with Locations((0, 0, inner_floor_z)):
        Box(inner_x, inner_y, inner_z,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT)

    # 3. Chamfer interior edges 3 mm
    #
    #    Vertical interior corner edges:
    #      run from z=inner_floor_z to z=OUTER_Z
    #      centre ≈ (±inner_cx, ±inner_cy, mid_z)
    #
    #    Interior floor-wall edges:
    #      at z=inner_floor_z, along the inner wall planes

    vert_interior = [
        e for e in mold.edges()
        if (abs(abs(e.center().X) - inner_cx) < 0.5 and
            abs(abs(e.center().Y) - inner_cy) < 0.5 and
            abs(e.center().Z - mid_z) < 0.5)
    ]

    floor_wall = [
        e for e in mold.edges()
        if (abs(e.center().Z - inner_floor_z) < 0.5 and
            (abs(abs(e.center().X) - inner_cx) < 0.5 or
             abs(abs(e.center().Y) - inner_cy) < 0.5))
    ]

    interior_edges = vert_interior + floor_wall
    assert len(interior_edges) == 8, (
        f"Expected 8 interior edges for chamfer, found {len(interior_edges)}. "
        "Check inner_cx/inner_cy/mid_z tolerances."
    )
    chamfer(interior_edges, length=CHAMFER_L)

    # 4. Hemisphere bumps on interior floor (convex registration keys)
    #    Flat face flush with floor, dome protruding up into cavity.
    hemi_x = inner_cx - HEMI_OFFSET   # 30
    hemi_y = inner_cy - HEMI_OFFSET   # 20

    with Locations(
        (hemi_x,  hemi_y,  inner_floor_z),
        (hemi_x,  -hemi_y, inner_floor_z),
        (-hemi_x, hemi_y,  inner_floor_z),
        (-hemi_x, -hemi_y, inner_floor_z),
    ):
        # arc_size1=0 → upper hemisphere only (equator to north pole)
        Sphere(HEMI_R, arc_size1=0, arc_size2=90)

    # 5. Rectangular notch on one long side (−Y interior wall) for half ID.
    #    Laid against both the interior floor and that wall:
    #      10 mm long (X), 5 mm wide into cavity (+Y), 5 mm tall (+Z).
    notch_cy = -(inner_cy - NOTCH_W / 2)    # −32.5  (centred in the 5 mm notch width)
    notch_cz = inner_floor_z + NOTCH_H / 2  #   7.5  (sits on floor)

    with Locations((0, notch_cy, notch_cz)):
        Box(NOTCH_L, NOTCH_W, NOTCH_H, mode=Mode.SUBTRACT)


# ── Export ─────────────────────────────────────────────────────────────────────
os.makedirs("output", exist_ok=True)
out_path = "output/mold_half.stl"
export_stl(mold.part, out_path)
print(f"Exported: {out_path}")
