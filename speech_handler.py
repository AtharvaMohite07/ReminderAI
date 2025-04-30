import re
from difflib import get_close_matches

class SpeechHandler:
    def __init__(self, database):
        self.database = database
        # Expanded wake words list
        self.wake_words = [
            "hey assistant", "assistant", "reminder app", "hey reminder", 
            "remind", "reminder", "hello", "hi there", "excuse me",
            "hey there", "yo", "listen"
        ]
        # Keep track of conversation context
        self.context = {
            "last_location": None,
            "last_task": None,
            "last_intent": None,
            "awaiting_confirmation": False
        }
        
    def process_command(self, text):
        """Process spoken command and determine the action"""
        original_text = text
        text = text.lower()
        
        # First, check for corrections or confirmations
        if self._is_correction(text) and self.context["last_intent"]:
            return self._handle_correction(text)
        
        if self._is_confirmation(text) and self.context["awaiting_confirmation"]:
            return self._handle_confirmation(text)
        
        # Extract command after wake word if present
        command = self._extract_command_after_wake_word(text)
        if command:
            text = command  # Use the text after wake word
        
        # Handle basic questions or greetings
        greeting_response = self._handle_greeting(text)
        if greeting_response:
            return greeting_response
            
        # Check for cancellation
        if self._is_cancellation(text):
            self._reset_context()
            return "Okay, I've cancelled that."
            
        # Check for reminder intent
        if self._is_add_reminder_intent(text):
            self.context["last_intent"] = "add"
            # Try to extract location and task
            location, task = self._extract_location_and_task(text)
            
            # If location is unclear but task is clear, ask for location
            if task and not location:
                self.context["last_task"] = task
                self.context["awaiting_confirmation"] = True
                return f"I understood you want to remember '{task}'. Where should I remind you about this?"
                
            # If task is unclear but location is clear, ask for task
            if location and not task:
                self.context["last_location"] = location
                self.context["awaiting_confirmation"] = True
                return f"What would you like me to remind you about when you're at {location}?"
            
            if location and task:
                self.context["last_location"] = location
                self.context["last_task"] = task
                return self._add_reminder(location, task)
            else:
                # Try to infer from past context
                if self.context["last_location"] and "same place" in text or "there too" in text:
                    location = self.context["last_location"]
                    # Try to extract just the task now
                    task = self._extract_task_only(text)
                    if task:
                        return self._add_reminder(location, task)
                
                return "I couldn't understand the location or task. Can you try saying something like 'remind me to buy milk at the grocery store'?"
        
        # Check for get reminders intent
        if self._is_get_reminder_intent(text):
            self.context["last_intent"] = "get"
            location = self._extract_location_for_retrieval(text)
            
            # Handle "same place" references
            if not location and ("same place" in text or "there" in text) and self.context["last_location"]:
                location = self.context["last_location"]
            
            if location:
                self.context["last_location"] = location
                return self._get_reminders(location)
            else:
                self.context["awaiting_confirmation"] = True
                return "Which location would you like to check reminders for?"
        
        # Check for list all locations intent
        if self._is_list_locations_intent(text):
            return self._list_all_locations()
            
        # Original pattern matching as fallback
        pattern_result = self._process_with_patterns(text)
        if pattern_result != "I couldn't understand your command. Please try again.":
            return pattern_result
            
        # Final fallback - try to understand the intent
        return self._general_fallback(text)
    
    def _extract_command_after_wake_word(self, text):
        """Extract the command part after any wake word"""
        for wake_word in self.wake_words:
            if wake_word in text:
                # Get text after wake word
                parts = text.split(wake_word, 1)
                if len(parts) > 1 and parts[1].strip():
                    return parts[1].strip()
        return None
    
    def _is_add_reminder_intent(self, text):
        """Detect if the intent is to add a reminder"""
        # First check for get reminder intent - this should take precedence
        if self._is_get_reminder_intent(text):
            return False
            
        add_keywords = [
            "remind me to", "add reminder", "create reminder", 
            "remember to", "don't forget to", "need to", "add task",
            "add to my list", "remind me about", "make a note",
            "write down", "put on my list", "new reminder",
            "set reminder", "keep in mind", "note that", 
            "should bring", "will need", "must remember"
        ]
        
        for keyword in add_keywords:
            if keyword in text:
                return True
                
        # Make location pattern check more specific
        if (" at " in text or " in " in text or " to " in text) and any(
            action in text for action in ["bring", "buy", "get", "pick", "grab"]):
            return True
                
        return False

    def _is_get_reminder_intent(self, text):
        """Detect if the intent is to get reminders"""
        get_keywords = [
            "what do i need", "what should i", "what was i supposed",
            "remind me what", "what did i need", "show me reminders",
            "tell me reminders", "what are my reminders", "list reminders",
            "check reminders", "check my list", "see my reminders",
            "what's on my list", "my reminders for", "items for",
            "tasks for", "anything for", "what do i have",
            "heading to", "on my way to", "going to"
        ]
        
        for keyword in get_keywords:
            if keyword in text:
                return True
                
        # Additional check for questions about locations
        question_starters = ["what", "tell", "show", "list", "check"]
        location_references = ["at", "in", "for"]
        
        words = text.split()
        if any(word in question_starters for word in words) and any(word in location_references for word in words):
            return True
            
        return False
    
    def _is_list_locations_intent(self, text):
        """Check if user wants to list all locations"""
        list_keywords = [
            "list all locations", "show all locations", "what locations",
            "all my locations", "saved locations", "places i have",
            "where do i have", "all places", "show me everywhere"
        ]
        
        for keyword in list_keywords:
            if keyword in text:
                return True
        return False
        
    def _is_cancellation(self, text):
        """Detect cancellation requests"""
        cancel_keywords = [
            "cancel", "forget it", "never mind", "stop", "ignore that",
            "delete that", "don't do that", "abort", "disregard"
        ]
        
        for keyword in cancel_keywords:
            if keyword in text:
                return True
        return False
        
    def _is_correction(self, text):
        """Detect correction phrases"""
        correction_keywords = [
            "no ", "not ", "incorrect", "wrong", "that's not right",
            "i meant", "i actually meant", "instead", "actually",
            "correction", "that should be", "rather", "change that to",
            "not what i meant"
        ]
        
        for keyword in correction_keywords:
            if keyword in text:
                return True
        return False
        
    def _is_confirmation(self, text):
        """Detect confirmation phrases"""
        confirm_keywords = [
            "yes", "yeah", "correct", "right", "exactly", "that's right",
            "that's it", "confirm", "confirmed", "perfect", "ok", "okay",
            "sounds good", "good", "sure", "definitely", "absolutely",
            "you got it"
        ]
        
        text = text.strip().lower()
        for keyword in confirm_keywords:
            if text == keyword or text.startswith(keyword + " ") or text.endswith(" " + keyword):
                return True
        return False
        
    def _handle_greeting(self, text):
        """Handle basic greetings and help requests"""
        greeting_patterns = {
            r"\b(hi|hello|hey)\b": "Hello! How can I help with your reminders?",
            r"\b(how are you|how's it going)\b": "I'm doing well, thanks for asking! How can I help with your reminders?",
            r"\b(thank you|thanks)\b": "You're welcome! Anything else you need help with?",
            r"\b(help|help me|what can you do)\b": "I can help you remember things based on locations. Try saying 'remind me to bring my umbrella to work' or 'what do I need to do at the grocery store?'"
        }
        
        for pattern, response in greeting_patterns.items():
            if re.search(pattern, text):
                return response
                
        return None
        
    def _handle_correction(self, text):
        """Handle corrections to previous commands"""
        # Try to extract new location and task
        new_location, new_task = self._extract_location_and_task(text)
        
        # If correcting an add reminder command
        if self.context["last_intent"] == "add":
            # If user is correcting the location
            if new_location and not new_task and self.context["last_task"]:
                self.context["last_location"] = new_location
                return self._add_reminder(new_location, self.context["last_task"])
                
            # If user is correcting the task
            if new_task and not new_location and self.context["last_location"]:
                self.context["last_task"] = new_task
                return self._add_reminder(self.context["last_location"], new_task)
                
            # If user provided both new location and task
            if new_location and new_task:
                self.context["last_location"] = new_location
                self.context["last_task"] = new_task
                return self._add_reminder(new_location, new_task)
                
        # If correcting a get reminder command
        if self.context["last_intent"] == "get" and new_location:
            self.context["last_location"] = new_location
            return self._get_reminders(new_location)
            
        # If we couldn't understand the correction
        return "I'm not sure what you'd like to correct. Can you try saying your full request again?"
        
    def _handle_confirmation(self, text):
        """Handle confirmation to previous query"""
        self.context["awaiting_confirmation"] = False
        
        # Handle confirmation for adding reminder
        if self.context.get("confirming_add"):
            if self._is_confirmation(text):
                return self._add_reminder(self.context["pending_location"], self.context["pending_task"])
            else:
                self.context["confirming_add"] = False
                return "Okay, I've cancelled that. What would you like to do instead?"
        
        # Handle new location confirmation from fallback
        if self.context.get("confirming_new_location"):
            if self._is_confirmation(text) or "yes" in text.lower():
                self.context["confirming_new_location"] = False
                self.context["last_intent"] = "add"
                # Extract task from the response
                task = self._extract_task_only(text)
                if task:
                    return self._add_reminder(self.context["last_location"], task)
                else:
                    self.context["awaiting_confirmation"] = True
                    return f"What would you like me to remind you about when you're at {self.context['last_location']}?"
            else:
                self.context["confirming_new_location"] = False
                self._reset_context()
                return "Okay, what would you like to do instead?"
        
        # If we were waiting for location confirmation for adding
        if self.context["last_intent"] == "add" and self.context["last_task"]:
            # Extract location from confirmation response
            location = self._extract_location_for_retrieval(text)
            if location:
                self.context["last_location"] = location
                return self._add_reminder(location, self.context["last_task"])
            else:
                return "I still don't understand which location. Please try again with a clear location name."
                
        # If we were waiting for task confirmation for adding
        if self.context["last_intent"] == "add" and self.context["last_location"]:
            # Use the entire text as the task if no clear task extraction
            task = self._extract_task_only(text) or text
            self.context["last_task"] = task
            return self._add_reminder(self.context["last_location"], task)
            
        # If we were waiting for location confirmation for getting
        if self.context["last_intent"] == "get":
            location = self._extract_location_for_retrieval(text)
            if location:
                self.context["last_location"] = location
                return self._get_reminders(location)
            else:
                return "I still don't understand which location. Please try again with a clear location name."
                
        return "I'm sorry, I lost track of our conversation. Can you try again with your complete request?"
    
    def _extract_location_and_task(self, text):
        """Extract location and task from various phrases"""
        # Try various patterns for location extraction
        location_patterns = [
            r"for (?:location|place|store|shop|spot) ([a-z0-9 ]+)",
            r"at (?:the |my |our )?([a-z0-9 ]+)",
            r"to (?:the |my |our )?([a-z0-9 ]+)",
            r"in (?:the |my |our )?([a-z0-9 ]+)",
            r"when (?:i'm|i am|we're|we are) (?:at|in) (?:the |my |our )?([a-z0-9 ]+)",
            r"(?:location|place) (?:is|should be) (?:the |my |our )?([a-z0-9 ]+)",
            r"if i(?:'m| am) (?:at|in|near) (?:the |my |our )?([a-z0-9 ]+)"
        ]
        
        location = None
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                potential_location = match.group(1).strip()
                # Filter out common false positives
                if (len(potential_location.split()) <= 3 and 
                    not any(word in potential_location for word in 
                            ["get", "bring", "buy", "pick", "remember", "forget"])):
                    location = potential_location
                    break
        
        # If no location found, return empty
        if not location:
            # Try to extract just a potential location name from standalone phrases
            standalone_match = re.search(r"(?:^|[.!?])\s*([A-Za-z0-9 ]{2,25})(?:$|[.!?])", text)
            if standalone_match:
                potential_location = standalone_match.group(1).strip()
                # Check if this looks like a valid location name
                if (len(potential_location.split()) <= 3 and
                    not any(word in potential_location.lower() for word in
                           ["remind", "forget", "remember", "need", "want", "get"])):
                    location = potential_location
        
        # Extract task based on common phrases
        task_patterns = [
            r"to (bring|get|buy|pick up|do|make|prepare|grab) ([a-z0-9 ]+)",
            r"about ([a-z0-9 ]+)",
            r"remember (?:to|about)? ([a-z0-9 ]+)",
            r"remind me (?:to|about) ([a-z0-9 ]+)",
            r"don't forget (?:to|about) ([a-z0-9 ]+)",
            r"need to ([a-z0-9 ]+)"
        ]
        
        task = None
        for pattern in task_patterns:
            match = re.search(pattern, text)
            if match:
                # Some patterns have verb + task, others just task
                if len(match.groups()) > 1:
                    verb = match.group(1)
                    task_part = match.group(2)
                    task = f"{verb} {task_part}"
                else:
                    task = match.group(1)
                break
        
        # If no task found via patterns, use remaining text
        if not task and location and location in text:
            # Split by location and take what's before or after depending on context
            parts = text.split(location)
            if len(parts) > 1:
                if any(kw in parts[0].lower() for kw in ["remind me", "remember", "forget", "need"]):
                    potential_task = parts[1].strip()
                    # Clean up the potential task
                    task = re.sub(r'^[,.;: ]+(to|about)?', '', potential_task).strip()
                else:
                    potential_task = parts[0].strip()
                    # Remove common prefixes
                    prefixes = ["remind me to", "remember to", "don't forget to", "need to"]
                    for prefix in prefixes:
                        if potential_task.endswith(prefix):
                            potential_task = potential_task[:-len(prefix)].strip()
                            break
                    task = potential_task
        
        return location, task
    
    def _extract_task_only(self, text):
        """Extract just the task from text without location context"""
        # Try to extract tasks using specific patterns
        task_only_patterns = [
            r"(?:to )?(bring|get|buy|pick up|do|make|prepare|grab) ([a-z0-9 ]+)",
            r"(?:about )([a-z0-9 ]+)",
            r"remember (?:to|about)? ([a-z0-9 ]+)",
            r"(?:remind me )(?:to|about) ([a-z0-9 ]+)",
            r"(?:don't forget )(?:to|about) ([a-z0-9 ]+)"
        ]
        
        for pattern in task_only_patterns:
            match = re.search(pattern, text)
            if match:
                # Handle single or multiple groups
                if len(match.groups()) > 1:
                    verb = match.group(1)
                    task_part = match.group(2)
                    return f"{verb} {task_part}"
                else:
                    return match.group(1)
        
        # If no specific task patterns match, try to clean up the entire text
        # Remove common prefixes/phrases
        task_text = text.lower()
        
        # First remove confirmation words that might appear at the beginning
        confirmation_prefixes = ["yes", "yeah", "sure", "ok", "okay", "right", "correct"]
        for prefix in confirmation_prefixes:
            if task_text.startswith(prefix):
                task_text = task_text[len(prefix):].strip()
                # Remove any leading connectors
                task_text = re.sub(r'^[,. ]*(i|to|about|it\'s|its|is|should be)', '', task_text).strip()
                break
                
        # Remove other common prefixes
        prefixes = [
            "remind me to", "remember to", "don't forget to", "need to",
            "i need to", "i want to", "i should", "i must",
            "to", "about", "it's", "its", "is", "the task is"
        ]
        for prefix in prefixes:
            if task_text.startswith(prefix):
                task_text = task_text[len(prefix):].strip()
                break
                
        return task_text if task_text else None
    
    def _extract_location_for_retrieval(self, text):
        """Extract location from retrieval requests"""
        # First clean up question phrases to avoid them being detected as locations
        text = re.sub(r'^what\s+(do|should|did)\s+i\s+(need|have|bring|get|buy|do)\s+(?:at|in|for)\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^tell\s+me\s+what\s+(?:i|to)\s+(?:need|have|bring|get|buy|do)\s+(?:at|in|for)\s+', '', text, flags=re.IGNORECASE)
        
        patterns = [
            r"going to (?:the |my |our )?([a-z0-9 ]+)",
            r"at (?:the |my |our )?([a-z0-9 ]+)$",  # Added $ to match end of string
            r"for (?:the |my |our )?([a-z0-9 ]+)$",
            r"in (?:the |my |our )?([a-z0-9 ]+)$",
            r"to (?:the |my |our )?([a-z0-9 ]+)$",
            r"(?:location|place) (?:is|should be) (?:the |my |our )?([a-z0-9 ]+)",
            r"(grocery|store|shop|mall|work|office|school|gym|home)"
        ]
        
        # First try exact location matches from database
        location_words = self._get_all_locations()
        if location_words:
            for word in location_words:
                word_pattern = r'\b' + re.escape(word.lower()) + r'\b'
                if re.search(word_pattern, text.lower()):
                    return word
        
        # Then try patterns
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                location = match.group(1).strip()
                # Verify it's not a question word or common verb
                if not any(word in location for word in ["what", "where", "when", "need", "have", "bring", "get"]):
                    return location
        
        # Finally try fuzzy matching if no exact match found
        if location_words:
            words = text.split()
            for word in words:
                if len(word) > 3:  # Only match words of reasonable length
                    matches = get_close_matches(word.lower(), [loc.lower() for loc in location_words], n=1, cutoff=0.8)
                    if matches:
                        # Find the original case version
                        for loc in location_words:
                            if loc.lower() == matches[0]:
                                return loc
        
        return None
    
    def _get_all_locations(self):
        """Get all locations from the database for matching"""
        try:
            conn = self.database._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM locations")
            locations = [row[0] for row in cursor.fetchall()]
            conn.close()
            return locations
        except:
            return []
    
    def _list_all_locations(self):
        """List all available locations"""
        locations = self._get_all_locations()
        
        if not locations:
            return "You don't have any saved locations yet."
            
        if len(locations) == 1:
            return f"You have one saved location: {locations[0]}."
            
        response = f"You have {len(locations)} saved locations: "
        for i, location in enumerate(locations):
            if i == len(locations) - 1:
                response += f"and {location}."
            else:
                response += f"{location}, "
                
        return response
    
    def _process_with_patterns(self, text):
        """Fall back to original pattern matching"""
        # Original patterns
        add_pattern1 = r"add (task|item) to reminder for (.+?) for next time"
        add_pattern2 = r"next time remind me to (bring|do) (.+?) for location (.+)"
        get_pattern = r"i am going to (.+?) remind me what"
        
        # Check for add reminder patterns
        add_match1 = re.search(add_pattern1, text)
        if add_match1:
            location = add_match1.group(2).strip()
            task_match = re.search(r"(.+?) add task", text)
            if task_match:
                task = task_match.group(1).strip()
                return self._add_reminder(location, task)
            else:
                return "I couldn't understand the task. Please try again."
        
        add_match2 = re.search(add_pattern2, text)
        if add_match2:
            action_type = add_match2.group(1)  # bring or do
            task = add_match2.group(2).strip()
            location = add_match2.group(3).strip()
            return self._add_reminder(location, f"{action_type} {task}")
        
        # Check for get reminders pattern
        get_match = re.search(get_pattern, text)
        if get_match:
            location = get_match.group(1).strip()
            return self._get_reminders(location)
        
        return "I couldn't understand your command. Please try again."
    
    def _add_reminder(self, location, task):
        """Add a reminder to the database"""
        # First time called - ask for confirmation
        if not self.context.get("confirming_add"):
            self.context["confirming_add"] = True
            self.context["pending_location"] = location
            self.context["pending_task"] = task
            self.context["awaiting_confirmation"] = True
            return f"Just to confirm - you want me to remind you to '{task}' when you're at {location}. Is that correct?"
        
        # If we get here, user has confirmed
        self.context["last_location"] = location
        self.context["last_task"] = task
        self.context["awaiting_confirmation"] = False
        self.context["confirming_add"] = False
        
        # Clean up the task text
        task = task.strip()
        task = re.sub(r'^(to|about|that)\s+', '', task)
        
        self.database.add_reminder(location, task)
        return f"I've added '{task}' to your reminders for {location}."
    
    def _get_reminders(self, location):
        """Get reminders for a location"""
        # Store in context
        self.context["last_location"] = location
        self.context["awaiting_confirmation"] = False
        
        reminders = self.database.get_reminders(location)
        
        if not reminders:
            return f"You don't have any reminders for {location}."
        
        response = f"For {location}, you need to: "
        for i, (reminder_id, task) in enumerate(reminders):
            response += f"{i+1}. {task}. "
        
        return response
        
    def _general_fallback(self, text):
        """Handle cases where we can't determine the intent"""
        # Check if text contains any location from our database
        locations = self._get_all_locations()
        
        location_in_text = None
        for location in locations:
            if location.lower() in text.lower():
                location_in_text = location
                break
                
        if location_in_text:
            # We found a location, ask if user wants to add or get reminders
            self.context["last_location"] = location_in_text
            self.context["awaiting_confirmation"] = True
            return f"I noticed you mentioned {location_in_text}. Do you want to add a reminder or check existing reminders for this location?"
            
        # Check if the text is very short, might just be a location name
        if len(text.split()) <= 3:
            # Treat as potential new location
            self.context["last_location"] = text
            self.context["awaiting_confirmation"] = True
            self.context["confirming_new_location"] = True  # Add this flag
            return f"Do you want to add a reminder for {text}? If so, what should I remind you about?"
            
        return "I'm not sure what you'd like to do. Try saying something like 'remind me to bring my umbrella to work' or 'what do I need at the grocery store?'"
        
    def _reset_context(self):
        """Reset the conversation context"""
        self.context = {
            "last_location": None,
            "last_task": None,
            "last_intent": None,
            "awaiting_confirmation": False,
            "confirming_add": False,
            "confirming_new_location": False
        }