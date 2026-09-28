#!/usr/bin/env python3
from pathlib import Path

# Paths
index_file = Path("index_top_labels.txt")
out_dir = Path("sas")
out_dir.mkdir(exist_ok=True)


def sas_escape(s: str) -> str:
    # SAS escapes a double-quote inside a quoted string by doubling it.
    return s.replace('"', '""')


# Read index_top_labels.txt
with index_file.open("r", encoding="utf-8") as f:
    lines = [line.strip().split(maxsplit=1) for line in f if line.strip()]
    # idx is the 6-digit label ID, keyword is the label string
    items = [(f"v{idx}", sas_escape(keyword)) for idx, keyword in lines]

# (1) Full format with label and ID
with (out_dir / "label_full_format.sas").open("w", encoding="utf-8") as f:
    f.write("PROC FORMAT library=work ;\n")
    f.write("  VALUE  $lexlabelsfull\n")
    for varname, label in items:
        f.write(f'"{varname}" = "{label} ({varname})"\n')
    f.write(";\nrun;\nquit;\n")

# (2) Short format with just label
with (out_dir / "label_format.sas").open("w", encoding="utf-8") as f:
    f.write("PROC FORMAT library=work ;\n")
    f.write("  VALUE  $lexlabels\n")
    for varname, label in items:
        f.write(f'"{varname}" = "{label}"\n')
    f.write(";\nrun;\nquit;\n")