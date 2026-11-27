"""td_plan: texel density and texture size planning (runner side, plain Python, no pymxs).

Formulas follow Huge Menace (sR1sAWWT2x8): texel density is texture pixels per cm of
surface, targets by camera distance, and a target can be derived from the pixels a
reference plane covers on screen. Padding rule from Abe Leal (2gv1jYDAoJc): 8 px at 2K.

Usage:
    python td_plan.py --area-cm2 60000 --td 5.12
    python td_plan.py --plane-cm 100 --pixels 248          # target from screen coverage
    python td_plan.py --pad-px 8 --size 2048                 # padding in UV units
"""

import argparse

TARGETS_PX_PER_CM = {
    "weapon_first_person": 20.48,
    "first_person": 10.24,
    "third_person": 5.12,
    "top_down": 2.56,
}


def td_from_screen(plane_cm, pixels):
    """Target px/cm from a plane of plane_cm width covering `pixels` at the closest distance."""
    return pixels / plane_cm


def size_for(area_cm2, td, utilization=0.75, max_size=8192):
    """Smallest power-of-two square that holds area_cm2 at td with the given UV utilization.

    Returns (size, expected_coverage_pct). Coverage above 100 means the shells do not fit.
    """
    needed_px2 = area_cm2 * td * td
    size = 1
    while size * size * utilization < needed_px2 and size < max_size:
        size *= 2
    coverage = 100.0 * needed_px2 / (size * size)
    return size, coverage


def padding_uv(pad_px, size):
    """Padding in 0-1 UV units for a pixel padding at a texture size."""
    return pad_px / float(size)


def padding_px_at_mip(pad_px, mip):
    """Pixels of padding left at a mip level (each level halves)."""
    return pad_px / float(2 ** mip)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--area-cm2", type=float, help="unfolded surface area in cm2")
    ap.add_argument("--td", type=float, help="target px/cm")
    ap.add_argument("--util", type=float, default=0.75, help="expected UV utilization (0-1)")
    ap.add_argument("--plane-cm", type=float)
    ap.add_argument("--pixels", type=float)
    ap.add_argument("--pad-px", type=float)
    ap.add_argument("--size", type=int, default=2048)
    a = ap.parse_args()
    if a.plane_cm and a.pixels:
        print("target td = %.3f px/cm" % td_from_screen(a.plane_cm, a.pixels))
    if a.area_cm2 and a.td:
        size, cov = size_for(a.area_cm2, a.td, a.util)
        print("texture %d px, expected coverage %.1f%% at %.2f px/cm" % (size, cov, a.td))
        if cov < 50:
            print("coverage under 50%: consider a non-square map, an atlas or soft TD")
    if a.pad_px:
        print("padding %.0f px at %d = %.5f UV" % (a.pad_px, a.size, padding_uv(a.pad_px, a.size)))
        for mip in range(1, 5):
            print("  mip %d: %.2f px" % (mip, padding_px_at_mip(a.pad_px, mip)))


if __name__ == "__main__":
    main()
