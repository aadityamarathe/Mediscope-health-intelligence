import random
import re
from datetime import datetime, timedelta, timezone

from ..database.mongo_connection import get_db
from ..nlp.ner import extract_entities
from ..nlp.relevance import is_relevant_article
from ..utils.severity import calculate_outbreak_severity


GENERIC_DISEASE_TERMS = {
    "unknown",
    "unknown disease",
    "unidentified disease",
    "infection",
    "virus",
    "outbreak",
    "epidemic",
    "pandemic",
    "fever",
    "respiratory illness",
    "diarrhea",
    "pneumonia",
}

# ── City / State → Country normalization ────────────────────────────
COUNTRY_FIX = {
    # United States cities / states
    "n.y.": "United States",
    "new york": "United States",
    "washington": "United States",
    "washington, d.c.": "United States",
    "washington d.c.": "United States",
    "d.c.": "United States",
    "west seneca": "United States",
    "california": "United States",
    "texas": "United States",
    "florida": "United States",
    "chicago": "United States",
    "los angeles": "United States",
    "boston": "United States",
    "seattle": "United States",
    "atlanta": "United States",
    "hawaii": "United States",
    "alaska": "United States",
    "colorado": "United States",
    "oregon": "United States",
    "ohio": "United States",
    "michigan": "United States",
    "pennsylvania": "United States",
    "virginia": "United States",
    "maryland": "United States",
    "georgia": "United States",
    "illinois": "United States",
    "minnesota": "United States",
    "wisconsin": "United States",
    "indiana": "United States",
    "iowa": "United States",
    "arizona": "United States",
    "massachusetts": "United States",
    "connecticut": "United States",
    "new jersey": "United States",
    "north carolina": "United States",
    "south carolina": "United States",
    "alabama": "United States",
    "louisiana": "United States",
    "tennessee": "United States",
    "kentucky": "United States",
    "missouri": "United States",
    "houston": "United States",
    "philadelphia": "United States",
    "phoenix": "United States",
    "san antonio": "United States",
    "san diego": "United States",
    "dallas": "United States",
    "san francisco": "United States",
    "denver": "United States",
    "mission": "United States",
    # United Kingdom cities
    "london": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "northern ireland": "United Kingdom",
    "manchester": "United Kingdom",
    "birmingham": "United Kingdom",
    "liverpool": "United Kingdom",
    "edinburgh": "United Kingdom",
    "glasgow": "United Kingdom",
    # India cities
    "mumbai": "India",
    "delhi": "India",
    "new delhi": "India",
    "chennai": "India",
    "kolkata": "India",
    "bangalore": "India",
    "hyderabad": "India",
    "pune": "India",
    "ahmedabad": "India",
    "jaipur": "India",
    # Pakistan
    "karachi": "Pakistan",
    "lahore": "Pakistan",
    "islamabad": "Pakistan",
    # Nigeria
    "lagos": "Nigeria",
    "abuja": "Nigeria",
    "kano": "Nigeria",
    # South Africa
    "cape town": "South Africa",
    "johannesburg": "South Africa",
    "durban": "South Africa",
    "pretoria": "South Africa",
    # China
    "beijing": "China",
    "shanghai": "China",
    "wuhan": "China",
    "guangzhou": "China",
    "shenzhen": "China",
    "hong kong": "China",
    # Japan
    "tokyo": "Japan",
    "osaka": "Japan",
    # Australia
    "sydney": "Australia",
    "melbourne": "Australia",
    "brisbane": "Australia",
    "perth": "Australia",
    # Europe
    "paris": "France",
    "marseille": "France",
    "lyon": "France",
    "berlin": "Germany",
    "munich": "Germany",
    "hamburg": "Germany",
    "rome": "Italy",
    "milan": "Italy",
    "madrid": "Spain",
    "barcelona": "Spain",
    "amsterdam": "Netherlands",
    "brussels": "Belgium",
    "vienna": "Austria",
    "zurich": "Switzerland",
    "geneva": "Switzerland",
    "lisbon": "Portugal",
    "stockholm": "Sweden",
    "oslo": "Norway",
    "copenhagen": "Denmark",
    "helsinki": "Finland",
    "dublin": "Ireland",
    "athens": "Greece",
    "bucharest": "Romania",
    "warsaw": "Poland",
    "prague": "Czech Republic",
    "budapest": "Hungary",
    "moscow": "Russia",
    "st. petersburg": "Russia",
    "saint petersburg": "Russia",
    "kyiv": "Ukraine",
    "kiev": "Ukraine",
    "istanbul": "Turkey",
    "ankara": "Turkey",
    # South America
    "sao paulo": "Brazil",
    "rio de janeiro": "Brazil",
    "brasilia": "Brazil",
    "buenos aires": "Argentina",
    "lima": "Peru",
    "bogota": "Colombia",
    "santiago": "Chile",
    "quito": "Ecuador",
    "caracas": "Venezuela",
    # Africa
    "kinshasa": "DR Congo",
    "nairobi": "Kenya",
    "kampala": "Uganda",
    "addis ababa": "Ethiopia",
    "dar es salaam": "Tanzania",
    "lusaka": "Zambia",
    "harare": "Zimbabwe",
    "luanda": "Angola",
    "maputo": "Mozambique",
    "accra": "Ghana",
    "dakar": "Senegal",
    "bamako": "Mali",
    "ouagadougou": "Burkina Faso",
    "niamey": "Niger",
    "conakry": "Guinea",
    "freetown": "Sierra Leone",
    "monrovia": "Liberia",
    "abidjan": "Ivory Coast",
    "antananarivo": "Madagascar",
    "khartoum": "Sudan",
    "mogadishu": "Somalia",
    "douala": "Cameroon",
    "yaounde": "Cameroon",
    "brazzaville": "Republic of the Congo",
    "tripoli": "Libya",
    "tunis": "Tunisia",
    "algiers": "Algeria",
    "casablanca": "Morocco",
    "rabat": "Morocco",
    # Middle East
    "dhaka": "Bangladesh",
    "kabul": "Afghanistan",
    "baghdad": "Iraq",
    "cairo": "Egypt",
    "sanaa": "Yemen",
    "aden": "Yemen",
    "tehran": "Iran",
    "riyadh": "Saudi Arabia",
    "dubai": "UAE",
    "doha": "Qatar",
    "beirut": "Lebanon",
    "amman": "Jordan",
    "damascus": "Syria",
    # Southeast Asia
    "bangkok": "Thailand",
    "hanoi": "Vietnam",
    "ho chi minh city": "Vietnam",
    "manila": "Philippines",
    "jakarta": "Indonesia",
    "kuala lumpur": "Malaysia",
    "singapore": "Singapore",
    "phnom penh": "Cambodia",
    "yangon": "Myanmar",
    "vientiane": "Laos",
    "kathmandu": "Nepal",
    "colombo": "Sri Lanka",
    # Central America / Caribbean
    "mexico city": "Mexico",
    "port-au-prince": "Haiti",
    "havana": "Cuba",
    "panama city": "Panama",
    "san jose": "Costa Rica",
    "kingston": "Jamaica",
}

