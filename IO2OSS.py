# -*- coding: utf-8 -*-
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
import os

os.environ['OSS_ACCESS_KEY_ID'] = 'LTAI5tMXuC9JJRdm4Trt2uLR'
os.environ['OSS_ACCESS_KEY_SECRET'] = 'jNg1hQ8oClcopvKVrxCMrRaD30lzN0'

auth = oss2.ProviderAuth(EnvironmentVariableCredentialsProvider())
bucket = oss2.Bucket(auth, 'https://oss-cn-hangzhou.aliyuncs.com', 'yourBucketName')


def download_from_oss(yourObjectName):
    return bucket.get_object(yourObjectName)


def upload_to_oss(yourObjectName, yourLocalFile):
    bucket.put_object_from_file(yourObjectName, yourLocalFile)
    os.remove(yourLocalFile)


def delete_from_oss(yourObjectName):
    bucket.delete_object(yourObjectName)
