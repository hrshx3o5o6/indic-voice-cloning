import typer
from rich.console import Console

from indic_voice.pipeline.asr import transcribe_audio
from indic_voice.pipeline.translator import translate
from indic_voice.pipeline.tts_indicf5 import generate_speech as indicf5_generate_speech

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
        # Auto-transcribe ref_voice if ref_text not provided (CLI-01)
        if ref_text is None:
            console.print("   [dim]Auto-transcribing reference audio...[/dim]")
            ref_text = transcribe_audio(ref_voice)
            console.print(f"   [dim]Ref transcript: '{ref_text}'[/dim]")

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
    End-to-End Translate: Transcribe (EN) -> Translate -> Generate (Indic) via IndicF5.
    """
    console.print("[bold blue]Running end-to-end Speech to Speech Translator...[/bold blue]")
    try:
        console.print("1. Transcribing source audio using Whisper...")
        en_text = transcribe_audio(audio)
        console.print(f"   [dim]Transcript: '{en_text}'[/dim]")

        console.print("2. Translating to target language...")
        hi_text = translate(en_text, target_lang=target_lang)
        console.print(f"   [dim]Translation: '{hi_text}'[/dim]")

        console.print("3. Generating cloned speech via IndicF5...")
        indicf5_generate_speech(
            text=hi_text,
            ref_audio_path=audio,  # Use source audio as reference
            ref_text=en_text,  # Use Whisper transcript as ref_text (CLI-02)
            output_path=output,
        )

        console.print(f"[bold green]Success![/bold green] Saved translated clone to [cyan]{output}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    app()
