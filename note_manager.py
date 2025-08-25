import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import uuid

class NoteManager:
    def __init__(self, data_file: str = "data/notes.json"):
        # Use the provided data_file (per-user file for privacy)
        self.data_file = data_file
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure the data directory exists"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            self.save_notes([])
    
    def load_notes(self) -> List[Dict]:
        """Load notes from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_notes(self, notes: List[Dict]) -> bool:
        """Save notes to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(notes, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving notes: {e}")
            return False
    
    def create_note(self, title: str, content: str) -> Optional[str]:
        """Create a new note and return its ID"""
        try:
            notes = self.load_notes()
            note_id = str(uuid.uuid4())
            current_time = datetime.now().isoformat()
            
            new_note = {
                'id': note_id,
                'title': title,
                'content': content,
                'created_at': current_time,
                'updated_at': current_time
            }
            
            notes.append(new_note)
            
            if self.save_notes(notes):
                return note_id
            return None
        except Exception as e:
            print(f"Error creating note: {e}")
            return None
    
    def get_note(self, note_id: str) -> Optional[Dict]:
        """Get a specific note by ID"""
        try:
            notes = self.load_notes()
            for note in notes:
                if note['id'] == note_id:
                    return note
            return None
        except Exception as e:
            print(f"Error getting note: {e}")
            return None
    
    def get_all_notes(self) -> List[Dict]:
        """Get all notes sorted by creation date (newest first)"""
        try:
            notes = self.load_notes()
            # Sort by creation date, newest first
            return sorted(notes, key=lambda x: x['created_at'], reverse=True)
        except Exception as e:
            print(f"Error getting all notes: {e}")
            return []
    
    def update_note(self, note_id: str, title: str, content: str) -> bool:
        """Update an existing note"""
        try:
            notes = self.load_notes()
            
            for i, note in enumerate(notes):
                if note['id'] == note_id:
                    notes[i]['title'] = title
                    notes[i]['content'] = content
                    notes[i]['updated_at'] = datetime.now().isoformat()
                    return self.save_notes(notes)
            
            return False  # Note not found
        except Exception as e:
            print(f"Error updating note: {e}")
            return False
    
    def delete_note(self, note_id: str) -> bool:
        """Delete a note by ID"""
        try:
            notes = self.load_notes()
            original_length = len(notes)
            notes = [note for note in notes if note['id'] != note_id]
            
            if len(notes) < original_length:
                return self.save_notes(notes)
            return False  # Note not found
        except Exception as e:
            print(f"Error deleting note: {e}")
            return False
    
    def search_notes(self, query: str) -> List[Dict]:
        """Search notes by title or content"""
        try:
            notes = self.get_all_notes()
            query = query.lower()
            
            matching_notes = []
            for note in notes:
                if (query in note['title'].lower() or 
                    query in note['content'].lower()):
                    matching_notes.append(note)
            
            return matching_notes
        except Exception as e:
            print(f"Error searching notes: {e}")
            return []
    
    def get_notes_count(self) -> int:
        """Get total number of notes"""
        try:
            notes = self.load_notes()
            return len(notes)
        except Exception as e:
            print(f"Error getting notes count: {e}")
            return 0
