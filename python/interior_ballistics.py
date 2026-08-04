"""
Lumped-parameter interior ballistics model for 5.56x45 mm NATO (M855).

Reference implementation used to calibrate and cross-check the JavaScript
simulator in `web/ballistics.html`.

State vector  y = [z, x, v, Q]
    z : fraction of the propellant web burnt         [-]
    x : bullet travel from its at-rest position      [m]
    v : bullet velocity                              [m/s]
    Q : heat lost to the barrel and chamber walls    [J]

Governing relations
    Burn (Vieille / geometric law)   de/dt = a p^n ,   z = e/e1
    Form function                    psi(z) = chi z (1 + lam z + mu z^2)
    Equation of state (Nobel-Abel)   p (V/m - alpha) = R T
    Energy balance (Resal + losses)  f mc psi = p Vpsi + theta[(phi/2) mb v^2
                                                 + Q + Wfric]
    Newton (Lagrange secondary work) phi mb dv/dt = A (pbar - pfric)
    Wall heat transfer               dQ/dt = h S(x) (Tgas - Twall)

Repository: https://github.com/Teknosofen/BallisticAnalysis
"""

from dataclasses import dataclass, field
import math

GR = 6.479891e-5  # kg per grain
PSI = 6894.757    # Pa per psi
IN = 0.0254       # m per inch


# ----------------------------------------------------------------------------
# Grain geometry presets: (chi, lambda, mu) for psi = chi z (1 + lam z + mu z^2)
# ----------------------------------------------------------------------------
FORM_FUNCTIONS = {
    "sphere":        (3.0, -1.0, 1.0 / 3.0),   # psi = 1-(1-z)^3, degressive
    "cylinder":      (2.0, -0.5, 0.0),         # psi = 1-(1-z)^2, degressive
    "flake":         (1.06, -0.06, 0.0),       # thin disc, mildly degressive
    "tube_1perf":    (1.0, 0.0, 0.0),          # neutral, constant surface
    "grain_7perf":   (0.7, 0.43, 0.0),         # progressive until slivering
    "ball_deterred": (0.7247, 0.3799, 0.0),    # calibrated WC 844 equivalent
}


def form_from_lambda(lam, mu=0.0):
    """Generalised form function normalised so that psi(1) = 1 exactly.

    lam > 0 -> progressive (growing burning surface: perforated or
    surface-deterred grains); lam = 0 -> neutral; lam < 0 -> degressive.
    """
    return (1.0 / (1.0 + lam + mu), lam, mu)


@dataclass
class Charge:
    """Cartridge, propellant and weapon parameters."""
    # --- projectile / bore -------------------------------------------------
    m_b: float = 62.0 * GR          # bullet mass                        [kg]
    d_bore: float = 5.65e-3         # effective bore diameter            [m]
    x_b0: float = 34.3e-3           # bullet base from bolt face at rest [m]

    # --- chamber -----------------------------------------------------------
    V0: float = 1.65e-6             # free chamber volume behind bullet  [m^3]

    # --- propellant --------------------------------------------------------
    m_c: float = 25.0 * GR          # charge mass                        [kg]
    rho_p: float = 1600.0           # solid propellant density        [kg/m^3]
    f_imp: float = 1.00e6           # impetus (force constant) R*Tv     [J/kg]
    T_v: float = 2850.0             # adiabatic flame temperature          [K]
    alpha: float = 1.0e-3           # covolume                       [m^3/kg]
    gamma: float = 1.24             # ratio of specific heats              [-]
    e1: float = 0.130e-3            # half-web (burn distance)             [m]
    a_burn: float = 3.90773e-8      # Vieille coefficient        [m/(s Pa^n)]
    n_burn: float = 0.80            # Vieille exponent                     [-]
    form: str = "ball_deterred"     # grain geometry preset

    # --- losses ------------------------------------------------------------
    p_ign: float = 15.0e6           # primer / igniter pressure           [Pa]
    p_start: float = 30.0e6         # shot-start (engraving) pressure     [Pa]
    p_fric: float = 10.0e6          # residual bore resistance            [Pa]
    K_fric: float = 1.02            # extra secondary-work factor          [-]
    h_wall: float = 3.3326e5        # wall heat-transfer coefficient [W/m^2K]
    T_wall: float = 300.0           # initial wall temperature             [K]

    # --- weapon geometry ---------------------------------------------------
    L_barrel: float = 20.0 * IN     # barrel length from bolt face        [m]
    x_port: float = 12.0 * IN       # gas port from bolt face             [m]

    # derived
    A: float = field(init=False)
    chi: float = field(init=False)
    lam: float = field(init=False)
    mu: float = field(init=False)

    def __post_init__(self):
        self.A = 0.25 * math.pi * self.d_bore ** 2
        self.chi, self.lam, self.mu = FORM_FUNCTIONS[self.form]

    # ------------------------------------------------------------------
    @property
    def theta(self):
        return self.gamma - 1.0

    @property
    def phi(self):
        """Secondary work coefficient (Lagrange gas inertia + friction)."""
        return self.K_fric + self.m_c / (3.0 * self.m_b)

    @property
    def zeta(self):
        return self.m_c / self.m_b

    @property
    def L0(self):
        """Reduced chamber length V0/A."""
        return self.V0 / self.A

    @property
    def travel_max(self):
        return self.L_barrel - self.x_b0

    @property
    def loading_density(self):
        return self.m_c / self.V0

    @property
    def packing_fraction(self):
        return (self.m_c / self.rho_p) / self.V0


