import json
from flask import request, jsonify, Blueprint
from sqlalchemy.orm import joinedload
from models import db, Patient, Case, Image, AiAdvice, Office
import utils.jwtauth
from utils.silicon_flow import silicon_flow_client

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/api/patient/analyze', methods=['POST'])
@utils.jwtauth.jwt_required
def analyze_patient():
    """
    接收 patient_id，对病人的所有病历和影像进行AI分析，并存储建议。
    """
    creator_id = request.user_id
    data = request.get_json()

    if not data or 'patient_id' not in data:
        return jsonify({'code': 400, 'message': '请求体中缺少必要参数: patient_id'}), 400

    patient_id = data.get('patient_id')
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'code': 404, 'message': '病人不存在'}), 404

    # 1. 找出该病人的所有病历记录，按时间倒序
    cases = Case.query.filter_by(patient_id=patient_id).order_by(Case.created_at.desc()).all()
    if not cases:
        return jsonify({'code': 404, 'message': '该病人没有任何病历记录'}), 404

    # 2. 构建 Prompt
    prompt_content = []
    prompt_content.append(f"### 病人基本信息\n- **姓名**: {patient.name}\n- **性别**: {patient.gender}\n- **出生日期**: {patient.birthday}\n\n")
    prompt_content.append("### 病历与影像资料 (按就诊时间倒序)\n")

    for case in cases:
        case_date_str = case.case_date.strftime('%Y-%m-%d') if case.case_date else '未知日期'
        prompt_content.append(f"#### 病历记录 (ID: {case.id}) - {case_date_str}\n")
        prompt_content.append(f"- **主诉**: {case.chief_complaint or '无'}\n")
        prompt_content.append(f"- **现病史**: {case.present_illness_history or '无'}\n")
        prompt_content.append(f"- **既往史**: {case.past_medical_history or '无'}\n")
        prompt_content.append(f"- **诊断结果**: {case.diagnosis or '无'}\n")
        prompt_content.append(f"- **治疗方案**: {case.treatment_plan or '无'}\n")
        prompt_content.append(f"- **备注**: {case.notes or '无'}\n")

        # 找出关联的主影像记录 (parent_image_id 为 NULL)
        main_images = Image.query.filter_by(case_id=case.id, parent_image_id=None).all()
        if main_images:
            prompt_content.append("- **关联的主影像**:\n")
            for image in main_images:
                prompt_content.append(f"  - **影像 (ID: {image.id})**: {image.name}\n")
                prompt_content.append(f"    - **类型**: {image.type}, **格式**: {image.format}, **维度**: {image.dim}\n")
                prompt_content.append(f"    - **尺寸**: {image.size:.2f} KB\n")
                prompt_content.append(f"    - **上传时间**: {image.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                prompt_content.append(f"    - **医生备注**: {image.note or '无'}\n")
        prompt_content.append("\n")
    
    full_prompt = "".join(prompt_content)

    # 3. 让AI生成建议
    system_prompt = """你是一位专业的医疗领域AI助手。你的任务是基于提供的病人病历和影像资料，进行全面的疾病分析和治疗建议。
请严格按照以下JSON格式输出你的分析和建议，不要包含任何额外的解释或代码块标记 (如 ```json):
{
  "disease": "对患者病情的综合分析，包括可能的诊断、发展趋势等。分析必须基于提供的资料，并使用特定格式引用来源。例如：'根据[2023-08-15的病历](case,123)，患者主诉为头痛...'",
  "therapy": "根据你的分析，提供详细的治疗建议，包括进一步检查、治疗方案、用药建议等。同样，建议也必须引用资料来源。例如：'鉴于[CT影像](image,456)显示的结果，建议进行增强MRI检查...'"
}
引用格式说明：
- 引用病历: [显示文本](case,病历ID)
- 引用影像: [显示文本](image,影像ID)
请确保你的回答客观、专业，并严格遵守此格式。
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_prompt}
    ]
    print(messages)

    try:
        response_content = silicon_flow_client.chat(messages, json_output=True)
        if not response_content:
            return jsonify({'code': 500, 'message': 'AI服务未返回有效内容'}), 500

        ai_result = json.loads(response_content)
        disease_analysis = ai_result.get('disease')
        therapy_suggestion = ai_result.get('therapy')

        if not disease_analysis or not therapy_suggestion:
            return jsonify({'code': 500, 'message': 'AI返回的数据格式不完整'}), 500

    except json.JSONDecodeError:
        return jsonify({'code': 500, 'message': 'AI返回内容非标准JSON格式', 'raw_response': response_content}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': f'调用AI服务时发生错误: {str(e)}'}), 500

    # 4. 存入数据库
    try:
        new_advice = AiAdvice(
            creator_id=creator_id,
            patient_id=patient_id,
            disease=disease_analysis,
            therapy=therapy_suggestion
        )
        db.session.add(new_advice)
        db.session.commit()
        
        return jsonify({'code': 201, 'message': 'AI分析建议生成成功', 'data': new_advice.to_dict()}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'数据库存储错误: {str(e)}'}), 500


@patient_bp.route('/api/patient/list', methods=['GET'])
@utils.jwtauth.jwt_required
def list_patients():
    """
    获取当前医生负责过的所有病人列表，去重并分页。
    """
    doctor_id = request.user_id
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    try:
        # 通过 Case 表找到所有该医生接触过的病人ID，并去重
        # 然后基于这些病人ID进行分页查询
        pagination = db.session.query(Patient) \
            .join(Case, Patient.id == Case.patient_id) \
            .filter(Case.doctor_id == doctor_id) \
            .distinct() \
            .paginate(page=page, per_page=per_page, error_out=False)

        patients = pagination.items
        data = [patient.to_dict() for patient in patients]

        return jsonify({
            'code': 200,
            'message': '查询成功',
            'data': data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'查询时发生内部错误: {str(e)}'}), 500


@patient_bp.route('/api/patient/case', methods=['GET'])
@utils.jwtauth.jwt_required
def list_patient_cases():
    """
    获取某个病人的所有病历列表，从新到旧排序并分页。
    """
    patient_id = request.args.get('patient_id', type=int)
    if not patient_id:
        return jsonify({'code': 400, 'message': '缺少必要参数: patient_id'}), 400

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if not Patient.query.get(patient_id):
        return jsonify({'code': 404, 'message': '病人不存在'}), 404
    
    try:
        # 使用 joinedload 预加载关联的 doctor 和 office.hospital 信息，避免 N+1 查询
        pagination = Case.query.filter_by(patient_id=patient_id) \
            .options(
                joinedload(Case.doctor),
                joinedload(Case.office).joinedload(Office.hospital)
            ) \
            .order_by(Case.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)
        
        cases = pagination.items
        data = []
        for case in cases:
            case_data = case.to_dict()
            case_data['doctor_name'] = case.doctor.name if case.doctor else '未知'
            case_data['office_name'] = case.office.name if case.office else '未知'
            case_data['hospital_name'] = case.office.hospital.name if case.office and case.office.hospital else '未知'
            data.append(case_data)

        return jsonify({
            'code': 200,
            'message': '查询成功',
            'data': data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'查询时发生内部错误: {str(e)}'}), 500


@patient_bp.route('/api/patient/analyze', methods=['GET'])
@utils.jwtauth.jwt_required
def list_patient_analyses():
    """
    获取某个病人的所有AI智能辅诊记录，从新到旧排序并分页。
    """
    patient_id = request.args.get('patient_id', type=int)
    if not patient_id:
        return jsonify({'code': 400, 'message': '缺少必要参数: patient_id'}), 400

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if not Patient.query.get(patient_id):
        return jsonify({'code': 404, 'message': '病人不存在'}), 404
    
    try:
        pagination = AiAdvice.query.filter_by(patient_id=patient_id) \
            .order_by(AiAdvice.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)
        
        advices = pagination.items
        data = []
        for advice in advices:
            advice_data = advice.to_dict()
            advice_data['creator_name'] = advice.creator.name if advice.creator else '未知'
            data.append(advice_data)

        return jsonify({
            'code': 200,
            'message': '查询成功',
            'data': data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': f'查询时发生内部错误: {str(e)}'}), 500


@patient_bp.route('/api/patient/detail', methods=['GET'])
@utils.jwtauth.jwt_required
def get_patient_detail():
    """
    获取指定病人的详细信息。
    """
    patient_id = request.args.get('patient_id', type=int)
    if not patient_id:
        return jsonify({'code': 400, 'message': '缺少必要参数: patient_id'}), 400

    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'code': 404, 'message': '病人不存在'}), 404
    
    return jsonify({'code': 200, 'message': '查询成功', 'data': patient.to_dict()})