# Conversation transcript — 5.56 × 45 mm NATO interior ballistics

Claude Cowork session, August 2026. Reconstructed for portability.

**How to read this.** User messages are reproduced **verbatim**. Assistant turns are
**condensed**: the substance, the numbers and the reasoning are preserved, but the tool
calls (file writes, shell commands, searches, screenshots) are summarised in italics rather
than reproduced. A verbatim copy of any claude.ai conversation can be obtained from
**Settings → Privacy → Export data**, which emails a JSON archive of the account.

**Redactions.** A GitHub personal access token pasted mid-session has been removed. It was
never successfully used and should have been revoked at the time — worth confirming at
https://github.com/settings/personal-access-tokens.

---

## 1 — The brief

> **User:** i want to be able to calculate and investigate the pressure over time in a rifle
> barrel shooting a standard NATO 5.56 mm cartridge. I am interested in how the barrel
> length affects the pressure over time (and bullet position), especially the final pressure
> in the barrel just when the bullet leaves the barrel. I want a .docx with the equations as
> well as a html script with embedded JS code to simulate and laborate with.

**Assistant** asked three clarifying questions before starting: how rigorous the physics
should be, what the simulator should focus on, and what level the document should target.

**User's answers:**
- Model depth: *"start with 1 but describe the possible compromises and improvements using the other models"* (i.e. lumped-parameter, with the Lagrange-gradient and distributed options discussed)
- Simulator: full lab bench
- Document: full derivation

---

## 2 — Scope additions, mid-work

> **User:** The velocity of the bullet when leaving the rifle shall also be calculated.
> in the document, please incude references to sources where appliccable and relevant
> please use my github repo at Teknosofen/BallisticAnalysis to store artifacts

*Assistant cloned the (empty) repository, researched cartridge and propellant data via web
search and a research subagent, and built the model.*

Key research findings carried into the model:

- Barrel-length velocity data from three independent M855 test series (Lucky Gunner cut-barrel, SADJ/Watters, TFB) — which disagree with each other by up to 8 % at the same length.
- NATO EPVAT max 430 MPa vs SCATP 380 MPa are the same event at different transducer locations.
- WC 844 thermochemistry is **not** published; generic single-base nitrocellulose values had to be used.
- SADJ measured "uncorking" pressures: 4 800 psi at 24 in rising to 17 140 psi at 7 in.

**Development notes from this phase:**

1. First attempt produced no ignition at all — the burning law is degenerate at ψ = 0. Fixed by specifying a primer pressure and inverting for the initial burnt fraction.
2. A spherical (degressive) form function could not reach the target velocity without a wildly excessive pressure peak. Switching to a *progressive* form function — physically correct for a surface-deterred ball propellant — resolved it, and the fit independently recovered λ = 0.38.
3. A flat heat-loss efficiency factor could not match measured velocity and measured muzzle pressure simultaneously; replacing it with a wall heat-transfer rate equation could. This was the pivotal modelling decision.

Calibration settled on `a = 3.90773e-8`, `λ = 0.3799`, `h = 3.3326e5`, fitted to peak
pressure plus ten velocity points, with the four published muzzle pressures withheld as an
independent check.

*Assistant built the HTML simulator, verified it headlessly in Chromium against the Python
reference (agreement 0.021 % across 16 barrel lengths), generated figures, and wrote the
.docx.*

**Delivered:** simulator, 25-page report, repo committed locally.

Headline results reported: 20 in barrel gives 928.5 m/s with 51.3 MPa (7 447 psi) still
behind the bullet at exit and a peak of 385 MPa; peak pressure is independent of barrel
length; 10.5 → 20 in gains 18 % velocity while muzzle pressure falls 66 %.

The assistant flagged §9.2 as deliberately unflattering: the model over-predicts
short-barrel uncorking pressure by 60–90 % against the one published dataset, and argued
from an independent energy balance that the discrepancy is at least partly in the
measurement rather than fitting it away.

---

## 3 — Getting it to GitHub

The sandbox had no `gh` CLI and no credentials. The assistant committed locally and asked
how to proceed.

> **User:** i can paste a token if ypu show me how to get it from github

