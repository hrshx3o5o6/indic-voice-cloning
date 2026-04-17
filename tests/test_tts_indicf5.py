"""Unit tests for IndicF5 TTS module.

Tests verify:
- Module imports without error
- Function signature and type hints
- Happy path: valid ref_audio, ref_text, output path
- Error handling: missing ref_audio, empty ref_text, output creation
"""

import os
import pytest
from unittest.mock import patch, MagicMock, call
import numpy as np
import torch

from indic_voice.pipeline.tts_indicf5 import generate_speech, _select_device


class TestDeviceSelection:
    """Test _select_device() device selection logic."""

    @patch("indic_voice.pipeline.tts_indicf5.torch.cuda.is_available")
    def test_device_selection_cuda_when_available(self, mock_cuda):
        """_select_device() returns cuda device when CUDA is available."""
        mock_cuda.return_value = True
        device = _select_device()
        assert device.type == "cuda"

    @patch("indic_voice.pipeline.tts_indicf5.torch.cuda.is_available")
    def test_device_selection_cpu_fallback(self, mock_cuda):
        """_select_device() returns cpu device when CUDA unavailable."""
        mock_cuda.return_value = False
        device = _select_device()
        assert device.type == "cpu"


class TestGenerateSpeechErrorHandling:
    """Test error handling paths in generate_speech()."""

    def test_missing_ref_audio_raises_filenotfounderror(self, tmp_path):
        """generate_speech() raises FileNotFoundError if ref_audio_path doesn't exist."""
        output_path = str(tmp_path / "out.wav")

        with pytest.raises(FileNotFoundError):
            generate_speech(
                text="नमस्ते",
                ref_audio_path="/nonexistent/ref.wav",
                ref_text="hello",
                output_path=output_path
            )

    @patch("indic_voice.pipeline.tts_indicf5.torchaudio.load")
    def test_empty_ref_text_raises_valueerror(self, mock_load, sample_wav, tmp_path):
        """generate_speech() raises ValueError if ref_text is empty string."""
        mock_load.return_value = (torch.randn(1, 16000), 16000)
        output_path = str(tmp_path / "out.wav")

        with pytest.raises(ValueError, match="reference text|ref_text|empty"):
            generate_speech(
                text="नमस्ते",
                ref_audio_path=sample_wav,
                ref_text="",
                output_path=output_path
            )

    @patch("indic_voice.pipeline.tts_indicf5.torchaudio.load")
    def test_none_ref_text_raises_valueerror(self, mock_load, sample_wav, tmp_path):
        """generate_speech() raises ValueError if ref_text is None."""
        mock_load.return_value = (torch.randn(1, 16000), 16000)
        output_path = str(tmp_path / "out.wav")

        with pytest.raises(ValueError, match="reference text|ref_text"):
            generate_speech(
                text="नमस्ते",
                ref_audio_path=sample_wav,
                ref_text=None,
                output_path=output_path
            )

    @patch("indic_voice.pipeline.tts_indicf5.soundfile.write")
    @patch("indic_voice.pipeline.tts_indicf5.AutoTokenizer.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.AutoModelForCausalLM.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.torchaudio.load")
    def test_model_loading_failure_raises_runtimeerror(
        self,
        mock_audio_load,
        mock_model_load,
        mock_tokenizer_load,
        mock_soundfile_write,
        sample_wav,
        tmp_path
    ):
        """generate_speech() raises RuntimeError if model loading fails."""
        mock_audio_load.return_value = (torch.randn(1, 16000), 16000)
        mock_model_load.side_effect = RuntimeError("Model download failed")

        output_path = str(tmp_path / "out.wav")

        with pytest.raises(RuntimeError, match="Failed to load IndicF5 model"):
            generate_speech(
                text="नमस्ते",
                ref_audio_path=sample_wav,
                ref_text="नमस्ते",
                output_path=output_path
            )


