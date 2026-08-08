#!/usr/bin/env python3
from pathlib import Path
import ast
import compileall
import csv
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ADDONS = ROOT / "addons"
errors = []
warnings = []

modules = [p for p in ADDONS.iterdir() if p.is_dir() and (p / "__manifest__.py").exists()]
names = {p.name for p in modules}

for mod in modules:
    manifest_path = mod / "__manifest__.py"
    try:
        manifest = ast.literal_eval(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{mod.name}: invalid manifest: {exc}")
        continue

    for key in ("name", "version", "license", "depends", "data", "installable"):
        if key not in manifest:
            errors.append(f"{mod.name}: missing manifest key {key}")

    for rel in manifest.get("data", []):
        if not (mod / rel).exists():
            errors.append(f"{mod.name}: manifest data file missing: {rel}")

    for bundle, assets in manifest.get("assets", {}).items():
        for asset in assets:
            prefix = mod.name + "/"
            if asset.startswith(prefix):
                rel = asset[len(prefix):]
                if not (mod / rel).exists():
                    errors.append(f"{mod.name}: asset missing: {asset}")

    for xml in mod.rglob("*.xml"):
        try:
            ET.parse(xml)
        except Exception as exc:
            errors.append(f"{xml.relative_to(ROOT)}: invalid XML: {exc}")

    for csv_path in mod.rglob("*.csv"):
        try:
            with csv_path.open(encoding="utf-8", newline="") as fh:
                rows = list(csv.reader(fh))
            if not rows or not rows[0]:
                errors.append(f"{csv_path.relative_to(ROOT)}: empty CSV")
        except Exception as exc:
            errors.append(f"{csv_path.relative_to(ROOT)}: invalid CSV: {exc}")

ok_compile = compileall.compile_dir(str(ADDONS), quiet=1)
if not ok_compile:
    errors.append("Python byte-compilation failed")

for required in [
    "ems_core","ems_ticketing","ems_badge","ems_access","ems_waitlist",
    "ems_seating","ems_notifications","ems_reporting","ems_gdpr",
    "ems_website","ems_api","ems_scanner_pwa","ems_payment_stripe","ems_ai","ems_suite"
]:
    if required not in names:
        errors.append(f"Missing required addon: {required}")


# Repository-level safety checks on shipped application/config files.
scan_roots = [ROOT / "addons", ROOT / "deploy"]
for scan_root in scan_roots:
    for path in scan_root.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() not in {".py",".xml",".js",".css",".md",".yml",".yaml",".template",".example",".csv",".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        stale_json_patterns = ("type=" + chr(34) + "json" + chr(34), "type=" + chr(39) + "json" + chr(39))
        if any(pattern in text for pattern in stale_json_patterns):
            errors.append(f"{path.relative_to(ROOT)}: stale Odoo <=18 controller request type; use jsonrpc in Odoo 19")
        private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
        if "sk_" + "live_" in text or private_key_marker in text:
            errors.append(f"{path.relative_to(ROOT)}: possible committed production secret")

print(f"Validated {len(modules)} addons")
if warnings:
    print("WARNINGS:")
    for item in warnings:
        print(" -", item)
if errors:
    print("ERRORS:")
    for item in errors:
        print(" -", item)
    sys.exit(1)
print("STATIC VALIDATION: PASS")
