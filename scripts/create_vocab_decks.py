#!/usr/bin/env python3
"""
Generate Anki flashcard decks for JLPT vocabulary from JMdict JSON
Split by JLPT level based on kanji JLPT levels

Usage:
    python create_vocab_decks.py --help
    python create_vocab_decks.py --examples  # Include example sentences
    python create_vocab_decks.py -e -o my_output_dir
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional

from jmdict_utils import (
    load_json,
    build_kanji_jlpt_map,
    get_word_jlpt_level,
    process_word,
)


def create_vocab_csv(
    words: List[Dict], output_path: Path, jlpt_tier: str, include_examples: bool = False
) -> None:
    """Create Anki-compatible CSV file"""
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
        tags_list = [jlpt_tier]
        if word.get("is_common"):
            tags_list.append("common")
        if word.get("form_type"):
            tags_list.append(word["form_type"])

        row = {"word": word["word"], "back": back, "tags": " ".join(tags_list)}
        output_rows.append(row)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Created: {output_path} ({len(words)} cards)")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate JLPT vocabulary Anki decks from JMdict",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Generate decks without examples
  %(prog)s --examples                # Include example sentences
  %(prog)s -e --output-dir decks/    # Custom output directory
  %(prog)s --jmdict path/to/jmdict.json --kanjidic path/to/kanjidic.json
        """,
    )

    parser.add_argument(
        "-e",
        "--examples",
        action="store_true",
        help="Include example sentences from JMdict examples file",
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
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: anki_vocab_jlpt/ or anki_vocab_jlpt_examples/)",
    )

    parser.add_argument(
        "--common-only", action="store_true", help="Only include words marked as common"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Determine which JMdict file to use
    if args.examples:
        jmdict_file = args.jmdict_examples
        default_output = Path("anki_vocab_jlpt_examples")
    else:
        jmdict_file = args.jmdict
        default_output = Path("anki_vocab_jlpt")

    output_dir = args.output_dir or default_output
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

    print("Loading Kanjidic2 (kanji JLPT data)...")
    kanjidic_data = load_json(kanjidic_file)
    kanji_jlpt_map = build_kanji_jlpt_map(kanjidic_data)
    print(f"Loaded {len(kanji_jlpt_map)} kanji with JLPT levels")

    print(
        f"\nLoading JMdict ({'with examples' if args.examples else 'without examples'})..."
    )
    jmdict_data = load_json(jmdict_file)
    tags = jmdict_data.get("tags", {})
    total_entries = len(jmdict_data.get("words", []))
    print(f"Total entries: {total_entries}")

    # Count entries with examples if applicable
    if args.examples:
        words_with_examples = sum(
            1
            for word in jmdict_data.get("words", [])
            if any(
                sense.get("examples") and len(sense["examples"]) > 0
                for sense in word.get("sense", [])
            )
        )
        print(f"Entries with examples: {words_with_examples}")

    # Categorize words by JLPT level
    print("\nCategorizing words by JLPT level...")
    jlpt_groups: Dict[str, List] = {
        "N5": [],
        "N4": [],
        "N3": [],
        "N2": [],
        "N1": [],
        "kana_only": [],
        "non_jlpt": [],
    }

    processed = 0
    skipped = 0

    for word in jmdict_data.get("words", []):
        result = process_word(word, tags, include_examples=args.examples)
        if result:
            # Filter by common-only if requested
            if args.common_only and not result["is_common"]:
                skipped += 1
                continue

            jlpt_level = get_word_jlpt_level(word, kanji_jlpt_map)
            jlpt_groups[jlpt_level].append(result)
            processed += 1
        else:
            skipped += 1

    print(f"Processed: {processed} words")
    if args.common_only:
        print(f"Skipped (not common): {skipped} words")

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print(f"\nGenerating CSV files in {output_dir}...")

    # Generate CSV files for each JLPT level
    for tier in ["N5", "N4", "N3", "N2", "N1"]:
        words = jlpt_groups[tier]
        if words:
            suffix = "_examples" if args.examples else ""
            output_path = output_dir / f"jlpt_{tier}_vocab{suffix}.csv"
            create_vocab_csv(words, output_path, tier, include_examples=args.examples)

    # Also create files for kana-only and non-JLPT words
    if jlpt_groups["kana_only"]:
        suffix = "_examples" if args.examples else ""
        output_path = output_dir / f"jlpt_kana_only_vocab{suffix}.csv"
        create_vocab_csv(
            jlpt_groups["kana_only"],
            output_path,
            "kana",
            include_examples=args.examples,
        )

    if jlpt_groups["non_jlpt"]:
        suffix = "_examples" if args.examples else ""
        output_path = output_dir / f"jlpt_non_jlpt_vocab{suffix}.csv"
        create_vocab_csv(
            jlpt_groups["non_jlpt"],
            output_path,
            "non_jlpt",
            include_examples=args.examples,
        )

    # Summary
    print("\n" + "=" * 60)
    print("VOCABULARY DECKS BY JLPT LEVEL")
    print("=" * 60)
    for tier in ["N5", "N4", "N3", "N2", "N1"]:
        count = len(jlpt_groups[tier])
        print(f"  {tier}: {count} words")
    print(f"\n  Kana-only: {len(jlpt_groups['kana_only'])} words")
    print(f"  Non-JLPT kanji: {len(jlpt_groups['non_jlpt'])} words")

    total = sum(len(jlpt_groups[t]) for t in ["N5", "N4", "N3", "N2", "N1"])
    print(f"\nTotal JLPT words: {total}")
    print(f"Files saved to: {output_dir.absolute()}")

    print("\n" + "=" * 60)
    print("IMPORT INSTRUCTIONS")
    print("=" * 60)
    print("1. Open Anki → File → Import")
    print("2. Select CSV file (e.g., jlpt_N5_vocab.csv)")
    print("3. Type: Basic")
    print("4. Field mapping:")
    print("   - Column 1 (word) → Front")
    print("   - Column 2 (back) → Back")
    print("   - Column 3 (tags) → Tags")
    print("5. ✅ Allow HTML in fields")
    print("\nNote: A word is assigned to the HIGHEST (most difficult)")
    print("JLPT level of any kanji it contains.")

    if args.examples:
        print("\nExamples are from Tatoeba corpus (Japanese/English pairs)")


if __name__ == "__main__":
    main()
