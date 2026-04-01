from hollow_idol.config import PrinterConfig

GENERIC_200 = PrinterConfig("Generic 200mm", bed_x=200, bed_y=200, bed_z=200)
PRUSA_MK4   = PrinterConfig("Prusa MK4",    bed_x=250, bed_y=210, bed_z=220)
BAMBU_P1S   = PrinterConfig("Bambu P1S",    bed_x=256, bed_y=256, bed_z=256)
BAMBU_X1C   = PrinterConfig("Bambu X1C",    bed_x=256, bed_y=256, bed_z=256)

DEFAULT = GENERIC_200
