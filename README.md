# 词达人全自动刷题

一键自动完成词达人所有班级任务。支持全题型（拼写/填空/排序），正确率 90%+。

## ⚠️ 免责声明

本项目仅供学习研究，使用者自行承担风险。请合理使用，不要高频大批量刷题。

---

## 快速开始

### 1. 抓取 UserToken（只需做一次，Token 过期后重抓）

1. 下载 [Fiddler Classic](https://www.telerik.com/download/fiddler)
2. 打开 Fiddler → **Tools → Options → HTTPS**，勾选：
   - ✅ Capture HTTPS CONNECTs
   - ✅ Decrypt HTTPS traffic
   - 证书弹窗全部 Yes
3. **PC 微信**打开词达人 → 点进任意练习
4. Fiddler 左侧找到 `app.vocabgo.com` → 展开（点 ▶）
5. 点开任意子请求 → **Inspectors → Headers**
6. 复制 `UserToken:` 后面那串（32位字符）

### 2. 填写配置

编辑 `config.json`：
```json
{
  "user_token": "这里粘贴你的Token",
  "settings": {
    "delay_per_question": 2,
    "correct_rate_target": 100,
    "max_questions_per_run": 500
  }
}
```

### 3. 运行

```bash
python3 cidaren.py --check   # 验证 token 有效
python3 cidaren.py --auto    # 全自动刷题
```

---

## 命令说明

| 命令 | 作用 |
|------|------|
| `python3 cidaren.py` | 交互模式，手动选任务 |
| `python3 cidaren.py --auto` | 全自动，刷所有待做任务 |
| `python3 cidaren.py --check` | 检查 token 是否有效 |
| `python3 cidaren.py --task-id ID` | 只刷指定任务 |

## 注意事项

- ⚠️ 运行期间**不要用手机打开词达人**
- Token 过期（几小时到一天）后需重新抓取
- 遇到"权限不足"的任务自动跳过
- 已完成低分任务会自动重置重刷
