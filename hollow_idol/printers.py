from __future__ import annotations

from hollow_idol.config import PrinterConfig

# Common printer presets keyed by lowercase name.
# All dimensions in mm.
_PRESETS: dict[str, PrinterConfig] = {
    "bambu_x1c": PrinterConfig(
        printer_name="Bambu Lab X1C",
        bed_x=256, bed_y=256, bed_z=256,
    ),
    "bambu_p1s": PrinterConfig(
        printer_name="Bambu Lab P1S",
        bed_x=256, bed_y=256, bed_z=256,
    ),
    "bambu_a1": PrinterConfig(
        printer_name="Bambu Lab A1",
        bed_x=256, bed_y=256, bed_z=256,
    ),
    "prusa_mk4": PrinterConfig(
        printer_name="Prusa MK4",
        bed_x=250, bed_y=210, bed_z=220,
    ),
    "prusa_xl": PrinterConfig(
        printer_name="Prusa XL",
        bed_x=360, bed_y=360, bed_z=360,
    ),
    "creality_ender3": PrinterConfig(
        printer_name="Creality Ender 3",
        bed_x=220, bed_y=220, bed_z=250,
    ),
    "creality_k1": PrinterConfig(
        printer_name="Creality K1",
        bed_x=220, bed_y=220, bed_z=250,
    ),
    "voron_2_4": PrinterConfig(
        printer_name="Voron 2.4 (300mm)",
        bed_x=300, bed_y=300, bed_z=280,
    ),
    # Resin printers — large format
    "elegoo_saturn3": PrinterConfig(
        printer_name="Elegoo Saturn 3 Ultra",
        bed_x=218, bed_y=123, bed_z=260,
    ),
    "phrozen_mega8k": PrinterConfig(
        printer_name="Phrozen Mega 8K",
        bed_x=218, bed_y=123, bed_z=235,
    ),
    "generic": PrinterConfig(
        printer_name="generic",
        bed_x=200, bed_y=200, bed_z=200,
    ),
}


def get_printer(name: str, **overrides) -> PrinterConfig:
    """Return a PrinterConfig preset by name, with optional field overrides.

    Args:
        name: Case-insensitive printer key (e.g. "bambu_x1c", "prusa_mk4").
        **overrides: Any PrinterConfig field to override on the returned preset.

    Raises:
        KeyError: If name is not a known preset.

    Example:
        printer = get_printer("bambu_x1c", bed_z=250)
    """
    key = name.lower().replace(" ", "_").replace("-", "_")
    if key not in _PRESETS:
        available = ", ".join(sorted(_PRESETS))
        raise KeyError(
            f"Unknown printer preset {name!r}. Available: {available}"
        )
    preset = _PRESETS[key]
    if not overrides:
        return preset
    # Apply overrides via dataclass replace
    from dataclasses import replace
    return replace(preset, **overrides)


def list_printers() -> list[str]:
    """Return sorted list of available printer preset names."""
    return sorted(_PRESETS)
