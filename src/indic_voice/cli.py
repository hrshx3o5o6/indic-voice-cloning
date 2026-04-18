import os

import typer
from rich.console import Console

from indic_voice.pipeline.asr import transcribe_audio
from indic_voice.pipeline.translator import translate
from indic_voice.pipeline.tts_indicf5 import generate_speech as indicf5_generate_speech
from indic_voice.pipeline.tts_sarvam import generate_speech
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
    ref_text: str = typer.Option(None, "--ref-text", help="Transcript of the reference audio (auto-generated if not provided)"),
    output: str = typer.Option("clone_output.wav", "--output", "-o", help="Path to save the cloned audio"),
) -> None:
    """
    Generate native Hindi speech cloned to your exact voice tone.
    """
    console.print("[bold green]Running clone...[/bold green]")
    try:
        console.print("1. Generating cloned speech via IndicF5...")
        indicf5_generate_speech(
            text=text,
            ref_audio_path=ref_voice,
            ref_text=ref_text,
            output_path=output,
        )

        console.print(f"[bold green]Success![/bold green] Saved cloned audio to [cyan]{output}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command(name="translate")
def translate_audio(
    audio: str = typer.Option(..., "--audio", "-a", help="Path to the English source audio (.wav)"),
    target_lang: str = typer.Option("hi", "--target-lang", "-l", help="Target Indic language code (e.g. 'hi')"),
    output: str = typer.Option("translated_clone.wav", "--output", "-o", help="Path to save the translated audio"),
) -> None:
    """
    End-to-End Translate: Transcribe (EN) -> Translate -> Generate (Indic) -> Tone Morph.
    """
    console.print("[bold blue]Running end-to-end Speech to Speech Translator...[/bold blue]")
    tmp_tts = "tmp_sarvam_tts.wav"
    try:
        console.print("1. Transcribing source audio using Whisper...")
        en_text = transcribe_audio(audio)
        console.print(f"   [dim]Transcript: '{en_text}'[/dim]")

        console.print("2. Translating to target language...")
        hi_text = translate(en_text, target_lang=target_lang)
        console.print(f"   [dim]Translation: '{hi_text}'[/dim]")

        console.print("3. Generating native speech via Sarvam AI...")
        generate_speech(hi_text, tmp_tts)

        console.print("4. Imprinting original voice clone via OpenVoice...")
        morph_tone(tmp_tts, audio, output)

        console.print(f"[bold green]Success![/bold green] Saved translated clone to [cyan]{output}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
    finally:
        if os.path.exists(tmp_tts):
            os.remove(tmp_tts)


if __name__ == "__main__":
    app()
