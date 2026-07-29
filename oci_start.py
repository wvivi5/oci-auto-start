"""
cron: */3 * * * *
new Env('甲骨文新加坡 AMD 抢开机(全通道单行配置版)');
"""

import os
import sys
import time
import base64
import requests
import hashlib
from datetime import datetime
from urllib.parse import urlparse

# ==================== 核心配置区域 ====================
USER_OCID = "ocid1.user.oc1..aaaa..."
TENANCY_OCID = "ocid1.tenancy.oc1..aaaaaaaaunpldtsmaphowagoyjzq5lkulnineh56zhlqbjiyijxqdi5hze3a"
FINGERPRINT = "xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
INSTANCE_ID = "ocid1.instance.oc1.ap-singapore-1.anzwsljrprlfhnacf5fkzq4gd3du72kjsg7uietdwwhpbf3mnaj5d3kyumja"
REGION = "ap-singapore-1"
KEY_FILE_PATH = "/ql/data/config/oci_api_key.pem"

# ----------------- 通知通道单行配置区 (优先读取环境变量，为空取默认值) -----------------
# 1. 企业微信应用 (格式: 企业ID,Secret,成员ID,应用ID)
QYWX_AM = os.getenv("QYWX_AM", "wwxxxxxxxxxxxxxx,SECRET_XXXXXXXXXX,@all,1000002")

# 2. 企业微信机器人 Webhook KEY
QYWX_KEY = os.getenv("QYWX_KEY", "")

# 3. Server酱 SendKey
PUSH_KEY = os.getenv("PUSH_KEY", "")

# 4. Pushplus Token
PUSH_PLUS_TOKEN = os.getenv("PUSH_PLUS_TOKEN", "")

# 5. Telegram 机器人 (格式: Token,Chat_ID)
TG_BOT = os.getenv("TG_BOT", "")
# ====================================================

try:
    from Crypto.PublicKey import RSA
    from Crypto.Signature import pkcs1_15
    from Crypto.Hash import SHA256
except ImportError:
    print("❌ 缺失依赖库 pycryptodome，请在青龙【依赖管理 -> Python3】添加依赖: pycryptodome")

# ----------------- 5 大全通道原生推送逻辑 -----------------
def send_all_notifications(title, content):
    """同时向已配置的所有通道发送通知"""
    pushed = False

    # 1. 企业微信应用 (解析单行 QYWX_AM 配置，发送纯文本，无 media_id 报错)
    if QYWX_AM and "," in QYWX_AM:
        try:
            parts = [p.strip() for p in QYWX_AM.split(",")]
            if len(parts) >= 4:
                corpid, secret, touser, agentid = parts[0], parts[1], parts[2], parts[3]
                token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corpid}&corpsecret={secret}"
                token_res = requests.get(token_url, timeout=10).json()
                access_token = token_res.get("access_token")
                if access_token:
                    msg_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
                    payload = {
                        "touser": touser,
                        "msgtype": "text",
                        "agentid": agentid,
                        "text": {"content": f"{title}\n\n{content}"},
                        "safe": 0
                    }
                    res = requests.post(msg_url, json=payload, timeout=10).json()
                    if res.get("errcode") == 0:
                        print("🎉 【企业微信应用】推送成功！")
                        pushed = True
                    else:
                        print(f"❌ 【企业微信应用】推送失败: {res}")
        except Exception as e:
            print(f"❌ 【企业微信应用】推送异常: {e}")

    # 2. 企业微信机器人 (Webhook)
    if QYWX_KEY:
        try:
            bot_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}"
            payload = {
                "msgtype": "text",
                "text": {"content": f"{title}\n\n{content}"}
            }
            res = requests.post(bot_url, json=payload, timeout=10).json()
            if res.get("errcode") == 0:
                print("🎉 【企业微信机器人】推送成功！")
                pushed = True
            else:
                print(f"❌ 【企业微信机器人】推送失败: {res}")
        except Exception as e:
            print(f"❌ 【企业微信机器人】推送异常: {e}")

    # 3. Server 酱
    if PUSH_KEY:
        try:
            sct_url = f"https://sctapi.ftqq.com/{PUSH_KEY}.send"
            payload = {"title": title, "desp": content}
            res = requests.post(sct_url, data=payload, timeout=10).json()
            if res.get("code") == 0 or res.get("errno") == 0:
                print("🎉 【Server酱】推送成功！")
                pushed = True
            else:
                print(f"❌ 【Server酱】推送失败: {res}")
        except Exception as e:
            print(f"❌ 【Server酱】推送异常: {e}")

    # 4. Pushplus (推送加)
    if PUSH_PLUS_TOKEN:
        try:
            pp_url = "http://www.pushplus.plus/send"
            payload = {"token": PUSH_PLUS_TOKEN, "title": title, "content": content}
            res = requests.post(pp_url, json=payload, timeout=10).json()
            if res.get("code") == 200:
                print("🎉 【Pushplus】推送成功！")
                pushed = True
            else:
                print(f"❌ 【Pushplus】推送失败: {res}")
        except Exception as e:
            print(f"❌ 【Pushplus】推送异常: {e}")

    # 5. Telegram 机器人 (格式: Token,Chat_ID)
    if TG_BOT and "," in TG_BOT:
        try:
            tg_token, tg_chat_id = TG_BOT.split(",")[0].strip(), TG_BOT.split(",")[1].strip()
            tg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            payload = {"chat_id": tg_chat_id, "text": f"{title}\n\n{content}"}
            res = requests.post(tg_url, json=payload, timeout=10).json()
            if res.get("ok"):
                print("🎉 【Telegram】推送成功！")
                pushed = True
            else:
                print(f"❌ 【Telegram】推送失败: {res}")
        except Exception as e:
            print(f"❌ 【Telegram】推送异常: {e}")

    if not pushed:
        print("⚠️ 未匹配到任何有效的推送参数，仅在控制台打印日志。")

