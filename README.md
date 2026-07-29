# Oracle Cloud (OCI) 自动抢开机脚本 (青龙面板专用)

本脚本用于 **Oracle Cloud Infrastructure (OCI)** 关机/抢占实例（如新加坡 AMD/ARM 实例）的自动轮询开机。使用 Python 原生 REST API + `pycryptodome` 进行标准 RSA-SHA256 签名，无需安装巨大的 Oracle 官方 SDK。

## 🌟 特点
1. **轻量极速**：不需要安装官方 `oci` 复杂 SDK，依靠轻量签名库即可直接与 OCI REST API 通信。
2. **青龙面板原生集成**：自带 `cron` 和 `Env` 声明，青龙拉取后可自动识别定时规则与任务名称。
3. **安全提醒**：开机成功后通过青龙通知系统（`notify`）发送推送提醒，方便及时禁用或接管。

---

## 🛠️ 环境准备与依赖

### 1. 青龙面板依赖
在青龙面板的 **【依赖管理 -> Python3】** 中添加以下依赖：
- `pycryptodome`
- `requests`

---

## 🔐 申请 OCI API Key

1. 登录 Oracle Cloud 控制台。
2. 点击右上角个人头像 -> **Profile / 用户设置** -> **API Keys (API 密钥)**。
3. 点击 **Add API Key (添加 API 密钥)**，选择 **Generate API Key Pair** 并下载私钥文件（例如 `oci_api_key.pem`）。
4. 将该 `.pem` 私钥文件上传或保存至青龙服务器指定路径（默认路径为：`/ql/data/config/oci_api_key.pem`）。
5. 复制控制台生成的配置信息，获取以下关键参数：
   - `user` (USER_OCID)
   - `tenancy` (TENANCY_OCID)
   - `fingerprint` (FINGERPRINT)
   - `region` (REGION)

---

## ⚙️ 脚本配置说明

修改 `oci_start.py` 中的核心配置区域：

```python
# ==================== 核心配置区域 ====================
USER_OCID = "ocid1.user.oc1..aaaa..."
TENANCY_OCID = "ocid1.tenancy.oc1..aaaaaaaa..."
FINGERPRINT = "xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
INSTANCE_ID = "ocid1.instance.oc1.ap-singapore-1.aaaa..." # 待开机的实例 OCID
REGION = "ap-singapore-1"                                # 对应区域
KEY_FILE_PATH = "/ql/data/config/oci_api_key.pem"      # 私钥文件存放路径
# ====================================================
```

### 获取实例 OCID (`INSTANCE_ID`)：
在 Oracle Cloud 控制台中进入 **Compute -> Instances**，点击对应的实例名称，在实例详情页面复制 **OCID**。

---

## 🚀 使用方法

### 方式一：青龙面板订阅/定时任务（推荐）
1. 在青龙面板新建脚本，将 `oci_start.py` 内容粘贴进去；或在订阅管理中配置该 GitHub 仓库。
2. 确认核心参数及私钥路径无误后启用任务。
3. 默认 Cron 表达式为 `*/3 * * * *`（每 3 分钟运行一次）。

### 方式二：命令行手动运行
```bash
python3 oci_start.py
```

---

## 📝 运行逻辑与通知

- **STOPPED（关机/抢占态）**：尝试发送 `START` 启动指令。如果节点容量不足（`Out of host capacity`），会记录日志并等待下一次轮询。
- **RUNNING（运行态）**：触发开机成功通知，提示用户手动禁用任务。
- **其他状态（如 PROVISIONING / STARTING）**：跳过本次请求，等待状态稳定。

---

## ⚠️ 免责声明与注意事项

- 请勿将包含私钥或真实 OCID 信息的代码直接提交至公开仓库。
- 请根据实际需求合理设置 Cron 轮询频率，避免触发 OCI API 的 429 频次限制。