# ----------------------------------------------------------------------------
def psi_of_z(c: Charge, z: float) -> float:
    """Form function: mass fraction of propellant burnt."""
    if z >= 1.0:
        return 1.0
    if z <= 0.0:
        return 0.0
    return min(c.chi * z * (1.0 + c.lam * z + c.mu * z * z), 1.0)


def z_of_psi(c: Charge, psi_target: float) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        if psi_of_z(c, mid) < psi_target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def initial_z(c: Charge) -> float:
    """Burnt fraction the primer/igniter must produce to reach p_ign."""
    Vg0 = c.V0 - c.m_c / c.rho_p                       # initial ullage
    den = c.f_imp * c.m_c - c.p_ign * c.m_c * (1.0 / c.rho_p - c.alpha)
    psi0 = min(max(c.p_ign * Vg0 / den, 1e-9), 0.5)
    return z_of_psi(c, psi0)


def state(c: Charge, y):
    """Return (pbar, psi, Vpsi, Tgas) for the current state."""
    z, x, v, Q = y
    psi = psi_of_z(c, z)
    Vpsi = (c.V0 + c.A * x
            - c.m_c * (1.0 - psi) / c.rho_p    # volume still occupied by solid
            - c.alpha * c.m_c * psi)           # co-volume of the gas produced
    Vpsi = max(Vpsi, 1e-12)
    W_fric = c.p_fric * c.A * x
    num = (c.f_imp * c.m_c * psi
           - c.theta * (0.5 * c.phi * c.m_b * v * v + Q + W_fric))
    p = max(num / Vpsi, 0.0)
    m_gas = max(c.m_c * psi, 1e-12)
    T = p * Vpsi * c.T_v / (c.f_imp * m_gas)
    return p, psi, Vpsi, T


def lagrange(c: Charge, pbar: float):
    """Breech and bullet-base pressure from the Lagrange gradient."""
    z_ = c.zeta
    p_breech = pbar * (1.0 + z_ / 2.0) / (1.0 + z_ / 3.0)
    p_base = pbar / (1.0 + z_ / 3.0)
    return p_breech, p_base


def wetted_area(c: Charge, x):
    """Gas-swept wall area: equivalent cylinder of reduced length L0 + x."""
    return math.pi * c.d_bore * (c.L0 + x) + 2.0 * c.A


def derivs(c: Charge, y):
    z, x, v, Q = y
    p, psi, _, T = state(c, y)

    dz = c.a_burn * p ** c.n_burn / c.e1 if (z < 1.0 and p > 0.0) else 0.0

    if v <= 0.0 and p < c.p_start:
        dv = 0.0                          # still held by case grip / rifling
    else:
        dv = c.A * (p - c.p_fric) / (c.phi * c.m_b)
        if dv < 0.0 and v <= 0.0:
            dv = 0.0

    dQ = max(c.h_wall * wetted_area(c, x) * (T - c.T_wall), 0.0)
    return (dz, v, dv, dQ)


