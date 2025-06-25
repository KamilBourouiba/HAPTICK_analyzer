# HAPTICK Analyzer

A Python tool that analyzes video/audio content and generates haptic feedback patterns for iOS applications. The tool extracts audio features and creates JSON files with haptic events that can be used with iOS haptic feedback generators.

## Features

- **Multi-Format Support**: Accepts any audio or video file format supported by FFmpeg
- **Audio Normalization**: Ensures consistent results between audio and video files
- **Audio Analysis**: Extracts RMS, spectral centroid, rolloff, and bandwidth from audio
- **Haptic Classification**: Classifies sounds into different haptic feedback types
- **iOS Integration**: Generates JSON files compatible with iOS haptic feedback systems
- **Multiple Haptic Types**: Supports all iOS haptic feedback types (impact and notification)

## Audio Processing

### Normalization
The tool automatically normalizes all audio to a standard RMS level (0.1) to ensure consistent haptic feedback generation regardless of the source file's volume level. This means:

- Audio files and their corresponding video files will produce identical haptic patterns
- Loud and quiet files are analyzed on the same scale
- The normalization factor is included in the output metadata for reference

### Consistency
All files (audio and video) go through the same audio extraction and normalization process:
1. Extract/convert audio to WAV format (22050Hz, mono)
2. Normalize to standard RMS level
3. Analyze audio features
4. Generate haptic events

This ensures that `song.mp3` and `song.mp4` (containing the same audio) will produce nearly identical haptic patterns.

## Supported File Formats

### Audio Formats
- `.mp3` - MPEG Audio Layer 3
- `.wav` - Waveform Audio File Format
- `.flac` - Free Lossless Audio Codec
- `.aac` - Advanced Audio Coding
- `.ogg` - Ogg Vorbis
- `.m4a` - MPEG-4 Audio
- `.wma` - Windows Media Audio

### Video Formats
- `.mp4` - MPEG-4 Video
- `.avi` - Audio Video Interleave
- `.mov` - QuickTime Movie
- `.mkv` - Matroska Video
- `.wmv` - Windows Media Video
- `.flv` - Flash Video
- `.webm` - WebM Video
- `.m4v` - iTunes Video

## Supported Haptic Feedback Types

### Impact Feedback (UIImpactFeedbackGenerator)
- `heavy`: Very deep bass and intense sounds
- `medium`: Normal bass and rigid sounds
- `light`: High-pitched sounds
- `soft`: Very soft sounds
- `rigid`: Very rigid/metallic sounds

### Notification Feedback (UINotificationFeedbackGenerator)
- `success`: Positive transitions
- `warning`: Neutral transitions
- `error`: Negative transitions

## Installation

1. Install required dependencies:
```bash
pip install numpy librosa ffmpeg-python scipy
```

2. Install FFmpeg (required for audio extraction):
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt install ffmpeg`
   - Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)

## Usage

```bash
python haptick_analyze.py <input_file> <output_haptics.json>
```

### Examples
```bash
# Process a video file
python haptick_analyze.py video.mp4 haptics.json

# Process an audio file
python haptick_analyze.py music.mp3 haptics.json

# Process different formats
python haptick_analyze.py movie.avi haptics.json
python haptick_analyze.py song.flac haptics.json
python haptick_analyze.py podcast.wav haptics.json
```

### Parameters
- `<input_file>`: Path to the input audio or video file
- `<output_haptics.json>`: Path for the output JSON file

### Optional Parameters
You can modify the FPS in the `main()` function call:
```python
main(sys.argv[1], sys.argv[2], fps=60)  # Default is 60 FPS
```

## Output Format

The tool generates a JSON file with the following structure:

```json
{
  "metadata": {
    "version": 3,
    "fps": 60,
    "duration": 120.5,
    "total_frames": 7230,
    "input_file": "example.mp3",
    "file_type": "audio",
    "media_duration": 120.5,
    "audio_duration": 120.47,
    "normalization_factor": 2.4567
  },
  "haptic_events": [
    {
      "time": 1.234,
      "intensity": 0.567,
      "sharpness": 0.789,
      "type": "heavy"
    }
  ]
}
```

### Event Properties
- `time`: Timestamp in seconds
- `intensity`: Vibration intensity (0-1)
- `sharpness`: Sound sharpness (0-1)
- `type`: Haptic feedback type

### Metadata Properties
- `version`: JSON format version
- `fps`: Frames per second used for analysis
- `duration`: Total duration used for analysis
- `total_frames`: Total number of frames analyzed
- `input_file`: Original filename
- `file_type`: "audio" or "video"
- `media_duration`: Duration from the original file
- `audio_duration`: Duration from the extracted audio
- `normalization_factor`: Audio level adjustment factor applied

## Detection Logic

### Bass Detection
- **Deep Bass**: Frequency < 100 Hz, RMS > 0.5 → `heavy`
- **Normal Bass**: Frequency < 200 Hz, RMS > 0.3 → `medium`

### High-Pitched Sound Detection
- **Very High**: Frequency > 3000 Hz, Rolloff > 0.7 → `sharp`
- **High**: Frequency > 2000 Hz, Rolloff > 0.6 → `light`

### Rigid Sound Detection
- **Very Rigid**: Bandwidth > 0.84, Medium Rolloff → `rigid`
- **Rigid**: Bandwidth > 0.7, Medium Rolloff → `medium`

### Transition Detection
- **Strong Transitions**: Large intensity changes
- **Positive**: High rolloff → `success`
- **Negative**: Low rolloff → `error`
- **Neutral**: Medium rolloff → `warning`

## Error Handling

The tool includes comprehensive error handling for:
- **File Validation**: Checks if input file exists and is supported
- **Audio Extraction**: Handles FFmpeg errors gracefully
- **Feature Extraction**: Manages librosa processing errors
- **Duration Detection**: Validates media duration

## iOS Integration

To use the generated JSON file in your iOS app:

```swift
import UIKit

class HapticManager {
    private let impactGenerator = UIImpactFeedbackGenerator(style: .heavy)
    private let notificationGenerator = UINotificationFeedbackGenerator()
    
    func playHapticEvent(_ event: HapticEvent) {
        switch event.type {
        case "heavy", "medium", "light", "soft", "rigid":
            let style = UIImpactFeedbackGenerator.FeedbackStyle(rawValue: event.type) ?? .medium
            let generator = UIImpactFeedbackGenerator(style: style)
            generator.impactOccurred()
        case "success":
            notificationGenerator.notificationOccurred(.success)
        case "warning":
            notificationGenerator.notificationOccurred(.warning)
        case "error":
            notificationGenerator.notificationOccurred(.error)
        default:
            break
        }
    }
}
```

## Configuration

You can adjust detection thresholds in the `determine_haptic_type()` function:

```python
# Detection thresholds
BASS_FREQ_THRESHOLD = 200      # Hz
HIGH_FREQ_THRESHOLD = 2000     # Hz
TRANSITION_THRESHOLD = 0.4     # Intensity change
RIGID_BANDWIDTH_THRESHOLD = 0.7 # Spectral bandwidth
```

You can also modify the audio normalization level in `extract_audio_features()`:

```python
target_rms = 0.1  # Standard RMS level for normalization
```

## Requirements

- Python 3.7+
- NumPy
- Librosa
- FFmpeg
- SciPy 