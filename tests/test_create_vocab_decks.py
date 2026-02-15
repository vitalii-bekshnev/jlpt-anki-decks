#!/usr/bin/env python3
"""
Tests for create_vocab_decks.py
"""

import csv
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from create_vocab_decks import create_vocab_csv, main, parse_args


class TestCreateVocabCsv:
    """Tests for create_vocab_csv function"""

    def test_basic_csv_creation(self, tmp_path):
        """Test creating basic CSV file"""
        output_path = tmp_path / "test.csv"
        words = [
            {
                "word": "学生",
                "readings": "がくせい",
                "senses": "1. (noun) student",
                "is_common": True,
                "form_type": "kanji",
            }
        ]

        create_vocab_csv(words, output_path, "N5", include_examples=False)

        assert output_path.exists()
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["word"] == "学生"
            assert "がくせい" in rows[0]["back"]
            assert "student" in rows[0]["back"]
            assert "N5" in rows[0]["tags"]
            assert "common" in rows[0]["tags"]

    def test_csv_with_examples(self, tmp_path):
        """Test creating CSV with example sentences"""
        output_path = tmp_path / "test_examples.csv"
        words = [
            {
                "word": "学生",
                "readings": "がくせい",
                "senses": "1. (noun) student",
                "examples": "1. 私は学生です。<br>→ I am a student.",
                "is_common": True,
                "form_type": "kanji",
            }
        ]

        create_vocab_csv(words, output_path, "N4", include_examples=True)

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert "Examples:" in rows[0]["back"]
            assert "私は学生です。" in rows[0]["back"]

    def test_csv_without_examples(self, tmp_path):
        """Test creating CSV without example sentences"""
        output_path = tmp_path / "test_no_examples.csv"
        words = [
            {
                "word": "学生",
                "readings": "がくせい",
                "senses": "1. (noun) student",
                "examples": "1. 私は学生です。<br>→ I am a student.",
                "is_common": True,
                "form_type": "kanji",
            }
        ]

        create_vocab_csv(words, output_path, "N3", include_examples=False)

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert "Examples:" not in rows[0]["back"]

    def test_multiple_words(self, tmp_path):
        """Test CSV with multiple words"""
        output_path = tmp_path / "test_multiple.csv"
        words = [
            {
                "word": "学生",
                "readings": "がくせい",
                "senses": "1. (noun) student",
                "is_common": True,
                "form_type": "kanji",
            },
            {
                "word": "先生",
                "readings": "せんせい",
                "senses": "1. (noun) teacher",
                "is_common": True,
                "form_type": "kanji",
            },
        ]

        create_vocab_csv(words, output_path, "N5", include_examples=False)

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["word"] == "学生"
            assert rows[1]["word"] == "先生"

    def test_kana_only_word_tags(self, tmp_path):
        """Test tags for kana-only words"""
        output_path = tmp_path / "test_kana.csv"
        words = [
            {
                "word": "です",
                "readings": "です",
                "senses": "1. (aux-v) to be",
                "is_common": False,
                "form_type": "kana",
            }
        ]

        create_vocab_csv(words, output_path, "kana", include_examples=False)

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert "kana" in rows[0]["tags"]
            assert "common" not in rows[0]["tags"]

    def test_empty_words_list(self, tmp_path):
        """Test creating CSV with empty words list"""
        output_path = tmp_path / "test_empty.csv"
        words = []

        create_vocab_csv(words, output_path, "N1", include_examples=False)

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0

    def test_non_common_word_tags(self, tmp_path):
        """Test tags for non-common words"""
        output_path = tmp_path / "test_non_common.csv"
        words = [
            {
                "word": "罕见",
                "readings": "まれ",
                "senses": "1. (adj) rare",
                "is_common": False,
                "form_type": "kanji",
            }
        ]

        create_vocab_csv(words, output_path, "N1", include_examples=False)

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert "common" not in rows[0]["tags"]
            assert "N1" in rows[0]["tags"]


