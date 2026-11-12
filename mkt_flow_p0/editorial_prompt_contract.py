"""Shared editorial prompt contract for every article genre.

Pure preparation step: no network, no factual certification, no approval.
Call immediately before the actual model request. Never infer missing facts.
"""
from mkt_flow_p0.editorial_substance import normalize_brief, writing_instruction


def prepare_editorial_prompt(system_prompt, brief, *, genre, voice_variant="mda"):
    """Fail closed for missing/invalid briefing or mismatched genre."""
    if not isinstance(system_prompt, str) or not system_prompt.strip():
        raise ValueError("prompt base editorial ausente")
    normalized = normalize_brief(brief)
    if normalized["genre"] != genre:
        raise ValueError("gênero do briefing diverge do artigo")
    return system_prompt + "\n" + writing_instruction(normalized, voice_variant=voice_variant)


def prepare_editorial_request(system_prompt, user_payload, brief, *, genre,
                              voice_variant="mda"):
    """Build a model request without changing verified source inputs."""
    return {
        "system": prepare_editorial_prompt(
            system_prompt, brief, genre=genre, voice_variant=voice_variant),
        "payload": user_payload,
        "genre": genre,
        "brief": normalize_brief(brief),
    }
