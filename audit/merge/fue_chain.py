"""
Full US exit, chipmunk -> tomato, one tomato item at a time (Step 3 check e): every difference in extra deaths
2026-2030 between the two branches attributed to the R1-R11 choices in PLAN.md.

    .venv/bin/python audit/merge/fue_chain.py <scratch dir> [out.csv]     # run from the root of the chipmunk checkout

Copies HEAD into <scratch dir>/chain (git archive; no branch or worktree is touched), then adds tomato's items
cumulatively: R1, R2, R5 and R6 are input columns only (copied from tomato's model_data/country_inputs.csv); R7 and
R3 also change health_model.py (tomato commits cd024d0 and 7f07d6b, applied with git apply) and add their own columns.
Each step runs every country (central run: n_draws=0, sudden cut, no government response, mortality trend on, as the
precomputed All Countries files). R8-R11 change nothing without a government response, so the last step must equal
tomato's own model_data/all_countries_Full_US_exit.csv.
"""
import io
import logging
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

GROUPS = [
    ("R1 ART cost (A1)", ["art_cost_full", "art_cost_full_lo", "art_cost_full_hi", "art_cost_full_source"], None),
    ("R2 donor pools (A2)", ["donor_share_hiv", "donor_share_hiv_source", "donor_share_imm", "donor_share_imm_source"],
     None),
    ("R5 WUENIC DTP3/MCV1 (L-17)", ["sh_imm_idpt", "sh_imm_idpt_year", "sh_imm_meas", "sh_imm_meas_year"], None),
    ("R6 UNAIDS HIV inputs (IMP-24)", ["sh_hiv_artc_zs", "sh_hiv_incd_tl", "sh_hiv_incd_tl_year", "sh_hiv_pmtc_zs",
                                       "sh_hiv_pmtc_zs_year", "plhiv", "hiv_pos_pregnancies",
                                       "hiv_pos_pregnancies_year"], None),
    ("R7 projected births (L-24)", [f"births_{y}" for y in range(2026, 2031)] + ["births_proj_source"], "cd024d0"),
    ("R3 malaria cap (A3)", [f"donor_share_mal_{k}{s}" for k in ("itn", "irs", "cm") for s in ("", "_source")],
     "7f07d6b"),
]
COLS = ["deaths_5y", "deaths_5y_HIV", "deaths_5y_TB", "deaths_5y_Malaria", "deaths_5y_Immunization"]
RUN = """
import logging, sys; logging.disable(logging.WARNING); sys.path.insert(0, '.')
import health_model as hm, scenarios as scn
I, P = hm.load_inputs(), hm.load_params()
sc = scn.build_scenario("Full US exit", scn.default_opts("Full US exit", I["ci"]), I["ci"])
out = hm.run_all(sc, hm.Fiscal(*scn.DEFAULT_FISCAL), I, P, n_draws=0)
print(",".join(f"{out[c].sum():.6f}" for c in %r))
""" % COLS


def git(*a, **k):
    return subprocess.run(["git", *a], capture_output=True, check=True, **k)


def main(scratch: Path, out: Path):
    d = scratch / "chain"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    subprocess.run(f"git archive HEAD | tar -x -C '{d}'", shell=True, check=True)
    T = pd.read_csv(io.StringIO(git("show", "tomato:model_data/country_inputs.csv", text=True).stdout))
    rows = []

    def step(name):
        r = subprocess.run([sys.executable, "-c", RUN], cwd=d, capture_output=True, text=True, check=True)
        rows.append([name, *map(float, r.stdout.strip().splitlines()[-1].split(","))])
        print(name, *(f"{v:,.0f}" for v in rows[-1][1:]))

    step("chipmunk")
    for name, cols, commit in GROUPS:
        if commit:
            patch = git("show", commit, "--", "health_model.py").stdout
            subprocess.run(["git", "apply", "-"], cwd=d, input=patch, check=True)
        H = pd.read_csv(d / "model_data/country_inputs.csv")
        assert (H.iso3.values == T.iso3.values).all()
        for c in cols:
            H[c] = T[c]
        H.to_csv(d / "model_data/country_inputs.csv", index=False)
        step("+ " + name)
    tom = pd.read_csv(io.StringIO(git("show", "tomato:model_data/all_countries_Full_US_exit.csv", text=True).stdout))
    rows.append(["tomato (its own precomputed file)", *[float(tom[c].sum()) for c in COLS]])
    df = pd.DataFrame(rows, columns=["step", *COLS])
    df.to_csv(out, index=False, float_format="%.0f")
    print(df.round(0).to_string(index=False))


if __name__ == "__main__":
    logging.disable(logging.WARNING)
    main(Path(sys.argv[1]), Path(sys.argv[2] if len(sys.argv) > 2 else "audit/merge/fue_chain.csv"))