COMMON_LOCATIONS = {
    "new york": "United States",
    "london": "United Kingdom",
    "delhi": "India",
}

COUNTRY_ALIASES = {
    # DR Congo
    "democratic republic of the congo": "DR Congo",
    "democratic republic of congo": "DR Congo",
    "democratic republic": "DR Congo",
    "congo": "DR Congo",
    "drc": "DR Congo",
    "d.r.c.": "DR Congo",
    "the democratic republic of the congo": "DR Congo",
    "congo (the democratic republic of the)": "DR Congo",
    "congo, democratic republic of the": "DR Congo",
    # Republic of Congo (separate country)
    "republic of the congo": "Republic of the Congo",
    "congo-brazzaville": "Republic of the Congo",
    # United States
    "u.s.": "United States",
    "us": "United States",
    "usa": "United States",
    "u.s.a.": "United States",
    "united states of america": "United States",
    "the united states": "United States",
    "the united states of america": "United States",
    "the us": "United States",
    "the usa": "United States",
    "america": "United States",
    # United Kingdom
    "u.k.": "United Kingdom",
    "uk": "United Kingdom",
    "britain": "United Kingdom",
    "great britain": "United Kingdom",
    "the united kingdom": "United Kingdom",
    "the uk": "United Kingdom",
    "united kingdom of great britain and northern ireland": "United Kingdom",
    # Korea
    "south korea": "South Korea",
    "republic of korea": "South Korea",
    "korea (the republic of)": "South Korea",
    "korea, republic of": "South Korea",
    "the republic of korea": "South Korea",
    "north korea": "North Korea",
    "democratic people's republic of korea": "North Korea",
    "korea (the democratic people's republic of)": "North Korea",
    # UAE
    "uae": "UAE",
    "united arab emirates": "UAE",
    "the united arab emirates": "UAE",
    # Saudi Arabia
    "saudi": "Saudi Arabia",
    "ksa": "Saudi Arabia",
    # Tanzania
    "united republic of tanzania": "Tanzania",
    "the united republic of tanzania": "Tanzania",
    "tanzania, united republic of": "Tanzania",
    "tanzania (united republic of)": "Tanzania",
    # Iran
    "islamic republic of iran": "Iran",
    "iran (islamic republic of)": "Iran",
    "iran, islamic republic of": "Iran",
    "the islamic republic of iran": "Iran",
    # Syria
    "syrian arab republic": "Syria",
    "syria": "Syria",
    # Venezuela
    "venezuela (bolivarian republic of)": "Venezuela",
    "bolivarian republic of venezuela": "Venezuela",
    # Bolivia
    "bolivia (plurinational state of)": "Bolivia",
    "plurinational state of bolivia": "Bolivia",
    # Ivory Coast
    "côte d'ivoire": "Ivory Coast",
    "cote d'ivoire": "Ivory Coast",
    "cote divoire": "Ivory Coast",
    "the ivory coast": "Ivory Coast",
    # Turkey
    "türkiye": "Turkey",
    "turkiye": "Turkey",
    "republic of turkey": "Turkey",
    "republic of türkiye": "Turkey",
    # Vietnam
    "viet nam": "Vietnam",
    # Myanmar
    "burma": "Myanmar",
    # Laos
    "lao people's democratic republic": "Laos",
    "lao pdr": "Laos",
    "laos": "Laos",
    # Czech Republic
    "czechia": "Czech Republic",
    # Moldova
    "republic of moldova": "Moldova",
    "moldova (republic of)": "Moldova",
    # Russia
    "russian federation": "Russia",
    "the russian federation": "Russia",
    # Egypt
    "the arab republic of egypt": "Egypt",
    # Libya
    "state of libya": "Libya",
    # Sudan
    "the sudan": "Sudan",
    "republic of the sudan": "Sudan",
    "south sudan": "South Sudan",
    "republic of south sudan": "South Sudan",
    # Ethiopia
    "federal democratic republic of ethiopia": "Ethiopia",
    # Nigeria
    "federal republic of nigeria": "Nigeria",
    # Philippines
    "the philippines": "Philippines",
    # Netherlands
    "the netherlands": "Netherlands",
    "holland": "Netherlands",
    # Eswatini / Swaziland
    "eswatini": "Eswatini",
    "swaziland": "Eswatini",
    # Timor-Leste
    "east timor": "Timor-Leste",
    "timor leste": "Timor-Leste",
    # Micronesia
    "federated states of micronesia": "Micronesia",
    # Cape Verde
    "cabo verde": "Cape Verde",
    # Various "the" prefixed
    "the gambia": "Gambia",
    "the bahamas": "Bahamas",
    "the comoros": "Comoros",
    "the maldives": "Maldives",
    "the seychelles": "Seychelles",
    "the marshall islands": "Marshall Islands",
    "the solomon islands": "Solomon Islands",
    # Sub-Saharan region names
    "saharan africa": None,  # Not a country — will be skipped
    "sub-saharan africa": None,
    "west africa": None,
    "east africa": None,
    "central africa": None,
    "southern africa": None,
    "southeast asia": None,
    "south asia": None,
    "middle east": None,
    "latin america": None,
    "central america": None,
    "north america": None,
    "european union": None,
    "european region": None,
}

