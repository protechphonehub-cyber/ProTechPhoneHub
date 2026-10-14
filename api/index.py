import os, re, json, urllib.parse, urllib.request, urllib.error
from html import escape
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException

# ============================ PRO TECH PHONE HUB ============================
SHOP_NAME     = "Pro Tech Phone Hub"
PHONE_DISPLAY = "0720 890 018"
PHONE_TEL     = "+254720890018"
WA_NUMBER     = "254720890018"
SHOP_EMAIL    = "protechphonehub@gmail.com"
OFFER_NOTE    = "Offer valid till the 20th"
SHEET_WEBHOOK = os.environ.get("PROTECH_SHEET_WEBHOOK", "")
APP_FILE      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "applications.jsonl")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 120 * 1024 * 1024

def e(v): return escape(str(v), quote=True)
def slugify(v):
    v = re.sub(r"[^a-z0-9]+", "-", str(v).lower().strip())
    return re.sub(r"-+", "-", v).strip("-")
def money(a):
    try: return f"KES {int(a):,}"
    except Exception: return f"KES {a}"
def truncate(t, l):
    t = str(t); return t if len(t) <= l else t[:l].strip() + "…"
def clean_text(v): return re.sub(r"\s+", " ", str(v)).strip()
def whatsapp_link(m): return "https://wa.me/" + WA_NUMBER + "?text=" + urllib.parse.quote(m)

def placeholder_image(text):
    clean = re.sub(r"[^A-Za-z0-9 ]+", "", str(text))[:18].strip() or "ProTech"
    clean = escape(clean, quote=True)
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' width='900' height='900'>"
           "<rect width='100%' height='100%' fill='#faf7f2'/>"
           "<rect x='18' y='18' width='864' height='864' rx='430' ry='300' fill='#f0e6da'/>"
           f"<text x='50%' y='52%' fill='#4b2440' font-family='Georgia' font-size='46' font-weight='700' text-anchor='middle'>{clean}</text>"
           "<text x='50%' y='63%' fill='#b95c72' font-family='Georgia' font-size='24' text-anchor='middle'>Pro Tech Phone Hub</text></svg>")
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg, safe="")

