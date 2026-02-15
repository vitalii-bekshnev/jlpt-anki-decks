#!/usr/bin/env python3
"""
Tests for jmdict_utils.py
"""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from jmdict_utils import (
    build_kanji_jlpt_map,
    format_examples,
    format_sense,
    get_primary_form,
    get_readings,
    get_word_jlpt_level,
    is_common_word,
    load_json,
    process_word,
)


class TestLoadJson:
    """Tests for load_json function"""

    def test_load_json_success(self, tmp_path):
        """Test successful JSON loading"""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        test_file.write_text(json.dumps(test_data))

        result = load_json(test_file)
        assert result == test_data

    def test_load_json_file_not_found(self, tmp_path):
        """Test FileNotFoundError handling"""
        test_file = tmp_path / "nonexistent.json"

        with pytest.raises(SystemExit) as exc_info:
            load_json(test_file)
        assert exc_info.value.code == 1

    def test_load_json_invalid_json(self, tmp_path):
        """Test JSONDecodeError handling"""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{invalid json}")

        with pytest.raises(SystemExit) as exc_info:
            load_json(test_file)
        assert exc_info.value.code == 1

    def test_load_json_unicode_content(self, tmp_path):
        """Test loading JSON with unicode characters"""
        test_file = tmp_path / "unicode.json"
        test_data = {"japanese": "日本語", "emoji": "🎌"}
        test_file.write_text(json.dumps(test_data, ensure_ascii=False))

        result = load_json(test_file)
        assert result["japanese"] == "日本語"
        assert result["emoji"] == "🎌"


class TestBuildKanjiJlptMap:
    """Tests for build_kanji_jlpt_map function"""

    def test_empty_characters(self):
        """Test with empty characters list"""
        data = {"characters": []}
        result = build_kanji_jlpt_map(data)
        assert result == {}

    def test_level_4_to_n5(self):
        """Test old level 4 maps to N5"""
        data = {
            "characters": [
                {"literal": "一", "misc": {"jlptLevel": 4}},
                {"literal": "二", "misc": {"jlptLevel": 4}},
            ]
        }
        result = build_kanji_jlpt_map(data)
        assert result["一"] == "N5"
        assert result["二"] == "N5"

    def test_level_3_to_n4(self):
        """Test old level 3 maps to N4"""
        data = {
            "characters": [
                {"literal": "食", "misc": {"jlptLevel": 3}},
            ]
        }
        result = build_kanji_jlpt_map(data)
        assert result["食"] == "N4"

    def test_level_1_to_n1(self):
        """Test old level 1 maps to N1"""
        data = {
            "characters": [
                {"literal": "鬱", "misc": {"jlptLevel": 1}},
            ]
        }
        result = build_kanji_jlpt_map(data)
        assert result["鬱"] == "N1"

    def test_level_2_split_n3(self):
        """Test old level 2 with grade <= 6 maps to N3"""
        data = {
            "characters": [
                {"literal": "学", "misc": {"jlptLevel": 2, "grade": 6}},
                {"literal": "校", "misc": {"jlptLevel": 2, "grade": 3}},
            ]
        }
        result = build_kanji_jlpt_map(data)
        assert result["学"] == "N3"
        assert result["校"] == "N3"

    def test_level_2_split_n2(self):
        """Test old level 2 with grade > 6 maps to N2"""
        data = {
            "characters": [
                {"literal": "複", "misc": {"jlptLevel": 2, "grade": 8}},
                {"literal": "雑", "misc": {"jlptLevel": 2, "grade": 7}},
            ]
        }
        result = build_kanji_jlpt_map(data)
        assert result["複"] == "N2"
        assert result["雑"] == "N2"

    def test_level_2_no_grade_defaults_to_n2(self):
        """Test old level 2 without grade maps to N2"""
        data = {
            "characters": [
                {"literal": "某", "misc": {"jlptLevel": 2}},
            ]
        }
        result = build_kanji_jlpt_map(data)
        assert result["某"] == "N2"

    def test_no_jlpt_level_skipped(self):
        """Test characters without JLPT level are skipped"""
        data = {
            "characters": [
                {"literal": "未", "misc": {"grade": 5}},  # No jlptLevel
            ]
        }
        result = build_kanji_jlpt_map(data)
        assert "未" not in result

    def test_no_literal_skipped(self):
        """Test characters without literal are skipped"""
        data = {
            "characters": [
                {"misc": {"jlptLevel": 4}},  # No literal
            ]
        }
        result = build_kanji_jlpt_map(data)
        assert result == {}


