#!/usr/bin/env python3
"""
Generate Anki flashcard decks organized by JLPT level and frequency tier.

Creates a directory structure like:
    output_dir/
        N5/
            Tier_1/
                kanji.csv
                vocab.csv
            Tier_2/
                kanji.csv
                vocab.csv
            ...
        N4/
            Tier_1/
                ...

Usage:
    python create_tiered_decks.py --help
    python create_tiered_decks.py -o my_decks/
    python create_tiered_decks.py --examples  # Include example sentences in vocab
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from jmdict_utils import (
    load_json,
    build_kanji_jlpt_map,
    build_kanji_frequency_map,
    calculate_frequency_tiers,
    get_word_jlpt_level,
    get_word_frequency_tier,
    process_word,
)


def process_kanji_character(char: Dict) -> Optional[Dict]:
    """Extract relevant fields from a kanji character entry"""
    literal = char.get("literal")
    if not literal:
        return None

    misc = char.get("misc", {})
    reading_meaning = char.get("readingMeaning")
    dict_refs = char.get("dictionaryReferences", [])

    # JLPT level (1-4, old system)
    jlpt_level = misc.get("jlptLevel")

    # Skip if no JLPT level
    if jlpt_level is None:
        return None

    # Stroke count
    stroke_counts = misc.get("strokeCounts", [])
    stroke_count = stroke_counts[0] if stroke_counts else None

    # Grade
    grade = misc.get("grade")

    # Frequency rank
    frequency = misc.get("frequency")

    # Extract readings
    on_readings = []
    kun_readings = []
    if reading_meaning and "groups" in reading_meaning:
        for group in reading_meaning.get("groups", []):
            for reading in group.get("readings", []):
                rtype = reading.get("type", "")
                value = reading.get("value", "")
                if rtype == "ja_on":
                    on_readings.append(value)
                elif rtype == "ja_kun":
                    kun_readings.append(value)

    # Extract meanings
    meanings = []
    if reading_meaning and "groups" in reading_meaning:
        for group in reading_meaning.get("groups", []):
            for meaning in group.get("meanings", []):
                if meaning.get("lang", "en") == "en":
                    value = meaning.get("value")
                    if value:
                        meanings.append(value)

    # Get radical
    radicals = char.get("radicals", [])
    radical = None
    if radicals and len(radicals) > 0:
        radical = radicals[0].get("value")

    # Extract name readings (nanori)
    nanori = reading_meaning.get("nanori", []) if reading_meaning else []

    # Extract Heisig RTK references
    heisig = None
    heisig6 = None
    for ref in dict_refs:
        if ref.get("type") == "heisig":
            heisig = ref.get("value")
        elif ref.get("type") == "heisig6":
            heisig6 = ref.get("value")

    return {
        "kanji": literal,
        "jlpt_level": jlpt_level,
        "on_readings": "; ".join(on_readings),
        "kun_readings": "; ".join(kun_readings),
        "meanings": "; ".join(meanings),
        "stroke_count": stroke_count,
        "grade": grade,
        "frequency": frequency,
        "radical": radical,
        "nanori": "; ".join(nanori) if nanori else "",
        "heisig_rtk": heisig if heisig else "",
        "heisig6_rtk": heisig6 if heisig6 else "",
    }


def format_kanji_back_field(char: Dict) -> str:
    """Create formatted back field with all kanji information"""
    parts = []

    # Meanings
    if char.get("meanings"):
        parts.append(f"<b>Meanings:</b> {char['meanings']}")

    # Readings
    if char.get("on_readings"):
        parts.append(f"<b>On'yomi:</b> {char['on_readings']}")
    if char.get("kun_readings"):
        parts.append(f"<b>Kun'yomi:</b> {char['kun_readings']}")

    # Name readings
    if char.get("nanori"):
        parts.append(f"<b>Name readings:</b> {char['nanori']}")

    # Stats
    stats = []
    if char.get("stroke_count"):
        stats.append(f"Strokes: {char['stroke_count']}")
    if char.get("radical"):
        stats.append(f"Radical: {char['radical']}")
    if char.get("frequency"):
        stats.append(f"Freq: #{char['frequency']}")
    if stats:
        parts.append(f"<b>Stats:</b> {' | '.join(stats)}")

    # Heisig RTK references
    if char.get("heisig_rtk") or char.get("heisig6_rtk"):
        rtk_parts = []
        if char.get("heisig_rtk"):
            rtk_parts.append(f"RTK: #{char['heisig_rtk']}")
        if char.get("heisig6_rtk"):
            rtk_parts.append(f"RTK6: #{char['heisig6_rtk']}")
        parts.append(f"<b>Heisig:</b> {' | '.join(rtk_parts)}")

    return "<br><br>".join(parts)


def create_kanji_csv(characters: List[Dict], output_path: Path) -> None:
    """Create Anki-compatible CSV file for kanji"""
    fieldnames = ["kanji", "back", "tags"]

    output_rows = []
    for char in characters:
        back = format_kanji_back_field(char)

        # Tags
        tags_list = []
        if char.get("grade"):
            tags_list.append(f"grade{char['grade']}")
        if char.get("tier"):
            tags_list.append(f"freq_tier{char['tier']}")

        row = {"kanji": char["kanji"], "back": back, "tags": " ".join(tags_list)}
        output_rows.append(row)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"    Created: {output_path} ({len(characters)} kanji)")


def create_vocab_csv(
    words: List[Dict], output_path: Path, include_examples: bool = False
) -> None:
    """Create Anki-compatible CSV file for vocabulary"""
    fieldnames = ["word", "back", "tags"]

    output_rows = []
    for word in words:
        back_parts = []

        # Readings
        if word.get("readings"):
            back_parts.append(f"<b>Reading:</b> {word['readings']}")

        # Meanings
        if word.get("senses"):
            back_parts.append(f"<b>Meanings:</b><br>{word['senses']}")

        # Examples (if included)
        if include_examples and word.get("examples"):
            back_parts.append(f"<b>Examples:</b><br>{word['examples']}")

        back = "<br><br>".join(back_parts)

        # Tags
        tags_list = []
        if word.get("is_common"):
            tags_list.append("common")
        if word.get("form_type"):
            tags_list.append(word["form_type"])
        if word.get("tier"):
            tags_list.append(f"freq_tier{word['tier']}")

        row = {"word": word["word"], "back": back, "tags": " ".join(tags_list)}
        output_rows.append(row)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"    Created: {output_path} ({len(words)} words)")


def get_new_jlpt_level(old_level: int, grade: Optional[int]) -> str:
    """Convert old JLPT level to new N-level system"""
    if old_level == 4:
        return "N5"
    elif old_level == 3:
        return "N4"
    elif old_level == 2:
        # Split level 2 between N3 and N2 based on grade
        if grade and grade <= 6:
            return "N3"
        else:
            return "N2"
    elif old_level == 1:
        return "N1"
    else:
        return "unknown"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate JLPT kanji and vocab decks organized by tier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Use default input files (with examples)
  %(prog)s -o my_decks/              # Custom output directory
  %(prog)s --no-examples             # Exclude example sentences
  %(prog)s --common-only             # Only include common words
        """,
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("tiered_decks"),
        help="Output directory (default: tiered_decks/)",
    )

    parser.add_argument(
        "--jmdict",
        type=Path,
        default=Path("jmdict-eng-3.6.2.json"),
        help="Path to JMdict JSON file (default: jmdict-eng-3.6.2.json)",
    )

    parser.add_argument(
        "--jmdict-examples",
        type=Path,
        default=Path("jmdict-examples-eng-3.6.2.json"),
        help="Path to JMdict examples JSON file (default: jmdict-examples-eng-3.6.2.json)",
    )

    parser.add_argument(
        "--kanjidic",
        type=Path,
        default=Path("kanjidic2-en-3.6.2.json"),
        help="Path to Kanjidic2 JSON file (default: kanjidic2-en-3.6.2.json)",
    )

    parser.add_argument(
        "--no-examples",
        action="store_true",
        help="Exclude example sentences from vocabulary decks (included by default)",
    )

    parser.add_argument(
        "--common-only", action="store_true", help="Only include words marked as common"
    )

    parser.add_argument(
        "--tier-strategy",
        type=str,
        choices=["conservative", "average", "first"],
        default="conservative",
        help=(
            "Strategy for calculating word frequency tier from kanji tiers (default: conservative). "
            "conservative: use highest tier (least frequent kanji) - safest for learning; "
            "average: round up average of all kanji tiers; "
            "first: use only the first kanji's tier"
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Determine which JMdict file to use (examples included by default)
    include_examples = not args.no_examples
    if include_examples:
        jmdict_file = args.jmdict_examples
    else:
        jmdict_file = args.jmdict

    output_dir = args.output_dir
    kanjidic_file = args.kanjidic

    # Validate input files
    if not jmdict_file.exists():
        print(f"Error: JMdict file not found: {jmdict_file}", file=sys.stderr)
        print("Please download from:", file=sys.stderr)
        print(
            "https://github.com/scriptin/jmdict-simplified/releases/latest",
            file=sys.stderr,
        )
        sys.exit(1)

    if not kanjidic_file.exists():
        print(f"Error: Kanjidic file not found: {kanjidic_file}", file=sys.stderr)
        print("Please download from:", file=sys.stderr)
        print(
            "https://github.com/scriptin/jmdict-simplified/releases/latest",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Loading Kanjidic2 (kanji JLPT and frequency data)...")
    kanjidic_data = load_json(kanjidic_file)
    kanji_jlpt_map = build_kanji_jlpt_map(kanjidic_data)
    print(f"Loaded {len(kanji_jlpt_map)} kanji with JLPT levels")

    # Calculate frequency tiers for kanji
    print("Calculating kanji frequency tiers...")
    kanji_freq_map = build_kanji_frequency_map(kanjidic_data)
    kanji_tier_map = calculate_frequency_tiers(kanji_freq_map)
    print(f"Calculated tiers for {len(kanji_tier_map)} kanji with frequency data")

    # Process kanji and organize by JLPT level and tier
    print("\nProcessing kanji...")
    jlpt_kanji_groups: Dict[str, Dict[int, List[Dict]]] = {
        "N5": {1: [], 2: [], 3: [], 4: []},
        "N4": {1: [], 2: [], 3: [], 4: []},
        "N3": {1: [], 2: [], 3: [], 4: []},
        "N2": {1: [], 2: [], 3: [], 4: []},
        "N1": {1: [], 2: [], 3: [], 4: []},
    }

    kanji_processed = 0
    kanji_skipped = 0

    for char in kanjidic_data.get("characters", []):
        result = process_kanji_character(char)
        if result:
            # Add tier information
            kanji = result["kanji"]
            if kanji in kanji_tier_map:
                result["tier"] = kanji_tier_map[kanji]

            level = result["jlpt_level"]
            grade = result.get("grade")
            new_level = get_new_jlpt_level(level, grade)

            if new_level in jlpt_kanji_groups and result.get("tier"):
                tier = result["tier"]
                jlpt_kanji_groups[new_level][tier].append(result)
                kanji_processed += 1
            else:
                kanji_skipped += 1
        else:
            kanji_skipped += 1

    print(f"Processed {kanji_processed} kanji with JLPT levels and frequency data")

    # Load and process vocabulary
    print(
        f"\nLoading JMdict ({'with examples' if include_examples else 'without examples'})..."
    )
    jmdict_data = load_json(jmdict_file)
    tags = jmdict_data.get("tags", {})
    total_entries = len(jmdict_data.get("words", []))
    print(f"Total entries: {total_entries}")

    # Process vocabulary and organize by JLPT level and tier
    print("\nProcessing vocabulary...")
    jlpt_vocab_groups: Dict[str, Dict[int, List[Dict]]] = {
        "N5": {1: [], 2: [], 3: [], 4: []},
        "N4": {1: [], 2: [], 3: [], 4: []},
        "N3": {1: [], 2: [], 3: [], 4: []},
        "N2": {1: [], 2: [], 3: [], 4: []},
        "N1": {1: [], 2: [], 3: [], 4: []},
    }

    vocab_processed = 0
    vocab_skipped = 0

    for word in jmdict_data.get("words", []):
        result = process_word(word, tags, include_examples=include_examples)
        if result:
            # Filter by common-only if requested
            if args.common_only and not result["is_common"]:
                vocab_skipped += 1
                continue

            jlpt_level = get_word_jlpt_level(word, kanji_jlpt_map)

            # Skip kana-only and non-JLPT words for tiered decks
            if jlpt_level not in ["N5", "N4", "N3", "N2", "N1"]:
                vocab_skipped += 1
                continue

            # Calculate frequency tier for the word
            tier = get_word_frequency_tier(
                word, kanji_tier_map, strategy=args.tier_strategy
            )

            if tier:
                result["tier"] = tier
                jlpt_vocab_groups[jlpt_level][tier].append(result)
                vocab_processed += 1
            else:
                vocab_skipped += 1
        else:
            vocab_skipped += 1

    print(f"Processed {vocab_processed} words with JLPT levels and frequency data")

    # Create directory structure and output files
    print(f"\nCreating tiered deck structure in {output_dir}...")
    output_dir.mkdir(exist_ok=True)

    total_kanji = 0
    total_vocab = 0

    for jlpt_level in ["N5", "N4", "N3", "N2", "N1"]:
        jlpt_dir = output_dir / jlpt_level
        jlpt_dir.mkdir(exist_ok=True)

        print(f"\n{jlpt_level}:")

        for tier in [1, 2, 3, 4]:
            tier_dir = jlpt_dir / f"Tier_{tier}"
            tier_dir.mkdir(exist_ok=True)

            kanji_list = jlpt_kanji_groups[jlpt_level][tier]
            vocab_list = jlpt_vocab_groups[jlpt_level][tier]

            print(f"  Tier {tier}: {len(kanji_list)} kanji, {len(vocab_list)} words")

            # Create kanji deck if there are kanji
            if kanji_list:
                kanji_path = tier_dir / "kanji.csv"
                create_kanji_csv(kanji_list, kanji_path)
                total_kanji += len(kanji_list)

            # Create vocab deck if there are words
            if vocab_list:
                vocab_path = tier_dir / "vocab.csv"
                create_vocab_csv(
                    vocab_list, vocab_path, include_examples=include_examples
                )
                total_vocab += len(vocab_list)

    # Summary
    print("\n" + "=" * 60)
    print("TIERED DECKS SUMMARY")
    print("=" * 60)
    print(f"Total kanji: {total_kanji}")
    print(f"Total vocabulary: {total_vocab}")
    print(f"\nDirectory structure:")
    print(f"  {output_dir}/")
    for jlpt_level in ["N5", "N4", "N3", "N2", "N1"]:
        print(f"    {jlpt_level}/")
        for tier in [1, 2, 3, 4]:
            kanji_count = len(jlpt_kanji_groups[jlpt_level][tier])
            vocab_count = len(jlpt_vocab_groups[jlpt_level][tier])
            if kanji_count > 0 or vocab_count > 0:
                print(f"      Tier_{tier}/ ({kanji_count} kanji, {vocab_count} words)")

    print(f"\nFiles saved to: {output_dir.absolute()}")

    print("\n" + "=" * 60)
    print("FREQUENCY TIER INFORMATION")
    print("=" * 60)
    print(f"Tier strategy: {args.tier_strategy}")
    print("Tier 1: Top 25% most frequent kanji")
    print("Tier 2: 25-50%")
    print("Tier 3: 50-75%")
    print("Tier 4: Bottom 25% least frequent")
    print("\nWords are tagged with 'freq_tierN' where N is 1-4")

    print("\n" + "=" * 60)
    print("IMPORT INSTRUCTIONS")
    print("=" * 60)
    print("1. Open Anki → File → Import")
    print("2. Navigate to the desired Tier folder")
    print("3. Select kanji.csv or vocab.csv")
    print("4. Type: Basic")
    print("5. Field mapping:")
    print("   - Column 1 (kanji/word) → Front")
    print("   - Column 2 (back) → Back")
    print("   - Column 3 (tags) → Tags")
    print("6. ✅ Allow HTML in fields")

    if include_examples:
        print("\nExamples are from Tatoeba corpus (Japanese/English pairs)")


if __name__ == "__main__":
    main()
