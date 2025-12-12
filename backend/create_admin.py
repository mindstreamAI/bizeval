import sys
import os
import hashlib

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import AdminUser

def hash_password(password: str) -> str:
    """Простой хеш для MVP, позже заменим на bcrypt"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin(email: str, password: str):
    db = SessionLocal()
    
    # Проверяем, существует ли уже админ
    existing = db.query(AdminUser).filter(AdminUser.email == email).first()
    if existing:
        print(f"Admin with email {email} already exists!")
        db.close()
        return
    
    # Хешируем пароль
    password_hash = hash_password(password)
    
    # Создаем админа
    admin = AdminUser(
        email=email,
        password_hash=password_hash,
        role="admin"
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print(f"✅ Admin created successfully!")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"   ID: {admin.id}")
    
    db.close()

if __name__ == "__main__":
    # Создаем первого админа
    create_admin("admin@bizeval.com", "admin123")
