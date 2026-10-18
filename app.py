import streamlit as st
import pandas as pd
import json
import os
import urllib.request
import urllib.parse
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
    .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 12px 14px;
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

DATA_FILE = "si_nutrition_gym_db_v2.json"
MEAL_SLOTS = ["Breakfast", "Lunch", "Pre/Post Workout", "Evening Tiffin", "Dinner"]

GYM_PROTOCOLS = {
    "Upper Body Hypertrophy (Bench, Incline, Lat Pulldown, Rows, Delts, Arms)": 5.2,
    "Lower Body Heavy Split (Leg Press, Lunges, Extensions, Curls, Calves)": 6.0,
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
# 2. DEFAULT DROPDOWN FOODS & EXTENDED AUTO-FETCH KNOWLEDGE BASE
# -----------------------------------------------------------------------------
DEFAULT_FOODS = [
    {"id": "boiled_egg", "name": "Boiled Egg (Whole Large)", "unit": "1 egg (50g)", "category": "High Protein", "cal": 72, "pro": 6.3, "carb": 0.6, "fat": 4.8, "fib": 0.0, "iron": 0.9, "calcium": 28, "magnesium": 6, "potassium": 69, "zinc": 0.6, "vitD": 1.1, "vitB12": 0.6, "sodium": 70},
    {"id": "egg_whites", "name": "Boiled Egg Whites", "unit": "3 egg whites", "category": "High Protein", "cal": 51, "pro": 10.8, "carb": 0.7, "fat": 0.2, "fib": 0.0, "iron": 0.1, "calcium": 7, "magnesium": 11, "potassium": 160, "zinc": 0.1, "vitD": 0.0, "vitB12": 0.1, "sodium": 165},
    {"id": "double_omelette", "name": "2-Egg South Indian Onion-Chilli Omelette", "unit": "1 omelette (2 eggs)", "category": "High Protein", "cal": 185, "pro": 13.0, "carb": 2.5, "fat": 13.8, "fib": 0.5, "iron": 1.9, "calcium": 62, "magnesium": 16, "potassium": 175, "zinc": 1.3, "vitD": 2.2, "vitB12": 1.2, "sodium": 240},
    {"id": "soya_fry", "name": "Home Dry Soya Chunk Pepper Fry (50g dry wt)", "unit": "1 plate (50g dry)", "category": "High Protein", "cal": 215, "pro": 26.0, "carb": 16.5, "fat": 5.0, "fib": 6.5, "iron": 4.0, "calcium": 175, "magnesium": 110, "potassium": 620, "zinc": 2.2, "vitD": 0.0, "vitB12": 0.0, "sodium": 290},
    {"id": "whey_scoop", "name": "Whey Protein Concentrate (1 Scoop)", "unit": "1 scoop (30g)", "category": "High Protein", "cal": 120, "pro": 24.0, "carb": 2.5, "fat": 1.5, "fib": 0.0, "iron": 0.4, "calcium": 130, "magnesium": 25, "potassium": 160, "zinc": 0.6, "vitD": 0.0, "vitB12": 0.5, "sodium": 55},
    {"id": "paneer_tawa", "name": "Paneer Bhurji / Tawa Paneer Masala (100g raw)", "unit": "1 serving (100g)", "category": "High Protein", "cal": 295, "pro": 18.5, "carb": 5.5, "fat": 22.0, "fib": 0.8, "iron": 0.8, "calcium": 460, "magnesium": 32, "potassium": 140, "zinc": 1.8, "vitD": 0.5, "vitB12": 0.8, "sodium": 260},
    {"id": "channa_sundal", "name": "Kondaikadalai (Black Channa) Sundal", "unit": "1 cup (140g)", "category": "High Protein", "cal": 210, "pro": 10.5, "carb": 32.0, "fat": 4.5, "fib": 8.2, "iron": 3.1, "calcium": 68, "magnesium": 65, "potassium": 380, "zinc": 1.5, "vitD": 0.0, "vitB12": 0.0, "sodium": 210},
    {"id": "dosa_plain", "name": "Kal Dosa / Home Dosa (Medium)", "unit": "1 dosa (75g)", "category": "Tiffin & Staples", "cal": 135, "pro": 3.6, "carb": 24.0, "fat": 2.8, "fib": 1.4, "iron": 0.9, "calcium": 18, "magnesium": 22, "potassium": 85, "zinc": 0.5, "vitD": 0.0, "vitB12": 0.0, "sodium": 160},
    {"id": "idli_std", "name": "Steamed Rice & Urad Idli", "unit": "2 idlis (110g)", "category": "Tiffin & Staples", "cal": 130, "pro": 4.4, "carb": 26.0, "fat": 0.6, "fib": 1.8, "iron": 0.8, "calcium": 20, "magnesium": 24, "potassium": 90, "zinc": 0.6, "vitD": 0.0, "vitB12": 0.0, "sodium": 150},
    {"id": "chapati_wheat", "name": "Whole Wheat Home Chapati", "unit": "1 chapati (45g)", "category": "Tiffin & Staples", "cal": 120, "pro": 4.0, "carb": 21.0, "fat": 2.2, "fib": 3.1, "iron": 1.5, "calcium": 16, "magnesium": 38, "potassium": 120, "zinc": 0.8, "vitD": 0.0, "vitB12": 0.0, "sodium": 90},
    {"id": "ponni_rice", "name": "Steamed Ponni Boiled Rice", "unit": "1 cup cooked (160g)", "category": "Tiffin & Staples", "cal": 195, "pro": 4.2, "carb": 43.0, "fat": 0.5, "fib": 1.2, "iron": 0.6, "calcium": 12, "magnesium": 20, "potassium": 60, "zinc": 0.7, "vitD": 0.0, "vitB12": 0.0, "sodium": 10},
    {"id": "oats_rolled", "name": "Rolled Oats (Dry Weight)", "unit": "60g dry", "category": "Tiffin & Staples", "cal": 230, "pro": 7.8, "carb": 40.0, "fat": 4.2, "fib": 6.0, "iron": 2.5, "calcium": 32, "magnesium": 85, "potassium": 210, "zinc": 1.8, "vitD": 0.0, "vitB12": 0.0, "sodium": 5},
    {"id": "sweet_potato", "name": "Boiled Sweet Potato (Sakkaraivalli Kizhangu)", "unit": "150g boiled", "category": "Tiffin & Staples", "cal": 135, "pro": 2.4, "carb": 31.0, "fat": 0.2, "fib": 4.5, "iron": 1.1, "calcium": 45, "magnesium": 38, "potassium": 510, "zinc": 0.4, "vitD": 0.0, "vitB12": 0.0, "sodium": 45},
    {"id": "pepper_rasam", "name": "TN Pepper, Cumin & Garlic Rasam (No Powder)", "unit": "1 bowl (180ml)", "category": "Kuzhambu & Sides", "cal": 55, "pro": 1.8, "carb": 8.5, "fat": 1.6, "fib": 1.4, "iron": 1.4, "calcium": 28, "magnesium": 26, "potassium": 195, "zinc": 0.4, "vitD": 0.0, "vitB12": 0.0, "sodium": 310},
    {"id": "tiffin_sambar", "name": "Murungakkai / Mixed Veg Toor Dal Sambar", "unit": "1 bowl (180ml)", "category": "Kuzhambu & Sides", "cal": 135, "pro": 6.5, "carb": 19.0, "fat": 3.8, "fib": 4.2, "iron": 1.9, "calcium": 48, "magnesium": 44, "potassium": 320, "zinc": 0.8, "vitD": 0.0, "vitB12": 0.0, "sodium": 360},
    {"id": "coconut_chutney", "name": "Coconut & Pottukadalai Chutney", "unit": "2 tbsp (45g)", "category": "Kuzhambu & Sides", "cal": 95, "pro": 2.4, "carb": 5.5, "fat": 7.2, "fib": 2.0, "iron": 0.7, "calcium": 12, "magnesium": 18, "potassium": 115, "zinc": 0.4, "vitD": 0.0, "vitB12": 0.0, "sodium": 140},
    {"id": "keerai_kootu", "name": "Arai Keerai / Spinach Moong Dal Kootu", "unit": "1 katori (150g)", "category": "Kuzhambu & Sides", "cal": 140, "pro": 7.2, "carb": 17.0, "fat": 4.5, "fib": 4.8, "iron": 4.2, "calcium": 135, "magnesium": 78, "potassium": 420, "zinc": 0.9, "vitD": 0.0, "vitB12": 0.0, "sodium": 240},
    {"id": "curd_bowl", "name": "Thick Home-Set Curd / Thayir", "unit": "1 katori (150g)", "category": "Kuzhambu & Sides", "cal": 98, "pro": 5.8, "carb": 7.2, "fat": 5.0, "fib": 0.0, "iron": 0.2, "calcium": 185, "magnesium": 22, "potassium": 230, "zinc": 0.8, "vitD": 0.2, "vitB12": 0.7, "sodium": 65},
    {"id": "peanut_butter", "name": "Natural Unsweetened Creamy Peanut Butter", "unit": "1 tbsp (16g)", "category": "Shakes & Fruits", "cal": 96, "pro": 4.2, "carb": 3.0, "fat": 8.0, "fib": 1.2, "iron": 0.3, "calcium": 8, "magnesium": 28, "potassium": 110, "zinc": 0.5, "vitD": 0.0, "vitB12": 0.0, "sodium": 5},
    {"id": "toned_milk", "name": "Toned Milk (for Shake / Filter Coffee)", "unit": "250 ml", "category": "Shakes & Fruits", "cal": 150, "pro": 8.0, "carb": 12.0, "fat": 7.5, "fib": 0.0, "iron": 0.2, "calcium": 300, "magnesium": 28, "potassium": 350, "zinc": 1.0, "vitD": 1.2, "vitB12": 1.1, "sodium": 110},
    {"id": "banana_robusta", "name": "Medium Robusta / Poovan Banana", "unit": "1 banana (120g)", "category": "Shakes & Fruits", "cal": 105, "pro": 1.3, "carb": 27.0, "fat": 0.4, "fib": 3.1, "iron": 0.3, "calcium": 6, "magnesium": 32, "potassium": 422, "zinc": 0.2, "vitD": 0.0, "vitB12": 0.0, "sodium": 1}
]

# Master offline dictionary for instant auto-fetch of regional & fitness foods
EXTENDED_SI_LOOKUP = [
    {"keywords": ["boiled egg", "egg", "muttai", "avicha muttai"], "name": "Boiled Egg (Whole Large)", "unit": "1 egg (50g)", "category": "High Protein", "cal": 72, "pro": 6.3, "carb": 0.6, "fat": 4.8, "fib": 0.0, "iron": 0.9, "calcium": 28, "magnesium": 6},
    {"keywords": ["egg white", "white egg"], "name": "Boiled Egg White (Single)", "unit": "1 egg white (33g)", "category": "High Protein", "cal": 17, "pro": 3.6, "carb": 0.2, "fat": 0.1, "fib": 0.0, "iron": 0.03, "calcium": 2, "magnesium": 4},
    {"keywords": ["scrambled egg", "egg podimas", "muttai podimas", "egg bhurji"], "name": "Muttai Podimas / Egg Bhurji (2 Eggs)", "unit": "1 serving (2 eggs)", "category": "High Protein", "cal": 195, "pro": 13.2, "carb": 3.0, "fat": 14.5, "fib": 0.6, "iron": 2.0, "calcium": 65, "magnesium": 18},
    {"keywords": ["ragi dosa", "kezhvaragu dosa", "finger millet dosa"], "name": "Ragi / Kezhvaragu Dosa", "unit": "1 dosa (80g)", "category": "Tiffin & Staples", "cal": 130, "pro": 3.8, "carb": 23.0, "fat": 2.4, "fib": 2.8, "iron": 1.8, "calcium": 95, "magnesium": 40},
    {"keywords": ["pesarattu", "moong dosa", "pasi paruppu dosa"], "name": "Pesarattu (Whole Green Gram Dosa)", "unit": "1 dosa (90g)", "category": "High Protein", "cal": 155, "pro": 7.5, "carb": 22.0, "fat": 3.8, "fib": 4.2, "iron": 2.1, "calcium": 45, "magnesium": 48},
    {"keywords": ["adai", "paruppu adai"], "name": "Tamil Nadu Mixed Lentil Adai", "unit": "1 medium adai (100g)", "category": "High Protein", "cal": 195, "pro": 8.4, "carb": 27.0, "fat": 5.8, "fib": 4.5, "iron": 2.4, "calcium": 42, "magnesium": 52},
    {"keywords": ["uttapam", "onion uttapam", "oothappam"], "name": "Onion-Tomato Uttapam", "unit": "1 uttapam (120g)", "category": "Tiffin & Staples", "cal": 180, "pro": 4.8, "carb": 31.0, "fat": 4.0, "fib": 2.2, "iron": 1.2, "calcium": 28, "magnesium": 30},
    {"keywords": ["appam", "thengai paal appam"], "name": "Fermented Rice Appam", "unit": "2 appams", "category": "Tiffin & Staples", "cal": 170, "pro": 3.2, "carb": 34.0, "fat": 2.0, "fib": 1.0, "iron": 0.6, "calcium": 15, "magnesium": 18},
    {"keywords": ["idiyappam", "string hoppers"], "name": "Steamed Idiyappam", "unit": "3 nests (120g)", "category": "Tiffin & Staples", "cal": 165, "pro": 3.1, "carb": 36.0, "fat": 0.6, "fib": 1.4, "iron": 0.7, "calcium": 14, "magnesium": 18},
    {"keywords": ["upma", "rava upma"], "name": "South Indian Vegetable Rava Upma", "unit": "1 cup (180g)", "category": "Tiffin & Staples", "cal": 210, "pro": 5.2, "carb": 34.0, "fat": 5.8, "fib": 2.5, "iron": 1.4, "calcium": 26, "magnesium": 32},
    {"keywords": ["pongal", "ven pongal", "khara pongal"], "name": "Ven Pongal (Rice & Moong Dal)", "unit": "1 cup (200g)", "category": "Tiffin & Staples", "cal": 280, "pro": 7.5, "carb": 41.0, "fat": 9.5, "fib": 2.8, "iron": 1.6, "calcium": 30, "magnesium": 42},
    {"keywords": ["medhu vadai", "ulundu vadai", "medu vada", "vada"], "name": "Medhu Vadai (Urad Dal)", "unit": "1 vadai (45g)", "category": "Tiffin & Staples", "cal": 135, "pro": 3.8, "carb": 13.5, "fat": 7.2, "fib": 1.8, "iron": 1.1, "calcium": 22, "magnesium": 25},
    {"keywords": ["curd rice", "thayir sadam"], "name": "Thayir Sadam / Curd Rice", "unit": "1 cup (220g)", "category": "Tiffin & Staples", "cal": 245, "pro": 7.8, "carb": 36.0, "fat": 7.2, "fib": 1.2, "iron": 0.7, "calcium": 195, "magnesium": 32},
    {"keywords": ["lemon rice", "elichampazham sadam"], "name": "Lemon Rice with Peanuts", "unit": "1 cup (200g)", "category": "Tiffin & Staples", "cal": 265, "pro": 5.8, "carb": 42.0, "fat": 8.0, "fib": 2.4, "iron": 1.3, "calcium": 22, "magnesium": 35},
    {"keywords": ["sambar rice", "sambar sadam", "bisibelebath"], "name": "Sambar Sadam (Rice + Dal + Veg)", "unit": "1 cup (240g)", "category": "Tiffin & Staples", "cal": 255, "pro": 8.2, "carb": 42.0, "fat": 5.5, "fib": 4.2, "iron": 2.2, "calcium": 52, "magnesium": 48},
    {"keywords": ["parotta", "malabar parotta"], "name": "South Indian Layered Parotta", "unit": "1 parotta (80g)", "category": "Tiffin & Staples", "cal": 260, "pro": 5.2, "carb": 38.0, "fat": 9.5, "fib": 1.5, "iron": 1.2, "calcium": 18, "magnesium": 20},
    {"keywords": ["filter coffee", "kumbakonam coffee", "coffee"], "name": "South Indian Filter Coffee (with Milk, Low Sugar)", "unit": "1 cup (150ml)", "category": "Shakes & Fruits", "cal": 85, "pro": 3.5, "carb": 8.5, "fat": 4.0, "fib": 0.0, "iron": 0.1, "calcium": 135, "magnesium": 16},
    {"keywords": ["buttermilk", "neer mor", "mor"], "name": "Spiced Neer Mor / Buttermilk", "unit": "1 glass (200ml)", "category": "Shakes & Fruits", "cal": 45, "pro": 2.6, "carb": 3.5, "fat": 2.2, "fib": 0.2, "iron": 0.2, "calcium": 85, "magnesium": 12},
    {"keywords": ["roasted peanuts", "verkadalai", "groundnut"], "name": "Roasted Peanuts (Verkadalai)", "unit": "30g handful", "category": "High Protein", "cal": 170, "pro": 7.8, "carb": 4.8, "fat": 14.5, "fib": 2.5, "iron": 1.3, "calcium": 26, "magnesium": 52},
    {"keywords": ["almonds", "badam"], "name": "Raw / Soaked Almonds (Badam)", "unit": "15 almonds (18g)", "category": "Shakes & Fruits", "cal": 104, "pro": 3.8, "carb": 3.9, "fat": 9.0, "fib": 2.2, "iron": 0.7, "calcium": 48, "magnesium": 49},
    {"keywords": ["greek yogurt", "epigamia", "skyr"], "name": "High-Protein Greek Yogurt (Unflavored)", "unit": "1 cup (100g)", "category": "High Protein", "cal": 95, "pro": 9.5, "carb": 4.5, "fat": 4.0, "fib": 0.0, "iron": 0.1, "calcium": 150, "magnesium": 15},
    {"keywords": ["tofu", "soya paneer"], "name": "Firm Tofu Stir Fry", "unit": "100g serving", "category": "High Protein", "cal": 145, "pro": 15.5, "carb": 3.0, "fat": 8.0, "fib": 1.2, "iron": 2.8, "calcium": 350, "magnesium": 58},
    {"keywords": ["avial", "aviyal"], "name": "Mixed Vegetable Coconut Avial", "unit": "1 katori (150g)", "category": "Kuzhambu & Sides", "cal": 145, "pro": 3.4, "carb": 14.0, "fat": 8.5, "fib": 4.2, "iron": 1.2, "calcium": 48, "magnesium": 32},
    {"keywords": ["kootu", "cabbage kootu", "chow chow kootu"], "name": "Poricha Kootu (Veg & Moong Dal)", "unit": "1 katori (150g)", "category": "Kuzhambu & Sides", "cal": 135, "pro": 6.2, "carb": 17.5, "fat": 4.2, "fib": 4.0, "iron": 1.8, "calcium": 45, "magnesium": 40},
    {"keywords": ["puli kuzhambu", "vathal kuzhambu", "kara kuzhambu"], "name": "Kara / Vathal Kuzhambu", "unit": "1 katori (120ml)", "category": "Kuzhambu & Sides", "cal": 125, "pro": 2.2, "carb": 14.0, "fat": 6.8, "fib": 2.4, "iron": 1.6, "calcium": 38, "magnesium": 28},
    {"keywords": ["ghee", "cow ghee", "nei"], "name": "Pure Cow Ghee", "unit": "1 tsp (5g)", "category": "Shakes & Fruits", "cal": 45, "pro": 0.0, "carb": 0.0, "fat": 5.0, "fib": 0.0, "iron": 0.0, "calcium": 0, "magnesium": 0},
    {"keywords": ["apple", "guava", "papaya", "pomegranate"], "name": "Fresh Fruit Bowl (Guava / Apple / Pomegranate)", "unit": "1 medium bowl (150g)", "category": "Shakes & Fruits", "cal": 92, "pro": 1.8, "carb": 21.0, "fat": 0.6, "fib": 5.4, "iron": 0.5, "calcium": 22, "magnesium": 20}
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
# 3. WEIGHT-BASED HEALTHY TARGET AUTO-CALCULATOR
# -----------------------------------------------------------------------------
def calculate_targets_from_weights(current_wt: float, target_wt: float):
    """
    Computes scientifically backed daily nutrition targets purely from
    Current Weight (kg) and Target Weight (kg).
    """
    diff = target_wt - current_wt
    maintenance_cal = round(current_wt * 31.0)

    if abs(diff) <= 1.0:
        mode_name = "Lean Body Recomposition (Maintain Weight + Build Muscle)"
        base_cal = maintenance_cal
        pro_per_kg = 2.05
        fat_per_kg = 0.90
        weekly_rate = "Maintain weight while increasing muscle density"
    elif diff > 1.0:
        mode_name = f"Lean Hypertrophy Bulk (+{diff:.1f} kg Goal)"
        # Controlled +250 kcal surplus to build muscle with minimal fat gain
        base_cal = maintenance_cal + 250
        pro_per_kg = 2.00
        fat_per_kg = 0.95
        weeks_est = max(4, round((diff * 7700) / (250 * 7)))
        weekly_rate = f"+0.25 kg/week (~{weeks_est} weeks to reach {target_wt} kg cleanly)"
    else:
        mode_name = f"Lean Definition Cut ({diff:.1f} kg Goal)"
        # Controlled -350 kcal deficit while elevating protein to protect lean mass
        base_cal = max(1500, maintenance_cal - 350)
        pro_per_kg = 2.15
        fat_per_kg = 0.85
        weeks_est = max(3, round((abs(diff) * 7700) / (350 * 7)))
        weekly_rate = f"-0.35 kg/week (~{weeks_est} weeks to reach {target_wt} kg)"

    pro_g = round(current_wt * pro_per_kg)
    fat_g = round(current_wt * fat_per_kg)
    remaining_cals = max(400, base_cal - (pro_g * 4) - (fat_g * 9))
    carb_g = round(remaining_cals / 4)
    fib_g = round(max(30, (base_cal / 1000) * 15))
    water_l = round(current_wt * 0.045, 1)

    return {
        "mode_name": mode_name,
        "weekly_rate": weekly_rate,
        "base_cal": base_cal,
        "pro_target": pro_g,
        "carb_target": carb_g,
        "fat_target": fat_g,
        "fib_target": fib_g,
        "water_target": water_l
    }

# -----------------------------------------------------------------------------
# 4. AUTO-FETCH FOOD ENGINE (LOCAL DICTIONARY + LIVE OPENFOODFACTS API)
# -----------------------------------------------------------------------------
def auto_fetch_food_nutrition(query_text: str):
    """
    1. Checks the built-in Extended South Indian & Fitness Dictionary first.
    2. Falls back to the live OpenFoodFacts API if not found locally.
    """
    q = query_text.strip().lower()
    if not q:
        return None, "Please enter a food name."

    # Step A: Check Built-In Extended South Indian & Fitness Dictionary
    for item in EXTENDED_SI_LOOKUP:
        if any(k in q or q in k for k in item["keywords"]):
            return {
                "id": f"fetched_{int(datetime.now().timestamp())}",
                "name": item["name"],
                "unit": item["unit"],
                "category": item["category"],
                "cal": float(item["cal"]),
                "pro": float(item["pro"]),
                "carb": float(item["carb"]),
                "fat": float(item["fat"]),
                "fib": float(item["fib"]),
                "iron": float(item["iron"]),
                "calcium": float(item["calcium"]),
                "magnesium": float(item["magnesium"]),
                "potassium": 180.0, "zinc": 0.7, "vitD": 0.2, "vitB12": 0.2, "sodium": 150.0
            }, "Matched from Built-in South Indian & Fitness Nutrition Dictionary!"

    # Step B: Live Internet Lookup via OpenFoodFacts Public API
    try:
        encoded = urllib.parse.quote(q)
        url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={encoded}&search_simple=1&action=process&json=1&page_size=5"
        req = urllib.request.Request(url, headers={"User-Agent": "SINutritionStudio/2.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            products = data.get("products", [])
            for prod in products:
                nutr = prod.get("nutriments", {})
                kcal = nutr.get("energy-kcal_100g") or nutr.get("energy-kcal_serving")
                pro = nutr.get("proteins_100g")
                carb = nutr.get("carbohydrates_100g")
                fat = nutr.get("fat_100g")
                if kcal is not None and pro is not None:
                    p_name = prod.get("product_name") or query_text.title()
                    return {
                        "id": f"api_{int(datetime.now().timestamp())}",
                        "name": f"{p_name.strip()} (Fetched)",
                        "unit": "100g serving",
                        "category": "High Protein" if float(pro) >= 12 else "Tiffin & Staples",
                        "cal": round(float(kcal), 1),
                        "pro": round(float(pro or 0), 1),
                        "carb": round(float(carb or 0), 1),
                        "fat": round(float(fat or 0), 1),
                        "fib": round(float(nutr.get("fiber_100g") or 1.5), 1),
                        "iron": round(float(nutr.get("iron_100g", 0.001)) * 1000, 1) if nutr.get("iron_100g") else 1.0,
                        "calcium": round(float(nutr.get("calcium_100g", 0.04)) * 1000, 0) if nutr.get("calcium_100g") else 40.0,
                        "magnesium": 30.0, "potassium": 180.0, "zinc": 0.6, "vitD": 0.0, "vitB12": 0.0, "sodium": 140.0
                    }, "Fetched live from OpenFoodFacts Global Nutrition API (per 100g)!"
    except Exception:
        pass

    return None, "Could not auto-fetch online. You can adjust the values below and click Save!"

# -----------------------------------------------------------------------------
# 5. PERSISTENCE & DATABASE INITIALIZATION
# -----------------------------------------------------------------------------
def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
                # Ensure Boiled Egg is always in dropdown
                if not any(x["id"] == "boiled_egg" for x in db.get("foods", [])):
                    db["foods"].insert(0, DEFAULT_FOODS[0])
                return db
        except Exception:
            pass

    auto_t = calculate_targets_from_weights(72.5, 72.5)
    return {
        "profile": {
            "current_weight": 72.5,
            "target_weight": 72.5,
            "eatback_pct": 75,
            **auto_t
        },
        "foods": list(DEFAULT_FOODS),
        "buckets": list(DEFAULT_BUCKETS),
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
            "gym": {"hours": 0.0, "protocol": list(GYM_PROTOCOLS.keys())[0]},
            "supplements": {"creatine": False, "fish_oil": False, "magnesium": False},
            "water_liters": 0.0
        }

def get_food_map():
    return {f["id"]: f for f in st.session_state.db["foods"]}

# -----------------------------------------------------------------------------
# 6. DAILY SUMMARY & GYM EXPENDITURE CALCULATOR
# -----------------------------------------------------------------------------
def compute_day_summary(date_str):
    ensure_day_log(date_str)
    day_log = st.session_state.db["logs"][date_str]
    food_map = get_food_map()
    prof = st.session_state.db["profile"]

    # Recalculate base targets from current & target weight automatically
    auto_t = calculate_targets_from_weights(
        float(prof.get("current_weight", 72.5)),
        float(prof.get("target_weight", 72.5))
    )
    prof.update(auto_t)

    totals = {
        "cal": 0.0, "pro": 0.0, "carb": 0.0, "fat": 0.0, "fib": 0.0,
        "iron": 0.0, "calcium": 0.0, "magnesium": 0.0, "potassium": 0.0,
        "zinc": 0.0, "vitD": 0.0, "vitB12": 0.0, "sodium": 0.0,
        "meals_over_28g_pro": 0,
        "slot_breakdown": {},
        "logged_food_names": []
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
            totals["logged_food_names"].append(f["name"])

            for m_key in MICRO_RDI.keys():
                totals[m_key] += f.get(m_key, 0.0) * q

        if slot_pro >= 28.0:
            totals["meals_over_28g_pro"] += 1
        totals["slot_breakdown"][slot] = {
            "cal": slot_cal, "pro": slot_pro, "carb": slot_carb, "fat": slot_fat
        }

    supps = day_log.get("supplements", {})
    if supps.get("magnesium"):
        totals["magnesium"] += 250.0
    if supps.get("fish_oil"):
        totals["fat"] += 1.0
        totals["cal"] += 9.0
        totals["vitD"] += 5.0

    # Gym Expenditure Calculation
    gym_hours = float(day_log["gym"].get("hours", 0.0))
    protocol = day_log["gym"].get("protocol", list(GYM_PROTOCOLS.keys())[0])
    met = GYM_PROTOCOLS.get(protocol, 5.2)
    gym_burn = round(met * float(prof["current_weight"]) * gym_hours)

    eatback_cals = round(gym_burn * (prof.get("eatback_pct", 75) / 100.0))
    totals["gym_hours"] = gym_hours
    totals["gym_burn"] = gym_burn
    totals["dynamic_cal_target"] = prof["base_cal"] + eatback_cals
    totals["dynamic_carb_target"] = prof["carb_target"] + round((eatback_cals * 0.80) / 4.0)
    totals["dynamic_pro_target"] = prof["pro_target"] + round((eatback_cals * 0.20) / 4.0)
    totals["net_calories"] = totals["cal"] - gym_burn

    return totals

# -----------------------------------------------------------------------------
# 7. SIDEBAR: WEIGHT-ONLY GOAL ENGINE & GYM CALORIE CALCULATOR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🍛 SI Nutrition Studio")
    selected_date = st.date_input("📅 Active Tracking Date", value=date.today())
    active_date_str = selected_date.strftime("%Y-%m-%d")
    ensure_day_log(active_date_str)
    current_day_log = st.session_state.db["logs"][active_date_str]

    st.divider()

    # --- WEIGHT-ONLY AUTOMATIC GOAL ENGINE ---
    st.subheader("🎯 Body Weight Goal Setup")
    st.caption("Set only your current & goal weight—macros and calories are auto-calculated.")
    prof = st.session_state.db["profile"]

    c_w1, c_w2 = st.columns(2)
    cur_wt = c_w1.number_input("Current (kg)", 40.0, 140.0, float(prof.get("current_weight", 72.5)), 0.5)
    trg_wt = c_w2.number_input("Goal (kg)", 40.0, 140.0, float(prof.get("target_weight", 72.5)), 0.5)

    if cur_wt != prof.get("current_weight") or trg_wt != prof.get("target_weight"):
        prof["current_weight"] = cur_wt
        prof["target_weight"] = trg_wt
        prof.update(calculate_targets_from_weights(cur_wt, trg_wt))
        save_db()
        st.rerun()

    st.success(
        f"**Strategy:** {prof['mode_name']}  \n"
        f"• **Pace:** {prof['weekly_rate']}  \n"
        f"• **Auto Base Target:** `{prof['base_cal']} kcal` | `{prof['pro_target']}g P` | `{prof['carb_target']}g C` | `{prof['fat_target']}g F`"
    )

    st.divider()

    # --- GYM HOURS & CALORIE BURN ---
    st.subheader("🏋️‍♂️ Today's Gym Log")
    gym_hours = st.number_input(
        "Gym Hours Today", 0.0, 5.0, float(current_day_log["gym"].get("hours", 0.0)), 0.25
    )
    protocol_list = list(GYM_PROTOCOLS.keys())
    saved_prot = current_day_log["gym"].get("protocol", protocol_list[0])
    p_idx = protocol_list.index(saved_prot) if saved_prot in protocol_list else 0
    gym_protocol = st.selectbox("Workout Type", options=protocol_list, index=p_idx)

    est_burn = round(GYM_PROTOCOLS[gym_protocol] * cur_wt * gym_hours)
    st.info(f"🔥 **Calories Burnt:** `{est_burn} kcal`")

    if gym_hours != current_day_log["gym"].get("hours") or gym_protocol != current_day_log["gym"].get("protocol"):
        current_day_log["gym"]["hours"] = gym_hours
        current_day_log["gym"]["protocol"] = gym_protocol
        save_db()
        st.rerun()

    st.divider()

    # --- DAILY SUPPLEMENTS & WATER ---
    st.subheader("⚡ Daily Supplements & Water")
    sc1, sc2, sc3 = st.columns(3)
    cre_v = sc1.checkbox("Creatine", value=current_day_log["supplements"].get("creatine", False))
    fo_v = sc2.checkbox("Fish Oil", value=current_day_log["supplements"].get("fish_oil", False))
    mag_v = sc3.checkbox("Magnesium", value=current_day_log["supplements"].get("magnesium", False))
    wat_v = st.slider(
        f"💧 Water (Target: {prof.get('water_target', 3.3)} L)",
        0.0, 5.0, float(current_day_log.get("water_liters", 0.0)), 0.25
    )
    if (cre_v != current_day_log["supplements"]["creatine"] or
        fo_v != current_day_log["supplements"]["fish_oil"] or
        mag_v != current_day_log["supplements"]["magnesium"] or
        wat_v != current_day_log["water_liters"]):
        current_day_log["supplements"].update({"creatine": cre_v, "fish_oil": fo_v, "magnesium": mag_v})
        current_day_log["water_liters"] = wat_v
        save_db()
        st.rerun()

# -----------------------------------------------------------------------------
# 8. TOP SUMMARY METRICS
# -----------------------------------------------------------------------------
day_summary = compute_day_summary(active_date_str)
prof = st.session_state.db["profile"]

k1, k2, k3, k4, k5 = st.columns(5)
cal_diff = round(day_summary["cal"] - day_summary["dynamic_cal_target"])
k1.metric(
    "Calories (vs Dynamic Goal)",
    f"{round(day_summary['cal'])} / {day_summary['dynamic_cal_target']} kcal",
    f"{cal_diff:+d} kcal"
)
k2.metric(
    "Protein (2.0g/kg Goal)",
    f"{day_summary['pro']:.1f} / {day_summary['dynamic_pro_target']} g",
    f"{(day_summary['pro']/prof['current_weight']):.2f} g/kg logged"
)
k3.metric(
    "Carbs & Fiber",
    f"{day_summary['carb']:.0f} / {day_summary['dynamic_carb_target']} g",
    f"Fiber: {day_summary['fib']:.1f}/{prof['fib_target']}g"
)
k4.metric(
    "Healthy Fats",
    f"{day_summary['fat']:.1f} / {prof['fat_target']} g",
    f"≥28g Pro Meals: {day_summary['meals_over_28g_pro']}/4"
)
k5.metric(
    "Gym Burn & Net Intake",
    f"{day_summary['gym_burn']} kcal burnt",
    f"Net: {round(day_summary['net_calories'])} kcal"
)

# -----------------------------------------------------------------------------
# 9. MAIN NAVIGATION TABS
# -----------------------------------------------------------------------------
tab_log, tab_manage, tab_trends, tab_backup = st.tabs([
    "🍛 Daily Meal Logger & Routine Coach",
    "🛠️ Customize Buckets & Auto-Fetch Foods",
    "📈 Weekly & Monthly Trends",
    "💾 Backup & 30-Day Demo Seeder"
])

# =============================================================================
# TAB 1: DAILY LOGGER, QUICK AUTO-FETCH & ROUTINE-BASED SMART COACH
# =============================================================================
with tab_log:
    col_l, col_r = st.columns([7, 5], gap="large")

    with col_l:
        st.subheader("1️⃣ Select Meal Slot & Click a Bucket")
        target_slot = st.radio("Log into Meal Slot:", options=MEAL_SLOTS, horizontal=True)

        food_map = get_food_map()
        if not st.session_state.db["buckets"]:
            st.info("No meal buckets available. Create one in the 'Customize Buckets' tab!")

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
                if st.button("➕ Log Pack", key=f"log_pack_{b['id']}", use_container_width=True):
                    slot_items = current_day_log["meals"][target_slot]
                    for item in b["items"]:
                        if item["foodId"] not in food_map:
                            continue
                        existing = next((x for x in slot_items if x["foodId"] == item["foodId"]), None)
                        if existing:
                            existing["qty"] = round(existing["qty"] + item["qty"], 2)
                        else:
                            slot_items.append({"foodId": item["foodId"], "qty": float(item["qty"])})
                    save_db()
                    st.rerun()
            st.markdown("<hr style='margin:6px 0;border-color:#1e293b;'>", unsafe_allow_html=True)

        # --- INDIVIDUAL FOOD DROPDOWN + INSTANT MISSING FOOD FETCHER ---
        st.subheader("2️⃣ Log Individual Food from Dropdown")
        fc1, fc2, fc3 = st.columns([3, 1, 1])
        food_options = {
            f"{f['name']} ({f['unit']} — {f['cal']:g} kcal, {f['pro']:g}g P)": f["id"]
            for f in st.session_state.db["foods"]
        }
        chosen_label = fc1.selectbox("Search Dropdown (Boiled Egg, Soya, Dosa, Rasam...)", options=list(food_options.keys()))
        chosen_qty = fc2.number_input("Quantity", 0.25, 15.0, 1.0, 0.25)
        if fc3.button("➕ Add Food", use_container_width=True):
            f_id = food_options[chosen_label]
            slot_items = current_day_log["meals"][target_slot]
            existing = next((x for x in slot_items if x["foodId"] == f_id), None)
            if existing:
                existing["qty"] = round(existing["qty"] + chosen_qty, 2)
            else:
                slot_items.append({"foodId": f_id, "qty": float(chosen_qty)})
            save_db()
            st.rerun()

        with st.expander("🔍 Food not in dropdown? Type any food here to Auto-Fetch & Save for future use"):
            qf1, qf2 = st.columns([3, 1])
            quick_query = qf1.text_input("Type food name (e.g., Boiled Egg, Ragi Dosa, Pesarattu, Roasted Peanuts)", key="quick_fetch_in")
            if qf2.button("Fetch & Add", use_container_width=True):
                fetched_item, msg = auto_fetch_food_nutrition(quick_query)
                if fetched_item:
                    st.session_state.db["foods"].insert(0, fetched_item)
                    save_db()
                    st.success(f"✅ Added **{fetched_item['name']}** ({fetched_item['cal']} kcal, {fetched_item['pro']}g P) to your dropdown!")
                    st.rerun()
                else:
                    st.warning(msg + " Go to Tab 2 ('Customize Buckets & Auto-Fetch Foods') to enter custom numbers.")

        # --- TODAY'S LOGGED MEALS ---
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
                    st.caption("Nothing logged in this meal slot yet.")
                else:
                    for idx, entry in enumerate(s_items):
                        f_obj = food_map.get(entry["foodId"])
                        if not f_obj:
                            continue
                        q = entry["qty"]
                        r1, r2, r3 = st.columns([4, 2, 1])
                        r1.write(f"**{f_obj['name']}** (`{q:g}x` {f_obj['unit']})")
                        r2.write(f"`{round(f_obj['cal']*q)} kcal` • **{f_obj['pro']*q:.1f}g P**")
                        if r3.button("🗑️", key=f"del_{slot}_{idx}"):
                            current_day_log["meals"][slot].pop(idx)
                            save_db()
                            st.rerun()

    # --- RIGHT COLUMN: ROUTINE-AWARE SMART COACH & MICRONUTRIENT BARS ---
    with col_r:
        st.subheader("🧠 Smart Coach (Based on Your Weight Goal & Routine)")

        pro_gap = round(day_summary["dynamic_pro_target"] - day_summary["pro"], 1)
        cal_gap = round(day_summary["dynamic_cal_target"] - day_summary["cal"])
        carb_gap = round(day_summary["dynamic_carb_target"] - day_summary["carb"])
        fib_gap = round(prof["fib_target"] - day_summary["fib"], 1)
        logged_names_str = " ".join(day_summary["logged_food_names"]).lower()

        # 1. Weight Goal & Daily Blueprint Card
        st.markdown(
            f"<div class='coach-box coach-info'>"
            f"<b>🎯 Active Blueprint: {prof['mode_name']}</b><br>"
            f"<span style='font-size:13px;'>At <b>{prof['current_weight']} kg</b> (Goal: <b>{prof['target_weight']} kg</b>), "
            f"your healthy daily requirement today (including <b>{day_summary['gym_hours']} hrs gym</b>) is:<br>"
            f"• <b>{day_summary['dynamic_cal_target']} kcal</b> | <b>{day_summary['dynamic_pro_target']}g Protein</b> | "
            f"<b>{day_summary['dynamic_carb_target']}g Carbs</b> | <b>{prof['fat_target']}g Fats</b></span>"
            f"</div>",
            unsafe_allow_html=True
        )

        # 2. Routine-Aware What to Eat Next (Protein & Calorie Prescription)
        if pro_gap > 12:
            # Suggest specific foods from the user's South Indian routine not yet maxed out today
            routine_recs = []
            if "soya" not in logged_names_str and pro_gap >= 22:
                routine_recs.append("<b>1 plate Home Dry Soya Chunk Fry</b> (+26g Protein, 215 kcal)")
            if "whey" not in logged_names_str and pro_gap >= 20:
                routine_recs.append("<b>1 scoop Whey Protein Shake</b> (+24g Protein, 120 kcal)")
            if "paneer" not in logged_names_str and cal_gap >= 250:
                routine_recs.append("<b>100g Paneer Tawa Masala</b> (+18.5g Protein, 295 kcal)")

            eggs_needed = max(1, min(4, round(pro_gap / 6.3)))
            routine_recs.append(f"<b>{eggs_needed} Boiled Eggs</b> (+{eggs_needed*6.3:.1f}g Protein, {eggs_needed*72} kcal)")
            routine_recs.append("<b>3 Boiled Egg Whites</b> (+10.8g Protein, only 51 kcal)")

            recs_html = "<br>• ".join(routine_recs[:3])
            st.markdown(
                f"<div class='coach-box coach-warn'>"
                f"<b>🥚 What to Take Next ({pro_gap}g Protein & {max(0, cal_gap)} kcal needed)</b><br>"
                f"<span style='font-size:13px;'>Based on what you have eaten so far today, pick one of these to hit your target:<br>"
                f"• {recs_html}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='coach-box coach-ok'>"
                f"<b>✅ Protein Target Complete ({day_summary['pro']:.1f}g / {day_summary['dynamic_pro_target']}g)</b><br>"
                f"<span style='font-size:13px;'>Your muscle protein synthesis requirement is 100% met today! "
                f"If you still have <b>{max(0, cal_gap)} kcal</b> left, fill it with clean carbs like "
                f"<b>Boiled Sweet Potato</b>, <b>Banana</b>, or <b>Chapati + Rasam</b>.</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        # 3. Routine Carbohydrate vs Protein Balance Check
        total_macro_cals = (day_summary["pro"] * 4) + (day_summary["carb"] * 4) + (day_summary["fat"] * 9)
        carb_pct = ((day_summary["carb"] * 4) / total_macro_cals * 100) if total_macro_cals > 0 else 0
        if day_summary["cal"] > 600 and carb_pct > 62:
            st.markdown(
                f"<div class='coach-box coach-warn'>"
                f"<b>⚖️ South Indian Carb-to-Protein Balance ({carb_pct:.0f}% Carbs)</b><br>"
                f"<span style='font-size:13px;'>Your intake today is skewing high on rice/dosa/tiffin carbs. "
                f"For your next meal, reduce 1 Dosa or 0.5 cup Rice and pair with <b>Boiled Eggs</b>, <b>Soya Fry</b>, or <b>Keerai Kootu</b>.</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        # 4. Micronutrient & Fiber Guidance
        if day_summary["iron"] < 12.0 or fib_gap > 10:
            st.markdown(
                f"<div class='coach-box coach-info'>"
                f"<b>🔬 Micronutrient & Fiber Boost</b><br>"
                f"<span style='font-size:13px;'>You need <b>+{max(0.0, 17.0 - day_summary['iron']):.1f}mg Iron</b> and <b>+{max(0.0, fib_gap):.1f}g Fiber</b>. "
                f"Include <b>TN Pepper-Cumin-Garlic Rasam</b> with <b>Arai Keerai Kootu</b> or <b>Kondaikadalai Sundal</b>—the black pepper piperine increases iron absorption.</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.divider()
        st.subheader("🔬 Essential Micronutrients (Daily RDI)")
        for m_key, meta in MICRO_RDI.items():
            val = day_summary[m_key]
            pct = min(1.0, val / meta["target"])
            st.progress(
                pct,
                text=f"**{meta['label']}**: {val:.1f} / {meta['target']:g} {meta['unit']} ({round(pct*100)}%)"
            )

# =============================================================================
# TAB 2: CUSTOMIZE / RENAME / DELETE PRESET BUCKETS & AUTO-FETCH FOODS
# =============================================================================
with tab_manage:
    m_col1, m_col2 = st.columns(2, gap="large")

    # --- LEFT: FULL CONTROL OVER PRESET & CUSTOM MEAL PACK BUCKETS ---
    with m_col1:
        st.subheader("🍱 Manage, Rename, Edit or Delete Any Meal Bucket")
        st.caption("You have full control over all preset and custom buckets.")

        bucket_choices = ["➕ Create a Brand New Meal Bucket"] + [
            f"✏️ Edit: {b['name']}" for b in st.session_state.db["buckets"]
        ]
        selected_b_mode = st.selectbox("Select Bucket to Edit or Create New:", options=bucket_choices)

        food_map = get_food_map()
        food_label_to_id = {f"{f['name']} ({f['unit']} — {f['pro']:g}g P)": f["id"] for f in st.session_state.db["foods"]}

        if selected_b_mode == "➕ Create a Brand New Meal Bucket":
            if "new_bucket_draft" not in st.session_state:
                st.session_state.new_bucket_draft = []

            b_name_in = st.text_input("New Bucket Name", placeholder="e.g., Post-Workout Egg & Sweet Potato Pack")
            b_slot_in = st.selectbox("Default Meal Slot", options=MEAL_SLOTS, key="new_b_slot")

            af1, af2, af3 = st.columns([3, 1, 1])
            pick_f = af1.selectbox("Choose Food to Add", options=list(food_label_to_id.keys()), key="new_b_food")
            pick_q = af2.number_input("Qty", 0.25, 15.0, 1.0, 0.25, key="new_b_qty")
            if af3.button("Add Item", key="new_b_add_btn", use_container_width=True):
                st.session_state.new_bucket_draft.append({"foodId": food_label_to_id[pick_f], "qty": float(pick_q)})

            if st.session_state.new_bucket_draft:
                st.markdown("**Items in New Bucket:**")
                for idx, it in enumerate(st.session_state.new_bucket_draft):
                    f_obj = food_map.get(it["foodId"])
                    if f_obj:
                        ic1, ic2 = st.columns([4, 1])
                        ic1.write(f"• `{it['qty']:g}x` **{f_obj['name']}** ({round(f_obj['cal']*it['qty'])} kcal, {f_obj['pro']*it['qty']:.1f}g P)")
                        if ic2.button("✖", key=f"rm_draft_{idx}"):
                            st.session_state.new_bucket_draft.pop(idx)
                            st.rerun()

                if st.button("💾 Save New Bucket", use_container_width=True):
                    if b_name_in.strip():
                        st.session_state.db["buckets"].append({
                            "id": f"bucket_{int(datetime.now().timestamp())}",
                            "name": b_name_in.strip(),
                            "defaultSlot": b_slot_in,
                            "items": list(st.session_state.new_bucket_draft)
                        })
                        st.session_state.new_bucket_draft = []
                        save_db()
                        st.success("New Meal Bucket created!")
                        st.rerun()
                    else:
                        st.warning("Please give your bucket a name.")

        else:
            # Editing an existing preset or custom bucket
            b_idx = bucket_choices.index(selected_b_mode) - 1
            active_bucket = st.session_state.db["buckets"][b_idx]

            edited_name = st.text_input("Rename Bucket", value=active_bucket["name"], key=f"rn_{active_bucket['id']}")
            edited_slot = st.selectbox(
                "Default Slot",
                options=MEAL_SLOTS,
                index=MEAL_SLOTS.index(active_bucket.get("defaultSlot", "Breakfast")) if active_bucket.get("defaultSlot") in MEAL_SLOTS else 0,
                key=f"sl_{active_bucket['id']}"
            )

            st.markdown("**Current Foods Inside This Bucket (Adjust Qty or Remove):**")
            items_to_keep = []
            for idx, item in enumerate(active_bucket["items"]):
                f_obj = food_map.get(item["foodId"])
                if not f_obj:
                    continue
                ec1, ec2, ec3 = st.columns([3, 1, 1])
                ec1.write(f"**{f_obj['name']}** ({f_obj['unit']})")
                new_q = ec2.number_input(
                    "Qty", 0.25, 15.0, float(item["qty"]), 0.25,
                    key=f"eq_{active_bucket['id']}_{idx}", label_visibility="collapsed"
                )
                remove_clicked = ec3.button("🗑️", key=f"edel_{active_bucket['id']}_{idx}")
                if not remove_clicked:
                    items_to_keep.append({"foodId": item["foodId"], "qty": float(new_q)})
                else:
                    active_bucket["items"].pop(idx)
                    save_db()
                    st.rerun()

            st.markdown("**Add Another Food to This Bucket:**")
            ap1, ap2, ap3 = st.columns([3, 1, 1])
            add_f_label = ap1.selectbox("Select Food", options=list(food_label_to_id.keys()), key=f"af_{active_bucket['id']}")
            add_f_qty = ap2.number_input("Qty", 0.25, 15.0, 1.0, 0.25, key=f"aq_{active_bucket['id']}")
            if ap3.button("➕ Add", key=f"abtn_{active_bucket['id']}", use_container_width=True):
                active_bucket["items"].append({"foodId": food_label_to_id[add_f_label], "qty": float(add_f_qty)})
                save_db()
                st.rerun()

            cs1, cs2 = st.columns(2)
            if cs1.button("💾 Save Changes to Bucket", key=f"save_b_{active_bucket['id']}", use_container_width=True):
                active_bucket["name"] = edited_name.strip() or active_bucket["name"]
                active_bucket["defaultSlot"] = edited_slot
                active_bucket["items"] = items_to_keep
                save_db()
                st.success("Bucket updated!")
                st.rerun()

            if cs2.button("🗑️ Delete This Bucket Permanently", key=f"del_b_{active_bucket['id']}", use_container_width=True):
                st.session_state.db["buckets"].pop(b_idx)
                save_db()
                st.success("Bucket deleted!")
                st.rerun()

    # --- RIGHT: SMART AUTO-FETCH FOOD FINDER & DROPDOWN MANAGER ---
    with m_col2:
        st.subheader("🔍 Smart Auto-Fetch Food into Dropdown")
        st.caption("Type any food (e.g., 'Boiled Egg', 'Ragi Dosa', 'Pesarattu', 'Medhu Vadai', 'Filter Coffee') to auto-populate its nutrition and add it to your dropdown.")

        if "fetched_draft" not in st.session_state:
            st.session_state.fetched_draft = {
                "name": "", "unit": "1 serving", "category": "High Protein",
                "cal": 100.0, "pro": 6.0, "carb": 10.0, "fat": 3.0,
                "fib": 1.5, "iron": 1.0, "calcium": 35.0, "magnesium": 25.0
            }

        s_col1, s_col2 = st.columns([3, 1])
        search_food_query = s_col1.text_input("Type Food Name to Fetch Details:", placeholder="e.g., Boiled Egg, Pesarattu, Ragi Dosa, Tofu...")
        if s_col2.button("🔍 Auto-Fetch", use_container_width=True):
            res, status_msg = auto_fetch_food_nutrition(search_food_query)
            if res:
                st.session_state.fetched_draft = res
                st.success(status_msg)
            else:
                st.session_state.fetched_draft["name"] = search_food_query.title()
                st.warning(status_msg)

        with st.form("confirm_fetched_food_form"):
            st.markdown("**Verify or Customize Fetched Details Before Saving to Dropdown:**")
            fd = st.session_state.fetched_draft
            f_name = st.text_input("Food Name", value=fd.get("name", ""))
            u_col, c_col = st.columns(2)
            f_unit = u_col.text_input("Serving Size Unit", value=fd.get("unit", "1 serving"))
            cat_list = ["High Protein", "Tiffin & Staples", "Kuzhambu & Sides", "Shakes & Fruits"]
            f_cat = c_col.selectbox("Category", options=cat_list, index=cat_list.index(fd.get("category", "High Protein")) if fd.get("category") in cat_list else 0)

            n1, n2, n3, n4 = st.columns(4)
            f_cal = n1.number_input("Calories (kcal)", 0.0, 2000.0, float(fd.get("cal", 100.0)), 5.0)
            f_pro = n2.number_input("Protein (g)", 0.0, 150.0, float(fd.get("pro", 6.0)), 0.5)
            f_carb = n3.number_input("Carbs (g)", 0.0, 250.0, float(fd.get("carb", 10.0)), 0.5)
            f_fat = n4.number_input("Fat (g)", 0.0, 150.0, float(fd.get("fat", 3.0)), 0.5)

            m1, m2, m3, m4 = st.columns(4)
            f_fib = m1.number_input("Fiber (g)", 0.0, 50.0, float(fd.get("fib", 1.5)), 0.5)
            f_iron = m2.number_input("Iron (mg)", 0.0, 40.0, float(fd.get("iron", 1.0)), 0.1)
            f_calc = m3.number_input("Calcium (mg)", 0.0, 1200.0, float(fd.get("calcium", 35.0)), 5.0)
            f_mag = m4.number_input("Magnesium (mg)", 0.0, 600.0, float(fd.get("magnesium", 25.0)), 5.0)

            if st.form_submit_button("✅ Save Food to My Dropdown List", use_container_width=True):
                if f_name.strip():
                    st.session_state.db["foods"].insert(0, {
                        "id": f"custom_{int(datetime.now().timestamp())}",
                        "name": f_name.strip(),
                        "unit": f_unit.strip() or "1 serving",
                        "category": f_cat,
                        "cal": f_cal, "pro": f_pro, "carb": f_carb, "fat": f_fat,
                        "fib": f_fib, "iron": f_iron, "calcium": f_calc, "magnesium": f_mag,
                        "potassium": 180.0, "zinc": 0.6, "vitD": 0.2, "vitB12": 0.2, "sodium": 140.0
                    })
                    save_db()
                    st.success(f"Added **{f_name}** to your dropdown for future use!")
                    st.rerun()

# =============================================================================
# TAB 3: WEEKLY (7-DAY) & MONTHLY (30-DAY) TRENDS (ZERO EXTERNAL CHART DEPS)
# =============================================================================
with tab_trends:
    st.subheader("📈 Weekly (7-Day) & Monthly (30-Day) Analytics")
    window_choice = st.radio(
        "Select Window:",
        options=["Last 7 Days (Weekly Trend)", "Last 30 Days (Monthly Trend)"],
        horizontal=True
    )
    num_days = 7 if "7" in window_choice else 30

    rows = []
    for offset in range(num_days - 1, -1, -1):
        d_obj = selected_date - timedelta(days=offset)
        d_str = d_obj.strftime("%Y-%m-%d")
        s = compute_day_summary(d_str)
        rows.append({
            "Date": d_str,
            "Calories Consumed": round(s["cal"]),
            "Dynamic Calorie Target": s["dynamic_cal_target"],
            "Gym Calories Burnt": s["gym_burn"],
            "Net Calories": round(s["net_calories"]),
            "Gym Hours": s["gym_hours"],
            "Protein (g)": round(s["pro"], 1),
            "Protein Target (g)": s["dynamic_pro_target"]
        })

    df_hist = pd.DataFrame(rows).set_index("Date")

    t1, t2 = st.columns(2)
    with t1:
        st.markdown("#### 🔥 Calories Consumed vs. Dynamic Target & Gym Burn")
        st.line_chart(df_hist[["Calories Consumed", "Dynamic Calorie Target", "Gym Calories Burnt"]])
    with t2:
        st.markdown("#### 💪 Daily Protein Intake vs. Target (g)")
        st.bar_chart(df_hist[["Protein (g)", "Protein Target (g)"]])

    st.markdown("#### 🏋️‍♂️ Daily Gym Hours Logged")
    st.bar_chart(df_hist[["Gym Hours"]])

    with st.expander("📋 View Full History Table"):
        st.dataframe(df_hist, use_container_width=True)

# =============================================================================
# TAB 4: BACKUP, RESTORE OR RESET
# =============================================================================
with tab_backup:
    st.subheader("💾 Backup Database or Generate Sample 30-Day History")
    b_left, b_right = st.columns(2)
    with b_left:
        st.download_button(
            "⬇️ Download Full JSON Backup",
            data=json.dumps(st.session_state.db, indent=2),
            file_name=f"si_nutrition_backup_{date.today()}.json",
            mime="application/json",
            use_container_width=True
        )
        up_file = st.file_uploader("⬆️ Restore JSON Backup", type=["json"])
        if up_file and st.button("Restore Database"):
            st.session_state.db = json.load(up_file)
            save_db()
            st.success("Restored!")
            st.rerun()

    with b_right:
        if st.button("🚀 Populate 30 Days Sample Gym & Meal History", use_container_width=True):
            import random
            for off in range(1, 30):
                ds = (date.today() - timedelta(days=off)).strftime("%Y-%m-%d")
                gym_day = (off % 7) in [1, 2, 4, 5]
                st.session_state.db["logs"][ds] = {
                    "meals": {
                        "Breakfast": [{"foodId": "oats_rolled", "qty": 1.0}, {"foodId": "whey_scoop", "qty": 1.0}, {"foodId": "banana_robusta", "qty": 1.0}, {"foodId": "toned_milk", "qty": 1.0}],
                        "Lunch": [{"foodId": "ponni_rice", "qty": 1.25}, {"foodId": "pepper_rasam", "qty": 1.0}, {"foodId": "soya_fry", "qty": 1.0}, {"foodId": "curd_bowl", "qty": 1.0}],
                        "Pre/Post Workout": [{"foodId": "sweet_potato", "qty": 1.0}, {"foodId": "boiled_egg", "qty": 3.0 if gym_day else 2.0}],
                        "Evening Tiffin": [{"foodId": "dosa_plain", "qty": 2.0}, {"foodId": "tiffin_sambar", "qty": 1.0}],
                        "Dinner": [{"foodId": "chapati_wheat", "qty": 3.0}, {"foodId": "paneer_tawa", "qty": 1.0}]
                    },
                    "gym": {"hours": random.choice([1.25, 1.5]) if gym_day else 0.0, "protocol": list(GYM_PROTOCOLS.keys())[0]},
                    "supplements": {"creatine": True, "fish_oil": True, "magnesium": True},
                    "water_liters": 3.5
                }
            save_db()
            st.success("30-day sample history generated! Check Tab 3 ('Weekly & Monthly Trends').")
            st.rerun()
