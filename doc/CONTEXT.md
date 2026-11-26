# Project handoff — 5.56 × 45 mm NATO interior ballistics

**Purpose of this file.** Paste or upload this into a new Claude conversation (or add it to
a Claude Project's knowledge) to bring a fresh session fully up to speed without replaying
the original work. It carries the decisions, the calibrated numbers and the known
weaknesses, so none of it has to be rediscovered or re-argued.

- **Owner:** Åke Larsson (Teknosofen)
- **Repository:** https://github.com/Teknosofen/BallisticAnalysis
- **Local working copy:** `C:\Users\tekno\VSC\BallisticsAnalysis\BallisticAnalysis`
- **Original work:** August 2026, in a Claude Cowork session
- **Companion file:** `TRANSCRIPT.md` — the conversation that produced it

---

## 1. The original request

Build a model of the pressure history inside a rifle barrel firing standard 5.56 × 45 mm
NATO, to investigate how **barrel length** affects pressure over time and bullet position —
with particular interest in the **pressure remaining behind the bullet at the instant it
leaves the muzzle**. Muzzle velocity was added as a second output. Deliverables: a `.docx`
with the equations and sourced references, and a self-contained HTML + JavaScript simulator
to experiment with.

Choices the user made when asked:

- **Model depth:** lumped-parameter, with the compromises and the higher-fidelity
  alternatives described rather than implemented.
- **Simulator:** full "lab bench" — every parameter a slider, live plots, barrel-length sweep.
- **Document:** full derivation from first principles, not a reference sheet.

Later in the session: equations must be **native, editable Word equation objects**;
attribution is **Åke Larsson, Teknosofen** (explicitly *not* Getinge); the simulator header
carries **"By Teknosofen 2026"**.

---

## 2. The model

State vector `y = [z, x, v, Q]` — web burnt fraction, bullet travel, bullet velocity,
cumulative heat lost to the walls. Pressure is never integrated; it is reconstructed
algebraically at every derivative evaluation.

| Element | Form |
|---|---|
| Burning law (Vieille) | `de/dt = a·p^n`, `z = e/e₁` |
| Form function | `ψ(z) = χ·z·(1 + λz + μz²)`, normalised `χ = 1/(1+λ+μ)` |
| Equation of state | Nobel–Abel, `p(V/m − α) = RT` |
| Energy balance (Résal) | `m_c·ψ·f/θ = p·V_ψ/θ + ½φ·m_b·v² + Q + W_r` |
| Free volume | `V_ψ = V₀ + A·x − m_c(1−ψ)/ρ_p − α·m_c·ψ` |
| Pressure gradient | Lagrange: `p_br/p_base = 1 + ζ/2`, `p̄/p_base = 1 + ζ/3` |
| Bullet motion | `φ·m_b·dv/dt = A(p̄ − p_r)`, `φ = K + ζ/3` |
| Wall heat transfer | `dQ/dt = h·S(x)·(T − T_w)`, `S(x) = πd(L₀+x) + 2A` |
| Integration | fixed-step classical RK4 |

Ignition is handled by specifying a primer pressure `p_ign` and inverting the pressure
relation for the corresponding initial burnt fraction `ψ₀` (≈ 0.0064 — under 1 % of the
charge, so the result is insensitive to it).

### Why heat loss is an ODE and not a flat efficiency factor

This matters and was learned the hard way. A constant fractional reduction of the impetus
removes energy *in proportion to energy released*, i.e. mostly early. The real loss keeps
accumulating through the expansion phase when the swept area is largest. With a flat factor
the model **could not match measured velocity and measured muzzle pressure at the same
time**; with the rate equation it can. Do not "simplify" this back.

---

## 3. Parameters

### Fitted (3 parameters, weighted least squares)

| Parameter | Value |
|---|---|
| `a` (Vieille coefficient) | 3.90773 × 10⁻⁸ m·s⁻¹·Pa⁻ⁿ |
| `λ` (form-function progressivity) | 0.3799 → χ = 0.7247 |
| `h` (wall heat-transfer coefficient) | 3.3326 × 10⁵ W·m⁻²·K⁻¹ |

Fitted against the peak breech pressure (380 MPa, weight × 3) plus ten muzzle-velocity
points from three independent M855 test series. The four published **muzzle** pressures were
deliberately **withheld** from the fit and used as an independent check.

Robustness: freeing the Vieille exponent `n` as a fourth parameter returns n = 0.797, so
fixing it at 0.80 costs nothing. Adding the withheld muzzle pressures to the objective moves
the parameters < 4 % and does *not* fix the short-barrel discrepancy — it is not a fitting
artefact.

### Fixed

| Quantity | Value | Class |
|---|---|---|
| Bullet mass `m_b` | 62 gr = 4.018 g | published |
| Effective bore dia. `d` | 5.65 mm → A = 25.07 mm² | assumed (between land and groove) |
| Bullet base from bolt face `x_b0` | 34.3 mm | derived from COAL − bullet length |
| Free chamber volume `V₀` | 1.65 cm³ | **derived — largest residual uncertainty** |
| Charge mass `m_c` | 25.0 gr = 1.620 g | assumed (packing-fraction limited) |
| Solid density `ρ_p` | 1600 kg/m³ | generic NC ball propellant |
| Impetus `f` | 1.00 MJ/kg | generic single-base |
| Flame temperature `T_v` | 2850 K | generic single-base |
| Covolume `α` | 1.00 × 10⁻³ m³/kg | generic |
| `γ` | 1.24 (θ = 0.24) | generic |
| Half-web `e₁` | 0.130 mm | only `a/e₁` is identifiable |
| Exponent `n` | 0.80 | fitted → 0.797, fixed |
| `p_ign` / `p_start` / `p_r` | 15 / 30 / 10 MPa | assumed |
| `K` | 1.02 | assumed |
| `T_wall` | 300 K | assumed (cold barrel) |

**Note on `V₀`:** seating depth 10.3 mm, bullet occupies ≈ 0.26 cm³ inside the case, leaving
≈ 1.59 cm³; 1.65 cm³ adopted to allow for the boat-tail and throat. Loading density 982
kg/m³, solid packing fraction 0.614 (random close packing of spheres is 0.64) — this
consistency check is what bounds the charge mass.

---

## 4. Headline results

Reference shot, 20 in barrel:

| Quantity | Value |
|---|---|
| Muzzle velocity | 928.5 m/s (3046 ft/s) |
| Peak breech pressure | 385.0 MPa (55 840 psi) at t = 0.408 ms |
| Muzzle pressure, bullet base | 51.3 MPa (7 447 psi) |
| Muzzle pressure, space-mean / breech | 58.2 / 61.7 MPa |
| Muzzle-exit time | 1.034 ms (travel 474.0 mm) |
| Charge burnt at exit | 100 % (complete at ≈ 290 mm travel) |
| Muzzle energy | 1 732 J |
| Peak acceleration | 1.91 × 10⁶ m/s² (195 000 g) |
| Gas temperature at exit | 1 220 K |

Barrel-length sweep:

| L (in) | v (m/s) | v (ft/s) | p_base at exit (MPa) | (psi) | t_exit (ms) | ψ (%) | E (J) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5.0 | 555.3 | 1822 | 249.8 | 36 230 | 0.553 | 63.4 | 620 |
| 7.0 | 665.4 | 2183 | 202.0 | 29 290 | 0.636 | 78.6 | 889 |
| 10.3 | 783.3 | 2570 | 152.6 | 22 130 | 0.751 | 97.0 | 1233 |
| 10.5 | 789.0 | 2589 | 150.3 | 21 810 | 0.757 | 98.0 | 1251 |
| 11.5 | 815.2 | 2674 | 134.1 | 19 460 | 0.789 | 100 | 1335 |
| 14.5 | 871.5 | 2859 | 91.2 | 13 220 | 0.879 | 100 | 1526 |
| 16.0 | 891.4 | 2925 | 76.9 | 11 160 | 0.922 | 100 | 1596 |
| 18.0 | 912.3 | 2993 | 62.4 | 9 048 | 0.979 | 100 | 1672 |
| 20.0 | 928.5 | 3046 | 51.3 | 7 447 | 1.034 | 100 | 1732 |
| 22.0 | 941.2 | 3088 | 42.8 | 6 200 | 1.088 | 100 | 1779 |
| 24.0 | 951.2 | 3121 | 35.9 | 5 209 | 1.142 | 100 | 1817 |
| 26.0 | 959.1 | 3147 | 30.4 | 4 408 | 1.195 | 100 | 1848 |

**The central finding.** Peak pressure is *completely independent of barrel length* — 385.0
MPa in every row. The in-bore pressure history is identical; barrel length only decides
where on that history the bullet leaves. From 10.5 in to 20 in the velocity rises 18 % while
the pressure behind the bullet at exit falls 66 %. Muzzle pressure is a far steeper function
of barrel length than velocity is, and that asymmetry is the whole story.

Energy budget at 20 in (chemical energy of charge 6 750 J): bullet KE 1 732 J (25.7 %), gas
KE 233 J (3.5 %), bore friction 119 J (1.8 %), gas internal energy still at the muzzle
2 890 J (42.8 %), heat to barrel 1 742 J (25.8 %), unburnt 0. Closure error −0.51 %.

---

## 5. Validation status

| Check | Result |
|---|---|
| Muzzle velocity vs 10 published points, 7–22 in | RMS error **2.7 %**, max 5.9 % |
| Energy budget closure at muzzle exit | **−0.51 %** |
| JavaScript vs Python implementations, 16 barrel lengths | agree to **0.021 %** |
| RK4 time-step convergence | < 0.01 % in velocity by Δt = 0.5 µs |
| Muzzle pressure vs SADJ (withheld from fit) | +8.5 % at 24 in, **+62 / +90 / +71 %** at 14.5 / 10.5 / 7 in |

### The known weakness — do not quietly "fix" it

The model over-predicts short-barrel uncorking pressure by up to a factor of two. This was
investigated and documented honestly in §9.2 of the report rather than fitted away. Three
findings:

1. **The model is energetically self-consistent.** An independent energy balance using the
   *measured* 7 in velocity gives ≈ 30 000 psi at the muzzle — essentially the model value.
   Producing the measured 17 140 psi would require ~1 500 J to vanish in 0.64 ms, more than
   the entire wall loss computed for a 20 in barrel over 1.03 ms.
2. **The measured set is flatter than adiabatic.** Between 24 in and 7 in the gas volume
   falls by 3.06×; pure adiabatic expansion at γ = 1.24 gives a pressure ratio of 4.25, and
   the real ratio should be *larger* still because 20 % of the charge is still burning at
   7 in. The measured ratio is 3.57.
3. **The measurement is hard.** The published intermediate points were obtained by averaging
   adjacent ports, the end points read from a chart, and a drilled port of finite volume
   sampling a pressure changing at ~10⁵ MPa/s will read low.

Conclusion carried in the document: the *trend* is robust; the *absolute level* below about
12 in should be treated as an upper bound with roughly a factor-of-two uncertainty.

The most likely modelling culprits, if anyone wants to pursue it: gas leakage past the
bullet (not modelled), and the constant bore-resistance assumption.

---

## 6. Section 11 — muzzle acoustics

Added late in the session, applying the muzzle conditions to the noise of the shot.

- **Blast source energy** = isentropic expansion work of the muzzle gas to ambient + gas
  kinetic energy + any ejected unburnt charge. 2 278 J at 20 in (0.54 g TNT equivalent),
  3 487 J at 10.5 in (0.83 g), 4 349 J at 7 in (1.04 g, of which 1 446 J is unburnt charge).
- **Bullet wave drag** deposits only ≈ 4 J per metre of flight — about 60 : 1 against the
  blast near the weapon.
- **Decay laws differ**: blast ∝ 1/R from the muzzle, crack ∝ r^(−3/4) in *miss distance*
  only. Blast dominates at the firing point; the crack dominates anywhere near the
  trajectory beyond ~10 m downrange. That is crack-thump.
- **Mach cone half-angle** 21.7° at Mach 2.71. The shooter sits at the apex and never
  receives his own bullet's N-wave — which is why a suppressor is fully effective for him
  even with supersonic ammunition.
- **Barrel length:** 10.5 in is **+4.4 dB** at the shooter's ear versus 20 in, splitting
  into +1.85 dB of extra blast energy and **+2.55 dB purely because the muzzle is 24 cm
  nearer the ear** (71 cm vs 95 cm). The crack moves 0.4 dB — it depends on Mach number
  only through an eighth root.
- **Conclusion:** the longer barrel is both faster and quieter. There is no acoustic price
  for the extra velocity; barrel length is not a noise-versus-performance trade.

**Important caveat, stated in §11.4 and §11.6:** absolute blast levels are *calibrated to a
published measurement* (162.5 dB peak at 1 m, AR-15 .223), not predicted. Ideal free-air
blast scaling over-predicts by ~9 dB because a muzzle is a directed gas jet, not a point
explosion. The relative comparisons are far more trustworthy than the absolute dB figures.

---

## 7. Repository layout and build

```
web/ballistics.html            self-contained simulator (no deps, no build)
python/interior_ballistics.py  reference implementation
python/calibrate.py            least-squares calibration
python/make_figures.py         regenerates every figure in the report
python/verify_js.js            drives the HTML headlessly (playwright), dumps results
python/compare_js_py.py        cross-checks JavaScript against Python
python/calibration.json        fitted parameters, reference results, sweep
doc/make_docx.js               builds the report (docx npm package)
doc/equations.tex.md           the 26 display equations, as LaTeX
doc/insert_equations.py        converts them to native Word objects (needs pandoc)
doc/5.56_interior_ballistics.docx / .pdf
handoff/                       this file and TRANSCRIPT.md
```

Rebuild the report:

```bash
cd python && python3 make_figures.py      # if figures changed
cd ../doc && node make_docx.js && python3 insert_equations.py
```

Verify the browser model still matches Python:

```bash
cd python && node verify_js.js > /tmp/js.json && python3 compare_js_py.py /tmp/js.json
```

### The equation pipeline — understand this before editing

Equations are **native Word OMML objects**, editable in Word's equation editor. They are
*not* images and *not* produced by the `docx` npm package directly.

1. `doc/equations.tex.md` holds all 26 as LaTeX, **in document order**.
2. `make_docx.js` emits a placeholder run `@@EQnn@@` for each, inside a paragraph that
   already carries the centre/right tab stops and the equation number.
3. `insert_equations.py` runs pandoc on the LaTeX, extracts each `<m:oMath>`, applies two
   schema-order corrections, and splices them into `word/document.xml`.

The two corrections are necessary — pandoc emits orderings the OOXML schema rejects (Word
tolerates them, but the file then fails validation): `CT_Dpr` requires begChr→sepChr→endChr,
and `CT_MathRPr` makes `<m:nor/>` and `<m:sty/>` mutually exclusive.

**To add or change an equation:** edit one line of LaTeX in `equations.tex.md`, add the
matching `eq()` call in `make_docx.js` at the right position, re-run both commands.
Equation numbering is positional — inserting one renumbers everything after it, and the
`eqRef(n)` cross-references in the prose must be updated by hand.

**Do not try to verify equations by converting to PDF with LibreOffice.** LibreOffice 24.2
cannot import OMML from .docx at all and renders them blank — this is a LibreOffice
limitation, not a defect in the file. Verify instead by round-tripping:
`pandoc -t markdown --wrap=none 5.56_interior_ballistics.docx | grep -oP '^\$.*\$ \(\d+\)$'`
should return all 26 with their numbers. Also run the docx skill's `validate.py`.

---

## 8. Decisions already taken (don't relitigate)

- **Lumped-parameter model**, by the user's explicit choice, with higher-fidelity options
  described in §12 rather than built.
- **Lagrange gradient included** — it costs three lines of algebra and no computation, and
  at ζ = 0.40 the breech-to-base spread is 20 %, so it is not optional.
- **Peak pressure calibrated to 380 MPa**, not the 430 MPa NATO EPVAT ceiling. The two
  figures are the same event measured at different transducer locations.
- **Equations as native Word objects**, after an earlier image-based version was rejected.
- **Report attribution: Åke Larsson, Teknosofen.** Getinge must not appear.
- **Figure and section numbering** is manual throughout `make_docx.js`. The document
  currently runs §1–§14 with Figures 1–13.

### GitHub

The Cowork sandbox routes git through a proxy that refuses any repository not authorised at
session start, so pushing from the sandbox fails with 403 regardless of credentials — a
personal access token does **not** help. Either push from the local clone, or start the
Cowork session with `Teknosofen/BallisticAnalysis` added to its sources, in which case the
proxy injects credentials automatically and no token is needed.

---

## 9. Open items

1. **Bore resistance** is a constant `p_r` after shot start. A measured `p_r(x)` curve —
   engraving spike, plateau, velocity-dependent rise — is the single highest-value
   improvement, and would let the model reproduce the velocity roll-over observed beyond
   about 20 in, which it currently cannot.
2. **Closed-bomb data for WC 844** would replace three fitted parameters and four generic
   thermochemical constants with measured values, turning the model from calibrated into
   predictive.
3. **Gas leakage past the bullet** — a simple orifice model would test whether blow-by
   explains part of the short-barrel muzzle-pressure gap.
4. **Nusselt-type heat-transfer correlation** instead of constant `h`, so the loss scales
   correctly with calibre and charge rather than being tied to this cartridge.
5. **After-effect modelling** — the blast field and the 1–3 % of velocity added by the gas
   jet in the first few calibres of free flight.

---

## 10. Sources used

Measured performance: Lucky Gunner Labs cut-barrel test; Small Arms Defense Journal
(Watters) barrel-length study; The Firearm Blog cartridge test 008; *International Journal
of Metrology and Quality Engineering* (2026) EPVAT measurements of SS109.

Cartridge specification: Wikipedia 5.56 × 45 mm NATO and .223 Remington; inetres.com 5.56 mm
ammunition; General Dynamics / St. Marks ball powder brochure.

Theory and propellant data: METU interior-ballistics thesis; ARL/BLAKE M1 propellant data;
ARL ADA555779 on 5.56 bore friction. Classical texts: Corner (1950), Serebryakov, Baer &
Frankle BRL-1183, IBHVG2 user's guide BRL-TR-2829.

Acoustics: Larson Davis firearm sound briefing; PEW Science unsuppressed M4A1 supplement;
Whitham (1952); Brode (1955).

Full URLs are in §14 of the report.

---

## 11. Standing disclaimer

This is an engineering modelling study for analysis and teaching. **It is not load data and
must not be used as such.** The parameter set was fitted to published aggregate performance
figures, not measured from any specific lot of ammunition, and the propellant thermochemistry
is generic. These numbers must not be used to develop handloads.
