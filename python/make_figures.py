"""Generate the figures used in doc/5.56_interior_ballistics.docx."""
import json
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from interior_ballistics import Charge, simulate, energy_budget, IN, PSI, GR

OUT = "../doc"
C = {"s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a", "s4": "#eda100",
     "s5": "#e87ba4", "s7": "#4a3aa7", "s8": "#e34948",
     "ink": "#0b0b0b", "sec": "#52514e", "grid": "#e1e0d9", "muted": "#898781"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": "#c3c2b7", "axes.linewidth": 0.8,
    "axes.labelcolor": C["sec"], "axes.titlesize": 10, "axes.titleweight": "bold",
    "xtick.color": C["muted"], "ytick.color": C["muted"],
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "grid.color": C["grid"], "grid.linewidth": 0.7,
    "legend.frameon": False, "legend.fontsize": 8,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.dpi": 220, "savefig.bbox": "tight",
})


def style(ax):
    ax.grid(True, axis="y")
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


BARRELS = [10.5, 14.5, 20.0]
COLS = [C["s1"], C["s2"], C["s3"]]
RUNS = []
for L in BARRELS:
    c = Charge(L_barrel=L * IN)
    RUNS.append((L, c, simulate(c, dt=1e-7, store_every=5)))

# ---------------------------------------------------------------- figure 1
fig, ax = plt.subplots(figsize=(6.4, 3.5))
for (L, c, r), col in list(zip(RUNS, COLS))[::-1]:
    H = r["history"]
    ax.plot([t * 1e3 for t in H["t"]], [p / 1e6 for p in H["p_base"]],
            color=col, lw=1.9, label=f"{L:g} in")
    ax.plot(r["t_exit"] * 1e3, r["p_muzzle_base"] / 1e6, "o", color=col,
            ms=5.5, mec="white", mew=1.4, zorder=5)
    ax.annotate(f"{r['p_muzzle_base']/1e6:.0f} MPa",
                (r["t_exit"] * 1e3, r["p_muzzle_base"] / 1e6),
                textcoords="offset points", xytext=(7, 4), fontsize=7.5,
                color=col, fontweight="bold")
ax.set_xlabel("time after ignition  t  (ms)")
ax.set_ylabel("bullet-base pressure  $p_\\mathrm{base}$  (MPa)")
ax.set_title("Bullet-base pressure history, M855, three barrel lengths")
ax.set_ylim(bottom=0)
h, l = ax.get_legend_handles_labels()
ax.legend(h[::-1], l[::-1], title="barrel length", title_fontsize=8)
style(ax)
fig.savefig(f"{OUT}/fig1_pressure_time.png")
plt.close(fig)

# ---------------------------------------------------------------- figure 2
fig, ax = plt.subplots(figsize=(6.4, 3.5))
L, c, r = RUNS[2]
H = r["history"]
for key, col, lab in (("p_breech", C["s1"], "breech, $p_\\mathrm{br}$"),
                      ("p", C["s2"], "space-mean, $\\bar p$"),
                      ("p_base", C["s3"], "bullet base, $p_\\mathrm{base}$")):
    ax.plot([t * 1e3 for t in H["t"]], [p / 1e6 for p in H[key]],
            color=col, lw=1.9, label=lab)
ax.plot([t * 1e3 for t in H["t"]], [p / 1e6 if p > 0 else float("nan")
                                    for p in H["p_port"]],
        color=C["s4"], lw=1.7, ls="--", label="gas-port station (12 in)")
ax.axvline(r["t_peak"] * 1e3, color=C["muted"], lw=0.8, ls=":")
ax.annotate(f"peak {r['peak_p_breech']/1e6:.0f} MPa at {r['t_peak']*1e3:.3f} ms",
            (r["t_peak"] * 1e3, r["peak_p_breech"] / 1e6),
            textcoords="offset points", xytext=(8, 2), fontsize=7.5, color=C["sec"])
ax.set_xlabel("time after ignition  t  (ms)")
ax.set_ylabel("pressure (MPa)")
ax.set_title("Pressure at three stations along the gas column, 20 in barrel")
ax.set_ylim(bottom=0)
ax.legend()
style(ax)
fig.savefig(f"{OUT}/fig2_stations.png")
plt.close(fig)

# ---------------------------------------------------------------- figure 3
fig, axes = plt.subplots(1, 2, figsize=(6.9, 3.0))
for (L, c, r), col in list(zip(RUNS, COLS))[::-1]:
    H = r["history"]
    axes[0].plot([x * 1e3 for x in H["x"]], [p / 1e6 for p in H["p_base"]],
                 color=col, lw=1.9, label=f"{L:g} in")
    axes[0].plot(r["x_exit"] * 1e3, r["p_muzzle_base"] / 1e6, "o", color=col,
                 ms=5, mec="white", mew=1.3, zorder=5)
    axes[1].plot([t * 1e3 for t in H["t"]], H["v"], color=col, lw=1.9, label=f"{L:g} in")
    axes[1].plot(r["t_exit"] * 1e3, r["v_muzzle"], "o", color=col,
                 ms=5, mec="white", mew=1.3, zorder=5)
