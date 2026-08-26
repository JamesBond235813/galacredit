# risktable Ghana API 接口文档

---

## 一、创建风控任务

**URL：** `POST https://www.risktable.xyz/xtable/gh_submit_data_v3`

**Content-Type：** `application/json`

---

### 请求参数

| 字段名                 | 类型           | 是否必填 | 字段含义                     | 示例                               |
|---------------------|--------------|------|--------------------------|----------------------------------|
| customer_id         | String       | 是    | 商户 ID，由平台分配              | `"merchant_001"`                 |
| request_id          | String       | 是    | 商户侧唯一请求号，全局唯一，重复提交会报错    | `"req_20250220_001"`             |
| customer_secret_key | String       | 是    | 商户密钥，由平台分配               | `"your_secret_key"`              |
| callback_url        | String/Array | 是    | 结果回调地址，支持字符串或字符串数组       | `"https://your.domain/callback"` |
| risk_data           | Object       | 是    | 风控数据，见下方「risk_data 字段说明」 | -                                |

---

### risk_data 字段说明

| 字段名       | 类型     | 是否必填 | 字段含义                                                   | 示例 / 备注                 |
|-----------|--------|------|--------------------------------------------------------|-------------------------|
| applyId   | String | 是    | 订单号，全局唯一                                               | `"ORDER_20250220_001"`  |
| applyTime | String | 是    | 申请时间，当地时间，格式 `yyyy-MM-dd HH:mm:ss`                     | `"2025-02-20 11:24:05"` |
| smsList   | Array  | 是    | 设备短信列表；key 建议始终传入，列表为空时传 `[]`，字段见下方「smsList 元素字段说明」    | -                       |
| appList   | Array  | 建议传  | 设备 APP 列表；key 建议始终传入，列表为空时传 `[]`，字段见下方「appList 元素字段说明」 | -                       |

---

### smsList 元素字段说明

| 字段名     | 类型     | 是否必填 | 字段含义                             | 示例 / 备注                |
|---------|--------|------|--------------------------------------|----------------------------|
| address | String | 是    | 短信对方号码                         | `"5595438734"`             |
| body    | String | 是    | 短信内容                             | `"verification code 5286"` |
| type    | int    | 是    | 短信类型：1 收到，2 发出             | `1`                        |
| time    | String | 是    | 短信时间，格式 `yyyy-MM-dd HH:mm:ss` | `"2025-02-20 16:47:00"`    |
| read    | int    | 是    | 是否已读：0 未读，1 已读             | `0`                        |

---

### appList 元素字段说明

| 字段名              | 类型     | 是否必填 | 字段含义                                 | 示例 / 备注                       |
|------------------|--------|------|--------------------------------------|-------------------------------|
| appName          | String | 是    | App 名称                               | `"Clonar teléfono"`           |
| packageName      | String | 是    | 安装包名称                                | `"com.coloros.backuprestore"` |
| firstInstallTime | String | 是    | 初次安装时间，当地时间，格式 `yyyy-MM-dd HH:mm:ss` | `"2010-01-01 00:00:25"`       |
| lastUpdateTime   | String | 是    | 最近更新时间，当地时间，格式 `yyyy-MM-dd HH:mm:ss` | `"2010-01-01 00:00:25"`       |
---

### 请求示例

```json
{
  "customer_id": "merchant_001",
  "request_id": "req_20250220_0010",
  "customer_secret_key": "your_secret_key",
  "callback_url": "https://your.domain/callback",
  "risk_data": {
    "applyId": "ORDER_20250220_00100",
    "applyTime": "2025-02-20 11:24:05",
    "smsList": [
      {
        "address": "5595438734",
        "body": "verification code 5286",
        "type": 1,
        "time": "2025-02-20 16:47:00",
        "read": 0
      }
    ],
    "appList": [
      {
        "appName": "Clonar teléfono",
        "packageName": "com.coloros.backuprestore",
        "firstInstallTime": "2010-01-01 00:00:25",
        "lastUpdateTime": "2010-01-01 00:00:25"
      }
    ]
  }
}
```

---

### 响应参数

| 字段名         | 类型     | 字段含义                    |
|-------------|--------|-------------------------|
| status      | String | 固定返回 `"success"`        |
| task_number | String | 平台任务号，用于查询接口和接收回调时的任务标识 |
| message     | String | 描述信息                    |

