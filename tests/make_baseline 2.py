"""Save sudden-cut results so tests can check that the current model, with the default path and the later mechanisms
switched off, reproduces them. baseline_sudden.json was made by running this file at commit 5eb6111 (before TB spread,
malaria rebound, vaccine cohorts and HIV infection deaths) with the current model_data/country_inputs.csv.
Run from the repo root:  python tests/make_baseline.py

America First MOUs is the exception (audit I-02/I-03): the preset was redefined to follow each country's MOU schedule
year by year, only for countries with a signed MOU and schedule data, so the old model cannot produce it. Its entries
(KEN, NGA, MOZ; HND and IRQ cannot run it) are written by the current model with the later mechanisms switched off,
as test (a) runs it:  python tests/make_baseline.py --mou-only
They lock the schedule-driven results against unintended changes; tests/test_mou.py checks the schedule itself.

New HIV infections (audit I-05): the dashboard now shows the central run, not the median of the draws, so every
entry's line infections_5y was replaced by the central run. For the 90 non-MOU entries the original model (commit
5eb6111, n_draws=0) and the current model (later mechanisms off) give identical central infections (max difference 0),
so only that statistic changed; all other fields are as before.

Global Fund & Gavi Shortfalls (audit I-07): the preset's cuts are now user-set (default Gavi 15%, Global Fund 20%). Its
entries keep the original 5eb6111 values, made with the old fixed cuts (Gavi 24%, Global Fund 28%), and the tests pass
those cuts explicitly (baseline_opts), so the lock against the original model still holds.

Malaria (audit I-06, I-11, I-27 malaria part): malaria coverage, cases and the death trend now come from the Malaria
Atlas Project, and malaria treatment costs US$14 a case, so entries with malaria results were refreshed with the current
model (later mechanisms off); outside the lives-first response only malaria lines, the totals and the malaria path were
allowed to change, and that is checked:  python tests/make_baseline.py --malaria

HIV (audit I-09, I-27 PMTCT part): HIV testing and care money left the ART line (kappa of it still counts toward ART),
PMTCT costs US$250 a woman including her ART, and PMTCT women are outside the ART line's people covered, so entries
with HIV results were refreshed (later mechanisms off); outside lives first only HIV lines, the totals and the HIV path
were allowed to change, and that is checked:  python tests/make_baseline.py --hiv

Malaria effect sizes (logic review L-04, L-20): the Lives Saved Tool effects now apply in full to under-5 malaria
deaths and x mal_adult_effect_frac (0.5) to deaths at 5 and over, and mal_cm_eff is 0.97 (ACT for uncomplicated
malaria) instead of 0.82. Entries with malaria results were refreshed again with --malaria, which checks that only
malaria lines, the totals and the malaria path moved outside lives first (63 of 99 entries refreshed; 2 under lives
first also moved other lines, through the refill order).

TB (logic review L-13, L-12, L-10): untreated HIV+ TB case fatality follows WHO Table 5 (0.78 off ART, 0.49 on ART,
weighted by ART coverage) instead of 0.62 x (1 - 0.3a); the detection rate is capped at 100%; the unused TB death
trend was removed. Entries with TB results were refreshed:  python tests/make_baseline.py --tb

Interest (audit I-26): the debt-stress factor now uses the more recent of World Bank and IMF WEO interest-to-revenue,
so fiscal capacity changed; entries with a government response were refreshed, and entries with no response were
checked to be unchanged:  python tests/make_baseline.py --fiscal

ART death risk and HIV transmission (logic review L-01, L-41, Batch 2): the ART hazard is now the excess death risk by
years since stopping ART from a CD4-stage cohort calculation (1.3-6.0% in years 1-5, up to 7.3% after), transmission is
the country's UNAIDS rate per person with unsuppressed viral load (median 0.12, was 0.04 everywhere) with one further
generation of infections, and art_reengage is 0.35 (was 0.5). Entries with HIV results were refreshed with --hiv (84 of
99; outside lives first only HIV lines, the totals and the HIV path moved, and no lives-first entry moved other lines).

Batch 3+4 (logic review L-05, L-43, IMP-03, IMP-11, IMP-04, IMP-16): the money-to-people conversion changed in every
disease (systems money no longer converted to services; unspecified money split by Global Fund module shares; country
ART and TB unit costs; the donor-funded cap; continuity 0.30). Entries whose results changed were refreshed one item at
a time with  python tests/make_baseline.py --batch34 <buckets>  (buckets: the diseases the item intentionally changes,
e.g. "HIV,TB,Malaria" or "all"); it refuses to run if a line outside those buckets moved outside lives first, and
lists what moved.

Aid rises (audit I-15): a line whose aid rises now counts as no loss instead of negative people losing services.
Entries where some line's aid rises were refreshed with the current model (later mechanisms off):
    python tests/make_baseline.py --gains-only"""
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
import health_model as hm  # noqa: E402
import scenarios as scn  # noqa: E402

