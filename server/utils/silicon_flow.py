import os
from openai import OpenAI

# 为了安全，推荐您将API密钥设置为环境变量。
# 您可以从 https://cloud.siliconflow.cn/account/ak 获取您的API密钥。
# 建议使用 python-dotenv 库来管理环境变量，在项目根目录创建 .env 文件并添加：
# SILICONFLOW_API_KEY="your-api-key-here"
API_KEY = "sk-rdzwrvxjqjvrnjvsdvjhoygzmczumhjebazfbmrrhskpskit"

class SiliconFlowClient:
    """
    一个用于与硅基流动 AI API 交互的客户端。
    该类作为一个中间件，以简化在应用程序其他部分中的API调用。
    """
    def __init__(self, api_key=API_KEY):
        if not api_key:
            raise ValueError("未找到硅基流动API密钥。请设置 SILICONFLOW_API_KEY 环境变量或将其传递给客户端。")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )

    def chat(self, messages, model="Qwen/Qwen3-235B-A22B", json_output=True):
        """
        向硅基流动API发送聊天补全请求。

        :param messages: 到目前为止构成对话的消息列表。
        :param model: 用于补全的模型。
        :param json_output: 如果为 True，则请求JSON格式的输出。
        :return: 助手的响应内容字符串，如果出错则为 None。
        """
        request_params = {
            "model": model,
            "messages": messages
        }
        if json_output:
            request_params["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**request_params)
            return response.choices[0].message.content
        except Exception as e:
            # 在实际应用中，您会希望使用一个合适的日志记录器。
            print(f"调用硅基流动API时发生错误: {e}")
            return None

# 一个可以在整个应用程序中导入和使用的全局实例。
#
# 在其他文件中使用示例:
#
# from server.utils.silicon_flow import silicon_flow_client
#
# messages = [
#     {"role": "system", "content": "你是一个乐于助人的助手，旨在输出JSON。"},
#     {"role": "user", "content": "? 2020年世界奥运会乒乓球男子和女子单打冠军分别是谁? "
#      "请以{\"男子冠军\": ..., \"女子冠军\": ...}的格式回应。"}
# ]
#
# response_content = silicon_flow_client.chat(messages, json_output=True)
# if response_content:
#     print(response_content)
#
silicon_flow_client = SiliconFlowClient()