class TestGetWordJlptLevel:
    """Tests for get_word_jlpt_level function"""

    def test_kana_only_word(self):
        """Test kana-only words return kana_only"""
        word = {"kanji": [], "kana": [{"text": "ひらがな"}]}
        kanji_map = {}
        result = get_word_jlpt_level(word, kanji_map)
        assert result == "kana_only"

    def test_single_kanji_n5(self):
        """Test word with single N5 kanji"""
        word = {"kanji": [{"text": "一"}]}
        kanji_map = {"一": "N5"}
        result = get_word_jlpt_level(word, kanji_map)
        assert result == "N5"

    def test_single_kanji_n1(self):
        """Test word with single N1 kanji"""
        word = {"kanji": [{"text": "鬱"}]}
        kanji_map = {"鬱": "N1"}
        result = get_word_jlpt_level(word, kanji_map)
        assert result == "N1"

    def test_multiple_kanji_highest_level(self):
        """Test word with multiple kanji returns highest level"""
        word = {"kanji": [{"text": "学生"}]}  # 学=N3, 生 could be N5
        kanji_map = {"学": "N3", "生": "N5"}
        result = get_word_jlpt_level(word, kanji_map)
        assert result == "N3"

    def test_multiple_kanji_n1_priority(self):
        """Test that N1 takes priority over lower levels"""
        word = {"kanji": [{"text": "鬱病"}]}
        kanji_map = {"鬱": "N1", "病": "N3"}
        result = get_word_jlpt_level(word, kanji_map)
        assert result == "N1"

    def test_non_jlpt_kanji(self):
        """Test word with kanji not in JLPT map"""
        word = {"kanji": [{"text": "罕见字"}]}
        kanji_map = {"罕": "N1"}  # 见 and 字 not in map
        result = get_word_jlpt_level(word, kanji_map)
        assert result == "N1"

    def test_all_non_jlpt_kanji(self):
        """Test word where all kanji are non-JLPT"""
        word = {"kanji": [{"text": "𠮷野家"}]}
        kanji_map = {}  # Special kanji not in JLPT
        result = get_word_jlpt_level(word, kanji_map)
        assert result == "non_jlpt"

    def test_multiple_kanji_forms(self):
        """Test word with multiple kanji forms"""
        word = {"kanji": [{"text": "学ぶ"}, {"text": "習う"}]}
        kanji_map = {"学": "N3", "習": "N4"}
        result = get_word_jlpt_level(word, kanji_map)
        assert result == "N3"

    def test_mixed_kana_kanji(self):
        """Test word with mixed kana and kanji"""
        word = {"kanji": [{"text": "食べる"}]}
        kanji_map = {"食": "N4"}
        result = get_word_jlpt_level(word, kanji_map)
        assert result == "N4"


class TestIsCommonWord:
    """Tests for is_common_word function"""

    def test_common_kanji(self):
        """Test word with common kanji form"""
        word = {
            "kanji": [{"text": "学生", "common": True}],
            "kana": [{"text": "がくせい", "common": False}],
        }
        assert is_common_word(word) is True

    def test_common_kana(self):
        """Test word with common kana form"""
        word = {
            "kanji": [{"text": "学生", "common": False}],
            "kana": [{"text": "がくせい", "common": True}],
        }
        assert is_common_word(word) is True

    def test_not_common(self):
        """Test word that is not common"""
        word = {
            "kanji": [{"text": "学生", "common": False}],
            "kana": [{"text": "がくせい", "common": False}],
        }
        assert is_common_word(word) is False

    def test_no_common_field(self):
        """Test word without common field"""
        word = {
            "kanji": [{"text": "学生"}],
            "kana": [{"text": "がくせい"}],
        }
        assert is_common_word(word) is False

    def test_empty_kanji_kana(self):
        """Test word with empty kanji and kana lists"""
        word = {"kanji": [], "kana": []}
        assert is_common_word(word) is False


class TestGetPrimaryForm:
    """Tests for get_primary_form function"""

    def test_common_kanji_first(self):
        """Test prefers common kanji form"""
        word = {
            "kanji": [
                {"text": "常用", "common": True},
                {"text": "非常用", "common": False},
            ],
            "kana": [{"text": "つかう"}],
        }
        form, form_type = get_primary_form(word)
        assert form == "常用"
        assert form_type == "kanji"

    def test_fallback_to_first_kanji(self):
        """Test falls back to first kanji if none common"""
        word = {
            "kanji": [{"text": "学生"}, {"text": "学"}],
            "kana": [{"text": "がくせい"}],
        }
        form, form_type = get_primary_form(word)
        assert form == "学生"
        assert form_type == "kanji"

    def test_kana_only_word(self):
        """Test word with only kana"""
        word = {"kanji": [], "kana": [{"text": "ひらがな"}]}
        form, form_type = get_primary_form(word)
        assert form == "ひらがな"
        assert form_type == "kana"

    def test_kana_only_when_no_kanji(self):
        """Test uses kana only when no kanji entries exist"""
        word = {
            "kanji": [],
            "kana": [{"text": "がくせい", "common": True}],
        }
        form, form_type = get_primary_form(word)
        assert form == "がくせい"
        assert form_type == "kana"

    def test_empty_word(self):
        """Test empty word returns None"""
        word = {"kanji": [], "kana": []}
        form, form_type = get_primary_form(word)
        assert form is None
        assert form_type == ""

    def test_no_text_field(self):
        """Test handling of entries without text field"""
        word = {"kanji": [{"common": True}], "kana": []}
        form, form_type = get_primary_form(word)
        assert form is None
        # Even with no text, if marked common it returns kanji type
        assert form_type == "kanji"


