# HAPTICK Analyzer

A Python tool that analyzes video/audio content and generates haptic feedback patterns for iOS applications. The tool extracts audio features and creates JSON files with haptic events that can be used with iOS haptic feedback generators.

## Features

- **Audio Analysis**: Extracts RMS, spectral centroid, rolloff, and bandwidth from audio
- **Haptic Classification**: Classifies sounds into different haptic feedback types
- **iOS Integration**: Generates JSON files compatible with iOS haptic feedback systems
- **Multiple Haptic Types**: Supports all iOS haptic feedback types (impact and notification)

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
python haptick_analyze.py input_video.mp4 output_haptics.json
```

### Parameters
- `input_video.mp4`: Path to the input video file
- `output_haptics.json`: Path for the output JSON file

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
    "total_frames": 7230
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

## Requirements

- Python 3.7+
- NumPy
- Librosa
- FFmpeg
- SciPy

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues and enhancement requests! 