axes[0].set_xlabel("bullet travel  x  (mm)")
axes[0].set_ylabel("bullet-base pressure (MPa)")
axes[0].set_title("Pressure vs. travel", fontsize=9.5)
axes[1].set_xlabel("time  t  (ms)")
axes[1].set_ylabel("bullet velocity  v  (m/s)")
axes[1].set_title("Velocity vs. time", fontsize=9.5)
for a in axes:
    a.set_ylim(bottom=0)
    style(a)
h, l = axes[1].get_legend_handles_labels()
axes[1].legend(h[::-1], l[::-1], title="barrel length", title_fontsize=8)
fig.savefig(f"{OUT}/fig3_px_vt.png")
plt.close(fig)

# ---------------------------------------------------------------- sweep
Ls, V, PB, PM, PK, TE, PSIe = [], [], [], [], [], [], []
for i in range(45):
    L = 5 + (26 - 5) * i / 44
    c = Charge(L_barrel=L * IN)
    r = simulate(c, dt=1e-7, store_every=10 ** 9)
    Ls.append(L); V.append(r["v_muzzle"]); PB.append(r["p_muzzle_base"] / 1e6)
    PM.append(r["p_muzzle_mean"] / 1e6); PK.append(r["peak_p_breech"] / 1e6)
    TE.append(r["t_exit"] * 1e3); PSIe.append(r["psi_exit"])

VEL_DATA = {"Lucky Gunner": [(7, 2257), (10.5, 2653), (14.5, 2920), (16, 2990),
                             (18, 3058), (22, 3110)],
            "SADJ / Watters": [(14.5, 2700), (20, 2979)],
            "TFB": [(16.1, 2932), (20, 3059)]}
PMUZ_DATA = [(24, 4800), (14.5, 8150), (10.5, 11500), (7, 17140)]

fig, ax = plt.subplots(figsize=(6.4, 3.5))
ax.plot(Ls, V, color=C["s1"], lw=2.0, label="model", zorder=3)
for (src, pts), col, mk in zip(VEL_DATA.items(),
                               [C["s2"], C["s3"], C["s4"]], ["o", "s", "^"]):
    ax.plot([p[0] for p in pts], [p[1] * 0.3048 for p in pts], mk, color=col,
            ms=5.5, mec="white", mew=1.2, ls="none", label=src, zorder=4)
ax.set_xlabel("barrel length from bolt face  $L_\\mathrm{b}$  (in)")
ax.set_ylabel("muzzle velocity  $v_\\mathrm{m}$  (m/s)")
ax.set_title("Muzzle velocity vs. barrel length — model and measurement")
ax.legend(loc="lower right")
style(ax)
sec = ax.secondary_yaxis("right", functions=(lambda v: v / 0.3048,
                                             lambda v: v * 0.3048))
sec.set_ylabel("(ft/s)", color=C["muted"])
fig.savefig(f"{OUT}/fig4_velocity_sweep.png")
plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 3.5))
ax.plot(Ls, PB, color=C["s1"], lw=2.0, label="model, bullet base $p_\\mathrm{base}$")
ax.plot(Ls, PM, color=C["s2"], lw=1.7, ls="--", label="model, space-mean $\\bar p$")
ax.plot([p[0] for p in PMUZ_DATA], [p[1] * PSI / 1e6 for p in PMUZ_DATA], "s",
        color=C["s3"], ms=6, mec="white", mew=1.2, ls="none",
        label="SADJ measured uncorking pressure")
ax.set_xlabel("barrel length from bolt face  $L_\\mathrm{b}$  (in)")
ax.set_ylabel("pressure at bullet exit (MPa)")
ax.set_title("Muzzle (uncorking) pressure vs. barrel length")
ax.legend()
style(ax)
sec = ax.secondary_yaxis("right", functions=(lambda v: v * 1e6 / PSI / 1000,
                                             lambda v: v * 1000 * PSI / 1e6))
sec.set_ylabel("(kpsi)", color=C["muted"])
fig.savefig(f"{OUT}/fig5_muzzle_pressure.png")
plt.close(fig)

# burnt fraction + exit time, two panels
fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.9))
axes[0].plot(Ls, PSIe, color=C["s1"], lw=2.0)
axes[0].set_xlabel("barrel length (in)")
axes[0].set_ylabel("burnt fraction $\\psi$ at exit")
axes[0].set_title("Charge consumed in the bore", fontsize=9.5)
axes[0].set_ylim(0, 1.05)
axes[1].plot(Ls, TE, color=C["s2"], lw=2.0)
axes[1].set_xlabel("barrel length (in)")
axes[1].set_ylabel("muzzle-exit time (ms)")
axes[1].set_title("Barrel time", fontsize=9.5)
for a in axes:
    style(a)
