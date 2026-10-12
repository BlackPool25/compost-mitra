#!/usr/bin/env python3
"""CompostMitra Biophysical Dynamic Kinetic Digital Twin.

Simulates aerobic composting biophysics using coupled Ordinary Differential Equations (ODEs)
grounded in Haug (1993), Mason (2006), and Higgins & Walker (2001) kinetics:
  1. Substrate degradation (Biodegradable Volatile Solids: BVS).
  2. Sensible and latent heat balance with temperature-dependent microbial kinetics.
  3. Moisture balance (metabolic water generation vs evaporative loss).
  4. US EPA 503 PFRP (Processes to Further Reduce Pathogens) thermal death integration.

Mathematical Model:
  - Substrate: dS/dt = -k_0 * f_T(T) * f_M(M) * f_O2 * S
  - Heat: C_p * dT/dt = H_rxn * (-dS/dt) - U*A*(T - T_amb) - lambda_vap * m_evap
  - Water: dW/dt = Y_w * (-dS/dt) - m_evap
  - Pathogens: d(log10 P)/dt = -k_pathogen(T)

Governance:
  - T1 REAL | LIT calc | D1 proxy
  - Deterministic physics equations; zero causal assertions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import plotly.graph_objects as go
from scipy.integrate import solve_ivp

# Thermodynamic and kinetic constants (Haug 1993, Mason 2006)
H_RXN_J_PER_KG_BVS = 18.0e6  # Enthalpy of dry organic oxidation (J/kg)
LAMBDA_VAP_J_PER_KG = 2.45e6  # Latent heat of water vaporization (J/kg)
CP_DRY_J_PER_KG_K = 1400.0  # Specific heat of dry organic matter (J/(kg*K))
CP_WATER_J_PER_KG_K = 4184.0  # Specific heat of liquid water (J/(kg*K))
Y_WATER_METABOLIC = 0.50  # kg metabolic water produced per kg BVS degraded
SEC_PER_DAY = 86400.0


@dataclass
class SimulationResults:
    """Outcome container for biophysical dynamic composting simulation."""

    days: np.ndarray
    temperature_c: np.ndarray
    moisture_pct: np.ndarray
    bvs_remaining_kg: np.ndarray
    cumulative_co2_kg: np.ndarray
    pathogen_log_reduction: np.ndarray
    max_temperature_c: float
    days_above_55c: float
    consecutive_days_above_55c: float
    pfrp_compliant: bool
    stabilization_day: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert simulation results to summary dictionary."""
        return {
            "max_temperature_c": round(self.max_temperature_c, 2),
            "days_above_55c": round(self.days_above_55c, 2),
            "consecutive_days_above_55c": round(self.consecutive_days_above_55c, 2),
            "pfrp_compliant": self.pfrp_compliant,
            "stabilization_day": self.stabilization_day,
            "final_temperature_c": round(float(self.temperature_c[-1]), 2),
            "final_moisture_pct": round(float(self.moisture_pct[-1]), 2),
            "total_bvs_degraded_pct": round(
                float((1.0 - self.bvs_remaining_kg[-1] / max(self.bvs_remaining_kg[0], 1e-6)) * 100.0),
                2,
            ),
            "cumulative_co2_kg": round(float(self.cumulative_co2_kg[-1]), 2),
            "pathogen_log_reduction": round(float(self.pathogen_log_reduction[-1]), 2),
            "metadata": self.metadata,
        }


def _cardinal_temp_factor(temp_c: float) -> float:
    """Cardinal temperature factor f_T(T) for microbial aerobic respiration.

    Follows Rosso / Ratkowsky shape:
      - T <= 5°C: 0.0 (dormancy)
      - 5°C < T < 35°C: quadratic mesophilic rise
      - 35°C <= T <= 58°C: plateau optimum (thermophilic zone)
      - 58°C < T < 72°C: linear decline due to thermal enzyme denaturation
      - T >= 72°C: 0.0 (inactivation)
    """
    if temp_c <= 5.0 or temp_c >= 72.0:
        return 0.0
    if temp_c < 35.0:
        return float(((temp_c - 5.0) / (35.0 - 5.0)) ** 2)
    if temp_c <= 58.0:
        return 1.0
    return float(max(0.0, 1.0 - (temp_c - 58.0) / (72.0 - 58.0)))


