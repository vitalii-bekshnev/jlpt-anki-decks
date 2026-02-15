#!/usr/bin/env python3
"""
Generate Anki flashcard decks for JLPT kanji from Kanjidic2 JSON

Usage:
    python create_kanji_decks.py --help
    python create_kanji_decks.py --input path/to/kanjidic.json -o my_decks/
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from jmdict_utils import (
    build_kanji_frequency_map,
    calculate_frequency_tiers,
)


def load_kanjidic(filepath: Path) -> Dict:
    """Load and parse kanjidic2 JSON file with error handling"""
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


def extract_readings(reading_meaning: Optional[Dict]) -> Tuple[List[str], List[str]]:
    """Extract on'yomi and kun'yomi readings"""
    if not reading_meaning or "groups" not in reading_meaning:
        return [], []

    on_readings = []
    kun_readings = []

    for group in reading_meaning.get("groups", []):
        for reading in group.get("readings", []):
            rtype = reading.get("type", "")
            value = reading.get("value", "")
            if rtype == "ja_on":
                on_readings.append(value)
            elif rtype == "ja_kun":
                kun_readings.append(value)

    return on_readings, kun_readings


def extract_meanings(reading_meaning: Optional[Dict], lang: str = "en") -> List[str]:
    """Extract meanings in specified language"""
    if not reading_meaning or "groups" not in reading_meaning:
        return []

    meanings = []
    for group in reading_meaning.get("groups", []):
        for meaning in group.get("meanings", []):
            if meaning.get("lang", "en") == lang:
                value = meaning.get("value")
                if value:
                    meanings.append(value)

    return meanings


def extract_dict_reference(dict_refs: List[Dict], ref_type: str) -> Optional[str]:
    """Extract a specific dictionary reference value"""
    for ref in dict_refs:
        if ref.get("type") == ref_type:
            return ref.get("value")
    return None


def extract_nanori(reading_meaning: Optional[Dict]) -> List[str]:
    """Extract name readings (nanori)"""
    if not reading_meaning:
        return []
    return reading_meaning.get("nanori", [])


def process_character(char: Dict) -> Optional[Dict]:
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
    on_readings, kun_readings = extract_readings(reading_meaning)

    # Extract meanings
    meanings = extract_meanings(reading_meaning)

    # Get radical
    radicals = char.get("radicals", [])
    radical = None
    if radicals and len(radicals) > 0:
        radical = radicals[0].get("value")

    # Extract name readings (nanori)
    nanori = extract_nanori(reading_meaning)

    # Extract Heisig RTK references
    heisig = extract_dict_reference(dict_refs, "heisig")
    heisig6 = extract_dict_reference(dict_refs, "heisig6")

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


def format_back_field(char: Dict) -> str:
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


def create_anki_csv(characters: List[Dict], output_path: Path, jlpt_tier: str) -> None:
    """Create Anki-compatible CSV file"""
    fieldnames = ["kanji", "back", "tags"]

    output_rows = []
    for char in characters:
        back = format_back_field(char)

        # Tags
        tags_list = [jlpt_tier]
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

    print(f"Created: {output_path} ({len(characters)} cards)")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate JLPT kanji Anki decks from Kanjidic2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Use default input file
  %(prog)s -i path/to/kanjidic.json  # Custom input file
  %(prog)s -o my_decks/              # Custom output directory
        """,
    )

    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("kanjidic2-en-3.6.2.json"),
        help="Path to Kanjidic2 JSON file (default: kanjidic2-en-3.6.2.json)",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("anki_decks"),
        help="Output directory (default: anki_decks/)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    input_file = args.input
    output_dir = args.output_dir

    if not input_file.exists():
        print(f"Error: {input_file} not found!", file=sys.stderr)
        print("Please download kanjidic2-en-3.6.2.json from:", file=sys.stderr)
        print(
            "https://github.com/scriptin/jmdict-simplified/releases/latest",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Loading kanjidic2 data...")
    data = load_kanjidic(input_file)

    # Validate data structure
    if "characters" not in data:
        print(
            "Error: Invalid kanjidic file - missing 'characters' key", file=sys.stderr
        )
        sys.exit(1)

    # Calculate frequency tiers for all kanji with frequency data
    print("Calculating frequency tiers...")
    kanji_freq_map = build_kanji_frequency_map(data)
    kanji_tier_map = calculate_frequency_tiers(kanji_freq_map)
    print(f"Calculated tiers for {len(kanji_tier_map)} kanji with frequency data")

    # Group characters by JLPT level
    # Old JLPT: 4=N5, 3=N4, 2=N3/N2, 1=N1
    jlpt_groups: Dict[str, List] = {
        "N5": [],  # Old level 4
        "N4": [],  # Old level 3
        "N3": [],  # Old level 2 (split)
        "N2": [],  # Old level 2 (split)
        "N1": [],  # Old level 1
    }

    print("Processing characters...")
    processed = 0
    skipped = 0

    for char in data.get("characters", []):
        result = process_character(char)
        if result:
            # Add tier information
            kanji = result["kanji"]
            if kanji in kanji_tier_map:
                result["tier"] = kanji_tier_map[kanji]

            level = result["jlpt_level"]
            if level == 4:
                jlpt_groups["N5"].append(result)
            elif level == 3:
                jlpt_groups["N4"].append(result)
            elif level == 2:
                # Split level 2 between N3 and N2 based on grade
                grade = result.get("grade")
                if grade and grade <= 6:
                    jlpt_groups["N3"].append(result)
                else:
                    jlpt_groups["N2"].append(result)
            elif level == 1:
                jlpt_groups["N1"].append(result)
            else:
                skipped += 1  # Unknown JLPT level
                continue
            processed += 1
        else:
            skipped += 1

    print(f"\nProcessed {processed} kanji with JLPT levels")
    if skipped > 0:
        print(f"Skipped {skipped} entries (no JLPT level or invalid data)")

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Generate CSV files
    print(f"\nGenerating CSV files in {output_dir}...")
    for tier in ["N5", "N4", "N3", "N2", "N1"]:
        characters = jlpt_groups[tier]
        if characters:
            output_path = output_dir / f"jlpt_{tier}_kanji.csv"
            create_anki_csv(characters, output_path, tier)

    # Summary
    print("\n" + "=" * 60)
    print("DECK SUMMARY")
    print("=" * 60)
    for tier in ["N5", "N4", "N3", "N2", "N1"]:
        count = len(jlpt_groups[tier])
        print(f"  {tier}: {count} kanji")
    print(f"\nTotal: {sum(len(jlpt_groups[t]) for t in jlpt_groups)} kanji")
    print(f"\nFiles saved to: {output_dir.absolute()}")

    print("\n" + "=" * 60)
    print("IMPORT INSTRUCTIONS")
    print("=" * 60)
    print("1. Open Anki")
    print("2. File → Import")
    print("3. Select CSV file")
    print("4. Set card type to 'Basic'")
    print("5. Field mapping:")
    print("   - Column 1 (kanji) → Front")
    print("   - Column 2 (back) → Back")
    print("   - Column 3 (tags) → Tags")
    print("6. ✅ Allow HTML in fields (checked)")


if __name__ == "__main__":
    main()
