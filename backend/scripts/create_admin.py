#!/usr/bin/env python3
"""创建管理员账号"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin").first()
        if user:
            user.password_hash = get_password_hash("admin123")
            user.status = 1
            print("✅ 已重置管理员密码")
        else:
            user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                real_name="系统管理员",
                role="admin",
                status=1
            )
            db.add(user)
            print("✅ 已创建管理员账号")
        db.commit()
        print("   用户名: admin")
        print("   密码: admin123")
    except Exception as e:
        db.rollback()
        print(f"❌ 失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
