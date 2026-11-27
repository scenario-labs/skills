#!/usr/bin/env python3
"""package_lint: offline check of a 3ds Max plug-in package (PackageContents.xml).

Runner side: plain Python 3.10+, any OS, never imports pymxs.
Rules come from scripting-pipeline__packagecontents-format-2026.md and
scripting-pipeline__packaging-plugins-2025.md. Passing this lint does not prove
3ds Max loads the package: start 3ds Max with ADSK_APPLICATION_PLUGINS pointing at
the package folder and read max.log and the Plug-in Package Manager messages.

Usage:
    python package_lint.py <package_folder_or_PackageContents.xml> [--release 2027] [--json]
Exit code: 0 no errors, 1 errors found, 2 file not found or not XML.
"""
import argparse
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

GUID = re.compile(r"^\{?[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}?$")
APPVER = re.compile(r"^\d+(\.\d+){0,2}$")
SERIES = re.compile(r"^\d{4}(\.\d+){0,3}$|^\d+$")
DESCRIPTIONS = {
    "plugins parts", "assemblies parts", "ui schemes parts", "default setting paths parts",
    "pre-start-up scripts parts", "macroscripts parts", "post-start-up scripts parts",
    "light icon paths parts", "dark icon paths parts", "scene converter folders parts",
    "osl folders parts", "amg folders parts", "hotkey parts",
}
FOLDER_PARTS = {"default setting paths parts", "light icon paths parts", "dark icon paths parts",
                "scene converter folders parts", "osl folders parts", "amg folders parts"}


def _series_tuple(v):
    try:
        return tuple(int(p) for p in v.split("."))
    except ValueError:
        return None


