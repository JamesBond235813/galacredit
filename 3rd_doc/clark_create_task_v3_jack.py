import asyncio
import os
import random

import httpx
url = "https://www.risktable.xyz/xtable/gh_submit_data_v3"

random_str = ''.join(random.sample('abcdefghijklmnopqrstuvwxyz', 8))

payload = {
    # 给我随机四个字符组成的字符串
    "request_id": f"req_0805_aaa_{random_str}",
    "customer_id": os.environ.get("GHANA_RISK_CUSTOMER_ID", ""),
    "customer_secret_key": os.environ.get("GHANA_RISK_CUSTOMER_SECRET_KEY", ""),

    "callback_url": os.environ.get("GHANA_RISK_CALLBACK_URL", "https://your.domain/callback"),
    "risk_data": {
        "applyId": f"ORDER_20250220_002{random_str}",
        "applyTime": "2025-02-20 11:24:05",
        "smsList": [
            {
                "address": "5595438734",
                "body": "verification code 5286",
                "type": 1,
                "time": "2025-02-20 10:47:00",
                "read": 0
            }
        ],
        "appList": [
            {
                "appName": "Clonar teléfono",
                "packageName": "com.coloros.backuprestore",
                "firstInstallTime": "2010-01-01 00:00:25",
                "lastUpdateTime": "2010-01-01 00:00:25",
            },
            {
                "appName": "Tethering",
                "packageName": "com.google.android.networkstack.tethering",
                "firstInstallTime": "2025-01-18 02:54:01",
                "lastUpdateTime": "2025-01-18 02:54:01",
            }
        ]
    }
}

headers = {
    "Content-Type": "application/json"
}

async def main():
    """提交示例风控任务，凭证仅从环境变量读取。

    :return: None
    """
    if not payload["customer_id"] or not payload["customer_secret_key"]:
        raise RuntimeError("请先设置 GHANA_RISK_CUSTOMER_ID 和 GHANA_RISK_CUSTOMER_SECRET_KEY")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload, headers=headers)
    print(response.text)
    print(response.status_code)


if __name__ == "__main__":
    asyncio.run(main())

"""
{"code": 200, "msg": "success",
 "data": {"status": "success", "task_number": "Gh924cc08b9a9b4f49a125ba1ff88bbf9c",
          "message": "Data received successfully. Analysis results will be sent to the callback URL."}}
"""
