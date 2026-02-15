#!/bin/bash
#
# Generate tiered JLPT Anki decks organized by JLPT level and frequency tier
#
# Uses the create_tiered_decks.py script to generate decks organized as:
#   - JLPT levels: N5, N4, N3, N2, N1
#   - Frequency tiers: Tier 1 (most frequent) to Tier 4 (least frequent)
#
# Output structure:
#   anki_decks_tiered/
#     N5/
#       Tier_1/
#         kanji.csv
#         vocab.csv
#       Tier_2/
#         ...
#     N4/
#       ...
#
# Usage:
#   ./generate_tiered_decks.sh
#   ./generate_tiered_decks.sh -o /path/to/output
#   ./generate_tiered_decks.sh --no-examples
#   ./generate_tiered_decks.sh --common-only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/anki_decks_tiered"
NO_EXAMPLES=""
COMMON_ONLY=""
TIER_STRATEGY=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --no-examples)
            NO_EXAMPLES="--no-examples"
            shift
            ;;
        --common-only)
            COMMON_ONLY="--common-only"
            shift
            ;;
        --tier-strategy)
            TIER_STRATEGY="--tier-strategy $2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -o, --output-dir DIR     Output directory (default: ./anki_decks_tiered)"
            echo "  --no-examples            Exclude example sentences from vocabulary decks"
            echo "  --common-only            Only include words marked as common"
            echo "  --tier-strategy STRATEGY Strategy for calculating word frequency tier"
            echo "                           (conservative|average|first, default: conservative)"
            echo "  -h, --help               Show this help message"
            echo ""
            echo "Generates:"
            echo "  - Tiered kanji decks organized by JLPT level and frequency tier"
            echo "  - Tiered vocabulary decks with sentence examples"
            echo ""
            echo "Tier Strategy:"
            echo "  conservative: Use highest tier (least frequent kanji) - safest for learning"
            echo "  average:      Round up average of all kanji tiers"
            echo "  first:        Use only the first kanji's tier"
            echo ""
            echo "Directory Structure:"
            echo "  {output_dir}/"
            echo "    N5/"
            echo "      Tier_1/ (most frequent)"
            echo "        kanji.csv"
            echo "        vocab.csv"
            echo "      Tier_2/"
            echo "      Tier_3/"
            echo "      Tier_4/ (least frequent)"
            echo "    N4/"
            echo "    N3/"
            echo "    N2/"
            echo "    N1/"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo "======================================"
echo "Generating Tiered JLPT Anki Decks"
echo "======================================"
echo ""
echo "Output directory: ${OUTPUT_DIR}"
if [[ -n "$NO_EXAMPLES" ]]; then
    echo "Examples: Excluded"
else
    echo "Examples: Included (default)"
fi
if [[ -n "$COMMON_ONLY" ]]; then
    echo "Words: Common only"
fi
if [[ -n "$TIER_STRATEGY" ]]; then
    echo "Tier strategy: ${TIER_STRATEGY#--tier-strategy }"
else
    echo "Tier strategy: conservative (default)"
fi
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Generate tiered decks
echo "======================================"
echo "Generating Tiered Kanji and Vocab Decks"
echo "======================================"
echo ""

python3 "${SCRIPT_DIR}/scripts/create_tiered_decks.py" \
    --output-dir "${OUTPUT_DIR}" \
    --jmdict "${SCRIPT_DIR}/jmdict-eng-3.6.2.json" \
    --jmdict-examples "${SCRIPT_DIR}/jmdict-examples-eng-3.6.2.json" \
    --kanjidic "${SCRIPT_DIR}/kanjidic2-en-3.6.2.json" \
    ${NO_EXAMPLES} \
    ${COMMON_ONLY} \
    ${TIER_STRATEGY}

echo ""
echo "======================================"
echo "Generation Complete!"
echo "======================================"
echo ""
echo "Decks created in: ${OUTPUT_DIR}"
echo ""
echo "Structure:"
echo "  ${OUTPUT_DIR}/"
echo "    N5/"
echo "      Tier_1/kanji.csv vocab.csv (most frequent)"
echo "      Tier_2/kanji.csv vocab.csv"
echo "      Tier_3/kanji.csv vocab.csv"
echo "      Tier_4/kanji.csv vocab.csv (least frequent)"
echo "    N4/"
echo "      Tier_1/ ... Tier_4/"
echo "    N3/"
echo "      Tier_1/ ... Tier_4/"
echo "    N2/"
echo "      Tier_1/ ... Tier_4/"
echo "    N1/"
echo "      Tier_1/ ... Tier_4/"
echo ""
echo "Tier Information:"
echo "  Tier 1: Top 25% most frequent kanji/words"
echo "  Tier 2: 25-50% frequency range"
echo "  Tier 3: 50-75% frequency range"
echo "  Tier 4: Bottom 25% least frequent"
echo ""
echo "Import Instructions:"
echo "  1. Open Anki → File → Import"
echo "  2. Navigate to the desired Tier folder"
echo "  3. Select kanji.csv or vocab.csv"
echo "  4. Type: Basic"
echo "  5. Map: Column 1 → Front, Column 2 → Back, Column 3 → Tags"
echo "  6. Check: Allow HTML in fields"
echo ""
