#!/usr/bin/env python3
"""
Tests for create_kanji_decks.py
"""

import csv
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from create_kanji_decks import (
    create_anki_csv,
    extract_dict_reference,
    extract_meanings,
    extract_nanori,
    extract_readings,
    format_back_field,
    load_kanjidic,
    main,
    parse_args,
    process_character,
)


class TestLoadKanjidic:
    """Tests for load_kanjidic function"""

    def test_load_valid_json(self, tmp_path):
        """Test loading valid JSON file"""
        test_file = tmp_path / "kanjidic.json"
        test_data = {"characters": [{"literal": "一"}]}
        test_file.write_text(json.dumps(test_data))

        result = load_kanjidic(test_file)
        assert result == test_data

    def test_file_not_found(self, tmp_path):
        """Test FileNotFoundError handling"""
        test_file = tmp_path / "nonexistent.json"

        with pytest.raises(SystemExit) as exc_info:
            load_kanjidic(test_file)
        assert exc_info.value.code == 1

    def test_invalid_json(self, tmp_path):
        """Test JSONDecodeError handling"""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{invalid json}")

        with pytest.raises(SystemExit) as exc_info:
            load_kanjidic(test_file)
        assert exc_info.value.code == 1


class TestExtractReadings:
    """Tests for extract_readings function"""

    def test_no_reading_meaning(self):
        """Test with None reading_meaning"""
        on, kun = extract_readings(None)
        assert on == []
        assert kun == []

    def test_no_groups(self):
        """Test with reading_meaning but no groups"""
        reading_meaning = {}
        on, kun = extract_readings(reading_meaning)
        assert on == []
        assert kun == []

    def test_on_readings_only(self):
        """Test extracting on'yomi readings"""
        reading_meaning = {
            "groups": [
                {
                    "readings": [
                        {"type": "ja_on", "value": "イチ"},
                        {"type": "ja_on", "value": "イツ"},
                    ]
                }
            ]
        }
        on, kun = extract_readings(reading_meaning)
        assert on == ["イチ", "イツ"]
        assert kun == []

    def test_kun_readings_only(self):
        """Test extracting kun'yomi readings"""
        reading_meaning = {
            "groups": [
                {
                    "readings": [
                        {"type": "ja_kun", "value": "ひと"},
                        {"type": "ja_kun", "value": "ひと.つ"},
                    ]
                }
            ]
        }
        on, kun = extract_readings(reading_meaning)
        assert on == []
        assert kun == ["ひと", "ひと.つ"]

    def test_mixed_readings(self):
        """Test extracting both on and kun readings"""
        reading_meaning = {
            "groups": [
                {
                    "readings": [
                        {"type": "ja_on", "value": "ガク"},
                        {"type": "ja_kun", "value": "まな.ぶ"},
                    ]
                }
            ]
        }
        on, kun = extract_readings(reading_meaning)
        assert on == ["ガク"]
        assert kun == ["まな.ぶ"]

    def test_multiple_groups(self):
        """Test extracting readings from multiple groups"""
        reading_meaning = {
            "groups": [
                {"readings": [{"type": "ja_on", "value": "コウ"}]},
                {"readings": [{"type": "ja_kun", "value": "いえ"}]},
            ]
        }
        on, kun = extract_readings(reading_meaning)
        assert on == ["コウ"]
        assert kun == ["いえ"]

    def test_unknown_reading_type(self):
        """Test handling unknown reading types"""
        reading_meaning = {
            "groups": [{"readings": [{"type": "pinyin", "value": "yi"}]}]
        }
        on, kun = extract_readings(reading_meaning)
        assert on == []
        assert kun == []


class TestExtractMeanings:
    """Tests for extract_meanings function"""

    def test_no_reading_meaning(self):
        """Test with None reading_meaning"""
        result = extract_meanings(None)
        assert result == []

    def test_single_meaning(self):
        """Test extracting single meaning"""
        reading_meaning = {"groups": [{"meanings": [{"lang": "en", "value": "one"}]}]}
        result = extract_meanings(reading_meaning)
        assert result == ["one"]

    def test_multiple_meanings(self):
        """Test extracting multiple meanings"""
        reading_meaning = {
            "groups": [
                {
                    "meanings": [
                        {"lang": "en", "value": "study"},
                        {"lang": "en", "value": "learning"},
                    ]
                }
            ]
        }
        result = extract_meanings(reading_meaning)
        assert result == ["study", "learning"]

    def test_non_english_meanings_filtered(self):
        """Test filtering non-English meanings"""
        reading_meaning = {
            "groups": [
                {
                    "meanings": [
                        {"lang": "en", "value": "school"},
                        {"lang": "ger", "value": "Schule"},
                        {"lang": "en", "value": "academy"},
                    ]
                }
            ]
        }
        result = extract_meanings(reading_meaning)
        assert result == ["school", "academy"]

    def test_default_language_english(self):
        """Test that meanings without lang default to English"""
        reading_meaning = {"groups": [{"meanings": [{"value": "book"}]}]}
        result = extract_meanings(reading_meaning)
        assert result == ["book"]

    def test_multiple_groups(self):
        """Test extracting meanings from multiple groups"""
        reading_meaning = {
            "groups": [
                {"meanings": [{"lang": "en", "value": "water"}]},
                {"meanings": [{"lang": "en", "value": "Wednesday"}]},
            ]
        }
        result = extract_meanings(reading_meaning)
        assert result == ["water", "Wednesday"]

    def test_empty_meanings(self):
        """Test handling empty meanings"""
        reading_meaning = {"groups": [{"meanings": []}]}
        result = extract_meanings(reading_meaning)
        assert result == []


