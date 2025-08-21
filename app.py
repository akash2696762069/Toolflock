from datetime import date, datetime, timezone
from calendar import monthrange
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import io
import zipfile
import base64
import os
import sqlite3
import secrets
import string
import requests
import tempfile
import subprocess
import shutil
from dotenv import load_dotenv
import re
from datetime import timedelta

try:
    from PIL import Image
except Exception:  # Pillow optional for image tools
    Image = None
try:
    import PyPDF2
except Exception:  # PyPDF2 optional for PDF tools
    PyPDF2 = None
try:
    import docx  # python-docx
except Exception:
    docx = None
try:
    import openpyxl
except Exception:
    openpyxl = None
try:
    import qrcode
except Exception:  # qrcode optional for QR tool
    qrcode = None
try:
    from spellchecker import SpellChecker
except Exception:
    SpellChecker = None
try:
    import speedtest  # speedtest-cli
except Exception:
    speedtest = None


# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates", static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# MongoDB Configuration
app.config['MONGODB_URI'] = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/toolflock')

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.titan.email')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
app.config['MAIL_ASCII_ATTACHMENTS'] = False

# Initialize extensions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signin'
login_manager.login_message = 'Please sign in to access this page.'
login_manager.login_message_category = 'info'

mail = Mail(app)

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'toolflock')

# Initialize MongoDB client
try:
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    users_collection = db.users
    analytics_collection = db.analytics
    # Test connection
    client.server_info()
    print("✅ MongoDB connected successfully to:", MONGODB_DB_NAME)
    print("✅ Collections: users, analytics")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    db = None
    users_collection = None
    analytics_collection = None

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