class TestParseArgs:
    """Tests for parse_args function"""

    def test_default_args(self):
        """Test default argument values"""
        with patch("sys.argv", ["create_vocab_decks.py"]):
            args = parse_args()
            assert args.examples is False
            assert args.jmdict == Path("jmdict-eng-3.6.2.json")
            assert args.jmdict_examples == Path("jmdict-examples-eng-3.6.2.json")
            assert args.kanjidic == Path("kanjidic2-en-3.6.2.json")
            assert args.output_dir is None
            assert args.common_only is False

    def test_examples_flag(self):
        """Test --examples flag"""
        with patch("sys.argv", ["create_vocab_decks.py", "--examples"]):
            args = parse_args()
            assert args.examples is True

    def test_short_examples_flag(self):
        """Test -e short flag"""
        with patch("sys.argv", ["create_vocab_decks.py", "-e"]):
            args = parse_args()
            assert args.examples is True

    def test_custom_jmdict_path(self):
        """Test custom JMdict path"""
        with patch(
            "sys.argv", ["create_vocab_decks.py", "--jmdict", "/path/to/jmdict.json"]
        ):
            args = parse_args()
            assert args.jmdict == Path("/path/to/jmdict.json")

    def test_custom_kanjidic_path(self):
        """Test custom Kanjidic path"""
        with patch(
            "sys.argv",
            ["create_vocab_decks.py", "--kanjidic", "/path/to/kanjidic.json"],
        ):
            args = parse_args()
            assert args.kanjidic == Path("/path/to/kanjidic.json")

    def test_custom_output_dir(self):
        """Test custom output directory"""
        with patch("sys.argv", ["create_vocab_decks.py", "-o", "/path/to/output"]):
            args = parse_args()
            assert args.output_dir == Path("/path/to/output")

    def test_long_output_dir(self):
        """Test --output-dir long form"""
        with patch(
            "sys.argv", ["create_vocab_decks.py", "--output-dir", "/custom/output"]
        ):
            args = parse_args()
            assert args.output_dir == Path("/custom/output")

    def test_common_only_flag(self):
        """Test --common-only flag"""
        with patch("sys.argv", ["create_vocab_decks.py", "--common-only"]):
            args = parse_args()
            assert args.common_only is True

    def test_combined_flags(self):
        """Test multiple flags together"""
        with patch(
            "sys.argv",
            [
                "create_vocab_decks.py",
                "-e",
                "--common-only",
                "-o",
                "decks/",
                "--jmdict",
                "custom.json",
            ],
        ):
            args = parse_args()
            assert args.examples is True
            assert args.common_only is True
            assert args.output_dir == Path("decks/")
            assert args.jmdict == Path("custom.json")