class TestExtractDictReference:
    """Tests for extract_dict_reference function"""

    def test_find_heisig(self):
        """Test finding Heisig reference"""
        dict_refs = [
            {"type": "heisig", "value": "1"},
            {"type": "nelson_c", "value": "100"},
        ]
        result = extract_dict_reference(dict_refs, "heisig")
        assert result == "1"

    def test_find_heisig6(self):
        """Test finding Heisig6 reference"""
        dict_refs = [
            {"type": "heisig", "value": "1"},
            {"type": "heisig6", "value": "2"},
        ]
        result = extract_dict_reference(dict_refs, "heisig6")
        assert result == "2"

    def test_reference_not_found(self):
        """Test when reference type not found"""
        dict_refs = [{"type": "nelson_c", "value": "100"}]
        result = extract_dict_reference(dict_refs, "heisig")
        assert result is None

    def test_empty_dict_refs(self):
        """Test with empty dictionary references"""
        result = extract_dict_reference([], "heisig")
        assert result is None


class TestExtractNanori:
    """Tests for extract_nanori function"""

    def test_no_reading_meaning(self):
        """Test with None reading_meaning"""
        result = extract_nanori(None)
        assert result == []

    def test_with_nanori(self):
        """Test extracting nanori readings"""
        reading_meaning = ({"nanori": ["かず", "い", "いっ", "いと", "かつ"]},)
        # Fix: reading_meaning should be a dict, not a tuple
        reading_meaning = {"nanori": ["かず", "い", "いっ", "いと", "かつ"]}
        result = extract_nanori(reading_meaning)
        assert result == ["かず", "い", "いっ", "いと", "かつ"]

    def test_empty_nanori(self):
        """Test with empty nanori list"""
        reading_meaning = {"nanori": []}
        result = extract_nanori(reading_meaning)
        assert result == []


class TestProcessCharacter:
    """Tests for process_character function"""

    def test_complete_character(self):
        """Test processing complete character data"""
        char = {
            "literal": "学",
            "misc": {
                "jlptLevel": 2,
                "strokeCounts": [8],
                "grade": 5,
                "frequency": 348,
            },
            "readingMeaning": {
                "groups": [
                    {
                        "readings": [
                            {"type": "ja_on", "value": "ガク"},
                            {"type": "ja_kun", "value": "まな.ぶ"},
                        ],
                        "meanings": [{"lang": "en", "value": "study"}],
                    }
                ],
                "nanori": ["たか"],
            },
            "radicals": [{"value": "子"}],
            "dictionaryReferences": [
                {"type": "heisig", "value": "1"},
                {"type": "heisig6", "value": "2"},
            ],
        }

        result = process_character(char)

        assert result["kanji"] == "学"
        assert result["jlpt_level"] == 2
        assert result["on_readings"] == "ガク"
        assert result["kun_readings"] == "まな.ぶ"
        assert result["meanings"] == "study"
        assert result["stroke_count"] == 8
        assert result["grade"] == 5
        assert result["frequency"] == 348
        assert result["radical"] == "子"
        assert result["nanori"] == "たか"
        assert result["heisig_rtk"] == "1"
        assert result["heisig6_rtk"] == "2"

    def test_no_literal_returns_none(self):
        """Test character without literal returns None"""
        char = {"misc": {"jlptLevel": 4}}
        result = process_character(char)
        assert result is None

    def test_no_jlpt_level_returns_none(self):
        """Test character without JLPT level returns None"""
        char = {"literal": "一", "misc": {"grade": 1}}
        result = process_character(char)
        assert result is None

    def test_minimal_character(self):
        """Test processing character with minimal data"""
        char = {
            "literal": "一",
            "misc": {"jlptLevel": 4},
            "readingMeaning": {"groups": []},
            "radicals": [],
            "dictionaryReferences": [],
        }

        result = process_character(char)

        assert result["kanji"] == "一"
        assert result["jlpt_level"] == 4
        assert result["on_readings"] == ""
        assert result["kun_readings"] == ""
        assert result["meanings"] == ""
        assert result["stroke_count"] is None
        assert result["grade"] is None
        assert result["frequency"] is None
        assert result["radical"] is None
        assert result["nanori"] == ""
        assert result["heisig_rtk"] == ""
        assert result["heisig6_rtk"] == ""

    def test_multiple_stroke_counts(self):
        """Test using first stroke count when multiple exist"""
        char = {
            "literal": "一",
            "misc": {"jlptLevel": 4, "strokeCounts": [1, 2, 3]},
        }

        result = process_character(char)
        assert result["stroke_count"] == 1


