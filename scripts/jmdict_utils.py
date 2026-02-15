#!/usr/bin/env python3
"""
Shared utilities for JMdict/Anki deck generation scripts
"""

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


def load_json(filepath: Path) -> Dict:
    """Load and parse JSON file with error handling"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def build_kanji_jlpt_map(kanjidic_data: Dict) -> Dict[str, str]:
    """
    Build a map of kanji -> JLPT level
    Maps old JLPT levels (1-4) to new system (N1-N5)
    """
    kanji_jlpt = {}

    # Old JLPT to new JLPT mapping:
    # Level 4 (easiest) -> N5
    # Level 3 -> N4
    # Level 2 -> N3/N2 (split by grade)
    # Level 1 (hardest) -> N1
    OLD_TO_NEW_JLPT = {
        4: "N5",
        3: "N4",
        2: None,  # Special handling below
        1: "N1",
    }

    for char in kanjidic_data.get("characters", []):
        literal = char.get("literal")
        if not literal:
            continue

        misc = char.get("misc", {})
        jlpt_level = misc.get("jlptLevel")

        if jlpt_level is None:
            continue

        if jlpt_level == 2:
            # Split old level 2: grade 1-6 -> N3, grade 7+ -> N2
            grade = misc.get("grade")
            if grade and grade <= 6:
                kanji_jlpt[literal] = "N3"
            else:
                kanji_jlpt[literal] = "N2"
        elif jlpt_level in OLD_TO_NEW_JLPT:
            kanji_jlpt[literal] = OLD_TO_NEW_JLPT[jlpt_level]

    return kanji_jlpt


def build_kanji_frequency_map(kanjidic_data: Dict) -> Dict[str, int]:
    """
    Build a map of kanji -> frequency rank
    Returns empty dict for kanji without frequency data
    """
    kanji_freq = {}

    for char in kanjidic_data.get("characters", []):
        literal = char.get("literal")
        if not literal:
            continue

        misc = char.get("misc", {})
        frequency = misc.get("frequency")

        if frequency is not None:
            kanji_freq[literal] = frequency

    return kanji_freq


def calculate_frequency_tiers(kanji_freq_map: Dict[str, int]) -> Dict[str, int]:
    """
    Calculate percentile-based frequency tiers.

    Tier 1: Top 25% (most frequent, rank 1-25%)
    Tier 2: 25-50%
    Tier 3: 50-75%
    Tier 4: Bottom 25% (least frequent)

    Lower rank = more frequent (rank 1 is most frequent)

    Example:
        With 1000 kanji sorted by frequency rank:
        - Ranks 1-250: Tier 1
        - Ranks 251-500: Tier 2
        - Ranks 501-750: Tier 3
        - Ranks 751-1000: Tier 4

    Returns a map of kanji -> tier number (1-4)
    """
    if not kanji_freq_map:
        return {}

    # Sort kanji by frequency rank (ascending = most frequent first)
    sorted_kanji = sorted(kanji_freq_map.items(), key=lambda x: x[1])
    total = len(sorted_kanji)

    if total == 0:
        return {}

    # Build tier map using percentile calculation for even distribution
    kanji_tiers = {}
    for i, (kanji, _) in enumerate(sorted_kanji):
        # Calculate percentile (0-100) for this kanji
        percentile = (i / total) * 100
        if percentile < 25:
            kanji_tiers[kanji] = 1  # Top 25% - most frequent
        elif percentile < 50:
            kanji_tiers[kanji] = 2  # 25-50%
        elif percentile < 75:
            kanji_tiers[kanji] = 3  # 50-75%
        else:
            kanji_tiers[kanji] = 4  # Bottom 25% - least frequent

    return kanji_tiers


def get_word_frequency_tier(
    word: Dict, kanji_tier_map: Dict[str, int], strategy: str = "conservative"
) -> Optional[int]:
    """
    Determine frequency tier for a word based on its kanji.

    Args:
        word: JMdict word entry
        kanji_tier_map: Map of kanji -> tier number (1-4)
        strategy: How to calculate tier from multiple kanji
            - "conservative": Use highest tier (least frequent kanji) - default
            - "average": Average tier (rounded up)
            - "first": Use tier of first kanji only

    Returns:
        Tier number (1-4) or None if no tier data available

    Example:
        Word "日本" with kanji [日(tier=1), 本(tier=1)]:
        - conservative -> tier 1 (max of [1, 1])
        - average -> tier 1 (ceil((1+1)/2) = 1)
        - first -> tier 1 (first kanji only)

        Word "曜日" with kanji [曜(tier=4), 日(tier=1)]:
        - conservative -> tier 4 (max of [4, 1]) - safest for learning
        - average -> tier 3 (ceil((4+1)/2) = 3)
        - first -> tier 4 (first kanji only)
    """
    kanji_forms = word.get("kanji", [])

    if not kanji_forms:
        # Kana-only word - no tier
        return None

    # Collect tiers for all kanji in the word
    tiers_found = []

    for kanji_entry in kanji_forms:
        kanji_text = kanji_entry.get("text", "")
        for char in kanji_text:
            # Only check characters that are actually kanji (CJK Unified Ideographs)
            if "\u4e00" <= char <= "\u9fff" and char in kanji_tier_map:
                tiers_found.append(kanji_tier_map[char])

    if not tiers_found:
        # No kanji with tier data found
        return None

    if strategy == "conservative":
        # Return highest tier (least frequent) - most conservative
        return max(tiers_found)
    elif strategy == "average":
        # Return average tier rounded up
        return math.ceil(sum(tiers_found) / len(tiers_found))
    elif strategy == "first":
        # Return tier of first kanji only
        return tiers_found[0]
    else:
        # Default to conservative
        return max(tiers_found)


def get_word_jlpt_level(word: Dict, kanji_jlpt_map: Dict[str, str]) -> str:
    """
    Determine JLPT level for a word based on its kanji.
    Returns the HIGHEST level (most difficult) among all kanji in the word.
    """
    kanji_forms = word.get("kanji", [])

    if not kanji_forms:
        # Kana-only word
        return "kana_only"

    # Check all kanji in all forms of the word
    levels_found = []

    for kanji_entry in kanji_forms:
        kanji_text = kanji_entry.get("text", "")
        for char in kanji_text:
            # Only check characters that are actually kanji (CJK Unified Ideographs)
            if "\u4e00" <= char <= "\u9fff" and char in kanji_jlpt_map:
                levels_found.append(kanji_jlpt_map[char])

    if not levels_found:
        # No JLPT kanji found in this word
        return "non_jlpt"

    # Return the highest (most difficult) level
    # Priority: N1 > N2 > N3 > N4 > N5
    level_priority = {"N1": 5, "N2": 4, "N3": 3, "N4": 2, "N5": 1}

    max_priority = 0
    max_level = levels_found[0]
    for level in levels_found:
        if level_priority.get(level, 0) > max_priority:
            max_priority = level_priority[level]
            max_level = level

    return max_level


def is_common_word(word: Dict) -> bool:
    """Check if word is marked as common"""
    kanji_common = any(k.get("common") for k in word.get("kanji", []))
    kana_common = any(ka.get("common") for ka in word.get("kana", []))
    return kanji_common or kana_common


def get_primary_form(word: Dict) -> Tuple[Optional[str], str]:
    """Get the primary kanji/kana form of a word"""
    # Prefer common kanji form
    for k in word.get("kanji", []):
        if k.get("common"):
            return k.get("text"), "kanji"

    # Fall back to any kanji
    if word.get("kanji"):
        text = word["kanji"][0].get("text")
        if text:
            return text, "kanji"

    # Use kana if no kanji
    for ka in word.get("kana", []):
        if ka.get("common"):
            return ka.get("text"), "kana"

    if word.get("kana"):
        text = word["kana"][0].get("text")
        if text:
            return text, "kana"

    return None, ""


def get_readings(word: Dict) -> List[str]:
    """Get all readings (kana forms)"""
    readings = []
    for kana in word.get("kana", []):
        text = kana.get("text")
        if text:
            readings.append(text)
    return readings


def format_sense(sense: Dict, tags: Dict[str, str]) -> str:
    """Format a single sense/meaning"""
    parts = []

    # Part of speech
    pos_tags = []
    for pos in sense.get("partOfSpeech", []):
        tag_text = tags.get(pos, pos)
        if tag_text:
            pos_tags.append(tag_text)
    if pos_tags:
        parts.append(f"({'; '.join(pos_tags)})")

    # Glosses (meanings)
    glosses = []
    for gloss in sense.get("gloss", []):
        if gloss.get("lang") == "eng":
            text = gloss.get("text")
            if text:
                glosses.append(text)
    if glosses:
        parts.append("; ".join(glosses))

    # Additional info
    info = sense.get("info", [])
    if info:
        parts.append(f"[{'; '.join(info)}]")

    # Misc tags
    misc = sense.get("misc", [])
    misc_labels = []
    for m in misc:
        tag_text = tags.get(m, m)
        if tag_text:
            misc_labels.append(tag_text)
    if misc_labels:
        parts.append(f"<i>({'; '.join(misc_labels)})</i>")

    return " ".join(parts)


def format_examples(examples: List[Dict], max_examples: int = 3) -> str:
    """Format example sentences from Tatoeba corpus"""
    if not examples:
        return ""

    formatted = []
    for i, ex in enumerate(examples[:max_examples], 1):
        sentences = ex.get("sentences", [])
        japanese = ""
        english = ""

        for sent in sentences:
            lang = sent.get("lang")
            text = sent.get("text", "")
            if lang == "jpn":
                japanese = text
            elif lang == "eng":
                english = text

        if japanese and english:
            formatted.append(f"{i}. {japanese}<br>→ {english}")

    return "<br>".join(formatted)


def process_word(
    word: Dict, tags: Dict[str, str], include_examples: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Extract relevant fields from a word entry.

    Args:
        word: JMdict word entry
        tags: Tag dictionary from JMdict
        include_examples: Whether to include example sentences

    Returns:
        Dictionary with processed word data or None if invalid
    """
    form, form_type = get_primary_form(word)

    if not form:
        return None

    readings = get_readings(word)

    # Format senses
    senses = []
    all_examples = []

    for i, sense in enumerate(word.get("sense", [])):
        sense_text = format_sense(sense, tags)
        if sense_text:
            senses.append(f"{i + 1}. {sense_text}")

        # Collect examples if requested
        if include_examples:
            examples = sense.get("examples", [])
            if examples:
                formatted_ex = format_examples(examples, max_examples=2)
                if formatted_ex:
                    all_examples.append(formatted_ex)

    if not senses:
        return None

    result = {
        "word": form,
        "readings": ", ".join(readings),
        "senses": "<br>".join(senses),
        "is_common": is_common_word(word),
        "form_type": form_type,
    }

    if include_examples and all_examples:
        result["examples"] = "<br><br>".join(all_examples[:2])

    return result