def simulate(c: Charge, dt=1.0e-7, t_max=5.0e-3, store_every=10):
    """RK4 integration until the bullet base reaches the muzzle."""
    y = [initial_z(c), 0.0, 0.0, 0.0]
    t = 0.0
    keys = ("t", "x", "v", "p", "p_breech", "p_base", "psi", "z", "p_port", "T")
    out = {k: [] for k in keys}
    xmax = c.travel_max
    port_travel = c.x_port - c.x_b0

    peak_p = 0.0
    t_peak = 0.0
    p_port_exit = 0.0
    p_port_peak = 0.0
    n = 0
    while t < t_max:
        p, psi, _, T = state(c, y)
        pb, pbase = lagrange(c, p)

        # pressure at the gas-port station (Lagrange parabolic distribution)
        L = c.L0 + y[1]
        yp = c.L0 + max(port_travel, 0.0)
        if y[1] >= port_travel and L > 0.0:
            r = min(yp / L, 1.0)
            p_port = pb * (c.m_b + 0.5 * c.m_c * (1 - r * r)) / (c.m_b + 0.5 * c.m_c)
        else:
            p_port = 0.0
        p_port_peak = max(p_port_peak, p_port)

        if n % store_every == 0:
            for k, val in zip(keys, (t, y[1], y[2], p, pb, pbase, psi,
                                     min(y[0], 1.0), p_port, T)):
                out[k].append(val)

        if pb > peak_p:
            peak_p, t_peak = pb, t

        if y[1] >= xmax:
            p_port_exit = p_port
            break

        k1 = derivs(c, y)
        y2 = [y[i] + 0.5 * dt * k1[i] for i in range(4)]
        k2 = derivs(c, y2)
        y3 = [y[i] + 0.5 * dt * k2[i] for i in range(4)]
        k3 = derivs(c, y3)
        y4 = [y[i] + dt * k3[i] for i in range(4)]
        k4 = derivs(c, y4)
        y = [y[i] + dt / 6.0 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
             for i in range(4)]
        y[0] = min(y[0], 1.0)
        t += dt
        n += 1

    p, psi, Vpsi, T = state(c, y)
    pb, pbase = lagrange(c, p)
    return dict(
        t_exit=t, v_muzzle=y[2], x_exit=y[1], Q_loss=y[3],
        p_muzzle_mean=p, p_muzzle_breech=pb, p_muzzle_base=pbase,
        T_muzzle=T, psi_exit=psi, V_exit=Vpsi,
        peak_p_breech=peak_p, t_peak=t_peak,
        p_port_exit=p_port_exit, p_port_peak=p_port_peak,
        history=out,
    )


# ----------------------------------------------------------------------------
def energy_budget(c: Charge, r):
    """Close the energy books at muzzle exit."""
    v = r["v_muzzle"]
    E_chem = c.m_c * c.f_imp / c.theta
    E_kin = 0.5 * c.m_b * v * v
    E_gas = c.m_c * v * v / 6.0
    E_fric = c.p_fric * c.A * r["x_exit"]
    E_int = r["p_muzzle_mean"] * r["V_exit"] / c.theta
    E_heat = r["Q_loss"]
    E_unburnt = (1.0 - r["psi_exit"]) * c.m_c * c.f_imp / c.theta
    total = E_kin + E_gas + E_fric + E_int + E_heat + E_unburnt
    return dict(chem=E_chem, kinetic=E_kin, gas_kinetic=E_gas, friction=E_fric,
                internal=E_int, heat=E_heat, unburnt=E_unburnt, total=total,
                closure=(total - E_chem) / E_chem)


def summary(c: Charge, r):
    print(f"  {c.L_barrel/IN:5.1f} in  v {r['v_muzzle']:6.1f} m/s "
          f"({r['v_muzzle']/0.3048:5.0f} fps)  t {r['t_exit']*1e3:5.3f} ms  "
          f"p_pk {r['peak_p_breech']/1e6:6.1f} MPa  "
          f"p_muz(base) {r['p_muzzle_base']/1e6:5.1f} MPa "
          f"({r['p_muzzle_base']/PSI:6.0f} psi)  burnt {r['psi_exit']*100:5.1f}%")


if __name__ == "__main__":
    c = Charge()
    print(f"bore area {c.A*1e6:.3f} mm^2   L0 {c.L0*1e3:.1f} mm")
    print(f"loading density {c.loading_density:.0f} kg/m^3   "
          f"packing {c.packing_fraction:.3f}   phi {c.phi:.3f}   zeta {c.zeta:.3f}")
    for L in (7, 10.5, 14.5, 16, 20, 24):
        c2 = Charge(L_barrel=L * IN)
        summary(c2, simulate(c2, store_every=100_000))
