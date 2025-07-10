from flask import Blueprint, request, jsonify
from models import db, Case, Patient, ImageSeg, AiAdvice, Office, Image
import utils.jwtauth
from datetime import date, timedelta
from sqlalchemy import func

home_bp = Blueprint('home', __name__)

@home_bp.route('/api/home/data', methods=['GET'])
@utils.jwtauth.jwt_required
def get_home_data():
    """
    获取首页的统计数据
    """
    doctor_id = request.user_id
    hospital_id = request.args.get('hospital_id', type=int)

    if not hospital_id:
        return jsonify({'code': 400, 'message': '缺少必要参数: hospital_id'}), 400

    today = date.today()
    seven_days_ago = today - timedelta(days=6)

    # 1. total_cases: 医生在指定医院创建的总病历数
    total_cases = db.session.query(func.count(Case.id)).join(Office).filter(
        Case.doctor_id == doctor_id,
        Office.hospital_id == hospital_id
    ).scalar()

    # 2. today_cases: 医生今天在指定医院创建的病历数
    today_cases = db.session.query(func.count(Case.id)).join(Office).filter(
        Case.doctor_id == doctor_id,
        Office.hospital_id == hospital_id,
        func.date(Case.created_at) == today
    ).scalar()

    # 3. total_patients: 医生在指定医院负责过的病人总数 (去重)
    total_patients = db.session.query(func.count(func.distinct(Case.patient_id))).join(Office).filter(
        Case.doctor_id == doctor_id,
        Office.hospital_id == hospital_id
    ).scalar()

    # 4. ai_seg: 医生在指定医院创建的总AI影像分割记录数
    ai_seg = db.session.query(func.count(ImageSeg.id)).join(Image, ImageSeg.image_id == Image.id).join(Office, Image.office_id == Office.id).filter(
        ImageSeg.creator_id == doctor_id,
        Office.hospital_id == hospital_id
    ).scalar()

    # 5. today_ai_seg: 医生今天在指定医院创建的AI影像分割记录数
    today_ai_seg = db.session.query(func.count(ImageSeg.id)).join(Image, ImageSeg.image_id == Image.id).join(Office, Image.office_id == Office.id).filter(
        ImageSeg.creator_id == doctor_id,
        Office.hospital_id == hospital_id,
        func.date(ImageSeg.created_at) == today
    ).scalar()

    # 6. ai_advice: 医生总共创建的AI辅诊建议数 (不按医院筛选)
    ai_advice = db.session.query(func.count(AiAdvice.id)).filter(
        AiAdvice.creator_id == doctor_id
    ).scalar()

    # 7. today_ai_advice: 医生今天创建的AI辅诊建议数 (不按医院筛选)
    today_ai_advice = db.session.query(func.count(AiAdvice.id)).filter(
        AiAdvice.creator_id == doctor_id,
        func.date(AiAdvice.created_at) == today
    ).scalar()

    # 8. recent_cases: 最近7天医生在指定医院创建的病历数量
    recent_cases_data = db.session.query(
        func.date(Case.created_at).label('case_date'),
        func.count(Case.id).label('count')
    ).join(Office).filter(
        Case.doctor_id == doctor_id,
        Office.hospital_id == hospital_id,
        func.date(Case.created_at) >= seven_days_ago
    ).group_by(func.date(Case.created_at)).all()
    
    date_to_count = {r.case_date.strftime('%Y-%m-%d'): r.count for r in recent_cases_data}
    
    recent_cases = []
    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        date_str = day.strftime('%Y-%m-%d')
        count = date_to_count.get(date_str, 0)
        recent_cases.append({'日期': date_str, '数量': count})

    # 组装返回数据
    data = {
        'total_cases': total_cases,
        'today_cases': today_cases,
        'total_patients': total_patients,
        'ai_seg': ai_seg,
        'today_ai_seg': today_ai_seg,
        'ai_advice': ai_advice,
        'today_ai_advice': today_ai_advice,
        'recent_cases': recent_cases
    }

    return jsonify({'code': 200, 'message': '查询成功', 'data': data})