class TestFormatBackField:
    """Tests for format_back_field function"""

    def test_complete_character(self):
        """Test formatting complete character data"""
        char = {
            "kanji": "学",
            "meanings": "study; learning",
            "on_readings": "ガク",
            "kun_readings": "まな.ぶ",
            "nanori": "たか",
            "stroke_count": 8,
            "radical": "子",
            "frequency": 348,
            "heisig_rtk": "1",
            "heisig6_rtk": "2",
        }

        result = format_back_field(char)

        assert "Meanings:" in result
        assert "study; learning" in result
        assert "On'yomi:" in result
        assert "ガク" in result
        assert "Kun'yomi:" in result
        assert "まな.ぶ" in result
        assert "Name readings:" in result
        assert "たか" in result
        assert "Stats:" in result
        assert "Strokes: 8" in result
        assert "Radical: 子" in result
        assert "Freq: #348" in result
        assert "Heisig:" in result
        assert "RTK: #1" in result
        assert "RTK6: #2" in result

    def test_no_optional_fields(self):
        """Test formatting with minimal data"""
        char = {
            "kanji": "一",
            "meanings": "one",
            "on_readings": "イチ; イツ",
            "kun_readings": "ひと; ひと.つ",
        }

        result = format_back_field(char)

        assert "Meanings:" in result
        assert "On'yomi:" in result
        assert "Kun'yomi:" in result
        assert "Name readings:" not in result
        assert "Stats:" not in result
        assert "Heisig:" not in result

    def test_only_meanings(self):
        """Test formatting with only meanings"""
        char = {"kanji": "一", "meanings": "one"}

        result = format_back_field(char)
        assert result == "<b>Meanings:</b> one"


class TestCreateAnkiCsv:
    """Tests for create_anki_csv function"""

    def test_basic_csv_creation(self, tmp_path):
        """Test creating basic kanji CSV file"""
        output_path = tmp_path / "test.csv"
        characters = [
            {
                "kanji": "一",
                "meanings": "one",
                "on_readings": "イチ",
                "kun_readings": "ひと",
                "grade": 1,
            }
        ]

        create_anki_csv(characters, output_path, "N5")

        assert output_path.exists()
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["kanji"] == "一"
            assert "one" in rows[0]["back"]
            assert "N5" in rows[0]["tags"]
            assert "grade1" in rows[0]["tags"]

    def test_multiple_characters(self, tmp_path):
        """Test CSV with multiple characters"""
        output_path = tmp_path / "test.csv"
        characters = [
            {"kanji": "一", "meanings": "one", "grade": 1},
            {"kanji": "二", "meanings": "two", "grade": 1},
            {"kanji": "三", "meanings": "three", "grade": 1},
        ]

        create_anki_csv(characters, output_path, "N5")

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3
            assert rows[0]["kanji"] == "一"
            assert rows[1]["kanji"] == "二"
            assert rows[2]["kanji"] == "三"

    def test_no_grade(self, tmp_path):
        """Test CSV without grade information"""
        output_path = tmp_path / "test.csv"
        characters = [{"kanji": "一", "meanings": "one"}]

        create_anki_csv(characters, output_path, "N5")

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert (
                "grade" not in rows[0]["tags"] or "grade" not in rows[0]["tags"].split()
            )
            assert "N5" in rows[0]["tags"]

    def test_empty_characters_list(self, tmp_path):
        """Test creating CSV with empty characters list"""
        output_path = tmp_path / "test.csv"
        characters = []

        create_anki_csv(characters, output_path, "N1")

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0


