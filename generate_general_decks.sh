#!/bin/bash
#
# Generate general (non-tiered) JLPT Anki decks organized by JLPT level only
#
# Uses existing Python scripts:
#   - create_kanji_decks.py: Generates kanji decks (N5-N1)
#   - create_vocab_decks.py: Generates vocabulary decks with sentence examples (N5-N1)
#
# Output structure:
#   anki_decks_general/
#     kanji/           - Kanji decks by JLPT level
#     vocabulary/      - Vocabulary decks with sentence examples by JLPT level
#
# Usage:
#   ./generate_general_decks.sh
#   ./generate_general_decks.sh -o /path/to/output

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/anki_decks_general"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -o, --output-dir DIR  Output directory (default: ./anki_decks_general)"
            echo "  -h, --help            Show this help message"
            echo ""
            echo "Generates:"
            echo "  - Kanji decks by JLPT level (N5-N1)"
            echo "  - Vocabulary decks with sentence examples by JLPT level (N5-N1)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

KANJI_OUTPUT="${OUTPUT_DIR}/kanji"
VOCAB_OUTPUT="${OUTPUT_DIR}/vocabulary"

echo "======================================"
echo "Generating General JLPT Anki Decks"
echo "======================================"
echo ""
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Create output directories
mkdir -p "${KANJI_OUTPUT}"
mkdir -p "${VOCAB_OUTPUT}"

# Generate Kanji decks
echo "======================================"
echo "Generating Kanji Decks with Word Examples"
echo "======================================"
echo ""

python3 "${SCRIPT_DIR}/scripts/create_kanji_decks.py" \
    --input "${SCRIPT_DIR}/kanjidic2-en-3.6.2.json" \
    --jmdict "${SCRIPT_DIR}/jmdict-eng-3.6.2.json" \
    --max-examples 3 \
    --output-dir "${KANJI_OUTPUT}"

echo ""

# Generate Vocabulary decks with sentence examples
echo "======================================"
echo "Generating Vocabulary Decks with Examples"
echo "======================================"
echo ""

python3 "${SCRIPT_DIR}/scripts/create_vocab_decks.py" \
    --examples \
    --jmdict-examples "${SCRIPT_DIR}/jmdict-examples-eng-3.6.2.json" \
    --kanjidic "${SCRIPT_DIR}/kanjidic2-en-3.6.2.json" \
    --output-dir "${VOCAB_OUTPUT}"

echo ""
echo "======================================"
echo "Generation Complete!"
echo "======================================"
echo ""
echo "Decks created in: ${OUTPUT_DIR}"
echo ""
echo "Structure:"
echo "  ${OUTPUT_DIR}/"
echo "    kanji/"
echo "      jlpt_N5_kanji.csv"
echo "      jlpt_N4_kanji.csv"
echo "      jlpt_N3_kanji.csv"
echo "      jlpt_N2_kanji.csv"
echo "      jlpt_N1_kanji.csv"
echo "    vocabulary/"
echo "      jlpt_N5_vocab_examples.csv"
echo "      jlpt_N4_vocab_examples.csv"
echo "      jlpt_N3_vocab_examples.csv"
echo "      jlpt_N2_vocab_examples.csv"
echo "      jlpt_N1_vocab_examples.csv"
echo "      jlpt_kana_only_vocab_examples.csv"
echo "      jlpt_non_jlpt_vocab_examples.csv"
echo ""
