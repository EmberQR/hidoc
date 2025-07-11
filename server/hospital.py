import utils.jwtauth
from flask import request, jsonify, Blueprint, make_response
from sqlalchemy import distinct
from sqlalchemy.orm import joinedload
from models import db, Doctor, Office, DoctorOffice, DoctorHospital, Patient, Case, Image
from datetime import datetime

hospital_bp = Blueprint('hospital', __name__)

@hospital_bp.route('/api/hospital/office', methods=['GET'])
@utils.jwtauth.jwt_required
def get_doctor_offices():
    """
    获取当前登录医生在指定医院负责的所有科室列表。
    如果医生负责的是一个父科室，则返回该科室及其所有子科室。
    结果会自动去重。
    
    请求参数:
    - hospital_id: 医院ID
    
    返回:
    {
        "code": 200,
        "message": "获取科室列表成功",
        "data": [
            {
                "id": 科室ID,
                "name": "科室名称",
                "parent_id": 父科室ID,
                "hospital_id": 医院ID,
                "created_at": "创建时间",
                "parent_path": [
                    {
                        "id": 父科室ID,
                        "name": "父科室名称",
                        "parent_id": 上级父科室ID,
                        "hospital_id": 医院ID,
                        "created_at": "创建时间"
                    },
                    ...
                ]
            },
            ...
        ]
    }
    """
    user_id = request.user_id
    hospital_id = request.args.get('hospital_id')
    
    if not hospital_id:
        return jsonify({
            'code': 400,
            'message': '缺少必要参数: hospital_id'
        }), 400
    
    try:
        hospital_id = int(hospital_id)
    except ValueError:
        return jsonify({
            'code': 400,
            'message': 'hospital_id必须是整数'
        }), 400
    
    # 验证医生是否属于该医院
    doctor_hospital = DoctorHospital.query.filter_by(
        doc_id=user_id,
        hosp_id=hospital_id
    ).first()
    
    if not doctor_hospital:
        return jsonify({
            'code': 403,
            'message': '您不属于该医院或该医院不存在'
        }), 403
    
    # 1. 获取医生在该医院直接负责的所有科室
    doctor_offices = db.session.query(Office).join(
        DoctorOffice, Office.id == DoctorOffice.off_id
    ).filter(
        DoctorOffice.doc_id == user_id,
        Office.hospital_id == hospital_id
    ).all()

    # 2. 收集所有相关科室（直接负责的 + 子科室），并去重
    final_offices_map = {} # 使用字典去重, key: office.id, value: office object

    def get_all_descendants(office):
        # 递归函数，获取一个科室及其所有子孙科室
        if office.id not in final_offices_map:
            final_offices_map[office.id] = office
            # office.children 来自于 models.py 中的 backref
            for child in office.children:
                get_all_descendants(child)

    for office in doctor_offices:
        get_all_descendants(office)

    # 3. 为每个科室构建完整的父科室路径
    result = []
    # 预先获取医院所有科室，以高效构建父路径，避免循环查库
    all_hospital_offices = {o.id: o for o in Office.query.filter_by(hospital_id=hospital_id).all()}

    for office in final_offices_map.values():
        office_data = office.to_dict()
        parent_path = []
        
        current_parent_id = office.parent_id
        while current_parent_id:
            # 使用预先获取的字典来查找父科室
            parent_office = all_hospital_offices.get(current_parent_id)
            if parent_office:
                parent_path.append(parent_office.to_dict())
                current_parent_id = parent_office.parent_id
            else:
                break
        
        # 反转路径，使其从顶层父科室开始
        parent_path.reverse()
        office_data['parent_path'] = parent_path
        result.append(office_data)
    
    return make_response(jsonify({
        'code': 200,
        'message': '获取科室列表成功',
        'data': result
    }))

def get_all_child_offices(parent_office_id):
    """
    递归获取一个科室下的所有子科室ID
    """
    # 使用集合以避免重复
    all_office_ids = {int(parent_office_id)}
    # 待检查的科室ID队列
    offices_to_check = [int(parent_office_id)]
    
    while offices_to_check:
        current_id = offices_to_check.pop(0)
        # 查询以当前科室为父科室的所有子科室
        children = Office.query.filter_by(parent_id=current_id).all()
        for child in children:
            if child.id not in all_office_ids:
                all_office_ids.add(child.id)
                offices_to_check.append(child.id)
                
    return list(all_office_ids)