# ── Comprehensive country coordinates ──────────────────────────────
COUNTRY_COORDS = {
    # Asia
    "India": (20.5937, 78.9629),
    "Pakistan": (30.3753, 69.3451),
    "Bangladesh": (23.6850, 90.3563),
    "Nepal": (28.3949, 84.1240),
    "Sri Lanka": (7.8731, 80.7718),
    "Afghanistan": (33.9391, 67.7100),
    "China": (35.8617, 104.1954),
    "Japan": (36.2048, 138.2529),
    "South Korea": (35.9078, 127.7669),
    "North Korea": (40.3399, 127.5101),
    "Philippines": (12.8797, 121.7740),
    "Thailand": (15.8700, 100.9925),
    "Vietnam": (14.0583, 108.2772),
    "Myanmar": (21.9162, 95.9560),
    "Indonesia": (-0.7893, 113.9213),
    "Malaysia": (4.2105, 101.9758),
    "Singapore": (1.3521, 103.8198),
    "Cambodia": (12.5657, 104.9910),
    "Laos": (19.8563, 102.4955),
    "Mongolia": (46.8625, 103.8467),
    "Taiwan": (23.6978, 120.9605),
    "Timor-Leste": (-8.8742, 125.7275),
    # Middle East
    "Iraq": (33.2232, 43.6793),
    "Iran": (32.4279, 53.6880),
    "Saudi Arabia": (23.8859, 45.0792),
    "UAE": (23.4241, 53.8478),
    "Yemen": (15.5527, 48.5164),
    "Syria": (34.8021, 38.9968),
    "Turkey": (38.9637, 35.2433),
    "Jordan": (30.5852, 36.2384),
    "Lebanon": (33.8547, 35.8623),
    "Israel": (31.0461, 34.8516),
    "Palestine": (31.9522, 35.2332),
    "Oman": (21.4735, 55.9754),
    "Kuwait": (29.3117, 47.4818),
    "Qatar": (25.3548, 51.1839),
    "Bahrain": (26.0667, 50.5577),
    # Europe
    "United Kingdom": (55.3781, -3.4360),
    "France": (46.2276, 2.2137),
    "Germany": (51.1657, 10.4515),
    "Italy": (41.8719, 12.5674),
    "Spain": (40.4637, -3.7492),
    "Poland": (51.9194, 19.1451),
    "Ukraine": (48.3794, 31.1656),
    "Russia": (61.5240, 105.3188),
    "Netherlands": (52.1326, 5.2913),
    "Belgium": (50.5039, 4.4699),
    "Austria": (47.5162, 14.5501),
    "Switzerland": (46.8182, 8.2275),
    "Portugal": (39.3999, -8.2245),
    "Sweden": (60.1282, 18.6435),
    "Norway": (60.4720, 8.4689),
    "Denmark": (56.2639, 9.5018),
    "Finland": (61.9241, 25.7482),
    "Ireland": (53.1424, -7.6921),
    "Greece": (39.0742, 21.8243),
    "Romania": (45.9432, 24.9668),
    "Czech Republic": (49.8175, 15.4730),
    "Hungary": (47.1625, 19.5033),
    "Serbia": (44.0165, 21.0059),
    "Croatia": (45.1000, 15.2000),
    "Bulgaria": (42.7339, 25.4858),
    "Slovakia": (48.6690, 19.6990),
    "Lithuania": (55.1694, 23.8813),
    "Latvia": (56.8796, 24.6032),
    "Estonia": (58.5953, 25.0136),
    "Slovenia": (46.1512, 14.9955),
    "Moldova": (47.4116, 28.3699),
    "Albania": (41.1533, 20.1683),
    "North Macedonia": (41.5124, 20.9631),
    "Bosnia and Herzegovina": (43.9159, 17.6791),
    "Montenegro": (42.7087, 19.3744),
    "Kosovo": (42.6026, 20.9030),
    "Belarus": (53.7098, 27.9534),
    "Georgia": (42.3154, 43.3569),
    "Armenia": (40.0691, 45.0382),
    "Azerbaijan": (40.1431, 47.5769),
    "Cyprus": (35.1264, 33.4299),
    "Malta": (35.9375, 14.3754),
    "Iceland": (64.9631, -19.0208),
    "Luxembourg": (49.8153, 6.1296),
    # Americas
    "United States": (39.8283, -98.5795),
    "Canada": (56.1304, -106.3468),
    "Mexico": (23.6345, -102.5528),
    "Brazil": (-14.2350, -51.9253),
    "Colombia": (4.5709, -74.2973),
    "Peru": (-9.1900, -75.0152),
    "Argentina": (-38.4161, -63.6167),
    "Chile": (-35.6751, -71.5430),
    "Venezuela": (6.4238, -66.5897),
    "Ecuador": (-1.8312, -78.1834),
    "Bolivia": (-16.2902, -63.5887),
    "Paraguay": (-23.4425, -58.4438),
    "Uruguay": (-32.5228, -55.7658),
    "Guyana": (4.8604, -58.9302),
    "Suriname": (3.9193, -56.0278),
    "Haiti": (18.9712, -72.2852),
    "Cuba": (21.5218, -77.7812),
    "Dominican Republic": (18.7357, -70.1627),
    "Jamaica": (18.1096, -77.2975),
    "Panama": (8.5380, -80.7821),
    "Costa Rica": (9.7489, -83.7534),
    "Guatemala": (15.7835, -90.2308),
    "Honduras": (15.2000, -86.2419),
    "El Salvador": (13.7942, -88.8965),
    "Nicaragua": (12.8654, -85.2072),
    "Trinidad and Tobago": (10.6918, -61.2225),
    # Africa
    "Nigeria": (9.0820, 8.6753),
    "South Africa": (-30.5595, 22.9375),
    "DR Congo": (-4.0383, 21.7587),
    "Republic of the Congo": (-0.2280, 15.8277),
    "Kenya": (-0.0236, 37.9062),
    "Uganda": (1.3733, 32.2903),
    "Ethiopia": (9.1450, 40.4897),
    "Tanzania": (-6.3690, 34.8888),
    "Egypt": (26.8206, 30.8025),
    "Ghana": (7.9465, -1.0232),
    "Cameroon": (7.3697, 12.3547),
    "Mozambique": (-18.6657, 35.5296),
    "Madagascar": (-18.7669, 46.8691),
    "Sudan": (12.8628, 30.2176),
    "South Sudan": (6.877, 31.307),
    "Somalia": (5.1521, 46.1996),
    "Zimbabwe": (-19.0154, 29.1549),
    "Zambia": (-13.1339, 27.8493),
    "Angola": (-11.2027, 17.8739),
    "Mali": (17.5707, -3.9962),
    "Niger": (17.6078, 8.0817),
    "Chad": (15.4542, 18.7322),
    "Burkina Faso": (12.2383, -1.5616),
    "Senegal": (14.4974, -14.4524),
    "Guinea": (9.9456, -9.6966),
    "Guinea-Bissau": (11.8037, -15.1804),
    "Sierra Leone": (8.4606, -11.7799),
    "Liberia": (6.4281, -9.4295),
    "Ivory Coast": (7.5400, -5.5471),
    "Togo": (8.6195, 0.8248),
    "Benin": (9.3077, 2.3158),
    "Eritrea": (15.1794, 39.7823),
    "Djibouti": (11.8251, 42.5903),
    "Rwanda": (-1.9403, 29.8739),
    "Burundi": (-3.3731, 29.9189),
    "Malawi": (-13.2543, 34.3015),
    "Namibia": (-22.9576, 18.4904),
    "Botswana": (-22.3285, 24.6849),
    "Eswatini": (-26.5225, 31.4659),
    "Lesotho": (-29.6100, 28.2336),
    "Mauritania": (21.0079, -10.9408),
    "Libya": (26.3351, 17.2283),
    "Tunisia": (33.8869, 9.5375),
    "Algeria": (28.0339, 1.6596),
    "Morocco": (31.7917, -7.0926),
    "Gambia": (13.4432, -15.3101),
    "Central African Republic": (6.6111, 20.9394),
    "Equatorial Guinea": (1.6508, 10.2679),
    "Gabon": (-0.8037, 11.6094),
    "Comoros": (-11.6455, 43.3333),
    "Mauritius": (-20.3484, 57.5522),
    "Seychelles": (-4.6796, 55.4920),
    "Cape Verde": (16.5388, -23.0418),
    "São Tomé and Príncipe": (0.1864, 6.6131),
    # Oceania
    "Australia": (-25.2744, 133.7751),
    "New Zealand": (-40.9006, 174.8860),
    "Papua New Guinea": (-6.3150, 143.9555),
    "Fiji": (-17.7134, 178.0650),
    "Samoa": (-13.7590, -172.1046),
    "Tonga": (-21.1790, -175.1982),
    "Solomon Islands": (-9.6457, 160.1562),
    "Vanuatu": (-15.3767, 166.9592),
    "Micronesia": (7.4256, 150.5508),
    "Marshall Islands": (7.1315, 171.1845),
    "Palau": (7.5150, 134.5825),
    # Caribbean / Small states
    "Bahamas": (25.0343, -77.3963),
    "Barbados": (13.1939, -59.5432),
    "Maldives": (3.2028, 73.2207),
    "Brunei": (4.5353, 114.7277),
    "Bhutan": (27.5142, 90.4336),
}

