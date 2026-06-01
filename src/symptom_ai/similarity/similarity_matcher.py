import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


KNOWN_PROFILES = {
    "benign_office_like": {
        "file_write_burst": 0.10,
        "file_rename_burst": 0.05,
        "high_entropy_write": 0.10,
        "mass_file_modification": 0.10,
        "suspicious_extension_change": 0.00,
        "ransom_note_created": 0.00,
        "c2_beaconing": 0.00,
        "data_exfiltration_pattern": 0.00
    },
    "lockbit_like": {
        "file_write_burst": 0.95,
        "file_rename_burst": 0.85,
        "high_entropy_write": 0.90,
        "mass_file_modification": 0.90,
        "suspicious_extension_change": 0.80,
        "ransom_note_created": 0.60,
        "c2_beaconing": 0.30,
        "data_exfiltration_pattern": 0.20
    },
    "network_exfiltration_like": {
        "file_write_burst": 0.30,
        "file_rename_burst": 0.10,
        "high_entropy_write": 0.40,
        "mass_file_modification": 0.20,
        "suspicious_extension_change": 0.10,
        "ransom_note_created": 0.00,
        "c2_beaconing": 0.90,
        "data_exfiltration_pattern": 0.95
    }
}


def align_vector(symptoms: dict, keys: list) -> np.ndarray:
    return np.array([float(symptoms.get(k, 0.0)) for k in keys]).reshape(1, -1)


def match_known_profile(symptoms: dict) -> dict:
    keys = sorted(set().union(*[p.keys() for p in KNOWN_PROFILES.values()], symptoms.keys()))
    sample_vec = align_vector(symptoms, keys)

    results = []
    for name, profile in KNOWN_PROFILES.items():
        profile_vec = align_vector(profile, keys)
        sim = float(cosine_similarity(sample_vec, profile_vec)[0][0])
        results.append({
            "profile": name,
            "similarity": round(sim, 4)
        })

    results = sorted(results, key=lambda x: x["similarity"], reverse=True)
    best = results[0] if results else {"profile": "unknown", "similarity": 0.0}

    return {
        "best_match": best,
        "all_matches": results
    }
