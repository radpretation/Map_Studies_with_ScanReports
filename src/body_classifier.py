import re

class BodyClassifier:
    # 1. Word boundaries (\b) added to short/ambiguous terms to prevent false positives
    brain_patterns = [
        r"brain", r"pons", r"cerebral", r"cerebell", 
        r"ventricles", r"intracranial", r"head", r"neuro", r"skull"
    ]
    
    chest_patterns = [
        r"chest", r"thorax", r"lung", r"pleural", 
        r"pneumothorax", r"mediast", r"cardiomediast"
    ]

    abdomen_patterns = [
        r"abdomen", r"abdo", r"\babd\b", r"\bkub\b", r"liver", 
        r"spleen", r"kidney", r"renal", r"pancreas", r"peritoneum"
    ]

    pelvis_patterns = [
        r"pelvis", r"pelvic", r"hip", r"bladder", 
        r"prostate", r"uterus", r"sacrum", r"iliac"
    ]

    spine_patterns = [
        r"spine", r"c-spine", r"t-spine", r"l-spine", 
        r"cervical", r"thoracic", r"lumbar", r"vertebra", r"sacral", r"coccyx"
    ]

    extremity_patterns = [
        r"\barm\b", r"\bleg\b", r"hand", r"foot", r"finger", r"toe", 
        r"femur", r"tibia", r"fibula", r"humerus", r"radius", 
        r"ulna", r"patella", r"knee", r"ankle", r"shoulder", 
        r"elbow", r"wrist", r"clavicle", r"scapula"
    ]

    # Pre-compile the regex patterns with IGNORECASE for high-performance processing
    BODY_PART_RE_MAP = {
        "HEAD": [re.compile(p, re.IGNORECASE) for p in brain_patterns], 
        "CHEST": [re.compile(p, re.IGNORECASE) for p in chest_patterns],
        "ABDOMEN": [re.compile(p, re.IGNORECASE) for p in abdomen_patterns],
        "PELVIS": [re.compile(p, re.IGNORECASE) for p in pelvis_patterns],
        "SPINE": [re.compile(p, re.IGNORECASE) for p in spine_patterns],
        "EXTREMITY": [re.compile(p, re.IGNORECASE) for p in extremity_patterns]
    }

    @staticmethod
    def get_body_part(description: str, full_text: str = "") -> str:
        """
        Scans the description (and falls back to full_text if needed) 
        to classify the anatomical region.
        """
        if not description or description == "UNKNOWN":
            search_text = full_text  # Fallback to scanning the whole document if heading failed
        else:
            search_text = description
            
        if not search_text:
            return "UNKNOWN"

        matched_regions = set()

        # Iterate through the mapping and search for matches
        for region, patterns in BodyClassifier.BODY_PART_RE_MAP.items():
            for pattern in patterns:
                if pattern.search(search_text):
                    matched_regions.add(region)
                    break # Stop checking patterns for this region once we have a match

        if not matched_regions:
            return "OTHER"
            
        # Return multiple regions as a joined string (e.g., "CHEST, ABDOMEN")
        return ", ".join(sorted(list(matched_regions)))