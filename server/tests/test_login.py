import json
import bcrypt
from models import Doctor

def test_login_success(client, db):
    """
    测试成功登录的情况
    """
    # 1. 准备：在数据库中创建一个测试医生
    password = 'password123'
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    test_doctor = Doctor(
        phone='12345678901',
        name='测试医生',
        gender='男',
        password=hashed_password.decode('utf-8')
    )
    db.session.add(test_doctor)
    db.session.commit()

    # 2. 执行：发送登录请求
    response = client.post(
        '/api/login',
        data=json.dumps({'phone': '12345678901', 'password': password}),
        content_type='application/json'
    )
    data = json.loads(response.data)

    # 3. 断言：验证返回结果是否正确
    assert response.status_code == 200
    assert data['code'] == 200
    assert data['message'] == '登录成功'
    assert data['data']['phone'] == '12345678901'
    assert 'password' not in data['data']  # 确认密码没有被返回
    # 检查是否设置了cookie
    assert 'token' in response.headers.get('Set-Cookie')

def test_login_wrong_password(client, db):
    """
    测试密码错误的情况
    """
    # 1. 准备：创建一个测试医生
    password = 'password123'
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    test_doctor = Doctor(
        phone='12345678902',
        name='测试医生2',
        gender='女',
        password=hashed_password.decode('utf-8')
    )
    db.session.add(test_doctor)
    db.session.commit()

    # 2. 执行：使用错误的密码发送登录请求
    response = client.post(
        '/api/login',
        data=json.dumps({'phone': '12345678902', 'password': 'wrongpassword'}),
        content_type='application/json'
    )
    data = json.loads(response.data)

    # 3. 断言：验证返回结果
    assert response.status_code == 401
    assert data['code'] == 401
    assert data['message'] == '手机号或密码错误'

def test_login_user_not_exist(client):
    """
    测试用户不存在的情况
    """
    # 1. 准备：数据库为空
    # 2. 执行：使用一个不存在的手机号登录
    response = client.post(
        '/api/login',
        data=json.dumps({'phone': '11111111111', 'password': 'anypassword'}),
        content_type='application/json'
    )
    data = json.loads(response.data)

    # 3. 断言：验证返回结果
    assert response.status_code == 401
    assert data['code'] == 401
    assert data['message'] == '手机号或密码错误'

def test_login_missing_fields(client):
    """
    测试缺少请求字段的情况
    """
    # 1. 测试缺少密码
    response = client.post(
        '/api/login',
        data=json.dumps({'phone': '12345678901'}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert response.status_code == 400
    assert data['message'] == '手机号和密码不能为空'

    # 2. 测试缺少手机号
    response = client.post(
        '/api/login',
        data=json.dumps({'password': 'password123'}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert response.status_code == 400
    assert data['message'] == '手机号和密码不能为空'
    
    # 3. 测试请求体为空
    response = client.post(
        '/api/login',
        data=json.dumps({}),
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert response.status_code == 400
    assert data['message'] == '请求体不能为空'

def test_logout(client):
    """
    测试登出接口
    """
    # 执行登出请求
    response = client.post('/api/logout')
    data = json.loads(response.data)

    # 断言结果
    assert response.status_code == 200
    assert data['code'] == 200
    assert data['message'] == '登出成功'
    # 检查cookie是否被清除
    cookie_header = response.headers.get('Set-Cookie')
    assert cookie_header is not None
    assert 'token=;' in cookie_header
    assert 'Expires=Thu, 01 Jan 1970 00:00:00 GMT' in cookie_header