# ── Known country names for fallback text matching ─────────────────
KNOWN_COUNTRIES = set(COUNTRY_COORDS.keys())

DISEASE_NAME_MAPPING = {
    "covid": "COVID-19",
    "covid 19": "COVID-19",
    "covid-19": "COVID-19",
    "coronavirus": "COVID-19",
    "sars-cov-2": "COVID-19",
    "flu": "Influenza",
    "tb": "Tuberculosis",
    "mpox": "Monkeypox",
}

DISEASE_DISPLAY_NAMES = {
    "cholera": "Cholera",
    "dengue": "Dengue",
    "malaria": "Malaria",
    "tuberculosis": "Tuberculosis",
    "covid-19": "COVID-19",
    "influenza": "Influenza",
    "hepatitis": "Hepatitis",
    "hepatitis a": "Hepatitis A",
    "hepatitis b": "Hepatitis B",
    "hepatitis c": "Hepatitis C",
    "typhoid": "Typhoid",
    "measles": "Measles",
    "monkeypox": "Monkeypox",
    "zika": "Zika",
    "polio": "Polio",
    "ebola": "Ebola",
    "yellow fever": "Yellow Fever",
    "plague": "Plague",
    "anthrax": "Anthrax",
    "rabies": "Rabies",
    "hiv": "HIV/AIDS",
    "hiv/aids": "HIV/AIDS",
    "lassa fever": "Lassa Fever",
    "marburg": "Marburg",
    "nipah": "Nipah",
    "chikungunya": "Chikungunya",
    "whooping cough": "Whooping Cough",
    "pertussis": "Whooping Cough",
    "diphtheria": "Diphtheria",
    "meningitis": "Meningitis",
    "leprosy": "Leprosy",
}