COUNTRIES = ["KEN", "NGA", "MOZ", "HND", "IRQ"]
FISCALS = {"none": scn.DEFAULT_FISCAL, "custom25": ("custom", 0.25, True, "pro_rata", "p75"),
           "max_lives": ("max", 0.0, True, "lives_first", "p75")}
N_DRAWS = 100
MOU = "America First MOUs"
LEGACY_OPTS = {"Global Fund & Gavi shortfalls": {"gavi_cut": 24, "gf_cut": 28}}   # cuts the baseline was made with
NEW_MECHANISMS = ["tb_secondary", "mal_resurgence", "hiv_inf_death_untreated", "hiv_inf_death_treated"]  # 0 = off


def baseline_opts(preset, ci):
    """The scenario options the baseline entries were made with."""
    return LEGACY_OPTS.get(preset) or scn.default_opts(preset, ci)


def snapshot(res):
    L = res["lines"].set_index("line")
    cols = ["units_lost", "units_lost_lo", "units_lost_hi", "deaths_y1", "deaths_5y", "deaths_5y_lo", "deaths_5y_hi",
            "infections_5y", "net_loss_usd", "replaced_usd", "cov_drop_pp"]
    return {"lines": {l: {c: float(L.loc[l, c]) if L.loc[l, c] == L.loc[l, c] else None for c in cols} for l in L.index},
            "totals": {k: float(v) for k, v in res["totals"].items()},
            "path": {b: [float(x) for x in res["path"][b]] for b in hm.BUCKETS}}


def main():
    I, P = hm.load_inputs(), hm.load_params()
    out = {}
    for iso in COUNTRIES:
        for preset in scn.PRESETS:
            if preset == MOU and hasattr(scn, "mou_group") and scn.mou_group(I["ci"], iso) != "A":
                continue
            sc = scn.build_scenario(preset, baseline_opts(preset, I["ci"]), I["ci"])
            for fk, ft in FISCALS.items():
                out[f"{iso}|{preset}|{fk}"] = snapshot(hm.run_country(iso, sc, hm.Fiscal(*ft), I, P, n_draws=N_DRAWS))
    p = Path(__file__).parent / "baseline_sudden.json"
    p.write_text(json.dumps(out))
    print(f"saved {len(out)} runs to {p}")


def refresh_mou():
    """Replace only the America First MOUs entries, with the current model and the later mechanisms switched off."""
    I, P = hm.load_inputs(), hm.load_params()
    P.loc[NEW_MECHANISMS, ["central", "low", "high"]] = 0.0
    p = Path(__file__).parent / "baseline_sudden.json"
    out = {k: v for k, v in json.loads(p.read_text()).items() if k.split("|")[1] != MOU}
    sc = scn.build_scenario(MOU, scn.default_opts(MOU, I["ci"]), I["ci"])
    for iso in COUNTRIES:
        if scn.mou_group(I["ci"], iso) != "A":
            continue
        for fk, ft in FISCALS.items():
            out[f"{iso}|{MOU}|{fk}"] = snapshot(hm.run_country(iso, sc, hm.Fiscal(*ft), I, P, n_draws=N_DRAWS))
    p.write_text(json.dumps(out))
    print(f"saved {len(out)} runs to {p} ({sum(k.split('|')[1] == MOU for k in out)} America First MOUs)")


