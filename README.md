# BallisticAnalysis

Interior ballistics of the **5.56 × 45 mm NATO** cartridge (M855 / SS109, 62 gr):
pressure and bullet motion inside the bore as a function of barrel length, with
particular attention to the **muzzle velocity** and the **pressure still acting
behind the bullet at the instant it leaves the muzzle** ("uncorking" pressure).

The model is of the classical lumped-parameter class — the same family as IBHVG2
and the interior-ballistics module of PRODAS — extended with the Lagrange
pressure gradient and an explicit wall heat-transfer term.

| | |
|---|---|
| **Simulator** | [`web/ballistics.html`](web/ballistics.html) — open it in any browser; no server, no build, no dependencies |
| **Report** | [`doc/5.56_interior_ballistics.docx`](doc/5.56_interior_ballistics.docx) — full derivation, calibration, validation, references ([PDF](doc/5.56_interior_ballistics.pdf)) |
| **Reference model** | [`python/interior_ballistics.py`](python/interior_ballistics.py) |

---

## Headline results

Reference load: 62 gr M855, 25.0 gr WC 844-equivalent charge, 1.65 cm³ free
chamber volume, effective bore diameter 5.65 mm.

| Barrel (in) | Muzzle velocity | Muzzle pressure at bullet base | Peak breech pressure | Charge burnt |
|---:|---:|---:|---:|---:|
| 7.0 | 665 m/s (2183 ft/s) | 202 MPa (29 290 psi) | 385 MPa | 79 % |
| 10.5 | 789 m/s (2589 ft/s) | 150 MPa (21 810 psi) | 385 MPa | 98 % |
| 14.5 | 872 m/s (2859 ft/s) | 91 MPa (13 220 psi) | 385 MPa | 100 % |
| 16.0 | 891 m/s (2925 ft/s) | 77 MPa (11 160 psi) | 385 MPa | 100 % |
| 20.0 | 928 m/s (3046 ft/s) | 51 MPa (7 447 psi) | 385 MPa | 100 % |
| 24.0 | 951 m/s (3121 ft/s) | 36 MPa (5 209 psi) | 385 MPa | 100 % |

Going from 10.5 in to 20 in buys **+18 % muzzle velocity** but drops the
uncorking pressure by **−66 %**. Peak pressure is completely independent of
barrel length: the pressure history inside the bore is identical, and barrel
length only decides where on that history the bullet leaves.

## The model

State vector `y = [z, x, v, Q]` — web burnt fraction, bullet travel, bullet
velocity, heat lost to the walls.

| | |
|---|---|
| Burning law | Vieille, `de/dt = a p^n`, `z = e/e₁` |
| Grain geometry | form function `ψ(z) = χz(1 + λz + μz²)` |
| Equation of state | Nobel–Abel, `p(V/m − α) = RT` |
| Energy balance | Résal, with explicit heat-loss and friction terms |
| Pressure distribution | Lagrange gradient — breech, space-mean, bullet base, gas port |
| Bullet motion | `φ m_b dv/dt = A(p̄ − p_r)`, `φ = K + ζ/3` |
| Wall heat transfer | `dQ/dt = h S(x)(T − T_w)` |
| Integration | fixed-step classical RK4 |

Three parameters are fitted (`a`, `λ`, `h`); everything else comes from published
data or standard values for single-base nitrocellulose propellant. See §7–§8 of
the report for the full parameter set and its sources.

## Validation

* **Muzzle velocity** — RMS error **2.7 %** against ten published chronograph
  points from three independent M855 cut-barrel test series spanning 7–22 in.
* **Muzzle pressure** — matched at 24 in (+8 %); over-predicted by 60–90 % below
  12 in against the only published uncorking-pressure dataset. §9.2 of the report
  works through why, and argues the discrepancy is at least partly in the
  measurement.
* **Energy** — the budget closes to **0.5 %** at muzzle exit.
* **Implementations** — the JavaScript and Python models agree to **0.021 %**
  across 16 barrel lengths.

## Repository layout

```
web/ballistics.html            self-contained interactive simulator
python/interior_ballistics.py  reference implementation
python/calibrate.py            least-squares calibration against published data
python/make_figures.py         regenerates every figure in the report
python/verify_js.js            runs the HTML page headlessly, dumps its results
python/compare_js_py.py        cross-checks JavaScript against Python
python/calibration.json        fitted parameters, reference results, sweep table
doc/make_docx.js               builds the report
doc/equations.tex.md           the 22 display equations, in LaTeX
doc/insert_equations.py        converts them to native Word equation objects
```

## Reproducing

```bash
# reference model and calibration
cd python
python3 interior_ballistics.py          # barrel-length sweep to stdout
python3 calibrate.py                    # refit a, lambda, h  (needs scipy)
python3 make_figures.py                 # regenerate doc/fig*.png (needs matplotlib)

# cross-check the browser model against Python
node verify_js.js > /tmp/js.json        # needs playwright + chromium
python3 compare_js_py.py /tmp/js.json

# rebuild the report
cd ../doc
node make_docx.js                       # needs the docx npm package
python3 insert_equations.py             # needs pandoc
```

The equations in the report are **native Word (OMML) equation objects**, editable
in Word's equation editor. They are authored as LaTeX in `doc/equations.tex.md`,
converted by pandoc, and spliced into the document — so editing an equation at
source means editing one line of LaTeX and re-running the two build commands.

## Disclaimer

This is an engineering modelling study for analysis and teaching. **It is not
load data and must not be used as such.** The parameter set was fitted to
published aggregate performance figures, not measured from any specific lot of
ammunition, and the propellant thermochemistry is generic. Do not use these
numbers to develop handloads.
