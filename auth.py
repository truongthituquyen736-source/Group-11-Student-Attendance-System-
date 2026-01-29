# auth.py
import hashlib
import re
from typing import Optional

def hash_password(password: str) -> str:
    """Hash mật khẩu bằng SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác minh mật khẩu"""
    return hash_password(plain_password) == hashed_password

def validate_email(email: str) -> bool:
    """Kiểm tra định dạng email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

def validate_required(value: str, field_name: str) -> Optional[str]:
    """Kiểm tra trường bắt buộc"""
    if not value or not value.strip():
        return f"{field_name} là bắt buộc."
    return None

def validate_username(username: str) -> Optional[str]:
    """Kiểm tra tên đăng nhập (chỉ chữ, số, gạch dưới)"""
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return "Tên đăng nhập phải từ 3-20 ký tự, chỉ chứa chữ, số, gạch dưới."
    return None
