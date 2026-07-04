"""
Authentication Module

Provides user authentication, password management, and session handling:
- User login/logout with password verification
- Password hashing using bcrypt
- Session state management
- Login rate limiting (brute force protection)
- Session timeout handling
"""

import bcrypt
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import streamlit as st


# Configuration
USERS_FILE = Path(__file__).parent / "users.json"
MAX_LOGIN_ATTEMPTS = 5
LOGIN_TIMEOUT_MINUTES = 15
SESSION_TIMEOUT_MINUTES = 30


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


class User:
    """User model representing authenticated user"""
    
    def __init__(self, username: str, role: str, email: str = ""):
        self.username = username
        self.role = role
        self.email = email
        self.login_time = datetime.now()
        self.last_activity = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary"""
        return {
            'username': self.username,
            'role': self.role,
            'email': self.email,
            'login_time': self.login_time.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def is_session_expired(self) -> bool:
        """Check if session has expired due to inactivity"""
        time_diff = datetime.now() - self.last_activity
        return time_diff > timedelta(minutes=SESSION_TIMEOUT_MINUTES)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        password: Plain text password
        hashed_password: Hashed password to check against
        
    Returns:
        True if password matches
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def load_users() -> Dict:
    """
    Load users from JSON file
    
    Returns:
        Dictionary of users
    """
    if not USERS_FILE.exists():
        # Create default users if file doesn't exist
        default_users = create_default_users()
        save_users(default_users)
        return default_users
    
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return {}


def save_users(users: Dict):
    """
    Save users to JSON file
    
    Args:
        users: Dictionary of users to save
    """
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        st.error(f"Error saving users: {e}")


def create_default_users() -> Dict:
    """
    Create default user accounts
    
    Returns:
        Dictionary of default users with hashed passwords
    """
    return {
        'admin': {
            'username': 'admin',
            'password': hash_password('Admin@123'),
            'role': 'Admin',
            'email': 'admin@drugconflict.com',
            'created_at': datetime.now().isoformat()
        },
        'doctor': {
            'username': 'doctor',
            'password': hash_password('Doctor@123'),
            'role': 'Doctor',
            'email': 'doctor@drugconflict.com',
            'created_at': datetime.now().isoformat()
        },
        'pharmacist': {
            'username': 'pharmacist',
            'password': hash_password('Pharma@123'),
            'role': 'Pharmacist',
            'email': 'pharmacist@drugconflict.com',
            'created_at': datetime.now().isoformat()
        }
    }


def initialize_session_state():
    """Initialize session state variables for authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = {}
    if 'failed_login_time' not in st.session_state:
        st.session_state.failed_login_time = {}


def check_login_attempts(username: str) -> Tuple[bool, int]:
    """
    Check if user has exceeded login attempts
    
    Args:
        username: Username to check
        
    Returns:
        Tuple of (is_allowed, remaining_attempts)
    """
    if username not in st.session_state.login_attempts:
        return True, MAX_LOGIN_ATTEMPTS
    
    attempts = st.session_state.login_attempts[username]
    
    # Check if timeout has expired
    if username in st.session_state.failed_login_time:
        timeout_time = st.session_state.failed_login_time[username]
        if datetime.now() - timeout_time > timedelta(minutes=LOGIN_TIMEOUT_MINUTES):
            # Reset attempts after timeout
            st.session_state.login_attempts[username] = 0
            del st.session_state.failed_login_time[username]
            return True, MAX_LOGIN_ATTEMPTS
    
    remaining = MAX_LOGIN_ATTEMPTS - attempts
    is_allowed = attempts < MAX_LOGIN_ATTEMPTS
    
    return is_allowed, remaining


def record_failed_login(username: str):
    """
    Record a failed login attempt
    
    Args:
        username: Username that failed login
    """
    if username not in st.session_state.login_attempts:
        st.session_state.login_attempts[username] = 0
    
    st.session_state.login_attempts[username] += 1
    
    if st.session_state.login_attempts[username] >= MAX_LOGIN_ATTEMPTS:
        st.session_state.failed_login_time[username] = datetime.now()


