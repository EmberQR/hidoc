import utils.jwtauth
from flask import request, jsonify, Blueprint
from models import db, Image, Patient, Office, Case, ImageBbox, ImageSeg
from utils.oss import upload_to_oss, custom_endpoint
import uuid
import io
import os
import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut
import nibabel as nib
import numpy as np
from PIL import Image as PilImage
import tempfile
import requests
import re

image_bp = Blueprint('image', __name__)

def convert_to_png(pixel_array, is_dicom, ds=None):
    """
    将DICOM或NII文件的像素数组转换为PNG图像字节流。
    如果可用，会为DICOM应用VOI LUT。
    """
    # 归一化或应用LUT
    if is_dicom and ds and 'VOILUTSequence' in ds:
        # 应用VOI LUT
        arr = apply_voi_lut(pixel_array, ds)
    else:
        # 其他情况进行简单的归一化
        arr = pixel_array.astype(np.float32)
        if np.max(arr) != np.min(arr):
            arr = (arr - np.min(arr)) / (np.max(arr) - np.min(arr)) * 255.0
        else:
            arr = np.zeros_like(arr)
    
    arr = arr.astype(np.uint8)

    # 转换为灰度PIL图像
    if arr.ndim == 2:
        pil_img = PilImage.fromarray(arr, 'L')
    else: # 对于可能存在的多通道数据，只取第一通道
        pil_img = PilImage.fromarray(arr[:,:,0], 'L')
    
    # 保存到内存缓冲区
    img_buffer = io.BytesIO()
    pil_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