class TestGetReadings:
    """Tests for get_readings function"""

    def test_single_reading(self):
        """Test word with single reading"""
        word = {"kana": [{"text": "がくせい"}]}
        result = get_readings(word)
        assert result == ["がくせい"]

    def test_multiple_readings(self):
        """Test word with multiple readings"""
        word = {
            "kana": [{"text": "ひ", "common": True}, {"text": "び", "common": True}]
        }
        result = get_readings(word)
        assert result == ["ひ", "び"]

    def test_no_readings(self):
        """Test word with no readings"""
        word = {"kana": []}
        result = get_readings(word)
        assert result == []

    def test_no_text_field(self):
        """Test handling entries without text field"""
        word = {"kana": [{"common": True}]}
        result = get_readings(word)
        assert result == []


class TestFormatSense:
    """Tests for format_sense function"""

    def test_basic_sense(self):
        """Test basic sense formatting"""
        sense = {
            "partOfSpeech": ["n"],
            "gloss": [{"lang": "eng", "text": "student"}],
        }
        tags = {"n": "noun"}
        result = format_sense(sense, tags)
        assert "student" in result
        assert "noun" in result

    def test_multiple_glosses(self):
        """Test sense with multiple glosses"""
        sense = {
            "partOfSpeech": ["n"],
            "gloss": [
                {"lang": "eng", "text": "school"},
                {"lang": "eng", "text": "academy"},
            ],
        }
        tags = {"n": "noun"}
        result = format_sense(sense, tags)
        assert "school; academy" in result

    def test_with_info(self):
        """Test sense with info field"""
        sense = {
            "partOfSpeech": ["v5r"],
            "gloss": [{"lang": "eng", "text": "to eat"}],
            "info": ["transitive verb"],
        }
        tags = {"v5r": "Godan verb"}
        result = format_sense(sense, tags)
        assert "to eat" in result
        assert "transitive verb" in result

    def test_with_misc_tags(self):
        """Test sense with misc tags"""
        sense = {
            "partOfSpeech": ["adj-i"],
            "gloss": [{"lang": "eng", "text": "delicious"}],
            "misc": ["uk", "col"],
        }
        tags = {"adj-i": "i-adjective", "uk": "usually kana", "col": "colloquial"}
        result = format_sense(sense, tags)
        assert "delicious" in result
        assert "usually kana" in result
        assert "colloquial" in result

    def test_no_english_gloss(self):
        """Test sense with no English gloss"""
        sense = {
            "partOfSpeech": ["n"],
            "gloss": [{"lang": "ger", "text": "Schule"}],
        }
        tags = {"n": "noun"}
        result = format_sense(sense, tags)
        assert result == "(noun)"

    def test_unknown_tag(self):
        """Test handling of unknown tags"""
        sense = {
            "partOfSpeech": ["unknown_tag"],
            "gloss": [{"lang": "eng", "text": "test"}],
        }
        tags = {}
        result = format_sense(sense, tags)
        assert "unknown_tag" in result

    def test_empty_sense(self):
        """Test empty sense"""
        sense = {"partOfSpeech": [], "gloss": []}
        tags = {}
        result = format_sense(sense, tags)
        assert result == ""


