"""Compare the browser (JavaScript) model against the Python reference.

Run:  node verify_js.js > /tmp/js.json  &&  python3 compare_js_py.py
"""
import json
import sys
from interior_ballistics import Charge, simulate, form_from_lambda, IN, PSI

A_BURN, LAM, H_WALL, N_BURN = 3.90773e-8, 0.3799, 3.3326e5, 0.80
DT = 1.0e-7                      # must equal the dt used in verify_js.js

js = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/js.json"))
if js["errors"]:
    print("!! JavaScript reported errors:", js["errors"])

print(f"{'L(in)':>6} | {'v_py':>8} {'v_js':>8} {'Δ%':>8} | "
      f"{'pmuz_py':>8} {'pmuz_js':>8} {'Δ%':>8} | "
      f"{'peak_py':>8} {'peak_js':>8} {'Δ%':>8} | {'ψ_py':>7} {'ψ_js':>7}")
worst = 0.0
for row in js["rows"]:
    c = Charge(a_burn=A_BURN, h_wall=H_WALL, n_burn=N_BURN, L_barrel=row["L"] * IN)
    c.chi, c.lam, c.mu = form_from_lambda(LAM)
    r = simulate(c, dt=DT, store_every=10**9)
    d = []
    for py, jsv in ((r["v_muzzle"], row["v"]),
                    (r["p_muzzle_base"], row["pBase"]),
                    (r["peak_p_breech"], row["peak"])):
        d.append(100.0 * (jsv - py) / py)
        worst = max(worst, abs(d[-1]))
    print(f"{row['L']:6.1f} | {r['v_muzzle']:8.2f} {row['v']:8.2f} {d[0]:+8.4f} | "
          f"{r['p_muzzle_base']/1e6:8.2f} {row['pBase']/1e6:8.2f} {d[1]:+8.4f} | "
          f"{r['peak_p_breech']/1e6:8.2f} {row['peak']/1e6:8.2f} {d[2]:+8.4f} | "
          f"{r['psi_exit']:7.4f} {row['psi']:7.4f}")

print(f"\nworst absolute relative difference between the two implementations: "
      f"{worst:.5f} %")
print("energy-closure error reported by the JS model: "
      f"{max(abs(r['closure']) for r in js['rows'])*100:.3f} % (max over the sweep)")
print("PASS" if worst < 0.05 else "FAIL - implementations disagree")