VALID_DISEASES = {
    "Dengue",
    "Cholera",
    "Malaria",
    "Tuberculosis",
    "COVID-19",
    "Influenza",
    "Hepatitis",
    "Hepatitis A",
    "Hepatitis B",
    "Hepatitis C",
    "Typhoid",
    "Measles",
    "Monkeypox",
    "HIV/AIDS",
    "Leprosy",
    "Yellow Fever",
    "Plague",
    "Anthrax",
    "Rabies",
    "Lassa Fever",
    "Marburg",
    "Nipah",
    "Chikungunya",
    "Whooping Cough",
    "Diphtheria",
    "Meningitis",
    "Zika",
    "Polio",
    "Ebola",
}

DISEASE_LIST = {disease.lower() for disease in VALID_DISEASES}
COUNTRY_LIST = {country.lower() for country in COUNTRY_COORDS}

CASE_PATTERNS = [
    re.compile(
        r"\b(\d{1,3}(?:,\d{3})+|\d+)\s*(cases?|deaths?|infected|infections?|patients?|confirmed|reported)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(\d+(?:\.\d+)?)\s*k\s*(cases?|deaths?|infected|infections?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(millions?|thousands?)\s+of\s+(cases?|deaths?|people)\b",
        re.IGNORECASE,
    ),
]


# ── Extraction helpers ─────────────────────────────────────────────

