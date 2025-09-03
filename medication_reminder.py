import schedule
import time
import threading
from datetime import datetime, timedelta
import re
import json
from flask_socketio import emit

class MedicationReminder:
    def __init__(self, socketio=None, db=None, app=None):
        self.reminder_thread = None
        self.is_running = False
        self.socketio = socketio
        self.db = db
        self.app = app  # Store Flask app instance for context
        self.active_reminders = {}  # Store active reminders by user_id
    
    def setup_reminders_for_user(self, medication, user_id):
        """Set up reminders for a medication based on its frequency for a specific user"""
        # This method will be called from the main app with the database context
        # The actual reminder creation is handled in the main app
        pass

    def start_reminder_service(self):
        """Start the active reminder checking service"""
        if not self.is_running:
            self.is_running = True
            self.reminder_thread = threading.Thread(target=self._reminder_loop, daemon=True)
            self.reminder_thread.start()
            print("🔔 Medication reminder service started")

    def stop_reminder_service(self):
        """Stop the reminder service"""
        self.is_running = False
        if self.reminder_thread:
            self.reminder_thread.join(timeout=1)
        print("🔕 Medication reminder service stopped")

    def _reminder_loop(self):
        """Main reminder checking loop - runs continuously"""
        while self.is_running:
            try:
                self._check_and_send_reminders()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"❌ Reminder loop error: {e}")
                time.sleep(60)  # Wait longer on error

    def _check_and_send_reminders(self):
        """Check for due reminders and send alerts"""
        if not self.db or not self.app:
            return

        try:
            # Use Flask application context
            with self.app.app_context():
                # Import here to avoid circular imports
                from app import Medication, Reminder, User

                current_time = datetime.now()
                current_time_str = current_time.strftime('%H:%M')

                # Get all active reminders that are due now (within 1 minute)
                due_reminders = self.db.session.query(Reminder).join(Medication).join(User).filter(
                    Reminder.is_active == True,
                    Medication.is_active == True,
                    User.is_active == True
                ).all()

                for reminder in due_reminders:
                    reminder_time_str = reminder.time.strftime('%H:%M')

                    # Check if it's time for this reminder (within 1 minute)
                    if self._is_time_match(current_time_str, reminder_time_str):
                        # Check if we haven't already sent this reminder today
                        if not self._reminder_sent_today(reminder):
                            self._send_reminder_alert(reminder)

        except Exception as e:
            print(f"❌ Error checking reminders: {e}")

    def _is_time_match(self, current_time_str, reminder_time_str):
        """Check if current time matches reminder time (within 1 minute)"""
        try:
            current_hour, current_min = map(int, current_time_str.split(':'))
            reminder_hour, reminder_min = map(int, reminder_time_str.split(':'))

            current_total_min = current_hour * 60 + current_min
            reminder_total_min = reminder_hour * 60 + reminder_min

            # Within 1 minute
            return abs(current_total_min - reminder_total_min) <= 1
        except:
            return False

    def _reminder_sent_today(self, reminder):
        """Check if reminder was already sent today"""
        if not reminder.last_taken:
            return False

        today = datetime.now().date()
        last_taken_date = reminder.last_taken.date()

        return last_taken_date == today

    def _send_reminder_alert(self, reminder):
        """Send reminder alert to user"""
        try:
            # Use Flask application context for database operations
            with self.app.app_context():
                # Update last_taken to prevent duplicate alerts
                reminder.last_taken = datetime.now()
                self.db.session.commit()

                # Prepare reminder data
                alert_data = {
                    'type': 'medication_reminder',
                    'medication_id': reminder.medication_id,
                    'medication_name': reminder.medication.name,
                    'dosage': reminder.medication.dosage,
                    'frequency': reminder.medication.frequency,
                    'time': reminder.time.strftime('%H:%M'),
                    'instructions': reminder.medication.instructions or '',
                    'timestamp': datetime.now().isoformat()
                }

                # Send WebSocket notification
                if self.socketio:
                    self.socketio.emit('medication_reminder', alert_data, room=f'user_{reminder.user_id}')
                    print(f"🔔 Sent reminder for {reminder.medication.name} to user {reminder.user_id}")

                # Store in active reminders for frontend polling
                if reminder.user_id not in self.active_reminders:
                    self.active_reminders[reminder.user_id] = []

                self.active_reminders[reminder.user_id].append(alert_data)

        except Exception as e:
            print(f"❌ Error sending reminder: {e}")

    def get_active_reminders_for_user(self, user_id):
        """Get active reminders for a user"""
        return self.active_reminders.get(user_id, [])

    def clear_reminder_for_user(self, user_id, medication_id):
        """Clear a specific reminder for a user"""
        if user_id in self.active_reminders:
            self.active_reminders[user_id] = [
                r for r in self.active_reminders[user_id]
                if r['medication_id'] != medication_id
            ]

    def check_reminders(self, medications):
        """Check which medications need reminders now (legacy method for testing)"""
        current_time = datetime.now()
        due_reminders = []

        for medication in medications:
            # Parse the frequency to get reminder times
            reminder_times = self.parse_frequency(medication.get('frequency', 'daily'))

            for reminder_time in reminder_times:
                # Convert reminder_time string to datetime
                try:
                    hour, minute = map(int, reminder_time.split(':'))
                    reminder_datetime = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

                    # Check if this reminder is due (within 5 minutes)
                    time_diff = abs((current_time - reminder_datetime).total_seconds())

                    if time_diff <= 300:  # Within 5 minutes
                        due_reminders.append({
                            'medication_id': medication.get('id'),
                            'medication_name': medication.get('name'),
                            'dosage': medication.get('dosage'),
                            'time': reminder_time,
                            'user_id': medication.get('user_id')
                        })

                except ValueError:
                    continue

        return due_reminders
    
    def parse_frequency(self, frequency):
        """Parse frequency string and return list of reminder times"""
        frequency_lower = frequency.lower()

        # Enhanced parsing for Indian prescription formats

        # Handle specific timing patterns from prescriptions
        if 'morning' in frequency_lower and 'night' in frequency_lower:
            return ['08:00', '20:00']  # Morning and night
        elif 'morning' in frequency_lower and 'afternoon' in frequency_lower:
            return ['08:00', '14:00']  # Morning and afternoon
        elif 'morning' in frequency_lower:
            return ['08:00']  # Morning only
        elif 'night' in frequency_lower:
            return ['20:00']  # Night only

        # Handle Indian prescription abbreviations
        elif 'tds' in frequency_lower or 't.d.s' in frequency_lower:
            return ['08:00', '14:00', '20:00']  # Three times daily
        elif 'q6h' in frequency_lower or 'qid' in frequency_lower:
            return ['06:00', '12:00', '18:00', '00:00']  # Every 6 hours
        elif 'q8h' in frequency_lower:
            return ['08:00', '16:00', '00:00']  # Every 8 hours
        elif 'q12h' in frequency_lower or 'bid' in frequency_lower:
            return ['08:00', '20:00']  # Every 12 hours

        # Handle numeric patterns (1-0-1, 1-1-1, etc.)
        elif '1-0-1' in frequency_lower or '1 0 1' in frequency_lower:
            return ['08:00', '20:00']  # Morning and night
        elif '1-1-1' in frequency_lower or '1 1 1' in frequency_lower:
            return ['08:00', '14:00', '20:00']  # Three times daily
        elif '1-1-0' in frequency_lower or '1 1 0' in frequency_lower:
            return ['08:00', '14:00']  # Morning and afternoon
        elif '0-1-1' in frequency_lower or '0 1 1' in frequency_lower:
            return ['14:00', '20:00']  # Afternoon and night
        elif '1-0-0' in frequency_lower or '1 0 0' in frequency_lower:
            return ['08:00']  # Morning only
        elif '0-0-1' in frequency_lower or '0 0 1' in frequency_lower:
            return ['20:00']  # Night only

        # Handle standard frequencies
        elif 'once daily' in frequency_lower or 'daily' in frequency_lower:
            return ['09:00']  # 9 AM
        elif 'twice daily' in frequency_lower:
            return ['09:00', '21:00']  # 9 AM and 9 PM
        elif 'three times daily' in frequency_lower:
            return ['08:00', '14:00', '20:00']  # 8 AM, 2 PM, 8 PM
        elif 'four times daily' in frequency_lower:
            return ['08:00', '12:00', '16:00', '20:00']  # Every 4 hours
        elif 'every 6 hours' in frequency_lower:
            return ['06:00', '12:00', '18:00', '00:00']  # Every 6 hours
        elif 'every 8 hours' in frequency_lower:
            return ['08:00', '16:00', '00:00']  # Every 8 hours
        elif 'every 12 hours' in frequency_lower:
            return ['08:00', '20:00']  # Every 12 hours

        # Handle SOS (as needed)
        elif 'sos' in frequency_lower or 'as needed' in frequency_lower:
            return []  # No scheduled reminders for SOS medications

        else:
            # Default to once daily
            return ['09:00']

    def add_custom_reminder(self, user_id, medication_id, reminder_time, db_session):
        """Add a custom reminder time for a medication"""
        try:
            from app import Reminder

            # Parse time string
            hour, minute = map(int, reminder_time.split(':'))
            time_obj = datetime.strptime(reminder_time, '%H:%M').time()

            # Check if reminder already exists
            existing = db_session.query(Reminder).filter_by(
                user_id=user_id,
                medication_id=medication_id,
                time=time_obj
            ).first()

            if existing:
                return False, "Reminder already exists for this time"

            # Create new reminder
            reminder = Reminder(
                user_id=user_id,
                medication_id=medication_id,
                time=time_obj,
                is_active=True
            )

            db_session.add(reminder)
            db_session.commit()

            print(f"✅ Added custom reminder: {reminder_time} for medication {medication_id}")
            return True, "Reminder added successfully"

        except Exception as e:
            print(f"❌ Error adding custom reminder: {e}")
            return False, str(e)

    def remove_reminder(self, user_id, medication_id, reminder_time, db_session):
        """Remove a specific reminder"""
        try:
            from app import Reminder

            time_obj = datetime.strptime(reminder_time, '%H:%M').time()

            reminder = db_session.query(Reminder).filter_by(
                user_id=user_id,
                medication_id=medication_id,
                time=time_obj
            ).first()

            if reminder:
                db_session.delete(reminder)
                db_session.commit()
                print(f"✅ Removed reminder: {reminder_time} for medication {medication_id}")
                return True, "Reminder removed successfully"
            else:
                return False, "Reminder not found"

        except Exception as e:
            print(f"❌ Error removing reminder: {e}")
            return False, str(e)

    def update_reminder_time(self, user_id, medication_id, old_time, new_time, db_session):
        """Update an existing reminder time"""
        try:
            from app import Reminder

            old_time_obj = datetime.strptime(old_time, '%H:%M').time()
            new_time_obj = datetime.strptime(new_time, '%H:%M').time()

            reminder = db_session.query(Reminder).filter_by(
                user_id=user_id,
                medication_id=medication_id,
                time=old_time_obj
            ).first()

            if reminder:
                reminder.time = new_time_obj
                db_session.commit()
                print(f"✅ Updated reminder: {old_time} → {new_time} for medication {medication_id}")
                return True, "Reminder updated successfully"
            else:
                return False, "Reminder not found"

        except Exception as e:
            print(f"❌ Error updating reminder: {e}")
            return False, str(e)
    
    def calculate_next_dose(self, medication, last_taken):
        """Calculate the next dose time based on frequency and last taken time"""
        frequency_lower = medication.frequency.lower()
        
        if 'once daily' in frequency_lower or 'daily' in frequency_lower:
            return last_taken + timedelta(days=1)
        elif 'twice daily' in frequency_lower or 'bid' in frequency_lower:
            return last_taken + timedelta(hours=12)
        elif 'three times daily' in frequency_lower or 'tid' in frequency_lower:
            return last_taken + timedelta(hours=8)
        elif 'four times daily' in frequency_lower or 'qid' in frequency_lower:
            return last_taken + timedelta(hours=6)
        elif 'every 6 hours' in frequency_lower or 'q6h' in frequency_lower:
            return last_taken + timedelta(hours=6)
        elif 'every 8 hours' in frequency_lower or 'q8h' in frequency_lower:
            return last_taken + timedelta(hours=8)
        elif 'every 12 hours' in frequency_lower or 'q12h' in frequency_lower:
            return last_taken + timedelta(hours=12)
        else:
            # Default to once daily
            return last_taken + timedelta(days=1)
    
    def _is_reminder_due(self, reminder, current_time):
        """Check if a reminder is due"""
        if not reminder.is_active:
            return False
        
        # Check if it's time for the reminder
        reminder_time = reminder.time
        current_time_only = current_time.time()
        
        # If the reminder time has passed today and we haven't taken it yet
        if current_time_only >= reminder_time:
            # Check if we've taken it today
            if reminder.last_taken:
                last_taken_date = reminder.last_taken.date()
                current_date = current_time.date()
                if last_taken_date == current_date:
                    return False  # Already taken today
            
            return True
        
        return False
    
    def get_upcoming_reminders_for_user(self, user_id, db_session, Reminder):
        """Get upcoming reminders for a specific user"""
        reminders = db_session.query(Reminder).filter_by(user_id=user_id, is_active=True).all()
        return reminders
    
    def mark_medication_taken_for_user(self, medication_id, user_id, db_session, Reminder):
        """Mark a medication as taken for a specific user"""
        reminder = db_session.query(Reminder).filter_by(
            medication_id=medication_id, 
            user_id=user_id
        ).first()
        
        if reminder:
            reminder.last_taken = datetime.utcnow()
            db_session.commit()
            return True
        return False
    
    def get_medication_history_for_user(self, user_id, db_session, MedicationLog, Medication):
        """Get medication history for a specific user"""
        logs = db_session.query(MedicationLog).filter_by(user_id=user_id).order_by(
            MedicationLog.taken_at.desc()
        ).all()
        
        history = []
        for log in logs:
            medication = db_session.query(Medication).get(log.medication_id)
            if medication:
                history.append({
                    'id': log.id,
                    'medication_name': medication.name,
                    'taken_at': log.taken_at,
                    'dosage_taken': log.dosage_taken,
                    'notes': log.notes
                })
        
        return history
    
    def get_user_compliance_stats(self, user_id, db_session, MedicationLog, Medication):
        """Get compliance statistics for a user"""
        # Get all medications for the user
        medications = db_session.query(Medication).filter_by(user_id=user_id, is_active=True).all()
        
        stats = {}
        for medication in medications:
            # Get logs for this medication in the last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            logs = db_session.query(MedicationLog).filter_by(
                medication_id=medication.id
            ).filter(MedicationLog.taken_at >= thirty_days_ago).all()
            
            # Calculate expected doses
            expected_doses = self._calculate_expected_doses(medication, thirty_days_ago)
            actual_doses = len(logs)
            
            compliance_rate = (actual_doses / expected_doses * 100) if expected_doses > 0 else 0
            
            stats[medication.name] = {
                'expected_doses': expected_doses,
                'actual_doses': actual_doses,
                'compliance_rate': round(compliance_rate, 2)
            }
        
        return stats
    
    def _calculate_expected_doses(self, medication, start_date):
        """Calculate expected number of doses since start_date"""
        frequency_lower = medication.frequency.lower()
        days_since_start = (datetime.utcnow() - start_date).days
        
        if 'once daily' in frequency_lower or 'daily' in frequency_lower:
            return days_since_start
        elif 'twice daily' in frequency_lower or 'bid' in frequency_lower:
            return days_since_start * 2
        elif 'three times daily' in frequency_lower or 'tid' in frequency_lower:
            return days_since_start * 3
        elif 'four times daily' in frequency_lower or 'qid' in frequency_lower:
            return days_since_start * 4
        elif 'every 6 hours' in frequency_lower or 'q6h' in frequency_lower:
            return days_since_start * 4
        elif 'every 8 hours' in frequency_lower or 'q8h' in frequency_lower:
            return days_since_start * 3
        elif 'every 12 hours' in frequency_lower or 'q12h' in frequency_lower:
            return days_since_start * 2
        else:
            return days_since_start 