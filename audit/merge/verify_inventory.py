"""
Step 3 check "nothing lost": mark every item of audit/merge/INVENTORY.md Present (with its location on chipmunk) or not.

    .venv/bin/python audit/merge/verify_inventory.py <out.csv>      # run from the root of the chipmunk checkout

Items and how each is checked (branches read with git show, so the checkout only needs the refs main, tomato, HEAD):
  - files (section 1): the path exists on HEAD; its blob equals main's / tomato's (or the difference is listed);
  - UI rows MAIN-UI-* / TOM-UI-* (sections 2-3): the file:line references are mapped from main's / tomato's file onto
    HEAD's with difflib; Present when every referenced line is unchanged on HEAD (or, for a range, its first line and
    every line but those the merge changed), giving HEAD's line;
  - functions, classes and constants; parameters; input files; input columns; tests; checks (section 4): looked up on
    HEAD (top-level def / class / assignment in the named file; row of model_params.csv; file; column of
    model_data/country_inputs.csv; test function in the named file; check name in audit/checks.py).
Writes one row per item: section, item, side (main / tomato / both), status, location, note.
"""
from __future__ import annotations

import ast
import csv
import difflib
import io
import re
import subprocess
import sys
from pathlib import Path

INV = Path("audit/merge/INVENTORY.md").read_text().splitlines()
ABBR = {"ms": "model_section.py", "pu": "paths_ui.py", "th": "theme.py", "D": "views/1_Dashboard.py",
        "AC": "views/2_All_Countries.py", "V": "views/3_Validation.py", "M": "views/4_Methods.py", "scn": "scenarios.py",
        "hm": "health_model.py", "app": "app.py"}