def _moisture_factor(moist_frac: float) -> float:
    """Moisture activity factor f_M(M) representing water activity and oxygen diffusion.

    Optimal range 50% to 65% moisture.
    Below 25%: biological activity severely limited by dryness.
    Above 70%: pore waterlogging restricts aerobic oxygen diffusion.
    """
    if moist_frac <= 0.25 or moist_frac >= 0.85:
        return 0.0
    if moist_frac < 0.50:
        return float((moist_frac - 0.25) / (0.50 - 0.25))
    if moist_frac <= 0.65:
        return 1.0
    return float(max(0.0, 1.0 - (moist_frac - 0.65) / (0.85 - 0.65)))


def _pathogen_kill_rate(temp_c: float) -> float:
    """Thermal death rate constant for fecal coliforms and Salmonella spp. (day^-1).

    Grounded in Bigelow / thermal death time kinetics:
      k_d(T) = k_ref * 10^((T - T_ref) / z) for T >= 45°C.
    """
    if temp_c < 45.0:
        return 0.01  # baseline background decay
    z_value = 5.5  # °C required for 10-fold rate increase
    return float(2.0 * (10.0 ** ((temp_c - 50.0) / z_value)))


def simulate_composting_pile(
    initial_wet_mass_kg: float = 20.0,
    initial_moisture_pct: float = 58.0,
    initial_bvs_fraction: float = 0.70,
    ambient_temp_c: float = 25.0,
    duration_days: float = 45.0,
    aeration_effectiveness: float = 0.90,
    insulation_level: str = "moderate",
    turning_days: Optional[List[int]] = None,
) -> SimulationResults:
    """Simulate dynamic aerobic composting pile trajectory over time.

    Solves the continuous coupled heat, mass, and biological decay system.

    Args:
        initial_wet_mass_kg: Starting wet mass of the pile (kg).
        initial_moisture_pct: Initial moisture percentage (e.g. 58.0).
        initial_bvs_fraction: Fraction of dry matter that is biodegradable (0.5 - 0.8).
        ambient_temp_c: Surrounding ambient temperature in °C.
        duration_days: Total simulation duration in days (e.g. 45 or 60).
        aeration_effectiveness: Oxygen availability factor (0.5 to 1.0).
        insulation_level: 'low', 'moderate', or 'high' (sets heat loss coefficient UA).
        turning_days: List of days on which turning aeration events occur.

    Returns:
        SimulationResults containing daily trajectory arrays, max T, PFRP status.
    """
    if initial_wet_mass_kg <= 0.1:
        raise ValueError("Initial wet mass must exceed 0.1 kg.")
    if not (20.0 <= initial_moisture_pct <= 85.0):
        raise ValueError("Initial moisture percentage must be between 20% and 85%.")

    turning_schedule = set(turning_days or [7, 14, 21, 28])

    # Initial state calculations
    moist_frac_0 = initial_moisture_pct / 100.0
    initial_water_kg = initial_wet_mass_kg * moist_frac_0
    initial_dry_kg = initial_wet_mass_kg * (1.0 - moist_frac_0)
    initial_bvs_kg = initial_dry_kg * initial_bvs_fraction
    inert_dry_kg = initial_dry_kg * (1.0 - initial_bvs_fraction)

    # Pile geometry and heat loss (UA)
    # Bulk density ~ 500 kg/m^3 -> Volume V = mass / 500
    volume_m3 = initial_wet_mass_kg / 500.0
    surface_area_m2 = 6.0 * (volume_m3 ** (2.0 / 3.0))  # approx cube surface

    ua_map = {
        "low": 12.0 * surface_area_m2,       # Uninsulated thin bin
        "moderate": 4.5 * surface_area_m2,   # Standard compost tumbler / plastic bin
        "high": 1.5 * surface_area_m2,       # Insulated hot-box / thick straw blanket
    }
    ua_w_per_k = ua_map.get(insulation_level.lower(), 4.5 * surface_area_m2)

    # Maximum degradation constant k0 (day^-1)
    k0 = 0.14

    # ODE State: y = [S (kg BVS), T (°C), W (kg water), cum_co2 (kg), log_pathogen_kill]
    y0 = [
        initial_bvs_kg,
        ambient_temp_c + 2.0,  # small initial biological warming
        initial_water_kg,
        0.0,
        0.0,
    ]

    def ode_system(t_day: float, y: np.ndarray) -> List[float]:
        S, T, W, cum_co2, log_kill = y

        S = max(0.001, S)
        W = max(0.001, W)
        total_dry = inert_dry_kg + S
        total_wet = total_dry + W
        m_frac = W / total_wet

        # Check turning event boost to aeration
        day_int = int(math.floor(t_day))
        current_aeration = aeration_effectiveness
        if day_int in turning_schedule:
            current_aeration = min(1.0, aeration_effectiveness * 1.15)

        # Kinetic factors
        f_T = _cardinal_temp_factor(T)
        f_M = _moisture_factor(m_frac)
        dS_dt = -k0 * f_T * f_M * current_aeration * S

        # Thermal capacity C_p (J/K)
        c_pile = total_dry * CP_DRY_J_PER_KG_K + W * CP_WATER_J_PER_KG_K

        # Heat generation (Watts converted to J/day)
        q_gen_j_per_day = (-dS_dt) * H_RXN_J_PER_KG_BVS

        # Heat loss to ambient (J/day)
        q_loss_j_per_day = ua_w_per_k * (T - ambient_temp_c) * SEC_PER_DAY

        # Evaporative moisture loss (kg/day)
        # Driven by saturated vapor pressure difference and biological temperature
        t_kelvin = T + 273.15
        p_sat = 610.78 * math.exp(17.27 * T / (T + 237.3))  # Pa
        p_amb = 610.78 * math.exp(17.27 * ambient_temp_c / (ambient_temp_c + 237.3)) * 0.60
        delta_p = max(0.0, p_sat - p_amb)
        evap_rate_kg_day = (delta_p / 101325.0) * (volume_m3 * 1.5) * current_aeration
        evap_rate_kg_day = min(evap_rate_kg_day, W * 0.05)  # cap at 5% pile water per day

        q_evap_j_per_day = evap_rate_kg_day * LAMBDA_VAP_J_PER_KG

        # Net temperature derivative dT/dt (°C/day)
        net_heat_j_per_day = q_gen_j_per_day - q_loss_j_per_day - q_evap_j_per_day
        dT_dt = net_heat_j_per_day / c_pile

        # Water derivative dW/dt (kg/day)
        dW_dt = Y_WATER_METABOLIC * (-dS_dt) - evap_rate_kg_day

        # CO2 generation derivative (approx 1.83 kg CO2 per kg BVS degraded based on C6H12O6 oxidation)
        dCO2_dt = 1.833 * (-dS_dt)

        # Pathogen thermal kill rate
        d_kill_dt = _pathogen_kill_rate(T) / math.log(10.0)

        return [dS_dt, dT_dt, dW_dt, dCO2_dt, d_kill_dt]

    t_eval = np.linspace(0.0, duration_days, int(duration_days * 4) + 1)
    sol = solve_ivp(
        ode_system,
        t_span=(0.0, duration_days),
        y0=y0,
        t_eval=t_eval,
        method="RK45",
        rtol=1e-5,
        atol=1e-6,
    )

    t_arr = sol.t
    s_arr = sol.y[0]
    t_arr_c = sol.y[1]
    w_arr = sol.y[2]
    co2_arr = sol.y[3]
    kill_arr = sol.y[4]

    # Calculate moisture percentages
    tot_wet = inert_dry_kg + s_arr + w_arr
    moist_arr_pct = (w_arr / tot_wet) * 100.0

    # US EPA 503 PFRP evaluation:
    # Requires continuous period of >= 3 days at >= 55°C
    above_55 = t_arr_c >= 55.0
    dt_step = duration_days / (len(t_arr) - 1)
    total_days_55 = float(np.sum(above_55) * dt_step)

    # Compute maximum consecutive days >= 55°C
    max_consecutive = 0.0
    current_consecutive = 0.0
    for is_above in above_55:
        if is_above:
            current_consecutive += dt_step
            if current_consecutive > max_consecutive:
                max_consecutive = current_consecutive
        else:
            current_consecutive = 0.0

    pfrp_ok = max_consecutive >= 3.0

    # Determine stabilization day (when temperature falls back to within 5°C of ambient)
    stabilization_day = int(duration_days)
    peak_idx = int(np.argmax(t_arr_c))
    for idx in range(peak_idx, len(t_arr)):
        if t_arr_c[idx] <= ambient_temp_c + 5.0 and t_arr[idx] > 10.0:
            stabilization_day = int(math.ceil(t_arr[idx]))
            break

    return SimulationResults(
        days=t_arr,
        temperature_c=t_arr_c,
        moisture_pct=moist_arr_pct,
        bvs_remaining_kg=s_arr,
        cumulative_co2_kg=co2_arr,
        pathogen_log_reduction=kill_arr,
        max_temperature_c=float(np.max(t_arr_c)),
        days_above_55c=total_days_55,
        consecutive_days_above_55c=max_consecutive,
        pfrp_compliant=pfrp_ok,
        stabilization_day=stabilization_day,
        metadata={
            "initial_wet_mass_kg": initial_wet_mass_kg,
            "ambient_temp_c": ambient_temp_c,
            "insulation_level": insulation_level,
            "turning_days": list(turning_schedule),
        },
    )


