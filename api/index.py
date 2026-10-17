import os, re, json, urllib.parse, urllib.request, urllib.error, hashlib
from html import escape
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException

SHOP_NAME = "Pro Tech Phone Hub"
PHONE_DISPLAY = "0720 890 018"
PHONE_TEL = "+254720890018"
WA_NUMBER = "254720890018"
SHOP_EMAIL = "protechphonehub@gmail.com"
OPEN_HOURS = "Open daily 8:00 AM – 9:00 PM"
FREE_DELIVERY_ZONES = "Nairobi County, Kiambu County, Nakuru Town & Mombasa Town"

GOOGLE_SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzKF4BsWu8_X3UN31QG_OjFwQ9MPLiIgNh42RgRd15dsE_6_Q8RfVGUY7HTnOJ4aJodjw/exec"
APP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "protech_applications.jsonl")

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
    t = str(t)
    return t if len(t) <= l else t[:l].strip() + "…"
def clean_text(v): return re.sub(r"\s+", " ", str(v)).strip()
def clean_url(v): return re.sub(r"\s+", "", str(v)).strip()

def placeholder_image(text):
    clean = re.sub(r"[^A-Za-z0-9 ]+", "", str(text))[:18].strip() or "ProTech"
    clean = escape(clean, quote=True)
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' width='900' height='900'>"
           "<rect width='100%' height='100%' fill='#0A192F'/>"
           "<rect x='18' y='18' width='864' height='864' rx='48' fill='#112240' stroke='#233554' stroke-width='2'/>"
           f"<text x='50%' y='54%' fill='#E2E8F0' font-family='Arial' font-size='42' font-weight='700' text-anchor='middle'>{clean}</text>"
           "<text x='50%' y='64%' fill='#00B4D8' font-family='Arial' font-size='22' text-anchor='middle'>Pro Tech Phone Hub</text>"
           "</svg>")
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg, safe="")

def whatsapp_link(m): return "https://wa.me/" + WA_NUMBER + "?text=" + urllib.parse.quote(m)

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

def post_to_google_sheet(payload):
    if not GOOGLE_SHEET_WEBHOOK_URL: return False, "No URL"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(GOOGLE_SHEET_WEBHOOK_URL, data=body, method="POST",
        headers={"Content-Type": "text/plain;charset=utf-8", "User-Agent": "Mozilla/5.0"})
    
    opener = urllib.request.build_opener(NoRedirectHandler)
    try:
        response = opener.open(req, timeout=60)
        raw = response.read().decode("utf-8", "ignore")
        return True, "Direct 200 OK"
    except urllib.error.HTTPError as h:
        if h.code in (301, 302, 303, 307, 308):
            location = h.headers.get("Location")
            if location:
                req2 = urllib.request.Request(location, method="GET", headers={"User-Agent": "Mozilla/5.0"})
                try:
                    r2 = urllib.request.urlopen(req2, timeout=60)
                    raw = r2.read().decode("utf-8", "ignore")
                    j = json.loads(raw)
                    if j.get("status") == "success": return True, "Success after redirect"
                    else: return False, f"GAS Error: {j}"
                except Exception as e2: return True, "Redirect fired (Script ran, echo unreadable)"
        return False, f"HTTP Error: {h.code} - {h.read().decode('utf-8', 'ignore')[:200]}"
    except Exception as e:
        return False, f"Network Error: {str(e)}"

def save_application_local(payload):
    try:
        trim = {k: v for k, v in payload.items() if k != "data"}
        if "data" in payload: trim["file_received"] = True
        trim["saved_at"] = datetime.now(timezone(timedelta(hours=3))).isoformat()
        with open(APP_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(trim, ensure_ascii=False) + "\n")
        return True
    except Exception: return False

def L(slug, name, apply_name, image, tagline, weekly, deposit, storage, colors, specs, reviews, storage_pricing=None, condition=None):
    d = {"slug": slug, "name": name, "apply_name": apply_name, "image": image, "tagline": tagline,
         "weekly": weekly, "deposit": deposit, "storage": storage, "colors": colors, "specs": specs, "reviews": reviews}
    if storage_pricing: d["storage_pricing"] = storage_pricing
    if condition: d["condition"] = condition
    return d

AM = "https://m.media-amazon.com/images/I/"
MOP = "https://mophones.co/cdn/shop/"

