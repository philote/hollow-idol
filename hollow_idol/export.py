import os
from build123d import Part, export_stl, export_step


def export_all(
    wall_left_a: Part,
    wall_right_a: Part,
    bottom_a: Part,
    wall_left_b: Part,
    wall_right_b: Part,
    bottom_b: Part,
    out_dir: str = "output",
    step: bool = False,
) -> None:
    """Export all 6 mold pieces to out_dir as STL (and optionally STEP)."""
    os.makedirs(out_dir, exist_ok=True)

    pieces = [
        (wall_left_a,  "half_a_wall_left"),
        (wall_right_a, "half_a_wall_right"),
        (bottom_a,     "half_a_bottom"),
        (wall_left_b,  "half_b_wall_left"),
        (wall_right_b, "half_b_wall_right"),
        (bottom_b,     "half_b_bottom"),
    ]

    for part, stem in pieces:
        stl_path = os.path.join(out_dir, f"{stem}.stl")
        export_stl(part, stl_path)
        print(f"Exported: {stl_path}")

        if step:
            step_path = os.path.join(out_dir, f"{stem}.step")
            export_step(part, step_path)
            print(f"Exported: {step_path}")
