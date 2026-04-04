from unittest.mock import MagicMock, patch

from indic_voice.pipeline.translator import translate


@patch("indic_voice.pipeline.translator.GoogleTranslator")
def test_translate_returns_translated_text(mock_translator_cls):
    """translate() returns the text from GoogleTranslator."""
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "नमस्ते दुनिया"
    mock_translator_cls.return_value = mock_instance

    result = translate("Hello world")

    assert result == "नमस्ते दुनिया"


@patch("indic_voice.pipeline.translator.GoogleTranslator")
def test_translate_passes_target_lang(mock_translator_cls):
    """translate() passes target_lang to GoogleTranslator constructor."""
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "வணக்கம்"
    mock_translator_cls.return_value = mock_instance

    translate("Hello", target_lang="ta")

    mock_translator_cls.assert_called_once_with(source="auto", target="ta")


@patch("indic_voice.pipeline.translator.GoogleTranslator")
def test_translate_default_language_is_hindi(mock_translator_cls):
    """translate() defaults to Hindi ('hi') when no target_lang is given."""
    mock_instance = MagicMock()
    mock_instance.translate.return_value = "नमस्ते"
    mock_translator_cls.return_value = mock_instance

    translate("Hello")

    mock_translator_cls.assert_called_once_with(source="auto", target="hi")
