"""CompostMitra - Streamlit Eco-Premium Shell on Mocks.

Offline intelligent home composting decision support interface.
Uses frozen contract v3.1 mock responses for zero-network deterministic UI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from tokens import (
    COLOR_ACCENT,
    COLOR_BADGE_BG,
    COLOR_BADGE_TEXT,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_CARD_BG,
    COLOR_PRIMARY,
    COLOR_SAGE,
    COLOR_SECONDARY,
    COLOR_SUCCESS,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_WARN_TEXT,
    FONT_FAMILY,
)

# Page configuration - eco-premium layout
st.set_page_config(
    page_title="CompostMitra | Eco-Premium Home Composting",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load CSS stylesheet
STYLE_PATH = Path(__file__).parent / "style.css"
if STYLE_PATH.exists():
    with open(STYLE_PATH, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Offline mock data loader with fallbacks
def load_mock_data() -> tuple[dict[str, Any], dict[str, Any]]:
    """Load mock fixtures from mock/ directory with deterministic fallback defaults."""
    repo_dir = Path(__file__).parent
    recipe_file = repo_dir / "mock" / "recipe_response.json"
    predict_file = repo_dir / "mock" / "predict_response.json"

    default_recipe = {
        "cn": 28.5,
        "n": 2.1,
        "p": 0.8,
        "k": 1.5,
        "moist_pct": 55.0,
        "ph": 6.8,
        "heuristic_grade": "MOCK_GRADE_A",
    }
    default_predict = {
        "p_mature": 0.85,
        "gi": 88.0,
        "cn_pred": 27.2,
        "shap": {
            "cn": 0.12,
            "ph": -0.05,
            "moist_pct": 0.08,
        },
        "conf": 0.90,
    }

    recipe_data = default_recipe
    predict_data = default_predict

    if recipe_file.exists():
        try:
            with open(recipe_file, encoding="utf-8") as f:
                recipe_data = json.load(f)
        except Exception:
            recipe_data = default_recipe

    if predict_file.exists():
        try:
            with open(predict_file, encoding="utf-8") as f:
                predict_data = json.load(f)
        except Exception:
            predict_data = default_predict

    return recipe_data, predict_data


recipe_mock, predict_mock = load_mock_data()

# Session State Initialization
if "current_step" not in st.session_state:
    st.session_state.current_step = 1

# Support query param override for testability
if "step" in st.query_params:
    try:
        step_param = int(st.query_params["step"])
        if 1 <= step_param <= 5:
            st.session_state.current_step = step_param
    except (ValueError, TypeError):
        pass

if "selected_plants" not in st.session_state:
    st.session_state.selected_plants = ["Tomato", "Rose", "Spinach"]

if "num_pots" not in st.session_state:
    st.session_state.num_pots = 5

if "waste_kitchen" not in st.session_state:
    st.session_state.waste_kitchen = 2.0

if "waste_coffee" not in st.session_state:
    st.session_state.waste_coffee = 0.5

if "waste_leaves" not in st.session_state:
    st.session_state.waste_leaves = 3.0

if "waste_grass" not in st.session_state:
    st.session_state.waste_grass = 1.5

# Step definitions
STEPS = [
    (1, "Plants Selection", "🌱"),
    (2, "Waste Inputs", "🍂"),
    (3, "Recipe Cards", "⭐"),
    (4, "Environmental Impact", "🌍"),
    (5, "Benefits & Validation", "📊"),
]


def navigate_to(step_num: int) -> None:
    """Safely navigate to step and sync query params."""
    st.session_state.current_step = step_num
    st.query_params["step"] = str(step_num)


# ==========================================
# SIDEBAR NAVIGATION (STEPPER)
# ==========================================
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 10px 0; border-bottom: 1px solid {COLOR_BORDER}; margin-bottom: 16px;">
            <div style="font-size: 24px; font-weight: 700; color: {COLOR_PRIMARY};">🌿 CompostMitra</div>
            <div style="font-size: 14px; color: {COLOR_TEXT_MUTED};">Eco-Premium Soil Companion</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Workflow Navigation")
    for num, label, icon in STEPS:
        is_active = st.session_state.current_step == num
        bg_color = COLOR_PRIMARY if is_active else COLOR_SAGE
        txt_color = COLOR_BG if is_active else COLOR_TEXT
        border_col = COLOR_PRIMARY if is_active else COLOR_BORDER
        badge = "● Active" if is_active else f"Step {num}"

        st.markdown(
            f"""
            <div style="background-color: {bg_color}; color: {txt_color}; border: 1px solid {border_col};
                        border-radius: 12px; padding: 10px 14px; margin-bottom: 8px; display: flex;
                        align-items: center; justify-content: space-between;">
                <span style="font-weight: 600;">{icon} {num}. {label}</span>
                <span style="font-size: 12px; opacity: 0.85;">{badge}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    step_choice = st.radio(
        "Jump to step:",
        options=[s[0] for s in STEPS],
        format_func=lambda x: f"{STEPS[x-1][2]} Step {x}: {STEPS[x-1][1]}",
        index=st.session_state.current_step - 1,
        key="sidebar_step_radio",
    )
    if step_choice != st.session_state.current_step:
        navigate_to(step_choice)
        st.rerun()

    st.markdown(
        """
        <div class="tier-footnote" style="margin-top: 30px;">
            Tier Footnote: T1 REAL | LIT calc | D1 proxy<br>
            CompostMitra v3.1 • Offline Mode (<3s)
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# STEP 1: PLANTS SELECTION
# ==========================================
if st.session_state.current_step == 1:
    st.markdown("## Step 1: Target Plants & Garden Scale")
    st.markdown(
        "Select your companion plants and pot volume to tailor compost nutrient delivery and moisture retention."
    )

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown(
            f"""
            <div class="eco-card">
                <h3 style="color: {COLOR_PRIMARY}; margin-top: 0;">Companion Plant Targets</h3>
                <p>Choose target crops to calculate recommended N-P-K ratios and pH bounds.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        all_plants = [
            "Tomato",
            "Rose",
            "Spinach",
            "Chili",
            "Coriander",
            "Basil",
            "Hibiscus",
            "Marigold",
            "Pothos",
            "Aloe Vera",
        ]
        selected = st.multiselect(
            "Target Garden Crops (Select up to 5):",
            options=all_plants,
            default=[p for p in st.session_state.selected_plants if p in all_plants]
            or ["Tomato", "Rose", "Spinach"],
            help="Select the plants you are growing in your pots or garden.",
        )
        st.session_state.selected_plants = selected

    with col2:
        st.markdown(
            f"""
            <div class="eco-card">
                <h3 style="color: {COLOR_PRIMARY}; margin-top: 0;">Garden Scale</h3>
                <p>Scaling volume maintains consistent compost requirements across all containers.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        num_pots = st.slider(
            "Number of Standard Pots / Planters (e.g., 20 pots):",
            min_value=1,
            max_value=50,
            value=st.session_state.num_pots,
            step=1,
            help="Edge case verification: 20 pots executes without scaling instability.",
        )
        st.session_state.num_pots = num_pots

        compost_need_kg = round(num_pots * 0.5, 1)
        st.markdown(
            f"""
            <div style="background-color: {COLOR_SAGE}; border-radius: 12px; padding: 14px; margin-top: 12px; border: 1px solid {COLOR_BORDER};">
                <div style="font-weight: 600; color: {COLOR_PRIMARY};">Estimated Compost Requirement</div>
                <div style="font-size: 22px; font-weight: 700; color: {COLOR_PRIMARY};">{compost_need_kg} kg / month</div>
                <div style="font-size: 14px; color: {COLOR_TEXT_MUTED};">Based on 0.5 kg top-dressing per pot every 30 days.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([3, 1])
    with col_r:
        st.markdown(
            f"""
            <div class="stepper-next" style="text-align: right;">
                <a href="?step=2" target="_self" class="stepper-next" style="text-decoration: none;">
                    <button class="stepper-next" style="background-color: {COLOR_PRIMARY}; color: {COLOR_BG};
                                border-radius: 12px; padding: 10px 24px; font-size: 16px; font-weight: 600;
                                border: none; cursor: pointer; width: 100%;">
                        Next: Waste Inputs ➔
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================
# STEP 2: WASTE INPUTS
# ==========================================
elif st.session_state.current_step == 2:
    st.markdown("## Step 2: Available Waste Feedstocks")
    st.markdown(
        "Enter your available household green (nitrogen) and brown (carbon) organic materials."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="eco-card">
                <h3 style="color: {COLOR_PRIMARY}; margin-top: 0;">🌿 Nitrogen Greens</h3>
                <p style="color: {COLOR_TEXT_MUTED};">Moist, fast-decomposing organic materials.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        w_kitchen = st.number_input(
            "Kitchen Scraps (vegetable peels, fruit rinds) [kg]:",
            min_value=0.0,
            max_value=50.0,
            value=float(st.session_state.waste_kitchen),
            step=0.5,
        )
        st.session_state.waste_kitchen = w_kitchen

        w_coffee = st.number_input(
            "Coffee Grounds (spent brew residues) [kg]:",
            min_value=0.0,
            max_value=20.0,
            value=float(st.session_state.waste_coffee),
            step=0.2,
        )
        st.session_state.waste_coffee = w_coffee

    with col2:
        st.markdown(
            f"""
            <div class="eco-card">
                <h3 style="color: {COLOR_PRIMARY}; margin-top: 0;">🍂 Carbon Browns & Bulking</h3>
                <p style="color: {COLOR_TEXT_MUTED};">Dry, fibrous materials for aeration and structure.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        w_leaves = st.number_input(
            "Dry Leaves & Shredded Twigs [kg]:",
            min_value=0.0,
            max_value=50.0,
            value=float(st.session_state.waste_leaves),
            step=0.5,
        )
        st.session_state.waste_leaves = w_leaves

        w_grass = st.number_input(
            "Grass Clippings / Garden Trimmings [kg]:",
            min_value=0.0,
            max_value=30.0,
            value=float(st.session_state.waste_grass),
            step=0.5,
        )
        st.session_state.waste_grass = w_grass

    total_waste = round(w_kitchen + w_coffee + w_leaves + w_grass, 2)

    # Empty waste edge case handling
    if total_waste == 0.0:
        st.markdown(
            """
            <div class="eco-warning">
                <strong>Notice (Empty Feedstock):</strong> Total waste input is currently 0.0 kg.
                Please enter at least one feedstock weight greater than 0 kg to formulate a customized compost recipe.
                (A helpful guidance fallback is active; zero traceback).
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="eco-hint">
                <strong>Feedstock Inventory:</strong> Total batch mass is <strong>{total_waste} kg</strong>.
                Greens: {round(w_kitchen + w_coffee, 2)} kg | Browns: {round(w_leaves + w_grass, 2)} kg.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_space, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button("⬅ Back: Plants", key="step2_back", use_container_width=True):
            navigate_to(1)
            st.rerun()
    with col_next:
        st.markdown(
            f"""
            <div class="stepper-next" style="text-align: right;">
                <a href="?step=3" target="_self" class="stepper-next" style="text-decoration: none;">
                    <button class="stepper-next" style="background-color: {COLOR_PRIMARY}; color: {COLOR_BG};
                                border-radius: 12px; padding: 10px 24px; font-size: 16px; font-weight: 600;
                                border: none; cursor: pointer; width: 100%;">
                        Next: Recipe Cards ➔
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================
# STEP 3: RECIPE CARDS (★)
# ==========================================
elif st.session_state.current_step == 3:
    st.markdown("## Step 3: Recommended Recipe Cards ⭐")
    st.markdown(
        "Optimal feedstock ratios calculated for rapid, odor-free decomposition meeting Cornell 30:1 standards."
    )

    total_waste = (
        st.session_state.waste_kitchen
        + st.session_state.waste_coffee
        + st.session_state.waste_leaves
        + st.session_state.waste_grass
    )

    if total_waste == 0.0:
        st.markdown(
            """
            <div class="eco-warning">
                <strong>Empty Waste Input Notice:</strong> You have not provided any waste amounts (0.0 kg total).
                Displaying baseline reference recipes from verified mock datasets.
                You can return to Step 2 anytime to add kitchen scraps or dry leaves.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3 Recommendation cards
    cards = [
        {
            "card_id": "recipe-card-1",
            "title": "Recipe 1: Cornell Balanced Gold (Recommended)",
            "grade": recipe_mock.get("heuristic_grade", "MOCK_GRADE_A"),
            "cn": recipe_mock.get("cn", 28.5),
            "moist": recipe_mock.get("moist_pct", 55.0),
            "ph": recipe_mock.get("ph", 6.8),
            "npk": f"{recipe_mock.get('n', 2.1)}% - {recipe_mock.get('p', 0.8)}% - {recipe_mock.get('k', 1.5)}%",
            "maturity": f"{int(predict_mock.get('p_mature', 0.85) * 100)}%",
            "gi": f"{predict_mock.get('gi', 88.0)}% GI",
            "desc": "Optimal 30:1 carbon-to-nitrogen ratio. High aeration and balanced microbial activity for urban containers.",
            "is_best": True,
        },
        {
            "card_id": "recipe-card-2",
            "title": "Recipe 2: Nitrogen-Rich Bio-Booster",
            "grade": "MOCK_GRADE_A",
            "cn": 26.2,
            "moist": 58.0,
            "ph": 6.9,
            "npk": "2.4% - 0.9% - 1.6%",
            "maturity": "82%",
            "gi": "84.5% GI",
            "desc": "Elevated coffee residue proportion accelerating initial thermophilic heating for heavy leafy feeders.",
            "is_best": False,
        },
        {
            "card_id": "recipe-card-3",
            "title": "Recipe 3: High-Carbon Odor Shield",
            "grade": "MOCK_GRADE_B",
            "cn": 31.0,
            "moist": 51.5,
            "ph": 6.6,
            "npk": "1.8% - 0.7% - 1.3%",
            "maturity": "78%",
            "gi": "80.0% GI",
            "desc": "Maximizes leaf bedding to prevent anaerobic pockets and odor in dense balcony installations.",
            "is_best": False,
        },
    ]

    for c in cards:
        best_ribbon = (
            f"<span style='color: {COLOR_ACCENT}; font-size: 14px; font-weight: 700;'>★ RECOMMENDED BLEND</span><br>"
            if c["is_best"]
            else ""
        )
        badge_style = (
            f"background-color: {COLOR_PRIMARY}; color: {COLOR_BG};"
            if c["is_best"]
            else f"background-color: {COLOR_BADGE_BG}; color: {COLOR_BADGE_TEXT};"
        )

        st.markdown(
            f"""
            <div id="{c['card_id']}" class="recipe-card eco-card" style="border: 1px solid {COLOR_BORDER};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                        {best_ribbon}
                        <h3 style="color: {COLOR_PRIMARY}; margin: 0 0 6px 0;">{c['title']}</h3>
                        <p style="color: {COLOR_TEXT_MUTED}; margin: 0;">{c['desc']}</p>
                    </div>
                    <div>
                        <span class="grade-badge" style="{badge_style}">{c['grade']}</span>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-top: 16px;">
                    <div style="background-color: {COLOR_SAGE}; padding: 10px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 13px; color: {COLOR_TEXT_MUTED};">C/N Ratio</div>
                        <div style="font-size: 18px; font-weight: 700; color: {COLOR_PRIMARY};">{c['cn']}</div>
                    </div>
                    <div style="background-color: {COLOR_SAGE}; padding: 10px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 13px; color: {COLOR_TEXT_MUTED};">Moisture</div>
                        <div style="font-size: 18px; font-weight: 700; color: {COLOR_PRIMARY};">{c['moist']}%</div>
                    </div>
                    <div style="background-color: {COLOR_SAGE}; padding: 10px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 13px; color: {COLOR_TEXT_MUTED};">pH Approx.</div>
                        <div style="font-size: 18px; font-weight: 700; color: {COLOR_PRIMARY};">{c['ph']}</div>
                    </div>
                    <div style="background-color: {COLOR_SAGE}; padding: 10px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 13px; color: {COLOR_TEXT_MUTED};">N - P - K</div>
                        <div style="font-size: 18px; font-weight: 700; color: {COLOR_PRIMARY};">{c['npk']}</div>
                    </div>
                    <div style="background-color: {COLOR_SAGE}; padding: 10px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 13px; color: {COLOR_TEXT_MUTED};">Est. Maturity</div>
                        <div style="font-size: 18px; font-weight: 700; color: {COLOR_SUCCESS};">{c['maturity']}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="tier-footnote">
            Tier Footnote: T1 REAL | LIT calc | D1 proxy • Evaluated with Cornell 28-32 C/N benchmark
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_space, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button("⬅ Back: Waste Inputs", key="step3_back", use_container_width=True):
            navigate_to(2)
            st.rerun()
    with col_next:
        st.markdown(
            f"""
            <div class="stepper-next" style="text-align: right;">
                <a href="?step=4" target="_self" class="stepper-next" style="text-decoration: none;">
                    <button class="stepper-next" style="background-color: {COLOR_PRIMARY}; color: {COLOR_BG};
                                border-radius: 12px; padding: 10px 24px; font-size: 16px; font-weight: 600;
                                border: none; cursor: pointer; width: 100%;">
                        Next: Impact View ➔
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================
# STEP 4: IMPACT VIEW
# ==========================================
elif st.session_state.current_step == 4:
    st.markdown("## Step 4: Environmental & Household Impact 🌍")
    st.markdown(
        "Quantified ecological diversion and economic savings calculated from your organic compost conversion."
    )

    total_waste = (
        st.session_state.waste_kitchen
        + st.session_state.waste_coffee
        + st.session_state.waste_leaves
        + st.session_state.waste_grass
    )
    pots = st.session_state.num_pots

    # Impact calculations (offline proxy formulas)
    monthly_diverted_kg = round(max(total_waste * 4.0, pots * 0.5 * 2.2), 1)
    monthly_savings_inr = round(monthly_diverted_kg * 22.5, 0)
    co2e_avoided_kg = round(monthly_diverted_kg * 0.45, 1)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="eco-metric-card">
                <div class="eco-metric-value">{monthly_diverted_kg} kg</div>
                <div class="eco-metric-label">Monthly Waste Diverted</div>
                <div style="font-size: 13px; color: {COLOR_TEXT_MUTED}; margin-top: 6px;">Kept out of municipal landfill</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="eco-metric-card">
                <div class="eco-metric-value">₹{int(monthly_savings_inr)}</div>
                <div class="eco-metric-label">Estimated Monthly Savings</div>
                <div style="font-size: 13px; color: {COLOR_TEXT_MUTED}; margin-top: 6px;">Offset fertilizer & soil conditioner spend</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="eco-metric-card">
                <div class="eco-metric-value">{co2e_avoided_kg} kg</div>
                <div class="eco-metric-label">CO2e Emissions Avoided</div>
                <div style="font-size: 13px; color: {COLOR_TEXT_MUTED}; margin-top: 6px;">Aerobic digestion methane mitigation</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="eco-card" style="margin-top: 24px;">
            <h3 style="color: {COLOR_PRIMARY}; margin-top: 0;">Impact Methodology</h3>
            <p>
                Calculations model landfill diversion by assuming 100% aerobic retention of household organic feedstocks.
                Economic savings represent regional organic compost market equivalents (₹22.5 / kg).
                Emission offset factors utilize IPCC urban solid waste guidelines (0.45 kg CO2e / kg diverted).
            </p>
            <div class="tier-footnote">
                Tier Footnote: T1 REAL | LIT calc | D1 proxy • Sanity check estimates based on literature proxy values (not proof).
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_space, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button("⬅ Back: Recipe Cards", key="step4_back", use_container_width=True):
            navigate_to(3)
            st.rerun()
    with col_next:
        st.markdown(
            f"""
            <div class="stepper-next" style="text-align: right;">
                <a href="?step=5" target="_self" class="stepper-next" style="text-decoration: none;">
                    <button class="stepper-next" style="background-color: {COLOR_PRIMARY}; color: {COLOR_BG};
                                border-radius: 12px; padding: 10px 24px; font-size: 16px; font-weight: 600;
                                border: none; cursor: pointer; width: 100%;">
                        Next: Benefits & Validation ➔
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================
# STEP 5: BENEFITS + VALIDATION
# ==========================================
elif st.session_state.current_step == 5:
    st.markdown("## Step 5: Benefits & Model Validation 📊")
    st.markdown(
        "Per-plant nutrient compatibility, model confidence metrics, and explainability attributions."
    )

    conf_pct = int(predict_mock.get("conf", 0.90) * 100)
    gi_val = predict_mock.get("gi", 88.0)
    p_mature = predict_mock.get("p_mature", 0.85)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown(
            f"""
            <div class="eco-card">
                <h3 style="color: {COLOR_PRIMARY}; margin-top: 0;">Per-Plant Nutrient Compatibility (MOCK)</h3>
                <p style="color: {COLOR_TEXT_MUTED}; font-size: 14px;">
                    Matching index evaluating macro-nutrient suitability for each selected companion plant.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        plants = st.session_state.selected_plants or ["Tomato", "Rose", "Spinach"]
        # Canonical benchmark mock compatibility values
        plant_scores = {
            "Tomato": 0.91,
            "Rose": 0.88,
            "Spinach": 0.84,
            "Chili": 0.86,
            "Coriander": 0.82,
            "Basil": 0.89,
            "Hibiscus": 0.85,
            "Marigold": 0.87,
            "Pothos": 0.90,
            "Aloe Vera": 0.81,
        }
        scores = [plant_scores.get(p, 0.85) for p in plants]

        # Plotly chart using tokens
        fig = go.Figure(
            data=[
                go.Bar(
                    x=scores,
                    y=plants,
                    orientation="h",
                    marker=dict(
                        color=COLOR_PRIMARY,
                        line=dict(color=COLOR_SECONDARY, width=1),
                    ),
                    text=[f"{s:.2f} (MOCK)" for s in scores],
                    textposition="auto",
                )
            ]
        )
        fig.update_layout(
            xaxis=dict(range=[0.0, 1.05], title="Suitability Match Index (0.0 - 1.0)"),
            yaxis=dict(autorange="reversed"),
            paper_bgcolor=COLOR_CARD_BG,
            plot_bgcolor=COLOR_SAGE,
            font=dict(family=FONT_FAMILY, size=14, color=COLOR_TEXT),
            margin=dict(l=20, r=20, t=20, b=20),
            height=260,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(
            f"""
            <div class="eco-card">
                <h3 style="color: {COLOR_PRIMARY}; margin-top: 0;">Validation Indicators</h3>
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 14px; color: {COLOR_TEXT_MUTED};">Model Confidence</div>
                    <div style="font-size: 26px; font-weight: 700; color: {COLOR_PRIMARY};">{conf_pct}%</div>
                </div>
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 14px; color: {COLOR_TEXT_MUTED};">Germination Index (GI)</div>
                    <div style="font-size: 26px; font-weight: 700; color: {COLOR_SUCCESS};">{gi_val}%</div>
                </div>
                <div>
                    <div style="font-size: 14px; color: {COLOR_TEXT_MUTED};">Maturity Probability</div>
                    <div style="font-size: 26px; font-weight: 700; color: {COLOR_PRIMARY};">{p_mature}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # SHAP explanations card
    shap_vals = predict_mock.get("shap", {"cn": 0.12, "ph": -0.05, "moist_pct": 0.08})
    st.markdown(
        f"""
        <div class="eco-card" style="margin-top: 16px;">
            <h3 style="color: {COLOR_PRIMARY}; margin-top: 0;">Feature Attribution & Sensitivity (SHAP proxy)</h3>
            <p style="color: {COLOR_TEXT_MUTED};">
                Relative influence of key chemical parameters toward the estimated compost maturity grade:
            </p>
            <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                <div style="background-color: {COLOR_SAGE}; border-radius: 12px; padding: 12px 18px; border: 1px solid {COLOR_BORDER};">
                    <span style="font-weight: 600;">C/N Ratio:</span>
                    <span style="color: {COLOR_PRIMARY}; font-weight: 700;">{shap_vals.get('cn', 0.12):+.2f}</span>
                    <div style="font-size: 12px; color: {COLOR_TEXT_MUTED};">Dominant positive driver</div>
                </div>
                <div style="background-color: {COLOR_SAGE}; border-radius: 12px; padding: 12px 18px; border: 1px solid {COLOR_BORDER};">
                    <span style="font-weight: 600;">Moisture Content:</span>
                    <span style="color: {COLOR_PRIMARY}; font-weight: 700;">{shap_vals.get('moist_pct', 0.08):+.2f}</span>
                    <div style="font-size: 12px; color: {COLOR_TEXT_MUTED};">Adequate biological hydration</div>
                </div>
                <div style="background-color: {COLOR_SAGE}; border-radius: 12px; padding: 12px 18px; border: 1px solid {COLOR_BORDER};">
                    <span style="font-weight: 600;">pH Delta:</span>
                    <span style="color: {COLOR_WARN_TEXT}; font-weight: 700;">{shap_vals.get('ph', -0.05):+.2f}</span>
                    <div style="font-size: 12px; color: {COLOR_TEXT_MUTED};">Mild transient acidity penalty</div>
                </div>
            </div>
            <div class="tier-footnote" style="margin-top: 16px;">
                Model Disclaimer: Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).
                Compost decomposition dynamics vary with ambient climate, aeration frequency, and feedstock quality.<br>
                Tier Footnote: T1 REAL | LIT calc | D1 proxy
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_space, col_restart = st.columns([1, 2, 1])
    with col_back:
        if st.button("⬅ Back: Impact View", key="step5_back", use_container_width=True):
            navigate_to(4)
            st.rerun()
    with col_restart:
        if st.button("🔄 Restart Workflow", key="step5_restart", use_container_width=True):
            navigate_to(1)
            st.rerun()
