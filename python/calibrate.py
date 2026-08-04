"""Calibrate the 5.56x45 NATO / M855 lumped-parameter model.

Three free parameters are fitted by weighted least squares:

    a_burn     Vieille burn-rate coefficient           [m/(s Pa^n)]
    lam        form-function progressivity             [-]
    h_wall     wall heat-transfer coefficient          [W/m^2 K]

against two classes of measurement:

    * peak breech pressure, 380 MPa
      (SADJ port 3 in from the bolt face: 55 744 psi = 384 MPa;
       SCATP 5.56 max average pressure 380 MPa)
    * muzzle velocity versus barrel length, M855, three independent test
      series (Lucky Gunner cut-barrel, SADJ / Watters cut-barrel, TFB)

The muzzle ("uncorking") pressures published by SADJ are deliberately NOT
fitted; they are held back and used as an independent check.
"""
import math
import json
from scipy.optimize import least_squares
from interior_ballistics import (Charge, simulate, energy_budget,
                                 form_from_lambda, IN, PSI)

TARGET_PEAK = 380.0e6
DT = 2.0e-7

# barrel length [in], measured velocity [fps], source
VEL_DATA = [
    (7.0, 2257, "LuckyGunner"), (10.5, 2653, "LuckyGunner"),
    (14.5, 2920, "LuckyGunner"), (16.0, 2990, "LuckyGunner"),
    (18.0, 3058, "LuckyGunner"), (22.0, 3110, "LuckyGunner"),
    (14.5, 2700, "SADJ"), (20.0, 2979, "SADJ"),
    (16.1, 2932, "TFB"), (20.0, 3059, "TFB"),
]
# held back for validation: barrel length [in], uncorking pressure [psi]
PMUZ_DATA = [(24, 4800), (14.5, 8150), (10.5, 11500), (7, 17140)]


N_BURN = [0.80]


def make(a_burn, lam, h, L=20 * IN):
    c = Charge(a_burn=a_burn, h_wall=h, L_barrel=L, n_burn=N_BURN[0])
    c.chi, c.lam, c.mu = form_from_lambda(lam)
    return c


def run(a_burn, lam, h, L=20 * IN):
    c = make(a_burn, lam, h, L)
    return c, simulate(c, dt=DT, store_every=1_000_000)


def residual(p):
    a, lam, h = math.exp(p[0]), p[1], math.exp(p[2])
    N_BURN[0] = p[3]
    res = []
    _, r20 = run(a, lam, h, 20 * IN)
    res.append(3.0 * (r20["peak_p_breech"] - TARGET_PEAK) / 1e7)   # weight 3
    for L, fps, _src in VEL_DATA:
        _, r = run(a, lam, h, L * IN)
        res.append((r["v_muzzle"] / 0.3048 - fps) / 30.0)
    return res


print("fitting ...")
sol = least_squares(residual,
                    [math.log(3.90773e-8), 0.3799, math.log(3.3326e5), 0.80],
                    bounds=([math.log(1e-10), -0.9, math.log(1e3), 0.795],
                            [math.log(1e-5), 3.0, math.log(3e6), 0.805]),
                    xtol=1e-12, ftol=1e-12)
a, lam, h = math.exp(sol.x[0]), sol.x[1], math.exp(sol.x[2])
N_BURN[0] = sol.x[3]
print(f"n_burn    = {sol.x[3]:.4f}")

c, r = run(a, lam, h)
print("\n=== calibrated parameters ===")
print(f"a_burn    = {a:.5e} m/(s Pa^n)      (n = {c.n_burn})")
print(f"a/e1      = {a/c.e1:.5e} 1/(s Pa^n)   with e1 = {c.e1*1e3:.3f} mm")
print(f"lambda    = {lam:.4f}   ->  chi = {c.chi:.4f}")
print(f"h_wall    = {h:.4e} W/m^2 K")
print(f"cost      = {sol.cost:.4f}")

print("\n=== reference shot, 20 in barrel ===")
print(f"peak breech pressure {r['peak_p_breech']/1e6:7.1f} MPa "
      f"({r['peak_p_breech']/PSI:6.0f} psi)  at t = {r['t_peak']*1e3:.3f} ms")
print(f"muzzle velocity      {r['v_muzzle']:7.1f} m/s "
      f"({r['v_muzzle']/0.3048:6.0f} fps)  at t = {r['t_exit']*1e3:.3f} ms")