def extract_case_count(text):
    numbers = []
    text = text or ""

    matches = re.findall(r"\d{1,3}(?:,\d{3})+", text)
    for m in matches:
        try:
            numbers.append(int(m.replace(",", "")))
        except Exception:
            continue

    matches2 = re.findall(r"(\d+)\s+cases", text, re.IGNORECASE)
    for m in matches2:
        try:
            numbers.append(int(m))
        except Exception:
            continue

    if numbers:
        return max(numbers)

    return None


def _build_analysis_text(article):
    title = article.get("title") or ""
    content = article.get("content") or ""
    return f"{title} {content}".strip()


# ── Disease helpers ────────────────────────────────────────────────

def _normalize_disease_name(disease):
    cleaned = (disease or "").strip().lower()
    if not cleaned or cleaned in GENERIC_DISEASE_TERMS:
        return None

    if cleaned in DISEASE_NAME_MAPPING:
        return DISEASE_NAME_MAPPING[cleaned]

    return DISEASE_DISPLAY_NAMES.get(cleaned, cleaned.title())


def _pick_primary_disease(analysis_text, disease_candidates, known_diseases):
    text_lower = analysis_text.lower()
    matched = []

    # 1) Check NER candidates against known diseases
    for disease in disease_candidates:
        normalized = _normalize_disease_name(disease)
        if not normalized:
            continue

        comparable = normalized.lower().replace("-", " ")
        if comparable in known_diseases or normalized.lower() in known_diseases:
            index = text_lower.find(disease.lower())
            if index == -1:
                index = text_lower.find(comparable)
            matched.append((index if index != -1 else 10**9, normalized))

    # 2) Check disease aliases in text
    for alias, normalized in DISEASE_NAME_MAPPING.items():
        index = text_lower.find(alias)
        if index != -1:
            matched.append((index, normalized))

    # 3) Check known disease names directly in text
    for disease in known_diseases:
        index = text_lower.find(disease)
        if index != -1:
            matched.append((index, DISEASE_DISPLAY_NAMES.get(disease, disease.title())))

    # 4) Check display-name keys directly in text (broader scan)
    for key, display in DISEASE_DISPLAY_NAMES.items():
        index = text_lower.find(key)
        if index != -1:
            matched.append((index, display))

    if not matched:
        return None

    matched.sort(key=lambda item: item[0])
    return matched[0][1]


def _detect_disease_from_text(text):
    text_lower = (text or "").lower()
    matched = []

    for disease in VALID_DISEASES:
        index = text_lower.find(disease.lower())
        if index != -1:
            matched.append((index, disease))

    for alias, normalized in DISEASE_NAME_MAPPING.items():
        if normalized not in VALID_DISEASES:
            continue
        index = text_lower.find(alias)
        if index != -1:
            matched.append((index, normalized))

    if not matched:
        return None

    matched.sort(key=lambda item: item[0])
    return matched[0][1]


# ── Country helpers ────────────────────────────────────────────────

# Regex to extract country from "in [Country]" phrases
_IN_COUNTRY_RE = re.compile(
    r"\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})",
)

# Regex to extract country from WHO DON-style titles:
#   "Disease outbreak news – Country"
#   "outbreak in Country"
_WHO_TITLE_RE = re.compile(
    r"(?:"
    r"disease\s+outbreak\s+news\s*[-–—]\s*(.+?)$"
    r"|"
    r"outbreak\s+(?:of\s+\w+\s+)?in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})"
    r")",
    re.IGNORECASE | re.MULTILINE,
)


def _normalize_country(raw):
    """Normalize a raw location string to a known country name, or return None."""
    cleaned = (raw or "").strip()
    if not cleaned:
        return None

    lower = cleaned.lower()

    # 1) Direct match against known country names
    for country in COUNTRY_COORDS:
        if lower == country.lower():
            return country

    # 2) Alias → canonical
    canonical = COUNTRY_ALIASES.get(lower)
    if canonical is not None:
        # None means it's a region name, not a country — skip
        if canonical in COUNTRY_COORDS:
            return canonical
        return None

    # 3) City / state → country (COUNTRY_FIX)
    fix = COUNTRY_FIX.get(lower)
    if fix and fix in COUNTRY_COORDS:
        return fix

    # 4) Strip leading "the " and retry
    if lower.startswith("the "):
        stripped = lower[4:]
        for country in COUNTRY_COORDS:
            if stripped == country.lower():
                return country
        canonical = COUNTRY_ALIASES.get(stripped)
        if canonical and canonical in COUNTRY_COORDS:
            return canonical

    # 5) Strip "Republic of" prefix and retry
    for prefix in ("republic of ", "the republic of ", "people's republic of ",
                   "federal republic of ", "islamic republic of "):
        if lower.startswith(prefix):
            remainder = lower[len(prefix):]
            for country in COUNTRY_COORDS:
                if remainder == country.lower():
                    return country

    return None