def sign_string(message, key_path):
    try:
        with open(key_path, "r", encoding="utf-8") as f:
            key_data = f.read()
            
        private_key = RSA.import_key(key_data)
        h = SHA256.new(message.encode('utf-8'))
        signature = pkcs1_15.new(private_key).sign(h)
        return base64.b64encode(signature).decode('utf-8')
    except Exception as e:
        print(f"❌ 读取私钥或签名失败: {e}")
        return None

def sign_request(method, url, key_path, body=""):
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path
    if parsed.query:
        path += "?" + parsed.query
        
    date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    method_upper = method.upper()
    
    headers_to_sign = {
        "(request-target)": f"{method.lower()} {path}",
        "date": date_str,
        "host": host
    }
    
    headers_out = {
        "date": date_str,
        "host": host
    }

    if method_upper in ["POST", "PUT"]:
        body_bytes = body.encode('utf-8') if isinstance(body, str) else body
        content_length = str(len(body_bytes))
        sha256_hash = hashlib.sha256(body_bytes).digest()
        content_sha256 = base64.b64encode(sha256_hash).decode('utf-8')
        
        headers_to_sign["content-type"] = "application/json"
        headers_to_sign["content-length"] = content_length
        headers_to_sign["x-content-sha256"] = content_sha256
        
        headers_out["content-type"] = "application/json"
        headers_out["content-length"] = content_length
        headers_out["x-content-sha256"] = content_sha256

    signed_headers_list = list(headers_to_sign.keys())
    signed_headers_str = " ".join(signed_headers_list)

    signing_string = "\n".join([f"{k}: {v}" for k, v in headers_to_sign.items()])
    
    b64_sig = sign_string(signing_string, key_path)
    if not b64_sig:
        return None
        
    key_id = f"{TENANCY_OCID}/{USER_OCID}/{FINGERPRINT}"
    auth_header = f'Signature version="1",keyId="{key_id}",algorithm="rsa-sha256",headers="{signed_headers_str}",signature="{b64_sig}"'
    
    headers_out["authorization"] = auth_header
    return headers_out

def main():
    if not os.path.exists(KEY_FILE_PATH):
        print(f"❌ 找不到私钥文件: {KEY_FILE_PATH}")
        return

    base_url = f"https://iaas.{REGION}.oraclecloud.com/20160918/instances/{INSTANCE_ID}"
    headers = sign_request("GET", base_url, KEY_FILE_PATH)
    if not headers:
        return

    res = requests.get(base_url, headers=headers)
    if res.status_code != 200:
        print(f"❌ 获取实例状态失败 [{res.status_code}]: {res.text}")
        return

    status = res.json().get("lifecycleState")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 当前实例状态: {status}")

    if status == "RUNNING":
        msg = "🎉 恭喜！你的 Oracle Cloud 新加坡 AMD 实例已经成功抢到资源并开机！"
        print(msg)
        # 单行配置解析，直连企微应用纯文本 API
        send_all_notifications("甲骨文开机成功提醒", msg)
        print("💡 请手动在青龙面板中禁用此任务。")
    elif status == "STOPPED":
        print("🚀 正在发送启动 (START) 指令...")
        action_url = f"{base_url}?action=START"
        body_data = ""
        action_headers = sign_request("POST", action_url, KEY_FILE_PATH, body=body_data)
        if not action_headers:
            return
        start_res = requests.post(action_url, headers=action_headers, data=body_data)
        if start_res.status_code in [200, 202]:
            print("✅ 启动请求已成功提交！等待下一次 Cron 轮询检查。")
        else:
            err_json = start_res.json()
            err_code = err_json.get("code", "")
            if "Out of host capacity" in str(err_json) or "OutOfCapacity" in err_code:
                print("❌ 节点资源依然不足 (Out of host capacity)...")
            elif start_res.status_code == 429:
                print("⚠️ 触发 API 频次限制 (429)...")
            else:
                print(f"⚠️ 请求失败 [{start_res.status_code}]: {err_json.get('message')}")
    else:
        print(f"⏳ 实例处于 {status} 状态，跳过执行。")

if __name__ == "__main__":
    main()