# User Model
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.name = user_data.get('name', user_data.get('email', '').split('@')[0])
        self.is_verified = user_data.get('is_verified', False)
        self.created_at = user_data.get('created_at', datetime.now(timezone.utc))
        self.profile_picture = user_data.get('profile_picture', '')
        self.preferences = user_data.get('preferences', {
            'theme': 'dark',
            'notifications': True,
            'analytics': True,
        })

    @staticmethod
    def get(user_id):
        if users_collection is None:
            return None
        try:
            user_data = users_collection.find_one({'_id': ObjectId(user_id)})
            return User(user_data) if user_data else None
        except:
            return None

    @staticmethod
    def get_by_email(email):
        if users_collection is None:
            return None
        user_data = users_collection.find_one({'email': email})
        return User(user_data) if user_data else None

    @staticmethod
    def create(email, name, password):
        if users_collection is None:
            return None
        
        # Check if user already exists
        if users_collection.find_one({'email': email}):
            return None
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create user document
        user_doc = {
            'email': email,
            'name': name,
            'password_hash': password_hash,
            'is_verified': False,
            'created_at': datetime.now(timezone.utc),
            'profile_picture': '',
            'verification_token': secrets.token_urlsafe(32),
            'preferences': {
                'theme': 'dark',
                'notifications': True,
                'analytics': True,
            }
        }
        
        result = users_collection.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        return User(user_doc)

    def check_password(self, password):
        user_data = users_collection.find_one({'_id': ObjectId(self.id)})
        if not user_data:
            return False
        stored_hash = user_data['password_hash']
        # Handle binary hash storage
        if isinstance(stored_hash, bytes):
            stored_hash = stored_hash.decode('utf-8')
        return check_password_hash(stored_hash, password)

    def verify_email(self):
        if users_collection is not None:
            users_collection.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': {'is_verified': True}, '$unset': {'verification_token': 1}}
            )
            self.is_verified = True


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def send_verification_email(user, token):
    """Send email verification"""
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        print("Email credentials not configured")
        return False
    
    try:
        msg = Message(
            'Verify Your Toolflock Account',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        
        verification_url = url_for('verify_email', token=token, _external=True)
        
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #7a5cff;">Welcome to Toolflock!</h2>
            <p>Hi {user.name},</p>
            <p>Thank you for signing up! Please verify your email address by clicking the button below:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" 
                   style="background: linear-gradient(100deg, #7a5cff, #4cd1ff); 
                          color: white; padding: 12px 24px; text-decoration: none; 
                          border-radius: 8px; display: inline-block;">
                    Verify Email Address
                </a>
            </div>
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <p>This link will expire in 24 hours.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">
                If you didn't create this account, please ignore this email.
            </p>
        </div>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False


def send_password_reset_email(user, token):
    """Send password reset email"""
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        print("Email credentials not configured")
        return False
    
    try:
        msg = Message(
            'Reset Your Toolflock Password',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        
        reset_url = url_for('reset_password', token=token, _external=True)
        
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #7a5cff;">Password Reset Request</h2>
            <p>Hi {user.name},</p>
            <p>You requested to reset your password. Click the button below to set a new password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background: linear-gradient(100deg, #7a5cff, #4cd1ff); 
                          color: white; padding: 12px 24px; text-decoration: none; 
                          border-radius: 8px; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>This link will expire in 1 hour.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">
                If you didn't request this password reset, please ignore this email.
            </p>
        </div>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) if os.path.dirname(DB_PATH) else None
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS short_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def generate_code(length: int = 7) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def difference_ymd(start_date: date, end_date: date) -> tuple[int, int, int]:
    years = end_date.year - start_date.year
    months = end_date.month - start_date.month
    days = end_date.day - start_date.day

    if days < 0:
        borrow_month = end_date.month - 1 or 12
        borrow_year = end_date.year if end_date.month != 1 else end_date.year - 1
        days_in_borrow_month = monthrange(borrow_year, borrow_month)[1]
        days += days_in_borrow_month
        months -= 1

    if months < 0:
        months += 12
        years -= 1

    return years, months, days


def add_months(base_date: date, months_to_add: int) -> date:
    total_months = base_date.year * 12 + (base_date.month - 1) + months_to_add
    new_year = total_months // 12
    new_month = total_months % 12 + 1
    last_day = monthrange(new_year, new_month)[1]
    new_day = min(base_date.day, last_day)
    return date(new_year, new_month, new_day)


def months_and_extra_days(start_date: date, end_date: date) -> tuple[int, int]:
    months_total = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if end_date.day < start_date.day:
        months_total -= 1
    anchor = add_months(start_date, months_total)
    extra_days = (end_date - anchor).days
    return months_total, extra_days


# Authentication Routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        # Validation
        if not name or len(name) < 2:
            return jsonify({'error': 'Name must be at least 2 characters long'}) if request.is_json else (render_template('auth.html', error='Name must be at least 2 characters long'), 400)

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return jsonify({'error': 'Invalid email format'}) if request.is_json else (render_template('auth.html', error='Invalid email format'), 400)

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}) if request.is_json else (render_template('auth.html', error='Password must be at least 6 characters long'), 400)

        # Check if user already exists
        if User.get_by_email(email):
            return jsonify({'error': 'Email already registered'}) if request.is_json else (render_template('auth.html', error='Email already registered'), 400)

        # Create user
        user = User.create(email, name, password)
        if not user:
            return jsonify({'error': 'Failed to create account'}) if request.is_json else (render_template('auth.html', error='Failed to create account'), 500)

        # Get verification token
        user_data = users_collection.find_one({'_id': ObjectId(user.id)})
        token = user_data.get('verification_token')

        # Send verification email
        if send_verification_email(user, token):
            flash('Account created! Please check your email to verify your account.', 'success')
        else:
            flash('Account created! Email verification failed - please contact support.', 'warning')

        return jsonify({'success': True, 'message': 'Account created successfully'}) if request.is_json else redirect(url_for('signin'))

    return render_template('auth.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember = data.get('remember', False)

        user = User.get_by_email(email)
        if user and user.check_password(password):
            if not user.is_verified:
                return jsonify({'error': 'Please verify your email before signing in'}) if request.is_json else (render_template('auth.html', error='Please verify your email before signing in'), 400)

            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return jsonify({'success': True, 'redirect': next_page or url_for('home')}) if request.is_json else redirect(next_page or url_for('home'))

        return jsonify({'error': 'Invalid email or password'}) if request.is_json else (render_template('auth.html', error='Invalid email or password'), 400)

    return render_template('auth.html')


@app.route('/signout')
@login_required
def signout():
    logout_user()
    flash('You have been signed out successfully.', 'info')
    return redirect(url_for('home'))


@app.route('/verify-email/<token>')
@app.route('/verify-email', methods=['GET'])
def verify_email(token=None):
    # Handle token in URL path
    if token:
        if users_collection is None:
            flash('Email verification is not available.', 'error')
            return redirect(url_for('home'))

        user_data = users_collection.find_one({'verification_token': token})
        if not user_data:
            flash('Invalid or expired verification link.', 'error')
            return redirect(url_for('signin'))

        user = User(user_data)
        user.verify_email()
        flash('Email verified successfully! You can now sign in.', 'success')
        return redirect(url_for('signin'))
    
    # Handle email in query parameter (for backward compatibility)
    email = request.args.get('email')
    if email:
        user_data = users_collection.find_one({'email': email})
        if user_data and not user_data.get('is_verified', False):
            # Generate a new verification token and send email
            user = User(user_data)
            verification_token = secrets.token_urlsafe(32)
            users_collection.update_one(
                {'_id': ObjectId(user.id)},
                {'$set': {'verification_token': verification_token}}
            )
            
            # Send verification email
            if send_verification_email(user, verification_token):
                flash('Verification email resent successfully!', 'success')
            else:
                flash('Failed to resend verification email.', 'error')
            return redirect(url_for('signin'))
        elif user_data and user_data.get('is_verified', False):
            flash('Email is already verified. Please sign in.', 'info')
            return redirect(url_for('signin'))
        else:
            flash('No account found with that email.', 'error')
            return redirect(url_for('signup'))
    
    # If no token or email provided
    flash('Invalid verification request.', 'error')
    return redirect(url_for('home'))


@app.route('/verify', methods=['GET'])
def verify_instructions():
    # Render verification instructions page; email can be passed via query param
    return render_template('verify_email.html')


@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    data = request.get_json() if request.is_json else request.form
    email = (data.get('email') or '').strip().lower()

    if not email:
        return jsonify({'success': False, 'error': 'Email is required'}), 400

    if users_collection is None:
        return jsonify({'success': False, 'error': 'Email verification is not available'}), 500

    user_data = users_collection.find_one({'email': email})
    if not user_data:
        return jsonify({'success': False, 'error': 'No account found with that email'}), 404

    if user_data.get('is_verified'):
        return jsonify({'success': True, 'message': 'Email already verified. Please sign in.'})

    user = User(user_data)
    verification_token = secrets.token_urlsafe(32)
    users_collection.update_one(
        {'_id': ObjectId(user.id)},
        {'$set': {'verification_token': verification_token}}
    )

    if send_verification_email(user, verification_token):
        return jsonify({'success': True, 'message': 'Verification email resent successfully!'})
    else:
        return jsonify({'success': False, 'error': 'Failed to resend verification email'}), 500

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()

        user = User.get_by_email(email)
        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            users_collection.update_one(
                {'_id': ObjectId(user.id)},
                {'$set': {
                    'reset_token': reset_token,
                    'reset_token_expires': datetime.now(timezone.utc) + timedelta(hours=1)
                }}
            )

            if send_password_reset_email(user, reset_token):
                message = 'Password reset email sent! Check your inbox.'
            else:
                message = 'Failed to send reset email. Please try again.'
        else:
            message = 'If an account with that email exists, a reset link has been sent.'

        return jsonify({'success': True, 'message': message}) if request.is_json else (render_template('forgot_password.html', message=message), 200)

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if users_collection is None:
        flash('Password reset is not available.', 'error')
        return redirect(url_for('home'))

    user_data = users_collection.find_one({
        'reset_token': token,
        'reset_token_expires': {'$gt': datetime.now(timezone.utc)}
    })

    if not user_data:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}) if request.is_json else (render_template('reset_password.html', token=token, error='Password must be at least 6 characters long'), 400)

        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}) if request.is_json else (render_template('reset_password.html', token=token, error='Passwords do not match'), 400)

        # Update password
        password_hash = generate_password_hash(password)
        users_collection.update_one(
            {'_id': user_data['_id']},
            {'$set': {'password_hash': password_hash}, '$unset': {'reset_token': 1, 'reset_token_expires': 1}}
        )

        flash('Password reset successfully! You can now sign in.', 'success')
        return jsonify({'success': True, 'message': 'Password reset successfully!', 'redirect': url_for('signin')}) if request.is_json else redirect(url_for('signin'))

    return render_template('reset_password.html', token=token)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user, current_user=current_user)


