import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from datetime import datetime, date, timedelta

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="South Indian Macro, Micro & Gym Studio",
    page_icon="🍛",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 12px 16px;
        border-radius: 12px;
    }
    .coach-box {
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 4px solid;
        background-color: #1e293b;
    }
    .coach-warn { border-left-color: #f59e0b; }
    .coach-info { border-left-color: #6366f1; }
    .coach-ok   { border-left-color: #10b981; }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "si_nutrition_gym_db.json"

MEAL_SLOTS = ["Breakfast", "Lunch", "Pre/Post Workout", "Evening Tiffin", "Dinner"]

# MET values for accurate gym expenditure calculation
GYM_PROTOCOLS = {
    "Upper Body Hypertrophy (Bench, Incline, Lat Pulldown, Rows, Delts, Arms)": 5.2,
    "Lower Body Heavy Split (Leg Press, Lunges, Extensions, Hamstring Curls, Calves)": 6.0,
    "Vigorous Compound Strength / Supersets": 6.5,
    "Moderate Accessory / Pump & Core Session": 4.2,
    "Conditioning / Hyrox / Cardio Circuit": 7.5,
    "Active Recovery / Mobility / Walking": 3.0
}

MICRO_RDI = {
    "iron": {"label": "Iron", "unit": "mg", "target": 17.0},
    "calcium": {"label": "Calcium", "unit": "mg", "target": 1000.0},
    "magnesium": {"label": "Magnesium", "unit": "mg", "target": 420.0},
    "potassium": {"label": "Potassium", "unit": "mg", "target": 3500.0},
    "zinc": {"label": "Zinc", "unit": "mg", "target": 12.0},
    "vitD": {"label": "Vitamin D", "unit": "mcg", "target": 15.0},
    "vitB12": {"label": "Vitamin B12", "unit": "mcg", "target": 2.4},
    "sodium": {"label": "Sodium", "unit": "mg", "target": 2300.0}
}

# -----------------------------------------------------------------------------
# 2. DEFAULT SOUTH INDIAN FOODS & MEAL PACK BUCKETS
# -----------------------------------------------------------------------------
DEFAULT_FOODS = [
    # Tiffin & Staples
    {"id": "dosa_plain", "name": "Kal Dosa / Home Dosa (Medium)", "unit": "1 dosa (75g)", "category": "Tiffin & Staples", "cal": 135, "pro": 3.6, "carb": 24.0, "fat": 2.8, "fib": 1.4, "iron": 0.9, "calcium": 18, "magnesium": 22, "potassium": 85, "zinc": 0.5, "vitD": 0.0, "vitB12": 0.0, "sodium": 160},
    {"id": "idli_std", "name": "Steamed Rice & Urad Idli", "unit": "2 idlis (110g)", "category": "Tiffin & Staples", "cal": 130, "pro": 4.4, "carb": 26.0, "fat": 0.6, "fib": 1.8, "iron": 0.8, "calcium": 20, "magnesium": 24, "potassium": 90, "zinc": 0.6, "vitD": 0.0, "vitB12": 0.0, "sodium": 150},
    {"id": "chapati_wheat", "name": "Whole Wheat Home Chapati", "unit": "1 chapati (45g)", "category": "Tiffin & Staples", "cal": 120, "pro": 4.0, "carb": 21.0, "fat": 2.2, "fib": 3.1, "iron": 1.5, "calcium": 16, "magnesium": 38, "potassium": 120, "zinc": 0.8, "vitD": 0.0, "vitB12": 0.0, "sodium": 90},
    {"id": "ponni_rice", "name": "Steamed Ponni Boiled Rice", "unit": "1 cup cooked (160g)", "category": "Tiffin & Staples", "cal": 195, "pro": 4.2, "carb": 43.0, "fat": 0.5, "fib": 1.2, "iron": 0.6, "calcium": 12, "magnesium": 20, "potassium": 60, "zinc": 0.7, "vitD": 0.0, "vitB12": 0.0, "sodium": 10},
    {"id": "oats_rolled", "name": "Rolled Oats (Dry Weight)", "unit": "60g dry", "category": "Tiffin & Staples", "cal": 230, "pro": 7.8, "carb": 40.0, "fat": 4.2, "fib": 6.0, "iron": 2.5, "calcium": 32, "magnesium": 85, "potassium": 210, "zinc": 1.8, "vitD": 0.0, "vitB12": 0.0, "sodium": 5},
    {"id": "sweet_potato", "name": "Boiled Sweet Potato (Sakkaraivalli Kizhangu)", "unit": "150g boiled", "category": "Tiffin & Staples", "cal": 135, "pro": 2.4, "carb": 31.0, "fat": 0.2, "fib": 4.5, "iron": 1.1, "calcium": 45, "magnesium": 38, "potassium": 510, "zinc": 0.4, "vitD": 0.0, "vitB12": 0.0, "sodium": 45},
    {"id": "pongal_ven", "name": "Ven Pongal (Moong Dal, Rice, Pepper & Ghee)", "unit": "1 cup (200g)", "category": "Tiffin & Staples", "cal": 280, "pro": 7.5, "carb": 41.0, "fat": 9.5, "fib": 2.8, "iron": 1.6, "calcium": 30, "magnesium": 42, "potassium": 190, "zinc": 0.9, "vitD": 0.1, "vitB12": 0.1, "sodium": 280},

    # Kuzhambu, Rasam & Sides
    {"id": "pepper_rasam", "name": "TN Pepper, Cumin & Garlic Rasam (No Commercial Powder)", "unit": "1 bowl (180ml)", "category": "Kuzhambu & Sides", "cal": 55, "pro": 1.8, "carb": 8.5, "fat": 1.6, "fib": 1.4, "iron": 1.4, "calcium": 28, "magnesium": 26, "potassium": 195, "zinc": 0.4, "vitD": 0.0, "vitB12": 0.0, "sodium": 310},
    {"id": "tiffin_sambar", "name": "Murungakkai / Mixed Veg Toor Dal Sambar", "unit": "1 bowl (180ml)", "category": "Kuzhambu & Sides", "cal": 135, "pro": 6.5, "carb": 19.0, "fat": 3.8, "fib": 4.2, "iron": 1.9, "calcium": 48, "magnesium": 44, "potassium": 320, "zinc": 0.8, "vitD": 0.0, "vitB12": 0.0, "sodium": 360},
    {"id": "coconut_chutney", "name": "Coconut & Pottukadalai Chutney", "unit": "2 tbsp (45g)", "category": "Kuzhambu & Sides", "cal": 95, "pro": 2.4, "carb": 5.5, "fat": 7.2, "fib": 2.0, "iron": 0.7, "calcium": 12, "magnesium": 18, "potassium": 115, "zinc": 0.4, "vitD": 0.0, "vitB12": 0.0, "sodium": 140},
    {"id": "tomato_chutney", "name": "Kara Onion-Tomato-Garlic Chutney", "unit": "2 tbsp (50g)", "category": "Kuzhambu & Sides", "cal": 65, "pro": 1.2, "carb": 7.0, "fat": 3.5, "fib": 1.5, "iron": 0.6, "calcium": 15, "magnesium": 14, "potassium": 140, "zinc": 0.2, "vitD": 0.0, "vitB12": 0.0, "sodium": 165},
    {"id": "keerai_kootu", "name": "Arai Keerai / Spinach Moong Dal Kootu", "unit": "1 katori (150g)", "category": "Kuzhambu & Sides", "cal": 140, "pro": 7.2, "carb": 17.0, "fat": 4.5, "fib": 4.8, "iron": 4.2, "calcium": 135, "magnesium": 78, "potassium": 420, "zinc": 0.9, "vitD": 0.0, "vitB12": 0.0, "sodium": 240},
    {"id": "beans_poriyal", "name": "Beans & Carrot Poriyal with Coconut", "unit": "1 katori (120g)", "category": "Kuzhambu & Sides", "cal": 90, "pro": 2.6, "carb": 11.0, "fat": 4.0, "fib": 3.8, "iron": 1.2, "calcium": 42, "magnesium": 28, "potassium": 230, "zinc": 0.4, "vitD": 0.0, "vitB12": 0.0, "sodium": 180},
    {"id": "curd_bowl", "name": "Thick Home-Set Curd / Thayir", "unit": "1 katori (150g)", "category": "Kuzhambu & Sides", "cal": 98, "pro": 5.8, "carb": 7.2, "fat": 5.0, "fib": 0.0, "iron": 0.2, "calcium": 185, "magnesium": 22, "potassium": 230, "zinc": 0.8, "vitD": 0.2, "vitB12": 0.7, "sodium": 65},

    # High Protein Anchors
    {"id": "soya_fry", "name": "Home Dry Soya Chunk Pepper Fry (50g dry wt)", "unit": "1 plate (50g dry)", "category": "High Protein", "cal": 215, "pro": 26.0, "carb": 16.5, "fat": 5.0, "fib": 6.5, "iron": 4.0, "calcium": 175, "magnesium": 110, "potassium": 620, "zinc": 2.2, "vitD": 0.0, "vitB12": 0.0, "sodium": 290},
    {"id": "whey_scoop", "name": "Whey Protein Concentrate (Unflavored / 1 Scoop)", "unit": "1 scoop (30g)", "category": "High Protein", "cal": 120, "pro": 24.0, "carb": 2.5, "fat": 1.5, "fib": 0.0, "iron": 0.4, "calcium": 130, "magnesium": 25, "potassium": 160, "zinc": 0.6, "vitD": 0.0, "vitB12": 0.5, "sodium": 55},
    {"id": "boiled_egg", "name": "Whole Boiled Egg", "unit": "1 large egg", "category": "High Protein", "cal": 72, "pro": 6.3, "carb": 0.6, "fat": 4.8, "fib": 0.0, "iron": 0.9, "calcium": 28, "magnesium": 6, "potassium": 69, "zinc": 0.6, "vitD": 1.1, "vitB12": 0.6, "sodium": 70},
    {"id": "egg_whites", "name": "Boiled Egg Whites", "unit": "3 whites", "category": "High Protein", "cal": 51, "pro": 10.8, "carb": 0.7, "fat": 0.2, "fib": 0.0, "iron": 0.1, "calcium": 7, "magnesium": 11, "potassium": 160, "zinc": 0.1, "vitD": 0.0, "vitB12": 0.1, "sodium": 165},
    {"id": "double_omelette", "name": "2-Egg South Indian Onion-Chilli Omelette", "unit": "1 omelette (2 eggs)", "category": "High Protein", "cal": 185, "pro": 13.0, "carb": 2.5, "fat": 13.8, "fib": 0.5, "iron": 1.9, "calcium": 62, "magnesium": 16, "potassium": 175, "zinc": 1.3, "vitD": 2.2, "vitB12": 1.2, "sodium": 240},
    {"id": "paneer_tawa", "name": "Paneer Bhurji / Tawa Paneer Masala (100g raw)", "unit": "1 serving (100g)", "category": "High Protein", "cal": 295, "pro": 18.5, "carb": 5.5, "fat": 22.0, "fib": 0.8, "iron": 0.8, "calcium": 460, "magnesium": 32, "potassium": 140, "zinc": 1.8, "vitD": 0.5, "vitB12": 0.8, "sodium": 260},
    {"id": "channa_sundal", "name": "Kondaikadalai (Black Channa) Sundal", "unit": "1 cup (140g)", "category": "High Protein", "cal": 210, "pro": 10.5, "carb": 32.0, "fat": 4.5, "fib": 8.2, "iron": 3.1, "calcium": 68, "magnesium": 65, "potassium": 380, "zinc": 1.5, "vitD": 0.0, "vitB12": 0.0, "sodium": 210},

    # Shakes, Dairy & Fruits
    {"id": "peanut_butter", "name": "Natural Unsweetened Creamy Peanut Butter", "unit": "1 tbsp (16g)", "category": "Shakes & Fruits", "cal": 96, "pro": 4.2, "carb": 3.0, "fat": 8.0, "fib": 1.2, "iron": 0.3, "calcium": 8, "magnesium": 28, "potassium": 110, "zinc": 0.5, "vitD": 0.0, "vitB12": 0.0, "sodium": 5},
    {"id": "toned_milk", "name": "Toned Milk (for Shake / Filter Coffee)", "unit": "250 ml", "category": "Shakes & Fruits", "cal": 150, "pro": 8.0, "carb": 12.0, "fat": 7.5, "fib": 0.0, "iron": 0.2, "calcium": 300, "magnesium": 28, "potassium": 350, "zinc": 1.0, "vitD": 1.2, "vitB12": 1.1, "sodium": 110},
    {"id": "banana_robusta", "name": "Medium Robusta / Poovan Banana", "unit": "1 banana (120g)", "category": "Shakes & Fruits", "cal": 105, "pro": 1.3, "carb": 27.0, "fat": 0.4, "fib": 3.1, "iron": 0.3, "calcium": 6, "magnesium": 32, "potassium": 422, "zinc": 0.2, "vitD": 0.0, "vitB12": 0.0, "sodium": 1},
    {"id": "cow_ghee", "name": "Pure Cow Ghee", "unit": "1 tsp (5g)", "category": "Shakes & Fruits", "cal": 45, "pro": 0.0, "carb": 0.0, "fat": 5.0, "fib": 0.0, "iron": 0.0, "calcium": 0, "magnesium": 0, "potassium": 0, "zinc": 0.0, "vitD": 0.2, "vitB12": 0.0, "sodium": 0}
]

DEFAULT_BUCKETS = [
    {
        "id": "bucket_oat_whey",
        "name": "🥤 Morning Oats, Whey, PB & Banana Shake",
        "defaultSlot": "Breakfast",
        "items": [
            {"foodId": "oats_rolled", "qty": 1.0},
            {"foodId": "whey_scoop", "qty": 1.0},
            {"foodId": "banana_robusta", "qty": 1.0},
            {"foodId": "peanut_butter", "qty": 1.0},
            {"foodId": "toned_milk", "qty": 1.0}
        ]
    },
    {
        "id": "bucket_dosa_egg",
        "name": "🥞 Tiffin Pack: 3 Dosas + Sambar + Chutney + 2 Boiled Eggs",
        "defaultSlot": "Breakfast",
        "items": [
            {"foodId": "dosa_plain", "qty": 3.0},
            {"foodId": "tiffin_sambar", "qty": 1.0},
            {"foodId": "coconut_chutney", "qty": 1.0},
            {"foodId": "boiled_egg", "qty": 2.0}
        ]
    },
    {
        "id": "bucket_lunch_soya",
        "name": "🍛 South Indian Power Lunch: Rice + Pepper Rasam + Dry Soya Fry + Curd",
        "defaultSlot": "Lunch",
        "items": [
            {"foodId": "ponni_rice", "qty": 1.25},
            {"foodId": "pepper_rasam", "qty": 1.0},
            {"foodId": "soya_fry", "qty": 1.0},
            {"foodId": "curd_bowl", "qty": 1.0}
        ]
    },
    {
        "id": "bucket_preworkout",
        "name": "🍠 Workout Fuel: Sweet Potato + 3 Boiled Eggs",
        "defaultSlot": "Pre/Post Workout",
        "items": [
            {"foodId": "sweet_potato", "qty": 1.0},
            {"foodId": "boiled_egg", "qty": 3.0}
        ]
    },
    {
        "id": "bucket_dinner_paneer",
        "name": "🫓 Dinner Pack: 3 Chapatis + Paneer Tawa Masala",
        "defaultSlot": "Dinner",
        "items": [
            {"foodId": "chapati_wheat", "qty": 3.0},
            {"foodId": "paneer_tawa", "qty": 1.0}
        ]
    }
]

# -----------------------------------------------------------------------------
# 3. PERSISTENCE & STATE INITIALIZATION
# -----------------------------------------------------------------------------
def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "profile": {
            "weight": 72.5,
            "goal_mode": "Body Recomposition (Maintain 72-73kg + Build Muscle)",
            "base_cal": 2200,
            "pro_target": 145,
            "carb_target": 255,
            "fat_target": 65,
            "fib_target": 35,
            "eatback_pct": 75  # % of gym calories burned added back to daily target
        },
        "foods": DEFAULT_FOODS,
        "buckets": DEFAULT_BUCKETS,
        "logs": {}
    }

def save_db():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.db, f, indent=2)

if "db" not in st.session_state:
    st.session_state.db = load_db()

def ensure_day_log(date_str):
    if date_str not in st.session_state.db["logs"]:
        st.session_state.db["logs"][date_str] = {
            "meals": {slot: [] for slot in MEAL_SLOTS},
            "gym": {
                "hours": 0.0,
                "protocol": list(GYM_PROTOCOLS.keys())[0],
                "custom_burn_override": 0
            },
            "supplements": {
                "creatine": False,
                "fish_oil": False,
                "magnesium": False
            },
            "water_liters": 0.0
        }

def get_food_map():
    return {f["id"]: f for f in st.session_state.db["foods"]}

# -----------------------------------------------------------------------------
# 4. CALCULATION ENGINE (MACROS, MICROS & GYM CALORIES BURNT)
# -----------------------------------------------------------------------------
def compute_gym_burn(day_log, weight_kg):
    gym = day_log.get("gym", {})
    hours = float(gym.get("hours", 0.0))
    protocol = gym.get("protocol", list(GYM_PROTOCOLS.keys())[0])
    override = int(gym.get("custom_burn_override", 0))
    if override > 0:
        return override
    met = GYM_PROTOCOLS.get(protocol, 5.2)
    # Standard Exercise Science Formula: Calories = MET * Weight(kg) * Duration(hours)
    return round(met * weight_kg * hours)

def compute_day_summary(date_str):
    ensure_day_log(date_str)
    day_log = st.session_state.db["logs"][date_str]
    food_map = get_food_map()
    profile = st.session_state.db["profile"]

    totals = {
        "cal": 0.0, "pro": 0.0, "carb": 0.0, "fat": 0.0, "fib": 0.0,
        "iron": 0.0, "calcium": 0.0, "magnesium": 0.0, "potassium": 0.0,
        "zinc": 0.0, "vitD": 0.0, "vitB12": 0.0, "sodium": 0.0,
        "meals_over_28g_pro": 0,
        "slot_breakdown": {}
    }

    for slot in MEAL_SLOTS:
        slot_cal, slot_pro, slot_carb, slot_fat = 0.0, 0.0, 0.0, 0.0
        for entry in day_log["meals"].get(slot, []):
            f = food_map.get(entry["foodId"])
            if not f:
                continue
            q = float(entry["qty"])
            slot_cal += f["cal"] * q
            slot_pro += f["pro"] * q
            slot_carb += f["carb"] * q
            slot_fat += f["fat"] * q

            totals["cal"] += f["cal"] * q
            totals["pro"] += f["pro"] * q
            totals["carb"] += f["carb"] * q
            totals["fat"] += f["fat"] * q
            totals["fib"] += f.get("fib", 0.0) * q

            for m_key in MICRO_RDI.keys():
                totals[m_key] += f.get(m_key, 0.0) * q

        if slot_pro >= 28.0:
            totals["meals_over_28g_pro"] += 1
        totals["slot_breakdown"][slot] = {
            "cal": slot_cal, "pro": slot_pro, "carb": slot_carb, "fat": slot_fat
        }

    # Supplements contribution
    supps = day_log.get("supplements", {})
    if supps.get("magnesium"):
        totals["magnesium"] += 250.0
    if supps.get("fish_oil"):
        totals["fat"] += 1.0
        totals["cal"] += 9.0
        totals["vitD"] += 5.0

    # Gym Expenditure & Dynamic Targets
    gym_burn = compute_gym_burn(day_log, profile["weight"])
    eatback_cals = round(gym_burn * (profile.get("eatback_pct", 75) / 100.0))
    dynamic_cal_target = profile["base_cal"] + eatback_cals
    # Extra gym burn is predominantly fueled by glycogen (carbohydrates)
    dynamic_carb_target = profile["carb_target"] + round((eatback_cals * 0.80) / 4.0)
    dynamic_pro_target = profile["pro_target"] + round((eatback_cals * 0.20) / 4.0)

    totals["gym_hours"] = float(day_log["gym"].get("hours", 0.0))
    totals["gym_burn"] = gym_burn
    totals["dynamic_cal_target"] = dynamic_cal_target
    totals["dynamic_carb_target"] = dynamic_carb_target
    totals["dynamic_pro_target"] = dynamic_pro_target
    totals["net_calories"] = totals["cal"] - gym_burn

    return totals

# -----------------------------------------------------------------------------
# 5. SIDEBAR: DATE PICKER, GYM HOURS TRACKER & PROFILE TARGETS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🍛 SI Nutrition Studio")
    st.caption("Macro, Micro, Meal Buckets & Gym Expenditure")

    selected_date = st.date_input("📅 Active Tracking Date", value=date.today())
    active_date_str = selected_date.strftime("%Y-%m-%d")
    ensure_day_log(active_date_str)
    current_day_log = st.session_state.db["logs"][active_date_str]

    st.divider()

    # --- MANUAL GYM HOURS & CALORIE BURN CALCULATOR ---
    st.subheader("🏋️‍♂️ Today's Gym & Burn Log")
    gym_hours = st.number_input(
        "Gym Duration (Hours)",
        min_value=0.0, max_value=5.0,
        value=float(current_day_log["gym"].get("hours", 0.0)),
        step=0.25,
        help="Enter 1.0 for 60 mins, 1.25 for 75 mins, 1.5 for 90 mins."
    )
    protocol_list = list(GYM_PROTOCOLS.keys())
    saved_protocol = current_day_log["gym"].get("protocol", protocol_list[0])
    prot_idx = protocol_list.index(saved_protocol) if saved_protocol in protocol_list else 0
    gym_protocol = st.selectbox("Training Split / Intensity", options=protocol_list, index=prot_idx)

    weight_now = st.session_state.db["profile"]["weight"]
    estimated_burn = round(GYM_PROTOCOLS[gym_protocol] * weight_now * gym_hours)
    st.info(f"🔥 **Estimated Gym Burn:** `{estimated_burn} kcal`  \n*(MET {GYM_PROTOCOLS[gym_protocol]} × {weight_now} kg × {gym_hours} hrs)*")

    if (gym_hours != current_day_log["gym"].get("hours") or
        gym_protocol != current_day_log["gym"].get("protocol")):
        current_day_log["gym"]["hours"] = gym_hours
        current_day_log["gym"]["protocol"] = gym_protocol
        save_db()

    st.divider()

    # --- DAILY SUPPLEMENT STACK & HYDRATION ---
    st.subheader("⚡ Daily Stack & Hydration")
    c_cre, c_fo, c_mag = st.columns(3)
    cre_val = c_cre.checkbox("Creatine 5g", value=current_day_log["supplements"].get("creatine", False))
    fo_val = c_fo.checkbox("Fish Oil", value=current_day_log["supplements"].get("fish_oil", False))
    mag_val = c_mag.checkbox("Magnesium", value=current_day_log["supplements"].get("magnesium", False))

    water_val = st.slider("💧 Water Intake (Liters)", 0.0, 5.0, float(current_day_log.get("water_liters", 0.0)), 0.25)

    if (cre_val != current_day_log["supplements"]["creatine"] or
        fo_val != current_day_log["supplements"]["fish_oil"] or
        mag_val != current_day_log["supplements"]["magnesium"] or
        water_val != current_day_log["water_liters"]):
        current_day_log["supplements"]["creatine"] = cre_val
        current_day_log["supplements"]["fish_oil"] = fo_val
        current_day_log["supplements"]["magnesium"] = mag_val
        current_day_log["water_liters"] = water_val
        save_db()

    st.divider()

    # --- BODY PROFILE & GOAL CONFIGURATOR ---
    with st.expander("⚙️ Body Weight & Base Targets"):
        prof = st.session_state.db["profile"]
        new_weight = st.number_input("Current Body Weight (kg)", 45.0, 130.0, float(prof["weight"]), 0.5)
        new_base_cal = st.number_input("Base Rest-Day Calories (kcal)", 1200, 4000, int(prof["base_cal"]), 50)
        new_pro = st.number_input("Base Protein Target (g)", 60, 260, int(prof["pro_target"]), 5)
        new_carb = st.number_input("Base Carbs Target (g)", 100, 500, int(prof["carb_target"]), 5)
        new_fat = st.number_input("Base Fats Target (g)", 35, 140, int(prof["fat_target"]), 5)
        new_eatback = st.slider("Gym Calorie Refuel %", 0, 100, int(prof.get("eatback_pct", 75)), 5,
                                help="Percentage of gym calories burned that gets added to today's calorie target.")
        if st.button("Save Targets", use_container_width=True):
            prof.update({
                "weight": new_weight,
                "base_cal": new_base_cal,
                "pro_target": new_pro,
                "carb_target": new_carb,
                "fat_target": new_fat,
                "eatback_pct": new_eatback
            })
            save_db()
            st.success("Targets updated!")
            st.rerun()

# -----------------------------------------------------------------------------
# 6. TOP KPI BANNER (DYNAMIC TARGETS + GYM EXPENDITURE)
# -----------------------------------------------------------------------------
day_summary = compute_day_summary(active_date_str)
prof = st.session_state.db["profile"]

m1, m2, m3, m4, m5 = st.columns(5)
cal_diff = round(day_summary["cal"] - day_summary["dynamic_cal_target"])
m1.metric(
    "Calories (vs Dynamic Target)",
    f"{round(day_summary['cal'])} / {day_summary['dynamic_cal_target']} kcal",
    f"{cal_diff:+d} kcal",
    delta_color="normal" if abs(cal_diff) <= 150 else "inverse"
)
m2.metric(
    "Protein Intake",
    f"{day_summary['pro']:.1f} / {day_summary['dynamic_pro_target']} g",
    f"{(day_summary['pro'] / prof['weight']):.2f} g/kg BW"
)
m3.metric(
    "Carbs & Dietary Fiber",
    f"{day_summary['carb']:.0f} / {day_summary['dynamic_carb_target']} g",
    f"Fiber: {day_summary['fib']:.1f} / {prof['fib_target']}g"
)
m4.metric(
    "Healthy Fats",
    f"{day_summary['fat']:.1f} / {prof['fat_target']} g",
    f"Leucine Meals (≥28g P): {day_summary['meals_over_28g_pro']}/4"
)
m5.metric(
    "Gym Burn & Net Intake",
    f"{day_summary['gym_burn']} kcal burnt",
    f"Net: {round(day_summary['net_calories'])} kcal ({day_summary['gym_hours']} hrs)"
)

# -----------------------------------------------------------------------------
# 7. MAIN APPLICATION TABS
# -----------------------------------------------------------------------------
tab_log, tab_trends, tab_buckets, tab_backup = st.tabs([
    "🍛 Daily Logger & Smart Coach",
    "📈 Weekly & Monthly Trends",
    "🍱 Meal Pack Bucket Builder & Foods",
    "💾 Database Backup / Demo Seeder"
])

# =============================================================================
# TAB 1: DAILY LOGGER, ONE-CLICK BUCKETS, MICROS & SMART COACH
# =============================================================================
with tab_log:
    col_left, col_right = st.columns([7, 5], gap="large")

    with col_left:
        st.subheader("1️⃣ One-Click Meal Pack Buckets")
        target_slot = st.radio(
            "Select Target Meal Slot:",
            options=MEAL_SLOTS,
            horizontal=True
        )

        food_map = get_food_map()
        for b in st.session_state.db["buckets"]:
            b_cal = sum(food_map[i["foodId"]]["cal"] * i["qty"] for i in b["items"] if i["foodId"] in food_map)
            b_pro = sum(food_map[i["foodId"]]["pro"] * i["qty"] for i in b["items"] if i["foodId"] in food_map)
            b_carb = sum(food_map[i["foodId"]]["carb"] * i["qty"] for i in b["items"] if i["foodId"] in food_map)
            b_fat = sum(food_map[i["foodId"]]["fat"] * i["qty"] for i in b["items"] if i["foodId"] in food_map)
            desc_items = " + ".join(
                f"{i['qty']:g}x {food_map[i['foodId']]['name'].split('(')[0].strip()}"
                for i in b["items"] if i["foodId"] in food_map
            )

            bc1, bc2 = st.columns([4, 1])
            with bc1:
                st.markdown(
                    f"**{b['name']}**  \n"
                    f"<span style='font-size:12px;color:#94a3b8;'>{desc_items}</span>  \n"
                    f"<span style='font-size:12px;color:#34d399;font-weight:600;'>{round(b_cal)} kcal</span> • "
                    f"<span style='font-size:12px;color:#818cf8;font-weight:600;'>{b_pro:.1f}g P</span> • "
                    f"<span style='font-size:12px;color:#fbbf24;'>{b_carb:.0f}g C</span> • "
                    f"<span style='font-size:12px;color:#fb7185;'>{b_fat:.1f}g F</span>",
                    unsafe_allow_html=True
                )
            with bc2:
                if st.button("➕ Log Pack", key=f"log_b_{b['id']}", use_container_width=True):
                    slot_items = current_day_log["meals"][target_slot]
                    for item in b["items"]:
                        existing = next((x for x in slot_items if x["foodId"] == item["foodId"]), None)
                        if existing:
                            existing["qty"] = round(existing["qty"] + item["qty"], 2)
                        else:
                            slot_items.append({"foodId": item["foodId"], "qty": float(item["qty"])})
                    save_db()
                    st.rerun()
            st.markdown("<hr style='margin:6px 0;border-color:#1e293b;'>", unsafe_allow_html=True)

        # --- SINGLE SOUTH INDIAN FOOD QUICK-ADD ---
        st.subheader("2️⃣ Add Individual South Indian Food")
        f_col1, f_col2, f_col3 = st.columns([3, 1, 1])
        food_options = {f"{f['name']} ({f['unit']} — {f['cal']} kcal, {f['pro']}g P)": f["id"] for f in st.session_state.db["foods"]}
        chosen_label = f_col1.selectbox("Search / Choose Food", options=list(food_options.keys()))
        chosen_qty = f_col2.number_input("Portion Multiplier", 0.25, 10.0, 1.0, 0.25)
        if f_col3.button("➕ Add Item", use_container_width=True):
            f_id = food_options[chosen_label]
            slot_items = current_day_log["meals"][target_slot]
            existing = next((x for x in slot_items if x["foodId"] == f_id), None)
            if existing:
                existing["qty"] = round(existing["qty"] + chosen_qty, 2)
            else:
                slot_items.append({"foodId": f_id, "qty": float(chosen_qty)})
            save_db()
            st.rerun()

        # --- LOGGED MEALS BREAKDOWN ---
        st.subheader(f"3️⃣ Logged Meals for {active_date_str}")
        for slot in MEAL_SLOTS:
            s_items = current_day_log["meals"].get(slot, [])
            s_meta = day_summary["slot_breakdown"][slot]
            badge = " ✅ ≥28g Protein Threshold" if s_meta["pro"] >= 28 else ""
            with st.expander(
                f"{slot} — {round(s_meta['cal'])} kcal | {s_meta['pro']:.1f}g P | {s_meta['carb']:.0f}g C | {s_meta['fat']:.1f}g F {badge}",
                expanded=(len(s_items) > 0)
            ):
                if not s_items:
                    st.caption("No items logged in this slot yet.")
                else:
                    for idx, entry in enumerate(s_items):
                        f_obj = food_map.get(entry["foodId"])
                        if not f_obj:
                            continue
                        q = entry["qty"]
                        r1, r2, r3 = st.columns([4, 2, 1])
                        r1.write(f"**{f_obj['name']}** (`{q}x` {f_obj['unit']})")
                        r2.write(f"`{round(f_obj['cal']*q)} kcal` • **{f_obj['pro']*q:.1f}g P**")
                        if r3.button("🗑️", key=f"del_{slot}_{idx}"):
                            current_day_log["meals"][slot].pop(idx)
                            save_db()
                            st.rerun()

    # --- RIGHT COLUMN: SMART COACH EVALUATOR & MICRONUTRIENT RDI ---
    with col_right:
        st.subheader("🧠 Smart Goal & Recomposition Coach")

        pro_gap = round(day_summary["dynamic_pro_target"] - day_summary["pro"], 1)
        cal_gap = round(day_summary["dynamic_cal_target"] - day_summary["cal"])
        fib_gap = round(prof["fib_target"] - day_summary["fib"], 1)

        # 1. Gym vs Nutrition Synchronization Alert
        if day_summary["gym_hours"] > 0:
            st.markdown(
                f"<div class='coach-box coach-ok'>"
                f"<b>🏋️‍♂️ Training Day Refuel Active ({day_summary['gym_hours']} hrs logged)</b><br>"
                f"<span style='font-size:13px;'>You burnt <b>{day_summary['gym_burn']} kcal</b> in the gym today. "
                f"Your calorie target automatically scaled up to <b>{day_summary['dynamic_cal_target']} kcal</b> "
                f"and carbs to <b>{day_summary['dynamic_carb_target']}g</b> to prevent muscle catabolism while staying lean.</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='coach-box coach-info'>"
                f"<b>🧘‍♂️ Rest / Recovery Day Baseline</b><br>"
                f"<span style='font-size:13px;'>0 gym hours logged today. Keeping calories tight at your "
                f"<b>{prof['base_cal']} kcal</b> baseline while maintaining <b>{prof['pro_target']}g protein</b> for muscle repair.</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        # 2. Protein Gap Prescription
        if pro_gap > 40:
            st.markdown(
                f"<div class='coach-box coach-warn'>"
                f"<b>⚠️ High Protein Deficit: {pro_gap}g remaining</b><br>"
                f"<span style='font-size:13px;'>To build lean muscle at {prof['weight']} kg without adding fat, "
                f"prioritize lean protein anchors before adding more rice/dosa: "
                f"<b>Dry Soya Chunk Fry (+26g P)</b>, <b>1 Scoop Whey (+24g P)</b>, or <b>3 Boiled Eggs (+19g P)</b>.</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        elif pro_gap > 10:
            st.markdown(
                f"<div class='coach-box coach-info'>"
                f"<b>🎯 Close to Protein Target ({pro_gap}g left)</b><br>"
                f"<span style='font-size:13px;'>Bridge this final gap easily with <b>2 Boiled Eggs (+12.6g P)</b>, "
                f"<b>3 Egg Whites (+10.8g P)</b>, or <b>1 bowl Thick Curd (+5.8g P) + Kondaikadalai Sundal (+10.5g P)</b>.</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='coach-box coach-ok'>"
                f"<b>✅ Daily Protein Goal Achieved! ({day_summary['pro']:.1f}g)</b><br>"
                f"<span style='font-size:13px;'>You are at <b>{(day_summary['pro']/prof['weight']):.2f} g/kg</b> body weight across "
                f"<b>{day_summary['meals_over_28g_pro']} leucine-trigger meals</b>. Hypertrophy recovery is locked in.</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        # 3. South Indian Carb-to-Protein Skew Warning
        total_macro_cals = (day_summary["pro"] * 4) + (day_summary["carb"] * 4) + (day_summary["fat"] * 9)
        carb_pct = ((day_summary["carb"] * 4) / total_macro_cals * 100) if total_macro_cals > 0 else 0
        if day_summary["cal"] > 700 and carb_pct > 62:
            st.markdown(
                f"<div class='coach-box coach-warn'>"
                f"<b>⚖️ Carbohydrate Skew Alert ({carb_pct:.0f}% of calories from Carbs)</b><br>"
                f"<span style='font-size:13px;'>South Indian staples can push carbs high early. Swap 1 Dosa or 0.5 cup Ponni Rice "
                f"for <b>Keerai Kootu</b>, <b>Paneer</b>, or <b>Boiled Egg Whites</b> in your next meal.</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        # 4. Micronutrient & Fiber Check
        if day_summary["iron"] < 11.0 or fib_gap > 12:
            st.markdown(
                f"<div class='coach-box coach-info'>"
                f"<b>🔬 Micronutrient & Fiber Optimizer</b><br>"
                f"<span style='font-size:13px;'>Iron is at <b>{day_summary['iron']:.1f}/17mg</b> and Fiber has <b>{max(0.0, fib_gap):.1f}g</b> left. "
                f"Adding <b>Pepper-Cumin-Garlic Rasam</b> alongside <b>Arai Keerai Kootu</b> or <b>Soya Chunk Fry</b> boosts non-heme iron absorption via black pepper piperine.</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.divider()

        # --- MICRONUTRIENT RDI PROGRESS BARS ---
        st.subheader("🔬 Daily Micronutrient RDI Tracker")
        for m_key, meta in MICRO_RDI.items():
            val = day_summary[m_key]
            pct = min(1.0, val / meta["target"])
            st.progress(
                pct,
                text=f"**{meta['label']}**: {val:.1f} / {meta['target']:g} {meta['unit']} ({round(pct*100)}%)"
            )

# =============================================================================
# TAB 2: WEEKLY (7-DAY) & MONTHLY (30-DAY) TRENDS + GYM EXPENDITURE ANALYTICS
# =============================================================================
with tab_trends:
    st.subheader("📊 Weekly (7-Day) & Monthly (30-Day) Performance Analytics")

    horizon = st.radio(
        "Select Analysis Window:",
        options=["Last 7 Days (Weekly View)", "Last 30 Days (Monthly View)"],
        horizontal=True
    )
    num_days = 7 if "7" in horizon else 30

    # Build historical dataframe ending on selected_date
    records = []
    for d_offset in range(num_days - 1, -1, -1):
        d_obj = selected_date - timedelta(days=d_offset)
        d_str = d_obj.strftime("%Y-%m-%d")
        s = compute_day_summary(d_str)
        records.append({
            "Date": d_str,
            "DisplayDate": d_obj.strftime("%d %b"),
            "Calories Consumed": round(s["cal"]),
            "Dynamic Calorie Target": s["dynamic_cal_target"],
            "Net Calories (Food - Gym)": round(s["net_calories"]),
            "Gym Hours": s["gym_hours"],
            "Gym Calories Burnt": s["gym_burn"],
            "Protein (g)": round(s["pro"], 1),
            "Protein Target (g)": s["dynamic_pro_target"],
            "Carbs (g)": round(s["carb"], 1),
            "Fats (g)": round(s["fat"], 1),
            "Fiber (g)": round(s["fib"], 1)
        })

    df_trend = pd.DataFrame(records)
    active_days_df = df_trend[df_trend["Calories Consumed"] > 0]

    # Summary KPI Row for the Period
    k1, k2, k3, k4 = st.columns(4)
    avg_cal = round(active_days_df["Calories Consumed"].mean()) if not active_days_df.empty else 0
    avg_pro = round(active_days_df["Protein (g)"].mean(), 1) if not active_days_df.empty else 0.0
    total_gym_hrs = round(df_trend["Gym Hours"].sum(), 2)
    total_gym_burn = int(df_trend["Gym Calories Burnt"].sum())

    k1.metric(f"Avg Daily Intake ({num_days}d)", f"{avg_cal} kcal", f"{len(active_days_df)}/{num_days} days logged")
    k2.metric(f"Avg Daily Protein ({num_days}d)", f"{avg_pro} g", f"{(avg_pro/prof['weight']):.2f} g/kg avg")
    k3.metric(f"Total Gym Volume ({num_days}d)", f"{total_gym_hrs} Hours", f"{int((df_trend['Gym Hours'] > 0).sum())} sessions completed")
    k4.metric(f"Total Gym Calories Burnt", f"{total_gym_burn:,} kcal", f"~{round(total_gym_burn/7700, 2)} kg fat eq. expenditure")

    # Chart 1: Calories Consumed vs Dynamic Target vs Gym Calories Burnt
    c_chart1, c_chart2 = st.columns(2)

    with c_chart1:
        fig_cal = go.Figure()
        fig_cal.add_trace(go.Bar(
            x=df_trend["DisplayDate"],
            y=df_trend["Calories Consumed"],
            name="Calories Consumed",
            marker_color="#10b981"
        ))
        fig_cal.add_trace(go.Bar(
            x=df_trend["DisplayDate"],
            y=df_trend["Gym Calories Burnt"],
            name="Gym Calories Burnt",
            marker_color="#f43f5e"
        ))
        fig_cal.add_trace(go.Scatter(
            x=df_trend["DisplayDate"],
            y=df_trend["Dynamic Calorie Target"],
            name="Dynamic Target (Base + Gym Refuel)",
            mode="lines+markers",
            line=dict(color="#38bdf8", width=2.5, dash="dot")
        ))
        fig_cal.update_layout(
            title="Calories Consumed vs. Dynamic Target & Gym Burn",
            barmode="group",
            template="plotly_dark",
            height=380,
            legend=dict(orientation="h", y=1.12)
        )
        st.plotly_chart(fig_cal, use_container_width=True)

    with c_chart2:
        fig_pro = go.Figure()
        fig_pro.add_trace(go.Bar(
            x=df_trend["DisplayDate"],
            y=df_trend["Protein (g)"],
            name="Protein Logged (g)",
            marker_color="#818cf8"
        ))
        fig_pro.add_trace(go.Scatter(
            x=df_trend["DisplayDate"],
            y=df_trend["Protein Target (g)"],
            name="Protein Target (g)",
            mode="lines",
            line=dict(color="#f59e0b", width=2.5, dash="dash")
        ))
        fig_pro.update_layout(
            title="Daily Protein Consistency vs. Hypertrophy Target",
            template="plotly_dark",
            height=380,
            legend=dict(orientation="h", y=1.12)
        )
        st.plotly_chart(fig_pro, use_container_width=True)

    # Chart 3: Gym Hours & Macro Composition Trend
    fig_gym = go.Figure()
    fig_gym.add_trace(go.Bar(
        x=df_trend["DisplayDate"],
        y=df_trend["Gym Hours"],
        name="Gym Duration (Hours)",
        marker_color="#f59e0b",
        yaxis="y1"
    ))
    fig_gym.add_trace(go.Scatter(
        x=df_trend["DisplayDate"],
        y=df_trend["Net Calories (Food - Gym)"],
        name="Net Calorie Balance (kcal)",
        mode="lines+markers",
        line=dict(color="#2dd4bf", width=2.5),
        yaxis="y2"
    ))
    fig_gym.update_layout(
        title="Gym Training Hours vs. Net Calorie Balance",
        template="plotly_dark",
        height=340,
        yaxis=dict(title="Gym Hours"),
        yaxis2=dict(title="Net Calories (kcal)", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.15)
    )
    st.plotly_chart(fig_gym, use_container_width=True)

    with st.expander("📋 View Raw Tabular History"):
        st.dataframe(df_trend.drop(columns=["DisplayDate"]), use_container_width=True)

# =============================================================================
# TAB 3: CUSTOM MEAL PACK BUCKET BUILDER & SOUTH INDIAN FOOD CREATOR
# =============================================================================
with tab_buckets:
    b_col1, b_col2 = st.columns(2, gap="large")

    with b_col1:
        st.subheader("🍱 Create New Meal Pack Bucket")
        st.caption("Combine multiple South Indian foods into a 1-click meal pack.")

        if "draft_bucket" not in st.session_state:
            st.session_state.draft_bucket = []

        new_b_name = st.text_input("Bucket Name", placeholder="e.g., Post-Workout Oats + 4 Egg Whites Pack")
        new_b_slot = st.selectbox("Default Slot", options=MEAL_SLOTS)

        food_options_b = {f"{f['name']} ({f['unit']})": f["id"] for f in st.session_state.db["foods"]}
        sel_b_food = st.selectbox("Pick Food to Add to Bucket", options=list(food_options_b.keys()))
        sel_b_qty = st.number_input("Quantity Multiplier", 0.25, 10.0, 1.0, 0.25, key="b_qty_in")

        if st.button("➕ Add Food to Draft Bucket"):
            fid = food_options_b[sel_b_food]
            st.session_state.draft_bucket.append({"foodId": fid, "qty": float(sel_b_qty)})

        if st.session_state.draft_bucket:
            st.markdown("**Current Items in Draft Bucket:**")
            food_map = get_food_map()
            tot_c, tot_p = 0, 0
            for i, d_item in enumerate(st.session_state.draft_bucket):
                f = food_map[d_item["foodId"]]
                tot_c += f["cal"] * d_item["qty"]
                tot_p += f["pro"] * d_item["qty"]
                st.write(f"- `{d_item['qty']}x` {f['name']} ({round(f['cal']*d_item['qty'])} kcal, {f['pro']*d_item['qty']:.1f}g P)")
            st.info(f"**Bucket Total:** {round(tot_c)} kcal | {tot_p:.1f}g Protein")

            c_save, c_clear = st.columns(2)
            if c_save.button("✅ Save Meal Pack Bucket", use_container_width=True):
                if new_b_name.strip():
                    st.session_state.db["buckets"].append({
                        "id": f"bucket_{int(datetime.now().timestamp())}",
                        "name": f"🍱 {new_b_name.strip()}",
                        "defaultSlot": new_b_slot,
                        "items": list(st.session_state.draft_bucket)
                    })
                    st.session_state.draft_bucket = []
                    save_db()
                    st.success("Custom Meal Pack Bucket Saved!")
                    st.rerun()
            if c_clear.button("Clear Draft", use_container_width=True):
                st.session_state.draft_bucket = []
                st.rerun()

    with b_col2:
        st.subheader("🥘 Add Custom South Indian Food to Database")
        with st.form("custom_food_form"):
            cf_name = st.text_input("Food / Dish Name", placeholder="e.g., Sundakkai Vathal Kuzhambu")
            cf_unit = st.text_input("Serving Size Description", placeholder="e.g., 1 katori (150g)")
            cf_cat = st.selectbox("Category", ["Tiffin & Staples", "Kuzhambu & Sides", "High Protein", "Shakes & Fruits"])
            fc1, fc2, fc3, fc4 = st.columns(4)
            cf_cal = fc1.number_input("Calories", 0, 1500, 140)
            cf_pro = fc2.number_input("Protein (g)", 0.0, 100.0, 5.0, 0.5)
            cf_carb = fc3.number_input("Carbs (g)", 0.0, 150.0, 18.0, 0.5)
            cf_fat = fc4.number_input("Fat (g)", 0.0, 100.0, 4.5, 0.5)

            mc1, mc2, mc3, mc4 = st.columns(4)
            cf_fib = mc1.number_input("Fiber (g)", 0.0, 40.0, 3.0, 0.5)
            cf_iron = mc2.number_input("Iron (mg)", 0.0, 30.0, 1.5, 0.1)
            cf_calc = mc3.number_input("Calcium (mg)", 0, 1000, 45)
            cf_mag = mc4.number_input("Magnesium (mg)", 0, 500, 35)

            if st.form_submit_button("💾 Save Custom Food to Database", use_container_width=True):
                if cf_name.strip():
                    st.session_state.db["foods"].insert(0, {
                        "id": f"custom_{int(datetime.now().timestamp())}",
                        "name": cf_name.strip(),
                        "unit": cf_unit.strip() or "1 serving",
                        "category": cf_cat,
                        "cal": cf_cal, "pro": cf_pro, "carb": cf_carb, "fat": cf_fat, "fib": cf_fib,
                        "iron": cf_iron, "calcium": cf_calc, "magnesium": cf_mag,
                        "potassium": 180, "zinc": 0.6, "vitD": 0.0, "vitB12": 0.0, "sodium": 180
                    })
                    save_db()
                    st.success(f"Added {cf_name}!")
                    st.rerun()

# =============================================================================
# TAB 4: DATABASE BACKUP / RESTORE & 30-DAY DEMO SEEDER
# =============================================================================
with tab_backup:
    st.subheader("💾 Backup, Restore & 30-Day Trend Simulator")
    b1, b2 = st.columns(2)

    with b1:
        st.markdown("#### Export / Import JSON Database")
        st.caption("Use this if hosting on Streamlit Cloud to keep a permanent backup of your logs.")
        json_str = json.dumps(st.session_state.db, indent=2)
        st.download_button(
            "⬇️ Download Full Database Backup (.json)",
            data=json_str,
            file_name=f"si_nutrition_backup_{date.today()}.json",
            mime="application/json",
            use_container_width=True
        )
        uploaded = st.file_uploader("⬆️ Restore from JSON Backup", type=["json"])
        if uploaded is not None:
            if st.button("Restore Uploaded Backup"):
                st.session_state.db = json.load(uploaded)
                save_db()
                st.success("Database restored!")
                st.rerun()

    with b2:
        st.markdown("#### 🧪 Populate 30 Days of Sample South Indian + Gym Data")
        st.caption("Want to immediately inspect how the 7-Day and 30-Day charts look with realistic Upper/Lower gym sessions and South Indian meal buckets? Click below:")
        if st.button("🚀 Generate 30-Day Sample History", use_container_width=True):
            import random
            for offset in range(1, 30):
                d_str = (date.today() - timedelta(days=offset)).strftime("%Y-%m-%d")
                is_gym_day = (offset % 7) in [1, 2, 4, 5]  # 4-day weekly Upper/Lower split
                st.session_state.db["logs"][d_str] = {
                    "meals": {
                        "Breakfast": [{"foodId": "oats_rolled", "qty": 1.0}, {"foodId": "whey_scoop", "qty": 1.0}, {"foodId": "banana_robusta", "qty": 1.0}, {"foodId": "toned_milk", "qty": 1.0}],
                        "Lunch": [{"foodId": "ponni_rice", "qty": 1.25}, {"foodId": "pepper_rasam", "qty": 1.0}, {"foodId": "soya_fry", "qty": 1.0}, {"foodId": "curd_bowl", "qty": 1.0}],
                        "Pre/Post Workout": [{"foodId": "sweet_potato", "qty": 1.0}, {"foodId": "boiled_egg", "qty": 3.0 if is_gym_day else 2.0}],
                        "Evening Tiffin": [{"foodId": "dosa_plain", "qty": 2.0}, {"foodId": "tiffin_sambar", "qty": 1.0}],
                        "Dinner": [{"foodId": "chapati_wheat", "qty": 3.0}, {"foodId": "paneer_tawa", "qty": 1.0}]
                    },
                    "gym": {
                        "hours": random.choice([1.25, 1.5]) if is_gym_day else 0.0,
                        "protocol": list(GYM_PROTOCOLS.keys())[0 if offset % 2 == 0 else 1],
                        "custom_burn_override": 0
                    },
                    "supplements": {"creatine": True, "fish_oil": True, "magnesium": True},
                    "water_liters": 3.5
                }
            save_db()
            st.success("Populated 30 days of realistic Upper/Lower gym & South Indian meal history! Check the 'Weekly & Monthly Trends' tab.")
            st.rerun()