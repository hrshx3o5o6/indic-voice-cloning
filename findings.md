# Findings
## Current Understanding
Goal: Zero-shot voice cloning (English $\rightarrow$ Hindi/Tamil) preserving exact tonality and intent.

SOTA shifted to **Conditional Flow Matching (CFM)** and **Diffusion**. Models like EZ-VC and IN-F5 show that English-pretrained models fine-tuned on Indic data provide the best results for zero-shot identity transfer.

## Patterns and Insights
- **CFM/Diffusion > Autoregressive**: Better naturalness and stability in zero-shot settings.
- **SSL Encoders**: Xeus/WavLM provide superior language-agnostic identity features compared to traditional speaker embeddings.
- **Language Prior**: Using English as a base model is critical for high-fidelity transfer to Indic languages.

## Lessons and Constraints
- **Prosody Mismatch**: English (stress-timed) vs. Indic (syllable-timed) means simple identity cloning doesn't automatically transfer "intent" or "emotion" accurately.
- **Data Scale**: Fine-tuning English priors requires relatively small but high-quality Indic datasets (~10h/lang).

## Open Questions
- How to specifically capture "intent" and "tonality" (prosody) in English and map it to equivalent Indic prosodic structures?
- Can discrete SSL quantization be used to "lock" the emotion/intent while changing the linguistic content?
