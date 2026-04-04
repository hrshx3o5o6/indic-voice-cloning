from deep_translator import GoogleTranslator


def translate(text: str, target_lang: str = "hi") -> str:
    """Translate text to the specified Indic language.

    Args:
        text: Source text to translate (auto-detected language).
        target_lang: BCP-47 language code for the translation target.
            Defaults to ``"hi"`` (Hindi).

    Returns:
        The translated text string.
    """
    translator = GoogleTranslator(source="auto", target=target_lang)
    return translator.translate(text)
