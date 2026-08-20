import spacy
from spacy.matcher import PhraseMatcher

DISEASE_MAP = {
    "covid": "covid-19",
    "covid-19": "covid-19",
    "coronavirus": "covid-19",
    "flu": "influenza",
    "tb": "tuberculosis",
    "hiv": "hiv/aids",
    "aids": "hiv/aids",
    "hepatitis a": "hepatitis a",
    "hepatitis b": "hepatitis b",
    "hepatitis c": "hepatitis c",
    # Keep base "hepatitis" so it normalizes to itself
}

DISEASE_KEYWORDS = [
    # COVID variants
    "cholera", "dengue", "malaria", "covid", "covid-19",
    "coronavirus", "ebola", "influenza", "flu",
    # TB / respiratory
    "tuberculosis", "tb",
    # Hepatitis — all three types explicitly listed
    "hepatitis", "hepatitis a", "hepatitis b", "hepatitis c",
    # Standard outbreak diseases
    "typhoid", "measles",
    "zika", "monkeypox", "mpox", "polio",
    # HIV
    "hiv", "aids",
    # NTDs
    "leprosy", "trachoma", "neglected tropical diseases", "ntd",
]

# ── These are used ONLY for the substring fallback scan ───────────────
# Includes hyphenated and compound forms that PhraseMatcher cannot handle.
FALLBACK_KEYWORDS = [
    "leprosy", "trachoma", "neglected tropical diseases", "ntd",
    "hepatitis a", "hepatitis b", "hepatitis c", "hepatitis",
    "hiv", "aids",
    "cholera", "dengue", "malaria", "covid", "coronavirus",
    "ebola", "influenza", "flu", "tuberculosis", "tb",
    "typhoid", "measles", "zika", "monkeypox", "mpox", "polio",
]

DISEASE_SYNONYMS = {
    "covid": "covid-19",
    "covid-19": "covid-19",
    "coronavirus": "covid-19",
}

_nlp = spacy.load("en_core_web_sm")
_matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
# Only add tokens that spaCy can reliably phrase-match (no compound/hyphenated forms here)
_matcher.add("DISEASES", [_nlp.make_doc(term) for term in DISEASE_KEYWORDS])


def _unique(values):
    unique_values = []
    seen = set()

    for value in values:
        if value not in seen:
            seen.add(value)
            unique_values.append(value)

    return unique_values


LOCATION_MAP = {
    # United States variants
    "U.S.": "United States",
    "USA": "United States",
    "US": "United States",
    "U.S.A.": "United States",
    "America": "United States",
    "the United States": "United States",
    "the US": "United States",
    "the USA": "United States",
    "WASHINGTON": "United States",
    # United Kingdom variants
    "UK": "United Kingdom",
    "U.K.": "United Kingdom",
    "Britain": "United Kingdom",
    "Great Britain": "United Kingdom",
    "the UK": "United Kingdom",
    "the United Kingdom": "United Kingdom",
    "England": "United Kingdom",
    # DR Congo variants
    "Congo": "DR Congo",
    "Democratic Republic": "DR Congo",
    "Democratic Republic of the Congo": "DR Congo",
    "DRC": "DR Congo",
    "D.R.C.": "DR Congo",
    # Korea
    "S. Korea": "South Korea",
    "N. Korea": "North Korea",
    "Republic of Korea": "South Korea",
    # Turkey
    "Türkiye": "Turkey",
    "Turkiye": "Turkey",
    # Vietnam
    "Viet Nam": "Vietnam",
    # Myanmar
    "Burma": "Myanmar",
    # Iran
    "Islamic Republic of Iran": "Iran",
    # Ivory Coast
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    # Tanzania
    "United Republic of Tanzania": "Tanzania",
    # Russia
    "Russian Federation": "Russia",
    # Czech Republic
    "Czechia": "Czech Republic",
    # Libya
    "State of Libya": "Libya",
    # Eswatini
    "Swaziland": "Eswatini",
}

