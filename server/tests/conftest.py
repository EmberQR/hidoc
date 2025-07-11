import os
import sys

# 将项目根目录(server)添加到python path中，以便能够找到app模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app as flask_app
from models import db as _db


@pytest.fixture(scope='session')
def app():
    """创建一个session级别的Flask app fixture"""
    # 使用一个单独的测试数据库，避免影响开发数据库
    db_path = os.path.join(os.path.dirname(__file__), 'test.db')
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SECRET_KEY": "test_secret_key"
    })

    # 在测试期间禁用CSRF保护
    flask_app.config['WTF_CSRF_ENABLED'] = False

    with flask_app.app_context():
        _db.create_all()

    yield flask_app

    # 清理数据库文件
    with flask_app.app_context():
        _db.drop_all()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture()
def client(app):
    """为每个测试函数创建一个测试客户端"""
    return app.test_client()


@pytest.fixture()
def db(app):
    """为每个测试函数提供数据库访问并确保测试隔离"""
    with app.app_context():
        # 每个测试开始前，清理所有表的数据，确保独立性
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()
        
        yield _db
        
        # 测试结束后，再次清理
        _db.session.rollback()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit() 