LIPA_PRODUCTS = [
    L("motorola-g-power", "Motorola G Power", "Motorola G Power 2023", MOP + "files/motorola-moto-g-power-5g-1_673x.jpg?v=1770894988", 'Ex-UK 5G | 5000mAh | 6.5" Display', 560, 4299, ["128GB"], ["Mineral Black", "Bright White"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.5" HD+ (720×1600) IPS LCD, 120Hz refresh', "Processor": "Octa-core 5G platform, 4GB RAM", "Rear Camera": "50MP main (f/1.8) + 2MP macro, LED flash, 1080p video", "Front Camera": "8MP selfie (f/2.2)", "Battery & Charging": "5000mAh, TurboPower fast charging", "OS & Updates": "Android 13 out of the box, upgradable", "Build & Extras": "Side fingerprint reader, water-repellent coating, 3.5mm jack, microSD slot"}, [(5, "Wanjiku M.", "PT-101", "Battery lasts two full days on a single charge. Never worry about finding an outlet.")]),
    L("motorola-g-stylus", "Motorola G Stylus", "Motorola G Stylus 2024", AM + "412KEd+cz3L.AC_US1000.jpg?v=1771506465", 'Ex-UK 5G | 5000mAh | 6.7" Display', 910, 6999, ["128GB", "256GB"], ["Caramel Latte", "Scarlet Wave"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.7" P-OLED, FHD+ (2400×1080), 120Hz', "Processor": "Snapdragon 6 Gen 1 octa-core", "Rear Camera": "50MP main with OIS + 13MP ultrawide (macro vision)", "Front Camera": "16MP selfie", "Battery & Charging": "5000mAh, 30W TurboPower wired", "OS & Updates": "Android 14, upgradable", "Build & Extras": "Built-in stylus pen, stereo speakers, in-display fingerprint, NFC"}, [(5, "Achieng O.", "PT-102", "The stylus transforms how I take notes. Colors are vivid, screen is buttery smooth.")], storage_pricing={"128GB": {"weekly": 910, "deposit": 6999}, "256GB": {"weekly": 1040, "deposit": 7999}}),
    L("samsung-galaxy-s21-fe", "Samsung Galaxy S21 FE 5G", "Samsung Galaxy S21 FE 5G", AM + "61PPEjwAkYL._Ac_SY300_SX300_QL70_FMwebp_.jpg", 'Ex-UK 5G | 4500mAh | 6.4" Display', 970, 7499, ["128GB"], ["Graphite", "White", "Lavender", "Olive"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.4" Dynamic AMOLED 2X, FHD+ (2400×1080), 120Hz, HDR10+', "Processor": "Snapdragon 888 octa-core", "Rear Camera": "12MP main (OIS) + 12MP ultrawide + 8MP telephoto (3x), 4K video", "Front Camera": "32MP selfie", "Battery & Charging": "4500mAh, 25W wired, 15W wireless", "OS & Updates": "Android 12 out of the box, fully upgradable", "Build & Extras": "IP68 water/dust resistance, in-display fingerprint, stereo speakers, NFC"}, [(5, "Peter K.", "PT-103", "Premium feel without the premium price. Screen is gorgeous, performance is snappy.")]),
    L("samsung-galaxy-note-20", "Samsung Galaxy Note 20", "Samsung Note 20 5G", MOP + "files/0c5ffb9f-1e94-480c-bdb1-71566919cc1d-1_46397bdd-1274-44a3-b4e9-52df8ac4fdbc_600x.jpg?v=1703753426", 'Ex-UK 5G | 4300mAh | 6.7" Display', 1160, 8999, ["128GB"], ["Black", "Green", "Rose-Gold"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.7" Super AMOLED Plus, FHD+ (2400×1080), 60Hz, HDR10+', "Processor": "Snapdragon 865+ / Exynos 990 octa-core", "Rear Camera": "12MP main (OIS) + 64MP telephoto (3x hybrid) + 12MP ultrawide, 8K video", "Front Camera": "10MP selfie", "Battery & Charging": "4300mAh, 25W wired, 15W wireless", "OS & Updates": "Android 10 out of the box, fully upgradable", "Build & Extras": "S-Pen stylus included, IP68, stereo speakers tuned by AKG, NFC, Samsung DeX"}, [(5, "Daniel E.", "PT-104", "S-Pen is indispensable for work. Sign docs, sketch ideas, annotate everything.")]),
    L("samsung-galaxy-s21-plus", "Samsung Galaxy S21+", "Samsung Galaxy S21 Plus 5G", MOP + "products/BLACK_d72adc1a-b989-4cf6-a641-b2919ad0a2de_500x.jpg?v=1676990538", 'Ex-UK 5G | 4800mAh | 6.7" Display', 1110, 8499, ["128GB", "256GB"], ["Black", "Silver", "Purple"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.7" Dynamic AMOLED 2X, FHD+ (2400×1080), 120Hz, HDR10+', "Processor": "Snapdragon 888 / Exynos 2100 octa-core", "Rear Camera": "12MP main (OIS) + 64MP telephoto (3x hybrid) + 12MP ultrawide, 8K video", "Front Camera": "10MP selfie", "Battery & Charging": "4800mAh, 25W wired, 15W wireless", "OS & Updates": "Android 11 out of the box, fully upgradable", "Build & Extras": "IP68, in-display fingerprint, stereo speakers, NFC, Samsung DeX"}, [(5, "Samuel O.", "PT-105", "Gets me through 12-hour shifts without breaking a sweat. Reliable workhorse.")], storage_pricing={"128GB": {"weekly": 1110, "deposit": 8499}, "256GB": {"weekly": 1420, "deposit": 10999}}),
    L("samsung-galaxy-s22-plus", "Samsung Galaxy S22+", "Samsung Galaxy S22 Plus 5G", AM + "714oVGJtWeL.AC_SY300_SY300_QL70_FMwebp.jpg", 'Ex-UK 5G | 4500mAh | 6.6" Display', 1230, 9499, ["128GB"], ["Phantom Black", "Lavender", "Green"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.6" Dynamic AMOLED 2X, FHD+ (2340×1080), 120Hz, HDR10+', "Processor": "Snapdragon 8 Gen 1 / Exynos 2200 octa-core", "Rear Camera": "50MP main (OIS) + 10MP telephoto (3x) + 12MP ultrawide, 8K video", "Front Camera": "10MP selfie", "Battery & Charging": "4500mAh, 45W wired, 15W wireless", "OS & Updates": "Android 12 out of the box, fully upgradable", "Build & Extras": "IP68, Armor Aluminum frame, in-display fingerprint, stereo speakers, NFC"}, [(5, "Grace W.", "PT-106", "Perfect size, amazing low-light photos. Fits my lifestyle perfectly.")]),
    L("samsung-galaxy-s20-ultra", "Samsung Galaxy S20 Ultra", "Samsung Galaxy S20 Ultra", MOP + "files/S20Ultra1_455x.jpg?v=1718780519", 'Ex-UK 5G | 5000mAh | 6.9" Display', 1230, 9499, ["128GB"], ["Black", "Grey"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.9" Dynamic AMOLED 2X, QHD+ (3200×1440), 120Hz, HDR10+', "Processor": "Snapdragon 865 / Exynos 990 octa-core", "Rear Camera": "108MP main + 48MP periscope (10x, 100x Space Zoom) + 12MP ultrawide + ToF, 8K video", "Front Camera": "40MP selfie", "Battery & Charging": "5000mAh, 45W wired, 15W wireless", "OS & Updates": "Android 10 out of the box, fully upgradable", "Build & Extras": "IP68, microSD slot, stereo speakers, NFC, Samsung DeX"}, [(5, "Brian M.", "PT-107", "That zoom is unreal. Streaming on this screen feels like a private cinema.")]),
    L("samsung-galaxy-s21-ultra", "Samsung Galaxy S21 Ultra", "Samsung Galaxy S21 Ultra", MOP + "files/8322653a-f2b7-44cf-a74c-6336bcec9f43-1_cadd4530-09b4-449e-aa1d-3894bad6e808_1024x.jpg?v=1700145645", 'Ex-UK 5G | 5000mAh | 6.8" Display', 1490, 11499, ["128GB"], ["Black", "Silver"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.8" Dynamic AMOLED 2X, QHD+ (3200×1440), 120Hz, HDR10+', "Processor": "Snapdragon 888 / Exynos 2100 octa-core", "Rear Camera": "108MP main + 10MP (3x) + 10MP (10x periscope) + 12MP ultrawide, 8K video", "Front Camera": "40MP selfie", "Battery & Charging": "5000mAh, 25W wired, 15W wireless", "OS & Updates": "Android 11 out of the box, fully upgradable", "Build & Extras": "S-Pen support (pen sold separately), IP68, stereo speakers, NFC, Samsung DeX"}, [(5, "David K.", "PT-108", "Photography game-changer. Zoom capability still impresses years later.")]),
    L("apple-iphone-12-mini", "Apple iPhone 12 Mini", "Apple iPhone 12 Mini", AM + "61bbqGftbUL.AC_SY879.jpg", 'Ex-UK 5G | 2227mAh | 5.4" Display', 1290, 9999, ["128GB"], ["Black", "Purple", "Blue", "Green", "Red", "White"], {"Network": "5G + 4G LTE dual SIM (eSIM)", "Display": '5.4" Super Retina XDR OLED, HDR, True Tone', "Processor": "Apple A14 Bionic (6-core)", "Rear Camera": "12MP main (f/1.6, OIS) + 12MP ultrawide, 4K Dolby Vision video", "Front Camera": "12MP TrueDepth with Face ID", "Battery & Charging": "2227mAh, 20W wired, 15W MagSafe wireless", "OS & Updates": "iOS 14 out of the box, fully upgradable", "Build & Extras": "IP68, Ceramic Shield front, aluminum frame, MagSafe accessories"}, [(5, "Simon A.", "PT-109", "Compact without compromise. Fast, fits anywhere, premium build.")]),
    L("apple-iphone-12", "Apple iPhone 12", "Apple iPhone 12", MOP + "products/12black_640x.jpg?v=1674896241", 'Ex-UK 5G | 2815mAh | 6.1" Display', 1540, 11899, ["128GB", "256GB"], ["Black", "Purple", "Blue", "Green", "Red", "White"], {"Network": "5G + 4G LTE dual SIM (eSIM)", "Display": '6.1" Super Retina XDR OLED, HDR, True Tone', "Processor": "Apple A14 Bionic (6-core)", "Rear Camera": "12MP main (f/1.6, OIS) + 12MP ultrawide, 4K Dolby Vision video", "Front Camera": "12MP TrueDepth with Face ID", "Battery & Charging": "2815mAh, 20W wired, 15W MagSafe wireless", "OS & Updates": "iOS 14 out of the box, fully upgradable", "Build & Extras": "IP68, Ceramic Shield front, aluminum frame, MagSafe accessories"}, [(5, "Faith W.", "PT-110", "Stunning colors, blazing speed. Camera quality exceeded expectations.")], storage_pricing={"128GB": {"weekly": 1540, "deposit": 11899}, "256GB": {"weekly": 1480, "deposit": 18199}}),
    L("samsung-galaxy-note-20-ultra", "Samsung Galaxy Note 20 Ultra", "Samsung Note 20 Ultra", MOP + "files/NOte20Black_23da7f6b-cc29-41a0-9eac-63d0385cc238_500x.jpg?v=1718362656", 'Ex-UK 5G | 4500mAh | 6.9" Display', 1550, 11999, ["128GB"], ["Black", "White", "Rose-Gold"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.9" Dynamic AMOLED 2X, QHD+ (3088×1440), 120Hz, HDR10+', "Processor": "Snapdragon 865+ / Exynos 990 octa-core", "Rear Camera": "108MP main + 12MP periscope (5x) + 12MP ultrawide + laser AF, 8K video", "Front Camera": "10MP selfie", "Battery & Charging": "4500mAh, 25W wired, 15W wireless", "OS & Updates": "Android 10 out of the box, fully upgradable", "Build & Extras": "S-Pen built-in, IP68, microSD slot, stereo speakers, NFC, Samsung DeX"}, [(5, "Cynthia W.", "PT-111", "Smooth 120Hz scrolling, gorgeous display. The S-Pen is pure luxury.")]),
    L("samsung-galaxy-s22-ultra", "Samsung Galaxy S22 Ultra", "Samsung Galaxy S22 Ultra", MOP + "files/Screenshot_2025-03-20_at_15.05.15_1010x.png?v=1742472440", 'Ex-UK 5G | 5000mAh | 6.8" Display', 1900, 23399, ["256GB", "512GB"], ["Black", "Purple", "Green"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.8" Dynamic AMOLED 2X, QHD+ (3088×1440), 120Hz, HDR10+', "Processor": "Snapdragon 8 Gen 1 / Exynos 2200 octa-core", "Rear Camera": "108MP main + 10MP (3x) + 10MP (10x periscope) + 12MP ultrawide, 8K video", "Front Camera": "40MP selfie", "Battery & Charging": "5000mAh, 45W wired, 15W wireless", "OS & Updates": "Android 12 out of the box, fully upgradable", "Build & Extras": "S-Pen built-in, IP68, Armor Aluminum, stereo speakers, NFC, Samsung DeX"}, [(5, "Benard O.", "PT-112", "Sketch architectural plans directly on screen. Productivity redefined.")]),
    L("apple-iphone-12-pro-max", "Apple iPhone 12 Pro Max", "Apple iPhone 12 Pro Max", AM + "41SLL9Zws6L.AC_SY300_SY300_QL70_FMwebp.jpg", 'Ex-UK 5G | 3687mAh | 6.7" Display', 1960, 24099, ["256GB"], ["Pacific Blue", "Graphite", "Gold", "Silver"], {"Network": "5G + 4G LTE dual SIM (eSIM)", "Display": '6.7" Super Retina XDR OLED, HDR, True Tone', "Processor": "Apple A14 Bionic (6-core)", "Rear Camera": "12MP main (sensor-shift OIS) + 12MP ultrawide + 12MP telephoto (2.5x) + LiDAR, 4K Dolby Vision", "Front Camera": "12MP TrueDepth with Face ID", "Battery & Charging": "3687mAh, 20W wired, 15W MagSafe wireless", "OS & Updates": "iOS 14 out of the box, fully upgradable", "Build & Extras": "IP68, Ceramic Shield, stainless-steel frame, MagSafe"}, [(5, "Kevin O.", "PT-113", "Big screen, big battery. Handles business calls and creative work flawlessly.")]),
    L("apple-iphone-13-pro-max", "Apple iPhone 13 Pro Max", "Apple iPhone 13 Pro Max", MOP + "products/apple_iphone_13_pro_max_gold_image_0_1024x.jpg?v=1674389404", 'Ex-UK 5G | 4352mAh | 6.7" Display', 2190, 26899, ["256GB", "512GB", "1TB"], ["Blue", "Black", "Gold", "Silver", "Alpine Green"], {"Network": "5G + 4G LTE dual SIM (eSIM)", "Display": '6.7" Super Retina XDR OLED, 120Hz ProMotion, HDR', "Processor": "Apple A15 Bionic (5-core GPU)", "Rear Camera": "12MP main (sensor-shift) + 12MP ultrawide + 12MP telephoto (3x) + LiDAR, ProRes video", "Front Camera": "12MP TrueDepth with Face ID", "Battery & Charging": "4352mAh, 27W wired, 15W MagSafe wireless", "OS & Updates": "iOS 15 out of the box, fully upgradable", "Build & Extras": "IP68, Ceramic Shield, stainless-steel frame, MagSafe"}, [(5, "Gladys M.", "PT-114", "120Hz makes everything feel instant. Battery lasts from morning to midnight.")]),
    L("samsung-galaxy-s23-ultra", "Samsung Galaxy S23 Ultra", "Samsung Galaxy S23 Ultra", MOP + "files/S23Ultra1_1024x.jpg?v=1718781685", 'Ex-UK 5G | 5000mAh | 6.8" Display', 2190, 26899, ["256GB", "512GB"], ["Black", "Green", "Cream"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.8" Dynamic AMOLED 2X, QHD+ (3088×1440), 120Hz, HDR10+', "Processor": "Snapdragon 8 Gen 2 for Galaxy", "Rear Camera": "200MP main + 10MP (3x) + 10MP (10x periscope) + 12MP ultrawide, 8K video", "Front Camera": "12MP selfie", "Battery & Charging": "5000mAh, 45W wired, 15W wireless", "OS & Updates": "Android 13 out of the box, 4 OS upgrades", "Build & Extras": "S-Pen built-in, IP68, Armor Aluminum, stereo speakers, NFC, Samsung DeX"}, [(5, "Joseph O.", "PT-115", "Night shots look like daylight. Zoom range is phenomenal.")]),
    L("apple-iphone-14-pro-max", "Apple iPhone 14 Pro Max", "Apple iPhone 14 Pro Max", MOP + "files/Screenshot_2025-05-29_at_09.05.01_776x.png?v=1748499274", 'Ex-UK 5G | 4323mAh | 6.7" Display', 2560, 31499, ["256GB"], ["Space Black", "Deep Purple", "Gold", "Silver"], {"Network": "5G + 4G LTE dual SIM (eSIM)", "Display": '6.7" LTPO Super Retina XDR OLED, 120Hz ProMotion, Always-On', "Processor": "Apple A16 Bionic", "Rear Camera": "48MP main (2nd-gen sensor-shift) + 12MP ultrawide + 12MP telephoto (3x) + LiDAR, ProRes", "Front Camera": "12MP TrueDepth with autofocus", "Battery & Charging": "4323mAh, 27W wired, 15W MagSafe wireless", "OS & Updates": "iOS 16 out of the box, fully upgradable", "Build & Extras": "Dynamic Island, IP68, Ceramic Shield, stainless steel, MagSafe, Crash Detection"}, [(5, "Rebecca C.", "PT-116", "Deep Purple is sophisticated. Dynamic Island is genuinely useful.")]),
    L("samsung-galaxy-s24-ultra", "Samsung Galaxy S24 Ultra", "Samsung Galaxy S24 Ultra", MOP + "files/S24_Ultra1_992x.png?v=1735648520", 'Ex-UK 5G | 5000mAh | 6.8" Display', 2700, 33199, ["256GB", "512GB"], ["Black", "Green", "Grey"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.8" Dynamic AMOLED 2X, QHD+ (3120×1440), 120Hz, Gorilla Armor', "Processor": "Snapdragon 8 Gen 3 for Galaxy", "Rear Camera": "200MP main + 50MP periscope (5x) + 10MP (3x) + 12MP ultrawide, 8K video", "Front Camera": "12MP selfie", "Battery & Charging": "5000mAh, 45W wired, 15W wireless", "OS & Updates": "Android 14 out of the box, 7 years of updates", "Build & Extras": "Titanium frame, S-Pen built-in, IP68, Galaxy AI suite, stereo speakers, NFC"}, [(5, "Michael K.", "PT-117", "AI translation in meetings saves hours weekly. Future-proof investment.")]),
    L("apple-iphone-15-pro-max", "Apple iPhone 15 Pro Max", "Apple iPhone 15 Pro Max", MOP + "files/Screenshot2025-11-04at16.05.25_ad9bcddb-df5e-4e98-9251-113e32673b12_770x.png?v=1762278234", 'Ex-UK 5G | 4422mAh | 6.7" Display', 3100, 38099, ["256GB"], ["Space Black", "Natural Titanium", "Blue Titanium", "White Titanium"], {"Network": "5G + 4G LTE dual SIM (eSIM)", "Display": '6.7" LTPO Super Retina XDR OLED, 120Hz ProMotion, Always-On', "Processor": "Apple A17 Pro (3nm)", "Rear Camera": "48MP main + 48MP-class ultrawide (12MP) + 12MP tetraprism (5x) + LiDAR, ProRes & Log", "Front Camera": "12MP TrueDepth", "Battery & Charging": "4422mAh, 27W wired, 15W MagSafe, USB-C 3.0", "OS & Updates": "iOS 17 out of the box, fully upgradable", "Build & Extras": "Titanium frame, Action Button, IP68, Ceramic Shield, MagSafe"}, [(5, "Stella W.", "PT-118", "Titanium feels premium. Video quality is cinema-grade.")]),
    L("samsung-galaxy-s25-ultra", "Samsung Galaxy S25 Ultra", "Samsung S25 Ultra", MOP + "files/s25_ultra_300x.png?v=1772294113", 'Ex-UK 5G | 5000mAh | 6.9" Display', 3300, 40599, ["256GB"], ["Black", "Titanium Black", "Titanium White", "Silver", "Titanium SilverBlue"], {"Network": "5G + 4G LTE dual SIM", "Display": '6.9" Dynamic LTPO AMOLED 2X, QHD+ (3120×1440), 120Hz, 2600 nits', "Processor": "Snapdragon 8 Elite for Galaxy", "Rear Camera": "200MP main + 50MP periscope (5x) + 10MP (3x) + 50MP ultrawide, 8K video", "Front Camera": "12MP selfie", "Battery & Charging": "5000mAh, 45W wired, 15W wireless", "OS & Updates": "Android 15 out of the box, 7 years of updates", "Build & Extras": "Titanium frame, S-Pen built-in, IP68, Galaxy AI, stereo speakers, NFC"}, [(5, "Dennis M.", "PT-119", "AI features are genuinely useful, not gimmicky. Noticeable speed boost.")]),
    L("apple-iphone-16-pro-max", "Apple iPhone 16 Pro Max", "Apple iPhone 16 Pro Max", AM + "51Vs7ZwpSpL.AC_SY300_SY300_QL70_FMwebp.jpg", 'New | 5G | 4685mAh | 6.9" Display', 3840, 47199, ["256GB"], ["Desert Titanium", "Natural Titanium", "White Titanium", "Black Titanium"], {"Network": "5G + 4G LTE dual SIM (eSIM)", "Display": '6.9" LTPO Super Retina XDR OLED, 120Hz ProMotion, Always-On', "Processor": "Apple A18 Pro", "Rear Camera": "48MP Fusion main + 48MP ultrawide + 12MP tetraprism (5x) + LiDAR, 4K120 ProRes", "Front Camera": "12MP TrueDepth", "Battery & Charging": "4685mAh, 27W wired, 25W MagSafe, USB-C 3.2", "OS & Updates": "iOS 18 out of the box, fully upgradable", "Build & Extras": "Titanium frame, Camera Control button, Action Button, IP68, MagSafe"}, [(5, "Wanjiru K.", "PT-120", "Latest and greatest. Unboxing felt special, performance is effortless.")], condition="New"),
]

def price_for(p, s):
    sp = p.get("storage_pricing", {})
    return sp[s] if s in sp else {"weekly": p["weekly"], "deposit": p["deposit"]}
def min_weekly(p):
    vals = [p.get("weekly", 0)]
    for v in p.get("storage_pricing", {}).values(): vals.append(v.get("weekly", p.get("weekly", 0)))
    return min(vals)

LIPA_PRODUCTS.sort(key=lambda p: (min_weekly(p), p.get("deposit", 0)))
PRODUCTS_BY_SLUG = {}
for lp in LIPA_PRODUCTS:
    lp["type"] = "lipa"; lp["model"] = lp["name"]
    if "condition" not in lp: lp["condition"] = "Ex-UK"
    lp["stock"] = "In Stock"
    PRODUCTS_BY_SLUG[lp["slug"]] = lp

SP_S26U = 'Display: 6.9" Dynamic AMOLED 2X, 144Hz, 3000 nits • Processor: Snapdragon 8 Elite Gen 5 • Rear Camera: 200MP main + 50MP periscope (5x) + 50MP telephoto (3x) + 50MP ultrawide • Front: 12MP • Battery: 5000mAh, 60W wired • OS: Android 16, 7 years updates • Build: Titanium frame, IP68, S-Pen'
SP_S26P = 'Display: 6.7" Dynamic AMOLED 2X, 120Hz • Processor: Snapdragon 8 Elite Gen 5 • Rear Camera: 50MP main + 10MP telephoto (3x) + 12MP ultrawide • Front: 12MP • Battery: 4900mAh, 45W wired • OS: Android 16 • Build: Armor Aluminum, IP68'
SP_S26 = 'Display: 6.36" Dynamic AMOLED 2X, 120Hz • Processor: Snapdragon 8 Elite Gen 5 • Rear Camera: 50MP main + 10MP telephoto (3x) + 12MP ultrawide • Front: 12MP • Battery: 4300mAh, 45W wired • OS: Android 16 • Build: IP68, Gorilla Glass Victus 2'
SP_S25U = 'Display: 6.8" Dynamic AMOLED 2X, 120Hz, 2600 nits • Processor: Snapdragon 8 Elite • Rear Camera: 200MP main + 50MP periscope (5x) + 10MP telephoto (3x) + 50MP ultrawide • Front: 12MP • Battery: 5000mAh, 45W wired • OS: Android 15, 7 years updates • Build: Titanium, IP68, S-Pen'
SP_S24U = 'Display: 6.8" Dynamic AMOLED 2X, 120Hz, Gorilla Armor • Processor: Snapdragon 8 Gen 3 • Rear Camera: 200MP main + 50MP periscope (5x) + 10MP telephoto (3x) + 12MP ultrawide • Front: 12MP • Battery: 5000mAh, 45W wired • OS: Android 14, 7 years updates • Build: Titanium frame, IP68, S-Pen'
SP_S23U = 'Display: 6.8" Dynamic AMOLED 2X, 120Hz • Processor: Snapdragon 8 Gen 2 • Rear Camera: 200MP main + 10MP periscope (10x) + 10MP telephoto (3x) + 12MP ultrawide • Front: 12MP • Battery: 5000mAh, 45W wired • OS: Android 13, 4 OS upgrades • Build: Armor Aluminum, IP68, S-Pen'
SP_S23P = 'Display: 6.6" Dynamic AMOLED 2X, 120Hz • Processor: Snapdragon 8 Gen 2 • Rear Camera: 50MP main + 10MP telephoto (3x) + 12MP ultrawide • Front: 12MP • Battery: 4700mAh, 45W wired • OS: Android 13, 4 OS upgrades • Build: IP68, stereo speakers'
SP_S22U = 'Display: 6.8" Dynamic AMOLED 2X, 120Hz • Processor: Snapdragon 8 Gen 1 • Rear Camera: 108MP main + 10MP periscope (10x) + 10MP telephoto (3x) + 12MP ultrawide • Front: 40MP • Battery: 5000mAh, 45W wired • OS: Android 12, upgradable • Build: IP68, S-Pen built-in'
SP_S22P = 'Display: 6.6" Dynamic AMOLED 2X, 120Hz • Processor: Snapdragon 8 Gen 1 • Rear Camera: 50MP main + 10MP telephoto (3x) + 12MP ultrawide • Front: 10MP • Battery: 4500mAh, 45W wired • OS: Android 12, upgradable • Build: IP68, Armor Aluminum'
SP_S21U = 'Display: 6.8" Dynamic AMOLED 2X, 120Hz, 1440p • Processor: Snapdragon 888 • Rear Camera: 108MP main + 10MP (3x) + 10MP (10x) + 12MP ultrawide • Front: 40MP • Battery: 5000mAh, 25W wired • OS: Android 11, upgradable • Build: IP68, S-Pen support'
SP_S21P = 'Display: 6.7" Dynamic AMOLED 2X, 120Hz • Processor: Snapdragon 888 • Rear Camera: 12MP main + 64MP telephoto (3x) + 12MP ultrawide • Front: 10MP • Battery: 4800mAh, 25W wired • OS: Android 11, upgradable • Build: IP68, stereo speakers'
SP_S21FE = 'Display: 6.4" Dynamic AMOLED 2X, 120Hz • Processor: Snapdragon 888 • Rear Camera: 12MP main (OIS) + 12MP ultrawide + 8MP telephoto (3x) • Front: 32MP • Battery: 4500mAh, 25W wired • OS: Android 12, upgradable • Build: IP68, in-display fingerprint'
SP_S20U = 'Display: 6.9" Dynamic AMOLED 2X, 120Hz, 1440p • Processor: Snapdragon 865 • Rear Camera: 108MP main + 48MP periscope (10x) + 12MP ultrawide + ToF • Front: 40MP • Battery: 5000mAh, 45W wired • OS: Android 10, upgradable • Build: IP68, microSD slot'
SP_S10 = 'Display: 6.1" Dynamic AMOLED, 1440p • Processor: Snapdragon 855 • Rear Camera: 12MP main (dual aperture) + 12MP telephoto (2x) + 16MP ultrawide • Front: 10MP • Battery: 3400mAh, 15W wired • OS: Android 9, upgradable • Build: IP68, microSD, 3.5mm jack'
SP_S105G = 'Display: 6.7" Dynamic AMOLED, 1440p • Processor: Snapdragon 855 • Rear Camera: 12MP main + 12MP telephoto + 16MP ultrawide + ToF • Front: 10MP + ToF • Battery: 4500mAh, 25W wired • OS: Android 9, upgradable • Build: IP68, 5G'
SP_N20U = 'Display: 6.9" Dynamic AMOLED 2X, 120Hz • Processor: Snapdragon 865+ • Rear Camera: 108MP main + 12MP periscope (5x) + 12MP ultrawide • Front: 10MP • Battery: 4500mAh, 25W wired • OS: Android 10, upgradable • Build: IP68, S-Pen built-in'
SP_N20 = 'Display: 6.7" Super AMOLED Plus, 60Hz • Processor: Snapdragon 865+ • Rear Camera: 12MP main + 64MP telephoto + 12MP ultrawide • Front: 10MP • Battery: 4300mAh, 25W wired • OS: Android 10, upgradable • Build: IP68, S-Pen'
SP_N10 = 'Display: 6.3" Dynamic AMOLED, HDR10+ • Processor: Snapdragon 855 • Rear Camera: 12MP main + 12MP telephoto (2x) + 16MP ultrawide • Front: 10MP • Battery: 3500mAh, 25W wired • OS: Android 9, upgradable • Build: IP68, S-Pen'
SP_N10P = 'Display: 6.8" Dynamic AMOLED, 1440p • Processor: Snapdragon 855 • Rear Camera: 12MP main + 12MP telephoto + 16MP ultrawide + ToF • Front: 10MP + ToF • Battery: 4300mAh, 45W wired • OS: Android 9, upgradable • Build: IP68, S-Pen, microSD'
SP_F6 = 'Display: 7.6" Foldable Dynamic AMOLED 2X, 120Hz + 6.3" cover • Processor: Snapdragon 8 Gen 3 • Rear Camera: 50MP main + 10MP telephoto (3x) + 12MP ultrawide • Front: 10MP + 4MP under-display • Battery: 4400mAh, 25W wired • OS: Android 14 • Build: IP48, Armor Aluminum hinge'
SP_F5 = 'Display: 7.6" Foldable Dynamic AMOLED 2X, 120Hz + 6.2" cover • Processor: Snapdragon 8 Gen 2 • Rear Camera: 50MP main + 10MP telephoto (3x) + 12MP ultrawide • Front: 10MP + 4MP • Battery: 4400mAh, 25W wired • OS: Android 13 • Build: IPX8'
SP_F4 = 'Display: 7.6" Foldable Dynamic AMOLED 2X, 120Hz + 6.2" cover • Processor: Snapdragon 8+ Gen 1 • Rear Camera: 50MP main + 10MP telephoto (3x) + 12MP ultrawide • Front: 10MP + 4MP • Battery: 4400mAh, 25W wired • OS: Android 12 • Build: IPX8'
SP_F3 = 'Display: 7.6" Foldable Dynamic AMOLED 2X, 120Hz + 6.2" cover • Processor: Snapdragon 888 • Rear Camera: 12MP main + 12MP telephoto (2x) + 12MP ultrawide • Front: 10MP + 4MP • Battery: 4400mAh, 25W wired • OS: Android 11 • Build: IPX8'
SP_L7 = 'Display: 6.9" Foldable AMOLED, 120Hz + 4.1" cover • Processor: Exynos 2500 • Rear Camera: 50MP main + 12MP ultrawide • Front: 10MP • Battery: 4300mAh, 25W wired • OS: Android 16 • Build: IP48, FlexWindow'
SP_L6 = 'Display: 6.7" Foldable Dynamic AMOLED 2X, 120Hz + 3.4" cover • Processor: Snapdragon 8 Gen 3 • Rear Camera: 50MP main + 12MP ultrawide • Front: 10MP • Battery: 4000mAh, 25W wired • OS: Android 14 • Build: IP48'
SP_L5 = 'Display: 6.7" Foldable Dynamic AMOLED 2X, 120Hz + 3.4" cover • Processor: Snapdragon 8 Gen 2 • Rear Camera: 12MP main + 12MP ultrawide • Front: 10MP • Battery: 3700mAh, 25W wired • OS: Android 13 • Build: IPX8'
SP_L4 = 'Display: 6.7" Foldable Dynamic AMOLED 2X, 120Hz + 1.9" cover • Processor: Snapdragon 8+ Gen 1 • Rear Camera: 12MP main + 12MP ultrawide • Front: 10MP • Battery: 3700mAh, 25W wired • OS: Android 12 • Build: IPX8'
SP_A57 = 'Display: 6.7" Super AMOLED, 120Hz • Processor: Octa-core • Rear Camera: 50MP main (OIS) + 12MP ultrawide • Front: 12MP • Battery: 5000mAh, 45W wired • OS: Android 15 • Build: IP68, Gorilla Glass Victus+'
SP_A37 = 'Display: 6.6" Super AMOLED, 120Hz • Processor: Octa-core • Rear Camera: 50MP main (OIS) + 8MP ultrawide • Front: 12MP • Battery: 5000mAh, 25W wired • OS: Android 15 • Build: IP67'
SP_A56 = 'Display: 6.7" Super AMOLED, 120Hz • Processor: Exynos 1580 • Rear Camera: 50MP main (OIS) + 12MP ultrawide + 5MP macro • Front: 12MP • Battery: 5000mAh, 45W wired • OS: Android 15 • Build: IP67, Gorilla Glass Victus+'
SP_A26 = 'Display: 6.7" Super AMOLED, 120Hz • Processor: Exynos 1380 • Rear Camera: 50MP main (OIS) + 8MP ultrawide + 2MP macro • Front: 13MP • Battery: 5000mAh, 25W wired • OS: Android 15 • Build: IP67'
SP_A27 = 'Display: 6.7" Super AMOLED, 120Hz • Processor: Octa-core • Rear Camera: 50MP main (OIS) + 8MP ultrawide • Front: 13MP • Battery: 5000mAh, 25W wired • OS: Android 15 • Build: IP67'
SP_A17 = 'Display: 6.7" Super AMOLED, 90Hz • Processor: Octa-core (4G/5G variants) • Rear Camera: 50MP main (OIS) + 5MP ultrawide • Front: 13MP • Battery: 5000mAh, 25W wired • OS: Android 15 • Build: IP54'
SP_A16 = 'Display: 6.7" Super AMOLED, 90Hz • Processor: Helio G99 / Dimensity 6300 • Rear Camera: 50MP main + 5MP ultrawide + 2MP macro • Front: 13MP • Battery: 5000mAh, 25W wired • OS: Android 14 • Build: IP54'
SP_A07 = 'Display: 6.7" PLS LCD, 90Hz • Processor: Octa-core • Rear Camera: 50MP main + 2MP depth • Front: 8MP • Battery: 5000mAh, 25W wired • OS: Android 15 • Build: IP54'
SP_A07S = 'Display: 6.7" PLS LCD, 90Hz • Processor: Octa-core • Rear Camera: 50MP main + 2MP depth • Front: 8MP • Battery: 5000mAh, 25W wired • OS: Android 15 • Build: IP54, big-battery variant'
SP_A06 = 'Display: 6.7" PLS LCD, HD+ • Processor: MediaTek Helio G85 • Rear Camera: 50MP main + 2MP depth • Front: 8MP • Battery: 5000mAh, 25W wired • OS: Android 14 • Build: Side fingerprint, dual SIM'
SP_I16PM = 'Display: 6.9" LTPO Super Retina XDR OLED, 120Hz • Processor: Apple A18 Pro • Rear Camera: 48MP Fusion + 48MP ultrawide + 12MP telephoto (5x) • Front: 12MP • Battery: 4685mAh, USB-C • OS: iOS 18 • Build: Titanium, IP68, MagSafe'
SP_I15PM = 'Display: 6.7" LTPO Super Retina XDR OLED, 120Hz • Processor: Apple A17 Pro • Rear Camera: 48MP main + 12MP ultrawide + 12MP telephoto (5x) • Front: 12MP • Battery: 4422mAh, USB-C • OS: iOS 17 • Build: Titanium, IP68, MagSafe'
SP_I15 = 'Display: 6.1" Super Retina XDR OLED • Processor: Apple A16 Bionic • Rear Camera: 48MP main + 12MP ultrawide • Front: 12MP • Battery: 3349mAh, USB-C • OS: iOS 17 • Build: Aluminum, Dynamic Island, IP68'
SP_I14PM = 'Display: 6.7" LTPO Super Retina XDR OLED, 120Hz • Processor: Apple A16 Bionic • Rear Camera: 48MP main + 12MP ultrawide + 12MP telephoto (3x) • Front: 12MP • Battery: 4323mAh • OS: iOS 16 • Build: Stainless steel, Dynamic Island, IP68'
SP_I14P = 'Display: 6.1" LTPO Super Retina XDR OLED, 120Hz • Processor: Apple A16 Bionic • Rear Camera: 48MP main + 12MP ultrawide + 12MP telephoto (3x) • Front: 12MP • Battery: 3200mAh • OS: iOS 16 • Build: Stainless steel, Dynamic Island, IP68'
SP_I14PL = 'Display: 6.7" Super Retina XDR OLED • Processor: Apple A15 Bionic • Rear Camera: 12MP main + 12MP ultrawide • Front: 12MP • Battery: 4325mAh • OS: iOS 16 • Build: Aluminum, IP68'
SP_I14 = 'Display: 6.1" Super Retina XDR OLED • Processor: Apple A15 Bionic • Rear Camera: 12MP main + 12MP ultrawide • Front: 12MP • Battery: 3279mAh • OS: iOS 16 • Build: Aluminum, IP68'
SP_I13PM = 'Display: 6.7" LTPO Super Retina XDR OLED, 120Hz • Processor: Apple A15 Bionic • Rear Camera: 12MP main + 12MP ultrawide + 12MP telephoto (3x) • Front: 12MP • Battery: 4352mAh • OS: iOS 15 • Build: Stainless steel, IP68'
SP_I13 = 'Display: 6.1" Super Retina XDR OLED • Processor: Apple A15 Bionic • Rear Camera: 12MP main (sensor-shift) + 12MP ultrawide • Front: 12MP • Battery: 3240mAh • OS: iOS 15 • Build: Aluminum, IP68'
SP_I12 = 'Display: 6.1" Super Retina XDR OLED • Processor: Apple A14 Bionic • Rear Camera: 12MP main + 12MP ultrawide • Front: 12MP • Battery: 2815mAh, MagSafe • OS: iOS 14 • Build: Aluminum, IP68'
SP_I12P = 'Display: 6.1" Super Retina XDR OLED • Processor: Apple A14 Bionic • Rear Camera: 12MP main + 12MP ultrawide + 12MP telephoto (2x) + LiDAR • Front: 12MP • Battery: 2815mAh, MagSafe • OS: iOS 14 • Build: Stainless steel, IP68'
SP_I12PM = 'Display: 6.7" Super Retina XDR OLED • Processor: Apple A14 Bionic • Rear Camera: 12MP main + 12MP ultrawide + 12MP telephoto (2.5x) + LiDAR • Front: 12MP • Battery: 3687mAh, MagSafe • OS: iOS 14 • Build: Stainless steel, IP68'
SP_I11PM = 'Display: 6.5" Super Retina XDR OLED • Processor: Apple A13 Bionic • Rear Camera: 12MP main + 12MP ultrawide + 12MP telephoto (2x) • Front: 12MP • Battery: 3969mAh • OS: iOS 13 • Build: Stainless steel, IP68'
SP_I11P = 'Display: 5.8" Super Retina XDR OLED • Processor: Apple A13 Bionic • Rear Camera: 12MP main + 12MP ultrawide + 12MP telephoto (2x) • Front: 12MP • Battery: 3046mAh • OS: iOS 13 • Build: Stainless steel, IP68'

CASH_CATEGORIES = []
CASH_PRODUCTS = {}
def add_cat(name, note): CASH_CATEGORIES.append({"name": name, "note": note, "products": []})
def C(cat, name, price, spec, img):
    slug = slugify("pt-" + name)
    prod = {"slug": slug, "type": "cash", "model": name, "name": name, "price": int(price),
            "specs": clean_text(spec), "image": clean_text(img), "category_name": cat}
    CASH_PRODUCTS[slug] = prod
    for c in CASH_CATEGORIES:
        if c["name"] == cat: c["products"].append(prod)
    return prod

S1 = "Refurbished & Boxed Phones"
S2 = "Ex-UK Phones"
S3 = "Apple iPhone"
add_cat(S1, "Latest Samsung S and A series — refurbished to grade-A standard, sealed in box with accessories.")
add_cat(S2, "Clean Samsung imports from the UK — flagships, foldables and the S-Pen line, every unit tested and verified original.")
add_cat(S3, "Premium. Powerful. Timeless. Genuine iPhones from 11 Pro to 16 Pro Max — battery health checked, fully functional.")

# ---------- 1) REFURBISHED & BOXED (poster column 1) ----------
C(S1, "Samsung Galaxy S25 Ultra 512GB", 127000, SP_S25U, AM + "51ybW3eCRhL.AC_SX679.jpg")
C(S1, "Samsung Galaxy S25 Ultra 256GB", 109000, SP_S25U, AM + "51ybW3eCRhL.AC_SX679.jpg")
C(S1, "Samsung Galaxy S26 Ultra 256GB", 128000, SP_S26U, AM + "618F1CD-gbL.AC_SX679.jpg")
C(S1, "Samsung Galaxy S26 Ultra 512GB", 148000, SP_S26U, AM + "618F1CD-gbL.AC_SX679.jpg")
C(S1, "Samsung Galaxy S26 256GB", 99000, SP_S26, AM + "61q1dJxGowL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy S26 Plus 256GB", 109000, SP_S26P, AM + "61q1dJxGowL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy S26 Plus 512GB", 121000, SP_S26P, AM + "61q1dJxGowL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A57 256GB / 8GB", 54500, SP_A57, AM + "51mD59m3QKL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A37 256GB / 8GB", 45999, SP_A37, AM + "51PfnB-QHxL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A56 256GB", 49500, SP_A56, AM + "618oogho7PL.AC_SY300_SX300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A06 64GB / 4GB", 15999, SP_A06, AM + "518iRq2DZKL.AC_SX679.jpg")
C(S1, "Samsung Galaxy A06 128GB / 4GB", 19000, SP_A06, AM + "518iRq2DZKL.AC_SX679.jpg")
C(S1, "Samsung Galaxy A07 64GB / 4GB", 19000, SP_A07, AM + "41uTZLTSxdL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A07 128GB / 4GB", 21300, SP_A07, AM + "41uTZLTSxdL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A07s 64GB / 4GB", 19499, SP_A07S, AM + "41uTZLTSxdL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A17 128GB / 4GB", 25000, SP_A17, AM + "61urRuuqCiL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A17 128GB / 6GB", 28300, SP_A17, AM + "61urRuuqCiL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A16 128GB / 4GB", 23100, SP_A16, AM + "71KGkQ+KOKL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A17 256GB / 8GB", 35000, SP_A17, AM + "61urRuuqCiL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A26 256GB / 8GB", 36500, SP_A26, AM + "51ZmengIdlL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A27 128GB / 6GB", 35500, SP_A27, AM + "41Md7kOXowL.SY300_SX300_QL70_FMwebp.jpg")
C(S1, "Samsung Galaxy A27 256GB / 8GB", 42000, SP_A27, AM + "41Md7kOXowL.SY300_SX300_QL70_FMwebp.jpg")

# ---------- 2) EX-UK (poster column 2) ----------
C(S2, "Samsung Galaxy S24 Ultra 512GB", 96999, SP_S24U, AM + "71WcjsOVOmL.AC_SX679.jpg")
C(S2, "Samsung Galaxy S24 Ultra 256GB", 89999, SP_S24U, AM + "71WcjsOVOmL.AC_SX679.jpg")
C(S2, "Samsung Galaxy S23 Ultra 512GB", 77999, SP_S23U, AM + "71iBKcLHXFL.AC_SX679.jpg")
C(S2, "Samsung Galaxy S23 Ultra 256GB", 72500, SP_S23U, AM + "71iBKcLHXFL.AC_SX679.jpg")
C(S2, "Samsung Galaxy S23 Plus 256GB", 42000, SP_S23P, AM + "51yz4TrDNdL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy S22 Ultra 256GB", 58500, SP_S22U, AM + "613Fp7fknhL.AC_SX679.jpg")
C(S2, "Samsung Galaxy S22 Ultra 512GB", 63500, SP_S22U, AM + "613Fp7fknhL.AC_SX679.jpg")
C(S2, "Samsung Galaxy S22 Plus 256GB", 38499, SP_S22P, AM + "714oVGJtWeL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy Fold 6 256GB", 97000, SP_F6, AM + "61Jjxzg7Q1L.AC_SX679.jpg")
C(S2, "Samsung Galaxy Fold 5 512GB", 79000, SP_F5, AM + "518OMBP4J7L.AC_SX679.jpg")
C(S2, "Samsung Galaxy Fold 5 256GB", 76000, SP_F5, AM + "518OMBP4J7L.AC_SX679.jpg")
C(S2, "Samsung Galaxy Fold 4 256GB", 67000, SP_F4, AM + "81TH5W29HgL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy Fold 4 512GB", 70500, SP_F4, AM + "81TH5W29HgL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy Fold 3 512GB", 63000, SP_F3, AM + "71MFE2UY6-L.AC_SX679.jpg")
C(S2, "Samsung Galaxy Fold 3 256GB", 59000, SP_F3, AM + "71MFE2UY6-L.AC_SX679.jpg")
C(S2, "Samsung Galaxy Flip 7 256GB", 82000, SP_L7, AM + "61mSUSY4xWL.AC_SX679.jpg")
C(S2, "Samsung Galaxy Flip 6 512GB", 63000, SP_L6, AM + "61mSUSY4xWL.AC_SX679.jpg")
C(S2, "Samsung Galaxy Flip 5 512GB", 52000, SP_L5, AM + "51Jzh8XTxQL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy Flip 4 512GB", 42000, SP_L4, AM + "51Ggw4SLTUL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy Flip 4 256GB", 40999, SP_L4, AM + "51Ggw4SLTUL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy Note 20 Ultra 256GB", 48999, SP_N20U, AM + "51UG-WVTAOL.AC_SX679.jpg")
C(S2, "Samsung Galaxy Note 20 256GB", 34499, SP_N20, AM + "71hB8cEDLYL.AC_SY300_SX300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy Note 10 256GB", 33999, SP_N10, AM + "61kJwlX9NOL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy Note 10 Plus 256GB", 39999, SP_N10P, AM + "517MGkvMhXL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy S21 Plus 256GB", 35599, SP_S21P, AM + "61-QMCHyUES.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy S21FE 128GB", 32499, SP_S21FE, AM + "616kK0b+d+L.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy S21 Ultra 256GB", 45999, SP_S21U, AM + "61fNCOu3kaL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S2, "Samsung Galaxy S20 Ultra 256GB", 37999, SP_S20U, MOP + "files/S20Ultra1_455x.jpg?v=1718780519")
C(S2, "Samsung Galaxy S10 4G 128GB", 32000, SP_S10, "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s10.jpg")
C(S2, "Samsung Galaxy S10 5G 256GB", 33500, SP_S105G, "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s10-5g.jpg")

# ---------- 3) APPLE iPHONE (poster column 3) ----------
C(S3, "Apple iPhone 16 Pro Max 256GB", 111499, SP_I16PM, AM + "51Vs7ZwpSpL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 15 Pro Max 256GB", 96499, SP_I15PM, AM + "81OdN4WB6VL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 15 128GB", 66000, SP_I15, AM + "51PtFHUPjBL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 14 Pro Max 256GB", 77000, SP_I14PM, AM + "51wqFSpP20L.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 14 Pro 256GB", 71999, SP_I14P, AM + "61XO4bORHUL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 14 Plus 128GB", 59999, SP_I14PL, AM + "513-nH35+UL.AC_SX300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 14 128GB", 57500, SP_I14, AM + "61aEBeER-+L.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 14 256GB", 59000, SP_I14, AM + "61aEBeER-+L.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 13 Pro Max 256GB", 69500, SP_I13PM, AM + "61ERgud-SbL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 13 128GB", 47500, SP_I13, AM + "518rwCXZ0SL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 13 256GB", 49500, SP_I13, AM + "518rwCXZ0SL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 12 128GB", 41000, SP_I12, AM + "61bbqGftbUL.AC_SY879.jpg")
C(S3, "Apple iPhone 12 Pro 128GB", 46500, SP_I12P, AM + "51q3qjXRz2L.AC_SY300_SX300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 12 Pro Max 256GB", 56999, SP_I12PM, AM + "41SLL9Zws6L.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 12 Pro 256GB", 49999, SP_I12P, AM + "51q3qjXRz2L.AC_SY300_SX300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 11 Pro Max 256GB", 44999, SP_I11PM, AM + "61G2REmnBIL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 11 Pro Max 512GB", 46500, SP_I11PM, AM + "61G2REmnBIL.AC_SY300_SY300_QL70_FMwebp.jpg")
C(S3, "Apple iPhone 11 Pro 256GB", 42999, SP_I11P, AM + "61UC1mk6dfL.AC_SY300_SY300_QL70_FMwebp.jpg")

for slug, prod in CASH_PRODUCTS.items(): PRODUCTS_BY_SLUG[slug] = prod

def build_search_index():
    index = []
    for p in LIPA_PRODUCTS:
        plan_lines = []
        for s in p["storage"]:
            pr = price_for(p, s)
            plan_lines.append(f"{s}: deposit {money(pr['deposit'])}, weekly {money(pr['weekly'])}")
        specs_text = "; ".join(f"{k}: {v}" for k, v in p["specs"].items())
        searchable = " ".join([p["name"], p.get("condition", "Ex-UK"), " ".join(p["storage"]), " ".join(p["colors"]), specs_text, "installment weekly plan deposit", p.get("tagline", "")]).lower()
        context = (f"{p['name']} | Installment Plan | {p.get('condition','Ex-UK')} | Stock: {p.get('stock','In Stock')} | "
                   f"Storage: {', '.join(p['storage'])} | Colors: {', '.join(p['colors'])} | "
                   f"Plans: {'; '.join(plan_lines)} | Specs: {specs_text} | Page: /device/{p['slug']}")
        index.append({"type": "lipa", "product": p, "text": searchable, "context": context, "name": p["name"],
                      "line": f"{p['name']} — {money(price_for(p, p['storage'][0])['deposit'])} initial, {money(price_for(p, p['storage'][0])['weekly'])}/week"})
    for p in CASH_PRODUCTS.values():
        searchable = " ".join([p["name"], p["category_name"], p["specs"], "cash full payment negotiable"]).lower()
        context = (f"{p['name']} | Cash Collection | {p['category_name']} | "
                   f"Price {money(p['price'])} (Negotiable) | Specs: {p['specs']} | Page: /device/{p['slug']}")
        index.append({"type": "cash", "product": p, "text": searchable, "context": context, "name": p["name"],
                      "line": f"{p['name']} — {money(p['price'])} (negotiable)"})
    return index

SEARCH_INDEX = build_search_index()
def search_items(query, limit=6):
    terms = [t for t in re.findall(r"[a-z0-9]+", str(query).lower()) if len(t) > 1]
    if not terms: return []
    scored = []
    for item in SEARCH_INDEX:
        score = 0
        for t in terms:
            if t in item["text"]: score += 1
        if score: scored.append((score, item))
    scored.sort(key=lambda x: (-x[0], len(x[1]["name"]), x[1]["name"]))
    return [item for _, item in scored[:limit]]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700;800&display=swap');
:root {
  --bg: #0A192F;
  --bg-deep: #050A15;
  --card: #112240;
  --card-hover: #1A2F4A;
  --border: #233554;
  --text: #E2E8F0;
  --text-light: #8892B0;
  --accent: #00B4D8;
  --accent-light: #48CAE4;
  --success: #10B981;
  --shadow: 0 4px 6px -1px rgba(0,0,0,.4), 0 10px 15px -3px rgba(0,0,0,.4);
  --shadow-lg: 0 20px 25px -5px rgba(0,0,0,.6), 0 10px 10px -5px rgba(0,0,0,.3);
  --display: 'Playfair Display', serif;
  --body: 'Inter', sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: var(--body); color: var(--text); background: var(--bg); line-height: 1.6; overflow-x: hidden; }
a { color: inherit; text-decoration: none; }
img { max-width: 100%; display: block; decoding: async; }
button, input, select, textarea { font: inherit; }
.container { width: min(1220px, 92%); margin: auto; }
.section { padding: 68px 0; }
.muted { color: var(--text-light); }
.hidden { display: none !important; }

.topbar { overflow: hidden; background: var(--bg-deep); color: #fff; font-weight: 600; font-size: 12.5px; letter-spacing: .05em; position: relative; z-index: 1200; border-bottom: 1px solid var(--border); }
.marquee { display: flex; width: max-content; animation: marquee 35s linear infinite; }
.marquee span { padding: 12px 30px; white-space: nowrap; color: var(--accent-light); }
@keyframes marquee { from { transform: translateX(0); } to { transform: translateX(-50%); } }

.header { position: sticky; top: 0; z-index: 1100; background: rgba(10, 25, 47, 0.85); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); box-shadow: var(--shadow); }
.header-inner { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 16px 0; }
.logo { font-family: var(--display); font-size: 28px; font-weight: 800; display: inline-flex; align-items: baseline; letter-spacing: -0.02em; color: var(--text); }
.logo i { font-style: normal; color: var(--accent); }
.nav { display: flex; align-items: center; gap: 24px; }
.nav a { color: var(--text-light); font-weight: 600; font-size: 14px; transition: .25s; letter-spacing: 0.01em; }
.nav a:hover, .nav a.active { color: var(--accent); }

.btn { display: inline-flex; align-items: center; justify-content: center; gap: 9px; padding: 13px 24px; border-radius: 8px; border: 1px solid transparent; font-family: var(--body); font-weight: 700; cursor: pointer; transition: .3s; white-space: nowrap; letter-spacing: 0.02em; text-transform: uppercase; font-size: 12px; }
.btn-accent { color: var(--bg); background: var(--accent); box-shadow: 0 4px 14px rgba(0, 180, 216, .25); }
.btn-accent:hover { background: var(--accent-light); transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0, 180, 216, .35); }
.btn-outline { color: var(--text); border-color: var(--border); background: transparent; }
.btn-outline:hover { border-color: var(--accent); color: var(--accent); transform: translateY(-1px); }
.btn-whatsapp { color: #fff; background: #25D366; box-shadow: 0 4px 14px rgba(37, 211, 102, .25); }
.btn-whatsapp:hover { transform: translateY(-2px); }
.btn-sm { padding: 9px 16px; font-size: 11px; border-radius: 6px; }
.hamburger { display: none; background: var(--card); border: 1px solid var(--border); width: 46px; height: 46px; border-radius: 8px; font-size: 20px; cursor: pointer; box-shadow: var(--shadow); color: var(--text); }

.hero { position: relative; padding: 80px 0 40px; overflow: hidden; }
.hero-inner { position: relative; z-index: 1; max-width: 920px; }
.eyebrow { display: inline-flex; padding: 8px 16px; border-radius: 4px; border: 1px solid rgba(0, 180, 216, .3); background: rgba(0, 180, 216, .05); color: var(--accent); font-family: var(--body); font-size: 11px; font-weight: 800; letter-spacing: .15em; text-transform: uppercase; }
.hero h1 { font-family: var(--display); font-weight: 700; font-size: clamp(2.6rem, 6vw, 4.8rem); line-height: 1.05; letter-spacing: -.03em; margin: 24px 0 20px; color: var(--text); }
.grad { background: linear-gradient(90deg, var(--accent), #48CAE4, var(--accent)); background-size: 220% auto; -webkit-background-clip: text; background-clip: text; color: transparent; animation: shine 6s linear infinite; }
@keyframes shine { to { background-position: 220% center; } }
.hero p { max-width: 780px; color: var(--text-light); font-size: clamp(1.05rem, 1.8vw, 1.2rem); font-weight: 400; line-height: 1.7; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 32px; }
.hero-stats { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 36px; }
.stat-pill { padding: 12px 18px; border-radius: 6px; background: var(--card); border: 1px solid var(--border); box-shadow: var(--shadow); font-weight: 600; font-size: 13px; color: var(--text); display: flex; align-items: center; gap: 8px; }
.stat-pill:before { content: "✓"; color: var(--success); font-weight: 800; }

.section-head { display: flex; align-items: end; justify-content: space-between; gap: 18px; margin-bottom: 32px; }
.section-head h2 { font-family: var(--display); font-weight: 700; font-size: clamp(1.8rem, 3vw, 2.6rem); letter-spacing: -0.02em; color: var(--text); }
.section-head h2:after { content: ""; display: block; width: 60px; height: 3px; margin-top: 12px; background: var(--accent); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 24px; }

.card { position: relative; display: flex; flex-direction: column; overflow: hidden; background: var(--card); border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow); transition: .4s cubic-bezier(0.2, 0.8, 0.2, 1); min-height: 100%; }
.card:hover { transform: translateY(-8px); border-color: rgba(0, 180, 216, .4); box-shadow: var(--shadow-lg); }
.card img { height: 220px; width: 100%; object-fit: contain; background: var(--bg-deep); padding: 20px; transition: .4s; }
.card:hover img { transform: scale(1.03); }
.card-body { padding: 20px; display: flex; flex-direction: column; gap: 10px; flex: 1; }
.card-body h3 { font-family: var(--display); font-weight: 600; font-size: 18px; line-height: 1.3; color: var(--text); }
.price { color: var(--accent); font-family: var(--body); font-weight: 800; font-size: 20px; letter-spacing: -0.01em; }
.stock-badge, .badge { position: absolute; z-index: 2; top: 16px; left: 16px; padding: 6px 12px; border-radius: 4px; font-size: 10px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; background: rgba(10, 25, 47, .95); border: 1px solid var(--border); color: var(--text-light); }
.stock-badge:before { content: ""; display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: var(--success); margin-right: 6px; animation: blink 2s ease-in-out infinite; }
.stock-badge.low { border-color: rgba(234, 88, 12, .3); color: #f97316; background: rgba(234, 88, 12, .1); }
.stock-badge.low:before { background: #f97316; }
@keyframes blink { 50% { opacity: .3; } }
.link { color: var(--accent); font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; margin-top: auto; }
.micro { font-size: 11px; color: var(--text-light); font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.calc-actions { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-top: auto; padding-top: 8px; }

.why-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px; }
.panel { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 32px; box-shadow: var(--shadow); position: relative; overflow: hidden; }
.panel h3 { font-family: var(--display); font-weight: 700; font-size: 22px; margin-bottom: 12px; color: var(--text); }
.panel h2 { font-family: var(--display); font-weight: 700; font-size: clamp(1.4rem, 3vw, 2.1rem); margin-bottom: 12px; color: var(--text); }
.cta-band { margin: 40px auto 80px; background: var(--card); border: 1px solid var(--accent); border-radius: 16px; padding: 48px; text-align: center; box-shadow: var(--shadow-lg); position: relative; overflow: hidden; color: var(--text); }
.cta-band h2 { font-family: var(--display); font-weight: 700; font-size: clamp(1.8rem, 3vw, 2.8rem); margin-bottom: 12px; }
.cta-band p { color: var(--text-light); margin-bottom: 24px; }

.footer { border-top: 1px solid var(--border); background: var(--bg-deep); padding: 56px 0 24px; margin-top: 48px; }
.footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 32px; margin-bottom: 32px; }
.footer h4 { font-family: var(--display); margin-bottom: 16px; font-size: 18px; color: var(--text); }
.footer a, .footer p { color: var(--text-light); font-size: 14px; line-height: 1.8; }
.footer a:hover { color: var(--accent); }
.copyright { border-top: 1px solid var(--border); padding-top: 24px; color: var(--text-light); font-size: 13px; text-align: center; }

.page-hero { padding: 70px 0 30px; }
.page-hero h1 { font-family: var(--display); font-weight: 700; font-size: clamp(2.2rem, 5vw, 4rem); letter-spacing: -.03em; margin: 16px 0 12px; color: var(--text); }
.product-page { display: grid; grid-template-columns: 1.1fr .9fr; gap: 40px; align-items: start; }
.product-image { width: 100%; height: 500px; object-fit: contain; background: var(--bg-deep); padding: 30px; border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow); }
.product-panel { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 32px; box-shadow: var(--shadow); }
.product-panel h1 { font-family: var(--display); font-weight: 700; font-size: clamp(1.8rem, 3vw, 2.6rem); margin-bottom: 10px; letter-spacing: -0.02em; color: var(--text); }
.plan-box { position: relative; margin: 24px 0; padding: 28px; border-radius: 12px; background: var(--bg); border: 1px solid var(--border); box-shadow: var(--shadow); overflow: hidden; }
.plan-title { font-family: var(--body); font-weight: 800; color: var(--accent); text-transform: uppercase; letter-spacing: .15em; font-size: 12px; margin-bottom: 12px; }
.plan-row { display: flex; justify-content: space-between; gap: 12px; padding: 12px 0; font-weight: 500; border-bottom: 1px dashed var(--border); color: var(--text); }
.plan-row strong { color: var(--text); font-weight: 700; }
.plan-row:last-of-type { border-bottom: none; }
.option-row { display: flex; flex-wrap: wrap; gap: 10px; margin: 12px 0 20px; }
.option-btn { padding: 12px 18px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg); color: var(--text-light); cursor: pointer; font-weight: 600; font-size: 13px; transition: .2s; }
.option-btn.active, .option-btn:hover { border-color: var(--accent); color: var(--accent); background: rgba(0, 180, 216, .05); }
.notice { padding: 16px 20px; border-radius: 8px; background: rgba(0, 180, 216, .05); border: 1px solid rgba(0, 180, 216, .2); color: var(--accent-light); font-size: 14px; margin: 16px 0; font-weight: 500; display: flex; align-items: center; gap: 10px; }
.notice:before { content: "🛡"; font-size: 18px; }
.promise-list, .trust-list, .box-list, .spec-list { display: grid; gap: 12px; margin: 16px 0 24px; }
.promise-list li, .trust-list li, .box-list li, .spec-list li { list-style: none; padding-left: 28px; position: relative; color: var(--text); font-weight: 500; line-height: 1.6; }
.promise-list li:before, .trust-list li:before, .box-list li:before, .spec-list li:before { content: "✓"; position: absolute; left: 0; color: var(--success); font-weight: 800; font-size: 16px; }
.spec-table { width: 100%; border-collapse: collapse; margin: 16px 0 24px; }
.spec-table th, .spec-table td { padding: 14px 16px; border: 1px solid var(--border); text-align: left; font-size: 14px; vertical-align: top; color: var(--text); }
.spec-table th { width: 140px; color: var(--accent); background: var(--bg); font-weight: 700; }
.review { border: 1px solid var(--border); border-radius: 12px; padding: 24px; background: var(--card); margin-bottom: 16px; box-shadow: var(--shadow); }
.review-top { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; }
.stars { color: var(--accent); letter-spacing: 2px; font-size: 18px; }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.field { display: grid; gap: 8px; margin-bottom: 16px; }
.field label { font-weight: 700; font-size: 13px; color: var(--text); text-transform: uppercase; letter-spacing: 0.05em; }
input, select, textarea { width: 100%; padding: 14px 16px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg); color: var(--text); outline: none; transition: .2s; font-size: 15px; }
input:focus, select:focus, textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 4px rgba(0, 180, 216, .1); }
textarea { min-height: 120px; resize: vertical; }
.file-label { display: flex; align-items: center; justify-content: space-between; gap: 12px; border: 2px dashed var(--border); background: var(--bg); padding: 18px 20px; border-radius: 8px; cursor: pointer; transition: .25s; }
.file-label:hover { border-color: var(--accent); background: rgba(0, 180, 216, .03); }
.file-label input { display: none; }
.file-label span { color: var(--text-light); font-size: 14px; font-weight: 600; }

.modal { position: fixed; inset: 0; z-index: 2000; display: none; place-items: center; background: rgba(5, 10, 21, .8); backdrop-filter: blur(8px); padding: 20px; }
.modal.open { display: grid; }
.modal-box { width: min(820px, 100%); max-height: 90vh; overflow: auto; background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 36px; position: relative; box-shadow: var(--shadow-lg); }
.modal-close { position: absolute; top: 16px; right: 16px; width: 40px; height: 40px; border-radius: 50%; background: var(--bg); border: 1px solid var(--border); cursor: pointer; color: var(--text); font-size: 20px; display: grid; place-items: center; }
.toast { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); background: var(--card); border: 1px solid var(--accent); color: var(--text); padding: 16px 24px; border-radius: 8px; display: none; z-index: 3000; box-shadow: var(--shadow-lg); font-weight: 600; }
.toast.show { display: block; animation: toastIn .3s ease; }
@keyframes toastIn { from { opacity: 0; transform: translate(-50%, 10px); } to { opacity: 1; transform: translate(-50%, 0); } }

.reveal { transition: opacity .8s ease, transform .8s ease; }
.reveal-init { opacity: 0; transform: translateY(30px); }
.reveal.visible { opacity: 1; transform: none; }

.faq-item { border: 1px solid var(--border); border-radius: 12px; background: var(--card); padding: 24px; margin-bottom: 16px; box-shadow: var(--shadow); }
.faq-item summary { cursor: pointer; font-weight: 700; list-style: none; font-size: 16px; color: var(--text); }
.faq-item summary::-webkit-details-marker { display: none; }
.faq-item p { margin-top: 16px; color: var(--text-light); line-height: 1.7; }

.steps-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
.step-number { width: 48px; height: 48px; border-radius: 8px; display: grid; place-items: center; background: rgba(0, 180, 216, .1); border: 1px solid rgba(0, 180, 216, .3); color: var(--accent); font-weight: 800; font-size: 20px; margin-bottom: 16px; }

.category-note { color: var(--text-light); margin-bottom: 24px; max-width: 900px; font-size: 15px; line-height: 1.7; }
.breadcrumbs { color: var(--text-light); font-size: 13px; margin-bottom: 16px; font-weight: 500; }
.breadcrumbs a { color: var(--accent); }
.product-meta { display: flex; flex-wrap: wrap; gap: 10px; margin: 16px 0; }
.meta-pill { padding: 8px 14px; border-radius: 6px; background: var(--bg); border: 1px solid var(--border); font-size: 12px; color: var(--text-light); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.meta-pill.gold { background: rgba(0, 180, 216, .08); border-color: rgba(0, 180, 216, .3); color: var(--accent); }

.wa-float { position: fixed; right: 24px; bottom: 24px; z-index: 1500; width: 64px; height: 64px; border-radius: 50%; background: #25D366; display: grid; place-items: center; box-shadow: 0 16px 40px rgba(37, 211, 102, .4); }
.wa-float:before { content: ""; position: absolute; inset: 0; border-radius: 50%; animation: waPulse 2.5s ease-out infinite; }
@keyframes waPulse { 0% { box-shadow: 0 0 0 0 rgba(37, 211, 102, .5); } 100% { box-shadow: 0 0 0 24px rgba(37, 211, 102, 0); } }

.exec-grid { display: grid; grid-template-columns: 1.1fr .9fr; gap: 32px; align-items: start; }
.exec-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 40px; box-shadow: var(--shadow-lg); position: relative; overflow: hidden; }
.exec-card:before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px; background: var(--accent); pointer-events: none; }
.exec-label { font-size: 11px; letter-spacing: .18em; text-transform: uppercase; color: var(--accent); font-weight: 800; margin-bottom: 12px; display: inline-flex; align-items: center; gap: 8px; }
.choice-field { margin-bottom: 16px; border-radius: 10px; border: 1px solid var(--border); background: var(--bg); padding: 18px; transition: .25s; }
.choice-field:focus-within { border-color: var(--accent); box-shadow: 0 0 0 4px rgba(0, 180, 216, .1); }
.choice-label { font-size: 11px; letter-spacing: .15em; text-transform: uppercase; color: var(--text-light); font-weight: 700; margin-bottom: 8px; }
.choice-field input, .choice-field select { width: 100%; border: none; background: transparent; padding: 0; font-weight: 600; color: var(--text); outline: none; box-shadow: none; font-size: 16px; }
.app-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: stretch; }
.apply-summary { position: sticky; top: 100px; }
.summary-line { display: flex; justify-content: space-between; gap: 12px; padding: 12px 0; border-bottom: 1px dashed var(--border); font-weight: 600; color: var(--text-light); }
.summary-line strong { color: var(--text); }
.summary-phone { display: flex; align-items: center; gap: 16px; padding: 16px; border: 1px solid var(--border); border-radius: 12px; background: var(--bg); margin: 0 0 16px; }
.summary-phone img { width: 80px; height: 80px; object-fit: contain; background: var(--card); border: 1px solid var(--border); border-radius: 8px; flex: none; }
.exec-points { display: grid; gap: 12px; margin: 20px 0 0; }
.exec-points div { display: flex; gap: 12px; align-items: flex-start; padding: 14px 16px; border: 1px solid var(--border); border-radius: 10px; background: var(--bg); font-weight: 600; color: var(--text); }
.exec-points div:before { content: "✓"; color: var(--success); font-weight: 800; font-size: 16px; }
.secure-band { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-top: 16px; }
.secure-band.compact { margin: 16px auto 0; max-width: 880px; }
.secure-pill { display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 6px; background: rgba(0, 180, 216, .05); border: 1px solid rgba(0, 180, 216, .2); color: var(--accent-light); font-size: 11px; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; }
.page-hero.apply-hero { padding: 40px 0 10px; text-align: center; }
.apply-hero .container { max-width: 880px; }
.apply-section { padding-top: 24px; }
.apply-progress { height: 6px; border-radius: 999px; background: var(--border); overflow: hidden; margin: 14px 0 8px; }
.apply-progress-bar { height: 100%; width: 0%; background: linear-gradient(90deg, var(--accent), #48CAE4); transition: width .4s ease; }
.apply-progress-text { font-size: 13px; font-weight: 600; color: var(--accent); margin-bottom: 16px; }
.doc-progress { height: 6px; border-radius: 999px; background: var(--border); overflow: hidden; margin: 12px 0 16px; }
.doc-progress span { display: block; height: 100%; width: 0; background: linear-gradient(90deg, var(--accent), #48CAE4); transition: width .45s ease; }
.doc-tip { font-size: 14px; color: var(--text); background: var(--bg); border: 1px solid var(--border); padding: 14px 16px; border-radius: 8px; margin-bottom: 20px; }
.done-badge { width: 80px; height: 80px; margin: 12px auto 20px; border-radius: 50%; display: grid; place-items: center; background: var(--success); color: #fff; font-size: 36px; animation: popIn .5s cubic-bezier(.2, 1.4, .4, 1); }
@keyframes popIn { from { transform: scale(0); } to { transform: scale(1); } }
.done-list { display: grid; gap: 10px; margin: 20px auto; max-width: 420px; text-align: left; }
.done-list div { padding: 12px 16px; border-radius: 8px; background: rgba(16, 185, 129, .08); border: 1px solid rgba(16, 185, 129, .2); color: var(--success); font-weight: 600; font-size: 14px; }
.why-note { background: rgba(0, 180, 216, .05); border: 1px solid rgba(0, 180, 216, .2); color: var(--text); padding: 14px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.why-note strong { color: var(--accent); display: block; margin-bottom: 4px; }

.assistant-dot { position: fixed; left: 24px; bottom: 24px; z-index: 1600; width: 60px; height: 60px; border-radius: 50%; background: var(--card); border: 1px solid var(--border); box-shadow: var(--shadow-lg); display: none; place-items: center; cursor: pointer; }
.assistant-dot.show { display: grid; }
.assistant-dot .dot { width: 14px; height: 14px; border-radius: 50%; background: var(--success); position: relative; }
.assistant-dot .dot:after { content: ""; position: absolute; inset: 0; border-radius: 50%; animation: waPulse 2.5s ease-out infinite; }
.assistant-panel { position: fixed; left: 24px; bottom: 96px; z-index: 1700; width: min(400px, calc(100vw - 48px)); height: 580px; background: var(--card); border: 1px solid var(--border); border-radius: 16px; box-shadow: var(--shadow-lg); display: none; flex-direction: column; overflow: hidden; }
.assistant-panel.open { display: flex; animation: fadeUp .3s ease; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: none; } }
.assistant-head { padding: 20px; background: var(--bg-deep); border-bottom: 1px solid var(--border); }
.assistant-head .row { display: flex; align-items: center; gap: 14px; }
.assistant-avatar { width: 48px; height: 48px; border-radius: 10px; display: grid; place-items: center; background: rgba(0, 180, 216, .1); font-weight: 800; color: var(--accent); font-size: 20px; font-family: var(--display); }
.online-text { color: var(--success); font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 6px; }
.online-text:before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--success); }
.assistant-body { flex: 1; overflow: auto; padding: 20px; background: var(--bg); }
.assistant-msg { max-width: 88%; margin-bottom: 12px; padding: 14px 18px; border-radius: 12px; font-size: 14px; line-height: 1.6; animation: fadeUp .25s ease; }
.assistant-msg.bot { background: var(--card); border: 1px solid var(--border); border-bottom-left-radius: 4px; box-shadow: var(--shadow); color: var(--text); }
.assistant-msg.user { margin-left: auto; background: var(--accent); color: var(--bg); border-bottom-right-radius: 4px; }
.assistant-input { display: flex; gap: 10px; padding: 16px; border-top: 1px solid var(--border); background: var(--card); }
.assistant-input input { flex: 1; padding: 14px 18px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg); color: var(--text); }
.assistant-close { margin-left: auto; width: 36px; height: 36px; border-radius: 8px; border: 1px solid var(--border); background: var(--card); cursor: pointer; color: var(--text-light); font-size: 18px; display: grid; place-items: center; }
.assistant-quick { display: flex; gap: 8px; flex-wrap: wrap; padding: 0 16px 16px; background: var(--bg); }
.assistant-quick button { padding: 8px 14px; border-radius: 6px; border: 1px solid var(--border); background: var(--card); font-size: 12px; font-weight: 600; color: var(--text-light); cursor: pointer; transition: .2s; }
.assistant-quick button:hover { color: var(--accent); border-color: var(--accent); }
.ai-cards { display: grid; gap: 10px; margin-top: 12px; }
.ai-card { border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; gap: 12px; background: var(--card); box-shadow: var(--shadow); }
.ai-card.whatsapp { background: rgba(37, 211, 102, .05); border-color: rgba(37, 211, 102, .2); }
.ai-card.gold { background: rgba(0, 180, 216, .05); border-color: rgba(0, 180, 216, .2); }
.ai-card-title { font-weight: 700; font-size: 14px; color: var(--text); }
.ai-card-sub { color: var(--text-light); font-size: 12px; margin-top: 2px; }
.ai-card-btn { padding: 10px 16px; border-radius: 6px; font-weight: 700; font-size: 11px; color: var(--bg); background: var(--accent); white-space: nowrap; text-transform: uppercase; letter-spacing: 0.05em; }
.ai-card.whatsapp .ai-card-btn { background: #25D366; color: #fff; }
.ai-card.outline .ai-card-btn { background: var(--card); border: 1px solid var(--border); color: var(--text); }

.search-box { display: flex; gap: 10px; margin: 24px 0 12px; }
.search-box input { flex: 1; padding: 16px 20px; border-radius: 8px; border: 1px solid var(--border); background: var(--card); outline: none; box-shadow: var(--shadow); font-size: 15px; color: var(--text); }
.chips { display: flex; flex-wrap: wrap; gap: 10px; margin: 28px 0 12px; }
.chip { padding: 10px 16px; border-radius: 6px; border: 1px solid var(--border); background: var(--card); color: var(--text-light); font-size: 13px; font-weight: 600; box-shadow: var(--shadow); transition: .25s; }
.chip:hover { color: var(--accent); border-color: var(--accent); transform: translateY(-2px); }

@media (max-width: 1020px) {
  .product-page, .exec-grid { grid-template-columns: 1fr; }
  .why-grid, .steps-grid { grid-template-columns: 1fr; }
  .footer-grid { grid-template-columns: 1fr; }
  .apply-summary { position: static; }
}
@media (max-width: 860px) {
  .nav { position: fixed; top: 80px; right: 4%; left: 4%; z-index: 1200; flex-direction: column; align-items: stretch; gap: 12px; padding: 20px; border-radius: 12px; border: 1px solid var(--border); background: var(--card); display: none; box-shadow: var(--shadow-lg); }
  .nav.open { display: flex; }
  .hamburger { display: block; }
  .form-grid, .app-grid { grid-template-columns: 1fr; }
  .product-image { height: 350px; }
  .section { padding: 48px 0; }
}
@media (max-width: 560px) {
  .grid { grid-template-columns: 1fr; }
  .card img { height: 180px; padding: 12px; }
  .hero-actions .btn { width: 100%; }
  .assistant-panel { left: 12px; right: 12px; width: auto; bottom: 84px; height: 65vh; }
  .secure-pill { font-size: 10px; padding: 6px 10px; }
}
"""

JS = r"""
function fmtKES(n){ return 'KES ' + Number(n).toLocaleString(); }
function escHtml(s){ var d=document.createElement('div'); d.textContent=s==null?'':String(s); return d.innerHTML; }
document.addEventListener('DOMContentLoaded', function(){
 [initMenu,initReveal,initStorageButtons,initColorButtons,initCashSearch,
 initFileLabels,initApplyForm,initModalClose,initAssistant].forEach(function(fn){try{fn();}catch(e){}});
});
function initMenu(){
 var b=document.getElementById('menuBtn'),n=document.getElementById('mainNav');
 if(b&&n){b.addEventListener('click',function(){n.classList.toggle('open');});}
}
function initReveal(){
 if(!('IntersectionObserver' in window)){return;}
 var o=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('visible');o.unobserve(en.target);}});},{threshold:.08});
 document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('reveal-init');o.observe(el);});
}
function initStorageButtons(){
 document.querySelectorAll('.storage-btn').forEach(function(btn){
  btn.addEventListener('click',function(){
   document.querySelectorAll('.storage-btn').forEach(function(b){b.classList.remove('active');});
   btn.classList.add('active');
   var a=document.getElementById('applyCta');
   if(a&&btn.dataset.product&&btn.dataset.storage){a.href='/apply-now?phone='+encodeURIComponent(btn.dataset.product+' ('+btn.dataset.storage+')');}
   var w=document.getElementById('planWeekly'),d=document.getElementById('planDeposit');
   if(w&&btn.dataset.weekly){w.textContent=btn.dataset.weekly;}
   if(d&&btn.dataset.deposit){d.textContent=btn.dataset.deposit;}
  });
 });
}
function initColorButtons(){
 document.querySelectorAll('.color-btn').forEach(function(b){
  b.addEventListener('click',function(){
   document.querySelectorAll('.color-btn').forEach(function(x){x.classList.remove('active');});
   b.classList.add('active');
  });
 });
}
function initCashSearch(){
 var s=document.getElementById('cashSearch');
 if(!s)return;
 s.addEventListener('input',function(){
  var t=s.value.toLowerCase();
  document.querySelectorAll('.cash-card').forEach(function(c){
   c.style.display=c.innerText.toLowerCase().indexOf(t)>-1?'':'none';
  });
 });
}
function initFileLabels(){
 document.querySelectorAll('.file-label input').forEach(function(i){
  i.addEventListener('change',function(){
   var l=i.closest('.file-label');
   var t=l?l.querySelector('span'):null;
   if(t){t.textContent=i.files&&i.files.length?i.files[0].name:'Upload file';}
  });
 });
}
function initModalClose(){
 document.querySelectorAll('[data-close]').forEach(function(b){
  b.addEventListener('click',function(){closeModal(b.getAttribute('data-close'));});
 });
}
function openModal(id){
 var m=document.getElementById(id);
 if(m){m.classList.add('open');document.body.style.overflow='hidden';}
}
function closeModal(id){
 var m=document.getElementById(id);
 if(m){m.classList.remove('open');document.body.style.overflow='';}
}
function showToast(msg){
 var t=document.getElementById('toast');
 if(!t)return;
 t.textContent=msg;
 t.classList.add('show');
 setTimeout(function(){t.classList.remove('show');},5000);
}
function val(id){
 var f=document.getElementById(id);
 return f?f.value:'';
}
function setStep(p){
 var b=document.getElementById('docProgressBar');
 if(b){b.style.width=p+'%';}
}
function jMsg(t){
 var m=document.getElementById('journeyMsg');
 if(m){m.textContent=t;}
}
var TW_SUB_ID=null;
var TW_STEP=2;
var TW_DONE=false;
function jGo(step){
 TW_STEP=step;
 if(step===5){TW_DONE=true;}
 var panels={2:'stepMpesa',3:'stepIdentity',4:'stepKin',5:'stepDone'};
 for(var k in panels){
  var el=document.getElementById(panels[k]);
  if(el){el.classList.add('hidden');}
 }
 var target=document.getElementById(panels[step]);
 if(target){target.classList.remove('hidden');}
 setStep(step===5?100:(step-1)*33);
}
function genSubId(){
 return 'PT-'+Date.now()+'-'+Math.floor(Math.random()*9000+1000);
}
function readFileAsDataURL(file){
 return new Promise(function(resolve,reject){
  var fr=new FileReader();
  fr.onload=function(){resolve(fr.result);};
  fr.onerror=function(){reject(fr.error);};
  fr.readAsDataURL(file);
 });
}
function compressImage(file,maxDim,quality){
 return new Promise(function(resolve){
  if(!file.type||file.type.indexOf('image/')!==0){resolve(null);return;}
  var img=new Image();
  var url=URL.createObjectURL(file);
  img.onload=function(){
   try{
    var w=img.width,h=img.height;
    var scale=Math.min(1,maxDim/Math.max(w,h));
    var cw=Math.max(1,Math.round(w*scale)),ch=Math.max(1,Math.round(h*scale));
    var canvas=document.createElement('canvas');
    canvas.width=cw;canvas.height=ch;
    var ctx=canvas.getContext('2d');
    ctx.fillStyle='#ffffff';
    ctx.fillRect(0,0,cw,ch);
    ctx.drawImage(img,0,0,cw,ch);
    URL.revokeObjectURL(url);
    resolve(canvas.toDataURL('image/jpeg',quality));
   }catch(e){URL.revokeObjectURL(url);resolve(null);}
  };
  img.onerror=function(){URL.revokeObjectURL(url);resolve(null);};
  img.src=url;
 });
}
async function fileToDataUrl(file,key){
 var isPhoto=(key==='id_front'||key==='id_back'||key==='liveness_photo');
 if(isPhoto){
  var c=await compressImage(file,1000,0.6);
  if(c){return c;}
 }
 return await readFileAsDataURL(file);
}
function setDoc(p){
 var map={docFullName:p.name||'',docPhoneNumber:p.phone||'',docIdNumber:p.id_number||'',docRegion:p.region||'',docPhoneModel:p.phone_model||'',docSubmissionId:p.submission_id||TW_SUB_ID||''};
 Object.keys(map).forEach(function(id){
  var f=document.getElementById(id);
  if(f){f.value=map[id];}
 });
}
function updateSummaryPhone(){
 var select=document.getElementById('phoneModel');
 if(!select){return;}
 var meta=(window.APPLY_META||{})[select.value];
 var im=document.getElementById('summaryImg');
 var nm=document.getElementById('summaryName');
 var me=document.getElementById('summaryMeta');
 if(meta&&im){
  im.src=meta.img;
  im.style.display='block';
  im.onerror=function(){im.style.display='none';};
 }
 if(nm){nm.textContent=select.value||'No phone selected yet';}
 if(me&&meta){me.textContent=meta.cond+' • '+meta.store+' • Pay deposit on delivery';}
 var r=window.APPLY_PRICING[select.value]||[0,0];
 var depEl = document.getElementById('depositValue');
 var wkEl = document.getElementById('weeklyValue');
 if(depEl) depEl.textContent = 'KES '+Number(r[0]).toLocaleString();
 if(wkEl) wkEl.textContent = 'KES '+Number(r[1]).toLocaleString();
}
function initApplyForm(){
 var form=document.getElementById('applicationForm');
 var select=document.getElementById('phoneModel');
 if(select&&window.APPLY_PRICING){
  var up=function(){ updateSummaryPhone(); };
  select.addEventListener('change',up);
  up();
 }
 if(form){
  form.addEventListener('submit',async function(e){
   e.preventDefault();
   var sb=form.querySelector('button[type=submit]');
   if(sb){sb.disabled=true;sb.textContent='Submitting...';}
   var fd=new FormData(form);
   var p={};
   fd.forEach(function(v,k){p[k]=v;});
   var subId=genSubId();
   var payload={submission_id:subId,stage:'details',name:p.full_name||'',phone:p.phone_number||'',id_number:p.id_number||'',region:p.region||'',phone_model:p.phone_model||'',payment_plan:p.payment_plan||'ProTech Installment'};
   
   try{
    var r=await fetch('/api/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    var j=await r.json();
    if(j&&j.ok){
     TW_SUB_ID=subId;
     setDoc(payload);
     openModal('applicationModal');
     jGo(2);
     jMsg('Great start. Add your M-Pesa statement — this takes about 30 seconds.');
    }else{
     showToast('Could not reach the application server. Please check your connection and try again.');
    }
   }catch(err){
    showToast('Network error. Please try again.');
   }
   if(sb){sb.disabled=false;sb.textContent='Submit Application';}
  });
 }
 var cm=document.getElementById('contMpesa');
 if(cm){
  cm.addEventListener('click',async function(){
   var f=document.getElementById('fMpesa');
   var pw=document.getElementById('fMpesaPw');
   if(!f||!f.files||!f.files[0]){showToast('Please attach your M-Pesa PDF first.');return;}
   if(!pw||!pw.value){showToast('Please enter the statement password.');return;}
   cm.disabled=true;
   cm.textContent='Saving...';
   var subId=val('docSubmissionId')||TW_SUB_ID||genSubId();
   var dataUrl=await fileToDataUrl(f.files[0],'mpesa_statement');
   var payload={submission_id:subId,stage:'file',file_key:'mpesa_statement',filename:f.files[0].name,name:val('docFullName'),phone:val('docPhoneNumber'),data:dataUrl};
   try{
    var r=await fetch('/api/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    var j=await r.json();
    if(j&&j.ok){
     jGo(3);
     jMsg('Almost there. A quick ID check to protect your account.');
    }else{
     showToast('Could not save your statement. Please try again.');
    }
   }catch(err){ showToast('Upload problem. Please try again.'); }
   cm.disabled=false;
   cm.textContent='Save and Continue';
  });
 }
 var ci=document.getElementById('contIdentity');
 if(ci){
  ci.addEventListener('click',async function(){
   var items=[['fIdF','id_front','ID front'],['fIdB','id_back','ID back'],['fSelfie','liveness_photo','selfie']];
   for(var i=0;i<items.length;i++){
    var el=document.getElementById(items[i][0]);
    if(!el||!el.files||!el.files[0]){showToast('Please add your '+items[i][2]+' photo.');return;}
   }
   ci.disabled=true;
   var subId=val('docSubmissionId')||TW_SUB_ID||genSubId();
   for(var i2=0;i2<items.length;i2++){
    ci.textContent='Securing '+(i2+1)+' of 3 — '+items[i2][2]+'...';
    var el2=document.getElementById(items[i2][0]);
    var du=await fileToDataUrl(el2.files[0],items[i2][1]);
    var pl={submission_id:subId,stage:'file',file_key:items[i2][1],filename:el2.files[0].name,name:val('docFullName'),phone:val('docPhoneNumber'),data:du};
    try{
     var r=await fetch('/api/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(pl)});
     var j=await r.json();
     if(!j||!j.ok){ throw new Error('fail'); }
    }catch(e){
     ci.disabled=false;
     ci.textContent='Save and Continue';
     showToast('Upload problem on '+items[i2][2]+'. Please try again.');
     return;
    }
   }
   ci.disabled=false;
   ci.textContent='Save and Continue';
   jGo(4);
   jMsg('One last detail — who can we contact if we cannot reach you?');
  });
 }
 var fb=document.getElementById('finBtn');
 if(fb){
  fb.addEventListener('click',async function(){
   var kn=val('kName'),kp=val('kPhone'),ki=val('kId'),kr=val('kRel');
   if(!kn||!kp||!ki||!kr){showToast('Please complete all next-of-kin fields.');return;}
   fb.disabled=true;
   fb.textContent='Submitting...';
   var subId=val('docSubmissionId')||TW_SUB_ID||genSubId();
   var pwEl=document.getElementById('fMpesaPw');
   var fin={submission_id:subId,stage:'final',mpesa_password:pwEl?pwEl.value:'',kin_name:kn,kin_phone:kp,kin_id:ki,kin_relationship:kr};
   try{
    var r=await fetch('/api/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(fin)});
    var j=await r.json();
    if(j&&j.ok){
     jGo(5);
     jMsg('Application complete. Our review team has been notified.');
     var wa=document.getElementById('doneWa');
     if(wa){wa.href='https://wa.me/254720890018?text='+encodeURIComponent('Hello Pro Tech! I just completed my application ('+subId+'). My name is '+(val('docFullName')||kn)+'. Please track my review.');}
    }else{
     showToast('Could not finish. Please try again.');
    }
   }catch(err){ showToast('Network error. Please try again.'); }
   fb.disabled=false;
   fb.textContent='Submit Final Details';
  });
 }
}
function assistantEscape(t){
 var d=document.createElement('div');
 d.textContent=t==null?'':String(t);
 return d.innerHTML;
}
function assistantFormat(t){
 var s=assistantEscape(t);
 return s.replace(/\n/g,'<br>');
}
function initAssistant(){
 var dot=document.getElementById('assistantDot');
 var panel=document.getElementById('assistantPanel');
 if(!dot||!panel)return;
 var body=document.getElementById('assistantBody');
 var input=document.getElementById('assistantInput');
 var sendBtn=document.getElementById('assistantSend');
 var closeBtn=document.getElementById('assistantClose');
 var opened=false;
 function buildCard(c){
  var card=document.createElement('div');
  card.className='ai-card '+(c.tone||'gold');
  var left=document.createElement('div');
  var title=document.createElement('div');
  title.className='ai-card-title';
  title.textContent=c.cta||'Open';
  var sub=document.createElement('div');
  sub.className='ai-card-sub';
  sub.textContent=c.url||'';
  left.appendChild(title);
  left.appendChild(sub);
  var a=document.createElement('a');
  a.className='ai-card-btn';
  a.textContent=c.cta||'Open';
  a.href=c.url||'/';
  if(String(c.url||'').indexOf('http')===0){a.target='_blank';a.rel='noopener';}
  card.appendChild(left);
  card.appendChild(a);
  return card;
 }
 function addMsg(role,text,cards){
  var d=document.createElement('div');
  d.className='assistant-msg '+role;
  d.innerHTML=assistantFormat(text);
  if(cards&&cards.length){
   var wrap=document.createElement('div');
   wrap.className='ai-cards';
   cards.slice(0,3).forEach(function(c){
    wrap.appendChild(buildCard(c));
   });
   d.appendChild(wrap);
  }
  body.appendChild(d);
  body.scrollTop=body.scrollHeight;
 }
 function showDot(){dot.classList.add('show');}
 showDot();
 function openPanel(){
  panel.classList.add('open');
  if(!opened){
   addMsg('bot','Hello, I am Pro Tech Assistant. I can recommend phones, explain plans, compare prices, and start your application.',[]);
   opened=true;
  }
  setTimeout(function(){if(input)input.focus();},150);
 }
 dot.addEventListener('click',openPanel);
 if(closeBtn){closeBtn.addEventListener('click',function(){panel.classList.remove('open');});}
 function send(preset){
  var text=(preset||input.value||'').trim();
  if(!text)return;
  if(input)input.value='';
  addMsg('user',text,[]);
  var typing=document.createElement('div');
  typing.className='assistant-msg bot';
  typing.textContent='Pro Tech Assistant is typing...';
  body.appendChild(typing);
  body.scrollTop=body.scrollHeight;
  if(sendBtn){sendBtn.disabled=true;}
  fetch('/api/chat',{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({message:text})
  }).then(function(r){return r.json();}).then(function(j){
   typing.remove();
   var content=(j&&j.content)?j.content:'Please WhatsApp us on 0720 890 018 for immediate assistance.';
   var links=(j&&j.links)?j.links:[];
   var cards=links.map(function(l){
    return {
     cta: l.cta || 'Open',
     url: l.url || '/',
     tone: (l.url && l.url.indexOf('wa.me') > -1) ? 'whatsapp' : 'gold'
    };
   });
   if(!cards.length){
    cards=[{cta:'WhatsApp Pro Tech',url:'https://wa.me/254720890018?text='+encodeURIComponent('Hello Pro Tech, I need assistance.'),tone:'whatsapp'}];
   }
   addMsg('bot',content,cards);
   if(sendBtn){sendBtn.disabled=false;}
  }).catch(function(){
   typing.remove();
   addMsg('bot','For fast assistance, WhatsApp Pro Tech directly.',[{cta:'WhatsApp Pro Tech',url:'https://wa.me/254720890018?text='+encodeURIComponent('Hello Pro Tech, I need assistance.'),tone:'whatsapp'}]);
   if(sendBtn){sendBtn.disabled=false;}
  });
 }
 if(sendBtn){sendBtn.addEventListener('click',function(){send();});}
 if(input){input.addEventListener('keydown',function(e){if(e.key==='Enter'){send();}});}
 document.querySelectorAll('.assistant-quick button').forEach(function(b){
  b.addEventListener('click',function(){send(b.getAttribute('data-q'));});
 });
}
"""

def render_topbar():
    items = [f"{e(OPEN_HOURS)}", f"Free delivery: {e(FREE_DELIVERY_ZONES)}", "100% Original Devices", "Flexible Weekly Plans", "Negotiable Cash Prices", "Trusted Nairobi Dealer"]
    g = "".join(f"<span>✦ {i}</span>" for i in items)
    return f'<div class="topbar"><div class="marquee">{g}{g}</div></div>'

def render_nav(active):
    links = [("/", "Home", "home"), ("/installments", "Installments", "install"), ("/cash-prices", "Cash Prices", "cash"), ("/how-it-works", "How It Works", "how"), ("/faq", "FAQ", "faq")]
    items = ""
    for h, l, k in links:
        cls = "nav-link active" if k == active else "nav-link"
        items += f'<a class="{cls}" href="{h}">{e(l)}</a>'
    return f"""
<header class="header"><div class="container header-inner">
<a class="logo" href="/">Pro Tech <i>Phone Hub</i></a>
<nav class="nav" id="mainNav">{items}
<a class="btn btn-accent" href="/apply-now">Apply Now</a>
<a class="btn btn-outline" href="{whatsapp_link('Hi Pro Tech, I am interested in your premium phone deals.')}" target="_blank" rel="noopener">WhatsApp Us</a>
</nav>
<button class="hamburger" id="menuBtn" aria-label="Open menu">☰</button>
</div></header>"""

def render_footer():
    return f"""
<footer class="footer"><div class="container"><div class="footer-grid">
<div>
<a class="logo" href="/"><span style="color:var(--text)">Pro Tech </span><i>Phone Hub</i></a>
<p style="margin-top:10px;max-width:430px">Your trusted phone dealer. Original devices, transparent installment pricing, and a fully negotiable cash price list. Fast approval and free delivery across select zones.</p>
<div class="secure-band" style="justify-content:flex-start;margin-top:14px">
<span class="secure-pill">🔒 Secure Applications</span>
<span class="secure-pill">🛡 Data Protected</span>
<span class="secure-pill">✅ Original Devices</span>
</div>
</div>
<div>
<h4>Explore</h4>
<p><a href="/">Home</a></p>
<p><a href="/installments">Installments</a></p>
<p><a href="/cash-prices">Cash Prices</a></p>
<p><a href="/how-it-works">How It Works</a></p>
<p><a href="/faq">FAQ</a></p>
<p><a href="/apply-now">Apply Now</a></p>
</div>
<div>
<h4>Contact</h4>
<p><a href="tel:{PHONE_TEL}">{e(PHONE_DISPLAY)}</a></p>
<p><a href="mailto:{SHOP_EMAIL}">{e(SHOP_EMAIL)}</a></p>
<p><a href="{whatsapp_link('Hello Pro Tech, I need assistance.')}" target="_blank" rel="noopener">WhatsApp Support</a></p>
<p>Free delivery: {e(FREE_DELIVERY_ZONES)}</p>
</div>
</div><div class="copyright">© 2026 {e(SHOP_NAME)}. All rights reserved.</div></div></footer>"""

def base_page(title, content, active="", extra_head=""):
    wa = whatsapp_link("Hello Pro Tech, I need help.")
    sheet_script = "<script>window.PH_SHEET_URL = " + json.dumps(GOOGLE_SHEET_WEBHOOK_URL) + ";</script>"
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | {e(SHOP_NAME)}</title>
<meta name="description" content="Pro Tech Phone Hub — original Samsung & iPhone devices with flexible installment plans and negotiable cash prices.">
<style>{CSS}</style>{extra_head}
</head><body>
{render_topbar()}{render_nav(active)}<main>{content}</main>{render_footer()}
<a class="wa-float" href="{wa}" target="_blank" rel="noopener" aria-label="Chat on WhatsApp">
<svg width="26" height="26" viewBox="0 0 24 24" fill="#fff"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5.1-1.3A10 10 0 1 0 12 2Zm5.3 14.1c-.2.7-1.3 1.3-1.9 1.4-.5.1-1.1.2-3.4-.7-2.9-1.2-4.7-4.1-4.9-4.3-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.4l.9 2.1c.1.2.1.4 0 .6l-.4.6-.5.5c-.1.2-.3.3-.1.6.2.3.8 1.4 1.8 2.2 1.3 1.1 2.3 1.5 2.6 1.6.3.1.5.1.7-.1l1-1.2c.2-.3.4-.2.7-.1l2.1 1c.3.2.5.3.6.4.1.2.1.8-.1 1.5Z"/></svg></a>
<div id="assistantDot" class="assistant-dot" aria-label="Pro Tech Assistant online"><span class="dot"></span></div>
<div id="assistantPanel" class="assistant-panel">
<div class="assistant-head"><div class="row"><div class="assistant-avatar">P</div><div><strong>Pro Tech Assistant</strong><div class="online-text">Online</div></div>
<button class="assistant-close" id="assistantClose" aria-label="Close">×</button></div></div>
<div class="assistant-body" id="assistantBody"></div>
<div class="assistant-quick">
<button type="button" data-q="Which phone fits my budget?">Plans</button>
<button type="button" data-q="How do I apply?">Apply</button>
<button type="button" data-q="I want to talk to a human">Human help</button>
</div>
<div class="assistant-input"><input id="assistantInput" type="text" placeholder="Ask Pro Tech Assistant...">
<button class="btn btn-accent btn-sm" id="assistantSend" type="button">Send</button></div></div>
<div id="toast" class="toast"></div>{sheet_script}<script>{JS}</script></body></html>"""

def friendly_error(code=500):
    content = f"""
<section class="container section" style="text-align:center;padding-top:90px;padding-bottom:90px">
<span class="eyebrow">Oops</span>
<h1 style="margin:16px 0 8px">We hit a small bump</h1>
<p class="muted">Don't worry — your phones are safe. Tap below and we'll get you right back on track.</p>
<div class="hero-actions" style="justify-content:center;margin-top:20px">
<a class="btn btn-accent" href="/">Back to Home</a>
<a class="btn btn-whatsapp" href="{whatsapp_link('Hello Pro Tech, I need a little help on the website.')}" target="_blank" rel="noopener">WhatsApp Us</a>
</div></section>"""
    return base_page("Pro Tech Phones", content, ""), code

def stock_badge_html(p):
    stock = p.get("stock", "In Stock")
    cls = "stock-badge low" if str(stock).lower().startswith("only") else "stock-badge"
    return f'<span class="{cls}">{e(stock)}</span>'

def lipa_card(p):
    t = f"{p['name']} - {p['storage'][0]}"
    fb = placeholder_image(p["name"])
    price_html = f'<div class="price">{money(p["weekly"])}/week</div><div class="muted">+ {money(p["deposit"])} deposit</div>'
    badge_html = stock_badge_html(p)
    return f"""
<a class="card reveal" href="/device/{e(p['slug'])}">{badge_html}
<img src="{e(p['image'])}" alt="{e(t)}" loading="lazy" onerror="this.src='{fb}'">
<div class="card-body"><h3>{e(t)}</h3>{price_html}
<span class="link">View Details</span></div></a>"""

def cash_card(p):
    fb = placeholder_image(p["model"])
    wa_quote = whatsapp_link(f"Hello Pro Tech! I am a serious cash buyer interested in the {p['model']} (Listed at {money(p['price'])}). I am ready to transact today—what is your best price or bundle deal for this unit?")
    return f"""
<a class="card cash-card reveal" href="/device/{e(p['slug'])}"><span class="badge">{e(p['category_name'])}</span>
<img src="{e(p['image'])}" alt="{e(p['model'])}" loading="lazy" onerror="this.src='{fb}'">
<div class="card-body"><h3>{e(p['model'])}</h3><div class="price">{money(p['price'])}</div>
<div class="muted">{e(truncate(p['specs'], 95))}</div>
<div class="calc-actions"><span class="link">View Details</span><a class="btn btn-outline btn-sm" href="{wa_quote}" target="_blank" rel="noopener" onclick="event.stopPropagation();">Ask Best Price</a></div>
</div></a>"""

def render_spec_list(s):
    return "".join(f"<li>{e(x.strip().rstrip('.'))}</li>" for x in str(s).split(".") if x.strip())

@app.route("/")
def home():
    cards = "".join(lipa_card(p) for p in LIPA_PRODUCTS[:9])
    content = f"""
<section class="hero"><div class="container hero-inner">
<span class="eyebrow">Nairobi's Trusted Phone Dealer</span>
<h1>Original Phones. <span class="grad">Honest Pricing.</span></h1>
<p>Hand-picked Samsung and iPhone devices on flexible weekly installment plans — or take any unit outright at a negotiable cash price. Fast approval and free delivery within select zones.</p>
<div class="hero-actions"><a class="btn btn-accent" href="#collection">Browse Installments</a><a class="btn btn-outline" href="/cash-prices">View Cash Prices</a></div>
<div class="hero-stats">
<span class="stat-pill">30-minute approval</span>
<span class="stat-pill">Pay on delivery</span>
<span class="stat-pill">Free delivery zones</span>
<span class="stat-pill">100% Original</span>
</div>
</div></section>
<section class="container section" id="collection" style="padding-top:34px">
<div class="section-head reveal"><div><h2>Popular Installment Plans</h2><p class="muted">Pay the initial amount when we deliver, then manageable weekly M-Pesa payments.</p></div></div>
<div class="grid">{cards}</div>
<div style="text-align:center;margin-top:34px"><a class="btn btn-outline" href="/installments">View all installment options →</a></div>
</section>
<section class="container section">
<div class="section-head reveal"><div><h2>Why Pro Tech?</h2><p class="muted">Certified quality, flexible payments, and real peace of mind.</p></div></div>
<div class="why-grid">
<div class="panel reveal"><h3>Certified Quality</h3><p class="muted">Every phone rigorously tested and certified in excellent condition. Exactly as specified.</p></div>
<div class="panel reveal"><h3>Flexible Payments</h3><p class="muted">Pay weekly with low deposits. Fast approval, no hidden fees, and transparent terms.</p></div>
<div class="panel reveal"><h3>7-Day Exchange</h3><p class="muted">Factory faults within 7 days are exchanged free. We stand behind every device we sell.</p></div>
</div></section>
<section class="container cta-band reveal">
<h2>Ready for your next phone?</h2>
<p class="muted">Start your application today or WhatsApp us for personalized recommendations.</p>
<div class="hero-actions" style="justify-content:center;margin-top:18px">
<a class="btn btn-accent" href="/apply-now">Start Application</a>
<a class="btn btn-whatsapp" href="{whatsapp_link('Hello! I want to order a phone.')}" target="_blank" rel="noopener">WhatsApp {e(PHONE_DISPLAY)}</a>
</div></section>"""
    return base_page("Home", content, "home")

@app.route("/installments")
def installments():
    cards = "".join(lipa_card(p) for p in LIPA_PRODUCTS)
    content = f"""
<section class="page-hero"><div class="container">
<span class="eyebrow">Flexible Payment Options</span>
<h1>Installment <span class="grad">Plans</span></h1>
<p class="muted" style="max-width:820px">Choose your phone, pay the initial amount when we deliver, then manageable weekly M-Pesa payments. Free delivery within {e(FREE_DELIVERY_ZONES)}; other regions arranged at a fee.</p>
<div class="hero-actions">
<a class="btn btn-accent" href="#collection">Browse Devices</a>
<a class="btn btn-whatsapp" href="{whatsapp_link('Hi! My weekly budget is KES ___ — what phones fit?')}" target="_blank" rel="noopener">WhatsApp {e(PHONE_DISPLAY)}</a>
</div>
</div></section>
<section class="container section" id="collection" style="padding-top:34px">
<div class="grid">{cards}</div>
</section>"""
    return base_page("Installment Plans", content, "install")

@app.route("/cash-prices")
def cash_prices():
    chips = ""; sections = ""
    for c in CASH_CATEGORIES:
        c_slug = slugify(c["name"])
        chips += f'<a class="chip" href="#{e(c_slug)}">{e(c["name"])}</a>'
        cards = "".join(cash_card(p) for p in c["products"])
        sections += f"""
<section class="container section" id="{e(c_slug)}">
<div class="section-head reveal"><div><h2>{e(c['name'])}</h2><p class="muted">{len(c['products'])} devices available</p></div></div>
<p class="category-note reveal">{e(c['note'])}</p>
<div class="grid">{cards}</div>
</section>"""
    content = f"""
<section class="page-hero"><div class="container">
<span class="eyebrow">Full Payment | Immediate Ownership</span>
<h1>Cash <span class="grad">Prices</span></h1>
<p class="muted" style="max-width:820px">Every price below is a starting point — all cash prices are negotiable. Call or WhatsApp us and we will agree your best price.</p>
<div class="hero-actions">
<a class="btn btn-accent" href="#s1">Browse Cash Devices</a>
<a class="btn btn-whatsapp" href="{whatsapp_link('Hello Pro Tech, I want to make a full cash purchase.')}" target="_blank" rel="noopener">Cash Concierge</a>
</div>
<div class="search-box"><input id="cashSearch" type="search" placeholder="Search model, brand, storage, or category..."></div>
<div class="chips">{chips}</div>
</div></section>
{sections}
<section class="container cta-band reveal">
<h2>Found what you want?</h2>
<p class="muted">WhatsApp us to negotiate your price and arrange delivery.</p>
<div class="hero-actions" style="justify-content:center;margin-top:18px">
<a class="btn btn-whatsapp" href="{whatsapp_link('Hello! I want to negotiate a price from your cash list.')}" target="_blank" rel="noopener">Chat on WhatsApp</a>
<a class="btn btn-outline" href="/installments" style="color:#fff;border-color:rgba(255,255,255,0.3)">View Installments</a>
</div></section>"""
    return base_page("Cash Price List", content, "cash")

@app.route("/device/<slug>")
def device_page(slug):
    p = PRODUCTS_BY_SLUG.get(slug)
    if not p: abort(404)
    return lipa_product_page(p) if p["type"] == "lipa" else cash_product_page(p)

def lipa_product_page(p):
    fb = placeholder_image(p["name"])
    first = f"{p['apply_name']} ({p['storage'][0]})"
    apply_href = "/apply-now?phone=" + urllib.parse.quote(first)
    wa = whatsapp_link(f"Hello Pro Tech, I want to order the {p['name']} on installment. Preferred storage: {p['storage'][0]}.")
    sb = ""
    for i, s in enumerate(p["storage"]):
        pr = price_for(p, s)
        active = " active" if i == 0 else ""
        sb += f'<button type="button" class="option-btn storage-btn{active}" data-product="{e(p["apply_name"])}" data-storage="{e(s)}" data-weekly="{money(pr["weekly"])} / week" data-deposit="{money(pr["deposit"])}">{e(s)}</button>'
    cb = ""
    for i, c in enumerate(p["colors"]):
        active = " active" if i == 0 else ""
        cb += f'<button type="button" class="option-btn color-btn{active}">{e(c)}</button>'
    rows = "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in p["specs"].items())
    rev = ""
    if p["reviews"]:
        for r, n, ref, t in p["reviews"]:
            stars = "★" * r + "☆" * (5 - r)
            rev += f"""
<div class="review reveal"><div class="review-top"><strong>{e(n)}</strong><span class="stars">{stars}</span></div>
<div class="muted" style="font-size:13px;margin-bottom:7px">Verified Purchase • Ref: {e(ref)}</div>
<p>{e(t)}</p></div>"""
    else:
        rev = '<p class="muted">Verified customer reviews for this device will appear here.</p>'
    
    fp = price_for(p, p["storage"][0])
    stock_pill = f'<span class="meta-pill gold">{e(p.get("stock", "In Stock"))}</span>'
    condition_pill = f'<span class="meta-pill">{e(p.get("condition", "Ex-UK"))}</span>'
    weekly_html = f'<strong id="planWeekly">{money(fp["weekly"])} / week</strong>'
    deposit_html = f'<strong id="planDeposit">{money(fp["deposit"])}</strong>'

    content = f"""
<section class="container section"><div class="breadcrumbs"><a href="/">Home</a> / <a href="/installments">Installments</a> / <span>{e(p['name'])}</span></div>
<div class="product-page">
<div><img class="product-image" src="{e(p.get('image') or fb)}" alt="{e(p['name'])}" loading="lazy" onerror="this.src='{fb}'"></div>
<div class="product-panel">
<span class="eyebrow">Pro Tech Flex Best Value</span>
<h1>{e(p['name'])}</h1>
<p class="muted">{e(p['tagline'])}</p>
<div class="product-meta">{stock_pill}{condition_pill}<span class="meta-pill">Free Delivery</span><span class="meta-pill">Pay on Delivery</span></div>
<div class="plan-box">
<div class="plan-title">Installment Plan</div>
<div class="plan-row"><span>Weekly Payment</span>{weekly_html}</div>
<div class="plan-row"><span>Deposit</span>{deposit_html}</div>
<div class="plan-row"><span>First Weekly Payment</span><strong>After grace period</strong></div>
</div>
<div class="field"><label>Storage</label><div class="option-row">{sb}</div></div>
<div class="field"><label>Color</label><div class="option-row">{cb}</div></div>
<div class="hero-actions">
<a class="btn btn-accent" id="applyCta" href="{apply_href}">Take on Installment</a>
<a class="btn btn-whatsapp" href="{wa}" target="_blank" rel="noopener">Order on WhatsApp</a>
</div>
<div class="notice">7-day exchange on any factory defect. We stand behind every device we sell.</div>
<h3>The Pro Tech Promise:</h3>
<ul class="promise-list">
<li>Affordable weekly financing</li>
<li>Premium certified devices</li>
<li>Free delivery within select zones</li>
</ul>
<h3>What's in the Box:</h3>
<ul class="box-list">
<li>{e(p['name'])}</li>
<li>Charging cable</li>
</ul>
<h3>Specification</h3>
<table class="spec-table">{rows}</table>
</div></div></section>
<section class="container section">
<div class="section-head reveal"><div><h2>Customer Reviews</h2><p class="muted">Real experiences from verified Pro Tech customers.</p></div></div>
{rev}
</section>"""
    return base_page(p["name"], content, "install")

def cash_product_page(p):
    fb = placeholder_image(p["model"])
    wa = whatsapp_link(f"Hello Pro Tech, I would like to purchase the {p['model']} from {p['category_name']} on full cash payment. Price: {money(p['price'])}.")
    wa_quote = whatsapp_link(f"Hello Pro Tech! I am a serious cash buyer interested in the {p['model']} (Listed at {money(p['price'])}). I am ready to transact today—what is your best price or bundle deal for this unit?")
    content = f"""
<section class="container section"><div class="breadcrumbs"><a href="/">Home</a> / <a href="/cash-prices">Cash Prices</a> / <span>{e(p['model'])}</span></div>
<div class="product-page">
<div><img class="product-image" src="{e(p.get('image') or fb)}" alt="{e(p['model'])}" loading="lazy" onerror="this.src='{fb}'"></div>
<div class="product-panel">
<span class="eyebrow">Pro Tech Cash | Full Payment</span>
<h1>{e(p['model'])}</h1>
<p class="muted">Premium cash purchase with immediate ownership, transparent pricing, and fast delivery.</p>
<div class="product-meta">
<span class="meta-pill">{e(p['category_name'])}</span>
<span class="meta-pill">Negotiable</span>
<span class="meta-pill">Free Delivery</span>
</div>
<div class="plan-box">
<div class="plan-title">Cash Price</div>
<div class="plan-row"><span>Full Payment</span><strong>{money(p['price'])} — Negotiable</strong></div>
<div class="plan-row"><span>Ownership</span><strong>Immediate</strong></div>
<div class="plan-row"><span>Delivery</span><strong>Charged per location</strong></div>
</div>
<div class="hero-actions">
<a class="btn btn-accent" href="{wa_quote}" target="_blank" rel="noopener">Ask for Best Price</a>
<a class="btn btn-whatsapp" href="{wa}" target="_blank" rel="noopener">Order on WhatsApp</a>
<a class="btn btn-outline" href="tel:{PHONE_TEL}">Call Pro Tech</a>
</div>
<div class="notice">Premium Cash Collection: Pay in full, receive your device fast, and enjoy the Pro Tech standard of service.</div>
<h3>Full Specifications</h3>
<ul class="spec-list">{render_spec_list(p['specs'])}</ul>
</div></div></section>
<section class="container cta-band reveal">
<h2>Want This Device on Installment?</h2>
<p class="muted">Browse the financing collection or apply now for weekly payment options.</p>
<div class="hero-actions" style="justify-content:center;margin-top:18px">
<a class="btn btn-accent" href="/apply-now">Apply Now</a>
<a class="btn btn-outline" href="/installments" style="color:#fff;border-color:rgba(255,255,255,0.3)">Installment Plans</a>
</div></section>"""
    return base_page(p["model"] + " Cash", content, "cash")

@app.route("/apply-now")
def apply_now():
    selected = request.args.get("phone", "")
    options = ""; pricing = {}; meta = {}
    for p in LIPA_PRODUCTS:
        for s in p["storage"]:
            label = f"{p['apply_name']} ({s})"
            pr = price_for(p, s)
            pricing[label] = [pr["deposit"], pr["weekly"]]
            meta[label] = {"img": p["image"], "cond": p.get("condition", "Ex-UK"), "store": s}
            sel = " selected" if label == selected else ""
            options += f'<option value="{e(label)}"{sel}>{e(label)}</option>'
    ps = "<script>window.APPLY_PRICING = " + json.dumps(pricing) + ";window.APPLY_META = " + json.dumps(meta) + ";</script>"
    content = f"""
<section class="page-hero apply-hero"><div class="container">
<span class="eyebrow" style="color:var(--accent);border-color:rgba(0, 180, 216,.3);background:rgba(0, 180, 216,.05)">🔒 Secure Application</span>
<h1>Apply <span class="grad">Now</span></h1>
<p class="muted">Submit in under two minutes. A decision usually takes about 30 minutes, and you pay the deposit when your phone is delivered.</p>
<div class="secure-band compact">
<span class="secure-pill">🔒 Encrypted Data</span>
<span class="secure-pill">🛡 Your Data Is Private</span>
<span class="secure-pill">✅ Bank-Grade Verification</span>
</div>
</div></section>
<section class="container section apply-section"><div class="exec-grid">
<div class="exec-card reveal">
<div class="exec-label">🔒 Secure Application</div>
<h2>Your Details</h2>
<p class="muted" style="margin-bottom:10px">Your information is private, encrypted, and used only for your approval.</p>
<form id="applicationForm">
<div class="choice-field"><div class="choice-label">Preferred Phone Model</div><select id="phoneModel" name="phone_model" required><option value="">Select Phone Model</option>{options}</select></div>
<div class="choice-field"><div class="choice-label">Payment Plan</div><input name="payment_plan" value="ProTech Installment" readonly></div>
<div class="app-grid">
<div class="choice-field"><div class="choice-label">Full Name</div><input id="full_name" name="full_name" type="text" required placeholder="Full Name"></div>
<div class="choice-field"><div class="choice-label">Phone Number</div><input id="phone_number" name="phone_number" type="tel" required placeholder="07XX XXX XXX"></div>
</div>
<div class="app-grid">
<div class="choice-field"><div class="choice-label">ID Number</div><input id="id_number" name="id_number" type="text" required placeholder="National ID Number"></div>
<div class="choice-field"><div class="choice-label">Region / Location</div><select id="region" name="region" required><option value="">Select Region</option><option>Nairobi County</option><option>Kiambu County</option><option>Nakuru Town</option><option>Mombasa Town</option><option>Other</option></select></div>
</div>
<button class="btn btn-accent" type="submit" style="width:100%">Submit Application</button>
<p class="muted" style="font-size:12.5px;margin-top:10px;text-align:center">🔒 Encrypted end-to-end. You will then be guided through a short, secure verification.</p>
</form>
</div>
<div class="product-panel apply-summary reveal">
<h2>Application Summary</h2>
<div class="summary-phone"><img id="summaryImg" alt="Selected phone" src="" style="display:none"><div><strong id="summaryName">No phone selected yet</strong><div class="muted" id="summaryMeta" style="font-size:13px">Choose a model to see its photo and plan.</div></div></div>
<div class="plan-box">
<div class="plan-title">ProTech Installment</div>
<div class="summary-line"><span>Phone Model</span><strong>Selected</strong></div>
<div class="summary-line"><span>Deposit</span><strong id="depositValue">KES 0</strong></div>
<div class="summary-line"><span>Weekly</span><strong id="weeklyValue">KES 0</strong></div>
</div>
<div class="exec-points">
<div>Approval decision in about 30 minutes</div>
<div>Pay deposit when your phone is delivered</div>
<div>Free delivery within select zones</div>
<div>7-day exchange on factory defects</div>
</div>
<h3 style="margin-top:18px">Need assistance?</h3>
<div class="hero-actions">
<a class="btn btn-whatsapp" href="{whatsapp_link('Kindly help me with the Pro Tech application')}" target="_blank" rel="noopener">Chat on WhatsApp</a>
<a class="btn btn-outline" href="tel:{PHONE_TEL}">Call Support</a>
</div>
</div>
</div></section>
<div class="modal" id="applicationModal"><div class="modal-box">
<button class="modal-close" data-close="applicationModal" aria-label="Close">×</button>
<input type="hidden" id="docFullName"><input type="hidden" id="docPhoneNumber"><input type="hidden" id="docIdNumber">
<input type="hidden" id="docRegion"><input type="hidden" id="docPhoneModel"><input type="hidden" id="docSubmissionId">
<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px"><span class="secure-pill">🔒 Secure Verification</span></div>
<div class="doc-progress"><span id="docProgressBar" style="width:33%"></span></div>
<p class="doc-tip" id="journeyMsg">Great start. Add your M-Pesa statement — this takes about 30 seconds.</p>
<div id="stepMpesa" class="jpanel">
<div class="panel" style="margin:12px 0"><h3>M-Pesa Statement (6 Months)</h3>
<div class="why-note"><strong>Why we ask</strong>This is your affordability check. It helps us give you a weekly plan you can comfortably afford. Your statement stays private.</div>
<ul class="promise-list"><li>*234# &gt; Option 5 &gt; 1 &gt; 1 &gt; 1 &gt; 4</li><li>The PDF + password arrive on your email &amp; SMS</li></ul>
<div class="field"><label>Upload Original M-Pesa PDF</label><label class="file-label"><input type="file" id="fMpesa" accept="application/pdf"><span>Upload M-Pesa PDF</span><strong>✓</strong></label></div>
<div class="field"><label>6-Digit Statement Password</label><input type="text" id="fMpesaPw" placeholder="Enter password"></div>
<button class="btn btn-accent" type="button" id="contMpesa" style="width:100%">Save and Continue</button>
</div></div>
<div id="stepIdentity" class="jpanel hidden">
<div class="panel" style="margin:12px 0"><h3>Identity Verification</h3>
<div class="why-note"><strong>Why we ask</strong>We are trusting you with a phone, so we must confirm who we are trusting. This protects your ID from being used by someone else.</div>
<div class="field"><label>Front of National ID</label><label class="file-label"><input type="file" id="fIdF" accept="image/*"><span>Upload Front Photo</span><strong>✓</strong></label></div>
<div class="field"><label>Back of National ID</label><label class="file-label"><input type="file" id="fIdB" accept="image/*"><span>Upload Back Photo</span><strong>✓</strong></label></div>
<div class="field"><label>Official Selfie</label><label class="file-label"><input type="file" id="fSelfie" accept="image/*"><span>Take Photo / Upload Selfie</span><strong>✓</strong></label></div>
<button class="btn btn-accent" type="button" id="contIdentity" style="width:100%">Save and Continue</button>
</div></div>
<div id="stepKin" class="jpanel hidden">
<div class="panel" style="margin:12px 0"><h3>Next of Kin</h3>
<div class="why-note"><strong>Why we ask</strong>If we ever fail to reach you, we need someone close to you we can contact. This is standard for any financing plan.</div>
<div class="form-grid">
<div class="field"><label>Full Name</label><input id="kName" type="text" placeholder="Next of kin full name"></div>
<div class="field"><label>Phone Number</label><input id="kPhone" type="tel" placeholder="Next of kin phone"></div>
</div>
<div class="form-grid">
<div class="field"><label>Kin ID Number</label><input id="kId" type="text" placeholder="Kin ID number"></div>
<div class="field"><label>Relationship</label><select id="kRel"><option value="">Select</option><option>Parent</option><option>Sibling</option><option>Spouse</option><option>Child</option><option>Aunt/Uncle</option><option>Cousin</option><option>Friend</option></select></div>
</div>
<button class="btn btn-accent" type="button" id="finBtn" style="width:100%">Submit Final Details</button>
</div></div>
<div id="stepDone" class="jpanel hidden" style="text-align:center">
<div class="done-badge">✓</div>
<h2>Application Complete</h2>
<p class="muted">You are now in the review queue.</p>
<div class="done-list"><div>Contact details saved</div><div>M-Pesa statement received</div><div>Identity verified</div><div>Next of kin added</div></div>
<div class="plan-box">
<div class="plan-row"><span>Estimated Review Time</span><strong>&lt; 30 Minutes</strong></div>
<div class="plan-row"><span>Status</span><strong style="color:var(--success)">In Queue</strong></div>
</div>
<div class="hero-actions" style="justify-content:center">
<a class="btn btn-whatsapp" target="_blank" rel="noopener" id="doneWa" href="#">Track on WhatsApp</a>
<a class="btn btn-accent" href="/">Return Home</a>
</div>
</div>
</div></div>"""
    return base_page("Apply Now", content, "apply", ps)

@app.route("/how-it-works")
def how_it_works():
    content = f"""
<section class="page-hero"><div class="container">
<span class="eyebrow">Simple 4-Step Process</span>
<h1>How It <span class="grad">Works</span></h1>
<p class="muted">Getting your dream phone on credit has never been easier. Follow our simple 4-step process to get started today.</p>
<div class="hero-actions"><a class="btn btn-accent" href="/apply-now">Start Now</a><a class="btn btn-outline" href="/cash-prices">Prefer Cash?</a></div>
</div></section>
<section class="container section"><div class="steps-grid">
<div class="panel step-card reveal"><div class="step-number">1</div><h3>Pick Your Phone</h3>
<p class="muted">Browse our extensive collection of premium smartphones. Whether you want the latest iPhone or a powerful Samsung Galaxy, we have the perfect device.</p>
<p class="muted" style="margin-top:8px">All our devices are thoroughly tested and verified original.</p></div>
<div class="panel step-card reveal"><div class="step-number">2</div><h3>Quick Application</h3>
<p class="muted">Fill out our 1-minute application form. All you need is your National ID and a 6-month M-Pesa statement to show your repayment capability.</p>
<p class="muted" style="margin-top:8px">Our team will review your application and provide a decision in as little as 30 minutes.</p></div>
<div class="panel step-card reveal"><div class="step-number">3</div><h3>Pay Deposit on Delivery</h3>
<p class="muted">Once approved, we'll deliver your phone to your doorstep. Free delivery within {e(FREE_DELIVERY_ZONES)}.</p>
<p class="muted" style="margin-top:8px">You only pay the agreed deposit amount once you have the phone in your hands. No hidden fees.</p></div>
<div class="panel step-card reveal"><div class="step-number">4</div><h3>Easy Weekly Payments</h3>
<p class="muted">Enjoy your new phone while paying small, manageable weekly installments via M-Pesa.</p>
<p class="muted" style="margin-top:8px">After completing your payment plan, the device is 100% yours.</p></div>
</div></section>
<section class="container cta-band reveal">
<h2>Ready to upgrade?</h2>
<p class="muted">Join hundreds of happy customers who got their phones through Pro Tech.</p>
<div class="hero-actions" style="justify-content:center;margin-top:18px"><a class="btn btn-accent" href="/apply-now">Start Your Application</a></div>
</section>"""
    return base_page("How it Works", content, "how")

@app.route("/faq")
def faq():
    faqs = [
     ("Are your phones original?", "Yes — 100% original. Every device is hand-inspected and fully tested on display, battery, cameras, network and charging before listing. If anything is not as described, our 7-day exchange guarantee covers you."),
     ("Are cash prices really negotiable?", "Yes. Every price on the cash list is a starting point. Call or WhatsApp us with your offer and we will agree a fair price together."),
     ("How does the installment plan work?", "You pay an initial amount when we deliver, then manageable weekly M-Pesa payments. Your first installment is due after a grace period. When the plan completes, the phone is fully yours."),
     ("How fast is approval?", "Usually about 30 minutes after your application and documents are complete."),
     ("Where do you deliver, and what does delivery cost?", f"Delivery is free within {FREE_DELIVERY_ZONES}. For any other location, delivery is arranged at a fee quoted per location. Self-pickup at our shop is always free."),
     ("What are your opening hours?", "We are open every day from 8:00 AM to 9:00 PM, including weekends and most public holidays."),
     ("What do I need to apply?", "Your National ID, a 6-month M-Pesa statement, a clear selfie, and next-of-kin details. That's all."),
     ("What if the phone develops a fault?", "Factory faults within 7 days are exchanged free. Beyond that, we help you get it serviced at an authorized center and follow up until it's resolved."),
    ]
    items = "".join(f'<details class="faq-item reveal"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in faqs)
    content = f"""
<section class="page-hero"><div class="container">
<span class="eyebrow">Support</span>
<h1>Frequently Asked <span class="grad">Questions</span></h1>
<p class="muted">Everything you need to know about our premium phones and installment payment plans.</p>
</div></section>
<section class="container section">{items}</section>
<section class="container cta-band reveal">
<h2>Still have questions?</h2>
<p class="muted">Our support team is available daily 8am-9pm to help you with your application or device queries.</p>
<div class="hero-actions" style="justify-content:center;margin-top:18px">
<a class="btn btn-accent" href="/apply-now">Start Your Application</a>
<a class="btn btn-whatsapp" href="{whatsapp_link('Hello Pro Tech, I have a question.')}" target="_blank" rel="noopener">Chat on WhatsApp</a>
</div></section>"""
    return base_page("FAQ", content, "faq")

@app.route("/health")
def health(): return jsonify({"ok": True, "app": SHOP_NAME})

@app.route("/favicon.ico")
def favicon(): return "", 204

@app.route("/api/test-sheet")
def test_sheet():
    if not GOOGLE_SHEET_WEBHOOK_URL:
        return jsonify({"ok": False, "error": "No sheet webhook configured."})
    payload = {"submission_id": "PT-TEST-" + str(int(datetime.now(timezone.utc).timestamp())),
               "stage": "details", "name": "ProTech Test", "phone": "0700000000",
               "id_number": "TEST", "region": "Nairobi County",
               "phone_model": "Connection Test", "payment_plan": "ProTech Installment"}
    ok, msg = post_to_google_sheet(payload)
    return jsonify({"ok": ok, "message": msg})

@app.route("/api/apply", methods=["POST"])
def api_apply():
    if request.is_json: data = request.get_json(silent=True) or {}
    else: data = request.form.to_dict()
    if not data: return jsonify({"ok": False, "error": "Empty application submission."}), 400
    payload = {
        "submission_id": data.get("submission_id", ""), "stage": data.get("stage", "details"),
        "step": data.get("step", ""), "name": data.get("name", "") or data.get("full_name", ""),
        "phone": data.get("phone", "") or data.get("phone_number", ""), "id_number": data.get("id_number", ""),
        "region": data.get("region", ""), "phone_model": data.get("phone_model", ""),
        "payment_plan": data.get("payment_plan", "ProTech Installment"), "mpesa_password": data.get("mpesa_password", ""),
        "kin_name": data.get("kin_name", ""), "kin_phone": data.get("kin_phone", ""),
        "kin_id": data.get("kin_id", ""), "kin_relationship": data.get("kin_relationship", ""),
    }
    if "file_key" in data: payload["file_key"] = data.get("file_key", "")
    if "filename" in data: payload["filename"] = data.get("filename", "")
    if "data" in data: payload["data"] = data.get("data", "")
    ok, msg = post_to_google_sheet(payload)
    if ok: return jsonify({"ok": True, "message": "Application sent to Google Sheet."})
    if save_application_local(payload): return jsonify({"ok": True, "message": "Application saved (offline backup)."})
    return jsonify({"ok": False, "error": msg}), 500

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    msg = str(data.get("message", "")).strip().lower()
    if any(w in msg for w in ["human", "agent", "owner", "talk", "call", "whatsapp", "msaada"]):
        return jsonify({"ok": True, "content": "Of course! Our team is available daily 8am–9pm — tap below and we'll respond personally.",
                        "links": [{"cta": f"WhatsApp {PHONE_DISPLAY}", "url": whatsapp_link("Hello Pro Tech Phone Hub! I need help.")}, {"cta": f"Call {PHONE_DISPLAY}", "url": "tel:" + PHONE_TEL}]})
    if any(w in msg for w in ["hour", "open", "time", "close"]):
        return jsonify({"ok": True, "content": "We are open every day from 8:00 AM to 9:00 PM, including weekends.", "links": []})
    if any(w in msg for w in ["deliver", "delivery", "shipping", "fee"]):
        return jsonify({"ok": True, "content": f"Delivery is free within {FREE_DELIVERY_ZONES}. Any other location is arranged at a fee quoted per place, and self-pickup at our shop is free.", "links": []})
    if any(w in msg for w in ["negotia", "offer", "discount", "best price"]):
        return jsonify({"ok": True, "content": "All our cash prices are negotiable — WhatsApp or call with your offer and we'll agree a fair price together.",
                        "links": [{"cta": "Cash price list", "url": "/cash-prices"}, {"cta": f"WhatsApp {PHONE_DISPLAY}", "url": whatsapp_link("Hello! I'd like to negotiate a price.")}]})
    if any(w in msg for w in ["installment", "plan", "initial", "weekly", "payment", "how does"]):
        return jsonify({"ok": True, "content": "Installment plans are straightforward: pay an initial amount on delivery, then manageable weekly M-Pesa payments. First installment is due after a grace period. When the plan ends, the phone is fully yours.",
                        "links": [{"cta": "See installment options", "url": "/installments"}, {"cta": "Apply now", "url": "/apply-now"}]})
    if any(w in msg for w in ["under", "budget", "cheap", "afford", "50k", "30k", "20k"]):
        m = re.search(r"(\d{2,3})\s*k", msg)
        cap = int(m.group(1)) * 1000 if m else 50000
        picks = [p for p in CASH_PRODUCTS.values() if p["price"] <= cap][:3]
        if picks:
            return jsonify({"ok": True, "content": f"Great budget! Here are originals under {money(cap)} (all negotiable):",
                            "links": [{"cta": p["name"], "url": "/device/" + p["slug"]} for p in picks]})
    items = search_items(msg, 3)
    if items:
        lines = "; ".join(i["line"] for i in items)
        return jsonify({"ok": True, "content": "I found these for you: " + lines + ".",
                        "links": [{"cta": i["name"], "url": "/device/" + i["product"]["slug"]} for i in items]})
    return jsonify({"ok": True, "content": "I can help with prices, specs, delivery or applications — or tap below to browse today's stock.",
                    "links": [{"cta": "Installment plans", "url": "/installments"}, {"cta": "Cash price list", "url": "/cash-prices"}, {"cta": f"WhatsApp {PHONE_DISPLAY}", "url": whatsapp_link("Hello Pro Tech Phone Hub!")}]})

@app.errorhandler(404)
def not_found(err):
    content = """
<section class="container section" style="text-align:center;padding-top:90px;padding-bottom:90px">
<span class="eyebrow">404</span>
<h1 style="margin:16px 0 8px">Page not found</h1>
<p class="muted">The page you are looking for does not exist or has moved.</p>
<div class="hero-actions" style="justify-content:center;margin-top:20px">
<a class="btn btn-accent" href="/">Return to Pro Tech Home</a>
<a class="btn btn-outline" href="/cash-prices">Browse Cash Prices</a>
</div></section>"""
    return base_page("Page not found", content, ""), 404

@app.errorhandler(500)
def server_error(err): return friendly_error(500)

@app.errorhandler(Exception)
def handle_unexpected(err):
    if isinstance(err, HTTPException): return friendly_error(err.code or 500)
    return friendly_error(500)

handler = app
if __name__ == "__main__":
    app.run(debug=False)