*Assistant gave step-by-step instructions for creating a fine-grained token scoped to the
single repository with Contents: Read and write, a 7-day expiry, and advice to revoke it
afterwards.*

> **User:** [token pasted — REDACTED]

The push failed anyway:

```
remote: access denied by the git proxy: Teknosofen/BallisticAnalysis is not in this
session's authorized repository set, so the proxy will not inject a credential for it.
```

The sandbox routes git through a proxy that refuses any repository not authorised at session
start — **a token cannot help**. The assistant acknowledged the error was its own for
suggesting the token route without checking the proxy first, advised revoking the token, and
delivered a `.bundle` (full history) and a `.zip` instead.

**Lesson recorded:** to push from a Cowork session, add the repository to the session's
sources when starting the task; then no token is needed at all.

---

## 4 — Summary chart

> **User:** Can I drag and drop the files directly into the repo?
> please add a summary graph in the document showin the final velocity as function of
> barrel length.

*Assistant explained GitHub's web uploader (Add file → Upload files; unzip first; drag the
folders not the parent; Chrome preserves structure, Safari doesn't; 100 files / 25 MB
limits; tradeoff is losing commit history) and added Figure 6 — muzzle velocity against
barrel length over 5–26 in with the five service configurations marked and tabulated.*

The point the figure makes: 14.5 → 20 in is 5.5 in of barrel for 57 m/s, while 14.5 → 10.3
in is only 4.2 in but costs 88 m/s. Barrel length matters far more at the short end.

> **User:** pls update the bundle with the new docx and I will put that to github as described

*Assistant verified by cloning the bundle fresh — two commits, 28 files, .docx byte-identical
to the delivered one.*

---

## 5 — Simulator behaviour

> **User:** nice, how do i force an update after changing parameters like gas port position?
>
> **User:** in the html simulator i mean

**Answer: you don't — it's live.** Every slider fires on `input` and recomputes the whole
model immediately, including charts on tabs that aren't visible. Verified headlessly by
driving the gas-port slider:

| Port position | At bullet exit | Peak |
|---|---|---|
| 12.00 in | 8.4 kpsi | 18.1 kpsi |
| 7.50 in | 8.7 kpsi | 27.9 kpsi |
| 9.75 in | 8.5 kpsi | 23.1 kpsi |
| 16.00 in | 8.0 kpsi | 11.1 kpsi |

The subtlety worth knowing: the large number on the tile is the pressure **at bullet exit**,
and by then the gas column has nearly equalised, so port position barely moves it (8.0–8.7
kpsi across the whole range). The number that actually responds is the **peak**, which
varies 2.5×. That is physics, not a stale chart — moving a port rearward doesn't change how
much pressure remains at uncorking, it changes how hard the port is hit while the bullet is
still accelerating past it.

---

## 6 — Attribution and local delivery

> **User:** in the document, I do not want Getinge to be mentioned but Åke Larsson,
> Teknosofen instead. Also on the simulator page I want it to read "By Teknsofen 2026" at the
> top of the screen. The files are now copied to
> C:\Users\tekno\VSC\BallisticsAnalysis\BallisticAnalysis, please update the documents there
> so I can simply commit and push to github

*Assistant changed the title page and docx metadata to "Åke Larsson — Teknosofen", added a
"By Teknosofen 2026" pill to the simulator header (correcting the typo "Teknsofen" to match
the GitHub handle), tightened the header layout so the byline didn't push the theme toggle
onto a second row, and regenerated the screenshot figures.*

The device bridge was not reachable at first, so files were delivered as a zip.

> **User:** [connected the folder] please copy the files to the folder I just gave yu

*Assistant listed the folder (a clone at the summary-chart commit), wrote exactly the 8
changed files with modification-time guards so any local edits would have blocked the write
rather than being clobbered, and verified the on-disk sizes matched byte for byte.*

Noted: `ballistics.html` and `make_docx.js` shrank because the clone had CRLF line endings
and the written files use LF — not lost content.

---

## 7 — Muzzle acoustics

> **User:** thinking about the noise when the bullet leaves the barrel, how much is the
> pressure wave from the gas released behing the bullet and how much is the shock wave from
> the bullet
>
> **User:** i.e., will a longer barrel with higher bullet speed but lower pressure behind the
> escaping bullet be noisier or quieter than a shorter with lower speed but higher residual
> pressure

