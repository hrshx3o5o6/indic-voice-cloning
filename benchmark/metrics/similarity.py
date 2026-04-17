"""Speaker similarity metric using WavLM cosine similarity.

Uses microsoft/wavlm-base-plus to extract speaker embeddings via mean-pool
of the last hidden state, then computes cosine similarity.

REQUIREMENT: BENCH-03
"""
from __future__ import annotations

import torch
import torchaudio
import torch.nn.functional as F
from transformers import AutoFeatureExtractor, WavLMModel


_MODEL_ID = "microsoft/wavlm-base-plus"
_TARGET_SR = 16_000

# Module-level cache so the model is loaded once per process
_feature_extractor: AutoFeatureExtractor | None = None
_model: WavLMModel | None = None


def _load_model() -> tuple[AutoFeatureExtractor, WavLMModel]:
    """Lazy-load WavLM model and feature extractor (cached after first call)."""
    global _feature_extractor, _model
    if _feature_extractor is None or _model is None:
        _feature_extractor = AutoFeatureExtractor.from_pretrained(_MODEL_ID)
        _model = WavLMModel.from_pretrained(_MODEL_ID)
        _model.eval()
    return _feature_extractor, _model


def _load_audio(path: str) -> torch.Tensor:
    """Load WAV file and resample to 16 kHz mono; returns 1-D tensor."""
    waveform, sr = torchaudio.load(path)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    if sr != _TARGET_SR:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=_TARGET_SR)
        waveform = resampler(waveform)
    return waveform.squeeze(0)


def _embed(waveform: torch.Tensor, feature_extractor: AutoFeatureExtractor, model: WavLMModel) -> torch.Tensor:
    """Extract speaker embedding as mean-pooled last hidden state."""
    inputs = feature_extractor(
        waveform.numpy(),
        sampling_rate=_TARGET_SR,
        return_tensors="pt",
    )
    with torch.no_grad():
        outputs = model(**inputs)
    # Mean-pool over time dimension: (1, T, H) -> (1, H)
    embedding = outputs.last_hidden_state.mean(dim=1)
    return embedding


def compute_speaker_similarity(ref_wav: str, hyp_wav: str) -> float:
    """Compute WavLM cosine similarity between two WAV files.

    Loads microsoft/wavlm-base-plus on first call (cached thereafter).
    Both files are resampled to 16 kHz mono before embedding.

    Args:
        ref_wav: Path to the reference speaker WAV file.
        hyp_wav: Path to the synthesized/hypothesis WAV file.

    Returns:
        Cosine similarity in [-1.0, 1.0]. Higher means more similar speaker identity.
    """
    feature_extractor, model = _load_model()
    ref_wave = _load_audio(ref_wav)
    hyp_wave = _load_audio(hyp_wav)
    ref_emb = _embed(ref_wave, feature_extractor, model)
    hyp_emb = _embed(hyp_wave, feature_extractor, model)
    sim: float = F.cosine_similarity(ref_emb, hyp_emb, dim=1).item()
    return sim