def build_digital_twin_figure(results: SimulationResults) -> go.Figure:
    """Generate interactive dual-axis Plotly figure of biophysical simulation trajectory.

    Displays:
      - Primary Y-axis: Temperature trajectory (°C) with EPA 55°C threshold zone.
      - Secondary Y-axis: Moisture percentage (%) and BVS degradation curve.
    """
    fig = go.Figure()

    # Temperature trace
    fig.add_trace(
        go.Scatter(
            x=results.days,
            y=results.temperature_c,
            mode="lines",
            name="Core Pile Temp (°C)",
            line={"color": "#e05638", "width": 3},
            hovertemplate="Day %{x:.1f}: %{y:.1f}°C<extra></extra>",
        )
    )

    # 55°C EPA PFRP horizontal threshold
    fig.add_hline(
        y=55.0,
        line_dash="dot",
        line_color="#c0392b",
        annotation_text="EPA 503 PFRP Inactivation Threshold (55°C)",
        annotation_position="top left",
    )

    # Moisture trace on secondary y-axis
    fig.add_trace(
        go.Scatter(
            x=results.days,
            y=results.moisture_pct,
            mode="lines",
            name="Moisture (%)",
            line={"color": "#2980b9", "width": 2, "dash": "dash"},
            yaxis="y2",
            hovertemplate="Day %{x:.1f}: %{y:.1f}%<extra></extra>",
        )
    )

    # Layout configuration
    status_text = "PFRP CERTIFIED" if results.pfrp_compliant else "PFRP BELOW THRESHOLD"
    status_color = "#27ae60" if results.pfrp_compliant else "#e67e22"

    fig.update_layout(
        title={
            "text": (
                f"<b>Biophysical Kinetic Digital Twin</b> | "
                f"<span style='color:{status_color}'>{status_text}</span> "
                f"(Max {results.max_temperature_c:.1f}°C, {results.consecutive_days_above_55c:.1f}d ≥55°C)"
            ),
            "x": 0.05,
        },
        xaxis={"title": "Composting Time (Days)", "gridcolor": "#ecf0f1"},
        yaxis={
            "title": "Temperature (°C)",
            "range": [15, max(75, float(results.max_temperature_c + 5))],
            "gridcolor": "#ecf0f1",
        },
        yaxis2={
            "title": "Moisture (%)",
            "overlaying": "y",
            "side": "right",
            "range": [20, 80],
            "showgrid": False,
        },
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        template="plotly_white",
        height=450,
        margin={"l": 50, "r": 50, "t": 60, "b": 50},
    )

    return fig