*Assistant computed blast source energies from the model's own energy budget, applied
Whitham's N-wave solution for the crack, calibrated the blast to a published measurement,
and checked against two acoustics sources.*

**Energy.** A 20 in barrel still holds 2 890 J in the gas at exit; ~2 280 J of that can do
work on the atmosphere — about half a gram of TNT equivalent in a millisecond. The bullet,
by contrast, deposits ~4 J per metre of flight through wave drag. Near the weapon the ratio
is about 60 : 1 in favour of the blast.

**But energy is the wrong currency** — the decay laws differ. Blast is a point source
(∝ 1/R from the muzzle); the crack is a moving line source (∝ r^−3/4 in *miss distance*,
independent of downrange position).

| Distance | Blast | Crack |
|---:|---:|---:|
| 1 m | 162.5 dB | 153.9 dB |
| 10 m | 142.5 dB | 138.9 dB |
| 50 m | 128.5 dB | 128.4 dB |
| 100 m | 122.5 dB | 123.9 dB |

At the firing point it is **essentially all blast** — the shooter is a metre from the source
*and* sits at the apex of the 21.7° Mach cone, so he never receives his own bullet's N-wave.
Near the trajectory beyond ~10 m downrange it is **essentially all crack**. That is
crack-thump, and the delay between the two is what acoustic sniper-location exploits.

**Which barrel is louder:** the short one, by **+4.4 dB** at the ear for 10.5 in vs 20 in —
+1.85 dB from 53 % more blast energy, and **+2.55 dB simply because the muzzle is 24 cm
closer to your head** (71 cm vs 95 cm). The crack changes by 0.4 dB, because it depends on
Mach number only through an eighth root.

**So the longer barrel is both faster and quieter.** No acoustic price for the extra
velocity — barrel length is not a noise-versus-performance trade at all.

Caveats given: peak overpressure is not perceived loudness; below 11.5 in unburnt propellant
burns outside as a secondary blast wave (which PEW Science measured); muzzle devices are not
modelled, and a brake can add 5–10 dB at the ear; and the absolute blast level is calibrated
to measurement, not predicted, because ideal blast scaling over-predicts a directed muzzle
jet by ~9 dB.

> **User:** please add this wonderful reasoning into the .docx including the reference

*Assistant added §11 "Muzzle noise: blast versus ballistic crack" with six subsections, four
new equations (23–26) as native Word objects, two new figures, and four new references
(Larson Davis, PEW Science, Whitham 1952, Brode 1955). Old §11–13 renumbered to §12–14, the
simulator screenshots became Figures 12–13, and all internal cross-references were updated.
Report now 32 pages, 26 equations, 13 figures.*

---

## 8 — This extract

> **User:** please help me extract this chat so i can import it onto another claude account

Produced `handoff/CONTEXT.md` (a working primer for a fresh session) and this transcript.

---

## Appendix — problems hit and how they were solved

| Problem | Resolution |
|---|---|
| No ignition — burning law degenerate at ψ = 0 | Specify primer pressure, invert for initial burnt fraction ψ₀ ≈ 0.0064 |
| Could not reach target velocity without excessive peak pressure | Progressive form function (λ > 0), physically right for deterred ball propellant |
| Could not match velocity **and** muzzle pressure together | Replace flat heat-loss factor with a wall heat-transfer rate equation |
| Calibration solver diverged (peak 5 157 MPa) | Bad initial guess; restarted from a known-good point |
| docx-js OMML equations rendered blank | LibreOffice 24.2 cannot import OMML at all — not a file defect |
| Images instead of equations — user wanted editable | pandoc LaTeX → OMML, spliced into `document.xml` via placeholders |
| pandoc OMML failed schema validation | Two element-order corrections in `insert_equations.py` |
| Overlapping curves in overlay charts | Draw longest barrel first so shorter ones sit on top |
| Clipped images in the .docx | Explicit `lineRule: 'auto'` on figure paragraphs |
| Clipped bar label in the energy chart | 14 % headroom on the axis |
| GitHub push 403 | Sandbox proxy, not credentials — add the repo to session sources, or push locally |
