import sqlite3
import os

class Database:
    def __init__(self, db_path='reminders.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database and create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create locations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create reminders table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def add_reminder(self, location_name, task):
        """Add a reminder for a specific location"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get or create location
        cursor.execute("SELECT id FROM locations WHERE name=? COLLATE NOCASE", (location_name,))
        result = cursor.fetchone()
        
        if result:
            location_id = result[0]
        else:
            cursor.execute("INSERT INTO locations (name) VALUES (?)", (location_name,))
            location_id = cursor.lastrowid
        
        # Add reminder
        cursor.execute("INSERT INTO reminders (location_id, task) VALUES (?, ?)", 
                      (location_id, task))
        
        conn.commit()
        conn.close()
        return True
    
    def get_reminders(self, location_name):
        """Get all reminders for a specific location"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.id, r.task
            FROM reminders r
            JOIN locations l ON r.location_id = l.id
            WHERE l.name=? COLLATE NOCASE AND r.completed=0
        """, (location_name,))
        
        reminders = cursor.fetchall()
        conn.close()
        
        return reminders
    
    def mark_reminder_completed(self, reminder_id):
        """Mark a reminder as completed"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE reminders SET completed=1 WHERE id=?", (reminder_id,))
        
        conn.commit()
        conn.close()
        return True