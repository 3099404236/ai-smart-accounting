# AI Accounting Software Configuration

# Xiaomi MiMo API Configuration
XIAOMI_API_KEY = "your-api-key-here"  # Replace with your Xiaomi MiMo API key
XIAOMI_API_BASE = "https://api.xiaomimimo.com/v1"
XIAOMI_MODEL = "mimo-v2-flash"

# Database Configuration
DATABASE_PATH = "accounting.db"

# Default Item Lifespan (years) - Reference for AI analysis
DEFAULT_LIFESPAN = {
    "phone": 3,
    "computer": 5,
    "laptop": 4,
    "tablet": 4,
    "tv": 8,
    "television": 8,
    "refrigerator": 12,
    "fridge": 12,
    "washing machine": 10,
    "air conditioner": 10,
    "microwave": 8,
    "rice cooker": 6,
    "wok": 10,
    "pan": 10,
    "cookware": 8,
    "furniture": 10,
    "bed": 10,
    "mattress": 8,
    "sofa": 10,
    "desk": 12,
    "table": 12,
    "chair": 8,
    "clothes": 2,
    "clothing": 2,
    "shoes": 2,
    "bag": 5,
    "watch": 10,
    "glasses": 3,
    "bicycle": 8,
    "bike": 8,
    "electric scooter": 5,
    "car": 10,
}

# Expense Keywords (no depreciation needed)
EXPENSE_KEYWORDS = [
    "lunch", "dinner", "breakfast", "meal", "food", "takeout", "coffee", "tea",
    "fruit", "snack", "grocery", "supermarket",
    "taxi", "uber", "lyft", "subway", "metro", "bus", "gas", "fuel",
    "movie", "cinema", "concert", "ticket", "entertainment", "game",
    "phone bill", "internet", "utility", "electricity", "water bill",
    "haircut", "salon", "spa", "massage",
    "hospital", "medicine", "doctor", "pharmacy",
]