class TestParseArgs:
    """Tests for parse_args function"""

    def test_default_args(self):
        """Test default argument values"""
        with patch("sys.argv", ["create_kanji_decks.py"]):
            args = parse_args()
            assert args.input == Path("kanjidic2-en-3.6.2.json")
            assert args.output_dir == Path("anki_decks")

    def test_custom_input(self):
        """Test custom input file"""
        with patch(
            "sys.argv", ["create_kanji_decks.py", "-i", "/path/to/kanjidic.json"]
        ):
            args = parse_args()
            assert args.input == Path("/path/to/kanjidic.json")

    def test_custom_output_dir(self):
        """Test custom output directory"""
        with patch("sys.argv", ["create_kanji_decks.py", "-o", "/path/to/output"]):
            args = parse_args()
            assert args.output_dir == Path("/path/to/output")

    def test_long_form_args(self):
        """Test long form arguments"""
        with patch(
            "sys.argv",
            [
                "create_kanji_decks.py",
                "--input",
                "custom.json",
                "--output-dir",
                "custom_output/",
            ],
        ):
            args = parse_args()
            assert args.input == Path("custom.json")
            assert args.output_dir == Path("custom_output/")


class TestMain:
    """Tests for main function"""

    @pytest.fixture
    def mock_kanjidic_data(self):
        """Fixture for mock Kanjidic data"""
        return {
            "characters": [
                {
                    "literal": "一",
                    "misc": {"jlptLevel": 4, "strokeCounts": [1], "grade": 1},
                    "readingMeaning": {
                        "groups": [
                            {
                                "readings": [
                                    {"type": "ja_on", "value": "イチ"},
                                    {"type": "ja_kun", "value": "ひと"},
                                ],
                                "meanings": [{"lang": "en", "value": "one"}],
                            }
                        ]
                    },
                    "radicals": [{"value": "一"}],
                    "dictionaryReferences": [],
                },
                {
                    "literal": "食",
                    "misc": {"jlptLevel": 3, "strokeCounts": [9], "grade": 3},
                    "readingMeaning": {
                        "groups": [
                            {
                                "readings": [
                                    {"type": "ja_on", "value": "ショク"},
                                    {"type": "ja_kun", "value": "た.べる"},
                                ],
                                "meanings": [{"lang": "en", "value": "eat"}],
                            }
                        ]
                    },
                    "radicals": [{"value": "食"}],
                    "dictionaryReferences": [],
                },
            ]
        }

    def test_main_missing_input_file(self, tmp_path):
        """Test main exits when input file not found"""
        with patch(
            "sys.argv",
            ["create_kanji_decks.py", "-i", str(tmp_path / "nonexistent.json")],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("create_kanji_decks.load_kanjidic")
    @patch("create_kanji_decks.create_anki_csv")
    def test_main_successful_run(
        self, mock_create_csv, mock_load_kanjidic, tmp_path, mock_kanjidic_data
    ):
        """Test successful main execution"""
        mock_load_kanjidic.return_value = mock_kanjidic_data

        output_dir = tmp_path / "output"
        input_file = tmp_path / "kanjidic.json"
        input_file.write_text("{}")

        with patch(
            "sys.argv",
            ["create_kanji_decks.py", "-i", str(input_file), "-o", str(output_dir)],
        ):
            main()

        # Check output directory was created
        assert output_dir.exists()

        # Check create_anki_csv was called
        assert mock_create_csv.called

    @patch("create_kanji_decks.load_kanjidic")
    def test_main_invalid_data_structure(self, mock_load_kanjidic, tmp_path):
        """Test main exits with invalid data structure"""
        mock_load_kanjidic.return_value = {
            "invalid": "data"
        }  # Missing 'characters' key

        input_file = tmp_path / "kanjidic.json"
        input_file.write_text("{}")
        output_dir = tmp_path / "output"

        with patch(
            "sys.argv",
            ["create_kanji_decks.py", "-i", str(input_file), "-o", str(output_dir)],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("create_kanji_decks.load_kanjidic")
    @patch("create_kanji_decks.create_anki_csv")
    def test_main_jlpt_level_grouping(
        self, mock_create_csv, mock_load_kanjidic, tmp_path, mock_kanjidic_data
    ):
        """Test that kanji are grouped by JLPT level correctly"""
        mock_load_kanjidic.return_value = mock_kanjidic_data

        output_dir = tmp_path / "output"
        input_file = tmp_path / "kanjidic.json"
        input_file.write_text("{}")

        with patch(
            "sys.argv",
            ["create_kanji_decks.py", "-i", str(input_file), "-o", str(output_dir)],
        ):
            main()

        # Check that create_anki_csv was called for each JLPT level
        call_args_list = mock_create_csv.call_args_list
        # Should be called for N5 and N4 (from level 4 and 3)
        tiers_called = [call[0][2] for call in call_args_list]
        assert "N5" in tiers_called
        assert "N4" in tiers_called
