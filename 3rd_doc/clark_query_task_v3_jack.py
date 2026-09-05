import asyncio
import os

import httpx

url = "https://www.risktable.xyz/xtable/gh_query_data_v3"

payload = {
    "customer_id": os.environ.get("GHANA_RISK_CUSTOMER_ID", ""),
    "customer_secret_key": os.environ.get("GHANA_RISK_CUSTOMER_SECRET_KEY", ""),
    "task_number": os.environ.get("GHANA_RISK_TASK_NUMBER", "")
}

headers = {
    "Content-Type": "application/json"
}

async def main():
    """查询示例风控任务，凭证和任务号仅从环境变量读取。

    :return: None
    """
    if not payload["customer_id"] or not payload["customer_secret_key"] or not payload["task_number"]:
        raise RuntimeError("请设置 GHANA_RISK_CUSTOMER_ID、GHANA_RISK_CUSTOMER_SECRET_KEY 和 GHANA_RISK_TASK_NUMBER")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload, headers=headers)
    print(response.status_code)
    print(response.json())


if __name__ == "__main__":
    asyncio.run(main())

"""
{'code': 200, 'msg': 'success', 
'data': {'task_score_v1': '395.0', 'task_score_v2': '401.7', 'task_number': 'Gh924cc08b9a9b4f49a125ba1ff88bbf9c', 'message': 'task is calculated', 'task_status': '2'}}
"""
