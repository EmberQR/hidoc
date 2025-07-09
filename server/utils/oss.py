import oss2
import os

access_key_id = 'LTAI5tHP6zqRhFLCkbCcZ2t1'
access_key_secret = 'VdZs0WNoUvi1zrIpvCnQ4Sk2kJMVa7'
bucket_name = 'emberauthor'
custom_endpoint = 'https://cdn.ember.ac.cn'

# 创建认证对象  
auth = oss2.Auth(access_key_id, access_key_secret)

# 创建 Bucket 对象
bucket = oss2.Bucket(auth, custom_endpoint, bucket_name, is_cname=True)

def upload_to_oss(file_storage, object_name):
    """
    将文件上传到阿里云OSS。

    :param file_storage: Flask 请求中的 FileStorage 对象或文件流
    :param object_name: 在 OSS 上存储的对象名称 (e.g., 'images/my-photo.jpg')
    :return: 上传成功则返回文件URL，否则返回None
    """
    try:
        # 使用 put_object 方法上传文件流
        result = bucket.put_object(object_name, file_storage)
        
        # 如果HTTP状态码是200，说明上传成功
        if result.status == 200:
            # 构建文件的公开访问URL
            file_url = f"{custom_endpoint}/{object_name}"
            return file_url
        else:
            print(f"OSS upload failed with status: {result.status}")
            return None
    except oss2.exceptions.OssError as e:
        print(f"Error uploading to OSS: {e}")
        return None
