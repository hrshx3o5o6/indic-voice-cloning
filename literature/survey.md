# Literature Survey: Cross-Lingual Voice Cloning & Prosody Transfer

## SOTA Models (2024-2025)

### EZ-VC (2025)
- **Core**: Xeus SSL encoder + Diffusion-Transformer (CFM decoder).
- **Findings**: SOTA zero-shot cross-lingual VC. High naturalness (UTMOS) and similarity (SSIM) for Hindi, Tamil, Telugu, Kannada, Bengali.
- **URL**: [arXiv:2505.20693](https://arxiv.org/pdf/2505.20693) (approx)

### IN-F5 (2025)
- **Core**: F5-TTS adaptation for 11 Indian languages.
- **Findings**: English foundation model $\rightarrow$ Indian data fine-tuning is superior to scratch training. Enables "polyglot fluency."
- **URL**: [arXiv:2409.13910](https://arxiv.org/pdf/2409.13910) (approx)

### CrossVoice (2024)
- **Core**: Cascade-S2ST (Faster-Whisper $\rightarrow$ Google NMT $\rightarrow$ MMS/FreeVC).
- **Findings**: Uses x-vector embeddings for identity preservation in Hindi/Tamil.
- **URL**: [arXiv:2406.00021v1](https://arxiv.org/html/2406.00021v1)

## Technical Trends
- **Architecture**: Shift from Autoregressive/VAE to Conditional Flow Matching (CFM) and Diffusion.
- **Encoding**: Use of discrete SSL units (Xeus, WavLM) instead of separate content/speaker encoders.
- **Prior**: English pre-training provides strong baseline for Indian languages.
- **Challenge**: Prosody gap between stress-timed (English) and syllable-timed (Indic) languages.