def post_to_google_sheet(payload):
    if not SHEET_WEBHOOK: return False
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(SHEET_WEBHOOK, data=body, method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (ProTechPhoneHub)"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            status = getattr(r, "status", 200)
    except urllib.error.HTTPError as h:
        status = h.code
    except Exception:
        return False
    return status in (200, 302, 303)

def save_application_local(payload):
    try:
        trim = {k: v for k, v in payload.items() if k != "data"}
        if "data" in payload: trim["file_received"] = True
        trim["saved_at"] = datetime.now(timezone(timedelta(hours=3))).isoformat()
        with open(APP_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(trim, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False

# ------------------------- POLE POLE STOCK (ProTech wording) -------------------------
def L(slug, name, apply_name, image, tagline, weekly, deposit, storage, colors, specs, review, storage_pricing=None, condition=None):
    d = {"slug": slug, "name": name, "apply_name": apply_name, "image": image, "tagline": tagline,
         "weekly": weekly, "deposit": deposit, "storage": storage, "colors": colors, "specs": specs, "review": review}
    if storage_pricing: d["storage_pricing"] = storage_pricing
    if condition: d["condition"] = condition
    return d

AM  = "https://m.media-amazon.com/images/I/"
MOP = "https://mophones.co/cdn/shop/"

LIPA_PRODUCTS = [
L("motorola-g-power", "Motorola G Power", "Motorola G Power 2023",
  MOP + "files/motorola-moto-g-power-5g-1_673x.jpg?v=1770894988",
  'Two-day battery • 5G • Roomy 6.5" screen', 560, 4299, ["128GB"], ["Mineral Black", "Bright White"],
  {"Network": "5G ready", "Screen": '6.5" IPS LCD, 120Hz', "System": "Android 16", "Battery": "5000mAh with fast charging"},
  (5, "Wanjiku M.", "PP-101", "Battery ya kitu! Two full days out and I never carry a power bank anymore.")),
L("motorola-g-stylus", "Motorola G Stylus", "Motorola G Stylus 2024",
  AM + "412KEd+cz3L.AC_US1000.jpg?v=1771506465",
  'Built-in pen • 5G • Silky 120Hz P-OLED', 910, 6999, ["128GB", "256GB"], ["Caramel Latte", "Scarlet Wave"],
  {"Network": "5G ready", "Screen": '6.7" P-OLED, 120Hz', "System": "Android 16", "Battery": "5000mAh, fast + wireless charging"},
  (5, "Achieng O.", "PP-102", "The pen makes my notes and sketches so easy. Screen colours are pure magic."),
  storage_pricing={"128GB": {"weekly": 910, "deposit": 6999}, "256GB": {"weekly": 1040, "deposit": 7999}}),
L("samsung-galaxy-s21-fe", "Samsung Galaxy S21 FE 5G", "Samsung Galaxy S21 FE 5G",
  AM + "61PPEjwAkYL._AC_SY300_SX300_QL70_FMwebp_.jpg",
  'The people\'s flagship • 5G • 120Hz AMOLED', 970, 7499, ["128GB"], ["Graphite", "White", "Lavender", "Olive"],
  {"Network": "5G ready", "Screen": '6.4" Dynamic AMOLED 2X, 120Hz', "System": "Android 15, upgradable", "Battery": "4500mAh, fast + wireless charging"},
  (5, "Peter K.", "PP-103", "Feels like a flagship, priced like a friend. Smooth screen and clean battery life.")),
L("samsung-galaxy-note-20", "Samsung Galaxy Note 20", "Samsung Note 20 5G",
  MOP + "files/0c5ffb9f-1e94-480c-bdb1-71566919cc1d-1_46397bdd-1274-44a3-b4e9-52df8ac4fdbc_600x.jpg?v=1703753426",
  'S-Pen elegance • 5G • Big 6.7" AMOLED', 1160, 8999, ["128GB"], ["Black", "Green", "Rose-Gold"],
  {"Network": "5G ready", "Screen": '6.7" Super AMOLED Plus, HDR10+', "System": "Android 15, upgradable", "Battery": "4300mAh, fast + wireless charging"},
  (5, "Daniel E.", "PP-104", "I sign documents and take notes with the S-Pen daily. Office life became soft.")),
L("samsung-galaxy-s21-plus", "Samsung Galaxy S21+", "Samsung Galaxy S21 Plus 5G",
  MOP + "products/BLACK_d72adc1a-b989-4cf6-a641-b2919ad0a2de_500x.jpg?v=1676990538",
  'All-day battery • 5G • 120Hz beauty', 1110, 8499, ["128GB", "256GB"], ["Black", "Silver", "Purple"],
  {"Network": "5G ready", "Screen": '6.7" Dynamic AMOLED 2X, 120Hz', "System": "Android 15, upgradable", "Battery": "4800mAh, fast + wireless charging"},
  (5, "Samuel O.", "PP-105", "Carries me through long hospital shifts and still has juice for movies at night."),
  storage_pricing={"128GB": {"weekly": 1110, "deposit": 8499}, "256GB": {"weekly": 1420, "deposit": 10999}}),
L("samsung-galaxy-s22-plus", "Samsung Galaxy S22+", "Samsung Galaxy S22 Plus 5G",
  AM + "714oVGJtWeL.AC_SY300_SY300_QL70_FMwebp.jpg",
  'Compact flagship • 5G • Night-loving camera', 1230, 9499, ["128GB"], ["Phantom Black", "Lavender", "Green"],
  {"Network": "5G ready", "Screen": '6.6" Dynamic AMOLED 2X, 120Hz', "System": "Android 16, upgradable", "Battery": "4500mAh, fast + wireless charging"},
  (5, "Grace W.", "PP-106", "Perfect size for my hand and my bag. Night photos come out shockingly clean.")),
L("samsung-galaxy-s20-ultra", "Samsung Galaxy S20 Ultra", "Samsung Galaxy S20 Ultra",
  MOP + "files/S20Ultra1_455x.jpg?v=1718780519",
  '100x zoom beast • 5G • Cinema 6.9" screen', 1230, 9499, ["128GB"], ["Black", "Grey"],
  {"Network": "5G ready", "Screen": '6.9" Dynamic AMOLED 2X, 120Hz', "System": "Android 15, upgradable", "Battery": "5000mAh, fast + wireless charging"},
  (5, "Brian M.", "PP-107", "That space zoom is entertainment on its own. Streaming on this screen is cinema.")),
L("samsung-galaxy-s21-ultra", "Samsung Galaxy S21 Ultra", "Samsung Galaxy S21 Ultra",
  MOP + "files/8322653a-f2b7-44cf-a74c-6336bcec9f43-1_cadd4530-09b4-449e-aa1d-3894bad6e808_1024x.jpg?v=1700145645",
  'Pro cameras, S-Pen ready • 5G • 120Hz', 1490, 11499, ["128GB"], ["Black", "Silver"],
  {"Network": "5G ready", "Screen": '6.8" Dynamic AMOLED 2X, 120Hz', "System": "Android 15, upgradable", "Battery": "5000mAh, fast + wireless charging"},
  (5, "David K.", "PP-108", "My outdoor photos look professional. The zoom still beats many newer phones.")),
L("apple-iphone-12-mini", "Apple iPhone 12 Mini", "Apple iPhone 12 Mini",
  AM + "61bbqGftbUL.AC_SY879.jpg",
  'Pocket-sized 5G iPhone • OLED • MagSafe', 1290, 9999, ["128GB"], ["Black", "Purple", "Blue", "Green", "Red", "White"],
  {"Network": "5G ready", "Screen": '5.4" Super Retina XDR OLED', "System": "iOS 26, upgradable", "Battery": "2227mAh, fast charge + MagSafe"},
  (5, "Simon A.", "PP-109", "Small, light and fast — fits every pocket and every handbag perfectly.")),
L("apple-iphone-12", "Apple iPhone 12", "Apple iPhone 12",
  MOP + "products/12black_640x.jpg?v=1674896241",
  'The people\'s iPhone • 5G • Crisp OLED', 1540, 11899, ["128GB", "256GB"], ["Black", "Purple", "Blue", "Green", "Red", "White"],
  {"Network": "5G ready", "Screen": '6.1" Super Retina XDR OLED', "System": "iOS 26, upgradable", "Battery": "2815mAh, fast charge + MagSafe"},
  (5, "Faith W.", "PP-110", "My colour choice turns heads everywhere. Fast, clean and the camera loves me."),
  storage_pricing={"128GB": {"weekly": 1540, "deposit": 11899}, "256GB": {"weekly": 1480, "deposit": 18199}}),
L("samsung-galaxy-note-20-ultra", "Samsung Galaxy Note 20 Ultra", "Samsung Note 20 Ultra",
  MOP + "files/NOte20Black_23da7f6b-cc29-41a0-9eac-63d0385cc238_500x.jpg?v=1718362656",
  'The legendary giant • 120Hz • S-Pen inside', 1550, 11999, ["128GB"], ["Black", "White", "Rose-Gold"],
  {"Network": "5G ready", "Screen": '6.9" Dynamic AMOLED 2X, 120Hz', "System": "Android 15, upgradable", "Battery": "4500mAh, fast + wireless charging"},
  (5, "Cynthia W.", "PP-111", "Buttery 120Hz screen and that bronze S-Pen — still the most beautiful Note ever.")),
L("samsung-galaxy-s22-ultra", "Samsung Galaxy S22 Ultra", "Samsung Galaxy S22 Ultra",
  MOP + "files/Screenshot_2025-03-20_at_15.05.15_1010x.png?v=1742472440",
  'S-Pen built in • 5G • 100x pro camera', 1900, 23399, ["256GB", "512GB"], ["Black", "Purple", "Green"],
  {"Network": "5G ready", "Screen": '6.8" Dynamic AMOLED 2X, 120Hz', "System": "Android 16, upgradable", "Battery": "5000mAh, fast + wireless charging"},
  (5, "Benard O.", "PP-112", "I sketch my architectural ideas straight on the screen. Pole pole made it possible.")),
L("apple-iphone-12-pro-max", "Apple iPhone 12 Pro Max", "Apple iPhone 12 Pro Max",
  AM + "41SLL9Zws6L.AC_SY300_SY300_QL70_FMwebp.jpg",
  'Big screen, big battery • Pro cameras • 5G', 1960, 24099, ["256GB"], ["Pacific Blue", "Graphite", "Gold", "Silver"],
  {"Network": "5G ready", "Screen": '6.7" Super Retina XDR OLED', "System": "iOS 26, upgradable", "Battery": "3687mAh, fast charge + MagSafe"},
  (5, "Kevin O.", "PP-113", "Business calls, photos, everything — the big battery simply refuses to die early.")),
L("apple-iphone-13-pro-max", "Apple iPhone 13 Pro Max", "Apple iPhone 13 Pro Max",
  MOP + "products/apple_iphone_13_pro_max_gold_image_0_1024x.jpg?v=1674389404",
  '120Hz ProMotion • Marathon battery • 5G', 2190, 26899, ["256GB", "512GB", "1TB"], ["Blue", "Black", "Gold", "Silver", "Alpine Green"],
  {"Network": "5G ready", "Screen": '6.7" Super Retina XDR OLED, 120Hz', "System": "iOS 26, upgradable", "Battery": "4352mAh, fast charge + MagSafe"},
  (5, "Gladys M.", "PP-114", "The blue is even prettier in person, and scrolling on 120Hz spoils you forever.")),
L("samsung-galaxy-s23-ultra", "Samsung Galaxy S23 Ultra", "Samsung Galaxy S23 Ultra",
  MOP + "files/S23Ultra1_1024x.jpg?v=1718781685",
  'Night photos that shock • S-Pen • 5G', 2190, 26899, ["256GB", "512GB"], ["Black", "Green", "Cream"],
  {"Network": "5G ready", "Screen": '6.8" Dynamic AMOLED 2X, 120Hz', "System": "Android 16, upgradable", "Battery": "5000mAh, fast + wireless charging"},
  (5, "Joseph O.", "PP-115", "Concert photos at night look like daylight. Best phone deal I found in Nairobi.")),
L("apple-iphone-14-pro-max", "Apple iPhone 14 Pro Max", "Apple iPhone 14 Pro Max",
  MOP + "files/Screenshot_2025-05-29_at_09.05.01_776x.png?v=1748499274",
  'Dynamic Island • 48MP • All-day battery', 2560, 31499, ["256GB"], ["Space Black", "Deep Purple", "Gold", "Silver"],
  {"Network": "5G ready", "Screen": '6.7" LTPO Super Retina XDR OLED', "System": "iOS 26, upgradable", "Battery": "4323mAh, fast charge + MagSafe"},
  (5, "Rebecca C.", "PP-116", "Deep Purple is elegance itself. Screen is vibrant and everything glides.")),
L("samsung-galaxy-s24-ultra", "Samsung Galaxy S24 Ultra", "Samsung Galaxy S24 Ultra",
  MOP + "files/S24_Ultra1_992x.png?v=1735648520",
  'Galaxy AI flagship • S-Pen • Titan frame', 2700, 33199, ["256GB", "512GB"], ["Black", "Green", "Grey"],
  {"Network": "5G ready", "Screen": '6.8" Dynamic AMOLED 2X, 120Hz', "System": "Android 16, upgradable", "Battery": "5000mAh, fast + wireless charging"},
  (5, "Michael K.", "PP-117", "Live translation saves my business meetings weekly. Worth every shilling.")),
L("apple-iphone-15-pro-max", "Apple iPhone 15 Pro Max", "Apple iPhone 15 Pro Max",
  MOP + "files/Screenshot2025-11-04at16.05.25_ad9bcddb-df5e-4e98-9251-113e32673b12_770x.png?v=1762278234",
  'Titanium light • USB-C • 5x zoom • 5G', 3100, 38099, ["256GB"], ["Space Black", "Natural Titanium", "Blue Titanium", "White Titanium"],
  {"Network": "5G ready", "Screen": '6.7" LTPO Super Retina XDR OLED', "System": "iOS 26, upgradable", "Battery": "4422mAh, fast charge + MagSafe"},
  (5, "Stella W.", "PP-118", "Titanium finish is jewellery. My video content stepped into another league.")),
L("samsung-galaxy-s25-ultra", "Samsung Galaxy S25 Ultra", "Samsung S25 Ultra",
  MOP + "files/s25_ultra_300x.png?v=1772294113",
  'The smartest Galaxy • AI everywhere • S-Pen', 3300, 40599, ["256GB"], ["Black", "Titanium Black", "Titanium White", "Silver", "Titanium SilverBlue"],
  {"Network": "5G ready", "Screen": '6.9" Dynamic LTPO AMOLED 2X, 120Hz', "System": "Android 16, upgradable", "Battery": "5000mAh, fast + wireless charging"},
  (5, "Dennis M.", "PP-119", "Upgraded from S23 Ultra — the AI speed difference is honestly crazy.")),
L("apple-iphone-16-pro-max", "Apple iPhone 16 Pro Max", "Apple iPhone 16 Pro Max",
  AM + "51Vs7ZwpSpL.AC_SY300_SY300_QL70_FMwebp.jpg",
  'Brand new • A18 Pro • 48MP fusion • 5G', 3840, 47199, ["256GB"], ["Desert Titanium", "Natural Titanium", "White Titanium", "Black Titanium"],
  {"Network": "5G ready", "Screen": '6.9" LTPO Super Retina XDR OLED, 120Hz', "System": "iOS 26, upgradable", "Battery": "4685mAh, fast charge + MagSafe"},
  (5, "Wanjiru K.", "PP-120", "Unboxing felt like a gift to myself. Fast, gorgeous and future-proof."),
  condition="New"),
]

for p in LIPA_PRODUCTS:
    if p["slug"] == "samsung-galaxy-s20-ultra":
        p.update(weekly=1160, deposit=8999, original_weekly=1230, original_deposit=9499, offer_badge="Offer till 20th")
    elif p["slug"] == "samsung-galaxy-note-20":
        p.update(weekly=1040, deposit=7999, original_weekly=1160, original_deposit=8999, offer_badge="Offer till 20th")
    elif p["slug"] == "samsung-galaxy-s24-ultra":
        p.update(weekly=2600, deposit=31999, original_weekly=2700, original_deposit=33199, offer_badge="Offer till 20th")

def price_for(p, s):
    sp = p.get("storage_pricing", {})
    return sp[s] if s in sp else {"weekly": p["weekly"], "deposit": p["deposit"]}
def min_weekly(p):
    vals = [p.get("weekly", 0)]
    for v in p.get("storage_pricing", {}).values(): vals.append(v.get("weekly", p.get("weekly", 0)))
    return min(vals)
LIPA_PRODUCTS.sort(key=lambda p: (min_weekly(p), p.get("deposit", 0)))
for lp in LIPA_PRODUCTS:
    lp["type"] = "lipa"; lp["model"] = lp["name"]
    lp.setdefault("condition", "Ex-UK")
    lp["stock"] = "In Stock"

# ------------------------- CASH STOCK — POSTER PRICES + YOUR PHOTOS -------------------------
CASH_CATEGORIES = []
CASH_PRODUCTS = {}
def add_cat(name, note):
    CASH_CATEGORIES.append({"name": name, "note": note, "products": []})
def C(cat, name, price, spec, img):
    slug = slugify("pt-" + name)
    prod = {"slug": slug, "type": "cash", "model": name, "name": name, "price": int(price),
            "specs": clean_text(spec), "image": clean_text(img), "category_name": cat}
    CASH_PRODUCTS[slug] = prod
    for c in CASH_CATEGORIES:
        if c["name"] == cat: c["products"].append(prod)
    return prod

S1 = "Samsung Galaxy S • Fold • Flip • Note"
S2 = "Samsung Galaxy A Series"
S3 = "Apple iPhone"
add_cat(S1, "Flagship power, foldable magic and the legendary S-Pen line — every unit original, tested and ready.")
add_cat(S2, "Everyday heroes with big batteries and pretty screens, at prices that make you smile.")
add_cat(S3, "From the beloved 11 Pro to the 16 Pro Max — genuine iPhones, battery-health checked.")

C(S1,"Samsung Galaxy S25 Ultra 512GB",127000,'6.8" 120Hz AMOLED • Snapdragon 8 Elite • 200MP cam • 5000mAh',AM+"51ybW3eCRhL.AC_SX679.jpg")
C(S1,"Samsung Galaxy S25 Ultra 256GB",109000,'6.8" 120Hz AMOLED • Snapdragon 8 Elite • 200MP cam • 5000mAh',AM+"51ybW3eCRhL.AC_SX679.jpg")
C(S1,"Samsung Galaxy S26 Ultra 256GB",128000,'6.9" 144Hz AMOLED • Snapdragon 8 Elite Gen 5 • 200MP cam • 5000mAh',AM+"618F1CD-gbL.AC_SX679.jpg")
C(S1,"Samsung Galaxy S26 Ultra 512GB",148000,'6.9" 144Hz AMOLED • Snapdragon 8 Elite Gen 5 • 200MP cam • 5000mAh',AM+"618F1CD-gbL.AC_SX679.jpg")
C(S1,"Samsung Galaxy S26 256GB",99000,'6.36" 120Hz AMOLED • Snapdragon 8 Elite Gen 5 • 50MP cam • 4300mAh',AM+"61q1dJxGowL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy S26 Plus 256GB",109000,'6.7" 120Hz AMOLED • Snapdragon 8 Elite Gen 5 • 50MP cam • 4900mAh',AM+"61q1dJxGowL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy S26 Plus 512GB",121000,'6.7" 120Hz AMOLED • Snapdragon 8 Elite Gen 5 • 50MP cam • 4900mAh',AM+"61q1dJxGowL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy S24 Ultra 512GB",96999,'6.8" 120Hz AMOLED • Snapdragon 8 Gen 3 • 200MP cam • 5000mAh',AM+"71WcjsOVOmL.AC_SX679.jpg")
C(S1,"Samsung Galaxy S24 Ultra 256GB",89999,'6.8" 120Hz AMOLED • Snapdragon 8 Gen 3 • 200MP cam • 5000mAh',AM+"71WcjsOVOmL.AC_SX679.jpg")
C(S1,"Samsung Galaxy S23 Ultra 512GB",77999,'6.8" 120Hz AMOLED • Snapdragon 8 Gen 2 • 200MP cam • 5000mAh',AM+"71iBKcLHXFL.AC_SX679.jpg")
C(S1,"Samsung Galaxy S23 Ultra 256GB",72500,'6.8" 120Hz AMOLED • Snapdragon 8 Gen 2 • 200MP cam • 5000mAh',AM+"71iBKcLHXFL.AC_SX679.jpg")
C(S1,"Samsung Galaxy S23 Plus 256GB",42000,'6.6" 120Hz AMOLED • Snapdragon 8 Gen 2 • 50MP cam • 4700mAh',AM+"51yz4TrDNdL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy S22 Ultra 256GB",58500,'6.8" 120Hz AMOLED • Snapdragon 8 Gen 1 • 108MP cam • S-Pen',AM+"613Fp7fknhL.AC_SX679.jpg")
C(S1,"Samsung Galaxy S22 Ultra 512GB",63500,'6.8" 120Hz AMOLED • Snapdragon 8 Gen 1 • 108MP cam • S-Pen',AM+"613Fp7fknhL.AC_SX679.jpg")
C(S1,"Samsung Galaxy S22 Plus 256GB",38499,'6.6" 120Hz AMOLED • Snapdragon 8 Gen 1 • 50MP cam • 4500mAh',AM+"714oVGJtWeL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy Fold 6 256GB",97000,'7.6" foldable 120Hz • Snapdragon 8 Gen 3 • 50MP cam',AM+"61Jjxzg7Q1L.AC_SX679.jpg")
C(S1,"Samsung Galaxy Fold 5 512GB",79000,'7.6" foldable 120Hz • Snapdragon 8 Gen 2 • 50MP cam',AM+"518OMBP4J7L.AC_SX679.jpg")
C(S1,"Samsung Galaxy Fold 5 256GB",76000,'7.6" foldable 120Hz • Snapdragon 8 Gen 2 • 50MP cam',AM+"518OMBP4J7L.AC_SX679.jpg")
C(S1,"Samsung Galaxy Fold 4 256GB",67000,'7.6" foldable 120Hz • Snapdragon 8+ Gen 1 • 50MP cam',AM+"81TH5W29HgL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy Fold 4 512GB",70500,'7.6" foldable 120Hz • Snapdragon 8+ Gen 1 • 50MP cam',AM+"81TH5W29HgL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy Fold 3 512GB",63000,'7.6" foldable 120Hz • Snapdragon 888 • 12MP cam',AM+"71MFE2UY6-L.AC_SX679.jpg")
C(S1,"Samsung Galaxy Fold 3 256GB",59000,'7.6" foldable 120Hz • Snapdragon 888 • 12MP cam',AM+"71MFE2UY6-L.AC_SX679.jpg")
C(S1,"Samsung Galaxy Flip 7 256GB",82000,'6.9" foldable 120Hz • Snapdragon 8 Elite • 50MP cam',AM+"61mSUSY4xWL.AC_SX679.jpg")
C(S1,"Samsung Galaxy Flip 6 512GB",63000,'6.7" foldable 120Hz • Snapdragon 8 Gen 3 • 50MP cam',AM+"61mSUSY4xWL.AC_SX679.jpg")
C(S1,"Samsung Galaxy Flip 5 512GB",52000,'6.7" foldable 120Hz • Snapdragon 8 Gen 2 • 12MP cam',AM+"51Jzh8XTxQL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy Flip 4 512GB",42000,'6.7" foldable 120Hz • Snapdragon 8+ Gen 1 • 12MP cam',AM+"51Ggw4SLTUL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy Flip 4 256GB",40999,'6.7" foldable 120Hz • Snapdragon 8+ Gen 1 • 12MP cam',AM+"51Ggw4SLTUL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy Note 20 Ultra 256GB",48999,'6.9" 120Hz AMOLED • Snapdragon 865+ • 108MP • S-Pen',AM+"51UG-WVTAOL.AC_SX679.jpg")
C(S1,"Samsung Galaxy Note 20 256GB",34499,'6.7" AMOLED • Snapdragon 865+ • 64MP cam • S-Pen',AM+"71hB8cEDLYL.AC_SY300_SX300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy Note 10 256GB",33999,'6.3" Dynamic AMOLED • Snapdragon 855 • S-Pen',AM+"61kJwlX9NOL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy Note 10 Plus 256GB",39999,'6.8" Dynamic AMOLED • Snapdragon 855 • S-Pen',AM+"517MGkvMhXL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy S21 Plus 256GB",35599,'6.7" 120Hz AMOLED • Snapdragon 888 • 12MP cam • 4800mAh',AM+"61-QMCHyUES.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy S21FE 128GB",32499,'6.4" 120Hz AMOLED • Snapdragon 888 • 12MP cam • 4500mAh',AM+"616kK0b+d+L.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy S21 Ultra 256GB",45999,'6.8" 120Hz AMOLED • Snapdragon 888 • 108MP cam',AM+"61fNCOu3kaL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1,"Samsung Galaxy S20 Ultra 256GB",37999,'6.9" 120Hz AMOLED • Snapdragon 865 • 108MP cam',MOP+"files/S20Ultra1_455x.jpg?v=1718780519")
C(S1,"Samsung Galaxy S10 4G 128GB",32000,'6.1" Dynamic AMOLED • Snapdragon 855 • 12MP cam',"https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s10.jpg")
C(S1,"Samsung Galaxy S10 5G 256GB",33500,'6.7" Dynamic AMOLED • Snapdragon 855 • 12MP cam',"https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s10-5g.jpg")
C(S2,"Samsung Galaxy A57 256GB / 8GB",54500,'6.7" 120Hz AMOLED • 50MP OIS • 5000mAh • 45W',AM+"51mD59m3QKL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A37 256GB / 8GB",45999,'6.6" 120Hz AMOLED • 50MP cam • 5000mAh',AM+"51PfnB-QHxL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A56 256GB",49500,'6.6" 120Hz Super AMOLED • 50MP OIS • 5000mAh',AM+"618oogho7PL.AC_SY300_SX300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A06 64GB / 4GB",15999,'6.7" LCD • 50MP cam • 5000mAh',AM+"518iRq2DZKL.AC_SX679.jpg")
C(S2,"Samsung Galaxy A06 128GB / 4GB",19000,'6.7" LCD • 50MP cam • 5000mAh',AM+"518iRq2DZKL.AC_SX679.jpg")
C(S2,"Samsung Galaxy A07 64GB / 4GB",19000,'6.7" 90Hz LCD • 50MP cam • 5000mAh',AM+"41uTZLTSxdL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A07 128GB / 4GB",21300,'6.7" 90Hz LCD • 50MP cam • 5000mAh',AM+"41uTZLTSxdL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A07s 64GB / 4GB",19499,'6.7" 90Hz LCD • 50MP cam • 5000mAh',AM+"41uTZLTSxdL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A17 128GB / 4GB",25000,'6.5" 90Hz Super AMOLED • 50MP cam • 5000mAh',AM+"61urRuuqCiL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A17 128GB / 6GB",28300,'6.5" 90Hz Super AMOLED • 50MP cam • 5000mAh',AM+"61urRuuqCiL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A16 128GB / 4GB",23100,'6.5" 90Hz Super AMOLED • 50MP cam • 5000mAh',AM+"71KGkQ+KOKL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A17 256GB / 8GB",35000,'6.5" 90Hz Super AMOLED • 50MP cam • 5000mAh',AM+"61urRuuqCiL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A26 256GB / 8GB",36500,'6.5" 120Hz Super AMOLED • 50MP cam • 5000mAh',AM+"51ZmengIdlL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A27 128GB / 6GB",35500,'6.5" 120Hz Super AMOLED • 50MP cam • 5000mAh',AM+"41Md7kOXowL.SY300_SX300_QL70_FMwebp.jpg")
C(S2,"Samsung Galaxy A27 256GB / 8GB",42000,'6.5" 120Hz Super AMOLED • 50MP cam • 5000mAh',AM+"41Md7kOXowL.SY300_SX300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 16 Pro Max 256GB",111499,'6.9" 120Hz OLED • A18 Pro • 48MP trio • Titanium',AM+"51Vs7ZwpSpL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 15 Pro Max 256GB",96499,'6.7" 120Hz OLED • A17 Pro • 48MP • Titanium',AM+"81OdN4WB6VL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 15 128GB",66000,'6.1" OLED • A16 • 48MP • USB-C',AM+"51PtFHUPjBL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 14 Pro Max 256GB",77000,'6.7" 120Hz OLED • A16 • 48MP • Dynamic Island',AM+"51wqFSpP20L.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 14 Pro 256GB",71999,'6.1" 120Hz OLED • A16 • 48MP • Dynamic Island',AM+"61XO4bORHUL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 14 Plus 128GB",59999,'6.7" OLED • A15 • 12MP dual cam',AM+"513-nH35+UL.AC_SX300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 14 128GB",57500,'6.1" OLED • A15 • 12MP dual cam',AM+"61aEBeER-+L.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 14 256GB",59000,'6.1" OLED • A15 • 12MP dual cam',AM+"61aEBeER-+L.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 13 Pro Max 256GB",69500,'6.7" 120Hz OLED • A15 • 12MP triple cam',AM+"61ERgud-SbL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 13 128GB",47500,'6.1" OLED • A15 • 12MP dual cam',AM+"518rwCXZ0SL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 13 256GB",49500,'6.1" OLED • A15 • 12MP dual cam',AM+"518rwCXZ0SL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 12 128GB",41000,'6.1" OLED • A14 • 12MP dual cam',AM+"61bbqGftbUL.AC_SY879.jpg")
C(S3,"Apple iPhone 12 Pro 128GB",46500,'6.1" OLED • A14 • 12MP triple cam',AM+"51q3qjXRz2L.AC_SY300_SX300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 12 Pro Max 256GB",56999,'6.7" OLED • A14 • 12MP triple cam',AM+"41SLL9Zws6L.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 12 Pro 256GB",49999,'6.1" OLED • A14 • 12MP triple cam',AM+"51q3qjXRz2L.AC_SY300_SX300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 11 Pro Max 256GB",44999,'6.5" OLED • A13 • 12MP triple cam',AM+"61G2REmnBIL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 11 Pro Max 512GB",46500,'6.5" OLED • A13 • 12MP triple cam',AM+"61G2REmnBIL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3,"Apple iPhone 11 Pro 256GB",42999,'5.8" OLED • A13 • 12MP triple cam',AM+"61UC1mk6dfL.AC_SY300_SY300_QL70_FMwebp.jpg")

PRODUCTS_BY_SLUG = {}
for lp in LIPA_PRODUCTS: PRODUCTS_BY_SLUG[lp["slug"]] = lp
for cp in CASH_PRODUCTS.values(): PRODUCTS_BY_SLUG[cp["slug"]] = cp

SEARCH_INDEX = []
for p in LIPA_PRODUCTS:
    pr = price_for(p, p["storage"][0])
    SEARCH_INDEX.append({"name": p["name"], "slug": p["slug"], "text": (p["name"] + " " + " ".join(p["storage"]) + " " + p["tagline"] + " pole pole weekly").lower(),
                         "line": f"{p['name']} — {money(pr['deposit'])} deposit, {money(pr['weekly'])}/week"})
for p in CASH_PRODUCTS.values():
    SEARCH_INDEX.append({"name": p["name"], "slug": p["slug"], "text": (p["name"] + " " + p["specs"] + " cash").lower(),
                         "line": f"{p['name']} — {money(p['price'])} cash"})

def search_items(q, limit=4):
    terms = [t for t in re.findall(r"[a-z0-9]+", str(q).lower()) if len(t) > 2]
    if not terms: return []
    scored = []
    for it in SEARCH_INDEX:
        s = sum(1 for t in terms if t in it["text"])
        if s: scored.append((s, it))
    scored.sort(key=lambda x: -x[0])
    return [i for _, i in scored[:limit]]

# ============================ PROTECH DESIGN SYSTEM ============================
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;0,9..144,900;1,9..144,600&family=Manrope:wght@400;500;600;700;800&family=Parisienne&display=swap');
:root{--ink:#241423;--plum:#4b2440;--plum2:#6d3b5e;--rose:#b95c72;--rose2:#d99aa8;--champ:#d8b98b;--cream:#faf7f2;--paper:#fffdf9;--sand:#efe7dc;--green:#1c7a4f;--line:#e8ddd2;--shadow:0 18px 44px rgba(75,36,64,.10);--serif:'Fraunces',Georgia,serif;--sans:'Manrope',sans-serif;--script:'Parisienne',cursive}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--sans);color:var(--ink);background:var(--cream);line-height:1.65;overflow-x:hidden}
a{color:inherit;text-decoration:none}img{max-width:100%;display:block}
button,input,select,textarea{font:inherit}
.container{width:min(1160px,92%);margin:auto}
.section{padding:64px 0}
.muted{color:#8a6f7f}
.hidden{display:none!important}
/* utility bar */
.utilbar{background:var(--ink);color:#e9d8e2;font-size:12.5px;letter-spacing:.06em}
.utilbar .container{display:flex;justify-content:space-between;gap:14px;padding:8px 0;flex-wrap:wrap}
.utilbar b{color:var(--champ);font-weight:700}
/* header */
.header{position:sticky;top:0;z-index:1100;background:var(--paper);border-bottom:1px solid var(--line)}
.header-inner{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 0}
.logo{display:flex;flex-direction:column;line-height:1}
.logo b{font-family:var(--serif);font-weight:900;font-size:24px;color:var(--plum);letter-spacing:-.02em}
.logo i{font-family:var(--script);font-style:normal;font-size:17px;color:var(--rose);margin-top:2px}
.nav{display:flex;align-items:center;gap:22px}
.nav a{font-weight:700;font-size:13.5px;letter-spacing:.08em;text-transform:uppercase;color:#6f5666;position:relative}
.nav a:after{content:"";position:absolute;left:0;right:100%;bottom:-6px;height:2px;background:var(--rose);transition:.25s}
.nav a:hover:after,.nav a.active:after{right:0}
.nav a.active{color:var(--plum)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:13px 24px;border-radius:6px;border:none;font-weight:800;font-size:14px;cursor:pointer;transition:.25s;white-space:nowrap;letter-spacing:.02em}
.btn-rose{color:#fff;background:var(--rose);box-shadow:0 12px 26px rgba(185,92,114,.28)}
.btn-rose:hover{background:#a34c62;transform:translateY(-2px)}
.btn-ink{color:var(--cream);background:var(--ink)}
.btn-ink:hover{background:var(--plum);transform:translateY(-2px)}
.btn-line{color:var(--plum);border:1.5px solid var(--plum);background:transparent}
.btn-line:hover{background:var(--plum);color:var(--cream)}
.btn-wa{color:#08130c;background:#25d366}
.btn-wa:hover{filter:brightness(.95)}
.btn-sm{padding:9px 15px;font-size:12.5px}
.hamburger{display:none;width:44px;height:44px;border-radius:8px;border:1px solid var(--line);background:#fff;font-size:19px;cursor:pointer}
/* hero collage */
.hero{padding:70px 0 40px;background:linear-gradient(180deg,var(--paper),var(--cream));position:relative;overflow:hidden}
.hero:before{content:"";position:absolute;top:-120px;right:-120px;width:420px;height:420px;border-radius:50%;background:radial-gradient(circle,rgba(216,185,139,.25),transparent 65%)}
.hero-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:40px;align-items:center;position:relative}
.kicker{font-size:12px;font-weight:800;letter-spacing:.22em;text-transform:uppercase;color:var(--rose)}
.hero h1{font-family:var(--serif);font-weight:900;font-size:clamp(2.4rem,5.4vw,4.3rem);line-height:1.03;letter-spacing:-.03em;color:var(--ink);margin:14px 0 16px}
.hero h1 em{font-family:var(--script);font-style:normal;font-weight:400;color:var(--rose);font-size:.92em}
.hero p.lead{max-width:560px;color:#6f5666;font-size:1.05rem}
.hero-actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px}
.hero-stats{display:flex;gap:26px;margin-top:30px;flex-wrap:wrap}
.hstat b{display:block;font-family:var(--serif);font-size:26px;font-weight:900;color:var(--plum)}
.hstat span{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#8a6f7f;font-weight:700}
.fan{position:relative;height:430px}
.fimg{position:absolute;width:225px;height:310px;object-fit:contain;background:linear-gradient(180deg,#fff,var(--sand));border:1px solid var(--line);border-radius:120px 120px 18px 18px;box-shadow:var(--shadow);padding:16px}
.f1{left:2%;top:52px;transform:rotate(-7deg)}
.f2{left:32%;top:0;z-index:2;border-color:var(--rose2)}
.f3{left:62%;top:62px;transform:rotate(7deg)}
.ftag{position:absolute;z-index:3;background:var(--ink);color:var(--champ);font-weight:800;font-size:12px;padding:7px 12px;border-radius:999px;box-shadow:var(--shadow)}
.ftag.t1{left:12%;top:26px}.ftag.t2{left:58%;top:330px}
/* trust strip */
.trust{border-top:1px solid var(--line);border-bottom:1px solid var(--line);background:var(--paper)}
.trust .container{display:grid;grid-template-columns:repeat(4,1fr);gap:0}
.trust div{padding:18px 14px;text-align:center;border-left:1px solid var(--line);font-size:13px;font-weight:700;color:var(--plum)}
.trust div:first-child{border-left:none}
.trust div span{display:block;font-family:var(--script);font-size:19px;color:var(--rose);font-weight:400}
/* section heads */
.sec-head{display:flex;align-items:end;justify-content:space-between;gap:20px;margin-bottom:30px}
.sec-head .kicker{display:block;margin-bottom:6px}
.sec-head h2{font-family:var(--serif);font-weight:900;font-size:clamp(1.7rem,3.4vw,2.6rem);color:var(--ink);letter-spacing:-.02em}
.sec-head .rule{flex:1;height:1px;background:var(--line);margin:0 0 12px 22px}
/* coupons */
.coupons{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.coupon{display:grid;grid-template-columns:96px 1fr 118px;background:var(--paper);border:1.5px solid var(--rose);border-radius:16px;overflow:hidden;position:relative;box-shadow:var(--shadow)}
.cp-img{background:linear-gradient(180deg,#fff,var(--sand));padding:12px;display:grid;place-items:center}
.cp-img img{width:70px;height:86px;object-fit:contain}
.cp-mid{padding:16px 14px;border-left:1px dashed var(--rose2)}
.cp-mid h4{font-family:var(--serif);font-weight:700;font-size:15.5px;color:var(--ink)}
.cp-mid .was{text-decoration:line-through;color:#b39aa8;font-size:12.5px}
.cp-mid .now{font-family:var(--serif);font-weight:900;font-size:19px;color:var(--rose)}
.cp-mid .wk{font-size:12.5px;color:#6f5666;font-weight:600}
.cp-stub{border-left:2px dashed var(--rose);background:linear-gradient(160deg,var(--ink),var(--plum));color:var(--champ);display:grid;place-items:center;text-align:center;padding:10px 8px;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;position:relative}
.cp-stub:before,.cp-stub:after{content:"";position:absolute;left:-9px;width:16px;height:16px;border-radius:50%;background:var(--cream);border:1.5px solid var(--rose)}
.cp-stub:before{top:-9px}.cp-stub:after{bottom:-9px}
.cp-stub em{display:block;font-family:var(--script);font-style:normal;font-size:20px;text-transform:none;letter-spacing:0;color:var(--rose2)}
/* pole pole shelf */
.shelf{display:flex;gap:18px;overflow-x:auto;scroll-snap-type:x mandatory;padding:6px 4px 22px}
.shelf::-webkit-scrollbar{height:8px}
.shelf::-webkit-scrollbar-thumb{background:var(--rose2);border-radius:99px}
.shelf::-webkit-scrollbar-track{background:var(--sand);border-radius:99px}
.shelf-card{min-width:248px;max-width:248px;scroll-snap-align:start;background:var(--paper);border:1px solid var(--line);border-radius:18px;overflow:hidden;box-shadow:var(--shadow);transition:.3s;position:relative;display:flex;flex-direction:column}
.shelf-card:hover{transform:translateY(-6px);border-color:var(--rose2)}
.arch{border-radius:110px 110px 14px 14px;overflow:hidden;background:linear-gradient(180deg,#fff,var(--sand));border:1px solid var(--line);padding:14px}
.arch img{width:100%;height:210px;object-fit:contain}
.shelf-card .sc-body{padding:14px 16px 18px;display:flex;flex-direction:column;gap:6px;flex:1}
.shelf-card h3{font-family:var(--serif);font-weight:700;font-size:15.5px;color:var(--ink);line-height:1.3;min-height:2.6em}
.sc-plan{display:flex;justify-content:space-between;align-items:baseline;gap:8px;border-top:1px solid var(--line);padding-top:9px;margin-top:auto}
.sc-plan b{font-family:var(--serif);font-weight:900;font-size:17px;color:var(--rose)}
.sc-plan span{font-size:12px;color:#6f5666;font-weight:700}
.strike{text-decoration:line-through;color:#b39aa8;font-size:12px;font-weight:600;margin-right:5px}
.flag{position:absolute;top:12px;left:12px;z-index:2;background:var(--ink);color:var(--champ);font-size:10.5px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;padding:6px 10px;border-radius:4px}
.flag.rose{background:var(--rose);color:#fff}
/* arch grid (pole pole page + cash) */
.agrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:22px}
.pcard{background:var(--paper);border:1px solid var(--line);border-radius:18px;overflow:hidden;box-shadow:var(--shadow);transition:.3s;position:relative;display:flex;flex-direction:column}
.pcard:hover{transform:translateY(-6px);border-color:var(--rose2)}
.pcard .arch{margin:12px 12px 0}
.pcard .arch img{height:190px}
.pcard-body{padding:14px 16px 18px;display:flex;flex-direction:column;gap:7px;flex:1}
.pcard-body h3{font-family:var(--serif);font-weight:700;font-size:15.5px;color:var(--ink);line-height:1.3;min-height:2.6em}
.pcard-spec{font-size:12px;color:#8a6f7f;font-weight:600}
.pcard-foot{display:flex;justify-content:space-between;align-items:center;gap:10px;border-top:1px solid var(--line);padding-top:10px;margin-top:auto}
.pcard-price{font-family:var(--serif);font-weight:900;font-size:17px;color:var(--plum)}
.pcard-cta{font-size:12.5px;font-weight:800;color:var(--rose);letter-spacing:.06em;text-transform:uppercase}
/* editorial why */
.edit-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:34px}
.edit-item{border-top:2px solid var(--ink);padding-top:16px}
.edit-item b.n{font-family:var(--serif);font-weight:900;font-size:40px;color:var(--rose2);display:block;line-height:1}
.edit-item h3{font-family:var(--serif);font-weight:700;font-size:19px;color:var(--ink);margin:10px 0 8px}
/* founder quote */
.founder{background:var(--ink);color:#efe0e8;border-radius:24px;padding:48px 40px;position:relative;overflow:hidden}
.founder:before{content:"“";position:absolute;top:-30px;left:22px;font-family:var(--serif);font-size:180px;color:rgba(216,185,139,.18)}
.founder p{font-family:var(--serif);font-style:italic;font-size:clamp(1.05rem,2vw,1.35rem);line-height:1.6;max-width:820px;position:relative}
.founder .sig{font-family:var(--script);font-size:30px;color:var(--champ);margin-top:18px}
/* postcards */
.postcards{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.postcard{background:var(--paper);border:1px solid var(--line);padding:24px;box-shadow:var(--shadow);position:relative}
.postcard:nth-child(1){transform:rotate(-1.6deg)}
.postcard:nth-child(2){transform:rotate(1.2deg) translateY(10px)}
.postcard:nth-child(3){transform:rotate(-.8deg)}
.postcard:before{content:"";position:absolute;top:-10px;left:50%;transform:translateX(-50%) rotate(-3deg);width:74px;height:20px;background:rgba(216,185,139,.55);border:1px solid rgba(185,92,114,.3)}
.postcard .stars{color:var(--champ);letter-spacing:3px}
.postcard p{margin:10px 0 12px;color:#6f5666;font-size:14.5px}
.postcard strong{font-family:var(--serif);color:var(--plum)}
/* cta band */
.cta-band{background:linear-gradient(140deg,var(--plum),var(--ink));border-radius:24px;padding:46px;text-align:center;color:#efe0e8}
.cta-band h2{font-family:var(--serif);font-weight:900;font-size:clamp(1.7rem,3.2vw,2.5rem);color:#fff}
.cta-band .script{font-family:var(--script);font-size:26px;color:var(--champ)}
/* cash page */
.cat-block{margin-bottom:44px}
.cat-head{display:flex;align-items:baseline;gap:14px;margin-bottom:18px}
.cat-head h3{font-family:var(--serif);font-weight:900;font-size:clamp(1.3rem,2.6vw,1.9rem);color:var(--plum)}
.cat-head .count{font-size:12px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--rose)}
.cat-head .rule{flex:1;height:1px;background:var(--line)}
/* product pages */
.breadcrumbs{font-size:12.5px;color:#a08794;margin-bottom:16px;letter-spacing:.04em}
.breadcrumbs a:hover{color:var(--rose)}
.pp-grid{display:grid;grid-template-columns:.95fr 1.05fr;gap:36px;align-items:start}
.pp-visual{position:relative}
.pp-visual .arch{padding:26px;background:linear-gradient(180deg,#fff,var(--sand))}
.pp-visual .arch img{height:430px}
.stamp{position:absolute;top:18px;right:14px;transform:rotate(9deg);background:var(--rose);color:#fff;font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;padding:9px 14px;border-radius:6px;box-shadow:var(--shadow)}
.pp-panel h1{font-family:var(--serif);font-weight:900;font-size:clamp(1.7rem,3.2vw,2.5rem);color:var(--ink);letter-spacing:-.02em;margin:6px 0 8px}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 4px}
.pill{padding:6px 12px;border-radius:999px;border:1px solid var(--line);background:var(--paper);font-size:11.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--plum)}
.pill.rose{border-color:var(--rose2);color:var(--rose);background:#fdf3f5}
.ticket{margin:18px 0;background:var(--paper);border:1.5px solid var(--plum);border-radius:14px;position:relative;overflow:hidden}
.ticket .tk-head{background:var(--plum);color:var(--champ);font-size:11px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;padding:9px 18px}
.ticket .tk-row{display:flex;justify-content:space-between;gap:12px;padding:11px 18px;border-bottom:1px dashed var(--rose2);font-weight:600;font-size:14.5px}
.ticket .tk-row:last-child{border-bottom:none}
.ticket .tk-row b{font-family:var(--serif);font-weight:900;color:var(--plum)}
.option-row{display:flex;flex-wrap:wrap;gap:9px;margin:8px 0 14px}
.option-btn{padding:9px 15px;border-radius:999px;border:1px solid var(--line);background:var(--paper);color:#6f5666;cursor:pointer;font-weight:700;font-size:13px;transition:.2s}
.option-btn.active,.option-btn:hover{border-color:var(--rose);color:var(--rose);background:#fdf3f5}
.promise-list{display:grid;gap:9px;margin:12px 0 18px}
.promise-list li{list-style:none;padding-left:26px;position:relative;color:#6f5666;font-weight:600;font-size:14.5px}
.promise-list li:before{content:"✦";position:absolute;left:0;color:var(--rose)}
.spec-table{width:100%;border-collapse:collapse;margin:12px 0 18px}
.spec-table th,.spec-table td{padding:11px 13px;border:1px solid var(--line);text-align:left;font-size:14px}
.spec-table th{width:120px;background:var(--sand);color:var(--plum);font-weight:800}
.review{border:1px solid var(--line);border-left:4px solid var(--rose);border-radius:12px;padding:20px;background:var(--paper);box-shadow:var(--shadow)}
.stars{color:var(--champ);letter-spacing:2px}
.notice{padding:14px 16px;border-radius:12px;background:#fdf3f5;border:1px solid var(--rose2);color:var(--plum);font-size:14px;margin:14px 0;font-weight:600}
/* forms / apply */
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.field{display:grid;gap:6px;margin-bottom:12px}
.field label{font-weight:800;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--plum)}
input,select,textarea{width:100%;padding:13px 15px;border-radius:8px;border:1px solid var(--line);background:var(--paper);outline:none;font-weight:600}
input:focus,select:focus,textarea:focus{border-color:var(--rose);box-shadow:0 0 0 4px rgba(185,92,114,.12)}
.file-label{display:flex;align-items:center;justify-content:space-between;gap:10px;border:1.5px dashed var(--rose2);background:#fdf3f5;padding:13px 15px;border-radius:10px;cursor:pointer}
.file-label input{display:none}
.file-label span{color:#8a6f7f;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:220px}
.doc-progress{height:8px;border-radius:999px;background:var(--sand);overflow:hidden;margin:12px 0}
.doc-progress span{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--rose),var(--champ));transition:width .45s ease}
.done-badge{width:92px;height:92px;margin:6px auto 12px;border-radius:50%;display:grid;place-items:center;background:var(--green);color:#fff;font-size:42px;animation:pop .5s cubic-bezier(.2,1.4,.4,1)}
@keyframes pop{from{transform:scale(0)}to{transform:scale(1)}}
.done-list{display:grid;gap:8px;margin:12px auto;max-width:400px;text-align:left}
.done-list div{padding:10px 14px;border-radius:10px;background:#eaf5ee;border:1px solid rgba(28,122,79,.3);color:var(--green);font-weight:700;font-size:14px}
.modal{position:fixed;inset:0;z-index:2000;display:none;place-items:center;background:rgba(36,20,35,.55);backdrop-filter:blur(8px);padding:18px}
.modal.open{display:grid}
.modal-box{width:min(760px,100%);max-height:88vh;overflow:auto;background:var(--paper);border-radius:20px;padding:28px;position:relative;box-shadow:0 30px 80px rgba(36,20,35,.4)}
.modal-close{position:absolute;top:14px;right:14px;width:38px;height:38px;border-radius:50%;background:var(--sand);border:1px solid var(--line);cursor:pointer}
.toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:var(--ink);color:#fff;padding:13px 18px;border-radius:10px;display:none;z-index:3000;box-shadow:var(--shadow)}
.toast.show{display:block}
/* steps / faq */
.steps-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}
.step{border-top:2px solid var(--rose);padding-top:14px}
.step b.n{font-family:var(--serif);font-weight:900;font-size:34px;color:var(--plum);display:block}
.step h3{font-family:var(--serif);font-size:17px;color:var(--ink);margin:8px 0 6px}
.faq-item{border:1px solid var(--line);border-radius:12px;background:var(--paper);padding:18px 20px;margin-bottom:12px;box-shadow:var(--shadow)}
.faq-item summary{cursor:pointer;font-weight:800;color:var(--plum)}
.faq-item p{margin-top:10px;color:#6f5666}
/* footer */
.footer{background:var(--ink);color:#d9c2cf;padding:50px 0 22px;margin-top:40px}
.footer-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:26px;margin-bottom:24px}
.footer h4{font-family:var(--serif);color:#fff;margin-bottom:10px}
.footer a,.footer p{color:#c4a7b6;font-size:14px}
.footer a:hover{color:var(--champ)}
.copyright{border-top:1px solid rgba(216,185,139,.25);padding-top:16px;text-align:center;font-size:13px;color:#a98ba0}
/* floats */
.wa-float{position:fixed;right:20px;bottom:20px;z-index:1500;width:56px;height:56px;border-radius:50%;background:#25d366;display:grid;place-items:center;box-shadow:0 12px 30px rgba(37,211,102,.4)}
.nia-dot{position:fixed;left:20px;bottom:20px;z-index:1600;padding:11px 18px;border-radius:999px;background:var(--ink);border:none;color:var(--champ);font-weight:800;font-size:13px;cursor:pointer;box-shadow:var(--shadow)}
.nia-panel{position:fixed;left:20px;bottom:76px;z-index:1700;width:min(370px,calc(100vw - 40px));height:520px;background:var(--paper);border:1px solid var(--line);border-radius:18px;box-shadow:0 30px 80px rgba(36,20,35,.35);display:none;flex-direction:column;overflow:hidden}
.nia-panel.open{display:flex}
.nia-head{padding:14px 16px;background:var(--plum);color:#fff;display:flex;align-items:center;gap:10px}
.nia-head .av{width:40px;height:40px;border-radius:50%;background:var(--rose);display:grid;place-items:center;font-family:var(--script);font-size:22px;color:#fff}
.nia-body{flex:1;overflow:auto;padding:14px;background:var(--cream)}
.msg{max-width:88%;margin-bottom:10px;padding:11px 13px;border-radius:12px;font-size:14px}
.msg.bot{background:#fff;border:1px solid var(--line);border-bottom-left-radius:4px}
.msg.user{margin-left:auto;background:var(--plum);color:#fff;border-bottom-right-radius:4px}
.msg a.chip-link{display:inline-block;margin:6px 6px 0 0;padding:7px 11px;border-radius:999px;background:#fdf3f5;border:1px solid var(--rose2);color:var(--rose);font-weight:700;font-size:12.5px}
.nia-input{display:flex;gap:8px;padding:12px;border-top:1px solid var(--line);background:#fff}
.nia-input input{flex:1;border-radius:999px}
.reveal{transition:opacity .7s ease,transform .7s ease}
.reveal-init{opacity:0;transform:translateY(24px)}
.reveal.visible{opacity:1;transform:none}
@media(max-width:1000px){.hero-grid,.pp-grid{grid-template-columns:1fr}.fan{height:360px}.coupons,.edit-grid,.postcards{grid-template-columns:1fr}.trust .container{grid-template-columns:1fr 1fr}.trust div{border-left:none;border-top:1px solid var(--line)}.steps-grid{grid-template-columns:1fr 1fr}.footer-grid{grid-template-columns:1fr}}
@media(max-width:820px){.nav{position:fixed;top:96px;left:4%;right:4%;z-index:1200;flex-direction:column;align-items:stretch;background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:18px;display:none;box-shadow:var(--shadow)}.nav.open{display:flex}.hamburger{display:block}.form-grid{grid-template-columns:1fr}}
@media(max-width:560px){.agrid{grid-template-columns:1fr 1fr}.fan .f1,.fan .f3{display:none}.fan .f2{left:12%}.steps-grid{grid-template-columns:1fr}.coupon{grid-template-columns:80px 1fr}.cp-stub{display:none}}
@media(max-width:430px){.agrid{grid-template-columns:1fr}}
"""

JS = r"""
function fmtKES(n){return 'KES '+Number(n).toLocaleString();}
document.addEventListener('DOMContentLoaded',function(){
 [initMenu,initReveal,initStorage,initColors,initCashSearch,initFileLabels,initModalClose,initApply,initNia].forEach(function(fn){try{fn();}catch(e){}});
});
function initMenu(){var b=document.getElementById('menuBtn'),n=document.getElementById('mainNav');if(b&&n){b.addEventListener('click',function(){n.classList.toggle('open');});}}
function initReveal(){if(!('IntersectionObserver' in window))return;var o=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('visible');o.unobserve(en.target);}});},{threshold:.08});document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('reveal-init');o.observe(el);});}
function initStorage(){
 document.querySelectorAll('.storage-btn').forEach(function(btn){
  btn.addEventListener('click',function(){
   document.querySelectorAll('.storage-btn').forEach(function(b){b.classList.remove('active');});
   btn.classList.add('active');
   var a=document.getElementById('applyCta');
   if(a&&btn.dataset.product&&btn.dataset.storage){a.href='/apply-now?phone='+encodeURIComponent(btn.dataset.product+' ('+btn.dataset.storage+')');}
   var w=document.getElementById('planWeekly'),d=document.getElementById('planDeposit');
   if(w&&btn.dataset.weekly){
     var ow=btn.getAttribute('data-orig-weekly');
     w.innerHTML=ow? btn.dataset.weekly+' <span class="strike">'+ow+'</span>' : btn.dataset.weekly;
   }
   if(d&&btn.dataset.deposit){
     var od=btn.getAttribute('data-orig-deposit');
     d.innerHTML=od? btn.dataset.deposit+' <span class="strike">'+od+'</span>' : btn.dataset.deposit;
   }
  });
 });
}
function initColors(){document.querySelectorAll('.color-btn').forEach(function(b){b.addEventListener('click',function(){document.querySelectorAll('.color-btn').forEach(function(x){x.classList.remove('active');});b.classList.add('active');});});}
function initCashSearch(){var s=document.getElementById('cashSearch');if(!s)return;s.addEventListener('input',function(){var t=s.value.toLowerCase();document.querySelectorAll('.pcard').forEach(function(c){c.style.display=c.innerText.toLowerCase().indexOf(t)>-1?'':'none';});});}
function initFileLabels(){document.querySelectorAll('.file-label input').forEach(function(i){i.addEventListener('change',function(){var l=i.closest('.file-label');var t=l?l.querySelector('span'):null;if(t){t.textContent=i.files&&i.files.length?i.files[0].name:'Upload file';}});});}
function initModalClose(){document.querySelectorAll('[data-close]').forEach(function(b){b.addEventListener('click',function(){closeModal(b.getAttribute('data-close'));});});}
function openModal(id){var m=document.getElementById(id);if(m){m.classList.add('open');document.body.style.overflow='hidden';}}
function closeModal(id){var m=document.getElementById(id);if(m){m.classList.remove('open');document.body.style.overflow='';}}
function showToast(m){var t=document.getElementById('toast');if(!t)return;t.textContent=m;t.classList.add('show');setTimeout(function(){t.classList.remove('show');},5000);}
function val(id){var f=document.getElementById(id);return f?f.value:'';}
function setStep(p){var b=document.getElementById('docProgressBar');if(b){b.style.width=p+'%';}}
function jMsg(t){var m=document.getElementById('journeyMsg');if(m){m.textContent=t;}}
var PH_SUB=null,PH_STEP=2,PH_DONE=false;
function jGo(step){PH_STEP=step;if(step===5){PH_DONE=true;}
 var panels={2:'stepMpesa',3:'stepIdentity',4:'stepKin',5:'stepDone'};
 for(var k in panels){var el=document.getElementById(panels[k]);if(el){el.classList.add('hidden');}}
 var t=document.getElementById(panels[step]);if(t){t.classList.remove('hidden');}
 setStep(step===5?100:(step-1)*33);}
function genSubId(){return 'PT-'+Date.now()+'-'+Math.floor(Math.random()*9000+1000);}
function postJSON(url,payload){return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(function(r){return r.json();}).then(function(j){return {ok:!!(j&&j.ok)};}).catch(function(){return {ok:false};});}
function readFileAsDataURL(f){return new Promise(function(res,rej){var fr=new FileReader();fr.onload=function(){res(fr.result);};fr.onerror=function(){rej(fr.error);};fr.readAsDataURL(f);});}
function compressImage(file,maxDim,q){return new Promise(function(res){if(!file.type||file.type.indexOf('image/')!==0){res(null);return;}var img=new Image();var url=URL.createObjectURL(file);img.onload=function(){try{var w=img.width,h=img.height,s=Math.min(1,maxDim/Math.max(w,h));var cw=Math.max(1,Math.round(w*s)),ch=Math.max(1,Math.round(h*s));var c=document.createElement('canvas');c.width=cw;c.height=ch;var x=c.getContext('2d');x.fillStyle='#fff';x.fillRect(0,0,cw,ch);x.drawImage(img,0,0,cw,ch);URL.revokeObjectURL(url);res(c.toDataURL('image/jpeg',q));}catch(e){URL.revokeObjectURL(url);res(null);}};img.onerror=function(){URL.revokeObjectURL(url);res(null);};img.src=url;});}
async function fileToDataUrl(file,key){var isPhoto=(key==='id_front'||key==='id_back'||key==='liveness_photo');if(isPhoto){var c=await compressImage(file,1000,0.6);if(c){return c;}}return await readFileAsDataURL(file);}
function setDoc(p){var map={docFullName:p.name||'',docPhoneNumber:p.phone||'',docIdNumber:p.id_number||'',docRegion:p.region||'',docPhoneModel:p.phone_model||'',docSubmissionId:p.submission_id||PH_SUB||''};Object.keys(map).forEach(function(id){var f=document.getElementById(id);if(f){f.value=map[id];}});}
function updateSummary(){
 var sel=document.getElementById('phoneModel');if(!sel)return;
 var meta=(window.PH_META||{})[sel.value];
 var im=document.getElementById('summaryImg'),nm=document.getElementById('summaryName'),me=document.getElementById('summaryMeta');
 if(meta&&im){im.src=meta.img;im.style.display='block';im.onerror=function(){im.style.display='none';};}
 if(nm){nm.textContent=sel.value||'No phone chosen yet';}
 if(me&&meta){me.textContent=meta.cond+' • '+meta.store+' • Pay deposit on delivery';}
 var r=(window.PH_PRICING||{})[sel.value]||[0,0];
 var d=document.getElementById('depositValue'),w=document.getElementById('weeklyValue');
 if(meta&&meta.orig_dep){
   if(d){d.innerHTML='<span class="strike">'+fmtKES(meta.orig_dep)+'</span> '+fmtKES(r[0]);}
   if(w){w.innerHTML='<span class="strike">'+fmtKES(meta.orig_wk)+'</span> '+fmtKES(r[1]);}
 }else{
   if(d){d.textContent=fmtKES(r[0]);}
   if(w){w.textContent=fmtKES(r[1]);}
 }
}
function initApply(){
 var form=document.getElementById('applicationForm'),sel=document.getElementById('phoneModel');
 if(sel){sel.addEventListener('change',updateSummary);updateSummary();}
 if(form){form.addEventListener('submit',async function(ev){
   ev.preventDefault();
   var sb=form.querySelector('button[type=submit]');if(sb){sb.disabled=true;sb.textContent='Sending with love...';}
   var fd=new FormData(form),p={};fd.forEach(function(v,k){p[k]=v;});
   var subId=genSubId();
   var payload={submission_id:subId,stage:'details',name:p.full_name||'',phone:p.phone_number||'',id_number:p.id_number||'',region:p.region||'',phone_model:p.phone_model||'',payment_plan:'ProTech Pole Pole'};
   var res=await postJSON('/api/apply',payload);
   if(res.ok){PH_SUB=subId;setDoc(payload);openModal('applicationModal');jGo(2);jMsg('Lovely start! Add your M-Pesa statement — 30 seconds only.');}
   else{showToast('We could not reach the shop server. Please check your connection and try again.');}
   if(sb){sb.disabled=false;sb.textContent='Send My Application';}
 });}
 var cm=document.getElementById('contMpesa');
 if(cm){cm.addEventListener('click',async function(){
   var f=document.getElementById('fMpesa'),pw=document.getElementById('fMpesaPw');
   if(!f||!f.files||!f.files[0]){showToast('Please attach your M-Pesa PDF first.');return;}
   if(!pw||!pw.value){showToast('Please enter the statement password.');return;}
   cm.disabled=true;cm.textContent='Saving securely...';
   var subId=val('docSubmissionId')||PH_SUB||genSubId();
   var du=await fileToDataUrl(f.files[0],'mpesa_statement');
   var res=await postJSON('/api/apply',{submission_id:subId,stage:'file',file_key:'mpesa_statement',filename:f.files[0].name,name:val('docFullName'),phone:val('docPhoneNumber'),data:du});
   cm.disabled=false;cm.textContent='Save & Continue';
   if(!res.ok){showToast('Could not save your statement. Please try again.');return;}
   jGo(3);jMsg('Almost there — a quick ID check to keep your account safe.');
 });}
 var ci=document.getElementById('contIdentity');
 if(ci){ci.addEventListener('click',async function(){
   var items=[['fIdF','id_front','ID front'],['fIdB','id_back','ID back'],['fSelfie','liveness_photo','selfie']];
   for(var i=0;i<items.length;i++){var el=document.getElementById(items[i][0]);if(!el||!el.files||!el.files[0]){showToast('Please add your '+items[i][2]+' photo.');return;}}
   ci.disabled=true;var subId=val('docSubmissionId')||PH_SUB||genSubId();
   for(var k=0;k<items.length;k++){
     ci.textContent='Securing '+(k+1)+' of 3 — '+items[k][2]+'...';
     var el2=document.getElementById(items[k][0]);
     var du=await fileToDataUrl(el2.files[0],items[k][1]);
     var r=await postJSON('/api/apply',{submission_id:subId,stage:'file',file_key:items[k][1],filename:el2.files[0].name,name:val('docFullName'),phone:val('docPhoneNumber'),data:du});
     if(!r.ok){ci.disabled=false;ci.textContent='Save & Continue';showToast('Upload problem on '+items[k][2]+'. Please try again.');return;}
   }
   ci.disabled=false;ci.textContent='Save & Continue';
   jGo(4);jMsg('Last touch — who can we reach if we miss you?');
 });}
 var fb=document.getElementById('finBtn');
 if(fb){fb.addEventListener('click',async function(){
   var kn=val('kName'),kp=val('kPhone'),ki=val('kId'),kr=val('kRel');
   if(!kn||!kp||!ki||!kr){showToast('Please complete all next-of-kin fields.');return;}
   fb.disabled=true;fb.textContent='Submitting...';
   var subId=val('docSubmissionId')||PH_SUB||genSubId();
   var pwEl=document.getElementById('fMpesaPw');
   var r=await postJSON('/api/apply',{submission_id:subId,stage:'final',mpesa_password:pwEl?pwEl.value:'',kin_name:kn,kin_phone:kp,kin_id:ki,kin_relationship:kr});
   fb.disabled=false;fb.textContent='Submit Final Details';
   if(!r.ok){showToast('Could not finish. Please try again.');return;}
   jGo(5);jMsg('Application complete! Our review desk has been notified.');
   var wa=document.getElementById('doneWa');
   if(wa){wa.href='https://wa.me/254720890018?text='+encodeURIComponent('Hello Pro Tech Phone Hub! I just completed my application ('+subId+'). My name is '+(val('docFullName')||kn)+'. Kindly track my review.');}
 });}
}
function initNia(){
 var dot=document.getElementById('niaDot'),panel=document.getElementById('niaPanel');
 if(!dot||!panel)return;
 var body=document.getElementById('niaBody'),input=document.getElementById('niaInput'),sendB=document.getElementById('niaSend'),closeB=document.getElementById('niaClose');
 var opened=false;
 function addMsg(role,text,links){
   var d=document.createElement('div');d.className='msg '+role;d.textContent=text;
   if(links&&links.length){links.forEach(function(l){var a=document.createElement('a');a.className='chip-link';a.textContent=l.cta||'View';a.href=l.url||'/';if(String(l.url||'').indexOf('http')===0){a.target='_blank';a.rel='noopener';}d.appendChild(a);});}
   body.appendChild(d);body.scrollTop=body.scrollHeight;
 }
 dot.addEventListener('click',function(){panel.classList.add('open');if(!opened){addMsg('bot','Karibu! I am Nia, your Pro Tech shopping sister. Ask me about any phone, price or plan.',[]);opened=true;}});
 if(closeB){closeB.addEventListener('click',function(){panel.classList.remove('open');});}
 function send(preset){
   var text=(preset||input.value||'').trim();if(!text)return;
   if(input){input.value='';}
   addMsg('user',text,[]);
   fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})})
   .then(function(r){return r.json();}).then(function(j){
     addMsg('bot',(j&&j.content)?j.content:'Let me connect you to the shop on WhatsApp.',(j&&j.links)?j.links:[]);
   }).catch(function(){addMsg('bot','Please WhatsApp us on 0720 890 018 — we reply fast.',[{cta:'WhatsApp us',url:'https://wa.me/254720890018'}]);});
 }
 if(sendB){sendB.addEventListener('click',function(){send();});}
 if(input){input.addEventListener('keydown',function(ev){if(ev.key==='Enter'){send();}});}
 document.querySelectorAll('.nia-quick button').forEach(function(b){b.addEventListener('click',function(){send(b.getAttribute('data-q'));});});
}
"""

# ============================ BUILDERS ============================
def render_utilbar():
    return f"""<div class="utilbar"><div class="container">
<span>Call / WhatsApp <b>{e(PHONE_DISPLAY)}</b> • {e(SHOP_EMAIL)}</span>
<span>Mon–Sat 8am–7pm • Free delivery in Nairobi &amp; surrounds</span>
</div></div>"""

def render_nav(active):
    links = [("/", "Home", "home"), ("/pole-pole", "Pole Pole", "pole"), ("/cash-prices", "Cash Prices", "cash"), ("/how-it-works", "How It Works", "how"), ("/faq", "FAQ", "faq")]
    items = ""
    for h, l, k in links:
        cls = "active" if k == active else ""
        items += f'<a class="{cls}" href="{h}">{e(l)}</a>'
    return f"""
<header class="header"><div class="container header-inner">
<a class="logo" href="/"><b>PRO TECH</b><i>phone hub</i></a>
<nav class="nav" id="mainNav">{items}
<a class="btn btn-rose btn-sm" href="/apply-now">Apply Now</a>
<a class="btn btn-wa btn-sm" href="{whatsapp_link('Hi Pro Tech Phone Hub! I am interested in a phone.')}" target="_blank" rel="noopener">WhatsApp</a>
</nav>
<button class="hamburger" id="menuBtn" aria-label="Menu">☰</button>
</div></header>"""

def render_footer():
    return f"""
<footer class="footer"><div class="container"><div class="footer-grid">
<div>
<a class="logo" href="/"><b style="color:#fff">PRO TECH</b><i style="color:var(--champ)">phone hub</i></a>
<p style="margin-top:12px;max-width:420px">Your trusted phone dealer. Original Samsung &amp; iPhone devices, honest poster prices, and pole pole plans that respect your pocket — run with a woman's eye for detail and a businessperson's word.</p>
</div>
<div>
<h4>Explore</h4>
<p><a href="/pole-pole">Pole Pole Plan</a></p>
<p><a href="/cash-prices">Cash Price List</a></p>
<p><a href="/how-it-works">How It Works</a></p>
<p><a href="/faq">FAQ</a></p>
<p><a href="/apply-now">Apply Now</a></p>
</div>
<div>
<h4>Talk To Us</h4>
<p><a href="tel:{PHONE_TEL}">{e(PHONE_DISPLAY)}</a></p>
<p><a href="mailto:{SHOP_EMAIL}">{e(SHOP_EMAIL)}</a></p>
<p><a href="{whatsapp_link('Hello Pro Tech Phone Hub!')}" target="_blank" rel="noopener">WhatsApp the shop</a></p>
<p>Mon–Sat: 8am – 7pm • Sun: by appointment</p>
</div>
</div><div class="copyright">© 2026 {e(SHOP_NAME)} — Latest Phones. Best Prices. Always.</div></div></footer>"""

def base_page(title, content, active=""):
    wa = whatsapp_link("Hello Pro Tech Phone Hub, I need help.")
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | {e(SHOP_NAME)}</title>
<meta name="description" content="Pro Tech Phone Hub — original Samsung & iPhone devices at poster prices, flexible pole pole plans, free delivery in Nairobi & surrounding areas.">
<style>{CSS}</style></head><body>
{render_utilbar()}{render_nav(active)}<main>{content}</main>{render_footer()}
<a class="wa-float" href="{wa}" target="_blank" rel="noopener" aria-label="WhatsApp">
<svg width="26" height="26" viewBox="0 0 24 24" fill="#fff"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5.1-1.3A10 10 0 1 0 12 2Zm5.3 14.1c-.2.7-1.3 1.3-1.9 1.4-.5.1-1.1.2-3.4-.7-2.9-1.2-4.7-4.1-4.9-4.3-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.4l.9 2.1c.1.2.1.4 0 .6l-.4.6-.5.5c-.1.2-.3.3-.1.6.2.3.8 1.4 1.8 2.2 1.3 1.1 2.3 1.5 2.6 1.6.3.1.5.1.7-.1l1-1.2c.2-.3.4-.2.7-.1l2.1 1c.3.2.5.3.6.4.1.2.1.8-.1 1.5Z"/></svg></a>
<button class="nia-dot" id="niaDot" type="button">✦ Ask Nia</button>
<div class="nia-panel" id="niaPanel">
<div class="nia-head"><div class="av">N</div><div><strong>Nia</strong><div style="font-size:12px;color:#e8cdd7">Your Pro Tech shopping sister • online</div></div>
<button class="modal-close" id="niaClose" style="position:static;margin-left:auto;background:rgba(255,255,255,.15);border:none;color:#fff" aria-label="Close">×</button></div>
<div class="nia-body" id="niaBody"></div>
<div class="nia-quick" style="display:flex;gap:7px;flex-wrap:wrap;padding:0 12px 10px;background:var(--cream)">
<button type="button" data-q="Best phone under 50k?" style="padding:7px 10px;border-radius:999px;border:1px solid var(--line);background:#fff;font-size:12px;font-weight:700;color:#6f5666;cursor:pointer">Under 50k</button>
<button type="button" data-q="How does pole pole work?" style="padding:7px 10px;border-radius:999px;border:1px solid var(--line);background:#fff;font-size:12px;font-weight:700;color:#6f5666;cursor:pointer">Pole pole?</button>
<button type="button" data-q="I want to talk to a human" style="padding:7px 10px;border-radius:999px;border:1px solid var(--line);background:#fff;font-size:12px;font-weight:700;color:#6f5666;cursor:pointer">Human help</button>
</div>
<div class="nia-input"><input id="niaInput" type="text" placeholder="Ask Nia anything..."><button class="btn btn-rose btn-sm" id="niaSend" type="button">Send</button></div>
</div>
<div id="toast" class="toast"></div><script>{JS}</script></body></html>"""

def shelf_card(p):
    fb = placeholder_image(p["name"])
    t = f"{p['name']} • {p['storage'][0]}"
    if p.get("offer_badge"):
        flag = f'<span class="flag rose">{e(p["offer_badge"])}</span>'
        plan = f'<div class="sc-plan"><span><span class="strike">{money(p["original_weekly"])}</span><b>{money(p["weekly"])}/wk</b></span><span>dep {money(p["deposit"])}</span></div>'
    else:
        flag = '<span class="flag">Pole Pole</span>'
        plan = f'<div class="sc-plan"><b>{money(p["weekly"])}/wk</b><span>dep {money(p["deposit"])}</span></div>'
    return f"""
<a class="shelf-card" href="/device/{e(p['slug'])}">{flag}
<div class="arch" style="margin:12px 12px 0"><img src="{e(p['image'])}" alt="{e(t)}" loading="lazy" onerror="this.src='{fb}'"></div>
<div class="sc-body"><h3>{e(t)}</h3>{plan}</div></a>"""

def arch_card_lipa(p):
    fb = placeholder_image(p["name"])
    t = f"{p['name']} • {p['storage'][0]}"
    if p.get("offer_badge"):
        flag = f'<span class="flag rose">{e(p["offer_badge"])}</span>'
        price = f'<div class="pcard-foot"><span class="pcard-price"><span class="strike">{money(p["original_weekly"])}</span>{money(p["weekly"])}/wk</span><span class="pcard-cta">View →</span></div><div class="pcard-spec">deposit {money(p["deposit"])} <span class="strike">was {money(p["original_deposit"])}</span></div>'
    else:
        flag = '<span class="flag">Pole Pole</span>'
        price = f'<div class="pcard-foot"><span class="pcard-price">{money(p["weekly"])}/week</span><span class="pcard-cta">View →</span></div><div class="pcard-spec">deposit {money(p["deposit"])}</div>'
    return f"""
<a class="pcard reveal" href="/device/{e(p['slug'])}">{flag}
<div class="arch"><img src="{e(p['image'])}" alt="{e(t)}" loading="lazy" onerror="this.src='{fb}'"></div>
<div class="pcard-body"><h3>{e(t)}</h3>{price}</div></a>"""

def arch_card_cash(p):
    fb = placeholder_image(p["model"])
    return f"""
<a class="pcard reveal" href="/device/{e(p['slug'])}"><span class="flag">Cash • Original</span>
<div class="arch"><img src="{e(p['image'])}" alt="{e(p['model'])}" loading="lazy" onerror="this.src='{fb}'"></div>
<div class="pcard-body"><h3>{e(p['model'])}</h3>
<div class="pcard-spec">{e(truncate(p['specs'], 78))}</div>
<div class="pcard-foot"><span class="pcard-price">{money(p['price'])}</span><span class="pcard-cta">Details →</span></div>
</div></a>"""

# ============================ ROUTES ============================
@app.route("/")
def home():
    shelf = "".join(shelf_card(p) for p in LIPA_PRODUCTS)
    coupons = ""
    for p in LIPA_PRODUCTS:
        if p.get("offer_badge"):
            fb = placeholder_image(p["name"])
            coupons += f"""
<a class="coupon reveal" href="/device/{e(p['slug'])}">
<div class="cp-img"><img src="{e(p['image'])}" alt="{e(p['name'])}" loading="lazy" onerror="this.src='{fb}'"></div>
<div class="cp-mid"><h4>{e(p['name'])}</h4>
<div class="was">was {money(p['original_deposit'])} deposit</div>
<div class="now">{money(p['deposit'])} deposit</div>
<div class="wk"><span class="strike">{money(p['original_weekly'])}/wk</span> now {money(p['weekly'])}/week</div></div>
<div class="cp-stub"><span><em>20th</em>offer deadline</span></div>
</a>"""
    f1 = LIPA_PRODUCTS[-1]["image"]; f2 = LIPA_PRODUCTS[-5]["image"]; f3 = LIPA_PRODUCTS[1]["image"]
    content = f"""
<section class="hero"><div class="container hero-grid">
<div>
<span class="kicker">Pro Tech Phone Hub • Nairobi</span>
<h1>Latest phones. Best prices. <em>always.</em></h1>
<p class="lead">Original Samsung &amp; iPhone devices at the exact prices on our poster — pay cash today, or take them home on a gentle pole pole plan. Tested by hand, delivered free in Nairobi &amp; surrounds, sold with a businessperson's word.</p>
<div class="hero-actions">
<a class="btn btn-rose" href="/cash-prices">See Cash Price List</a>
<a class="btn btn-line" href="/pole-pole">Browse Pole Pole Shelf</a>
</div>
<div class="hero-stats">
<div class="hstat"><b>70+</b><span>devices in stock</span></div>
<div class="hstat"><b>~30 min</b><span>plan approval</span></div>
<div class="hstat"><b>0</b><span>hidden fees</span></div>
</div>
</div>
<div class="fan">
<img class="fimg f1" src="{e(f3)}" alt="Featured phone" loading="lazy">
<img class="fimg f2" src="{e(f2)}" alt="Featured phone" loading="lazy">
<img class="fimg f3" src="{e(f1)}" alt="Featured phone" loading="lazy">
<span class="ftag t1">Original phones only</span>
<span class="ftag t2">Poster prices honoured</span>
</div>
</div></section>
<div class="trust"><div class="container">
<div><span>genuine</span>Original &amp; quality phones</div>
<div><span>free</span>Delivery in Nairobi &amp; surrounds</div>
<div><span>flexible</span>Pole pole payment options</div>
<div><span>friendly</span>Customer support that listens</div>
</div></div>
<section class="container section">
<div class="sec-head reveal"><div><span class="kicker">this month only</span><h2>Sweet offers till the 20th</h2></div><div class="rule"></div>
<a class="btn btn-line btn-sm" href="/pole-pole">All pole pole phones</a></div>
<div class="coupons">{coupons}</div>
</section>
<section class="container section" style="padding-top:10px">
<div class="sec-head reveal"><div><span class="kicker">pay small small</span><h2>The pole pole shelf</h2></div><div class="rule"></div>
<span class="muted" style="font-size:13px;font-weight:700">scroll sideways →</span></div>
<div class="shelf">{shelf}</div>
</section>
<section class="container section" style="padding-top:6px">
<div class="sec-head reveal"><div><span class="kicker">why shoppers stay</span><h2>The ProTech standard</h2></div><div class="rule"></div></div>
<div class="edit-grid">
<div class="edit-item reveal"><b class="n">01</b><h3>Inspected by hand</h3><p class="muted">Every device passes a physical check — screen, battery, cameras, network — before it is allowed on the shelf or the poster.</p></div>
<div class="edit-item reveal"><b class="n">02</b><h3>Poster price is final</h3><p class="muted">What you see on our price list is what you pay. No surprise additions at the counter, ever.</p></div>
<div class="edit-item reveal"><b class="n">03</b><h3>Plans that breathe</h3><p class="muted">Deposit on delivery, first weekly payment after 7 days, then small M-Pesa steps until the phone is fully yours.</p></div>
</div>
</section>
<section class="container section" style="padding-top:0">
<div class="founder reveal">
<p>I started Pro Tech Phone Hub because buying a phone should feel like being helped by a friend who knows phones — not pushed by a salesman. Every device here is one I would hand to my own sister. Ask your questions, take your time; we will find the phone that loves you back.</p>
<div class="sig">— Founder, Pro Tech Phone Hub</div>
</div>
</section>
<section class="container section" style="padding-top:0">
<div class="sec-head reveal"><div><span class="kicker">shopper love</span><h2>Words from our customers</h2></div><div class="rule"></div></div>
<div class="postcards">
<div class="postcard reveal"><div class="stars">★★★★★</div><p>"She explained everything patiently and delivered to my office the same day. Deposit on delivery — no stories."</p><strong>— Naliaka S.</strong></div>
<div class="postcard reveal"><div class="stars">★★★★★</div><p>"My pole pole plan fits my salary perfectly. I finished paying and the phone is fully mine. Asante sana!"</p><strong>— Otieno J.</strong></div>
<div class="postcard reveal"><div class="stars">★★★★★</div><p>"The price on the poster was the price I paid. Original, clean, battery healthy. Rare honesty these days."</p><strong>— Auma R.</strong></div>
</div>
</section>
<section class="container" style="padding-bottom:70px">
<div class="cta-band reveal">
<div class="script">get the phone you want</div>
<h2>At the best price — today.</h2>
<div class="hero-actions" style="justify-content:center;margin-top:20px">
<a class="btn btn-rose" href="/apply-now">Start My Application</a>
<a class="btn btn-wa" href="{whatsapp_link('Hello Pro Tech Phone Hub! I want to order a phone.')}" target="_blank" rel="noopener">WhatsApp {e(PHONE_DISPLAY)}</a>
</div>
</div>
</section>"""
    return base_page("Home", content, "home")

@app.route("/pole-pole")
def pole_pole():
    cards = "".join(arch_card_lipa(p) for p in LIPA_PRODUCTS)
    content = f"""
<section class="hero" style="padding:52px 0 14px"><div class="container">
<span class="kicker">pay small small, own it fully</span>
<h1 style="font-family:var(--serif);font-weight:900;font-size:clamp(2rem,4.6vw,3.4rem);color:var(--ink);margin-top:10px">The pole pole <em style="font-family:var(--script);font-style:normal;color:var(--rose)">shelf</em></h1>
<p class="lead" style="max-width:700px;color:#6f5666">Choose your phone, pay a friendly deposit on delivery, then small weekly M-Pesa payments — first one after 7 days — until it is 100% yours.</p>
</div></section>
<section class="container section" style="padding-top:26px"><div class="agrid">{cards}</div></section>
<section class="container" style="padding-bottom:70px">
<div class="cta-band reveal">
<div class="script">not sure what fits?</div>
<h2>WhatsApp us your weekly budget.</h2>
<p style="color:#d9c2cf;margin-top:8px">We will shortlist three phones that love you back — no pressure.</p>
<div class="hero-actions" style="justify-content:center;margin-top:20px">
<a class="btn btn-wa" href="{whatsapp_link('Hi! My weekly budget is KES ___ — which phones fit?')}" target="_blank" rel="noopener">WhatsApp {e(PHONE_DISPLAY)}</a>
<a class="btn btn-rose" href="/apply-now">Apply Now</a>
</div>
</div>
</section>"""
    return base_page("Pole Pole Shelf", content, "pole")

@app.route("/cash-prices")
def cash_prices():
    blocks = ""
    for c in CASH_CATEGORIES:
        cards = "".join(arch_card_cash(p) for p in c["products"])
        blocks += f"""
<section class="container cat-block"><div class="cat-head reveal">
<h3>{e(c['name'])}</h3><span class="count">{len(c['products'])} devices</span><div class="rule"></div></div>
<p class="muted reveal" style="margin:-6px 0 18px;max-width:820px">{e(c['note'])}</p>
<div class="agrid">{cards}</div></section>"""
    content = f"""
<section class="hero" style="padding:52px 0 14px"><div class="container">
<span class="kicker">the full poster, live</span>
<h1 style="font-family:var(--serif);font-weight:900;font-size:clamp(2rem,4.6vw,3.4rem);color:var(--ink);margin-top:10px">Cash prices — <em style="font-family:var(--script);font-style:normal;color:var(--rose)">pay in full, own today</em></h1>
<p class="lead" style="max-width:760px;color:#6f5666">Every price below is the final price from our shop poster. Tap any phone for photos, specs and its own page — or WhatsApp us to reserve it.</p>
<div style="max-width:520px;margin-top:18px"><input id="cashSearch" type="search" placeholder="Search model, storage or series..."></div>
</div></section>
<section class="container section" style="padding-top:30px;padding-bottom:10px">{blocks}</section>
<section class="container" style="padding-bottom:70px">
<div class="cta-band reveal">
<div class="script">seen your price?</div>
<h2>We'll hold it for you.</h2>
<div class="hero-actions" style="justify-content:center;margin-top:20px">
<a class="btn btn-wa" href="{whatsapp_link('Hello! I want to reserve a phone from your cash price list.')}" target="_blank" rel="noopener">WhatsApp {e(PHONE_DISPLAY)}</a>
</div>
</div>
</section>"""
    return base_page("Cash Price List", content, "cash")

@app.route("/device/<slug>")
def device_page(slug):
    p = PRODUCTS_BY_SLUG.get(slug)
    if not p: abort(404)
    fb = placeholder_image(p["name"])
    if p["type"] == "cash":
        wa = whatsapp_link(f"Hello Pro Tech Phone Hub! I want to buy the {p['name']} at {money(p['price'])}.")
        specs = "".join(f"<li>{e(x.strip())}</li>" for x in p["specs"].split("•") if x.strip())
        content = f"""
<section class="container section"><div class="breadcrumbs"><a href="/">Home</a> / <a href="/cash-prices">Cash Prices</a> / <span>{e(p['name'])}</span></div>
<div class="pp-grid">
<div class="pp-visual"><div class="arch"><img src="{e(p['image'])}" alt="{e(p['name'])}" loading="lazy" onerror="this.src='{fb}'"></div>
<span class="stamp">Original • Tested</span></div>
<div class="pp-panel">
<div class="pills"><span class="pill">{e(p['category_name'])}</span><span class="pill rose">Cash price</span><span class="pill">Free Nairobi delivery</span></div>
<h1>{e(p['name'])}</h1>
<p class="muted">{e(p['specs'])}</p>
<div class="ticket"><div class="tk-head">Cash purchase</div>
<div class="tk-row"><span>Pay in full</span><b>{money(p['price'])}</b></div>
<div class="tk-row"><span>Ownership</span><b>Immediately yours</b></div>
<div class="tk-row"><span>Delivery</span><b>Free in Nairobi &amp; surrounds</b></div></div>
<div class="hero-actions">
<a class="btn btn-wa" href="{wa}" target="_blank" rel="noopener">Order on WhatsApp</a>
<a class="btn btn-line" href="tel:{PHONE_TEL}">Call {e(PHONE_DISPLAY)}</a>
</div>
<div class="notice">Prefer pole pole? Many cash phones can also go home on a weekly plan — ask us on WhatsApp.</div>
<h3 style="font-family:var(--serif);color:var(--ink)">Quick specifications</h3>
<ul class="promise-list">{specs}</ul>
</div></div></section>"""
        return base_page(p["name"], content, "cash")
    first = f"{p['apply_name']} ({p['storage'][0]})"
    apply_href = "/apply-now?phone=" + urllib.parse.quote(first)
    wa = whatsapp_link(f"Hello Pro Tech Phone Hub! I want the {p['name']} on pole pole. Preferred storage: {p['storage'][0]}.")
    sb = ""
    for i, s in enumerate(p["storage"]):
        pr = price_for(p, s)
        act = " active" if i == 0 else ""
        ow = money(p["original_weekly"]) + " / week" if p.get("original_weekly") else ""
        od = money(p["original_deposit"]) if p.get("original_deposit") else ""
        sb += f'<button type="button" class="option-btn storage-btn{act}" data-product="{e(p["apply_name"])}" data-storage="{e(s)}" data-weekly="{money(pr["weekly"])} / week" data-deposit="{money(pr["deposit"])}" data-orig-weekly="{ow}" data-orig-deposit="{od}">{e(s)}</button>'
    cb = "".join(f'<button type="button" class="option-btn color-btn{" active" if i == 0 else ""}">{e(c)}</button>' for i, c in enumerate(p["colors"]))
    rows = "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in p["specs"].items())
    r, n, ref, rev_txt = p["review"]
    fp = price_for(p, p["storage"][0])
    if p.get("original_weekly"):
        wk = f'<b id="planWeekly" style="color:var(--rose)">{money(fp["weekly"])} / week</b> <span class="strike">{money(p["original_weekly"])}</span>'
        dp = f'<b id="planDeposit" style="color:var(--rose)">{money(fp["deposit"])}</b> <span class="strike">{money(p["original_deposit"])}</span>'
        stamp = f'<span class="stamp">{e(p["offer_badge"])}</span>'
        offer_row = f'<div class="tk-row"><span>Promotion</span><b style="color:var(--rose)">{e(OFFER_NOTE)}</b></div>'
    else:
        wk = f'<b id="planWeekly">{money(fp["weekly"])} / week</b>'
        dp = f'<b id="planDeposit">{money(fp["deposit"])}</b>'
        stamp = '<span class="stamp">Pole Pole</span>'
        offer_row = ""
    content = f"""
<section class="container section"><div class="breadcrumbs"><a href="/">Home</a> / <a href="/pole-pole">Pole Pole</a> / <span>{e(p['name'])}</span></div>
<div class="pp-grid">
<div class="pp-visual"><div class="arch"><img src="{e(p['image'])}" alt="{e(p['name'])}" loading="lazy" onerror="this.src='{fb}'"></div>{stamp}</div>
<div class="pp-panel">
<div class="pills"><span class="pill">{e(p.get('condition','Ex-UK'))}</span><span class="pill">{e(p['stock'])}</span><span class="pill rose">Deposit on delivery</span></div>
<h1>{e(p['name'])}</h1>
<p class="muted">{e(p['tagline'])}</p>
<div class="ticket"><div class="tk-head">Pole pole plan</div>
<div class="tk-row"><span>Weekly payment</span>{wk}</div>
<div class="tk-row"><span>Goodwill deposit</span>{dp}</div>
<div class="tk-row"><span>First weekly payment</span><b>After 7 days</b></div>{offer_row}</div>
<div class="field"><label>Storage</label><div class="option-row">{sb}</div></div>
<div class="field"><label>Colour</label><div class="option-row">{cb}</div></div>
<div class="hero-actions">
<a class="btn btn-rose" id="applyCta" href="{apply_href}">Take It On Pole Pole</a>
<a class="btn btn-wa" href="{wa}" target="_blank" rel="noopener">Order on WhatsApp</a>
</div>
<h3 style="font-family:var(--serif);color:var(--ink);margin-top:16px">The ProTech promise</h3>
<ul class="promise-list">
<li>Original, fully tested — or your money back</li>
<li>Deposit paid only when the phone is in your hands</li>
<li>Free delivery within Nairobi &amp; surrounding areas</li>
<li>7-day exchange guarantee on any factory fault</li>
</ul>
<h3 style="font-family:var(--serif);color:var(--ink)">Specification</h3>
<table class="spec-table">{rows}</table>
</div></div></section>
<section class="container section" style="padding-top:0">
<div class="sec-head reveal"><div><span class="kicker">shopper love</span><h2>Verified review</h2></div><div class="rule"></div></div>
<div class="review reveal"><div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><strong style="font-family:var(--serif);color:var(--plum)">{e(n)}</strong><span class="stars">{"★"*r}{"☆"*(5-r)}</span></div>
<div class="muted" style="font-size:13px;margin:6px 0">Verified purchase • Ref {e(ref)}</div><p style="color:#6f5666">{e(rev_txt)}</p></div>
</section>"""
    return base_page(p["name"], content, "pole")

@app.route("/apply-now")
def apply_now():
    selected = request.args.get("phone", "")
    options, pricing, meta = "", {}, {}
    for p in LIPA_PRODUCTS:
        for s in p["storage"]:
            label = f"{p['apply_name']} ({s})"
            pr = price_for(p, s)
            pricing[label] = [pr["deposit"], pr["weekly"]]
            meta[label] = {"img": p["image"], "cond": p.get("condition", "Ex-UK"), "store": s,
                           "orig_dep": p.get("original_deposit"), "orig_wk": p.get("original_weekly")}
            sel = " selected" if label == selected else ""
            options += f'<option value="{e(label)}"{sel}>{e(label)}</option>'
    ps = "<script>window.PH_PRICING = " + json.dumps(pricing) + ";window.PH_META = " + json.dumps(meta) + ";</script>"
    content = f"""
<section class="hero" style="padding:46px 0 10px"><div class="container" style="max-width:840px">
<span class="kicker">join the protech family</span>
<h1 style="font-family:var(--serif);font-weight:900;font-size:clamp(2rem,4.6vw,3.4rem);color:var(--ink);margin-top:10px">Apply in <em style="font-family:var(--script);font-style:normal;color:var(--rose)">under 2 minutes</em></h1>
<p class="lead" style="color:#6f5666">A decision usually takes about 30 minutes. You pay your deposit only when the phone is delivered to you.</p>
</div></section>
<section class="container section" style="padding-top:22px"><div class="pp-grid">
<div class="ticket reveal" style="margin:0">
<div class="tk-head">Your details — private &amp; safe</div>
<div style="padding:20px">
<form id="applicationForm">
<div class="field"><label>Preferred phone</label><select id="phoneModel" name="phone_model" required><option value="">Choose your phone...</option>{options}</select></div>
<div class="form-grid">
<div class="field"><label>Full name</label><input id="full_name" name="full_name" required placeholder="Your full name"></div>
<div class="field"><label>Phone number</label><input id="phone_number" name="phone_number" type="tel" required placeholder="07XX XXX XXX"></div>
</div>
<div class="form-grid">
<div class="field"><label>National ID number</label><input id="id_number" name="id_number" required placeholder="ID number"></div>
<div class="field"><label>Region / location</label><select id="region" name="region" required><option value="">Choose...</option><option>Nairobi</option><option>Kiambu</option><option>Nakuru</option><option>Mombasa</option><option>Other</option></select></div>
</div>
<button class="btn btn-rose" type="submit" style="width:100%">Send My Application ✦</button>
<p class="muted" style="font-size:12.5px;margin-top:10px;text-align:center">You'll then be guided through a short, secure verification.</p>
</form>
</div></div>
<div class="ticket reveal" style="margin:0;position:sticky;top:96px">
<div class="tk-head">Your summary</div>
<div style="padding:20px">
<div style="display:flex;align-items:center;gap:12px;padding:12px;border:1px solid var(--line);border-radius:12px;background:var(--cream);margin-bottom:14px">
<img id="summaryImg" alt="Selected phone" src="" style="display:none;width:70px;height:70px;object-fit:contain;background:#fff;border:1px solid var(--line);border-radius:10px">
<div><strong id="summaryName" style="font-family:var(--serif);color:var(--plum)">No phone chosen yet</strong><div class="muted" id="summaryMeta" style="font-size:13px">Pick a model to see its plan.</div></div>
</div>
<div class="tk-row"><span>Deposit</span><b id="depositValue">KES 0</b></div>
<div class="tk-row"><span>Weekly</span><b id="weeklyValue">KES 0</b></div>
<div class="tk-row"><span>First payment</span><b>After 7 days</b></div>
<ul class="promise-list" style="margin-top:14px">
<li>Decision in about 30 minutes</li>
<li>Deposit paid on delivery</li>
<li>Free delivery in Nairobi &amp; environs</li>
<li>7-day exchange guarantee on factory faults</li>
</ul>
<div class="hero-actions">
<a class="btn btn-wa btn-sm" href="{whatsapp_link('Kindly help me with my Pro Tech application.')}" target="_blank" rel="noopener">WhatsApp help</a>
<a class="btn btn-line btn-sm" href="tel:{PHONE_TEL}">Call {e(PHONE_DISPLAY)}</a>
</div>
</div></div>
</div></section>
<div class="modal" id="applicationModal"><div class="modal-box">
<button class="modal-close" data-close="applicationModal" aria-label="Close">×</button>
<input type="hidden" id="docFullName"><input type="hidden" id="docPhoneNumber"><input type="hidden" id="docIdNumber">
<input type="hidden" id="docRegion"><input type="hidden" id="docPhoneModel"><input type="hidden" id="docSubmissionId">
<div class="doc-progress"><span id="docProgressBar" style="width:33%"></span></div>
<p class="notice" id="journeyMsg" style="margin:0 0 14px">Lovely start! Add your M-Pesa statement — 30 seconds only.</p>
<div id="stepMpesa"><div class="ticket" style="margin:0"><div class="tk-head">M-Pesa statement (6 months)</div><div style="padding:20px">
<div class="notice"><strong>Why we ask:</strong> this is simply your affordability check, so your weekly plan stays comfortable. It stays private.</div>
<ul class="promise-list"><li>Dial *234# → Option 5 → 1 → 1 → 1 → 4</li><li>The PDF + password arrive on your email &amp; SMS</li></ul>
<div class="field"><label>Upload the M-Pesa PDF</label><label class="file-label"><input type="file" id="fMpesa" accept="application/pdf"><span>Upload M-Pesa PDF</span><strong>✦</strong></label></div>
<div class="field"><label>Statement password</label><input type="text" id="fMpesaPw" placeholder="Enter password"></div>
<button class="btn btn-rose" type="button" id="contMpesa" style="width:100%">Save &amp; Continue</button></div></div></div>
<div id="stepIdentity" class="hidden"><div class="ticket" style="margin:0"><div class="tk-head">Identity check</div><div style="padding:20px">
<div class="notice"><strong>Why we ask:</strong> we're trusting you with a phone — this confirms it's really you, and protects your ID from misuse.</div>
<div class="field"><label>Front of National ID</label><label class="file-label"><input type="file" id="fIdF" accept="image/*"><span>Upload front photo</span><strong>✦</strong></label></div>
<div class="field"><label>Back of National ID</label><label class="file-label"><input type="file" id="fIdB" accept="image/*"><span>Upload back photo</span><strong>✦</strong></label></div>
<div class="field"><label>Official selfie</label><label class="file-label"><input type="file" id="fSelfie" accept="image/*"><span>Take / upload selfie</span><strong>✦</strong></label></div>
<button class="btn btn-rose" type="button" id="contIdentity" style="width:100%">Save &amp; Continue</button></div></div></div>
<div id="stepKin" class="hidden"><div class="ticket" style="margin:0"><div class="tk-head">Next of kin</div><div style="padding:20px">
<div class="notice"><strong>Why we ask:</strong> if we ever miss you, we need someone close we can reach. Standard for any financing plan.</div>
<div class="form-grid">
<div class="field"><label>Full name</label><input id="kName" placeholder="Next of kin name"></div>
<div class="field"><label>Phone number</label><input id="kPhone" type="tel" placeholder="Next of kin phone"></div>
</div>
<div class="form-grid">
<div class="field"><label>Kin ID number</label><input id="kId" placeholder="Kin ID number"></div>
<div class="field"><label>Relationship</label><select id="kRel"><option value="">Choose...</option><option>Parent</option><option>Sibling</option><option>Spouse</option><option>Child</option><option>Aunt/Uncle</option><option>Cousin</option><option>Friend</option></select></div>
</div>
<button class="btn btn-rose" type="button" id="finBtn" style="width:100%">Submit Final Details</button></div></div></div>
<div id="stepDone" class="hidden" style="text-align:center">
<div class="done-badge">✓</div>
<h2 style="font-family:var(--serif);color:var(--ink)">Application complete!</h2>
<p class="muted">You're now in our review queue — we'll be in touch shortly.</p>
<div class="done-list"><div>Contact details saved</div><div>M-Pesa statement received</div><div>Identity verified</div><div>Next of kin added</div></div>
<div class="ticket" style="max-width:420px;margin:14px auto"><div class="tk-row"><span>Estimated review</span><b>&lt; 30 minutes</b></div><div class="tk-row"><span>Status</span><b style="color:var(--green)">In queue ✦</b></div></div>
<div class="hero-actions" style="justify-content:center">
<a class="btn btn-wa" target="_blank" rel="noopener" id="doneWa" href="#">Track on WhatsApp</a>
<a class="btn btn-line" href="/">Back home</a>
</div></div>
</div></div>"""
    return base_page("Apply Now", content, "")

@app.route("/how-it-works")
def how_it_works():
    content = f"""
<section class="hero" style="padding:52px 0 14px"><div class="container">
<span class="kicker">simple, gentle, clear</span>
<h1 style="font-family:var(--serif);font-weight:900;font-size:clamp(2rem,4.6vw,3.4rem);color:var(--ink);margin-top:10px">How <em style="font-family:var(--script);font-style:normal;color:var(--rose)">ProTech</em> works</h1>
</div></section>
<section class="container section" style="padding-top:26px"><div class="steps-grid">
<div class="step reveal"><b class="n">1</b><h3>Choose your favourite</h3><p class="muted">Browse the pole pole shelf or the cash price list. Every phone is original and fully tested.</p></div>
<div class="step reveal"><b class="n">2</b><h3>Pick how to pay</h3><p class="muted">Cash in full and own it today — or pole pole with a friendly deposit and small weekly payments.</p></div>
<div class="step reveal"><b class="n">3</b><h3>We deliver, you inspect</h3><p class="muted">Free delivery in Nairobi &amp; surrounds. Check the phone, love the phone, then pay your deposit.</p></div>
<div class="step reveal"><b class="n">4</b><h3>Pay small small</h3><p class="muted">Weekly M-Pesa payments, first one after 7 days. When the plan completes, the phone is 100% yours.</p></div>
</div></section>
<section class="container" style="padding-bottom:70px">
<div class="cta-band reveal">
<div class="script">your phone is waiting</div>
<h2>Start today — it takes two minutes.</h2>
<div class="hero-actions" style="justify-content:center;margin-top:20px">
<a class="btn btn-rose" href="/apply-now">Apply Now</a>
<a class="btn btn-wa" href="{whatsapp_link('Hello! I have a question before applying.')}" target="_blank" rel="noopener">Ask on WhatsApp</a>
</div>
</div>
</section>"""
    return base_page("How It Works", content, "how")

@app.route("/faq")
def faq():
    faqs = [
     ("Are your phones original?", "Yes — 100% original. Every device is hand-inspected and fully tested before it is listed. If anything is ever not as described, our 7-day exchange guarantee covers you."),
     ("How does the pole pole plan work?", "You pay a goodwill deposit when we deliver, then small weekly M-Pesa payments — first one after 7 days. When the plan ends, the phone is fully yours."),
     ("How fast is approval?", "Usually about 30 minutes after your application and documents are complete."),
     ("Do you deliver?", "Free within Nairobi & surrounding areas. Upcountry we arrange safe, tracked courier delivery at a small fare."),
     ("What do I need to apply?", "Your National ID, a 6-month M-Pesa statement, a clear selfie, and next-of-kin details. That's all."),
     ("Can I pay cash in full?", "Absolutely — the cash price list shows final poster prices. Pay in full and the phone is immediately yours."),
     ("What if the phone develops a fault?", "Factory faults within 7 days are exchanged free. Beyond that, we walk with you to the nearest authorised service centre and follow up until it's resolved."),
    ]
    items = "".join(f'<details class="faq-item reveal"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in faqs)
    content = f"""
<section class="hero" style="padding:52px 0 14px"><div class="container">
<span class="kicker">we love questions</span>
<h1 style="font-family:var(--serif);font-weight:900;font-size:clamp(2rem,4.6vw,3.4rem);color:var(--ink);margin-top:10px">Frequently asked <em style="font-family:var(--script);font-style:normal;color:var(--rose)">questions</em></h1>
</div></section>
<section class="container section" style="padding-top:26px;max-width:860px">{items}
<div class="cta-band reveal" style="margin-top:26px">
<div class="script">still curious?</div><h2>Ask us anything — no pressure.</h2>
<div class="hero-actions" style="justify-content:center;margin-top:18px">
<a class="btn btn-wa" href="{whatsapp_link('Hello! I have a question.')}" target="_blank" rel="noopener">WhatsApp {e(PHONE_DISPLAY)}</a>
<a class="btn btn-rose" href="/apply-now">Apply Now</a>
</div></div>
</section>"""
    return base_page("FAQ", content, "faq")

@app.route("/health")
def health(): return jsonify({"ok": True, "app": SHOP_NAME})

@app.route("/favicon.ico")
def favicon(): return "", 204

@app.route("/api/apply", methods=["POST"])
def api_apply():
    data = request.get_json(silent=True) or {}
    if not data: return jsonify({"ok": False, "error": "Empty submission."}), 400
    forwarded = post_to_google_sheet(data)
    saved = save_application_local(data) if not forwarded else True
    if forwarded or saved:
        return jsonify({"ok": True, "message": "Received with love."})
    return jsonify({"ok": False, "error": "Could not save application."}), 500

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    msg = str(data.get("message", "")).strip().lower()
    if any(w in msg for w in ["human", "agent", "owner", "talk", "call", "whatsapp", "msaada"]):
        return jsonify({"ok": True, "content": "Of course! The shop line is open — tap below and we'll reply personally.",
                        "links": [{"cta": f"WhatsApp {PHONE_DISPLAY}", "url": whatsapp_link("Hello Pro Tech Phone Hub! I need human help.")}, {"cta": f"Call {PHONE_DISPLAY}", "url": "tel:" + PHONE_TEL}]})
    if any(w in msg for w in ["pole pole", "plan", "deposit", "weekly", "installment", "how does"]):
        return jsonify({"ok": True, "content": "Pole pole is simple: pay a friendly deposit when we deliver, then small weekly M-Pesa payments — first one after 7 days. When the plan ends, the phone is fully yours.",
                        "links": [{"cta": "See pole pole phones", "url": "/pole-pole"}, {"cta": "Apply now", "url": "/apply-now"}]})
    if any(w in msg for w in ["deliver", "delivery", "shipping"]):
        return jsonify({"ok": True, "content": "Delivery is free within Nairobi & surrounding areas. Upcountry we arrange safe tracked courier at a small fare.", "links": []})
    if any(w in msg for w in ["under", "budget", "cheap", "afford", "50k", "30k", "20k"]):
        m = re.search(r"(\d{2,3})\s*k", msg)
        cap = int(m.group(1)) * 1000 if m else 50000
        picks = [p for p in CASH_PRODUCTS.values() if p["price"] <= cap][:3]
        if picks:
            return jsonify({"ok": True, "content": f"Lovely budget! Here are originals under {money(cap)}:",
                            "links": [{"cta": p["name"], "url": "/device/" + p["slug"]} for p in picks]})
    items = search_items(msg, 3)
    if items:
        lines = "; ".join(i["line"] for i in items)
        return jsonify({"ok": True, "content": "I found these for you: " + lines + ".",
                        "links": [{"cta": i["name"], "url": "/device/" + i["slug"]} for i in items]})
    return jsonify({"ok": True, "content": "I can help with prices, plans, delivery or applications — or tap below to see today's collection.",
                    "links": [{"cta": "Pole pole shelf", "url": "/pole-pole"}, {"cta": "Cash price list", "url": "/cash-prices"}, {"cta": f"WhatsApp {PHONE_DISPLAY}", "url": whatsapp_link("Hello Pro Tech Phone Hub!")}]})

@app.errorhandler(404)
def not_found(err):
    content = """
<section class="container section" style="text-align:center;padding:90px 0">
<span class="kicker">oops</span><h1 style="font-family:var(--serif);font-weight:900;color:var(--ink);margin-top:8px">This page wandered off</h1>
<p class="muted">Let's get you back to the phones.</p>
<div class="hero-actions" style="justify-content:center;margin-top:18px">
<a class="btn btn-rose" href="/">Back home</a><a class="btn btn-line" href="/cash-prices">Cash prices</a>
</div></section>"""
    return base_page("Not found", content, ""), 404

@app.errorhandler(500)
def server_error(err):
    return base_page("Oops", "<section class='container section' style='text-align:center;padding:90px 0'><h1 style=\"font-family:var(--serif)\">A small bump — please try again.</h1></section>", ""), 500

@app.errorhandler(Exception)
def handle_unexpected(err):
    if isinstance(err, HTTPException):
        return base_page("Oops", "<section class='container section' style='text-align:center;padding:90px 0'><h1 style=\"font-family:var(--serif)\">Page error.</h1></section>", ""), err.code or 500
    return base_page("Oops", "<section class='container section' style='text-align:center;padding:90px 0'><h1 style=\"font-family:var(--serif)\">A small bump — please try again.</h1></section>", ""), 500

handler = app
if __name__ == "__main__":
    app.run(debug=False)
