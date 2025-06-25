import sys
import json
import numpy as np
import librosa
import ffmpeg
import subprocess
import os
from scipy.signal import savgol_filter

def extract_audio(input_file, output_audio):
    """Extract audio from any video/audio file format"""
    try:
        ffmpeg.input(input_file).output(output_audio, ac=1, ar=22050).overwrite_output().run(quiet=True)
        return True
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return False

def get_media_duration(path):
    """Get duration of any media file (audio or video)"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting media duration: {e}")
        return 0.0

def is_audio_file(file_path):
    """Check if the file is an audio file"""
    audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma']
    return any(file_path.lower().endswith(ext) for ext in audio_extensions)

def is_video_file(file_path):
    """Check if the file is a video file"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
    return any(file_path.lower().endswith(ext) for ext in video_extensions)

def extract_audio_features(audio_path, sr=22050, hop_length=512):
    y, sr = librosa.load(audio_path, sr=sr)
    
    # Basic characteristics
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    freqs = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
    
    # Advanced spectral analysis
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop_length)[0]
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=hop_length)[0]
    
    # Percussion detection
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
    
    # Note analysis
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=hop_length)
    pitch_max = np.zeros_like(magnitudes[0])
    pitch_min = np.zeros_like(magnitudes[0])
    
    for t in range(magnitudes.shape[1]):
        non_zero_pitches = pitches[:, t][magnitudes[:, t] > 0]
        if len(non_zero_pitches) > 0:
            pitch_max[t] = np.max(non_zero_pitches)
            pitch_min[t] = np.min(non_zero_pitches)
    
    return {
        'rms': rms,
        'freqs': freqs,
        'pitch_max': pitch_max,
        'pitch_min': pitch_min,
        'spectral_rolloff': spectral_rolloff,
        'spectral_bandwidth': spectral_bandwidth,
        'onset_env': onset_env,
        'onset_frames': onset_frames,
        'duration': librosa.get_duration(y=y, sr=sr)
    }

def determine_haptic_type(features, frame_idx):
    # Determine haptic feedback type based on audio characteristics
    rms = features['rms']
    freq = features['freqs']
    rolloff = features['spectral_rolloff']
    bandwidth = features['spectral_bandwidth']
    
    # Detection thresholds
    BASS_FREQ_THRESHOLD = 200
    HIGH_FREQ_THRESHOLD = 2000
    TRANSITION_THRESHOLD = 0.4
    RIGID_BANDWIDTH_THRESHOLD = 0.7
    RIGID_ROLLOFF_MIN = 0.4
    RIGID_ROLLOFF_MAX = 0.6
    
    # Bass detection (low frequency and high intensity)
    is_bass = freq < BASS_FREQ_THRESHOLD and rms > 0.3
    is_deep_bass = freq < BASS_FREQ_THRESHOLD/2 and rms > 0.5
    
    # High-pitched sound detection (high frequency and high rolloff)
    is_high_pitched = freq > HIGH_FREQ_THRESHOLD and rolloff > 0.6
    is_very_high_pitched = freq > HIGH_FREQ_THRESHOLD * 1.5 and rolloff > 0.7
    
    # Metallic/rigid sound detection (high bandwidth and medium rolloff)
    is_rigid = bandwidth > RIGID_BANDWIDTH_THRESHOLD and RIGID_ROLLOFF_MIN < rolloff < RIGID_ROLLOFF_MAX
    is_very_rigid = bandwidth > RIGID_BANDWIDTH_THRESHOLD * 1.2 and RIGID_ROLLOFF_MIN < rolloff < RIGID_ROLLOFF_MAX
    
    # Important transition detection (rapid intensity change)
    is_transition = abs(rms - np.mean(features['rms'])) > TRANSITION_THRESHOLD
    is_strong_transition = abs(rms - np.mean(features['rms'])) > TRANSITION_THRESHOLD * 1.5
    
    # Enhanced classification logic with thresholds
    if is_deep_bass and rms > 0.7:
        return "heavy"  # Very deep bass
    elif is_bass and rms > 0.5:
        return "medium"  # Normal bass
    elif is_very_high_pitched and rms > 0.4:
        return "sharp"  # Very high-pitched sounds
    elif is_high_pitched and rms > 0.3:
        return "light"  # High-pitched sounds
    elif is_very_rigid and rms > 0.5:
        return "rigid"  # Very rigid sounds
    elif is_rigid and rms > 0.4:
        return "medium"  # Rigid sounds
    elif is_strong_transition and rms > 0.6:
        if rolloff > 0.7:
            return "success"  # Strong positive transition
        elif rolloff < 0.3:
            return "error"  # Strong negative transition
        else:
            return "warning"  # Strong neutral transition
    elif is_transition and rms > 0.5:
        if rolloff > 0.6:
            return "success"  # Positive transition
        elif rolloff < 0.4:
            return "error"  # Negative transition
        else:
            return "warning"  # Neutral transition
    elif rms > 0.7 and bandwidth > 0.6:
        return "heavy"
    elif rms > 0.4 and rolloff > 0.5:
        return "medium"
    elif rms > 0.2:
        return "light"
    else:
        return "soft"

