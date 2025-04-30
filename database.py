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
    
    def get_similar_tasks(self, location, task):
        """
        Find similar tasks at the given location to prevent duplicates
        Returns list of similar tasks based on string similarity
        """
        cursor = self._get_connection().cursor()
        
        # Get all tasks for this location
        cursor.execute("""
            SELECT r.task 
            FROM reminders r
            JOIN locations l ON r.location_id = l.id
            WHERE l.name = ? AND r.completed = 0
        """, (location,))
        
        existing_tasks = [row[0] for row in cursor.fetchall()]
        
        # Use difflib to find similar tasks
        from difflib import SequenceMatcher
        
        similar_tasks = []
        for existing_task in existing_tasks:
            similarity = SequenceMatcher(None, task.lower(), existing_task.lower()).ratio()
            if similarity > 0.6:  # Threshold for similarity (60%)
                similar_tasks.append({
                    'task': existing_task,
                    'similarity': similarity
                })
        
        # Sort by similarity score
        similar_tasks.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similar_tasks
    
    def get_all_locations_with_counts(self):
        """Get all locations and their reminder counts"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT l.name, COUNT(r.id) as count
                FROM locations l
                LEFT JOIN reminders r ON l.id = r.location_id 
                    AND r.completed = 0
                GROUP BY l.name
                ORDER BY count DESC, l.name
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"Database error in get_all_locations_with_counts: {str(e)}")
            return []