from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Hospital(db.Model):
    __tablename__ = 'hospital'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='医院ID')
    name = db.Column(db.String(100), nullable=False, comment='医院名称')
    address = db.Column(db.String(255), nullable=True, comment='医院地址')
    deleted = db.Column(db.Boolean, default=False, comment='逻辑删除标志，True表示已删除')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'deleted': self.deleted,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Doctor(db.Model):
    __tablename__ = 'doctor'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='医生ID')
    phone = db.Column(db.String(20), unique=True, nullable=False, comment='医生电话，唯一且非空')
    name = db.Column(db.String(100), nullable=False, comment='医生姓名')
    password = db.Column(db.String(100), nullable=False, comment='医生密码')
    gender = db.Column(db.Enum('男', '女', '未知'), nullable=False, comment='医生性别')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'name': self.name,
            'password': self.password,
            'gender': self.gender,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Office(db.Model):
    __tablename__ = 'office'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='科室ID')
    name = db.Column(db.String(100), nullable=False, comment='科室名称')
    parent_id = db.Column(db.Integer, db.ForeignKey('office.id', ondelete='CASCADE'), nullable=True, comment='上级科室ID')
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False, comment='所属医院ID')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')
    
    # 自引用关系，添加级联删除
    parent = db.relationship('Office', remote_side=[id], 
                           backref=db.backref('children', lazy='dynamic', cascade='all, delete-orphan'),
                           passive_deletes=True)
    # 与医院的关系
    hospital = db.relationship('Hospital', backref=db.backref('offices', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'hospital_id': self.hospital_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class DoctorOffice(db.Model):
    __tablename__ = 'doctor_office'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='关联ID')
    doc_id = db.Column(db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), nullable=False, comment='医生ID')
    off_id = db.Column(db.Integer, db.ForeignKey('office.id', ondelete='CASCADE'), nullable=False, comment='科室ID')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')
    
    # 关系
    doctor = db.relationship('Doctor', backref=db.backref('offices', lazy='dynamic', cascade='all, delete-orphan'))
    office = db.relationship('Office', backref=db.backref('doctors', lazy='dynamic', cascade='all, delete-orphan'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'doc_id': self.doc_id,
            'off_id': self.off_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class DoctorHospital(db.Model):
    __tablename__ = 'doctor_hospital'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='关联ID')
    doc_id = db.Column(db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), nullable=False, comment='医生ID')
    hosp_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False, comment='医院ID')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')
    
    # 关系
    doctor = db.relationship('Doctor', backref=db.backref('hospitals', lazy='dynamic', cascade='all, delete-orphan'))
    hospital = db.relationship('Hospital', backref=db.backref('doctors', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'doc_id': self.doc_id,
            'hosp_id': self.hosp_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Patient(db.Model):
    __tablename__ = 'patient'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='病人ID')
    name = db.Column(db.String(100), nullable=False, comment='病人姓名')
    gender = db.Column(db.Enum('男', '女', '未知'), nullable=False, comment='病人性别')
    birthday = db.Column(db.String(10), nullable=True, comment='出生日期，格式YYYY-MM-DD')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'birthday': self.birthday,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Case(db.Model):
    __tablename__ = 'case'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='病历ID')
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete='CASCADE'), nullable=False, comment='病人ID')
    office_id = db.Column(db.Integer, db.ForeignKey('office.id', ondelete='CASCADE'), nullable=False, comment='科室ID')
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), nullable=False, comment='医生ID')
    case_date = db.Column(db.Date, nullable=False, comment='就诊日期')
    chief_complaint = db.Column(db.Text, nullable=True, comment='主诉')
    present_illness_history = db.Column(db.Text, nullable=True, comment='现病史')
    past_medical_history = db.Column(db.Text, nullable=True, comment='既往史')
    personal_history = db.Column(db.Text, nullable=True, comment='个人史')
    family_history = db.Column(db.Text, nullable=True, comment='家族史')
    physical_examination = db.Column(db.Text, nullable=True, comment='体格检查')
    diagnosis = db.Column(db.Text, nullable=True, comment='诊断结果')
    treatment_plan = db.Column(db.Text, nullable=True, comment='治疗方案')
    medication_details = db.Column(db.Text, nullable=True, comment='用药详情')
    notes = db.Column(db.Text, nullable=True, comment='备注')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.TIMESTAMP, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    patient = db.relationship('Patient', backref=db.backref('cases', lazy='dynamic', cascade='all, delete-orphan'))
    office = db.relationship('Office', backref=db.backref('cases', lazy='dynamic'))
    doctor = db.relationship('Doctor', backref=db.backref('cases', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'office_id': self.office_id,
            'doctor_id': self.doctor_id,
            'case_date': self.case_date.strftime('%Y-%m-%d') if self.case_date else None,
            'chief_complaint': self.chief_complaint,
            'present_illness_history': self.present_illness_history,
            'past_medical_history': self.past_medical_history,
            'personal_history': self.personal_history,
            'family_history': self.family_history,
            'physical_examination': self.physical_examination,
            'diagnosis': self.diagnosis,
            'treatment_plan': self.treatment_plan,
            'medication_details': self.medication_details,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class Image(db.Model):
    __tablename__ = 'image'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='影像ID')
    name = db.Column(db.String(255), nullable=True, comment='影像名称')
    format = db.Column(db.Enum('dicom', 'nii', 'picture'), nullable=False, comment='影像格式')
    type = db.Column(db.Enum('X-ray', 'CT', 'MRI', 'PET', 'US', '其他'), nullable=False, comment='影像类型')
    dim = db.Column(db.Enum('2D', '3D'), nullable=False, default='2D', comment='影像维度')
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete='SET NULL'), nullable=True, comment='病人ID')
    creator_id = db.Column(db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), nullable=False, comment='创建者ID (医生)')
    office_id = db.Column(db.Integer, db.ForeignKey('office.id', ondelete='SET NULL'), nullable=True, comment='科室ID')
    case_id = db.Column(db.Integer, db.ForeignKey('case.id', ondelete='SET NULL'), nullable=True, comment='病历ID')
    note = db.Column(db.Text, nullable=True, comment='备注')
    oss_key = db.Column(db.String(255), nullable=False, unique=True, comment='OSS对象存储键')
    size = db.Column(db.Numeric(10, 2), nullable=False, comment='文件大小(KB)')
    parent_image_id = db.Column(db.Integer, db.ForeignKey('image.id', ondelete='CASCADE'), nullable=True, comment='父影像ID (用于3D影像切片)')
    slice_direction = db.Column(db.Enum('x', 'y', 'z'), nullable=True, comment='3D影像切片方向')
    slice = db.Column(db.Integer, nullable=True, comment='3D影像切片索引')
    slice_x = db.Column(db.Integer, nullable=True, comment='3D影像x方向切片数')
    slice_y = db.Column(db.Integer, nullable=True, comment='3D影像y方向切片数')
    slice_z = db.Column(db.Integer, nullable=True, comment='3D影像z方向切片数')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')
    
    # 关系
    patient = db.relationship('Patient', backref=db.backref('images', lazy='dynamic'))
    creator = db.relationship('Doctor', backref=db.backref('created_images', lazy='dynamic'))
    office = db.relationship('Office', backref=db.backref('images', lazy='dynamic'))
    case = db.relationship('Case', backref=db.backref('images', lazy='dynamic'))
    parent_image = db.relationship('Image', remote_side=[id], backref=db.backref('child_images', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'format': self.format,
            'type': self.type,
            'dim': self.dim,
            'patient_id': self.patient_id,
            'creator_id': self.creator_id,
            'office_id': self.office_id,
            'case_id': self.case_id,
            'note': self.note,
            'oss_key': self.oss_key,
            'size': float(self.size) if self.size is not None else None,
            'parent_image_id': self.parent_image_id,
            'slice_direction': self.slice_direction,
            'slice': self.slice,
            'slice_x': self.slice_x,
            'slice_y': self.slice_y,
            'slice_z': self.slice_z,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class ImageBbox(db.Model):
    __tablename__ = 'image_bbox'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='边界框标注ID')
    image_id = db.Column(db.Integer, db.ForeignKey('image.id', ondelete='CASCADE'), nullable=False, comment='影像ID')
    creator_id = db.Column(db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), nullable=False, comment='创建者ID (医生)')
    up_left_x = db.Column(db.Integer, nullable=False, comment='左上角X坐标')
    up_left_y = db.Column(db.Integer, nullable=False, comment='左上角Y坐标')
    bottom_right_x = db.Column(db.Integer, nullable=False, comment='右下角X坐标')
    bottom_right_y = db.Column(db.Integer, nullable=False, comment='右下角Y坐标')
    note = db.Column(db.Text, nullable=True, comment='备注')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')

    # 关系
    image = db.relationship('Image', backref=db.backref('bboxes', lazy='dynamic', cascade='all, delete-orphan'))
    creator = db.relationship('Doctor', backref=db.backref('created_bboxes', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'image_id': self.image_id,
            'creator_id': self.creator_id,
            'up_left_x': self.up_left_x,
            'up_left_y': self.up_left_y,
            'bottom_right_x': self.bottom_right_x,
            'bottom_right_y': self.bottom_right_y,
            'note': self.note,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class ImageMask(db.Model):
    __tablename__ = 'image_mask'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='掩码标注ID')
    image_id = db.Column(db.Integer, db.ForeignKey('image.id', ondelete='CASCADE'), nullable=False, comment='影像ID')
    creator_id = db.Column(db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), nullable=False, comment='创建者ID (医生)')
    mask_oss_key = db.Column(db.String(255), nullable=False, unique=True, comment='掩码文件OSS键')
    note = db.Column(db.Text, nullable=True, comment='备注')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')

    # 关系
    image = db.relationship('Image', backref=db.backref('masks', lazy='dynamic', cascade='all, delete-orphan'))
    creator = db.relationship('Doctor', backref=db.backref('created_masks', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'image_id': self.image_id,
            'creator_id': self.creator_id,
            'mask_oss_key': self.mask_oss_key,
            'note': self.note,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class ImageSeg(db.Model):
    __tablename__ = 'image_seg'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='AI分割结果ID')
    image_id = db.Column(db.Integer, db.ForeignKey('image.id', ondelete='CASCADE'), nullable=False, comment='影像ID')
    creator_id = db.Column(db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), nullable=False, comment='创建者ID (医生)')
    query = db.Column(db.Text, nullable=True, comment='分割查询')
    reasoning = db.Column(db.Text, nullable=True, comment='分割推理')
    oss_key = db.Column(db.String(255), nullable=False, unique=True, comment='分割结果OSS键')
    created_at = db.Column(db.TIMESTAMP, default=datetime.now, comment='创建时间')

    # 关系
    image = db.relationship('Image', backref=db.backref('segs', lazy='dynamic', cascade='all, delete-orphan'))
    creator = db.relationship('Doctor', backref=db.backref('created_segs', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'image_id': self.image_id,
            'creator_id': self.creator_id,
            'query': self.query,
            'reasoning': self.reasoning,
            'oss_key': self.oss_key,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
