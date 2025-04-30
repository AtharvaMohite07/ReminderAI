from flask import Flask, request, jsonify, render_template
from database import Database
from speech_handler import SpeechHandler

app = Flask(__name__)  # This line is crucial - 'app' must be the name
db = Database()
speech_handler = SpeechHandler(db)

@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_speech():
    """Process speech command"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No speech text provided'}), 400
    
    response = speech_handler.process_command(text)
    return jsonify({'response': response})

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all locations for autocomplete"""
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM locations")
    locations = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({'locations': locations})

@app.route('/api/reminders/<location>', methods=['GET'])
def get_reminders(location):
    """Get reminders for a specific location"""
    reminders = db.get_reminders(location)
    return jsonify({'reminders': [{'id': r[0], 'task': r[1]} for r in reminders]})

@app.route('/api/reminders/<int:reminder_id>/complete', methods=['POST'])
def complete_reminder(reminder_id):
    """Mark a reminder as completed"""
    db.mark_reminder_completed(reminder_id)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)