### 响应示例

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "status": "success",
    "task_number": "Gh20250220AbCdEf",
    "message": "Data received successfully. Analysis results will be sent to the callback URL."
  }
}
```

---

### 错误码说明

| code | 含义                                             |
|------|------------------------------------------------|
| 200  | 成功                                             |
| 403  | 参数缺失 / 商户不存在 / IP 不在白名单 / 密钥错误 / request_id 重复 |

---

---

## 二、查询风控结果

**URL：** `POST https://www.risktable.xyz/xtable/gh_query_data_v3`

**Content-Type：** `application/json`

> 说明：风控计算需要一定时间，建议提交任务后 **间隔 5 秒** 开始轮询，推荐优先使用回调方式获取结果。

---

### 请求参数

| 字段名                 | 类型     | 是否必填 | 字段含义                    | 示例                   |
|---------------------|--------|------|-------------------------|----------------------|
| customer_id         | String | 是    | 商户 ID，由平台分配             | `"merchant_001"`     |
| customer_secret_key | String | 是    | 商户密钥，由平台分配              | `"your_secret_key"`  |
| task_number         | String | 是    | 创建任务接口返回的 `task_number` | `"Gh20250220AbCdEf"` |

---

### 请求示例

```json
{
  "customer_id": "merchant_001",
  "customer_secret_key": "your_secret_key",
  "task_number": "Gh20250220AbCdEf"
}
```

---

### 响应参数

**task_status = 0（等待计算）**

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "task_number": "Gh20250220AbCdEf",
    "message": "task is waiting calculate",
    "task_status": "0"
  }
}
```

**task_status = 1（计算中）**

```json
{
    "code": 200,
    "msg": "success",
  "data": {
    "task_number": "Gh20250220AbCdEf",
    "message": "task is calculating",
    "task_status": "1"
  }
}
```

**task_status = 2（计算完成）**

```json
{
    "code": 200,
    "msg": "success",
  "data": {
    "task_score": "812.5",
    "task_number": "Gh20250220AbCdEf",
    "message": "task is calculated",
    "task_status": "2"
  }
}
```

---

### task_status 枚举说明

| task_status | 含义               |
|-------------|--------------------|
| 0           | 等待计算           |
| 1           | 计算中             |
| 2           | 计算完成，可取分数 |
| 3           | 计算错误           |

### 分数字段说明

| 字段名     | 类型     | 字段含义 |
|------------|--------|----------|
| task_score | String | 风控评分 |

---

### 错误码说明

| code | 含义                                    |
|------|---------------------------------------|
| 200  | 成功                                    |
| 403  | 参数缺失 / 商户不存在 / 密钥错误 / task_number 不存在 |

---

---

## 三、回调通知说明

> 风控计算完成后，平台会主动向创建任务时填写的 `callback_url` 发送 POST 请求，推送计算结果。**建议优先依赖回调，查询接口作为兜底。
**

---

### 回调请求说明

- 请求方式：`POST`
- Content-Type：`application/json`
- 回调目标：创建任务时传入的 `callback_url`
- 重试机制：回调失败最多重试 **5 次**，请确保回调地址可正常接收请求

---

### 回调请求体

| 字段名      | 类型     | 字段含义                                          |
|-------------|--------|---------------------------------------------------|
| task_score  | String | 风控评分                                          |
| task_number | String | 平台任务号，与创建任务时返回的 `task_number` 一致 |
| task_status | String | 固定为 `"2"`，表示计算完成                        |
| message     | String | 描述信息，固定为 `"task is calculated"`           |

### 回调请求体示例

```json
{
  "task_score": "812.5",
  "task_number": "Gh20250220AbCdEf",
  "task_status": "2",
  "message": "task is calculated"
}
```

---

### 回调响应要求

接收到回调后，请返回 HTTP 200，响应体格式不限，建议返回：

```json
{
  "code": 200
}
```

> ⚠️ 注意：若平台未收到 HTTP 200 响应，或请求超时（30秒），将视为回调失败并进行重试，最多重试 5 次。超过重试次数后不再推送，请及时通过
**查询接口**补拉结果。

---

## 四、接入流程说明

```
商户                          平台                        
  |                             |                         
  |--- 1. POST 创建风控任务 ---->|                         
  |<-- 返回 task_number --------|                         
  |                             |                         
  |--- 2. POST 查询结果(轮询) -->|  （可选，建议兜底使用）  
  |<-- 返回 task_status --------|                         
  |                             |                         
  |<-- 3. 回调推送结果 ----------|  （推荐，计算完成主动推）
  |--- 返回 200 --------------->|                         
```