# Known country names for text-scan fallback (populated from processor at import time)
# This is kept as a separate constant to avoid circular imports; these are the
# most common country names that spaCy's small model frequently misses.
_FALLBACK_COUNTRY_NAMES = [
    "India", "Nigeria", "Pakistan", "South Africa", "Yemen", "DR Congo",
    "United States", "United Kingdom", "China", "Japan", "Australia",
    "France", "Germany", "Italy", "Spain", "Brazil", "Mexico", "Canada",
    "Russia", "Indonesia", "Bangladesh", "Kenya", "Uganda", "Ethiopia",
    "Tanzania", "Afghanistan", "Iraq", "Egypt", "Saudi Arabia", "UAE",
    "South Korea", "Philippines", "Thailand", "Vietnam", "Myanmar",
    "Colombia", "Peru", "Argentina", "Chile", "Ghana", "Cameroon",
    "Mozambique", "Madagascar", "Sudan", "South Sudan", "Somalia",
    "Haiti", "Nepal", "Sri Lanka", "Syria", "Iran", "Turkey", "Poland",
    "Ukraine", "Zimbabwe", "Zambia", "Angola", "Mali", "Niger", "Chad",
    "Burkina Faso", "Senegal", "Guinea", "Sierra Leone", "Liberia",
    "Ivory Coast", "Libya", "Tunisia", "Algeria", "Morocco", "Rwanda",
    "Burundi", "Malawi", "Namibia", "Botswana", "Eritrea", "Djibouti",
    "Jordan", "Lebanon", "Israel", "Oman", "Kuwait", "Qatar",
    "Netherlands", "Belgium", "Austria", "Switzerland", "Portugal",
    "Sweden", "Norway", "Denmark", "Finland", "Ireland", "Greece",
    "Romania", "Czech Republic", "Hungary", "Serbia", "Croatia",
    "Bulgaria", "Moldova", "Albania", "Belarus", "Georgia", "Armenia",
    "Venezuela", "Ecuador", "Bolivia", "Paraguay", "Uruguay",
    "Cuba", "Dominican Republic", "Jamaica", "Panama", "Costa Rica",
    "Guatemala", "Honduras", "El Salvador", "Nicaragua",
    "New Zealand", "Papua New Guinea", "Fiji",
    "Malaysia", "Singapore", "Cambodia", "Laos", "Mongolia",
    "Gambia", "Central African Republic", "Gabon", "Togo", "Benin",
]


def extract_entities(text):
    if not text:
        return {"diseases": [], "locations": []}

    doc = _nlp(text)

    # ---- LOCATION EXTRACTION ----
    locations = set()

    for ent in doc.ents:
        if ent.label_ == "GPE":
            loc = ent.text.strip()

            if not loc:
                continue

            # normalize
            loc = LOCATION_MAP.get(loc, loc)

            locations.add(loc)

    # ---- FALLBACK: text-scan for known country names ─────────────
    # spaCy's small model often misses country names, especially in
    # WHO/CDC article text. Scan for known countries as a backup.
    text_lower = text.lower()
    for country_name in _FALLBACK_COUNTRY_NAMES:
        if country_name.lower() in text_lower:
            locations.add(country_name)

    # ---- DISEASE EXTRACTION via PhraseMatcher ----
    diseases = set()

    for _, start, end in _matcher(doc):
        disease = doc[start:end].text.strip().lower()

        # normalize using BOTH maps
        disease = DISEASE_MAP.get(disease, disease)

        diseases.add(disease)

    # ---- FALLBACK: direct substring scan of the raw text ─────────────
    # PhraseMatcher operates on spaCy token boundaries, so hyphenated
    # forms like "leprosy-free" or "dengue-endemic" won't match "leprosy"
    # or "dengue". A simple substring scan catches those missed cases.
    text_lower = text.lower()
    for kw in FALLBACK_KEYWORDS:
        # Use 'in' so "leprosy-free" and "leprosy" both hit on "leprosy"
        if kw in text_lower:
            normalized_kw = DISEASE_MAP.get(kw, kw)
            diseases.add(normalized_kw)

    return {
        "diseases": list(diseases),
        "locations": list(locations),
    }
