# ReminderAI: Location-Based Voice Reminder System

A modern web application that lets you create and retrieve reminders based on location names using natural voice commands. Simply tell the app what you need to remember for specific places, and it will remind you when you're headed there.

## Features

- **Voice-Activated Commands**: Speak naturally to add or retrieve reminders
- **Wake Word Detection**: Activate with phrases like "Hey Assistant" or "Reminder App"
- **Continuous Listening Mode**: Always-on assistant similar to Alexa/Google Home
- **Natural Language Understanding**: Flexible command recognition that understands various phrases
- **Location-Based Organization**: Organize reminders by location name (not GPS coordinates)
- **Voice Feedback**: Spoken responses for hands-free operation
- **Modern UI**: Clean, responsive interface with dark mode support
- **Mobile-Friendly**: Works on smartphones and tablets
- **Offline Capable**: Local database storage for your reminders

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript, Font Awesome
- **Backend**: Python, Flask
- **Database**: SQLite
- **Voice Recognition**: Web Speech API
- **Speech Synthesis**: Web Speech API

## Installation

### Prerequisites

- Python 3.7+
- SQLite3
- Web browser with speech recognition support (Chrome recommended)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/AtharvaMohite07/ReminderAI.git
   cd ReminderAI
   ```

2. Install required dependencies:
   ```
   pip install flask
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Usage

### Voice Commands

#### Adding Reminders:

- "Remember to bring umbrella next time I'm at work"
- "Remind me to buy milk at grocery store"
- "Don't forget to check the printer at office"
- "I need to return book at library"

#### Retrieving Reminders:

- "I'm going to the grocery store, what did I need to get?"
- "What should I bring to work?"
- "Show me my reminders for the library"
- "What do I need to do at home?"

### Web Interface

1. **Dashboard**: Overview of all your reminders
2. **Voice Controls**: Record button for immediate commands or toggle Assistant mode
3. **Reminders List**: View and manage reminders for specific locations
4. **Dark Mode**: Toggle between light and dark themes

## Project Structure

```
ReminderAI/
├── app.py                # Flask application & API endpoints
├── database.py           # Database operations
├── speech_handler.py     # Voice recognition and processing
├── static/
│   ├── js/
│   │   └── main.js       # Frontend logic
│   └── css/
│       └── style.css     # Styling
└── templates/
    └── index.html        # Web interface
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/process` | POST | Process voice command |
| `/api/locations` | GET | Get all saved locations |
| `/api/reminders/<location>` | GET | Get reminders for a location |
| `/api/reminders/<id>/complete` | POST | Mark reminder as completed |

## Voice Recognition Support

This application uses the Web Speech API which is best supported in:
- Google Chrome
- Microsoft Edge
- Safari (macOS)

Firefox and other browsers may have limited support or require enabling flags.

## Customization

### Adding Custom Wake Words

Edit the `wake_words` list in speech_handler.py to add your preferred activation phrases:

```python
self.wake_words = [
    "hey assistant", "assistant", "reminder app", "hey reminder", 
    # Add your custom wake words here
    "computer", "jarvis", "your-word-here"
]
```

### Language Support

Change the recognition language in `main.js`:

```javascript
recognition.lang = 'en-US'; // Change to your preferred language code
```

## Troubleshooting

### Common Issues

- **Microphone Access**: Ensure your browser has permission to use the microphone
- **Speech Recognition Not Working**: Make sure you're using a supported browser
- **Database Errors**: Check file permissions for the SQLite database

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Font Awesome for the icons
- Google Fonts for the Inter font family
- The Flask team for the excellent web framework

## Future Enhancements

- User accounts and cloud sync
- Export/import reminders
- GPS-based location detection
- Reminder categories and tags
- Mobile app version

---

Created by Atharva Mohite - [GitHub Profile](https://github.com/AtharvaMohite07)