def reset_login_attempts(username: str):
    """
    Reset login attempts for user after successful login
    
    Args:
        username: Username to reset
    """
    if username in st.session_state.login_attempts:
        st.session_state.login_attempts[username] = 0
    if username in st.session_state.failed_login_time:
        del st.session_state.failed_login_time[username]


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Authenticate a user with username and password
    
    Args:
        username: Username
        password: Password
        
    Returns:
        Tuple of (success, error_message)
    """
    # Check login attempts
    is_allowed, remaining = check_login_attempts(username)
    
    if not is_allowed:
        return False, f"Too many failed login attempts. Please try again in {LOGIN_TIMEOUT_MINUTES} minutes."
    
    # Load users
    users = load_users()
    
    # Check if user exists
    if username not in users:
        record_failed_login(username)
        return False, "Invalid username or password"
    
    user_data = users[username]
    
    # Verify password
    if not verify_password(password, user_data['password']):
        record_failed_login(username)
        remaining -= 1
        if remaining > 0:
            return False, f"Invalid username or password. {remaining} attempts remaining."
        else:
            return False, f"Too many failed attempts. Account locked for {LOGIN_TIMEOUT_MINUTES} minutes."
    
    # Successful login
    reset_login_attempts(username)
    
    # Create user object
    user = User(
        username=user_data['username'],
        role=user_data['role'],
        email=user_data.get('email', '')
    )
    
    # Store in session
    st.session_state.authenticated = True
    st.session_state.user = user
    
    return True, None


def logout_user():
    """Logout current user and clear session"""
    st.session_state.authenticated = False
    st.session_state.user = None


def get_current_user() -> Optional[User]:
    """
    Get current authenticated user
    
    Returns:
        Current user object or None if not authenticated
    """
    return st.session_state.get('user')


def is_authenticated() -> bool:
    """
    Check if user is authenticated
    
    Returns:
        True if user is authenticated
    """
    if not st.session_state.get('authenticated', False):
        return False
    
    user = get_current_user()
    if user is None:
        return False
    
    # Check session timeout
    if user.is_session_expired():
        logout_user()
        return False
    
    # Update activity
    user.update_activity()
    
    return True


def require_authentication():
    """
    Decorator function to require authentication for a page
    Redirects to login if not authenticated
    """
    if not is_authenticated():
        st.warning("⚠️ Please login to access this page")
        st.stop()


def add_user(username: str, password: str, role: str, email: str = "") -> Tuple[bool, Optional[str]]:
    """
    Add a new user to the system
    
    Args:
        username: New username
        password: Plain text password
        role: User role
        email: User email
        
    Returns:
        Tuple of (success, error_message)
    """
    users = load_users()
    
    # Check if user already exists
    if username in users:
        return False, "Username already exists"
    
    # Validate username (alphanumeric only)
    if not username.isalnum():
        return False, "Username must contain only letters and numbers"
    
    # Add user
    users[username] = {
        'username': username,
        'password': hash_password(password),
        'role': role,
        'email': email,
        'created_at': datetime.now().isoformat()
    }
    
    save_users(users)
    return True, None


def change_password(username: str, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Change user password
    
    Args:
        username: Username
        old_password: Current password
        new_password: New password
        
    Returns:
        Tuple of (success, error_message)
    """
    users = load_users()
    
    if username not in users:
        return False, "User not found"
    
    # Verify old password
    if not verify_password(old_password, users[username]['password']):
        return False, "Current password is incorrect"
    
    # Update password
    users[username]['password'] = hash_password(new_password)
    users[username]['password_changed_at'] = datetime.now().isoformat()
    
    save_users(users)
    return True, None


def delete_user(username: str) -> Tuple[bool, Optional[str]]:
    """
    Delete a user from the system
    
    Args:
        username: Username to delete
        
    Returns:
        Tuple of (success, error_message)
    """
    users = load_users()
    
    if username not in users:
        return False, "User not found"
    
    # Prevent deletion of last admin
    if users[username]['role'] == 'Admin':
        admin_count = sum(1 for u in users.values() if u['role'] == 'Admin')
        if admin_count <= 1:
            return False, "Cannot delete the last admin user"
    
    del users[username]
    save_users(users)
    return True, None


def get_all_users() -> List[Dict]:
    """
    Get list of all users (without passwords)
    
    Returns:
        List of user dictionaries
    """
    users = load_users()
    return [
        {
            'username': user_data['username'],
            'role': user_data['role'],
            'email': user_data.get('email', ''),
            'created_at': user_data.get('created_at', '')
        }
        for user_data in users.values()
    ]


def get_user_role(username: str) -> Optional[str]:
    """
    Get role for a specific user
    
    Args:
        username: Username
        
    Returns:
        User role or None if not found
    """
    users = load_users()
    if username in users:
        return users[username]['role']
    return None
