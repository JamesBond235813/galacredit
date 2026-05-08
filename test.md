## `backend` 端新增功能。
1. 记录 `user_events` 用户事件时，要求传入IP地址，此时直接保存不解析IP地址。
2. 解析IP地址：
   1. 解析IP地址的函数，写到`backend/app/services/location.py` 文件里。 
   2. 保存`user_events`信息后， 要求异步调用解析IP地址的接口， 将解析后，IP对应的地址信息填充到对应的user_events信息。 
   3. 编写兜底的定时任务（每小时运行1次），扫描前未解析IP的记录（范围为 10分钟前，且未解析过IP的数据）
   4. 解析IP的API接口
      - 接口地址， TOKEN要求可通过 .env系列文件进行配置。
      - 接口使用GET 方式调用，要求通过httpx 库`AsyncClient`进行请求。curl的请求样例如下：
        - curl 命令： ` curl "https://api.ip138.com/ipdata/?ip=36.21.252.191&datatype=json" -H "token:${IP_TOKEN}"`
        - 响应信息: ` {"ret":"ok","ip":"36.21.252.191","data":["中国","浙江","","","电信","321000","0579","移动网络"]}`
        - 上述响应信息 `data` 字段数组内容依次为: `ip_country`, `ip_province`, `ip_city`, `ip_district`,运营商,邮编,区号,网络类型
        - `user_events`表`ip_detail`字段，填`data`字段的json（字符串）信息， 如上述响应信息中的 `["中国","浙江","","","电信","321000","0579","移动网络"]`
        - 若 响应 `ret` 不为 `ok` 或 HTTP请求返回的状态码非200时，视为异常，不保存IP解析内容  
        - IP地址解析已成功后，要求做内存缓存，有效期8小时。 
        - 请求IP地址解析的API时， 要求目标IP为粒度加锁， 防止相同IP并行请求三方API以造成成本浪费。