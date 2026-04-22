from indic_voice.pipeline.tts_indicf5 import generate_speech

result = generate_speech(
    text='नमस्ते',
    ref_audio_path='/Users/harsha/Downloads/ventures_hacks_projects_backup/iitb/audio_data/Harsa_2.m4a',
    ref_text='Hello this is a test',
    output_path='indicf5_output.wav',
)
print(f'Output: {result}')