class TestFormatExamples:
    """Tests for format_examples function"""

    def test_single_example(self):
        """Test single example formatting"""
        examples = [
            {
                "sentences": [
                    {"lang": "jpn", "text": "私は学生です。"},
                    {"lang": "eng", "text": "I am a student."},
                ]
            }
        ]
        result = format_examples(examples)
        assert "私は学生です。" in result
        assert "I am a student." in result

    def test_multiple_examples(self):
        """Test multiple examples with max limit"""
        examples = [
            {
                "sentences": [
                    {"lang": "jpn", "text": "学生です。"},
                    {"lang": "eng", "text": "I am a student."},
                ]
            },
            {
                "sentences": [
                    {"lang": "jpn", "text": "先生です。"},
                    {"lang": "eng", "text": "I am a teacher."},
                ]
            },
            {
                "sentences": [
                    {"lang": "jpn", "text": "医者です。"},
                    {"lang": "eng", "text": "I am a doctor."},
                ]
            },
        ]
        result = format_examples(examples, max_examples=2)
        assert result.count("1.") == 1
        assert result.count("2.") == 1
        assert "3." not in result

    def test_missing_english(self):
        """Test example missing English translation"""
        examples = [
            {
                "sentences": [
                    {"lang": "jpn", "text": "学生です。"},
                    # No English sentence
                ]
            }
        ]
        result = format_examples(examples)
        assert result == ""

    def test_missing_japanese(self):
        """Test example missing Japanese sentence"""
        examples = [
            {
                "sentences": [
                    {"lang": "eng", "text": "I am a student."},
                    # No Japanese sentence
                ]
            }
        ]
        result = format_examples(examples)
        assert result == ""

    def test_empty_examples(self):
        """Test empty examples list"""
        result = format_examples([])
        assert result == ""

    def test_example_with_other_languages(self):
        """Test example with other languages ignored"""
        examples = [
            {
                "sentences": [
                    {"lang": "jpn", "text": "学生です。"},
                    {"lang": "ger", "text": "Ich bin Student."},
                    {"lang": "eng", "text": "I am a student."},
                ]
            }
        ]
        result = format_examples(examples)
        assert "学生です。" in result
        assert "I am a student." in result
        assert "Ich bin Student" not in result


class TestProcessWord:
    """Tests for process_word function"""

    def test_basic_word(self):
        """Test basic word processing"""
        word = {
            "kanji": [{"text": "学生", "common": True}],
            "kana": [{"text": "がくせい", "common": True}],
            "sense": [
                {
                    "partOfSpeech": ["n"],
                    "gloss": [{"lang": "eng", "text": "student"}],
                }
            ],
        }
        tags = {"n": "noun"}
        result = process_word(word, tags)

        assert result["word"] == "学生"
        assert result["readings"] == "がくせい"
        assert "student" in result["senses"]
        assert result["is_common"] is True
        assert result["form_type"] == "kanji"

    def test_kana_only_word(self):
        """Test processing kana-only word"""
        word = {
            "kanji": [],
            "kana": [{"text": "です", "common": True}],
            "sense": [
                {
                    "partOfSpeech": ["aux-v"],
                    "gloss": [{"lang": "eng", "text": "to be"}],
                }
            ],
        }
        tags = {"aux-v": "auxiliary verb"}
        result = process_word(word, tags)

        assert result["word"] == "です"
        assert result["readings"] == "です"
        assert result["form_type"] == "kana"

    def test_multiple_senses(self):
        """Test word with multiple senses"""
        word = {
            "kanji": [{"text": "上"}],
            "kana": [{"text": "うえ"}],
            "sense": [
                {
                    "partOfSpeech": ["n"],
                    "gloss": [{"lang": "eng", "text": "above"}],
                },
                {
                    "partOfSpeech": ["n"],
                    "gloss": [{"lang": "eng", "text": "top"}],
                },
            ],
        }
        tags = {"n": "noun"}
        result = process_word(word, tags)

        assert "1." in result["senses"]
        assert "2." in result["senses"]
        assert "above" in result["senses"]
        assert "top" in result["senses"]

    def test_no_senses_returns_none(self):
        """Test word with no valid senses returns None"""
        word = {
            "kanji": [{"text": "学生"}],
            "kana": [{"text": "がくせい"}],
            "sense": [],
        }
        tags = {}
        result = process_word(word, tags)
        assert result is None

    def test_with_examples(self):
        """Test word with examples included"""
        word = {
            "kanji": [{"text": "学生"}],
            "kana": [{"text": "がくせい"}],
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
        tags = {"n": "noun"}
        result = process_word(word, tags, include_examples=True)

        assert "examples" in result
        assert "私は学生です。" in result["examples"]

    def test_no_examples_when_not_requested(self):
        """Test examples not included when flag is False"""
        word = {
            "kanji": [{"text": "学生"}],
            "kana": [{"text": "がくせい"}],
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
        tags = {"n": "noun"}
        result = process_word(word, tags, include_examples=False)

        assert "examples" not in result

    def test_no_valid_form_returns_none(self):
        """Test word with no valid form returns None"""
        word = {"kanji": [], "kana": [], "sense": [{"gloss": []}]}
        tags = {}
        result = process_word(word, tags)
        assert result is None

    def test_common_flag_in_result(self):
        """Test is_common flag is correctly set"""
        word = {
            "kanji": [{"text": "学生", "common": False}],
            "kana": [{"text": "がくせい", "common": False}],
            "sense": [{"gloss": [{"lang": "eng", "text": "student"}]}],
        }
        tags = {}
        result = process_word(word, tags)
        assert result["is_common"] is False