@image_bp.route('/api/image/add', methods=['POST'])
@utils.jwtauth.jwt_required
def add_image():
    """
    处理医学影像上传、处理和数据库记录创建。
    """
    creator_id = request.user_id

    # 1. --- 验证输入 ---
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '缺少必要参数: file'}), 400
    
    name = request.form.get('name')
    img_type = request.form.get('type')

    if not all([name, img_type]):
        return jsonify({'code': 400, 'message': '缺少必要参数: name, type'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '未选择文件'}), 400

    patient_id = request.form.get('patient_id') if request.form.get('patient_id') else None
    office_id = request.form.get('office_id') if request.form.get('office_id') else None
    case_id = request.form.get('case_id') if request.form.get('case_id') else None
    note = request.form.get('note')

    # 验证可选的外键是否存在
    if patient_id and not Patient.query.get(patient_id):
        return jsonify({'code': 404, 'message': '病人不存在'}), 404
    if office_id and not Office.query.get(office_id):
        return jsonify({'code': 404, 'message': '科室不存在'}), 404
    if case_id and not Case.query.get(case_id):
        return jsonify({'code': 404, 'message': '病历不存在'}), 404

    # 2. --- 文件分析 ---
    file_bytes = file.read()
    file_size_kb = len(file_bytes) / 1024.0
    file.close()

    file_stream = io.BytesIO(file_bytes)
    
    ds = None
    nib_img = None
    img_format = 'picture' 
    tmp_path = None

    try:
        file_stream.seek(0)
        ds = pydicom.dcmread(file_stream, stop_before_pixels=False)
        img_format = 'dicom'
    except pydicom.errors.InvalidDicomError:
        pass

    if not ds:
        try:
            # 使用临时文件来稳健地处理NII加载
            # 后缀有助于nibabel猜测文件类型
            suffix = os.path.splitext(file.filename)[1] if file.filename and file.filename.endswith(('.nii', '.nii.gz')) else '.tmp'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            
            nib_img = nib.load(tmp_path)
            img_format = 'nii'
        except (nib.filebasedimages.ImageFileError, ValueError):
            # 不是一个有效的NII文件。它将被作为 'picture' 处理。
            pass

    # 3. --- 处理并保存 ---
    try:
        # 情况 A: 普通图片
        if img_format == 'picture':
            oss_key = f"hidoc2/images/{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
            file_stream.seek(0)
            if not upload_to_oss(file_stream, oss_key):
                raise Exception("OSS upload failed")

            new_image = Image(
                name=name, format='picture', type=img_type, dim='2D',
                patient_id=patient_id, creator_id=creator_id,
                office_id=office_id, case_id=case_id, note=note,
                oss_key=oss_key, size=file_size_kb
            )
            db.session.add(new_image)
            db.session.commit()
            return jsonify({'code': 201, 'message': '影像上传成功', 'data': new_image.to_dict()}), 201

        # 情况 B: DICOM 或 NII
        is_dicom = (img_format == 'dicom')
        
        original_ext = ".dcm" if is_dicom else os.path.splitext(file.filename)[1]
        original_oss_key = f"hidoc2/images/{uuid.uuid4()}{original_ext}"
        file_stream.seek(0)
        if not upload_to_oss(file_stream, original_oss_key):
            raise Exception("Original file OSS upload failed")

        pixel_array = ds.pixel_array if is_dicom else nib_img.get_fdata()
        shape = pixel_array.shape
        is_3d = (hasattr(ds, 'NumberOfFrames') and ds.NumberOfFrames > 1) if is_dicom else (pixel_array.ndim >= 3)
        
        # B.1 --- 处理3D影像 ---
        if is_3d:
            slice_x, slice_y, slice_z = (shape[2], shape[1], shape[0]) if is_dicom else (shape[0], shape[1], shape[2])
            
            volume_image = Image(
                name=name, format=img_format, type=img_type, dim='3D',
                patient_id=patient_id, creator_id=creator_id,
                office_id=office_id, case_id=case_id, note=note,
                oss_key=original_oss_key, size=file_size_kb,
                slice_x=slice_x, slice_y=slice_y, slice_z=slice_z
            )
            db.session.add(volume_image)
            db.session.flush()
            parent_id = volume_image.id

            axes = {'x': (slice_x, ' sagittal'), 'y': (slice_y, ' coronal'), 'z': (slice_z, ' axial')}
            for axis_name, (slice_count, axis_label) in axes.items():
                for i in range(slice_count):
                    if axis_name == 'z':
                        slice_arr = pixel_array[i, :, :] if is_dicom else pixel_array[:, :, i].T
                    elif axis_name == 'y':
                        slice_arr = pixel_array[:, i, :] if is_dicom else pixel_array[:, i, :].T
                    else: # x
                        slice_arr = pixel_array[:, :, i] if is_dicom else pixel_array[i, :, :].T
                    
                    png_buffer = convert_to_png(slice_arr, is_dicom, ds)
                    png_oss_key = f"hidoc2/images/{uuid.uuid4()}.png"
                    png_size_kb = len(png_buffer.getvalue()) / 1024.0
                    upload_to_oss(png_buffer, png_oss_key)
                    slice_img = Image(
                        name=f"{name}_{axis_label.strip()}_{i}", format='picture', type=img_type, dim='2D',
                        creator_id=creator_id, oss_key=png_oss_key, size=png_size_kb,
                        parent_image_id=parent_id, slice_direction=axis_name, slice=i
                    )
                    db.session.add(slice_img)
        # B.2 --- 处理2D影像 ---
        else:
            slice_y, slice_x = shape[:2]
            
            main_image = Image(
                name=name, format=img_format, type=img_type, dim='2D',
                patient_id=patient_id, creator_id=creator_id,
                office_id=office_id, case_id=case_id, note=note,
                oss_key=original_oss_key, size=file_size_kb,
                slice_x=slice_x, slice_y=slice_y
            )
            db.session.add(main_image)
            db.session.flush()
            parent_id = main_image.id

            png_buffer = convert_to_png(pixel_array, is_dicom, ds)
            png_oss_key = f"hidoc2/images/{uuid.uuid4()}.png"
            png_size_kb = len(png_buffer.getvalue()) / 1024.0
            upload_to_oss(png_buffer, png_oss_key)
            
            vis_image = Image(
                name=f"{name}_preview", format='picture', type=img_type, dim='2D',
                creator_id=creator_id, oss_key=png_oss_key, size=png_size_kb,
                parent_image_id=parent_id
            )
            db.session.add(vis_image)

        db.session.commit()
        return jsonify({'code': 201, 'message': '影像处理成功'}), 201

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'处理影像时发生内部错误: {str(e)}'}), 500
    finally:
        file_stream.close()
        # 确保在使用完毕后删除临时文件
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@image_bp.route('/api/image/<int:image_id>', methods=['GET'])
@utils.jwtauth.jwt_required
def get_image_preview(image_id):
    """
    获取单个影像的预览信息。
    - 对于2D影像，返回源文件URL和单个预览图URL。
    - 对于3D影像，根据direction参数返回对应方向的所有切片URL。
    """
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'code': 404, 'message': '影像不存在'}), 404

    base_url = custom_endpoint
    response_data = {'image_info': image.to_dict()}

    # --- 3D影像处理 ---
    if image.dim == '3D':
        direction = request.args.get('direction', 'z')
        if direction not in ['x', 'y', 'z']:
            return jsonify({'code': 400, 'message': '无效的direction参数，应为 "x"、"y" 或 "z"'}), 400

        source_url = f"{base_url}/{image.oss_key}"
        
        slices = Image.query.filter_by(
            parent_image_id=image.id,
            slice_direction=direction
        ).order_by(Image.slice.asc()).all()
        
        slice_previews = [
            {'slice': s.slice, 'url': f"{base_url}/{s.oss_key}", 'id': s.id} for s in slices
        ]
        
        # 查询哪些切片包含标注信息 (Bbox)
        annotated_slices = []
        if slices:
            slice_ids = [s.id for s in slices]
            # 查询所有相关的bbox记录，然后获取有bbox的image_id
            annotated_slice_ids_query = db.session.query(ImageBbox.image_id).filter(
                ImageBbox.image_id.in_(slice_ids)
            ).distinct()
            
            annotated_slice_ids = {row.image_id for row in annotated_slice_ids_query}

            # 过滤出包含标注的切片索引
            annotated_slices = [s.slice for s in slices if s.id in annotated_slice_ids]

        response_data.update({
            'dim': '3D',
            'source_url': source_url,
            'direction': direction,
            'slice_previews': slice_previews,
            'annotated_slices': annotated_slices
        })

    # --- 2D影像处理 ---
    elif image.dim == '2D':
        source_url = f"{base_url}/{image.oss_key}"
        preview_url = source_url # 默认为自身

        # 如果是专业的2D影像格式，则查找其单独生成的预览图
        if image.format in ['dicom', 'nii']:
            preview_image = Image.query.filter_by(parent_image_id=image.id).first()
            if preview_image:
                preview_url = f"{base_url}/{preview_image.oss_key}"
        
        response_data.update({
            'dim': '2D',
            'source_url': source_url,
            'preview_url': preview_url,
        })
    
    else:
        return jsonify({'code': 500, 'message': '未知的影像维度'}), 500

    return jsonify({'code': 200, 'message': '获取成功', 'data': response_data})


