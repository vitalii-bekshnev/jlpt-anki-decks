# JLPT Anki Decks (JLPT Anki Generator)

Free Anki flashcard decks for JLPT (Japanese Language Proficiency Test) study. Includes kanji and vocabulary for all levels (N5-N1).

## Examples

<table>
  <tr>
    <td align="center"><b>Kanji Card</b></td>
    <td align="center"><b>Vocabulary Card</b></td>
  </tr>
  <tr>
    <td><img src="docs/kanji_example.png" width="400"/></td>
    <td><img src="docs/vocab_example.png" width="400"/></td>
  </tr>
</table>

## 📥 Quick Start

1. Go to [Releases](../../releases) and download the latest release
2. Choose the decks you need (you don't have to download everything):
   - **General decks**: All kanji or vocab for a specific JLPT level
   - **Tiered decks**: Divided into 4 frequency tiers per level
3. Extract the CSV file(s) from the archive
4. Open Anki → File → Import → select the CSV
5. ✅ Check "Allow HTML in fields" (important!)
6. Click Import

That's it! Your deck is ready to study.

## 📦 What's Included

### Kanji Decks

Learn kanji with readings, meanings, stroke counts, and more.

| Level | Kanji | Description |
|-------|-------|-------------|
| N5 | 103 | Beginner level |
| N4 | 181 | Basic level |
| N3 | 579 | Intermediate |
| N2 | 160 | Upper-intermediate |
| N1 | 1,207 | Advanced |

**Each kanji card shows:**
- The kanji character
- Readings (on'yomi and kun'yomi)
- Meanings in English
- Stroke count
- Frequency rank (how common it is)

### Vocabulary Decks

Learn words with example sentences.

| Level | Words | With Examples |
|-------|-------|---------------|
| N5 | ~7,700 | ~1,600 examples |
| N4 | ~15,100 | ~2,900 examples |
| N3 | ~68,500 | ~10,300 examples |
| N2 | ~13,000 | ~2,150 examples |
| N1 | ~65,100 | ~7,700 examples |
| Kana-only | ~40,700 | Words written only in hiragana/katakana |
| Non-JLPT | ~5,100 | Words with kanji outside JLPT scope |

**Each vocabulary card shows:**
- The word (kanji or kana)
- Readings
- English meanings
- Example sentences (when available)
- JLPT level tag

### Tiered Decks (Advanced)

Want to focus on the most common words first? Use tiered decks!

Each JLPT level is split into 4 frequency tiers:
- **Tier 1**: Top 25% most common (start here!)
- **Tier 2**: 25-50% frequency
- **Tier 3**: 50-75% frequency
- **Tier 4**: Bottom 25% least common

This helps you learn the most useful words first within each level.

## 🔄 How Releases Work

New decks are automatically built and released monthly:

1. **Check for updates**: The system checks for new dictionary data from JMdict
2. **Generate decks**: Creates kanji and vocabulary decks for all JLPT levels
3. **Create archives**: Packages everything into easy-to-download files
4. **Publish**: Uploads to GitHub Releases with version numbers

**Version numbers** match the dictionary version (e.g., `3.6.2+20260209125202`), so you know exactly which dictionary data your cards come from.

**Release schedule**: First of every month (or whenever dictionary data updates).

## 🌍 Other Languages

Want decks in your language? The generator supports many languages!

**Available languages** (check the [jmdict-simplified releases](https://github.com/scriptin/jmdict-simplified/releases)):
- Russian (`jmdict-rus`)
- German (`jmdict-deu`)
- French (`jmdict-fra`)
- Spanish (`jmdict-spa`)
- Portuguese (`jmdict-por`)
- Italian (`jmdict-ita`)
- Dutch (`jmdict-dut`)
- And more!

### Generate Decks in Your Language

**Option 1: Download Pre-built (if available)**
Check if someone has already built decks for your language in the releases.

**Option 2: Build Yourself**

1. Install Python 3.7 or higher
2. Download the JSON files for your language from [jmdict-simplified releases](https://github.com/scriptin/jmdict-simplified/releases):
   - `kanjidic2-[lang]-[version].json` (kanji)
   - `jmdict-[lang]-[version].json` (vocabulary)
   - `jmdict-examples-[lang]-[version].json` (examples - optional)
3. Clone this repository
4. Run the generator:

```bash
# For kanji decks
python scripts/create_kanji_decks.py -i path/to/kanjidic2-[lang].json

# For vocabulary decks with examples
python scripts/create_vocab_decks.py \
  --jmdict path/to/jmdict-[lang].json \
  --jmdict-examples path/to/jmdict-examples-[lang].json \
  --kanjidic path/to/kanjidic2-[lang].json
```

The generated CSV files will be in the `decks/` folder, ready to import into Anki.

## ⚠️ Troubleshooting

**Import shows weird characters?**
→ Make sure "Allow HTML in fields" is checked when importing

**Missing example sentences?**
→ Only ~17% of words have examples. Common words are more likely to have them.

**Files are too big?**
→ Download only the specific level you need, or use tiered decks to start with common words only.

**Can't find a specific kanji?**
→ It might be in the "non-JLPT" vocab deck if it doesn't have an official JLPT level assigned.

## 📊 How Cards Are Organized

### Kanji Levels
Based on the old JLPT system mapped to new levels:
- Old Level 4 → N5 (easiest)
- Old Level 3 → N4
- Old Level 2 → N3 or N2 (split by grade)
- Old Level 1 → N1 (hardest)

### Vocabulary Levels
Words are assigned to the **highest** JLPT level of any kanji they contain:
- Example: A word with N5 + N1 kanji → N1 deck
- This prevents you from seeing kanji you haven't studied yet
- Kana-only words go in a separate "kana_only" deck

## 📄 License

These decks are derived from:
- **JMdict**: Electronic Dictionary Research and Development Group (EDRDG)
- **Kanjidic2**: Creative Commons Attribution-ShareAlike License v4.0
- **Tatoeba Examples**: Creative Commons CC-BY 2.0 FR

## 🙏 Acknowledgments

- [EDRDG](https://www.edrdg.org/) - Dictionary data
- [Tatoeba Project](https://tatoeba.org/) - Example sentences
- [jmdict-simplified](https://github.com/scriptin/jmdict-simplified) - JSON conversion

---

## 🛠️ Technical Details

For developers and advanced users who want to customize or contribute.

### Project Structure

```
jlpt-anki-generator/
├── scripts/
│   ├── create_kanji_decks.py      # Kanji deck generator
│   ├── create_vocab_decks.py      # Vocabulary deck generator
│   ├── create_tiered_decks.py     # Tiered/frequency-based decks
│   └── jmdict_utils.py            # Shared utilities
├── .github/workflows/
│   └── build-and-release.yml      # Automated release workflow
└── decks/                         # Generated decks (output)
```

### Automated Workflow

The `.github/workflows/build-and-release.yml` file defines a GitHub Actions workflow that:

1. Fetches the latest dictionary release from [jmdict-simplified](https://github.com/scriptin/jmdict-simplified)
2. Downloads the required JSON files (kanjidic2, JMdict, examples)
3. Generates kanji decks using `create_kanji_decks.py`
4. Generates vocabulary decks using `create_vocab_decks.py`
5. Generates tiered decks using `create_tiered_decks.py`
6. Creates tar.gz and zip archives for each deck type
7. Publishes a GitHub release with all archives

**Triggers:**
- Monthly (1st of each month via cron)
- Manual trigger (workflow_dispatch)
- Push to main/master (when workflow file changes)

### Prerequisites for Local Generation

- Python 3.7+
- JSON dictionary files from [jmdict-simplified releases](https://github.com/scriptin/jmdict-simplified/releases)

### Script Options

**Kanji Decks:**
```bash
python scripts/create_kanji_decks.py -i input.json -o output_dir/
```

**Vocabulary Decks:**
```bash
python scripts/create_vocab_decks.py \
  --jmdict path/to/jmdict.json \
  --jmdict-examples path/to/examples.json \
  --kanjidic path/to/kanjidic.json \
  --output-dir my_decks/ \
  --examples          # Include example sentences
  --common-only       # Only common words
```

**Tiered Decks:**
```bash
python scripts/create_tiered_decks.py \
  --jmdict path/to/jmdict.json \
  --jmdict-examples path/to/examples.json \
  --kanjidic path/to/kanjidic.json \
  --output-dir tiered_decks/
```

### Customizing Output

The CSV files use HTML formatting. You can customize appearance by:
1. Editing the Python scripts to change field formatting
2. Modifying Anki card templates after import
3. Adding CSS to your Anki card styling

Example CSS:
```css
.card {
  font-family: "Noto Sans JP", sans-serif;
}
b { color: #0066cc; }
```

### Contributing

1. Fork the repository
2. Make changes to the Python scripts
3. Test by generating decks locally
4. Submit a pull request

Issues and feature requests welcome!