def show(ref: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


def blob(ref: str, path: str) -> str | None:
    r = subprocess.run(["git", "rev-parse", f"{ref}:{path}"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


HEAD_FILES = set(subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD"], capture_output=True,
                                text=True).stdout.splitlines())
_maps: dict = {}


def line_map(ref: str, path: str):
    """{line in ref's file: line in HEAD's file} for unchanged lines (1-based)."""
    key = (ref, path)
    if key not in _maps:
        a, b = show(ref, path), show("HEAD", path)
        if a is None or b is None:
            _maps[key] = None
        else:
            m = {}
            sm = difflib.SequenceMatcher(None, a.splitlines(), b.splitlines(), autojunk=False)
            for i, j, n in sm.get_matching_blocks():
                for k in range(n):
                    m[i + k + 1] = j + k + 1
            _maps[key] = m
    return _maps[key]


def parse_refs(cell: str, default_file: str | None):
    """'ms:1426-1490, 1499' -> [(file, lo, hi), ...]."""
    out, cur = [], default_file
    for part in re.split(r"[;,]\s*", cell):
        m = re.search(r"(?:([A-Za-z_][\w./ ]*?\.py|[A-Za-z]+):)?(\d+)(?:\s*[-–]\s*(\d+))?", part)
        if not m:
            continue
        f = m.group(1)
        if f:
            cur = ABBR.get(f, f)
        if cur is None:
            continue
        lo = int(m.group(2))
        out.append((cur, lo, int(m.group(3)) if m.group(3) else lo))
    return out


def ui_status(ref: str, refs):
    if not refs:
        return None, ""
    locs, changed, missing = [], 0, []
    for f, lo, hi in refs:
        mp = line_map(ref, f)
        if mp is None:
            missing.append(f"{f} not on HEAD")
            continue
        hit = [mp.get(k) for k in range(lo, hi + 1)]
        if hit[0] is None and not any(hit):
            missing.append(f"{f}:{lo}{'-' + str(hi) if hi != lo else ''} changed")
            continue
        changed += sum(h is None for h in hit)
        first = next(h for h in hit if h)
        last = max(h for h in hit if h)
        locs.append(f"{f}:{first}" + (f"-{last}" if last != first else ""))
    if missing:
        return False, "; ".join(locs + missing)
    return True, "; ".join(locs) + (f" ({changed} line(s) in the range changed by the merge)" if changed else "")


def top_names(src: str) -> set:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    names = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                for x in ast.walk(t):
                    if isinstance(x, ast.Name):
                        names.add(x.id)
    return names


def all_defs(src: str) -> set:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


rows = []


def add(section, item, side, ok, loc, note=""):
    rows.append({"section": section, "item": item, "side": side,
                 "status": {True: "Present", False: "NOT PRESENT", None: "Present (see note)"}[ok] if not isinstance(
                     ok, str) else ok, "location": loc, "note": note})


# ---------------- section 1: files ----------------
cat = None
for i, ln in enumerate(INV):
    if ln.startswith("## 2."):
        break
    m = re.match(r"### (.+?) \(\d+\)", ln)
    if m:
        cat = m.group(1)
        continue
    if cat is None:
        continue
    for p in (re.findall(r"`([^`]+)`", ln) if (ln.startswith("- ") or cat == "identical") else []):
        side = "main" if cat in ("main only", "different: changed on main only") else \
            "tomato" if cat in ("tomato only", "different: changed on tomato only") else "both"
        here = p in HEAD_FILES
        bh, bm, bt = blob("HEAD", p), blob("main", p), blob("tomato", p)
        note = ""
        if here:
            same = [n for n, b in (("main", bm), ("tomato", bt)) if b and b == bh]
            note = "same as " + " and ".join(same) if same else "merged / changed on chipmunk"
            if bt and bt != bh and side in ("tomato", "both"):
                where = [q for q in HEAD_FILES if blob("HEAD", q) == bt] if False else []
                note += "; tomato's version differs (decision R1-R11 / C1-C8, see PLAN.md)" if not same or \
                    "tomato" not in same else ""
        add("1 files: " + cat, p, side, here, p if here else "", note)

# ---------------- sections 2-3: UI rows ----------------
for ln in INV:
    m = re.match(r"\| (MAIN-UI-\d+|TOM-UI-\d+) \|", ln)
    if not m:
        continue
    cells = [c.strip() for c in ln.strip().strip("|").split("|")]
    uid, page, kind, name, fn, fl, shown = (cells + [""] * 7)[:7]
    ref = "main" if uid.startswith("MAIN") else "tomato"
    default = {"Dashboard": "views/1_Dashboard.py", "All Countries": "views/2_All_Countries.py",
               "Methods": "views/4_Methods.py", "Validation": "views/3_Validation.py",
               "Validation & Benchmarks": "views/3_Validation.py"}.get(page)
    refs = parse_refs(fl, default)
    ok, loc = ui_status(ref, refs)
    add("2-3 UI", f"{uid} {kind}: {name[:110]}", ref, ok, loc, f"{ref} shown: {shown[:80]}")

# ---------------- section 4 ----------------
sec = None
heads = show("HEAD", "model_params.csv")
params = {r["param"] for r in csv.DictReader(io.StringIO(heads))}
cols = set(next(csv.reader(io.StringIO(show("HEAD", "model_data/country_inputs.csv")))))
checks_src = show("HEAD", "audit/checks.py")
_src_cache: dict = {}
for ln in INV[[i for i, x in enumerate(INV) if x.startswith("## 4.")][0]:]:
    if ln.startswith("### "):
        sec = ln[4:]
        continue
    m = re.match(r"\| `([^`]+)` \| (yes|\*\*no\*\*) \| (yes|\*\*no\*\*) \|", ln)
    if not m or sec is None:
        continue
    item, on_m, on_t = m.group(1), m.group(2) == "yes", m.group(3) == "yes"
    side = "both" if on_m and on_t else "main" if on_m else "tomato"
    if sec.startswith("Model and UI functions"):
        f, rest = item.split("::", 1)
        nm = rest.split(" ")[0]
        if f not in _src_cache:
            s = show("HEAD", f)
            _src_cache[f] = (top_names(s), all_defs(s)) if s else (set(), set())
        top, alld = _src_cache[f]
        key = nm.split(".")[-1]
        ok = key in top or key in alld
        add("4 functions", item, side, ok, f if ok else "")
    elif sec.startswith("Parameters"):
        add("4 parameters", item, side, item in params, "model_params.csv" if item in params else "")
    elif sec.startswith("Model input files"):
        add("4 input files", item, side, item in HEAD_FILES, item if item in HEAD_FILES else "")
    elif sec.startswith("Input columns"):
        add("4 input columns", item, side, item in cols, "model_data/country_inputs.csv" if item in cols else "")
    elif sec.startswith("Tests"):
        f, t = item.split("::")
        s = show("HEAD", f) or ""
        ok = re.search(rf"^def {re.escape(t)}\(", s, re.M) is not None
        add("4 tests", item, side, ok, f if ok else "")
    elif sec.startswith("Checks"):
        ok = f'"{item}' in checks_src or f"'{item}" in checks_src
        add("4 checks", item, side, ok, "audit/checks.py" if ok else "")

# ---------------- tomato items not on chipmunk's live code: the decision that keeps them off, and where tomato's own
# version still is on chipmunk (main's " 2" copies are byte-identical to tomato's files; see PLAN.md and VERIFICATION.md)
D2, D3, D4, D5, D6, D7 = ("Off by decision 2 (D2: lede, The Numbers and outcome deaths pills)",
                          "Off by decision 2 (D3: US$1M cards' deaths line)",
                          "Off by decision 2 (D4: How the Damage Scales charts)",
                          "Off by decision 2 (D5: Scenario A vs B / replacement deaths)",
                          "Off by decision 2 (D6: All Countries deaths)",
                          "Off by decision 2 (D7: Validation in navigation, Methods Cross-Checks tab)")
MAINV = "main's version kept (conflicts default to main): "
REASON = {
    "TOM-UI-005": MAINV + "main's header (MAIN-UI-007/008)", "TOM-UI-006": MAINV + "main does not show it (MAIN-UI-300)",
    "TOM-UI-007": MAINV + "main's header facts", "TOM-UI-008": MAINV + "main's header facts",
    "TOM-UI-009": MAINV + "main's header facts", "TOM-UI-010": MAINV + "MAIN-UI-011",
    "TOM-UI-011": MAINV + "MAIN-UI-012", "TOM-UI-013": D2, "TOM-UI-014": MAINV + "MAIN-UI-022",
    "TOM-UI-015": D2, "TOM-UI-016": D2, "TOM-UI-020": D2, "TOM-UI-026": MAINV + "MAIN-UI-304 (not shown on main)",
    "TOM-UI-032": MAINV + "MAIN-UI-058", "TOM-UI-033": MAINV + "MAIN-UI-058/063", "TOM-UI-034": MAINV + "MAIN-UI-025",
    "TOM-UI-042": MAINV + "MAIN-UI-045", "TOM-UI-045": MAINV + "MAIN-UI-041 (default off on main)",
    "TOM-UI-046": D2 + "; main fixes the death-rate trend on (scn.DEFAULT_MORTALITY_TREND)",
    "TOM-UI-058": MAINV + "MAIN-UI-063", "TOM-UI-066": D5, "TOM-UI-067": D5, "TOM-UI-068": D5 + "; main: MAIN-UI-072",
    "TOM-UI-071": D5, "TOM-UI-072": MAINV + "MAIN-UI-090", "TOM-UI-095": MAINV + "MAIN-UI-076",
    "TOM-UI-096": MAINV + "MAIN-UI-077", "TOM-UI-097": MAINV + "MAIN-UI-078", "TOM-UI-098": MAINV + "MAIN-UI-081",
    "TOM-UI-099": MAINV + "MAIN-UI-082", "TOM-UI-100": MAINV + "MAIN-UI-083", "TOM-UI-101": MAINV + "MAIN-UI-084",
    "TOM-UI-102": MAINV + "MAIN-UI-085", "TOM-UI-103": MAINV + "MAIN-UI-086", "TOM-UI-104": MAINV + "MAIN-UI-088",
    "TOM-UI-106": MAINV + "MAIN-UI-117", "TOM-UI-109": D2, "TOM-UI-110": MAINV + "MAIN-UI-118", "TOM-UI-113": D2,
    "TOM-UI-114": D2, "TOM-UI-115": D2, "TOM-UI-118": D5 + "; main: MAIN-UI-122",
    "TOM-UI-120": D5 + "; main: MAIN-UI-124", "TOM-UI-121": D2 + " (Download Country Brief; main: MAIN-UI-293)",
    "TOM-UI-122": D3, "TOM-UI-123": D3 + "; main: MAIN-UI-292", "TOM-UI-128": MAINV + "main has no source line there",
    "TOM-UI-129": "Present", "TOM-UI-131": "Present",
    "TOM-UI-132": MAINV + "small multiples (MAIN-UI-288 not shown on main)", "TOM-UI-133": D4, "TOM-UI-134": D4,
    "TOM-UI-135": D4, "TOM-UI-136": D4, "TOM-UI-137": D4, "TOM-UI-138": D4, "TOM-UI-139": D4,
    "TOM-UI-145": MAINV + "MAIN-UI-139 chart", "TOM-UI-146": MAINV + "MAIN-UI-139 chart",
    "TOM-UI-147": MAINV + "MAIN-UI-139 chart", "TOM-UI-148": MAINV + "MAIN-UI-299 (not shown on main)",
    "TOM-UI-152": MAINV + "UI_PRESETS (MAIN-UI-305/306)", "TOM-UI-158": D6, "TOM-UI-159": D6, "TOM-UI-160": D6,
    "TOM-UI-161": D6, "TOM-UI-218": MAINV + "MAIN-UI-164 wording",
    "TOM-UI-247": MAINV + "Methods Step 3 wording; 'Malaria input flags' is R11 (item 14)",
    "TOM-UI-257": MAINV + "Funding Paths wording; 'Which services are tracked how' is deaths-by-path text (D)",
    "TOM-UI-259": "Off by decision 2 (deaths-by-path table in tomato's Funding Paths, not Step 4)",
    "TOM-UI-260": "Off by decision 2 (Further deaths 2031-2035 display)", "TOM-UI-269": "Not adopted: R10 (L-32 label)",
    "TOM-UI-270": "Not adopted: R10 (L-32 label)", "TOM-UI-276": D7, "TOM-UI-277": D7, "TOM-UI-278": D7,
    "TOM-UI-279": D7, "TOM-UI-284": D7,
    "fiscal_inputs.py::weo_nominal_growth": "Not adopted: R11 (item 10)",
    "health_model.py::budget_growth_factors": "Not adopted: R11 (item 10)",
    "scenarios.py::MOU_PRICE_BASE_YEAR (constant)": "Not adopted: R11 (L-35)",
    "scenarios.py::mou_deflate_settings": "Not adopted: R11 (L-35)", "budget_growth": "Not adopted: R11 (item 10)",
    "mou_deflate": "Not adopted: R11 (L-35)", "mou_us_inflation": "Not adopted: R11 (L-35)",
    "gdp_growth_weo_2026_30": "Not adopted: R11 (item 10)", "gdp_growth_weo_2026_30_source": "Not adopted: R11 (item 10)",
    "flag_interest_alt_def": "Not adopted: R8 (L-34)", "hiv_deaths_unaids": "Not adopted: R9 (L-11)",
    "hiv_deaths_unaids_source": "Not adopted: R9 (L-11)", "hiv_deaths_unaids_year": "Not adopted: R9 (L-11)",
    "sh_hiv_incd_tl_source": "Not adopted: R6 (IMP-24)", "sh_imm_idpt_source": "Not adopted: R5 (L-17)",
    "sh_imm_meas_source": "Not adopted: R5 (L-17)",
    "tests/test_fiscal.py::test_imf_net_interest_is_primary_and_the_world_bank_fallback_is_flagged":
        "Not adopted: R8 (L-34); tomato's test file is kept byte-identical as 'tests/test_fiscal 2.py' (not collected, "
        "decision 4)",
}
for k in [f"births_{y}" for y in range(2026, 2031)] + ["births_proj_source"]:
    REASON[k] = "Not adopted: R7 (L-24)"
for k in [f"donor_share_mal_{x}{s}" for x in ("itn", "irs", "cm") for s in ("", "_source")]:
    REASON[k] = "Not adopted: R3 (A3)"
for k in ("flag_irs_household", "flag_irs_implied", "flag_itn_default", "flag_map_who_gap"):
    REASON[k] = "Not adopted: R11 (item 14)"
PRESENT_NOW = {"TOM-UI-129": "model_section.py:1098 (What Each Service Loses, help notes adapted to main's page)",
               "TOM-UI-131": "model_section.py:1101-1110 (caption reworded: four diseases only, Other Aid)"}
COPY = {"views/1_Dashboard.py": "views/1_Dashboard 2.py", "model_section.py": "model_section 2.py",
        "paths_ui.py": "paths_ui 2.py", "views/2_All_Countries.py": "views/2_All_Countries 2.py",
        "views/4_Methods.py": "views/4_Methods 2.py", "fiscal_inputs.py": "fiscal_inputs 2.py",
        "health_model.py": "health_model 2.py", "scenarios.py": "scenarios 2.py", "tests/test_fiscal.py":
        "tests/test_fiscal 2.py", "model_params.csv": "model_params 2.csv"}
for r in rows:
    if r["status"] != "NOT PRESENT":
        continue
    key = r["item"].split(" ")[0] if r["item"].startswith("TOM-UI") else r["item"]
    reason = REASON.get(key)
    if reason is None:
        continue                                              # stays NOT PRESENT: nothing explains it
    if reason == "Present":
        r["status"], r["location"] = "Present", PRESENT_NOW[key]
        continue
    copy = ""
    f = r["location"].split(":")[0] if r["item"].startswith("TOM-UI") else (
        r["item"].split("::")[0] if "::" in r["item"] else "model_params.csv" if r["section"] == "4 parameters" else "")
    if f in COPY and blob("tomato", f) == blob("HEAD", COPY[f]):
        copy = f"; tomato's code kept byte-identical in '{COPY[f]}' (not run)"
    elif r["section"] == "4 input columns":
        copy = "; on tomato (backup-tomato-2026-10-29) only"
    r["status"] = "Not on chipmunk's live page/model by decision"
    r["note"] = reason + copy + ("; " + r["note"] if r["note"] else "")

out = sys.argv[1] if len(sys.argv) > 1 else "audit/merge/verification_items.csv"
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
from collections import Counter
c = Counter((r["section"].split(":")[0], r["status"]) for r in rows)
for k in sorted(c):
    print(k, c[k])
print(f"{len(rows)} items -> {out}")