@image_bp.route('/api/image/<int:image_id>', methods=['PUT'])
@utils.jwtauth.jwt_required
def update_image(image_id):
    """
    编辑影像备注 (只允许操作主影像)
    """
    user_id = request.user_id
    data = request.get_json()
    if not data or 'note' not in data:
        return jsonify({'code': 400, 'message': '请求体中缺少必要参数: note'}), 400

    image = Image.query.get(image_id)
    if not image:
        return jsonify({'code': 404, 'message': '影像不存在'}), 404

    # 校验是否为主影像
    if image.parent_image_id is not None:
        return jsonify({'code': 403, 'message': '只允许编辑主影像的备注'}), 403

    # 校验创建者权限
    if image.creator_id != user_id:
        return jsonify({'code': 403, 'message': '您无权编辑此影像'}), 403

    try:
        image.note = data['note']
        db.session.commit()
        return jsonify({'code': 200, 'message': '影像备注更新成功', 'data': image.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'数据库错误: {str(e)}'}), 500


@image_bp.route('/api/image/<int:image_id>', methods=['DELETE'])
@utils.jwtauth.jwt_required
def delete_image(image_id):
    """
    删除影像 (只允许操作主影像)
    删除主影像会一并删除其所有子切片和相关标注
    """
    user_id = request.user_id

    image = Image.query.get(image_id)
    if not image:
        return jsonify({'code': 404, 'message': '影像不存在'}), 404

    # 校验是否为主影像
    if image.parent_image_id is not None:
        return jsonify({'code': 403, 'message': '只允许删除主影像'}), 403

    # 校验创建者权限
    if image.creator_id != user_id:
        return jsonify({'code': 403, 'message': '您无权删除此影像'}), 403
    
    try:
        # OSS上的文件不会被删除，只删除数据库记录
        db.session.delete(image)
        db.session.commit()
        return jsonify({'code': 200, 'message': '影像删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'数据库错误: {str(e)}'}), 500


@image_bp.route('/api/image/list', methods=['GET'])
@utils.jwtauth.jwt_required
def list_images():
    """
    获取当前医生创建的所有影像列表 (仅父影像)
    """
    creator_id = request.user_id
    
    # 只查询 parent_image_id 为 NULL 的顶层影像
    images = Image.query.filter_by(creator_id=creator_id, parent_image_id=None).order_by(Image.created_at.desc()).all()
    
    results = []
    base_url = "https://cdn.ember.ac.cn"

    for image in images:
        image_data = image.to_dict()
        source_url = f"{base_url}/{image.oss_key}"
        preview_url = source_url  # 默认预览URL为源URL

        # 1. 对于2D picture类型，使用源URL作为预览 (默认行为)
        
        # 2. 对于2D dicom/nii, 查找其子预览影像
        if image.dim == '2D' and image.format in ['dicom', 'nii']:
            preview_image = Image.query.filter_by(parent_image_id=image.id).first()
            if preview_image:
                preview_url = f"{base_url}/{preview_image.oss_key}"
        
        # 3. 对于3D dicom/nii, 查找第一个切片作为预览
        elif image.dim == '3D':
            first_slice = Image.query.filter_by(parent_image_id=image.id).order_by(Image.id.asc()).first()
            if first_slice:
                preview_url = f"{base_url}/{first_slice.oss_key}"

        image_data['source_url'] = source_url
        image_data['preview_url'] = preview_url
        results.append(image_data)
        
    return jsonify({'code': 200, 'message': '查询成功', 'data': results})


@image_bp.route('/api/image/annotate', methods=['POST'])
@utils.jwtauth.jwt_required
def add_annotation():
    """
    为影像添加标注 (目前仅支持bbox)
    """
    creator_id = request.user_id
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    image_id = data.get('image_id')
    anno_type = data.get('anno_type')

    if not all([image_id, anno_type]):
        return jsonify({'code': 400, 'message': '缺少必要参数: image_id, anno_type'}), 400

    image = Image.query.get(image_id)
    if not image:
        return jsonify({'code': 404, 'message': '影像不存在'}), 404
    
    # 检查影像是否为可标注的2D图片
    if image.format != 'picture':
        return jsonify({'code': 400, 'message': '标注功能仅支持 picture 格式的影像或切片'}), 400

    if anno_type == 'bbox':
        required_fields = ['up_left_x', 'up_left_y', 'bottom_right_x', 'bottom_right_y']
        if not all(field in data for field in required_fields):
            return jsonify({'code': 400, 'message': f'缺少bbox必要参数: {required_fields}'}), 400

        try:
            new_bbox = ImageBbox(
                image_id=image_id,
                creator_id=creator_id,
                up_left_x=int(data['up_left_x']),
                up_left_y=int(data['up_left_y']),
                bottom_right_x=int(data['bottom_right_x']),
                bottom_right_y=int(data['bottom_right_y']),
                note=data.get('note')
            )
            db.session.add(new_bbox)
            db.session.commit()
            return jsonify({'code': 201, 'message': '标注创建成功', 'data': new_bbox.to_dict()}), 201
        except (ValueError, TypeError):
            return jsonify({'code': 400, 'message': '坐标参数必须是有效的整数'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'code': 500, 'message': f'数据库错误: {str(e)}'}), 500
    
    elif anno_type == 'mask':
        return jsonify({'code': 501, 'message': 'Mask标注功能暂未实现'}), 501
    else:
        return jsonify({'code': 400, 'message': '无效的anno_type，应为 "bbox" 或 "mask"'}), 400

@image_bp.route('/api/image/annotate', methods=['GET'])
@utils.jwtauth.jwt_required
def get_annotations():
    """
    获取影像的标注信息
    """
    image_id = request.args.get('image_id')
    anno_type = request.args.get('anno_type')

    if not all([image_id, anno_type]):
        return jsonify({'code': 400, 'message': '缺少必要参数: image_id, anno_type'}), 400
    
    if not Image.query.get(image_id):
        return jsonify({'code': 404, 'message': '影像不存在'}), 404

    if anno_type == 'bbox':
        bboxes = ImageBbox.query.filter_by(image_id=image_id).all()
        data = []
        for bbox in bboxes:
            bbox_data = bbox.to_dict()
            bbox_data['creator_name'] = bbox.creator.name if bbox.creator else '未知'
            data.append(bbox_data)
        return jsonify({'code': 200, 'message': '查询成功', 'data': data})
    
    else:
        return jsonify({'code': 400, 'message': '无效的anno_type'}), 400

@image_bp.route('/api/image/annotate', methods=['DELETE'])
@utils.jwtauth.jwt_required
def delete_annotation():
    """
    删除指定的标注
    """
    user_id = request.user_id
    data = request.get_json()
    anno_id = data.get('anno_id')
    anno_type = data.get('anno_type')

    if not all([anno_id, anno_type]):
        return jsonify({'code': 400, 'message': '请求体中缺少必要参数: anno_id, anno_type'}), 400

    if anno_type == 'bbox':
        bbox = ImageBbox.query.get(anno_id)
        if not bbox:
            return jsonify({'code': 404, 'message': '标注不存在'}), 404
        
        if bbox.creator_id != user_id:
            print(bbox.creator_id, user_id)
            return jsonify({'code': 403, 'message': '您无权删除此标注'}), 403
            
        try:
            db.session.delete(bbox)
            db.session.commit()
            return jsonify({'code': 200, 'message': '标注删除成功'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'code': 500, 'message': f'数据库错误: {str(e)}'}), 500
    
    else:
        return jsonify({'code': 400, 'message': '无效的anno_type'}), 400

@image_bp.route('/api/image/annotate', methods=['PUT'])
@utils.jwtauth.jwt_required
def update_annotation():
    """
    更新指定的标注信息
    """
    user_id = request.user_id
    data = request.get_json()
    anno_id = data.get('anno_id')
    anno_type = data.get('anno_type')

    if not all([anno_id, anno_type]):
        return jsonify({'code': 400, 'message': '请求体中缺少必要参数: anno_id, anno_type'}), 400

    if anno_type == 'bbox':
        bbox = ImageBbox.query.get(anno_id)
        if not bbox:
            return jsonify({'code': 404, 'message': '标注不存在'}), 404

        if bbox.creator_id != user_id:
            return jsonify({'code': 403, 'message': '您无权编辑此标注'}), 403

        # 更新字段
        try:
            for key, value in data.items():
                if key in ['up_left_x', 'up_left_y', 'bottom_right_x', 'bottom_right_y']:
                    setattr(bbox, key, int(value))
                elif key == 'note':
                    setattr(bbox, key, value)
            
            db.session.commit()
            return jsonify({'code': 200, 'message': '标注更新成功', 'data': bbox.to_dict()})
        except (ValueError, TypeError):
            return jsonify({'code': 400, 'message': '坐标参数必须是有效的整数'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'code': 500, 'message': f'数据库错误: {str(e)}'}), 500
            
    else:
        return jsonify({'code': 400, 'message': '无效的anno_type'}), 400


@image_bp.route('/api/image/seg', methods=['POST'])
@utils.jwtauth.jwt_required
def seg_image():
    """
    接收影像ID和查询词，调用AI服务进行分割，并存储结果。
    """
    creator_id = request.user_id
    data = request.get_json()
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    image_id = data.get('image_id')
    query = data.get('query')

    if not all([image_id, query]):
        return jsonify({'code': 400, 'message': '缺少必要参数: image_id, query'}), 400

    image = Image.query.get(image_id)
    if not image:
        return jsonify({'code': 404, 'message': '影像不存在'}), 404

    if image.format != 'picture' or image.dim != '2D':
        return jsonify({'code': 400, 'message': 'AI分割仅支持2D picture格式的影像'}), 400

    try:
        # 1. 从OSS获取影像文件
        image_url = f"{custom_endpoint}/{image.oss_key}"
        image_response = requests.get(image_url, timeout=10)
        image_response.raise_for_status()
        image_bytes = image_response.content
        
        # 从oss_key中提取文件名
        filename = image.oss_key.split('/')[-1]

        # 2. 调用外部AI预测服务
        predict_url = 'http://localhost:6006/predict'
        files = {'image': (filename, image_bytes, 'application/octet-stream')}
        payload = {'query': query}
        
        try:
            predict_response = requests.post(predict_url, files=files, data=payload, timeout=60)
            predict_response.raise_for_status()
            predict_data = predict_response.json()
        except requests.exceptions.RequestException as e:
            return jsonify({'code': 503, 'message': f'调用AI服务失败: {e}'}), 503

        # 3. 将结果存入数据库
        raw_reasoning = predict_data.get('result', '')
        normalized_reasoning = raw_reasoning
        if raw_reasoning:
            # 规范化AI模型输出的文本，去除序号和括号间的空格，以匹配前端解析规则
            normalized_reasoning = re.sub(r'(\d+)\.\s+【', r'\1.【', raw_reasoning)
            
        new_seg = ImageSeg(
            image_id=image_id,
            creator_id=creator_id,
            query=query,
            reasoning=normalized_reasoning,
            oss_key=predict_data.get('oss_key')
        )
        db.session.add(new_seg)
        db.session.commit()

        return jsonify({'code': 201, 'message': '影像分割成功', 'data': new_seg.to_dict()}), 201

    except requests.exceptions.HTTPError as e:
        return jsonify({'code': 500, 'message': f'从OSS获取影像失败: {e}'}), 500
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'处理请求时发生内部错误: {str(e)}'}), 500


@image_bp.route('/api/image/seg/list', methods=['GET'])
@utils.jwtauth.jwt_required
def list_image_segs():
    """
    获取指定影像的所有AI分割记录，支持分页。
    """
    image_id = request.args.get('image_id', type=int)
    if not image_id:
        return jsonify({'code': 400, 'message': '缺少必要参数: image_id'}), 400

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    image = Image.query.get(image_id)
    if not image:
        return jsonify({'code': 404, 'message': '影像不存在'}), 404
    
    if image.format != 'picture' or image.dim != '2D':
        return jsonify({'code': 400, 'message': '此接口仅支持查询2D picture格式影像的分割记录'}), 400
    
    try:
        pagination = db.session.query(ImageSeg).filter_by(image_id=image_id) \
            .order_by(ImageSeg.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)
        
        segs = pagination.items
        data = [seg.to_dict() for seg in segs]

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
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': f'查询时发生内部错误: {str(e)}'}), 500