def _pick_primary_country(analysis_text, location_candidates):
    """Return the best-matching country name, or None."""
    text_lower = analysis_text.lower()
    matched = []

    # 1) Check NER location candidates
    for location in location_candidates:
        country = _normalize_country(location)
        if not country:
            continue
        index = text_lower.find(location.lower())
        if index == -1:
            index = text_lower.find(country.lower())
        matched.append((index if index != -1 else 10**9, country))

    # 2) Direct scan for known country names in text
    for country in COUNTRY_COORDS:
        index = text_lower.find(country.lower())
        if index != -1:
            matched.append((index, country))

    # 3) Check city/state names in text → map to country
    for city, country in COUNTRY_FIX.items():
        index = text_lower.find(city.lower())
        if index != -1 and country in COUNTRY_COORDS:
            matched.append((index, country))

    for location, country in COMMON_LOCATIONS.items():
        index = text_lower.find(location.lower())
        if index != -1 and country in COUNTRY_COORDS:
            matched.append((index, country))

    # 4) Check aliases in text
    for alias, country in COUNTRY_ALIASES.items():
        if country is None:
            continue  # skip region names
        index = text_lower.find(alias)
        if index != -1 and country in COUNTRY_COORDS:
            matched.append((index, country))

    # 5) WHO title pattern extraction
    who_match = _WHO_TITLE_RE.search(analysis_text)
    if who_match:
        candidate = (who_match.group(1) or who_match.group(2) or "").strip()
        if candidate:
            country = _normalize_country(candidate)
            if country:
                matched.append((0, country))  # title → highest priority

    # 6) "in [Country]" regex fallback
    for m in _IN_COUNTRY_RE.finditer(analysis_text):
        candidate = m.group(1).strip()
        country = _normalize_country(candidate)
        if country:
            matched.append((m.start(), country))

    if not matched:
        return None

    matched.sort(key=lambda item: item[0])
    _, country = matched[0]
    if country not in COUNTRY_COORDS:
        return None
    return country


# ── DB helpers ─────────────────────────────────────────────────────

def _update_article_status(db, article_id, relevance, diseases_found, locations_found):
    db["raw_articles"].update_one(
        {"_id": article_id},
        {
            "$set": {
                "processed": True,
                "is_relevant": relevance["is_relevant"],
                "diseases_found": diseases_found,
                "locations_found": locations_found,
                "confidence": relevance["confidence"],
            }
        },
    )


# ── Main pipeline ──────────────────────────────────────────────────

