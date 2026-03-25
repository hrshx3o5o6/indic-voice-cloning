import typer
import os
from rich.console import Console

from indic_voice.pipeline.asr import transcribe_audio
from indic_voice.pipeline.translator import translate_to_hindi
from indic_voice.pipeline.tts_sarvam import generate_hindi_speech
from indic_voice.models.tone_transfer import morph_tone

app = typer.Typer(
    help="Zero-shot Indic Voice Cloning & S2ST Pipeline",
    add_completion=False,
)
console = Console()

@app.command()
def clone(
    text: str = typer.Option(..., "--text", "-t", help="The Hindi text to generate"),
    ref_voice: str = typer.Option(..., "--ref-voice", "-v", help="Path to your 3-second reference voice (.wav)"),
    output: str = typer.Option("clone_output.wav", "--output", "-o", help="Path to save the cloned audio"),
):
    """
    Generate native Hindi speech cloned to your exact voice tone.
    """
    console.print(f"[bold green]Running clone...[/bold green]")
    try:
        tmp_tts = "tmp_sarvam_tts.wav"
        
        console.print("1. Generating base Hindi speech via Sarvam AI...")
        generate_hindi_speech(text, tmp_tts)
        
        console.print("2. Imprinting your voice clone via OpenVoice...")
        morph_tone(tmp_tts, ref_voice, output)
        
        console.print(f"[bold green]Success![/bold green] Saved cloned audio to [cyan]{output}[/cyan]")
        
        if os.path.exists(tmp_tts):
            os.remove(tmp_tts)
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@app.command()
def translate(
    audio: str = typer.Option(..., "--audio", "-a", help="Path to the English source audio (.wav)"),
    target_lang: str = typer.Option("hi", "--target-lang", "-l", help="Target Indic language code (e.g. 'hi')"),
    output: str = typer.Option("translated_clone.wav", "--output", "-o", help="Path to save the translated audio"),
):
    """
    End-to-End Translate: Transcribe (EN) -> Translate -> Generate (Indic) -> Tone Morph.
    """
    console.print(f"[bold blue]Running end-to-end Speech to Speech Translator...[/bold blue]")
    try:
        console.print("1. Transcribing source audio using Whisper...")
        en_text = transcribe_audio(audio)
        console.print(f"   [dim]Transcript: '{en_text}'[/dim]")
        
        console.print("2. Translating to Hindi...")
        hi_text = translate_to_hindi(en_text)
        console.print(f"   [dim]Translation: '{hi_text}'[/dim]")
        
        tmp_tts = "tmp_sarvam_tts.wav"
        console.print("3. Generating native Hindi speech via Sarvam AI...")
        generate_hindi_speech(hi_text, tmp_tts)
        
        console.print(f"4. Imprinting original voice clone via OpenVoice...")
        morph_tone(tmp_tts, audio, output)
        
        console.print(f"[bold green]Success![/bold green] Saved translated clone to [cyan]{output}[/cyan]")
        
        if os.path.exists(tmp_tts):
            os.remove(tmp_tts)
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    app()
