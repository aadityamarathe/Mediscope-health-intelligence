import spacy
import re
from collections import Counter

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Layer 2: Alias dictionary
DISEASE_ALIASES = {
    "influenza": ["flu", "h1n1", "h3n2", "h5n1", "avian flu", "swine flu", "influenza a", "influenza b", "influenza"],
    "tuberculosis": ["tb", "tubercular", "mycobacterium tuberculosis", "consumption", "phthisis", "tuberculosis", "pulmonary tuberculosis"],
    "covid-19": ["covid", "sars-cov-2", "coronavirus", "covid 19", "ncov", "novel coronavirus", "covid-19", "corona virus"],
    "dengue": ["dengue fever", "breakbone fever", "dengue hemorrhagic fever", "dhf", "dengue", "dengue shock syndrome"],
    "malaria": ["plasmodium", "falciparum", "vivax", "plasmodium falciparum", "malaria", "plasmodium vivax", "quartan fever"],
    "cholera": ["vibrio cholerae", "asiatic cholera", "epidemic cholera", "cholera", "cholera infection"],
    "measles": ["rubeola", "morbillivirus", "measles virus", "measles", "english measles"],
    "ebola": ["ebola virus", "ebola hemorrhagic fever", "evd", "ebola virus disease", "ebola"],
    "mpox": ["monkeypox", "mpx", "mpxv", "monkeypox virus", "mpox", "monkey pox"],
    "hiv/aids": ["hiv", "aids", "human immunodeficiency virus", "acquired immunodeficiency syndrome", "hiv/aids", "hiv infection"],
    "hepatitis b": ["hbv", "hep b", "serum hepatitis", "hepatitis b virus", "hepatitis b", "hepb"],
    "leprosy": ["hansen's disease", "hansen disease", "mycobacterium leprae", "leprosy", "lepromatous leprosy"],
    "yellow fever": ["yellow jack", "yellow plague", "sylvatic yellow fever", "yellow fever", "urban yellow fever"],
    "plague": ["bubonic plague", "pneumonic plague", "septicemic plague", "yersinia pestis", "black death", "plague"],
    "rabies": ["hydrophobia", "lyssavirus", "rabies virus", "rabies", "rabies encephalomyelitis"],
    "typhoid": ["typhoid fever", "salmonella typhi", "enteric fever", "paratyphoid", "typhoid", "typhoid infection"],
    "zika": ["zika virus", "zikv", "zika fever", "zika", "zika virus disease"],
    "chikungunya": ["chikungunya virus", "chikv", "chikungunya fever", "chikungunya", "chikungunya infection"]
}

ALIAS_TO_CANONICAL = {}
for canonical, aliases in DISEASE_ALIASES.items():
    for alias in aliases:
        ALIAS_TO_CANONICAL[alias.lower()] = canonical

# Layer 1: EntityRuler setup
if not nlp.has_pipe("entity_ruler"):
    ruler = nlp.add_pipe("entity_ruler", before="ner", config={"phrase_matcher_attr": "LOWER"})
else:
    ruler = nlp.get_pipe("entity_ruler")

patterns = []
for alias in ALIAS_TO_CANONICAL.keys():
    patterns.append({"label": "DISEASE", "pattern": alias})
ruler.add_patterns(patterns)

# Layer 3: Regex fallback patterns
REGEX_PATTERNS = [
    r"\b(COVID-19|SARS-CoV-2)\b",
    r"\b(TB)\b",
    r"\b(HIV)\b",
    r"\b(HBV)\b",
    r"\b(H1N1|H3N2|H5N1)\b"
]

LOCATION_MAP = {
    "U.S.": "United States",
    "USA": "United States",
    "UK": "United Kingdom",
    "Congo": "Democratic Republic of the Congo",
    "Democratic Republic": "Democratic Republic of the Congo"
}

def extract_entities(text, article=None):
    """
    Extracts diseases and locations from text using a multi-layer strategy.
    Acts as a drop-in replacement by returning the expected format.
    """
    if not text:
        return {"diseases": [], "locations": [], "disease": None, "extraction_method": None}

    doc = nlp(text)
    
    # Extract locations using NER to maintain drop-in compatibility
    locations = set()
    for ent in doc.ents:
        if ent.label_ == "GPE":
            loc = ent.text.strip()
            if loc:
                loc = LOCATION_MAP.get(loc, loc)
                locations.add(loc)
    
    locations_list = list(locations)

    def get_most_frequent_disease(found_terms):
        canonical_counts = Counter()
        for term in found_terms:
            canonical = ALIAS_TO_CANONICAL.get(term.lower())
            if canonical:
                canonical_counts[canonical] += 1
        
        if canonical_counts:
            return canonical_counts.most_common(1)[0][0]
        return None

    # Layer 1: EntityRuler on full text
    ruler_matches = [ent.text for ent in doc.ents if ent.label_ == "DISEASE"]
    disease = get_most_frequent_disease(ruler_matches)
    if disease:
        return {
            "diseases": [disease],
            "locations": locations_list,
            "disease": disease,
            "extraction_method": "entity_ruler"
        }

    # Layer 3: Regex fallback on raw text
    regex_matches = []
    for pattern in REGEX_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        regex_matches.extend(matches)
        
    disease = get_most_frequent_disease(regex_matches)
    if disease:
        return {
            "diseases": [disease],
            "locations": locations_list,
            "disease": disease,
            "extraction_method": "regex"
        }

    # Layer 4: Title fallback
    title_text = ""
    if article and isinstance(article, dict) and article.get("title"):
        title_text = article["title"]
    
    if title_text:
        title_doc = nlp(title_text)
        title_ruler_matches = [ent.text for ent in title_doc.ents if ent.label_ == "DISEASE"]
        disease = get_most_frequent_disease(title_ruler_matches)
        if disease:
            return {
                "diseases": [disease],
                "locations": locations_list,
                "disease": disease,
                "extraction_method": "title_fallback"
            }
            
        title_regex_matches = []
        for pattern in REGEX_PATTERNS:
            matches = re.findall(pattern, title_text, re.IGNORECASE)
            title_regex_matches.extend(matches)
        disease = get_most_frequent_disease(title_regex_matches)
        if disease:
            return {
                "diseases": [disease],
                "locations": locations_list,
                "disease": disease,
                "extraction_method": "title_fallback"
            }

    return {
        "diseases": [],
        "locations": locations_list,
        "disease": None,
        "extraction_method": None
    }