class TestMain:
    """Tests for main function"""

    @pytest.fixture
    def mock_jmdict_data(self):
        """Fixture for mock JMdict data"""
        return {
            "tags": {"n": "noun", "v5r": "Godan verb"},
            "words": [
                {
                    "kanji": [{"text": "学生", "common": True}],
                    "kana": [{"text": "がくせい", "common": True}],
                    "sense": [
                        {
                            "partOfSpeech": ["n"],
                            "gloss": [{"lang": "eng", "text": "student"}],
                        }
                    ],
                },
                {
                    "kanji": [{"text": "食べる", "common": True}],
                    "kana": [{"text": "たべる", "common": True}],
                    "sense": [
                        {
                            "partOfSpeech": ["v5r"],
                            "gloss": [{"lang": "eng", "text": "to eat"}],
                        }
                    ],
                },
            ],
        }

    @pytest.fixture
    def mock_kanjidic_data(self):
        """Fixture for mock Kanjidic data"""
        return {
            "characters": [
                {"literal": "学", "misc": {"jlptLevel": 2, "grade": 5}},
                {"literal": "生", "misc": {"jlptLevel": 4}},
                {"literal": "食", "misc": {"jlptLevel": 3}},
            ]
        }

    def test_main_missing_jmdict_file(self, tmp_path):
        """Test main exits when JMdict file not found"""
        with patch(
            "sys.argv",
            ["create_vocab_decks.py", "--jmdict", str(tmp_path / "nonexistent.json")],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_main_missing_kanjidic_file(self, tmp_path, mock_jmdict_data):
        """Test main exits when Kanjidic file not found"""
        jmdict_file = tmp_path / "jmdict.json"
        jmdict_file.write_text(str(mock_jmdict_data).replace("'", '"'))

        with patch(
            "sys.argv",
            [
                "create_vocab_decks.py",
                "--jmdict",
                str(jmdict_file),
                "--kanjidic",
                str(tmp_path / "nonexistent.json"),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("create_vocab_decks.load_json")
    @patch("create_vocab_decks.create_vocab_csv")
    def test_main_successful_run(
        self,
        mock_create_csv,
        mock_load_json,
        tmp_path,
        mock_jmdict_data,
        mock_kanjidic_data,
    ):
        """Test successful main execution"""
        mock_load_json.side_effect = [mock_kanjidic_data, mock_jmdict_data]

        output_dir = tmp_path / "output"
        jmdict_file = tmp_path / "jmdict.json"
        kanjidic_file = tmp_path / "kanjidic.json"

        # Create empty files (content mocked)
        jmdict_file.write_text("{}")
        kanjidic_file.write_text("{}")

        with patch(
            "sys.argv",
            [
                "create_vocab_decks.py",
                "--jmdict",
                str(jmdict_file),
                "--kanjidic",
                str(kanjidic_file),
                "-o",
                str(output_dir),
            ],
        ):
            main()

        # Check output directory was created
        assert output_dir.exists()

        # Check create_vocab_csv was called for each JLPT level with words
        assert mock_create_csv.called

    @patch("create_vocab_decks.load_json")
    @patch("create_vocab_decks.create_vocab_csv")
    def test_main_common_only_filter(
        self,
        mock_create_csv,
        mock_load_json,
        tmp_path,
        mock_jmdict_data,
        mock_kanjidic_data,
    ):
        """Test main with --common-only filter"""
        mock_load_json.side_effect = [mock_kanjidic_data, mock_jmdict_data]

        output_dir = tmp_path / "output"
        jmdict_file = tmp_path / "jmdict.json"
        kanjidic_file = tmp_path / "kanjidic.json"

        jmdict_file.write_text("{}")
        kanjidic_file.write_text("{}")

        with patch(
            "sys.argv",
            [
                "create_vocab_decks.py",
                "--jmdict",
                str(jmdict_file),
                "--kanjidic",
                str(kanjidic_file),
                "-o",
                str(output_dir),
                "--common-only",
            ],
        ):
            main()

        assert output_dir.exists()
        assert mock_create_csv.called

    @patch("create_vocab_decks.load_json")
    @patch("create_vocab_decks.create_vocab_csv")
    def test_main_with_examples(
        self, mock_create_csv, mock_load_json, tmp_path, mock_kanjidic_data
    ):
        """Test main with --examples flag"""
        mock_jmdict_with_examples = {
            "tags": {"n": "noun"},
            "words": [
                {
                    "kanji": [{"text": "学生", "common": True}],
                    "kana": [{"text": "がくせい", "common": True}],
                    "sense": [
                        {
                            "partOfSpeech": ["n"],
                            "gloss": [{"lang": "eng", "text": "student"}],
                            "examples": [
                                {
                                    "sentences": [
                                        {"lang": "jpn", "text": "私は学生です。"},
                                        {"lang": "eng", "text": "I am a student."},
                                    ]
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        mock_load_json.side_effect = [mock_kanjidic_data, mock_jmdict_with_examples]

        output_dir = tmp_path / "output_examples"
        jmdict_file = tmp_path / "jmdict_examples.json"
        kanjidic_file = tmp_path / "kanjidic.json"

        jmdict_file.write_text("{}")
        kanjidic_file.write_text("{}")

        # When using -e flag, need to specify --jmdict-examples to override the default
        with patch(
            "sys.argv",
            [
                "create_vocab_decks.py",
                "--jmdict-examples",
                str(jmdict_file),
                "--kanjidic",
                str(kanjidic_file),
                "-o",
                str(output_dir),
                "-e",
            ],
        ):
            main()

        assert output_dir.exists()
        assert mock_create_csv.called
