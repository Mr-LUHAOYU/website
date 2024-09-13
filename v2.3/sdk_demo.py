import os

from alibabacloud_ecs20140526 import client as ecs_client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_20140526_models


def init_ecs_client():
    """
    初始化ECS客户端。

    该函数不接受任何参数。

    返回:
        ecs_client.Client: 一个初始化好的ECS客户端对象，可用于进一步的ECS操作。
    """
    # 创建ECS配置对象，并从环境变量中读取访问密钥
    ecs_config = open_api_models.Config()
    ecs_config.access_key_id = os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID']
    ecs_config.access_key_secret = os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
    # 设置endpoint
    ecs_config.endpoint = 'ecs-cn-hangzhou.aliyuncs.com'

    # 使用配置初始化ECS客户端并返回
    return ecs_client.Client(ecs_config)


if __name__ == '__main__':
    # 初始化ECS客户端
    client = init_ecs_client()
    # 创建DescribeRegionsRequest请求对象
    describeRegions_request = ecs_20140526_models.DescribeRegionsRequest()
    # 发送describeRegions请求，获取地域信息
    response = client.describe_regions(describeRegions_request)
    print(response.body)