def smooth_data(data, window_length=11):
    return savgol_filter(data, window_length, 3)

def main(input_file, json_path, fps=60):
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        return
    
    # Check if input file is audio or video
    if not (is_audio_file(input_file) or is_video_file(input_file)):
        print(f"Error: '{input_file}' is not a supported audio or video file.")
        print("Supported audio formats: .mp3, .wav, .flac, .aac, .ogg, .m4a, .wma")
        print("Supported video formats: .mp4, .avi, .mov, .mkv, .wmv, .flv, .webm, .m4v")
        return
    
    print(f"Processing {'audio' if is_audio_file(input_file) else 'video'} file: {input_file}")
    
    # Extract audio (or use directly if it's already audio)
    if is_audio_file(input_file):
        audio_path = input_file
        temp_audio = False
    else:
        audio_path = 'temp_audio.wav'
        temp_audio = True
        if not extract_audio(input_file, audio_path):
            print("Failed to extract audio from video file.")
            return
    
    # Extract audio features
    try:
        features = extract_audio_features(audio_path)
    except Exception as e:
        print(f"Error extracting audio features: {e}")
        if temp_audio and os.path.exists(audio_path):
            os.remove(audio_path)
        return
    
    # Get media duration
    media_duration = get_media_duration(input_file)
    if media_duration == 0.0:
        print("Could not determine media duration.")
        if temp_audio and os.path.exists(audio_path):
            os.remove(audio_path)
        return
    
    n_frames = int(media_duration * fps)

    # Interpolation to cover the entire media
    rms_interp = np.interp(np.linspace(0, len(features['rms'])-1, n_frames), np.arange(len(features['rms'])), features['rms'])
    freqs_interp = np.interp(np.linspace(0, len(features['freqs'])-1, n_frames), np.arange(len(features['freqs'])), features['freqs'])
    rolloff_interp = np.interp(np.linspace(0, len(features['spectral_rolloff'])-1, n_frames), np.arange(len(features['spectral_rolloff'])), features['spectral_rolloff'])
    bandwidth_interp = np.interp(np.linspace(0, len(features['spectral_bandwidth'])-1, n_frames), np.arange(len(features['spectral_bandwidth'])), features['spectral_bandwidth'])

    # Data smoothing
    rms_smooth = smooth_data(rms_interp)
    freqs_smooth = smooth_data(freqs_interp)
    rolloff_smooth = smooth_data(rolloff_interp)
    bandwidth_smooth = smooth_data(bandwidth_interp)

    haptic_data = {
        "metadata": {
            "version": 3,
            "fps": fps,
            "duration": round(media_duration, 2),
            "total_frames": n_frames,
            "input_file": os.path.basename(input_file),
            "file_type": "audio" if is_audio_file(input_file) else "video"
        },
        "haptic_events": []
    }

    # Dynamic threshold based on mean and standard deviation
    intensity_threshold = np.mean(rms_smooth) + 0.5 * np.std(rms_smooth)
    
    for i in range(n_frames):
        t = i / fps
        
        # Calculate intensity
        intensity = float(np.clip(rms_smooth[i] * 2, 0, 1))
        
        # Calculate sharpness
        sharpness = float(np.clip(freqs_smooth[i] / np.max(freqs_smooth), 0, 1)) if np.max(freqs_smooth) > 0 else 0.5
        
        # Determine haptic feedback type
        frame_features = {
            'rms': rms_smooth[i],
            'freqs': freqs_smooth[i],
            'spectral_rolloff': rolloff_smooth[i],
            'spectral_bandwidth': bandwidth_smooth[i]
        }
        haptic_type = determine_haptic_type(frame_features, i)

        # Add only significant events
        if intensity > intensity_threshold and i % 2 == 0:
            haptic_data["haptic_events"].append({
                "time": round(t, 3),
                "intensity": round(intensity, 3),
                "sharpness": round(sharpness, 3),
                "type": haptic_type
            })

    with open(json_path, 'w') as f:
        json.dump(haptic_data, f, indent=2)
    print(f"JSON file generated: {json_path}")
    print(f"Generated {len(haptic_data['haptic_events'])} haptic events")
    
    # Clean up temporary audio file
    if temp_audio and os.path.exists(audio_path):
        os.remove(audio_path)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python haptick_analyze.py <input_file> <output.json>")
        print("Supported formats:")
        print("  Audio: .mp3, .wav, .flac, .aac, .ogg, .m4a, .wma")
        print("  Video: .mp4, .avi, .mov, .mkv, .wmv, .flv, .webm, .m4v")
        sys.exit(1)
    
    main(sys.argv[1], sys.argv[2])