fig.savefig(f"{OUT}/fig6_burnt_time.png")
plt.close(fig)

# ---------------------------------------------------------------- energy
c = Charge(L_barrel=20 * IN)
r = simulate(c, dt=1e-7, store_every=10 ** 9)
b = energy_budget(c, r)
labels = ["bullet\nkinetic\nenergy", "propellant\ngas KE", "bore\nfriction",
          "gas internal\nenergy at exit", "heat to\nbarrel wall", "unburnt\npropellant"]
vals = [b["kinetic"], b["gas_kinetic"], b["friction"], b["internal"],
        b["heat"], b["unburnt"]]
cols = [C["s1"], C["s3"], C["s4"], C["s2"], C["s8"], C["s7"]]
fig, ax = plt.subplots(figsize=(6.4, 3.2))
bars = ax.bar(range(len(vals)), vals, color=cols, width=0.55)
for i, (v, bar) in enumerate(zip(vals, bars)):
    ax.text(i, v + b["chem"] * 0.018, f"{100*v/b['chem']:.1f} %\n{v:.0f} J",
            ha="center", va="bottom", fontsize=8, color=C["ink"], fontweight="bold")
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, fontsize=8, color=C["sec"])
ax.set_ylabel("energy (J)")
ax.set_ylim(0, max(vals) * 1.30)
ax.set_title(f"Energy budget at muzzle exit, 20 in barrel "
             f"(charge chemical energy {b['chem']:.0f} J)")
style(ax)
fig.savefig(f"{OUT}/fig7_energy.png")
plt.close(fig)

# ---------------------------------------------------------------- form functions
fig, ax = plt.subplots(figsize=(6.4, 3.0))
zs = [i / 200 for i in range(201)]
for lam, col, lab in ((-0.9, C["s8"], "$\\lambda=-0.9$  strongly degressive"),
                      (-0.5, C["s2"], "$\\lambda=-0.5$  degressive"),
                      (0.0, C["s4"], "$\\lambda=0$  neutral"),
                      (0.3799, C["s1"], "$\\lambda=0.380$  fitted WC 844"),
                      (1.0, C["s7"], "$\\lambda=1.0$  strongly progressive")):
    chi = 1 / (1 + lam)
    ax.plot(zs, [min(chi * z * (1 + lam * z), 1) for z in zs], color=col,
            lw=1.9 if abs(lam - 0.3799) < 1e-6 else 1.4, label=lab)
ax.set_xlabel("fraction of the web burnt  $z$")
ax.set_ylabel("burnt mass fraction  $\\psi$")
ax.set_title("Form function $\\psi(z)=\\chi z(1+\\lambda z)$ for different grain geometries")
ax.legend(loc="upper left")
style(ax)
fig.savefig(f"{OUT}/fig8_form.png")
plt.close(fig)

# ---------------------------------------------------------------- exports
with open("calibration.json", "w") as fh:
    json.dump({
        "fitted": {"a_burn": c.a_burn, "n_burn": c.n_burn, "e1": c.e1,
                   "lambda": c.lam, "chi": c.chi, "h_wall": c.h_wall},
        "reference_20in": {"v_muzzle": r["v_muzzle"], "peak_breech": r["peak_p_breech"],
                           "p_muzzle_base": r["p_muzzle_base"],
                           "p_muzzle_mean": r["p_muzzle_mean"],
                           "t_exit": r["t_exit"], "t_peak": r["t_peak"]},
        "energy_budget_20in": b,
        "sweep": [{"L_in": L, "v": v, "p_base_MPa": pb, "p_mean_MPa": pm,
                   "peak_MPa": pk, "t_exit_ms": te, "psi_exit": ps}
                  for L, v, pb, pm, pk, te, ps in zip(Ls, V, PB, PM, PK, TE, PSIe)],
    }, fh, indent=1)

# a compact table used verbatim in the document
rows = []
for Lt in (5, 7, 7.5, 10.3, 10.5, 11.5, 14.5, 16, 18, 20, 22, 24, 26):
    c2 = Charge(L_barrel=Lt * IN, x_port=min(12 * IN, Lt * IN - 0.05))
    r2 = simulate(c2, dt=1e-7, store_every=10 ** 9)
    rows.append([Lt, Lt * 25.4, r2["v_muzzle"], r2["v_muzzle"] / 0.3048,
                 r2["p_muzzle_base"] / 1e6, r2["p_muzzle_base"] / PSI,
                 r2["p_muzzle_breech"] / 1e6, r2["t_exit"] * 1e3,
                 r2["psi_exit"] * 100, 0.5 * c2.m_b * r2["v_muzzle"] ** 2])
with open("sweep_table.json", "w") as fh:
    json.dump(rows, fh, indent=1)

print("figures + json written")
for L, v, pb in zip(Ls[::6], V[::6], PB[::6]):
    print(f"  {L:5.1f} in  {v:6.1f} m/s  {pb:6.1f} MPa")
