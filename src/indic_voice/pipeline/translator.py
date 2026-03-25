from deep_translator import GoogleTranslator

def translate_to_hindi(text: str) -> str:
    """
    Translates detected english text to Hindi.
    """
    translator = GoogleTranslator(source='auto', target='hi')
    return translator.translate(text)
