import os
from build123d import Part, export_stl, export_step


def export_pair(
    half_a: Part,
    half_b: Part,
    out_dir: str = "output",
    stem_a: str = "mold_half_a",
    stem_b: str = "mold_half_b",
    step: bool = False,
) -> None:
    """Export both mold halves to out_dir as STL (and optionally STEP)."""
    os.makedirs(out_dir, exist_ok=True)

    for part, stem in [(half_a, stem_a), (half_b, stem_b)]:
        stl_path = os.path.join(out_dir, f"{stem}.stl")
        export_stl(part, stl_path)
        print(f"Exported: {stl_path}")

        if step:
            step_path = os.path.join(out_dir, f"{stem}.step")
            export_step(part, step_path)
            print(f"Exported: {step_path}")
