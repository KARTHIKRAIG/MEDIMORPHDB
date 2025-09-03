import mongoengine as me
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

# MongoDB Configuration
DB_NAME = "medimorph_db"
MONGODB_URI = "mongodb://localhost:27017/"


# ---------------------------------------------------
# Database Initialization
# ---------------------------------------------------
def init_mongodb(app=None):
    """Initialize MongoDB with MongoEngine"""
    try:
        me.connect(
            db=DB_NAME,
            host="localhost",
            port=27017,
            alias="default"
        )
        print("✅ MongoDB initialized with MongoEngine")
        return True
    except Exception as e:
        print(f"❌ MongoDB initialization failed: {e}")
        return False


def test_mongodb_connection():
    """Ping MongoDB"""
    try:
        conn = me.get_connection(alias="default")
        conn.admin.command("ping")
        print("✅ MongoDB test connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB test connection failed: {e}")
        return False


def get_database_stats():
    """Return collection counts"""
    try:
        conn = me.get_connection(alias="default")
        db = conn.get_database(DB_NAME)
        return {
            "users": db.users.count_documents({}),
            "medications": db.medications.count_documents({}),
            "reminders": db.reminders.count_documents({}),
            "medication_logs": db.medication_logs.count_documents({}),
            "prescription_uploads": db.prescription_upload.count_documents({}),
        }
    except Exception as e:
        print(f"❌ Error fetching DB stats: {e}")
        return None


def create_default_users():
    """Insert a default admin user if none exists"""
    if not User.objects(username="admin").first():
        admin = User(
            username="admin",
            email="admin@example.com",
            first_name="System",
            last_name="Admin",
            is_active=True,
            role="admin"
        )
        admin.set_password("admin123")
        admin.save()
        print("✅ Default admin user created (username=admin, password=admin123)")
        return True
    return False


# ---------------------------------------------------
# Models
# ---------------------------------------------------
class User(me.Document, UserMixin):
    username = me.StringField(required=True, unique=True)
    email = me.StringField(required=True, unique=True)
    password_hash = me.StringField(required=True)
    first_name = me.StringField()
    last_name = me.StringField()
    role = me.StringField(default="user")  # user, admin, staff
    is_active = me.BooleanField(default=True)
    created_at = me.DateTimeField(default=datetime.utcnow)
    last_login = me.DateTimeField()

    meta = {"collection": "users", "strict": False}

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Return the user id as a string for Flask-Login."""
        return str(self.id)

    def to_dict(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "role": self.role,
            "is_active": self.is_active,
        }


class Medication(me.Document):
    user_id = me.ObjectIdField(required=True)
    user_username = me.StringField()
    name = me.StringField(required=True)
    dosage = me.StringField()
    frequency = me.StringField()
    instructions = me.StringField()
    duration = me.StringField()
    source = me.StringField(default="manual")  # manual / ocr
    confidence_score = me.FloatField(default=1.0)
    is_active = me.BooleanField(default=True)
    created_at = me.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "medications", "strict": False}

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "instructions": self.instructions,
            "duration": self.duration,
            "source": self.source,
            "confidence_score": self.confidence_score,
        }


class Reminder(me.Document):
    user_id = me.ObjectIdField(required=True)
    medication_id = me.ObjectIdField(required=True)
    time = me.StringField(required=True)  # e.g. "09:00"
    is_active = me.BooleanField(default=True)
    last_sent = me.DateTimeField()

    meta = {"collection": "reminders", "strict": False}


class MedicationLog(me.Document):
    user_id = me.ObjectIdField(required=True)
    medication_id = me.ObjectIdField(required=True)
    taken_at = me.DateTimeField(default=datetime.utcnow)
    notes = me.StringField()

    meta = {"collection": "medication_logs", "strict": False}


class PrescriptionUpload(me.Document):
    user_id = me.ObjectIdField(required=True)
    filename = me.StringField(required=True)
    original_filename = me.StringField()
    file_path = me.StringField()
    file_size = me.IntField()
    mime_type = me.StringField()
    extracted_text = me.StringField()
    medications_found = me.IntField(default=0)
    medications_added = me.IntField(default=0)
    processing_status = me.StringField(default="pending")
    processing_time = me.FloatField()
    processed_at = me.DateTimeField()

    meta = {"collection": "prescription_upload", "strict": False}
