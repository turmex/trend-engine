"""
Trend Engine V2.0 — Configuration
=============================================
All constants, keyword taxonomies, and environment config.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════
# 7-DIMENSIONAL KEYWORD TAXONOMY
# ═══════════════════════════════════════════════════════════════════

KEYWORDS = {
    # DIMENSION 1: Anatomical region (where it hurts)
    "anatomical_region": {
        "spine_cervical": ["neck pain", "stiff neck"],
        "spine_thoracic": ["upper back pain"],
        "spine_lumbar": [
            "lower back pain", "sciatica", "herniated disc",
        ],
        "pelvis_hip": [
            "hip pain", "anterior pelvic tilt", "hip flexor pain",
        ],
        "shoulder": ["shoulder pain"],
        "extremity": ["knee pain", "plantar fasciitis", "carpal tunnel"],
        "head_jaw": ["tension headache", "forward head posture"],
    },

    # DIMENSION 2: Lifestyle cause (what triggers it)
    "lifestyle_cause": {
        "desk_work": [
            "working from home", "office ergonomics",
            "standing desk", "text neck",
        ],
        "commute_travel": ["driving back pain"],
        "occupational": ["work injury"],
        "athletic": ["squat form", "deadlift form"],
        "life_stage": ["aging posture"],
    },

    # DIMENSION 3: Diagnosed conditions
    "condition": [
        "fibromyalgia", "chronic pain syndrome",
        "degenerative disc disease", "piriformis syndrome",
        "thoracic outlet syndrome", "cancer pain",
    ],

    # DIMENSION 4: Treatment modality
    "treatment_modality": [
        "corrective exercise", "posture correction",
        "foam rolling", "mobility exercises",
    ],

    # DIMENSION 5: Yoga therapy (Bart's 10K+ yoga hours)
    "yoga_therapy": [
        "yoga for back pain", "yoga for sciatica",
        "therapeutic yoga", "yoga for chronic pain",
        "restorative yoga", "yin yoga for pain",
    ],

    # DIMENSION 6: Running recovery (Bart is an ultra marathoner)
    "running_recovery": [
        "runner's knee", "IT band syndrome",
        "achilles tendonitis", "plantar fasciitis running",
        "hip flexor running", "marathon recovery",
    ],

    # DIMENSION 7: Longevity & biohacking (Bart is a Longevity Coach)
    "longevity_biohacking": [
        "longevity exercises", "mobility for aging",
        "functional fitness over 40", "joint health",
        "movement longevity",
    ],

    # DIMENSION 8: Cancer exercise (Bart is ACSM-CET certified)
    "cancer_exercise": [
        "exercise during chemotherapy", "cancer rehabilitation",
        "exercise after cancer treatment", "cancer fatigue exercise",
        "oncology exercise",
    ],
}


def get_all_keywords() -> list[str]:
    """Flatten the keyword taxonomy into a single list for Google Trends."""
    keywords = []
    for dimension_key, dimension_val in KEYWORDS.items():
        if isinstance(dimension_val, dict):
            for sub_group in dimension_val.values():
                keywords.extend(sub_group)
        elif isinstance(dimension_val, list):
            keywords.extend(dimension_val)
    return keywords


# ═══════════════════════════════════════════════════════════════════
# SUBREDDIT MONITORING
# ═══════════════════════════════════════════════════════════════════

SUBREDDITS = {
    # Core pain communities — high signal, almost every post is relevant
    "pain_support": [
        "ChronicPain", "backpain", "Sciatica", "Fibromyalgia",
        "PelvicFloor", "TMJ",
    ],
    # Fitness & recovery — broader subs, relevance filter extracts
    # pain/form/injury posts and drops diet/meme/progress-pic noise
    "fitness_recovery": [
        "flexibility", "posture", "bodyweightfitness",
        "PhysicalTherapy", "Fitness",
    ],
    "strength_sports": [
        "CrossFit", "powerlifting", "weightroom",
    ],
    "clinical_professional": [
        "physicaltherapy", "Ergonomics",
    ],
    "sports_pain": [
        "cycling", "golf",
    ],
    "yoga_recovery": [
        "yoga", "yogatherapy", "ashtanga",
    ],
    "running_injury": [
        "running", "AdvancedRunning", "Marathon", "ultrarunning",
    ],
    "longevity": [
        "longevity", "Biohackers", "QuantifiedSelf",
    ],
    "cancer_exercise": [
        "cancer", "CancerFighters", "breastcancer",
    ],
}

EXEC_SUBREDDITS = [
    "fatFIRE", "startups", "experienceddevs",
    "consulting", "sales", "ycombinator",
    "venturecapital", "Entrepreneur", "Biohackers",
    "SaaS", "cscareerquestions",
]


# ═══════════════════════════════════════════════════════════════════
# QUORA SEARCH QUERIES
# ═══════════════════════════════════════════════════════════════════

QUORA_SEARCH_QUERIES = [
    "best exercises for chronic back pain",
    "how to prevent lower back pain from sitting",
    "sciatica pain relief exercises",
    "posture correction for desk workers",
    "piriformis syndrome vs sciatica difference",
    "how to fix forward head posture permanently",
    "best exercises for thoracic outlet syndrome",
    "why does my hip hurt after sitting all day",
    "how long does it take to fix anterior pelvic tilt",
    "is a standing desk better than sitting for back pain",
    "best foam roller exercises for back pain relief",
    "how to prevent back pain as a nurse",
    "chiropractor vs physical therapist for sciatica",
    "tension headache from bad posture treatment",
    "corrective exercise specialist vs physical therapist",
    # Yoga therapy
    "yoga for sciatica pain relief",
    "best yoga poses for lower back pain",
    "is yoga good for herniated disc",
    # Running injuries
    "how to fix IT band syndrome from running",
    "best exercises for runner's knee",
    "marathon recovery exercises",
    # Cancer exercise
    "safe exercises during chemotherapy",
    "exercise after cancer treatment fatigue",
    # Longevity
    "best exercises for longevity over 40",
    "mobility exercises for aging joints",
]


# ═══════════════════════════════════════════════════════════════════
# WIKIPEDIA ARTICLES TO TRACK
# ═══════════════════════════════════════════════════════════════════

WIKI_ARTICLES = [
    "Chronic_pain", "Sciatica", "Fibromyalgia", "Low_back_pain",
    "Physical_therapy", "Ergonomics", "Kyphosis",
    "Piriformis_syndrome", "Thoracic_outlet_syndrome",
    "Plantar_fasciitis", "Rotator_cuff_tear",
    "Sacroiliac_joint_dysfunction", "Spinal_stenosis",
    "Scoliosis", "Spinal_disc_herniation",
    "Tension_headache", "Myofascial_pain_syndrome",
    "Carpal_tunnel_syndrome", "Lordosis",
    "Anterior_pelvic_tilt", "Posture",
    # Yoga therapy
    "Yoga_therapy", "Yoga_as_exercise",
    # Running injuries
    "Iliotibial_band_syndrome", "Achilles_tendinitis",
    "Patellofemoral_pain_syndrome",
    # Cancer exercise
    "Cancer-related_fatigue", "Exercise_and_cancer",
    # Longevity
    "Blue_zone", "Longevity",
]


# ═══════════════════════════════════════════════════════════════════
# EXERCISE PRESCRIPTION MAPPING
# ═══════════════════════════════════════════════════════════════════

TOPIC_SOLUTIONS = {
    "sciatica": ["Piriformis stretch", "Nerve flossing", "Figure-4 stretch"],
    "back pain": ["Cat-cow", "Bird dog", "McGill big 3"],
    "lower back pain": ["Cat-cow", "Bird dog", "McGill big 3", "Glute bridges"],
    "neck pain": ["Chin tucks", "Scalene stretch", "Thoracic extension"],
    "posture": ["Wall angels", "Band pull-aparts", "Doorway stretch"],
    "sitting": ["Hip flexor stretch", "Glute bridges", "Walking breaks"],
    "cancer pain": ["Gentle mobility", "Breathwork", "Mindful movement"],
    "hip pain": ["Clamshells", "Hip flexor stretch", "90/90 stretch", "Pigeon pose"],
    "shoulder pain": ["Band pull-aparts", "External rotation", "Face pulls", "Sleeper stretch"],
    "upper back pain": ["Thoracic extension", "Foam roller thoracic", "Prone Y raise"],
    "knee pain": ["Terminal knee extension", "Step-downs", "Quad foam roll"],
    "tension headache": ["Chin tucks", "Suboccipital release", "Upper trap stretch"],
    "plantar fasciitis": ["Calf stretch", "Toe curls", "Frozen bottle roll"],
    "piriformis": ["Piriformis stretch", "Figure-4 stretch", "Pigeon pose", "Glute foam roll"],
    "piriformis syndrome": ["Piriformis stretch", "Figure-4 stretch", "Pigeon pose", "Glute foam roll"],
    "thoracic outlet": ["Scalene stretch", "Pec minor stretch", "Nerve glides"],
    "thoracic outlet syndrome": ["Scalene stretch", "Pec minor stretch", "Nerve glides"],
    "forward head posture": ["Chin tucks", "Wall angels", "Cervical retraction"],
    "anterior pelvic tilt": ["Hip flexor stretch", "Glute bridges", "Dead bugs", "Posterior pelvic tilt drill"],
    "carpal tunnel": ["Wrist flexor stretch", "Nerve glides", "Tendon gliding"],
    "fibromyalgia": ["Gentle walking", "Aquatic exercise", "Tai chi", "Yoga"],
    "text neck": ["Chin tucks", "Thoracic extension", "Scalene stretch"],
    "standing desk": ["Calf raises", "Weight shifting", "Standing hip flexor stretch"],
    "office ergonomics": ["Desk stretches", "Eye-level monitor", "90-90 sitting posture"],
    "foam rolling": ["Thoracic roller", "IT band", "Glute roll", "Lat roll"],
    "mobility exercises": ["World's greatest stretch", "90/90", "Cat-cow", "Thread the needle"],
    # Yoga therapy (Bart's 10K+ yoga hours)
    "yoga for back pain": ["Cat-cow (Marjaryasana)", "Child's pose (Balasana)", "Sphinx pose", "Supine twist"],
    "yoga for sciatica": ["Reclined pigeon", "Supine twist", "Figure-4 stretch", "Thread the needle"],
    "therapeutic yoga": ["Supported bridge", "Legs-up-the-wall", "Constructive rest", "Supine spinal twist"],
    "yoga for chronic pain": ["Gentle cat-cow", "Supported child's pose", "Savasana with props", "Diaphragmatic breathing"],
    "restorative yoga": ["Supported bridge", "Legs-up-the-wall", "Supported fish", "Side-lying savasana"],
    # Running recovery (Bart is an ultra marathoner)
    "runner's knee": ["Terminal knee extension", "VMO activation", "Single-leg step-down", "Foam roll quads/IT band"],
    "IT band syndrome": ["Side-lying clamshells", "Lateral band walks", "Foam roll IT band", "Single-leg deadlift"],
    "achilles tendonitis": ["Eccentric heel drops", "Calf raises (bent knee)", "Ankle alphabet", "Soleus stretch"],
    "plantar fasciitis running": ["Calf stretch (wall)", "Toe curls with towel", "Frozen bottle roll", "Arch doming"],
    "marathon recovery": ["Foam roll full body", "Gentle walking", "Legs-up-the-wall", "Epsom salt bath"],
    "hip flexor running": ["Half-kneeling hip flexor stretch", "Couch stretch", "Psoas march", "Glute bridges"],
    # Cancer exercise (Bart is ACSM-CET certified)
    "exercise during chemotherapy": ["Gentle walking (10-15 min)", "Seated arm raises", "Chair-supported squats", "Diaphragmatic breathing"],
    "cancer rehabilitation": ["Progressive walking program", "Light resistance bands", "Balance exercises", "Gentle yoga"],
    "exercise after cancer treatment": ["Graduated walking", "Bodyweight squats", "Wall push-ups", "Gentle stretching"],
    "cancer fatigue exercise": ["5-minute walk intervals", "Seated exercises", "Gentle range of motion", "Restorative breathing"],
    "oncology exercise": ["Supervised progressive resistance", "Aerobic intervals", "Flexibility work", "Balance training"],
    # Longevity & biohacking
    "longevity exercises": ["Zone 2 walking", "Goblet squats", "Farmer carries", "Turkish get-up"],
    "mobility for aging": ["World's greatest stretch", "Hip CARs", "Thoracic rotation", "Ankle mobility"],
    "functional fitness over 40": ["Deadlift pattern", "Push-pull balance", "Single-leg work", "Loaded carries"],
    "joint health": ["CARs (controlled articular rotations)", "Band pull-aparts", "Hip CARs", "Shoulder CARs"],
    "movement longevity": ["Ground-to-standing transitions", "Balance work", "Grip strength", "Mobility flows"],
}

# ═══════════════════════════════════════════════════════════════════
# ENRICHED EXERCISE PRESCRIPTIONS (clinical depth)
# ═══════════════════════════════════════════════════════════════════
# Structured exercise data with sets/reps, progressions, regressions,
# and contraindications for the most common themes.

EXERCISE_PROTOCOLS = {
    "sciatica": [
        {"name": "Piriformis stretch", "sets": "3x30s each side", "progression": "Add hip internal rotation", "regression": "Supine figure-4 with strap", "contraindication": "Acute disc herniation with progressive neurological deficit"},
        {"name": "Nerve flossing (sciatic)", "sets": "2x10 reps", "progression": "Add ankle dorsiflexion", "regression": "Seated slump only", "contraindication": "Acute radiculopathy with severe pain"},
        {"name": "Figure-4 stretch", "sets": "3x30s each side", "progression": "Standing figure-4", "regression": "Supine with pillow under head", "contraindication": "Recent hip replacement"},
    ],
    "lower back pain": [
        {"name": "Cat-cow", "sets": "2x10 cycles", "progression": "Add bird dog from cat-cow", "regression": "Pelvic tilts only (supine)", "contraindication": "Spondylolisthesis with instability"},
        {"name": "Bird dog", "sets": "3x8 each side", "progression": "Add resistance band", "regression": "Hands and knees only (no limb lift)", "contraindication": "None standard"},
        {"name": "McGill curl-up", "sets": "3x10", "progression": "Increase hold to 10s", "regression": "Head lift only", "contraindication": "Recent abdominal surgery"},
        {"name": "Glute bridges", "sets": "3x12", "progression": "Single-leg bridge", "regression": "Smaller range of motion", "contraindication": "Acute SI joint flare"},
    ],
    "neck pain": [
        {"name": "Chin tucks", "sets": "3x10 (5s hold)", "progression": "Add resistance with hand", "regression": "Supine chin tucks", "contraindication": "Cervical instability"},
        {"name": "Scalene stretch", "sets": "2x30s each side", "progression": "Add gentle overpressure", "regression": "Active range only", "contraindication": "Thoracic outlet syndrome (acute)"},
        {"name": "Thoracic extension", "sets": "2x10 over foam roller", "progression": "Arms overhead", "regression": "Towel roll (smaller ROM)", "contraindication": "Osteoporosis with compression fracture history"},
    ],
    "hip pain": [
        {"name": "Clamshells", "sets": "3x15 each side", "progression": "Add resistance band", "regression": "Smaller range of motion", "contraindication": "Labral tear (if painful)"},
        {"name": "Hip flexor stretch (half-kneeling)", "sets": "3x30s each side", "progression": "Add lateral trunk lean", "regression": "Standing lunge stretch", "contraindication": "Acute hip flexor strain"},
        {"name": "90/90 stretch", "sets": "2x30s each side", "progression": "Active transitions", "regression": "Supported with cushion", "contraindication": "Severe hip impingement"},
    ],
    "posture": [
        {"name": "Wall angels", "sets": "3x10", "progression": "Add band resistance", "regression": "Seated arm slides", "contraindication": "Acute rotator cuff injury"},
        {"name": "Band pull-aparts", "sets": "3x15", "progression": "Heavier band", "regression": "No band (arm movement only)", "contraindication": "None standard"},
        {"name": "Doorway stretch (pec)", "sets": "3x30s", "progression": "Vary arm angles (high/mid/low)", "regression": "Wall corner stretch", "contraindication": "Anterior shoulder instability"},
    ],
    "cancer fatigue exercise": [
        {"name": "5-minute walk intervals", "sets": "2-3 intervals, rest between", "progression": "Increase to 10-min walks", "regression": "Seated marching in place", "contraindication": "Platelet count <50,000; active infection; bone metastasis at weight-bearing site"},
        {"name": "Seated arm raises", "sets": "2x8 (light or no weight)", "progression": "Add 1-2 lb weights", "regression": "Assisted range of motion", "contraindication": "Lymphedema (affected arm)"},
        {"name": "Diaphragmatic breathing", "sets": "3x5 breaths", "progression": "Add 4-7-8 pattern", "regression": "Hands on belly awareness only", "contraindication": "None standard"},
    ],
}


# ═══════════════════════════════════════════════════════════════════
# HELP-SEEKING SIGNAL KEYWORDS (for engagement ranking)
# ═══════════════════════════════════════════════════════════════════

HELP_SEEKING_SIGNALS = [
    "advice", "help", "struggling", "years", "months",
    "nothing works", "getting worse", "desperate", "recommend",
    "any tips", "what should I do", "tried everything",
    "pain", "chronic", "can't sleep", "surgery",
    "scared", "terrified", "frustrated",
]


# ═══════════════════════════════════════════════════════════════════
# API & EMAIL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

EMAIL_CONFIG = {
    "sender": os.getenv("SENDER_EMAIL", ""),
    "recipient": os.getenv("RECIPIENT_EMAIL", ""),
    # Keys matching sender.py expectations
    "smtp_host": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "smtp_user": os.getenv("SENDER_EMAIL", ""),
    "smtp_pass": os.getenv("SENDER_PASSWORD", ""),
    "from_name": "Trend Engine",
    "use_tls": True,
}

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "FormCoachBot/1.5")

# Claude model configuration
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
CLAUDE_MAX_TOKENS = 4096
