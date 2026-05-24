import re

def compute_cqr(human_text: str, ai_response: str, mission_target_words: int = 300) -> dict:
    if not human_text.strip():
        return {"cqr": 0.0, "breakdown": {"originality": 0, "depth": 0, "conciseness": 0}}
    
    words = re.findall(r'\b\w+\b', human_text.lower())
    unique_ratio = len(set(words)) / len(words) if words else 0
    long_phrase_score = 1.0 - (len(re.findall(r'\b(the|and|that|which|this|from|with)\b', human_text)) / len(words) * 0.8)
    originality = (unique_ratio * 0.7 + long_phrase_score * 0.3) ** 1.5
    
    markers = ["from first principles", "define", "axiom", "assume", "counterexample", "derive", "debug", "iterate"]
    depth_score = sum(1 for m in markers if m in human_text.lower()) / len(markers)
    has_structure = bool(re.search(r'(step|because|therefore|if|then)', human_text, re.I)) * 0.6
    
    word_count = len(words)
    conciseness = min(1.0, mission_target_words / max(word_count, 50))
    
    cqr = (originality * 0.60) + (depth_score * 0.25) + (conciseness * 0.15)
    cqr = max(0.0, min(1.0, cqr))
    
    return {
        "cqr": round(cqr, 3),
        "breakdown": {
            "originality": round(originality, 3),
            "depth": round(depth_score * has_structure, 3),
            "conciseness": round(conciseness, 3),
            "human_words": word_count,
            "ai_words": len(re.findall(r'\b\w+\b', ai_response))
        }
    }