def refresh_gains():
    """I-15: a service line whose aid rises now counts as no loss (gains aren't modelled), where the original model
    counted gains as negative people losing services and negative deaths. Replace only the entries where some line's
    aid rises (IHME 2025 preliminary estimates for NGA and HND), with the current model and the later mechanisms off."""
    I, P = hm.load_inputs(), hm.load_params()
    P.loc[NEW_MECHANISMS, ["central", "low", "high"]] = 0.0
    p = Path(__file__).parent / "baseline_sudden.json"
    out = json.loads(p.read_text())
    done = []
    for key in list(out):
        iso, preset, fk = key.split("|")
        sc = scn.build_scenario(preset, baseline_opts(preset, I["ci"]), I["ci"])
        r = hm.run_country(iso, sc, hm.Fiscal(*FISCALS[fk]), I, P, n_draws=N_DRAWS)
        if r["totals"]["gains"] > 0:
            out[key] = snapshot(r)
            done.append(key)
    p.write_text(json.dumps(out))
    print(f"refreshed {len(done)} entries with aid rises: {done}")


def _close(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))


def refresh_hiv():
    """I-09 / I-27 PMTCT: HIV testing and care money is its own line (kappa of it counts toward ART), PMTCT costs
    US$250 a woman including her ART, and PMTCT women are outside the ART line's people covered. Replace the entries
    whose results changed, with the current model and the later mechanisms off. Outside the lives-first response, only
    HIV lines (and the totals and HIV path that include them) may change; that is checked here."""
    _refresh("hiv_", "HIV")


def refresh_tb():
    """L-13 / L-12: untreated HIV+ TB case fatality is now WHO Table 5's 0.78 off ART and 0.49 on ART, weighted by ART
    coverage, and the TB detection rate is capped at 100%. Replace the entries whose results changed, with the current
    model and the later mechanisms off. Outside the lives-first response, only TB lines (and the totals and TB path
    that include them) may change; that is checked here."""
    _refresh("tb_", "TB")


def _refresh(prefix, label):
    I, P = hm.load_inputs(), hm.load_params()
    P.loc[NEW_MECHANISMS, ["central", "low", "high"]] = 0.0
    p = Path(__file__).parent / "baseline_sudden.json"
    out = json.loads(p.read_text())
    done, other = [], []
    for key in list(out):
        iso, preset, fk = key.split("|")
        sc = scn.build_scenario(preset, baseline_opts(preset, I["ci"]), I["ci"])
        new = snapshot(hm.run_country(iso, sc, hm.Fiscal(*FISCALS[fk]), I, P, n_draws=N_DRAWS))
        old = out[key]
        moved = [l for l, cols in old["lines"].items() if any(not _close(new["lines"][l][c], v) for c, v in cols.items())]
        if not moved and all(_close(new["totals"][k], v) for k, v in old["totals"].items()):
            continue
        outside = [l for l in moved if not l.startswith(prefix)]
        if outside and fk != "max_lives":
            raise SystemExit(f"{key}: non-{label} lines changed outside lives first: {outside}")
        if outside:
            other.append(key)
        out[key] = new
        done.append(key)
    p.write_text(json.dumps(out))
    print(f"refreshed {len(done)} of {len(out)} entries; {len(other)} (lives first) also moved non-{label} lines: "
          f"{other}")


def refresh_batch34(buckets: str):
    """Batch 3+4: refresh every entry whose results changed, allowing only lines of the named buckets ("all" = every
    bucket) to move outside the lives-first response; prints the lines that moved per bucket."""
    allowed = hm.BUCKETS if buckets == "all" else [b.strip() for b in buckets.split(",")]
    I, P = hm.load_inputs(), hm.load_params()
    P.loc[NEW_MECHANISMS, ["central", "low", "high"]] = 0.0
    p = Path(__file__).parent / "baseline_sudden.json"
    out = json.loads(p.read_text())
    done, other, moved_lines = [], [], {}
    for key in list(out):
        iso, preset, fk = key.split("|")
        sc = scn.build_scenario(preset, baseline_opts(preset, I["ci"]), I["ci"])
        new = snapshot(hm.run_country(iso, sc, hm.Fiscal(*FISCALS[fk]), I, P, n_draws=N_DRAWS))
        old = out[key]
        moved = [l for l, cols in old["lines"].items() if any(not _close(new["lines"][l][c], v) for c, v in cols.items())]
        if not moved and all(_close(new["totals"][k], v) for k, v in old["totals"].items()):
            continue
        outside = [l for l in moved if hm.FULL_LINE_BUCKET.get(l) not in allowed]
        if outside and fk != "max_lives":
            raise SystemExit(f"{key}: lines outside {allowed} changed outside lives first: {outside}")
        if outside:
            other.append(key)
        for l in moved:
            moved_lines[l] = moved_lines.get(l, 0) + 1
        out[key] = new
        done.append(key)
    p.write_text(json.dumps(out))
    print(f"refreshed {len(done)} of {len(out)} entries; lines moved (entries): {moved_lines}; "
          f"{len(other)} lives-first entries also moved lines outside {allowed}: {other}")


