import flask
from flask import request, jsonify
from models import db, Doctor
from login import auth_bp
from utils.jwtauth import jwt_required
import bcrypt
from user import user_bp
from hospital import hospital_bp
from utils.oss import upload_to_oss
from werkzeug.utils import secure_filename
from image import image_bp
import os

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://hidoc2:n3kbYPY3feKrJfBd@49.232.202.164:3306/hidoc2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'hidoc_secret_key'  # 添加JWT密钥

db.init_app(app)

# 注册认证蓝图
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(hospital_bp)
app.register_blueprint(image_bp)

# 创建数据库表
def create_tables():
    with app.app_context():
        db.create_all()

# 添加一个受保护的API接口示例
@app.route('/api/protected', methods=['GET'])
@jwt_required
def protected():
    """需要JWT认证的受保护接口示例"""
    return jsonify({
        'code': 200,
        'message': '认证成功',
        'data': {
            'user_id': request.user_id,
            'phone': request.user_phone
        }
    })

@app.route('/api/upload', methods=['POST'])
@jwt_required
def upload_file():
    """接收文件并上传到阿里云OSS的接口"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '请求中不包含文件'}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({'code': 400, 'message': '未选择文件'}), 400

    if file:
        # 使用 secure_filename 确保文件名安全
        filename = secure_filename(file.filename)
        # 为了防止文件名冲突，可以加上用户ID或时间戳等作为前缀
        # 这里我们简单地存放在 'uploads/' 目录下
        object_name = f"hidoc2/uploads/{request.user_id}/{filename}"

        # 直接上传文件流到OSS
        file_url = upload_to_oss(file.stream, object_name)

        if file_url:
            return jsonify({
                'code': 200,
                'message': '文件上传成功',
                'data': {
                    'url': file_url
                }
            })
        else:
            return jsonify({'code': 500, 'message': '文件上传失败'}), 500

    return jsonify({'code': 500, 'message': '发生未知错误'}), 500

if __name__ == '__main__':
    create_tables()  # 在启动应用前创建数据库表
    app.run(debug=True)