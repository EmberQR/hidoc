from flask import Blueprint, request, jsonify, make_response
from models import db, Doctor
from utils.jwtauth import JWTAuth
import bcrypt

auth_bp = Blueprint('auth', __name__)

# 注册接口，暂时不用
# @auth_bp.route('/api/register', methods=['POST'])
# def register():
#     """
#     医生注册接口
    
#     请求体:
#     {
#         "phone": "手机号",
#         "name": "姓名",
#         "password": "密码",
#         "gender": "性别",
#     }
    
#     返回:
#     {
#         "code": 201,
#         "message": "注册成功",
#         "data": {
#             "id": 医生ID,
#             "phone": "手机号",
#             "name": "姓名",
#             "gender": "性别",
#         }
#     }
#     """
#     data = request.json
    
#     # 验证请求数据
#     if not data:
#         return jsonify({
#             'code': 400,
#             'message': '请求体不能为空'
#         }), 400
    
#     # 验证必填字段
#     required_fields = ['phone', 'name', 'password', 'gender']
#     for field in required_fields:
#         if field not in data:
#             return jsonify({
#                 'code': 400,
#                 'message': f'缺少必填字段: {field}'
#             }), 400
    
#     # 验证性别枚举值
#     if data['gender'] not in ['男', '女', '未知']:
#         return jsonify({
#             'code': 400,
#             'message': '性别必须是: 男, 女, 未知'
#         }), 400
    
#     # 检查手机号是否已存在
#     if Doctor.query.filter_by(phone=data['phone']).first():
#         return jsonify({
#             'code': 400,
#             'message': f'手机号 {data["phone"]} 已被注册'
#         }), 400
    
#     # 对密码进行加密
#     hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
#     # 创建新医生
#     new_doctor = Doctor(
#         phone=data['phone'],
#         name=data['name'],
#         gender=data['gender'],
#         password=hashed_password.decode('utf-8')  # 存储为字符串
#     )
    
#     db.session.add(new_doctor)
#     db.session.commit()
    
#     # 准备返回数据，移除敏感信息
#     doctor_data = new_doctor.to_dict()
#     doctor_data.pop('password', None)
    
#     return jsonify({
#         'code': 201,
#         'message': '注册成功',
#         'data': doctor_data
#     }), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """
    医生登录接口
    
    请求体:
    {
        "phone": "手机号",
        "password": "密码"
    }
    
    返回:
    {
        "code": 200,
        "message": "登录成功",
        "data": {
            "id": 医生ID,
            "phone": "手机号",
            "name": "姓名",
            "gender": "性别",
        }
    }
    """
    data = request.json
    
    # 验证请求数据
    if not data:
        return jsonify({
            'code': 400,
            'message': '请求体不能为空'
        }), 400
    
    phone = data.get('phone')
    password = data.get('password')
    
    if not phone or not password:
        return jsonify({
            'code': 400,
            'message': '手机号和密码不能为空'
        }), 400
    
    # 查询医生
    doctor = Doctor.query.filter_by(phone=phone).first()
    
    # 验证医生是否存在及密码是否正确
    if not doctor or not bcrypt.checkpw(password.encode('utf-8'), doctor.password.encode('utf-8')):
        return jsonify({
            'code': 401,
            'message': '手机号或密码错误'
        }), 401
    
    # 生成JWT令牌
    token = JWTAuth.generate_token(doctor.id, doctor.phone)
    
    # 准备返回数据，移除敏感信息
    doctor_data = doctor.to_dict()
    doctor_data.pop('password', None)
    
    # 创建响应对象
    response = make_response(jsonify({
        'code': 200,
        'message': '登录成功',
        'data': doctor_data
    }))
    
    # 设置Cookie
    response.set_cookie(
        'token', 
        token, 
        httponly=True,
        max_age=24 * 60 * 60,  # 24小时
        secure=False,  # 生产环境应设为True，要求HTTPS
        samesite='Lax'
    )
    
    return response

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    """
    登出接口
    """
    response = make_response(jsonify({
        'code': 200,
        'message': '登出成功'
    }))
    
    # 清除Cookie中的令牌
    response.set_cookie('token', '', expires=0)
    
    return response