@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json() if request.is_json else request.form
    name = data.get('name', '').strip()

    # Optional preference updates in same payload
    pref_theme = data.get('theme')
    pref_notifications = data.get('notifications')
    pref_analytics = data.get('analytics')

    if not name or len(name) < 2:
        if request.is_json:
            return jsonify({'error': 'Name must be at least 2 characters long'}), 400
        flash('Name must be at least 2 characters long', 'error')
        return redirect(url_for('profile'))

    update_fields = {'name': name}

    # Normalize and apply preferences if present
    prefs_update = {}
    if pref_theme in ('light', 'dark'):
        prefs_update['preferences.theme'] = pref_theme
    if pref_notifications is not None:
        if isinstance(pref_notifications, str):
            pref_notifications = pref_notifications.lower() in ('1', 'true', 'yes', 'on')
        prefs_update['preferences.notifications'] = bool(pref_notifications)
    if pref_analytics is not None:
        if isinstance(pref_analytics, str):
            pref_analytics = pref_analytics.lower() in ('1', 'true', 'yes', 'on')
        prefs_update['preferences.analytics'] = bool(pref_analytics)

    set_doc = {'name': name}
    if prefs_update:
        set_doc.update(prefs_update)

    users_collection.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': set_doc}
    )
    
    # Update the current user object
    current_user.name = name
    if 'preferences.theme' in prefs_update:
        current_user.preferences['theme'] = pref_theme
    if 'preferences.notifications' in prefs_update:
        current_user.preferences['notifications'] = bool(pref_notifications)
    if 'preferences.analytics' in prefs_update:
        current_user.preferences['analytics'] = bool(pref_analytics)

    if request.is_json:
        return jsonify({'success': True, 'message': 'Profile updated successfully!'})
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))


