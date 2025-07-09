import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app

class JWTAuth:
    @staticmethod
    def generate_token(user_id, phone, expire_hours=24):
        """
        生成JWT令牌
        
        Args:
            user_id: 用户ID
            phone: 用户手机号
            expire_hours: 过期时间(小时)，默认24小时
            
        Returns:
            生成的JWT令牌
        """
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=expire_hours),
            'iat': datetime.datetime.utcnow(),
            'sub': str(user_id),
            'phone': phone
        }
        return jwt.encode(
            payload,
            current_app.config.get('SECRET_KEY', 'hidoc_secret_key'),
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_token(token):
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            解码后的payload或None(如果验证失败)
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config.get('SECRET_KEY', 'hidoc_secret_key'),
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError as e:
            return None
    
    @staticmethod
    def refresh_token(token, expire_hours=24):
        """
        刷新JWT令牌
        
        Args:
            token: 原JWT令牌
            expire_hours: 新令牌过期时间(小时)
            
        Returns:
            新的JWT令牌或None(如果原令牌无效)
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config.get('SECRET_KEY', 'hidoc_secret_key'),
                algorithms=['HS256']
            )
            
            # 创建新的payload，保留原有信息但更新过期时间
            new_payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=expire_hours),
                'iat': datetime.datetime.utcnow(),
                'sub': payload['sub'],
                'phone': payload['phone']
            }
            
            return jwt.encode(
                new_payload,
                current_app.config.get('SECRET_KEY', 'hidoc_secret_key'),
                algorithm='HS256'
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

def jwt_required(f):
    """
    JWT认证装饰器，用于保护需要认证的API接口
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头或Cookie中获取token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            token = request.cookies.get('token')
            
        if not token:
            return jsonify({
                'code': 401,
                'message': '缺少认证令牌'
            }), 401
        
        # 验证token
        payload = JWTAuth.verify_token(token)
        if not payload:
            return jsonify({
                'code': 401,
                'message': '认证令牌无效或已过期'
            }), 401
            
        # 将用户信息添加到request对象中，以便在视图函数中使用
        request.user_id = int(payload['sub'])
        request.user_phone = payload['phone']
        
        return f(*args, **kwargs)
    
    return decorated
