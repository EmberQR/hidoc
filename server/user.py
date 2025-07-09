import utils.jwtauth
from flask import request, jsonify, Blueprint, make_response
from models import db, Doctor, DoctorHospital, Hospital

user_bp = Blueprint('user', __name__)

@user_bp.route('/api/user/info', methods=['GET'])
@utils.jwtauth.jwt_required
def get_user_info():
    user_id = request.user_id
    doctor = Doctor.query.filter_by(id=user_id).first()
    return make_response(jsonify({
        'code': 200,
        'message': '获取用户信息成功',
        'data': doctor.to_dict()
    }))

# 获取医生的医院列表。用于医生登录后选择自己的一个医院
@user_bp.route('/api/user/hospitals', methods=['GET'])
@utils.jwtauth.jwt_required
def get_user_hospitals():
    user_id = request.user_id
    
    # 查询医生关联的所有未删除的医院
    hospitals = Hospital.query.join(
        DoctorHospital, Hospital.id == DoctorHospital.hosp_id
    ).filter(
        DoctorHospital.doc_id == user_id,
        Hospital.deleted == False
    ).all()
    
    # 转换为字典列表
    hospital_list = [hospital.to_dict() for hospital in hospitals]
    
    return make_response(jsonify({
        'code': 200,
        'message': '获取医生医院列表成功',
        'data': hospital_list
    }))

# 修改医生个人信息
@user_bp.route('/api/user/update', methods=['PUT'])
@utils.jwtauth.jwt_required
def update_user_info():
    user_id = request.user_id
    data = request.json
    
    if not data:
        return jsonify({
            'code': 400,
            'message': '请求体不能为空'
        }), 400
    
    doctor = Doctor.query.filter_by(id=user_id).first()
    if not doctor:
        return jsonify({
            'code': 404,
            'message': '用户不存在'
        }), 404
    
    # 只允许修改姓名和性别
    if 'name' in data:
        doctor.name = data['name']
    
    if 'gender' in data:
        if data['gender'] not in ['男', '女', '未知']:
            return jsonify({
                'code': 400,
                'message': '性别必须是: 男, 女, 未知'
            }), 400
        doctor.gender = data['gender']
    
    try:
        db.session.commit()
        return make_response(jsonify({
            'code': 200,
            'message': '更新用户信息成功',
            'data': doctor.to_dict()
        }))
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'更新用户信息失败: {str(e)}'
        }), 500