@app.route('/profile/preferences', methods=['GET', 'POST'])
@login_required
def profile_preferences():
    if request.method == 'GET':
        return jsonify({'success': True, 'preferences': current_user.preferences})

    data = request.get_json(force=True)
    updates = {}
    theme = data.get('theme')
    if theme in ('light', 'dark'):
        updates['preferences.theme'] = theme
    if 'notifications' in data:
        updates['preferences.notifications'] = bool(data['notifications'])
    if 'analytics' in data:
        updates['preferences.analytics'] = bool(data['analytics'])

    if not updates:
        return jsonify({'success': False, 'error': 'No valid preferences provided'}), 400

    users_collection.update_one({'_id': ObjectId(current_user.id)}, {'$set': updates})

    # Reflect changes in current_user
    if 'preferences.theme' in updates:
        current_user.preferences['theme'] = updates['preferences.theme']
    if 'preferences.notifications' in updates:
        current_user.preferences['notifications'] = updates['preferences.notifications']
    if 'preferences.analytics' in updates:
        current_user.preferences['analytics'] = updates['preferences.analytics']

    return jsonify({'success': True, 'preferences': current_user.preferences})


@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json() if request.is_json else request.form
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not current_user.check_password(current_password):
        if request.is_json:
            return jsonify({'error': 'Current password is incorrect'}), 400
        flash('Current password is incorrect', 'error')
        return redirect(url_for('profile'))

    if len(new_password) < 6:
        if request.is_json:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        flash('New password must be at least 6 characters long', 'error')
        return redirect(url_for('profile'))

    if new_password != confirm_password:
        if request.is_json:
            return jsonify({'error': 'New passwords do not match'}), 400
        flash('New passwords do not match', 'error')
        return redirect(url_for('profile'))

    password_hash = generate_password_hash(new_password)
    users_collection.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': {'password_hash': password_hash}}
    )

    if request.is_json:
        return jsonify({'success': True, 'message': 'Password changed successfully!'})
    flash('Password changed successfully!', 'success')
    return redirect(url_for('profile'))