def process_articles():
    db = get_db()
    known_diseases = {
        item["name"].strip().lower()
        for item in db["diseases"].find({}, {"_id": 0, "name": 1})
        if item.get("name")
    }

    processed_count = 0
    relevant_count = 0
    inserted_count = 0
    skipped_invalid = 0
    skipped_duplicate = 0
    inserted_records = []
    processed_diseases = set()

    for article in db["raw_articles"].find({"$or": [{"processed": False}, {"processed": {"$exists": False}}]}):
        analysis_text = _build_analysis_text(article)
        entities = extract_entities(analysis_text)
        relevance = is_relevant_article(analysis_text)

        diseases_found = entities["diseases"]
        locations_found = entities["locations"]

        _update_article_status(
            db=db,
            article_id=article["_id"],
            relevance=relevance,
            diseases_found=diseases_found,
            locations_found=locations_found,
        )

        processed_count += 1

        if not relevance["is_relevant"]:
            continue

        relevant_count += 1

        disease = _pick_primary_disease(analysis_text, diseases_found, known_diseases)
        if disease not in VALID_DISEASES:
            disease = None
        if disease is None:
            disease = _detect_disease_from_text(analysis_text)

        country = _pick_primary_country(analysis_text, locations_found)
        case_count = extract_case_count(analysis_text)
        lat = None
        lng = None

        if disease:
            disease = disease.lower().strip()
        if disease and disease in COUNTRY_LIST:
            disease = None

        if country:
            country = country.strip()
        if country and country.lower() in DISEASE_LIST:
            country = None

        if country:
            lat, lng = COUNTRY_COORDS.get(country, (None, None))

        print(f"  [EXTRACT] disease={disease!r}  country={country!r}  case_count={case_count}")

        if not disease:
            skipped_invalid += 1
            print(
                f"  -> skipped_invalid: disease={disease!r} "
                f"country={country!r} case_count={case_count}"
            )
            continue

        if not country:
            country = "unknown"

        case_count_estimated = False
        if not case_count:
            from ..pipeline.enricher import enrich_case_count
            case_count = enrich_case_count(disease, country)
            if case_count:
                print(f"  -> case_count_enriched from WHO GHO: {case_count}")
                case_count_source = "who_gho"
            else:
                case_count = 0
                case_count_estimated = True
                case_count_source = "missing"
                print(f"  -> case_count_missing: no WHO GHO data found")
        else:
            case_count_source = "extracted"

        source_url = article.get("url")
        
        raw_date = article.get("published_date") or article.get("pub_date") or article.get("crawled_at")
        outbreak_date = None
        if isinstance(raw_date, datetime):
            outbreak_date = raw_date
        elif isinstance(raw_date, str):
            try:
                outbreak_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            except ValueError:
                pass
        
        if not outbreak_date:
            print(f"  -> skipped_invalid: missing date for {disease} in {country}")
            skipped_invalid += 1
            continue

        # Normalize to timezone-aware (UTC) for consistent comparison
        if outbreak_date.tzinfo is None:
            outbreak_date = outbreak_date.replace(tzinfo=timezone.utc)

        severity = calculate_outbreak_severity(case_count)
        outbreak = {
            "disease": disease,
            "country": country,
            "lat": lat,
            "lng": lng,
            "case_count": case_count,
            "case_count_estimated": case_count_estimated,
            "case_count_source": case_count_source,
            "date": outbreak_date,
            "severity": severity,
            "source": article.get("source"),
            "source_url": source_url,
            "updated_at": datetime.utcnow(),
        }
        
        def get_source_rank(st):
            if not st: return 1
            st = str(st).lower().strip()
            if "disease.sh" in st or "disease_sh" in st: return 4
            if "gho" in st: return 3
            if "extracted" in st: return 2
            return 1

        def is_valid_coord(lt, lg):
            if lt is None or lg is None: return False
            try:
                lt, lg = float(lt), float(lg)
                return -90 <= lt <= 90 and -180 <= lg <= 180 and not (lt == 0.0 and lg == 0.0)
            except: return False

        existing = db["outbreaks_v2"].find_one({"disease": disease, "country": country})
        upserted_or_modified = False
        
        if existing:
            updates = {}
            
            # Date
            sim_date = existing.get("date")
            sim_date_aware = sim_date.replace(tzinfo=timezone.utc) if sim_date and sim_date.tzinfo is None else sim_date
            if outbreak_date and (not sim_date_aware or outbreak_date > sim_date_aware):
                if sim_date and sim_date.tzinfo is None:
                    updates["date"] = outbreak_date.replace(tzinfo=None)
                else:
                    updates["date"] = outbreak_date
            
            # Source & Case Count
            inc_rank = get_source_rank(case_count_source)
            sim_rank = get_source_rank(existing.get("case_count_source") or "missing")
            inc_cc = case_count if case_count is not None else -1
            sim_cc = existing.get("case_count") if existing.get("case_count") is not None else -1
            
            if inc_rank > sim_rank or (inc_rank == sim_rank and inc_cc > sim_cc):
                updates["case_count"] = case_count
                updates["case_count_estimated"] = case_count_estimated
                updates["case_count_source"] = case_count_source
                updates["source"] = article.get("source")
                updates["source_url"] = source_url
                updates["severity"] = severity
                
            # Coordinates
            if is_valid_coord(lat, lng) and not is_valid_coord(existing.get("lat"), existing.get("lng")):
                updates["lat"] = lat
                updates["lng"] = lng
                
            if updates:
                updates["updated_at"] = datetime.utcnow()
                db["outbreaks_v2"].update_one({"_id": existing["_id"]}, {"$set": updates})
                upserted_or_modified = True
                outbreak.update(updates)
        else:
            outbreak["created_at"] = datetime.utcnow()
            db["outbreaks_v2"].insert_one(outbreak)
            upserted_or_modified = True
        
        processed_diseases.add(disease)

        if upserted_or_modified:
            inserted_count += 1
            inserted_records.append(outbreak)
            print(f"UPSERTED V2: {disease} | {country} | {case_count}")
        else:
            skipped_duplicate += 1

    print("\n" + "=" * 55)
    print(f"  Total processed:          {processed_count}")
    print(f"  Relevant articles:        {relevant_count}")
    print(f"  Skipped (no usable data): {skipped_invalid}")
    print(f"  Skipped (duplicate):      {skipped_duplicate}")
    print(f"  Outbreaks inserted:       {inserted_count}")
    print("=" * 55)

    sample = inserted_records[:5]
    if sample:
        print("\n--- Sample inserted outbreaks ---")
        for i, rec in enumerate(sample, 1):
            print(
                f"  {i}. {rec['disease']} | {rec['country']} "
                f"| cases={rec['case_count']} | severity={rec['severity']}"
            )
    else:
        print("\n[WARNING] No outbreaks were inserted this run.")

    # ── Refresh last_updated on all processed disease records ─────
    if processed_diseases:
        now = datetime.utcnow()
        for d_name in processed_diseases:
            db["diseases"].update_one(
                {"name": {"$regex": f"^{d_name}$", "$options": "i"}},
                {"$set": {"last_updated": now}},
            )
        print(f"\n[INFO] Refreshed last_updated on {len(processed_diseases)} disease(s).")

    print("\n=== Disease Distribution ===")
    for disease_name in sorted(db["outbreaks_v2"].distinct("disease")):
        count = db["outbreaks_v2"].count_documents({"disease": disease_name})
        print(disease_name, count)

    return processed_count

if __name__ == "__main__":
    process_articles()