print(f"muzzle pressure      mean {r['p_muzzle_mean']/1e6:.1f} MPa, "
      f"breech {r['p_muzzle_breech']/1e6:.1f} MPa, "
      f"base {r['p_muzzle_base']/1e6:.1f} MPa ({r['p_muzzle_base']/PSI:.0f} psi)")
print(f"gas temp at exit     {r['T_muzzle']:.0f} K,  burnt {r['psi_exit']*100:.1f} %")

print("\n--- barrel-length sweep ---")
print(f"{'L(in)':>6} {'v(m/s)':>8} {'v(fps)':>8} {'pmuz_base':>10} {'(psi)':>8} "
      f"{'pmuz_mean':>10} {'p_peak':>8} {'t_exit':>8} {'burnt%':>7} {'port psi':>9}")
sweep = []
for L in (5, 7, 7.5, 8, 9, 10.3, 10.5, 11.5, 12.5, 14.5, 16, 18, 20, 22, 24, 26):
    c2 = make(a, lam, h, L * IN)
    c2.x_port = min(c2.x_port, c2.L_barrel - 0.05)
    r2 = simulate(c2, dt=DT, store_every=1_000_000)
    sweep.append(dict(L_in=L, v=r2["v_muzzle"], p_base=r2["p_muzzle_base"],
                      p_mean=r2["p_muzzle_mean"], peak=r2["peak_p_breech"],
                      t=r2["t_exit"], psi=r2["psi_exit"]))
    print(f"{L:6.1f} {r2['v_muzzle']:8.1f} {r2['v_muzzle']/0.3048:8.0f} "
          f"{r2['p_muzzle_base']/1e6:10.1f} {r2['p_muzzle_base']/PSI:8.0f} "
          f"{r2['p_muzzle_mean']/1e6:10.1f} {r2['peak_p_breech']/1e6:8.1f} "
          f"{r2['t_exit']*1e3:8.3f} {r2['psi_exit']*100:7.1f} "
          f"{r2['p_port_exit']/PSI:9.0f}")

print("\n--- fit quality: muzzle velocity ---")
errs = []
for L, fps, src in VEL_DATA:
    _, r2 = run(a, lam, h, L * IN)
    mod = r2["v_muzzle"] / 0.3048
    errs.append(100 * (mod - fps) / fps)
    print(f"  {L:5.1f} in  {src:12s} measured {fps:5.0f}  model {mod:5.0f} fps"
          f"   {errs[-1]:+5.1f} %")
print(f"  RMS error {math.sqrt(sum(e*e for e in errs)/len(errs)):.2f} %, "
      f"max |error| {max(abs(e) for e in errs):.2f} %")

print("\n--- independent check (NOT fitted): SADJ uncorking pressure ---")
for L, psi_ in PMUZ_DATA:
    _, r2 = run(a, lam, h, L * IN)
    mod = r2["p_muzzle_base"] / PSI
    print(f"  {L:5.1f} in   measured {psi_:6.0f} psi   model {mod:6.0f} psi"
          f"   {100*(mod-psi_)/psi_:+6.1f} %")

c2, r2 = run(a, lam, h, 20 * IN)
b = energy_budget(c2, r2)
print("\n--- energy budget at muzzle exit, 20 in ---")
for k, lbl in (("chem", "chemical energy in charge"),
               ("kinetic", "bullet translational KE"),
               ("gas_kinetic", "propellant-gas KE (Lagrange)"),
               ("friction", "work against bore friction"),
               ("internal", "internal energy left in gas"),
               ("heat", "heat lost to barrel walls"),
               ("unburnt", "unburnt propellant")):
    print(f"  {lbl:32s} {b[k]:8.1f} J   ({100*b[k]/b['chem']:5.1f} %)")
print(f"  {'TOTAL accounted':32s} {b['total']:8.1f} J   "
      f"closure error {100*b['closure']:+.3f} %")

with open("calibration.json", "w") as fh:
    json.dump(dict(a_burn=a, lam=lam, chi=c.chi, h_wall=h,
                   n_burn=c.n_burn, e1=c.e1, sweep=sweep), fh, indent=2)

print("\nPASTE INTO JS:")
print(f"  aBurn: {a:.6e},  lam: {lam:.5f},  hWall: {h:.5e}")