# Main Routes
@app.route("/")
def home():
    return render_template("home.html", current_user=current_user)


@app.get("/all-tools")
def all_tools():
    return render_template("all_tools.html", current_user=current_user)


@app.get("/age")
def age_calculator():
    return render_template("age.html", current_user=current_user)


@app.post("/api/diff")
def api_diff():
    try:
        data = request.get_json(force=True)
        start_input = data.get("startDate")
        end_input = data.get("endDate")
        if not start_input or not end_input:
            return jsonify({"error": "startDate and endDate are required (YYYY-MM-DD)"}), 400
        start_parts = list(map(int, start_input.split("-")))
        end_parts = list(map(int, end_input.split("-")))
        start_date = date(*start_parts)
        end_date = date(*end_parts)
    except Exception as ex:
        return jsonify({"error": f"Invalid input: {ex}"}), 400

    if end_date < start_date:
        start_date, end_date = end_date, start_date

    years, months, days = difference_ymd(start_date, end_date)
    total_months, extra_days = months_and_extra_days(start_date, end_date)
    total_days = (end_date - start_date).days

    return jsonify({
        "years": years,
        "months": months,
        "days": days,
        "totalMonths": total_months,
        "extraDays": extra_days,
        "totalDays": total_days
    })


 


# ---------------------------- PDF Tools ----------------------------

@app.get("/pdf")
def pdf_tools_page():
    return render_template("pdf_tools.html", current_user=current_user)


@app.post("/api/pdf/merge")
def api_pdf_merge():
    if PyPDF2 is None:
        return jsonify({"error": "PyPDF2 not installed"}), 500
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No PDF files uploaded"}), 400
    merger = PyPDF2.PdfMerger()
    for f in files:
        merger.append(io.BytesIO(f.read()))
    output = io.BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)
    return send_file(output, mimetype="application/pdf", as_attachment=True, download_name="merged.pdf")


@app.post("/api/pdf/split")
def api_pdf_split():
    if PyPDF2 is None:
        return jsonify({"error": "PyPDF2 not installed"}), 500
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No PDF uploaded"}), 400
    reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i in range(len(reader.pages)):
            writer = PyPDF2.PdfWriter()
            writer.add_page(reader.pages[i])
            single_buffer = io.BytesIO()
            writer.write(single_buffer)
            zf.writestr(f"page_{i+1}.pdf", single_buffer.getvalue())
    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name="split_pages.zip")


@app.post("/api/pdf/compress")
def api_pdf_compress():
    if PyPDF2 is None:
        return jsonify({"error": "PyPDF2 not installed"}), 500
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No PDF uploaded"}), 400
    reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
    writer = PyPDF2.PdfWriter()
    for page in reader.pages:
        try:
            page.compress_content_streams()
        except Exception:
            pass
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return send_file(out, mimetype="application/pdf", as_attachment=True, download_name="compressed.pdf")