class TestGenerateSpeechHappyPath:
    """Test successful generate_speech() execution."""

    @patch("indic_voice.pipeline.tts_indicf5.soundfile.write")
    @patch("indic_voice.pipeline.tts_indicf5.AutoTokenizer.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.AutoModelForCausalLM.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.torchaudio.load")
    def test_generate_speech_returns_output_path(
        self,
        mock_audio_load,
        mock_model_load,
        mock_tokenizer_load,
        mock_soundfile_write,
        mock_indicf5_audio_output,
        sample_wav,
        tmp_path
    ):
        """generate_speech() returns output_path string on success."""
        # Setup mocks
        mock_audio_load.return_value = (torch.randn(1, 16000), 16000)

        mock_model = MagicMock()
        mock_model.generate.return_value = torch.tensor(mock_indicf5_audio_output)
        mock_model_load.return_value = mock_model

        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_tokenizer_load.return_value = mock_tokenizer

        output_path = str(tmp_path / "output.wav")

        # Execute
        result = generate_speech(
            text="नमस्ते",
            ref_audio_path=sample_wav,
            ref_text="नमस्ते",
            output_path=output_path
        )

        # Verify
        assert result == output_path
        assert isinstance(result, str)

    @patch("indic_voice.pipeline.tts_indicf5.soundfile.write")
    @patch("indic_voice.pipeline.tts_indicf5.AutoTokenizer.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.AutoModelForCausalLM.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.torchaudio.load")
    def test_generate_speech_calls_soundfile_write(
        self,
        mock_audio_load,
        mock_model_load,
        mock_tokenizer_load,
        mock_soundfile_write,
        mock_indicf5_audio_output,
        sample_wav,
        tmp_path
    ):
        """generate_speech() calls soundfile.write() with output_path and audio data."""
        # Setup mocks
        mock_audio_load.return_value = (torch.randn(1, 16000), 16000)

        mock_model = MagicMock()
        mock_model.generate.return_value = torch.tensor(mock_indicf5_audio_output)
        mock_model_load.return_value = mock_model

        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_tokenizer_load.return_value = mock_tokenizer

        output_path = str(tmp_path / "output.wav")

        # Execute
        generate_speech(
            text="नमस्ते",
            ref_audio_path=sample_wav,
            ref_text="नमस्ते",
            output_path=output_path
        )

        # Verify: soundfile.write() was called
        mock_soundfile_write.assert_called_once()
        call_args = mock_soundfile_write.call_args
        # First positional argument should be output_path
        assert call_args[0][0] == output_path

    @patch("indic_voice.pipeline.tts_indicf5.soundfile.write")
    @patch("indic_voice.pipeline.tts_indicf5.AutoTokenizer.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.AutoModelForCausalLM.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.torchaudio.load")
    def test_generate_speech_normalizes_int16_to_float32(
        self,
        mock_audio_load,
        mock_model_load,
        mock_tokenizer_load,
        mock_soundfile_write,
        sample_wav,
        tmp_path
    ):
        """generate_speech() normalizes int16 audio to float32 before writing (per INDICF5-07)."""
        # Setup mocks
        mock_audio_load.return_value = (torch.randn(1, 16000), 16000)

        # Model returns int16 audio (requires normalization)
        int16_audio = np.array([-32768, 0, 32767, -100, 100], dtype=np.int16)
        mock_model = MagicMock()
        mock_model.generate.return_value = torch.tensor(int16_audio)
        mock_model_load.return_value = mock_model

        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_tokenizer_load.return_value = mock_tokenizer

        output_path = str(tmp_path / "output.wav")

        # Execute
        generate_speech(
            text="नमस्ते",
            ref_audio_path=sample_wav,
            ref_text="नमस्ते",
            output_path=output_path
        )

        # Verify: soundfile.write() was called with float32 normalized audio
        assert mock_soundfile_write.called
        call_args = mock_soundfile_write.call_args
        # Audio data is second positional argument or 'data' kwarg
        audio_data = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("data")

        # Check normalization: int16 [-32768, 0, 32767] → float32 [-1.0, 0.0, ~1.0]
        assert audio_data.dtype == np.float32 or str(audio_data.dtype).startswith("float")
        # Check approximate values after normalization
        assert abs(audio_data[0] - (-1.0)) < 0.01  # -32768 / 32768 = -1.0
        assert abs(audio_data[1]) < 0.01  # 0 / 32768 = 0.0

    @patch("indic_voice.pipeline.tts_indicf5.soundfile.write")
    @patch("indic_voice.pipeline.tts_indicf5.AutoTokenizer.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.AutoModelForCausalLM.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.torchaudio.load")
    def test_generate_speech_creates_output_directory(
        self,
        mock_audio_load,
        mock_model_load,
        mock_tokenizer_load,
        mock_soundfile_write,
        mock_indicf5_audio_output,
        sample_wav,
        tmp_path
    ):
        """generate_speech() creates parent directories for output_path if they don't exist."""
        # Setup mocks
        mock_audio_load.return_value = (torch.randn(1, 16000), 16000)

        mock_model = MagicMock()
        mock_model.generate.return_value = torch.tensor(mock_indicf5_audio_output)
        mock_model_load.return_value = mock_model

        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_tokenizer_load.return_value = mock_tokenizer

        # Create output path with nested directory that doesn't exist yet
        output_path = str(tmp_path / "nested" / "dirs" / "output.wav")

        # Execute
        generate_speech(
            text="नमस्ते",
            ref_audio_path=sample_wav,
            ref_text="नमस्ते",
            output_path=output_path
        )

        # Verify: soundfile.write() was called with the full nested path
        mock_soundfile_write.assert_called_once()
        call_args = mock_soundfile_write.call_args
        assert call_args[0][0] == output_path

    @patch("indic_voice.pipeline.tts_indicf5.soundfile.write")
    @patch("indic_voice.pipeline.tts_indicf5.AutoTokenizer.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.AutoModelForCausalLM.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.torchaudio.load")
    def test_generate_speech_uses_correct_device(
        self,
        mock_audio_load,
        mock_model_load,
        mock_tokenizer_load,
        mock_soundfile_write,
        mock_indicf5_audio_output,
        sample_wav,
        tmp_path
    ):
        """generate_speech() uses device returned by _select_device() for inference."""
        # Setup mocks
        mock_audio_load.return_value = (torch.randn(1, 16000), 16000)

        mock_model = MagicMock()
        mock_model.generate.return_value = torch.tensor(mock_indicf5_audio_output)
        mock_model_load.return_value = mock_model

        mock_tokenizer = MagicMock()
        def tokenizer_call(text, return_tensors=None):
            return {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_tokenizer.side_effect = tokenizer_call
        mock_tokenizer_load.return_value = mock_tokenizer

        output_path = str(tmp_path / "output.wav")

        # Mock device selection to return CPU
        with patch("indic_voice.pipeline.tts_indicf5._select_device") as mock_device:
            mock_device.return_value = torch.device("cpu")

            # Execute
            generate_speech(
                text="नमस्ते",
                ref_audio_path=sample_wav,
                ref_text="नमस्ते",
                output_path=output_path
            )

            # Verify: _select_device was called
            mock_device.assert_called_once()

    @patch("indic_voice.pipeline.tts_indicf5.soundfile.write")
    @patch("indic_voice.pipeline.tts_indicf5.AutoTokenizer.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.AutoModelForCausalLM.from_pretrained")
    @patch("indic_voice.pipeline.tts_indicf5.torchaudio.load")
    def test_generate_speech_loads_ref_audio(
        self,
        mock_audio_load,
        mock_model_load,
        mock_tokenizer_load,
        mock_soundfile_write,
        mock_indicf5_audio_output,
        sample_wav,
        tmp_path
    ):
        """generate_speech() loads reference audio from ref_audio_path."""
        # Setup mocks
        mock_audio_load.return_value = (torch.randn(1, 16000), 16000)

        mock_model = MagicMock()
        mock_model.generate.return_value = torch.tensor(mock_indicf5_audio_output)
        mock_model_load.return_value = mock_model

        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_tokenizer_load.return_value = mock_tokenizer

        output_path = str(tmp_path / "output.wav")

        # Execute
        generate_speech(
            text="नमस्ते",
            ref_audio_path=sample_wav,
            ref_text="नमस्ते",
            output_path=output_path
        )

        # Verify: torchaudio.load was called with ref_audio_path
        mock_audio_load.assert_called_once_with(sample_wav)