@hospital_bp.route('/api/hospital/case', methods=['GET'])
@utils.jwtauth.jwt_required
def get_cases_by_office():
    """
    根据科室ID获取所有病历（包括子科室），支持分页、病人姓名搜索和只看我的病历
    """
    user_id = request.user_id
    office_id = request.args.get('office_id')
    patient_name = request.args.get('patient_name')
    my_case = request.args.get('my_case') # 'true' or 'false'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if not office_id:
        return jsonify({'code': 400, 'message': '缺少office_id参数'}), 400

    try:
        office_id = int(office_id)
    except ValueError:
        return jsonify({'code': 400, 'message': 'office_id必须是整数'}), 400

    # 检查科室是否存在
    office = Office.query.get(office_id)
    if not office:
        return jsonify({'code': 404, 'message': '科室不存在'}), 404

    # 获取该科室及其所有子科室的ID
    all_office_ids = get_all_child_offices(office_id)

    # 在这些科室中查询病历
    cases_query = Case.query.filter(Case.office_id.in_(all_office_ids))
    
    # 如果提供了病人姓名，则加入查询条件
    if patient_name:
        cases_query = cases_query.join(Patient).filter(Patient.name.contains(patient_name))
    
    # 如果勾选了"只显示我创建的"
    if my_case == 'true':
        cases_query = cases_query.filter(Case.doctor_id == user_id)

    # 按病历日期降序排序
    cases_pagination = cases_query.order_by(Case.case_date.desc(), Case.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    cases = cases_pagination.items
    
    # 优化：一次性获取所有相关影像及其预览图
    images_by_case_id = {}
    case_ids = [c.id for c in cases]
    
    if case_ids:
        # 1. 获取所有病例关联的主影像
        main_images = db.session.query(Image).filter(
            Image.case_id.in_(case_ids),
            Image.parent_image_id.is_(None)
        ).all()

        main_image_ids = [img.id for img in main_images]
        previews_by_parent_id = {}

        if main_image_ids:
            # 2. 为兼容旧版MySQL，采用两步查询法获取预览图
            # 首先，获取所有主影像关联的子影像
            all_child_images = db.session.query(Image).filter(
                Image.parent_image_id.in_(main_image_ids)
            ).order_by(Image.parent_image_id, Image.id.asc()).all()

            # 然后，在Python中处理，为每个父ID找到第一个子影像
            for child in all_child_images:
                if child.parent_image_id not in previews_by_parent_id:
                    previews_by_parent_id[child.parent_image_id] = child

        # 3. 构建影像信息并按case_id分组
        base_url = "https://cdn.ember.ac.cn"
        for img in main_images:
            preview_url = f"{base_url}/{img.oss_key}" # 默认是源文件

            if img.format in ['dicom', 'nii']:
                preview_image = previews_by_parent_id.get(img.id)
                if preview_image:
                    preview_url = f"{base_url}/{preview_image.oss_key}"

            image_info = {
                'image_id': img.id,
                'name': img.name,
                'preview_url': preview_url, 
                'dim': img.dim
            }
            if img.case_id not in images_by_case_id:
                images_by_case_id[img.case_id] = []
            images_by_case_id[img.case_id].append(image_info)
    
    # 格式化返回数据
    data = []
    for case in cases:
        case_data = case.to_dict()
        case_data['patient_name'] = case.patient.name
        case_data['doctor_name'] = case.doctor.name
        case_data['office_name'] = case.office.name
        case_data['images'] = images_by_case_id.get(case.id, []) # 添加影像列表
        data.append(case_data)

    return jsonify({
        'code': 200,
        'message': '查询成功',
        'data': data,
        'pagination': {
            'page': cases_pagination.page,
            'per_page': cases_pagination.per_page,
            'total_pages': cases_pagination.pages,
            'total_items': cases_pagination.total
        }
    })

@hospital_bp.route('/api/hospital/add_patient', methods=['POST'])
@utils.jwtauth.jwt_required
def add_patient():
    """
    添加新病人
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    name = data.get('name')
    gender = data.get('gender')
    birthday = data.get('birthday')  # birthday是可选的

    if not name or not gender:
        return jsonify({'code': 400, 'message': '缺少必要参数: name, gender'}), 400

    if gender not in ['男', '女', '未知']:
        return jsonify({'code': 400, 'message': 'gender参数无效，应为 "男"、"女" 或 "未知"'}), 400

    try:
        new_patient = Patient(name=name, gender=gender, birthday=birthday)
        db.session.add(new_patient)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'数据库错误: {str(e)}'}), 500

    return jsonify({
        'code': 201,
        'message': '添加病人成功',
        'data': new_patient.to_dict()
    }), 201

@hospital_bp.route('/api/hospital/case', methods=['POST'])
@utils.jwtauth.jwt_required
def add_case():
    """
    创建新病历
    """
    doctor_id = request.user_id
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    patient_id = data.get('patient_id')
    office_id = data.get('office_id')
    case_date_str = data.get('case_date')

    if not all([patient_id, office_id, case_date_str]):
        return jsonify({'code': 400, 'message': '缺少必要参数: patient_id, office_id, case_date'}), 400

    # 验证数据
    if not Patient.query.get(patient_id):
        return jsonify({'code': 404, 'message': '病人不存在'}), 404
        
    office = Office.query.get(office_id)
    if not office:
        return jsonify({'code': 404, 'message': '科室不存在'}), 404
        
    # 验证医生是否属于该科室所在的医院
    if not DoctorHospital.query.filter_by(doc_id=doctor_id, hosp_id=office.hospital_id).first():
        return jsonify({'code': 403, 'message': '您不属于该科室所在的医院，无法创建病历'}), 403

    try:
        case_date = datetime.strptime(case_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'code': 400, 'message': 'case_date格式不正确，应为YYYY-MM-DD'}), 400

    # 创建新病历
    new_case = Case(
        doctor_id=doctor_id,
        patient_id=patient_id,
        office_id=office_id,
        case_date=case_date,
        chief_complaint=data.get('chief_complaint'),
        present_illness_history=data.get('present_illness_history'),
        past_medical_history=data.get('past_medical_history'),
        personal_history=data.get('personal_history'),
        family_history=data.get('family_history'),
        physical_examination=data.get('physical_examination'),
        diagnosis=data.get('diagnosis'),
        treatment_plan=data.get('treatment_plan'),
        medication_details=data.get('medication_details'),
        notes=data.get('notes')
    )
    
    try:
        db.session.add(new_case)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'数据库错误: {str(e)}'}), 500

    return jsonify({'code': 201, 'message': '病历创建成功', 'data': new_case.to_dict()}), 201

@hospital_bp.route('/api/hospital/case', methods=['PUT'])
@utils.jwtauth.jwt_required
def update_case():
    """
    更新病历信息
    """
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    case_id = data.get('id')
    if not case_id:
        return jsonify({'code': 400, 'message': '缺少病历ID (id)'}), 400

    case = Case.query.get(case_id)
    if not case:
        return jsonify({'code': 404, 'message': '病历不存在'}), 404
    
    # 任何医生都可以编辑病历，也可以添加权限控制
    # if case.doctor_id != request.user_id:
    #     return jsonify({'code': 403, 'message': '您无权编辑此病历'}), 403

    # 更新字段
    for key, value in data.items():
        # id和创建时间不能被修改
        if key not in ['id', 'created_at', 'doctor_id', 'patient_id'] and hasattr(case, key):
            if key == 'case_date':
                try:
                    setattr(case, key, datetime.strptime(value, '%Y-%m-%d').date())
                except (ValueError, TypeError):
                    # 如果日期格式错误，可以忽略或返回错误
                    pass 
            else:
                setattr(case, key, value)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'数据库错误: {str(e)}'}), 500

    return jsonify({'code': 200, 'message': '病历更新成功', 'data': case.to_dict()})

@hospital_bp.route('/api/hospital/case/single', methods=['GET'])
@utils.jwtauth.jwt_required
def get_single_case():
    """
    根据病历ID获取单个病历的详细信息，包括其关联的所有影像
    """
    case_id = request.args.get('case_id')
    if not case_id:
        return jsonify({'code': 400, 'message': '缺少 case_id 参数'}), 400

    try:
        case_id = int(case_id)
    except ValueError:
        return jsonify({'code': 400, 'message': 'case_id 必须是整数'}), 400

    case = Case.query.options(
        joinedload(Case.patient),
        joinedload(Case.doctor),
        joinedload(Case.office).joinedload(Office.hospital)
    ).filter(Case.id == case_id).first()

    if not case:
        return jsonify({'code': 404, 'message': '病历不存在'}), 404

    # 获取病历关联的影像
    images_by_case_id = {}
    main_images = db.session.query(Image).filter(
        Image.case_id == case_id,
        Image.parent_image_id.is_(None)
    ).all()

    main_image_ids = [img.id for img in main_images]
    previews_by_parent_id = {}

    if main_image_ids:
        all_child_images = db.session.query(Image).filter(
            Image.parent_image_id.in_(main_image_ids)
        ).order_by(Image.parent_image_id, Image.id.asc()).all()

        for child in all_child_images:
            if child.parent_image_id not in previews_by_parent_id:
                previews_by_parent_id[child.parent_image_id] = child

    image_list = []
    base_url = "https://cdn.ember.ac.cn"
    for img in main_images:
        preview_url = f"{base_url}/{img.oss_key}"

        if img.format in ['dicom', 'nii']:
            preview_image = previews_by_parent_id.get(img.id)
            if preview_image:
                preview_url = f"{base_url}/{preview_image.oss_key}"

        image_info = {
            'image_id': img.id,
            'name': img.name,
            'preview_url': preview_url,
            'dim': img.dim,
            'format': img.format,
            'type': img.type,
            'note': img.note
        }
        image_list.append(image_info)
    
    # 格式化返回数据
    case_data = case.to_dict()
    case_data['patient_name'] = case.patient.name
    case_data['doctor_name'] = case.doctor.name
    case_data['office_name'] = case.office.name
    case_data['hospital_name'] = case.office.hospital.name if case.office and case.office.hospital else '未知'
    case_data['images'] = image_list

    return jsonify({
        'code': 200,
        'message': '查询成功',
        'data': case_data
    })

# 根据姓名搜索病人
@hospital_bp.route('/api/hospital/patient', methods=['GET'])
@utils.jwtauth.jwt_required
def search_patient():
    """
    根据姓名搜索病人
    """
    name = request.args.get('name')
    if not name:
        return jsonify({'code': 400, 'message': '缺少必要参数: name'}), 400
    
    patients = Patient.query.filter(Patient.name.contains(name)).all()
    return jsonify({
        'code': 200,
        'message': '搜索成功',
        'data': [patient.to_dict() for patient in patients]
    })
