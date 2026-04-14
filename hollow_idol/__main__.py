import argparse
import sys

from hollow_idol.config import MoldConfig
from hollow_idol.mold_case import generate
from hollow_idol.export import export_all
from hollow_idol import printers


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m hollow_idol",
        description="Generate 3-piece plaster mold cases for ceramic slip casting.",
    )

    # Tray dimensions
    parser.add_argument("--outer-x",     type=float, default=100.0, metavar="MM", help="Outer width  (default 100)")
    parser.add_argument("--outer-y",     type=float, default=80.0,  metavar="MM", help="Outer depth  (default 80)")
    parser.add_argument("--outer-z",     type=float, default=40.0,  metavar="MM", help="Outer height (default 40)")
    parser.add_argument("--wall",        type=float, default=5.0,   metavar="MM", help="Wall + floor thickness (default 5)")
    parser.add_argument("--chamfer",     type=float, default=3.0,   metavar="MM", help="Interior edge chamfer (default 3)")

    # Registration keys
    parser.add_argument("--hemi-r",      type=float, default=6.0,   metavar="MM", help="Key sphere radius (default 6)")
    parser.add_argument("--hemi-height", type=float, default=3.0,   metavar="MM", help="Dome/divot height (default 3)")
    parser.add_argument("--hemi-offset", type=float, default=15.0,  metavar="MM", help="Key centre distance from interior corner (default 15)")

    # Sliding panel fit
    parser.add_argument("--tongue-clearance",  type=float, default=0.25, metavar="MM", help="Panel fit clearance (default 0.25)")

    # Flanges
    parser.add_argument("--flange-width",     type=float, default=10.0, metavar="MM", help="Binder clip flange width (default 10)")
    parser.add_argument("--flange-thickness", type=float, default=3.0,  metavar="MM", help="Flange thickness (default 3)")

    # Printer + output
    parser.add_argument(
        "--printer",
        choices=list(printers.BY_NAME.keys()),
        default="generic-200",
        help="Printer preset for bed-size warnings (default: generic-200)",
    )
    parser.add_argument("--out-dir", default="output", metavar="DIR", help="Output directory (default: output/)")
    parser.add_argument("--step", action="store_true", help="Also export STEP files")

    args = parser.parse_args()

    cfg = MoldConfig(
        outer_x=args.outer_x,
        outer_y=args.outer_y,
        outer_z=args.outer_z,
        wall=args.wall,
        chamfer=args.chamfer,
        hemi_r=args.hemi_r,
        hemi_height=args.hemi_height,
        hemi_offset=args.hemi_offset,
        tongue_clearance=args.tongue_clearance,
        flange_width=args.flange_width,
        flange_thickness=args.flange_thickness,
    )

    printer = printers.BY_NAME[args.printer]

    import warnings
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        wla, wra, ba, wlb, wrb, bb = generate(cfg, printer)

    for w in caught:
        print(f"WARNING: {w.message}", file=sys.stderr)

    export_all(wla, wra, ba, wlb, wrb, bb, out_dir=args.out_dir, step=args.step)


if __name__ == "__main__":
    main()
