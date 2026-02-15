# JLPT Anki Generator

A Python-based generator that creates Anki flashcard decks for JLPT (Japanese Language Proficiency Test) kanji and vocabulary from dictionary sources. This tool automatically builds decks from the [jmdict-simplified](https://github.com/scriptin/jmdict-simplified) JSON dictionaries, allowing you to:

- **Generate fresh decks** anytime dictionary data is updated
- **Customize output** (include examples, filter by common words, etc.)
- **Rebuild decks** with your own modifications to the Python scripts
- **Stay current** with the latest JMdict/Kanjidic releases

Pre-built decks are included in the `decks/` directory for immediate use, but the real power is in the generator scripts.

## 📦 Contents

### Kanji Decks (5 levels)
- **N5**: 103 kanji (Beginner)
- **N4**: 181 kanji (Basic)
- **N3**: 579 kanji (Intermediate)
- **N2**: 160 kanji (Upper-Intermediate)
- **N1**: 1,207 kanji (Advanced)

**Total**: 2,230 kanji with JLPT levels

**Each kanji card includes:**
- Kanji character
- On'yomi (Chinese-derived) readings
- Kun'yomi (native Japanese) readings
- Name readings (nanori) - important for N1/N2!
- English meanings
- Stroke count
- Radical number
- Frequency rank (newspaper usage)
- Heisig RTK reference numbers (if available)

### Vocabulary Decks with Examples (5 levels)
- **N5**: 7,692 words with 1,595 having examples (20.7%)
- **N4**: 15,130 words with 2,886 having examples (19.1%)
- **N3**: 68,495 words with 10,277 having examples (15.0%)
- **N2**: 12,965 words with 2,152 having examples (16.6%)
- **N1**: 65,099 words with 7,688 having examples (11.8%)
- **Kana-only**: 40,684 words (hiragana/katakana only)
- **Non-JLPT**: 5,076 words (using kanji outside JLPT scope)

**Total**: 215,141 vocabulary entries

**Each vocabulary card includes:**
- Word in kanji (or kana if no kanji)
- Readings
- English meanings with part of speech
- Example sentences from Tatoeba corpus (where available)
- JLPT level tag
- Common word indicator

## 🚀 Quick Start

### Import into Anki

1. Download the CSV files from `decks/kanji/` or `decks/vocab/`
2. Open Anki
3. **File → Import**
4. Select the CSV file
5. **Type**: Basic
6. **Field mapping**:
   - Column 1 → **Front** (kanji/word)
   - Column 2 → **Back** (readings, meanings, examples)
   - Column 3 → **Tags** (JLPT level, grade, etc.)
7. ✅ **Allow HTML in fields** (IMPORTANT!)

## 🛠️ Generating Your Own Decks

### Prerequisites

- Python 3.7+
- JSON dictionary files from [jmdict-simplified releases](https://github.com/scriptin/jmdict-simplified/releases):
  - `kanjidic2-en-3.6.2.json` (for kanji decks)
  - `jmdict-eng-3.6.2.json` (for basic vocab decks)
  - `jmdict-examples-eng-3.6.2.json` (for vocab decks with examples)

**Note for other languages:** To generate decks in other languages (e.g., Russian, German, French, Spanish), select the corresponding JSON files from the [jmdict-simplified releases](https://github.com/scriptin/jmdict-simplified/releases) page (e.g., `jmdict-rus-3.6.2.json`, `jmdict-deu-3.6.2.json`) and follow the same instructions.

### Installation

```bash
# Clone this repo
git clone https://github.com/<username>/jlpt-anki-generator.git
cd jlpt-anki-generator

# Place the JSON files in the scripts/ directory or reference them by path
```

### Generate Kanji Decks

```bash
# Basic usage (uses default kanjidic2-en-3.6.2.json)
python scripts/create_kanji_decks.py

# Custom input/output
python scripts/create_kanji_decks.py -i path/to/kanjidic.json -o my_kanji_decks/
```

### Generate Vocabulary Decks

```bash
# Basic vocabulary decks (no examples)
python scripts/create_vocab_decks.py

# With example sentences (requires jmdict-examples file)
python scripts/create_vocab_decks.py --examples

# Only common words (smaller decks)
python scripts/create_vocab_decks.py --common-only

# With examples AND only common words
python scripts/create_vocab_decks.py --examples --common-only

# Custom paths
python scripts/create_vocab_decks.py \
  --jmdict path/to/jmdict.json \
  --jmdict-examples path/to/jmdict-examples.json \
  --kanjidic path/to/kanjidic.json \
  -o my_output_dir/
```

## 🔄 Updating Decks

When new versions of JMdict or Kanjidic are released, simply:

1. Download the new JSON files from [jmdict-simplified releases](https://github.com/scriptin/jmdict-simplified/releases)
2. Re-run the generator scripts (see commands above)
3. New decks will be created with updated dictionary data

This ensures your Anki decks always contain the most current definitions, readings, and example sentences.

## 📁 Directory Structure

```
jlpt-anki-generator/
├── README.md
├── scripts/
│   ├── jmdict_utils.py          # Shared utilities (don't run directly)
│   ├── create_kanji_decks.py    # Kanji deck generator script
│   └── create_vocab_decks.py    # Vocabulary deck generator script
└── decks/
    ├── kanji/
    │   ├── jlpt_N5_kanji.csv
    │   ├── jlpt_N4_kanji.csv
    │   ├── jlpt_N3_kanji.csv
    │   ├── jlpt_N2_kanji.csv
    │   └── jlpt_N1_kanji.csv
    └── vocab/
        ├── jlpt_N5_vocab_examples.csv
        ├── jlpt_N4_vocab_examples.csv
        ├── jlpt_N3_vocab_examples.csv
        ├── jlpt_N2_vocab_examples.csv
        ├── jlpt_N1_vocab_examples.csv
        ├── jlpt_kana_only_vocab_examples.csv
        └── jlpt_non_jlpt_vocab_examples.csv
```

## 📝 Methodology

### Kanji Level Assignment
Based on the old JLPT system (1-4) mapped to new levels (N1-N5):
- **Level 4** → N5 (easiest)
- **Level 3** → N4
- **Level 2** → N3/N2 (split by grade: 1-6 → N3, 7+ → N2)
- **Level 1** → N1 (hardest)

### Vocabulary Level Assignment
A word is assigned to the **highest (most difficult)** JLPT level of any kanji it contains:
- Example: A word with N5 + N1 kanji → assigned to N1 deck
- This ensures you don't encounter kanji you haven't studied yet
- Kana-only words are in a separate "kana_only" deck

### Data Sources
- **Kanji data**: Kanjidic2 from EDRDG
- **Vocabulary data**: JMdict from EDRDG
- **Example sentences**: Tatoeba Project (Japanese/English pairs)

## 📊 Statistics

| Level | Kanji | Vocab (All) | Vocab (Common Only) | Examples Coverage |
|-------|-------|-------------|---------------------|-------------------|
| N5 | 103 | 7,692 | 983 | 20.7% |
| N4 | 181 | 15,130 | 2,068 | 19.1% |
| N3 | 579 | 68,495 | 7,403 | 15.0% |
| N2 | 160 | 12,965 | 1,331 | 16.6% |
| N1 | 1,207 | 65,099 | 5,890 | 11.8% |

## 🔧 Advanced Usage

### Filtering by Grade
Kanji decks include tags like `grade3`, `grade8` for Kyōiku grade levels.

### Custom Card Templates
The CSV files use HTML formatting (`<b>`, `<br>`). You can customize the appearance by:
1. Importing with "Allow HTML" checked
2. Editing the card template in Anki
3. Adding CSS styling

Example CSS for the back of cards:
```css
.card {
  font-family: "Noto Sans JP", "Hiragino Kaku Gothic", sans-serif;
}
b {
  color: #0066cc;
}
```

## 📄 License

The generated decks are derived from:
- **JMdict/JMnedict**: Property of Electronic Dictionary Research and Development Group (EDRDG)
- **Kanjidic2**: Creative Commons Attribution-ShareAlike License v4.0
- **Tatoeba Examples**: Creative Commons CC-BY 2.0 FR

All derived files are distributed under the same licenses as required by the original sources.

## 🙏 Acknowledgments

- [EDRDG](https://www.edrdg.org/) - JMdict, Kanjidic2, and related projects
- [Tatoeba Project](https://tatoeba.org/) - Example sentences
- [jmdict-simplified](https://github.com/scriptin/jmdict-simplified) - JSON conversion project

## 🤝 Contributing

This is a code-first project. To contribute improvements:
1. Edit the Python generator scripts in `scripts/`
2. Regenerate the decks with your changes
3. Submit a pull request with both script changes and updated decks

Issues and feature requests for the generator scripts are welcome!

## 🐛 Troubleshooting

**Import shows garbled text**: Make sure "Allow HTML in fields" is checked

**Examples not showing**: Only ~17% of words have examples. Check if the word appears in the Tatoeba corpus.

**Missing kanji**: Some kanji don't have JLPT levels assigned. Check the "non_jlpt" vocab deck.

**Large file sizes**: The vocab decks are large. Consider using `--common-only` flag for smaller, more manageable decks.

## 📧 Support

For issues with the generated decks or scripts, please open an issue in this repository.

For questions about the source data (JMdict, Kanjidic2), please refer to the [EDRDG wiki](https://www.edrdg.org/wiki/index.php/Main_Page).