@app.post("/api/pdf/to-word")
def api_pdf_to_word():
    if PyPDF2 is None or docx is None:
        return jsonify({"error": "PyPDF2 and python-docx required"}), 500
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No PDF uploaded"}), 400
    reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
    document = docx.Document()
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        document.add_heading(f"Page {i}", level=2)
        for line in text.splitlines():
            document.add_paragraph(line)
    out = io.BytesIO()
    document.save(out)
    out.seek(0)
    return send_file(out, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document", as_attachment=True, download_name="converted.docx")


@app.post("/api/pdf/to-excel")
def api_pdf_to_excel():
    if PyPDF2 is None or openpyxl is None:
        return jsonify({"error": "PyPDF2 and openpyxl required"}), 500
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No PDF uploaded"}), 400
    reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "PDF Text"
    row_idx = 1
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").splitlines()
        ws.cell(row=row_idx, column=1, value=f"Page {i}")
        row_idx += 1
        for line in text:
            ws.cell(row=row_idx, column=1, value=line)
            row_idx += 1
        row_idx += 1
    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return send_file(out, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="converted.xlsx")


# ------------------------- File Converter -------------------------

@app.get("/file-converter")
def file_converter_page():
    return render_template("file_converter.html", current_user=current_user)


@app.post("/api/convert/image")
def api_convert_image():
    if Image is None:
        return jsonify({"error": "Pillow not installed"}), 500
    file = request.files.get("file")
    target = request.form.get("target", "png").lower()
    if not file:
        return jsonify({"error": "No image uploaded"}), 400
    image = Image.open(file.stream).convert("RGB")
    output = io.BytesIO()
    image.save(output, format=target.upper())
    output.seek(0)
    return send_file(output, mimetype=f"image/{target}", as_attachment=True, download_name=f"converted.{target}")


@app.post("/api/convert/video")
def api_convert_video():
    # Requires ffmpeg installed on OS and present in PATH
    file = request.files.get("file")
    target = request.form.get("target", "mp4").lower()
    if not file:
        return jsonify({"error": "No video uploaded"}), 400
    if shutil.which("ffmpeg") is None:
        return jsonify({"error": "ffmpeg not found. Please install ffmpeg and add to PATH"}), 500
    with tempfile.TemporaryDirectory() as td:
        in_path = os.path.join(td, "input")
        out_path = os.path.join(td, f"output.{target}")
        file.save(in_path)
        cmd = ["ffmpeg", "-y", "-i", in_path, out_path]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            return jsonify({"error": "Conversion failed"}), 500
        return send_file(out_path, as_attachment=True, download_name=f"converted.{target}")


# ------------------------- URL Shortener -------------------------

@app.get("/shortener")
def url_shortener_page():
    return render_template("url_shortener.html", current_user=current_user)


@app.post("/api/shorten")
def api_shorten():
    data = request.get_json(force=True)
    url = data.get("url")
    if not url:
        return jsonify({"error": "url is required"}), 400
    code = generate_code()
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute("INSERT INTO short_urls(code, url) VALUES(?, ?)", (code, url))
        except sqlite3.IntegrityError:
            code = generate_code()
            conn.execute("INSERT INTO short_urls(code, url) VALUES(?, ?)", (code, url))
    short = request.host_url.rstrip("/") + url_for("redirect_short", code=code)
    return jsonify({"code": code, "shortUrl": short})


@app.get("/u/<code>")
def redirect_short(code: str):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT url FROM short_urls WHERE code = ?", (code,))
        row = cur.fetchone()
    if not row:
        return render_template("url_shortener.html", error="Invalid code"), 404
    return redirect(row[0])


# ----------------------- QR Code Tools ---------------------------

@app.get("/qr")
def qr_tools_page():
    return render_template("qr_tools.html", current_user=current_user)


@app.post("/api/qr/generate")
def api_qr_generate():
    if qrcode is None:
        return jsonify({"error": "qrcode not installed"}), 500
    data = request.get_json(force=True)
    text = data.get("text", "")
    size = int(data.get("size", 256))
    fill = data.get("fill", "#000000")
    back = data.get("back", "#FFFFFF")
    if not text:
        return jsonify({"error": "text is required"}), 400
    qr = qrcode.QRCode(version=None, box_size=10, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill, back_color=back).resize((size, size))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return jsonify({"pngBase64": f"data:image/png;base64,{b64}"})


# ---------------- Image Resizer & Compressor (Bulk) --------------

@app.get("/image-tools")
def image_tools_page():
    return render_template("image_tools.html", current_user=current_user)


@app.post("/api/image/bulk")
def api_image_bulk():
    if Image is None:
        return jsonify({"error": "Pillow not installed"}), 500
    files = request.files.getlist("files")
    width = request.form.get("width")
    height = request.form.get("height")
    quality = int(request.form.get("quality", 80))
    fmt = request.form.get("format", "jpeg").lower()
    if not files:
        return jsonify({"error": "No images uploaded"}), 400
    width_i = int(width) if width else None
    height_i = int(height) if height else None
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            img = Image.open(f.stream)
            img = img.convert("RGB")
            if width_i or height_i:
                img = img.resize((width_i or img.width, height_i or img.height))
            out = io.BytesIO()
            save_kwargs = {"quality": quality}
            if fmt == "png":
                save_kwargs.pop("quality", None)
            img.save(out, format=fmt.upper(), **save_kwargs)
            zf.writestr(os.path.splitext(f.filename)[0] + f"_processed.{fmt}", out.getvalue())
    mem_zip.seek(0)
    return send_file(mem_zip, mimetype="application/zip", as_attachment=True, download_name="images_processed.zip")


# ------------------------ Unit Converter -------------------------

@app.get("/unit-converter")
def unit_converter_page():
    return render_template("unit_converter.html", current_user=current_user)


# ------------------------ Internet Speed Test --------------------

@app.get("/speed-test")
def speed_test_page():
    return render_template("speed_test.html", current_user=current_user)


@app.post("/api/speedtest")
def api_speedtest():
    if speedtest is None:
        return jsonify({"error": "speedtest-cli not installed"}), 500
    s = speedtest.Speedtest()
    s.get_best_server()
    down = s.download() / 1_000_000
    up = s.upload() / 1_000_000
    ping = s.results.ping
    return jsonify({"downloadMbps": round(down, 2), "uploadMbps": round(up, 2), "pingMs": round(ping, 2)})


# ------------------------ Currency Converter ---------------------

@app.post("/api/currency")
def api_currency():
    try:
        data = request.get_json(force=True)
        amount = float(data.get("amount"))
        from_cur = data.get("from").upper().strip()
        to_cur = data.get("to").upper().strip()
        if not from_cur or not to_cur:
            return jsonify({"error": "from and to currencies required"}), 400
    except Exception:
        return jsonify({"error": "Invalid input"}), 400
    try:
        r = requests.get("https://api.exchangerate.host/convert", params={"from": from_cur, "to": to_cur, "amount": amount}, timeout=15)
        j = r.json()
        if not r.ok or "result" not in j:
            return jsonify({"error": "Rate lookup failed"}), 502
        return jsonify({"amount": amount, "from": from_cur, "to": to_cur, "converted": j["result"]})
    except Exception:
        return jsonify({"error": "Conversion service unreachable"}), 502


# ------------------------ Screen Recorder (Web) ------------------

@app.get("/screen-recorder")
def screen_recorder_page():
    return render_template("screen_recorder.html", current_user=current_user)


# ---------------------- Grammar / Spell Checker ------------------

@app.get("/grammar")
def grammar_page():
    return render_template("grammar.html", current_user=current_user)


@app.post("/api/grammar")
def api_grammar():
    text = request.get_json(force=True).get("text", "")
    if not text:
        return jsonify({"errors": []})
    results = []
    if SpellChecker is not None:
        sp = SpellChecker()
        words = [w.strip(".,!?;:\"'()[]{}") for w in text.split()]
        misspelled = sp.unknown([w for w in words if w])
        for w in misspelled:
            suggestions = list(sp.candidates(w))[:5]
            results.append({"word": w, "suggestions": suggestions})
    return jsonify({"errors": results})


# ------------------------ Footer Links -------------------------

@app.get("/about")
def about_page():
    return render_template("about.html", current_user=current_user)

@app.get("/contact")
def contact_page():
    return render_template("contact.html", current_user=current_user)

@app.get("/privacy")
def privacy_page():
    return render_template("privacy.html", current_user=current_user)

@app.get("/terms")
def terms_page():
    return render_template("terms.html", current_user=current_user)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
