.PHONY: install test example

install:
	pip install -e ".[dev]"

test:
	pytest

example:
	python -c "\
from hollow_idol.config import MoldConfig, PrinterConfig; \
from hollow_idol.mold_case import build_blank_mold; \
from hollow_idol.export import export_mold; \
cfg = MoldConfig(); \
printer = PrinterConfig(); \
result = build_blank_mold(cfg, printer); \
export_mold(result, output_dir='output', base_name='example_mold', printer=printer) \
"