def refresh_fiscal():
    """I-26: interest as % of revenue now comes from the more recent of World Bank and IMF WEO (no silent default), so
    the debt-stress factor and fiscal capacity changed. Only runs with a government response can change; entries with
    no response must be identical (checked)."""
    I, P = hm.load_inputs(), hm.load_params()
    P.loc[NEW_MECHANISMS, ["central", "low", "high"]] = 0.0
    p = Path(__file__).parent / "baseline_sudden.json"
    out = json.loads(p.read_text())
    done = []
    for key in list(out):
        iso, preset, fk = key.split("|")
        sc = scn.build_scenario(preset, baseline_opts(preset, I["ci"]), I["ci"])
        new = snapshot(hm.run_country(iso, sc, hm.Fiscal(*FISCALS[fk]), I, P, n_draws=N_DRAWS))
        old = out[key]
        same = all(_close(new["lines"][l][c], v) for l, cols in old["lines"].items() for c, v in cols.items()) and \
            all(_close(new["totals"][k], v) for k, v in old["totals"].items())
        if same:
            continue
        if fk == "none":
            raise SystemExit(f"{key}: a run with no government response changed")
        out[key] = new
        done.append(key)
    p.write_text(json.dumps(out))
    print(f"refreshed {len(done)} of {len(out)} entries (all with a government response): {done}")


def refresh_malaria():
    """I-06 / I-11 / I-27 (malaria): malaria coverage, cases and death trend now come from the Malaria Atlas Project,
    bednets and spraying have separate coverages, and malaria treatment costs US$14 a case. Replace the entries whose
    results changed, with the current model and the later mechanisms off. Outside the lives-first response, only
    malaria lines (and the totals and malaria path that include them) may change; that is checked here. Under lives
    first, malaria's deaths per dollar set the order in which the government refills lines, so other lines can move."""
    I, P = hm.load_inputs(), hm.load_params()
    P.loc[NEW_MECHANISMS, ["central", "low", "high"]] = 0.0
    p = Path(__file__).parent / "baseline_sudden.json"
    out = json.loads(p.read_text())
    done, other = [], []
    for key in list(out):
        iso, preset, fk = key.split("|")
        sc = scn.build_scenario(preset, baseline_opts(preset, I["ci"]), I["ci"])
        new = snapshot(hm.run_country(iso, sc, hm.Fiscal(*FISCALS[fk]), I, P, n_draws=N_DRAWS))
        old = out[key]
        moved = [l for l, cols in old["lines"].items() if any(not _close(new["lines"][l][c], v) for c, v in cols.items())]
        if not moved and all(_close(new["totals"][k], v) for k, v in old["totals"].items()):
            continue
        non_mal = [l for l in moved if not l.startswith("mal_")]
        if non_mal and fk != "max_lives":
            raise SystemExit(f"{key}: non-malaria lines changed outside lives first: {non_mal}")
        if non_mal:
            other.append(key)
        out[key] = new
        done.append(key)
    p.write_text(json.dumps(out))
    print(f"refreshed {len(done)} of {len(out)} entries; {len(other)} (lives first) also moved non-malaria lines: "
          f"{other}")


if __name__ == "__main__":
    if "--mou-only" in sys.argv:
        refresh_mou()
    elif "--gains-only" in sys.argv:
        refresh_gains()
    elif "--malaria" in sys.argv:
        refresh_malaria()
    elif "--hiv" in sys.argv:
        refresh_hiv()
    elif "--tb" in sys.argv:
        refresh_tb()
    elif "--fiscal" in sys.argv:
        refresh_fiscal()
    elif "--batch34" in sys.argv:
        refresh_batch34(sys.argv[sys.argv.index("--batch34") + 1])
    else:
        main()