def lint(path, release=None):
    findings = []

    def add(sev, rule, msg):
        findings.append({"severity": sev, "rule": rule, "message": msg})

    xml_path = os.path.join(path, "PackageContents.xml") if os.path.isdir(path) else path
    root_dir = os.path.dirname(os.path.abspath(xml_path))
    if not os.path.isfile(xml_path):
        return None, [{"severity": "error", "rule": "file", "message": "not found: %s" % xml_path}]
    if os.path.basename(xml_path) != "PackageContents.xml":
        add("error", "file-name", "3ds Max scans for a file named PackageContents.xml")
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as exc:
        return None, [{"severity": "error", "rule": "xml", "message": str(exc)}]
    app = tree.getroot()
    if app.tag != "ApplicationPackage":
        add("error", "root", "root element must be <ApplicationPackage>, found <%s>" % app.tag)
    a = app.attrib
    if a.get("AutodeskProduct") != "3ds Max":
        add("error", "AutodeskProduct", 'AutodeskProduct must be "3ds Max" (got %r)' % a.get("AutodeskProduct"))
    if a.get("ProductType") != "Application":
        add("error", "ProductType", 'ProductType must be "Application"')
    if "AppName" in a:
        add("warning", "AppName", "AppName is not a documented 3ds Max attribute; use Name")
    if not a.get("Name"):
        add("warning", "Name", "Name attribute missing")
    if not APPVER.match(a.get("AppVersion", "")):
        add("error", "AppVersion", "AppVersion must look like MMM.mmm.bbb (got %r)" % a.get("AppVersion"))
    if not GUID.match(a.get("UpgradeCode", "")):
        add("error", "UpgradeCode", "UpgradeCode is required by 3ds Max and must be a GUID")
    if "ProductCode" not in a:
        add("info", "ProductCode", "ProductCode not required by 3ds Max; change it with every AppVersion if used")
    elif not GUID.match(a["ProductCode"]):
        add("warning", "ProductCode", "ProductCode is not a GUID")
    if app.find("CompanyDetails") is None:
        add("error", "CompanyDetails", "<CompanyDetails /> is mandatory: the package will not load without it")

    comps = app.findall("Components")
    if not comps:
        add("warning", "Components", "no <Components> node: nothing will load")
    for i, comp in enumerate(comps, 1):
        desc = comp.attrib.get("Description", "")
        where = "Components #%d (%s)" % (i, desc or "no Description")
        if desc not in DESCRIPTIONS:
            add("error", "Description", "%s: unknown Description %r" % (where, desc))
        rr = comp.find("RuntimeRequirements")
        if rr is None:
            add("error", "RuntimeRequirements", "%s: RuntimeRequirements is required in every Components node" % where)
        else:
            r = rr.attrib
            if r.get("OS") != "Win64":
                add("error", "OS", '%s: OS must be "Win64"' % where)
            if r.get("Platform") != "3ds Max":
                add("error", "Platform", '%s: Platform must be "3ds Max"' % where)
            smax, smin = r.get("SeriesMax"), r.get("SeriesMin", "0")
            if not smax:
                add("error", "SeriesMax", "%s: SeriesMax is mandatory" % where)
            elif not SERIES.match(smax) or not SERIES.match(smin):
                add("error", "Series", "%s: SeriesMin/SeriesMax must be YYYY or YYYY.u.h.bbbb" % where)
            else:
                lo, hi = _series_tuple(smin), _series_tuple(smax)
                # a shorter SeriesMax covers every later part: "2027" includes 2027.3
                if lo and hi and lo[:len(hi)] > hi:
                    add("error", "Series", "%s: SeriesMin > SeriesMax" % where)
                if release and hi and not (lo[:1] <= (int(release),) <= hi[:1]):
                    add("error", "Series", "%s: release %s outside SeriesMin %s .. SeriesMax %s "
                        "(3ds Max does not test binary compatibility)" % (where, release, smin, smax))
        entries = comp.findall("ComponentEntry")
        if not entries:
            add("warning", "ComponentEntry", "%s: no ComponentEntry" % where)
        for e in entries:
            mod = e.attrib.get("ModuleName", "")
            if not mod:
                add("error", "ModuleName", "%s: ComponentEntry without ModuleName" % where)
                continue
            # Windows separators read the same on any OS
            full = os.path.normpath(os.path.join(root_dir, mod.replace("\\", "/")))
            if desc in FOLDER_PARTS:
                if not os.path.isdir(full):
                    add("error", "ModuleName", "%s: folder not found %s" % (where, mod))
                if desc == "osl folders parts" and os.path.basename(full.rstrip("\\/")) != "OSL":
                    add("error", "OSL", "%s: the last folder must be named OSL" % where)
            elif not os.path.isfile(full) and any(c in os.path.basename(full) for c in "*?["):
                # file name wildcard: not in the saved 2026 page [verify]; at least one file must match
                if not [f for f in glob.glob(full) if os.path.isfile(f)]:
                    add("error", "ModuleName", "%s: no file matches %s" % (where, mod))
            elif not os.path.isfile(full):
                add("error", "ModuleName", "%s: file not found %s" % (where, mod))
            ext = os.path.splitext(mod)[1].lower()
            if desc == "pre-start-up scripts parts" and ext != ".ms":
                add("error", "pre-start-up", "%s: pre-start-up scripts are MAXScript only (%s)" % (where, mod))
            if desc == "post-start-up scripts parts" and ext not in (".ms", ".py", ".mse"):
                add("warning", "post-start-up", "%s: expected .ms or .py (%s)" % (where, mod))
            if desc == "hotkey parts" and ext != ".hsx":
                add("error", "hotkey", "%s: hotkey parts take an .hsx file" % where)
            for dep in e.iter("DependentBundle"):
                if not GUID.match(dep.attrib.get("UpgradeCode", "")):
                    add("error", "DependentBundle", "%s: DependentBundle UpgradeCode is not a GUID (ignored by 3ds Max)" % where)

    for ev in app.findall("EnvironmentVariables"):
        if ev.find("RuntimeRequirements") is None:
            add("error", "EnvironmentVariables", "EnvironmentVariables needs its own RuntimeRequirements (3ds Max 2023+)")
        for var in ev.findall("EnvironmentVariable"):
            v = var.attrib
            if not v.get("Name") or "Value" not in v:
                add("error", "EnvironmentVariable", "EnvironmentVariable needs Name, Value and Type")
            typ = v.get("Type", "")
            if typ.lower() not in ("string", "path"):
                add("error", "EnvironmentVariable", "%s: Type must be string or path" % v.get("Name"))
            elif typ not in ("string", "path"):
                add("info", "EnvironmentVariable", "%s: Type %r; the spec table spells it lowercase" % (v.get("Name"), typ))
            val = v.get("Value", "")
            if val.startswith("+") and typ.lower() == "path":
                add("warning", "EnvironmentVariable",
                    "%s: the spec escapes + when appending to a path (Value=\"\\+;.\\Contents\")" % v.get("Name"))

    for tag in ("DependentBundle", "LoadAfterBundle"):
        for el in app.iter(tag):
            if not GUID.match(el.attrib.get("UpgradeCode", "")):
                add("error", tag, "%s UpgradeCode is not a GUID (3ds Max ignores the element)" % tag)
    return xml_path, findings


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("path")
    p.add_argument("--release", help="3ds Max release year that must load the package, e.g. 2027")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    xml_path, findings = lint(args.path, args.release)
    errors = [f for f in findings if f["severity"] == "error"]
    if args.json:
        print(json.dumps({"file": xml_path, "errors": len(errors), "findings": findings}, indent=2))
    else:
        for f in findings:
            print("%-7s %-22s %s" % (f["severity"], f["rule"], f["message"]))
        print("%d error(s), %d finding(s)" % (len(errors), len(findings)))
    if xml_path is None:
        return 2
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
