#!/usr/bin/env python3
"""
词达人全自动刷题 — 班级共享版
===============================
用法:
  python3 cidaren.py --auto       # 全自动批量刷题
  python3 cidaren.py --check      # 检查 token 是否有效
  python3 cidaren.py --task-id ID # 单独刷指定任务

首次使用:
  1. 用 Fiddler 抓取你的 UserToken (见 README.md)
  2. 填入 config.json 的 user_token 字段
  3. python3 cidaren.py --check   # 验证
  4. python3 cidaren.py --auto    # 开刷!
"""

import hashlib
import json
import os
import random
import re
import ssl
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
LOG_PATH = os.path.join(SCRIPT_DIR, "run.log")

SECRET = "ajfajfamsnfaflfasakljdlalkflak"
VERSION = "2.7.0.260528_01"
API_BASE = "https://app.vocabgo.com/student/api/Student"
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
)

# ============ 工具函数 ============

def md5(s):
    return hashlib.md5(s.encode()).hexdigest()

def now_ms():
    return round(time.time() * 1000)

def log(msg, end="\n"):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, end=end, flush=True)
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + end)
    except:
        pass

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

# ============ 签名 & HTTP ============

def sign_data(data_dict):
    keys = sorted(data_dict.keys())
    parts = []
    for k in keys:
        v = data_dict[k]
        if isinstance(v, (dict, list)):
            v = json.dumps(v, separators=(",", ":"), ensure_ascii=False)
        if v == "" or v is None:
            continue
        parts.append(f"{k}={v}")
    raw = "&".join(parts) + SECRET
    return md5(raw)

def add_common_params(data_dict):
    data_dict["app_type"] = 1
    data_dict["timestamp"] = now_ms()
    data_dict["version"] = VERSION
    data_dict["sign"] = sign_data(data_dict)
    return data_dict

def _headers(token, extra=None):
    h = {
        "Host": "app.vocabgo.com",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": DEFAULT_UA,
        "Origin": "https://app.vocabgo.com",
        "Referer": "https://app.vocabgo.com/",
        "Connection": "keep-alive",
        "ABC": "9c7c7340193fed50e3e6ccac0cbfb1df",
    }
    if token:
        h["UserToken"] = token
    if extra:
        h.update(extra)
    return h

# ============ JV 数据解码 ============

JV_TABLES = {
    "2_1254": [{"site":0,"num":3},{"site":1,"num":2},{"site":31,"num":1},{"site":41,"num":2},{"site":51,"num":1},{"site":87,"num":1},{"site":97,"num":1}],
    "2_10234": [{"site":0,"num":3},{"site":1,"num":4},{"site":39,"num":1},{"site":57,"num":2},{"site":188,"num":1},{"site":259,"num":1},{"site":316,"num":2}],
    "2_9214": [{"site":0,"num":3},{"site":1,"num":4},{"site":41,"num":2},{"site":57,"num":1},{"site":139,"num":2},{"site":272,"num":1},{"site":361,"num":2}],
    "2_9314": [{"site":0,"num":3},{"site":1,"num":4},{"site":31,"num":2},{"site":60,"num":1},{"site":142,"num":2},{"site":275,"num":1},{"site":364,"num":2}],
}

import base64 as _base64

def decode_response(j):
    jv = j.get("jv", "")
    data = j.get("data")
    if not data or not isinstance(data, str):
        return j
    if jv == "99":
        return j
    if jv == "1":
        data = data[32:]
        try:
            j["data"] = json.loads(_base64.b64decode(data).decode("utf-8"))
        except:
            pass
        return j
    if jv.startswith("2_"):
        table = JV_TABLES.get(jv, [])
        for entry in table:
            site, num = entry["site"], entry["num"]
            if site:
                data = data[:site] + data[site + num:]
            else:
                data = data[num:]
        try:
            j["data"] = json.loads(_base64.b64decode(data).decode("utf-8"))
        except:
            pass
        return j
    if jv == "4":
        try:
            j["data"] = json.loads(_base64.b64decode(data).decode("utf-8"))
        except:
            pass
        return j
    return j

# ============ API 请求 ============

def api_get(path, token, params=None):
    if params is None:
        params = {}
    add_common_params(params)
    qs = urllib.parse.urlencode(params)
    url = f"{API_BASE}/{path}?{qs}"
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers=_headers(token, {"Referer": "https://app.vocabgo.com/student/"}))
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            raw = resp.read().decode()
            j = json.loads(raw)
            j = decode_response(j)
            return resp.status, json.dumps(j, ensure_ascii=False)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='ignore')
    except Exception as e:
        return 0, str(e)

def api_post(path, token, data=None):
    if data is None:
        data = {}
    add_common_params(data)
    body = json.dumps(data, separators=(",", ":")).encode()
    url = f"{API_BASE}/{path}"
    ctx = ssl.create_default_context()
    headers = _headers(token, {"Content-Type": "application/json;charset=utf-8"})
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            raw = resp.read().decode()
            j = json.loads(raw)
            j = decode_response(j)
            return resp.status, json.dumps(j, ensure_ascii=False)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='ignore')
    except Exception as e:
        return 0, str(e)

# ============ Token 验证 ============

def check_token_valid(token):
    status, body = api_get("Main", token)
    if status == 200:
        try:
            j = json.loads(body)
            if j["code"] == 1:
                user = j["data"]["user_info"]
                name = user.get("student_name", user.get("nick_name", "未知"))
                cls = user.get("class_name", "")
                info = f"{name} ({cls})" if cls else name
                log(f"Token 有效 — {info}")
                return True, user
            else:
                log(f"Token 无效: code={j['code']} msg={j.get('msg','')}")
        except:
            pass
    return False, None

# ============ 任务获取 ============

def get_class_tasks(token):
    log("获取班级任务...")
    all_tasks = []
    for page in range(1, 10):
        status, body = api_get("ClassTask/List", token,
                               {"page_count": page, "page_size": 20})
        if status != 200:
            break
        try:
            j = json.loads(body)
            tasks = j["data"]["task_list"]
            all_tasks.extend(tasks)
            if len(tasks) < 20:
                break
        except:
            break

    active = [t for t in all_tasks
              if t["over_status"] != 3
              and (t.get("score", 0) != 100 and t.get("progress", 0) != 100)]
    log(f"  找到 {len(active)} 个待做任务")
    return active

def start_answer(token, task):
    params = {
        "task_id": task["task_id"],
        "task_type": task["task_type"],
        "release_id": task["release_id"],
    }
    status, body = api_get("ClassTask/StartAnswer", token, params)
    try:
        return json.loads(body)
    except:
        return {"code": -1}

# ============ 答题核心 ============

def verify_answer(token, answer_str, topic_code, task_type="ClassTask"):
    data = {"answer": answer_str, "topic_code": topic_code}
    status, body = api_post(f"ClassTask/VerifyAnswer", token, data)
    try:
        return json.loads(body)
    except:
        return {"code": -1}

def submit_answer(token, topic_code, time_spent, task_type="ClassTask"):
    data = {"topic_code": topic_code, "time_spent": time_spent}
    status, body = api_post(f"ClassTask/SubmitAnswerAndSave", token, data)
    try:
        return json.loads(body)
    except:
        return {"code": -1}

def skip_answer(token, topic_code, topic_mode, task_type="ClassTask"):
    max_t = {11:20,13:35,15:15,16:15,17:10,18:10,
             21:15,22:15,31:25,32:20,41:25,42:25,
             43:30,44:30,51:25,52:25,53:35,54:35,73:20}
    time_spent = max_t.get(topic_mode, 20) * 1000
    data = {"topic_code": topic_code, "time_spent": time_spent}
    status, body = api_post("ClassTask/SubmitAnswerAndSave", token, data)
    try:
        return json.loads(body)
    except:
        return {"code": -1}

def solve_question(token, stem_data, task_id, task_type, release_id, config):
    topic_code = stem_data["topic_code"]
    topic_mode = stem_data["topic_mode"]
    content = stem_data["stem"]["content"]

    log(f"  [mode={topic_mode}] {str(content)[:50]}", end="")

    settings = config.get("settings", {})
    min_t = settings.get("delay_per_question", 3)
    max_t = min_t + 2
    time.sleep(random.uniform(min_t * 0.5, max_t * 0.5))

    # mode 0: 学习卡片
    if topic_mode == 0:
        log(" skip(card)")
        submit_answer(token, topic_code, 0, task_type)
        return None

    # mode 73: 拼写题 (JSON数组格式)
    if topic_mode == 73:
        w_lens = stem_data.get("w_lens", [])
        blank_count = len(w_lens) if w_lens else content.count('{')
        if blank_count == 0:
            blank_count = 1

        blank_arr = json.dumps([""] * blank_count)
        rv = verify_answer(token, blank_arr, topic_code, task_type)
        rd = rv.get("data", {}) or {}

        if rv.get("code") != 1:
            log(" SKIP(api_fail)")
            submit_answer(token, topic_code, 20000, task_type)
            return None

        if rd.get("answer_result") == 1:
            log(" OK(blank)")
            submit_answer(token, rd.get("topic_code", topic_code), 10000, task_type)
            return rd

        word = rd.get("word", "")
        if word:
            word = urllib.parse.unquote(word)
            hints = re.findall(r'\{([^}]+)\}', content)
            if not hints:
                hints = [w[:2] for w in word.split()[-blank_count:]]

            all_words = word.split()
            answers = []
            for hint, wlen in zip(hints, w_lens if len(w_lens) == len(hints) else [len(h) for h in hints]):
                found = None
                for w in all_words:
                    cw = w.strip('.,;:!?()[]{}"')
                    if cw.lower().startswith(hint.lower()) and len(cw) == wlen:
                        found = cw; break
                if not found:
                    for w in all_words:
                        cw = w.strip('.,;:!?()[]{}"')
                        if cw.lower().startswith(hint.lower()):
                            found = cw; break
                if found:
                    answers.append(found)

            if len(answers) == len(hints):
                correct_arr = json.dumps(answers)
                rv2 = verify_answer(token, correct_arr, rd.get("topic_code", topic_code), task_type)
                rd2 = rv2.get("data", {}) or {}
                if rv2.get("code") == 1 and rd2.get("answer_result") == 1:
                    log(f" OK({','.join(answers)})")
                    submit_answer(token, rd2.get("topic_code", rd.get("topic_code", topic_code)), 10000, task_type)
                    return rd2

        log(" SKIP")
        submit_answer(token, topic_code, 20000, task_type)
        return None

    # 通用解法: 两次空白获取正确答案
    rv = verify_answer(token, "", topic_code, task_type)
    rd = rv.get("data", {}) or {}

    if rv.get("code") != 1:
        log(" SKIP(api_fail)")
        submit_answer(token, topic_code, 20000, task_type)
        return None

    if rd.get("answer_result") == 1:
        log(" OK(blank)")
        ts = random.randint(int(min_t * 1000), int(max_t * 1000))
        submit_answer(token, rd.get("topic_code", topic_code), ts, task_type)
        return rd

    new_tc = rd.get("topic_code", topic_code)
    rv2 = verify_answer(token, "", new_tc, task_type)
    rd2 = rv2.get("data", {}) or {}

    corrects = (rd2.get("answer_corrects") or
                rd2.get("answer") or
                rd2.get("correct_answer") or [])

    if not corrects:
        word = rd2.get("word", "") or rd.get("word", "")
        if word:
            log(f" [word={urllib.parse.unquote(word)}]", end="")
        log(" SKIP(no_corrects)")
        skip_answer(token, new_tc, topic_mode, task_type)
        return None

    ans = corrects[0] if isinstance(corrects, list) else corrects

    if topic_mode in (32,):
        if isinstance(ans, str):
            words = ans.split()
            blank_count = content.count('_')
            if len(words) < blank_count:
                expanded = []
                for w in words:
                    if '-' in w:
                        expanded.extend(w.split('-'))
                    else:
                        expanded.append(w)
                words = expanded
            ans = ",".join(words) if len(words) > 1 else ans
        elif isinstance(ans, list):
            ans = ",".join(str(x) for x in ans)

    ans_str = str(ans)
    rv3 = verify_answer(token, ans_str, new_tc, task_type)
    rd3 = rv3.get("data", {}) or {}

    if rv3.get("code") == 1 and rd3.get("answer_result") == 1:
        log(f" OK({ans_str})")
        ts = random.randint(int(min_t * 1000), int(max_t * 1000))
        submit_answer(token, rd3.get("topic_code", new_tc), ts, task_type)
        return rd3
    else:
        log(f" SKIP(verify_fail:{ans_str})")
        skip_answer(token, new_tc, topic_mode, task_type)
        return None

# ============ 学习任务处理 ============

def handle_learning_task(token, task, resp):
    task_id = task["task_id"]
    task_type = task["task_type"]

    if resp.get("code") == 20001:
        log("   选词中...")
        status, body = api_get("ClassTask/ChoseWordList", token,
                               {"task_id": task_id, "task_type": task_type})
        try:
            j = json.loads(body)
            if j.get("code") == 0 and "权限" in j.get("msg", ""):
                log("   !! 权限不足，跳过此任务")
                return {"code": 0, "msg": "skip"}
            word_list = j["data"]["word_list"]
            word_map = {}
            for w in word_list:
                if w.get("score", 0) != 10:
                    key = f"{w['course_id']}:{w['list_id']}"
                    word_map.setdefault(key, []).append(w["word"])
            for w in word_list:
                if sum(len(v) for v in word_map.values()) >= 5:
                    break
                key = f"{w['course_id']}:{w['list_id']}"
                if w["word"] not in word_map.get(key, []):
                    word_map.setdefault(key, []).append(w["word"])
            if word_map:
                api_post("ClassTask/SubmitChoseWord", token,
                         {"task_id": task_id, "task_type": task_type,
                          "word_map": word_map, "chose_err_item": 1, "reset_chose_words": 1})
                log("   选词完成")
                resp = start_answer(token, task)
        except Exception as e:
            log(f"   选词出错: {e}")
            return resp

    d = resp.get("data") or resp
    if isinstance(d, dict) and d.get("topic_mode") == 0:
        log("   跳过学习阶段...")
        tc = d["topic_code"]
        submit_answer(token, tc, 0, task_type)
        api_post("ClassTask/SubmitAnswerAndSave", token, {"topic_code": tc, "time_spent": 0})
        log("   已跳过")
        resp = start_answer(token, task)

    return resp

# ============ 执行单个任务 ============

def do_task(token, task, config):
    t_name = task["task_name"]
    task_type = "ClassTask" if task.get("task_type") in (1, 2) else "MyselfTask"
    release_id = task["release_id"]

    log(f"\n{'='*40}")
    log(f"{t_name}")

    resp = start_answer(token, task)

    if resp.get("code") in (20001,) or (isinstance(resp.get("data") or resp, dict) and (resp.get("data") or resp).get("topic_mode") == 0):
        resp = handle_learning_task(token, task, resp)
    if resp.get("code") == 0 and resp.get("msg") == "skip":
        log(f"  跳过: 无权限")
        return

    if resp.get("code") in (0, -1):
        log(f"  错误: {resp.get('msg', '未知')} [code={resp.get('code')}]")
        return

    data = resp.get("data")
    if not isinstance(data, dict):
        log("  无法获取答题数据")
        return

    while True:
        code = resp.get("code", -1)
        d = resp.get("data", resp)

        if code in (20004, 20001):
            log(f"   任务完成，尝试重置...")
            r_reset = json.loads(api_get("ClassTask/ChoseWordList", token,
                               {"task_id": task["task_id"], "task_type": task["task_type"]})[1])
            if r_reset.get("code") == 1:
                wl = r_reset["data"]["word_list"]
                wm = {}
                for w in wl[:10]:
                    k = f"{w['course_id']}:{w['list_id']}"
                    if k not in wm: wm[k] = []
                    wm[k].append(w['word'])
                r2 = json.loads(api_post("ClassTask/SubmitChoseWord", token,
                    {"task_id": task["task_id"], "task_type": task["task_type"],
                     "word_map": wm, "chose_err_item": 1, "reset_chose_words": 1})[1])
                if r2.get("code") == 1:
                    resp = start_answer(token, task)
                    if resp.get("code") in (20001,) or (isinstance(resp.get("data") or resp, dict) and (resp.get("data") or resp).get("topic_mode") == 0):
                        resp = handle_learning_task(token, task, resp)
                    if resp.get("code") in (0, -1) or not isinstance(resp.get("data"), dict):
                        log(f"  重置失败")
                        break
                    d = resp.get("data", resp)
                    if isinstance(d, dict):
                        done = d.get("topic_done_num", 0)
                        total = d.get("topic_total", 0)
                        log(f"  已重置! 进度: {done}/{total}")
                    continue
            log(f"  任务完成!")
            break

        done = d.get("topic_done_num", 0)
        total = d.get("topic_total", 0)
        if done >= total and total > 0:
            break

        if "stem" in d:
            solve_question(token, d, task["task_id"], task_type, release_id, config)
        else:
            log(f"  无题目数据, code={code}")
            break

        params = {
            "task_id": task["task_id"],
            "task_type": task["task_type"],
            "release_id": release_id,
        }
        status, body = api_get("ClassTask/StartAnswer", token, params)
        try:
            resp = json.loads(body)
        except:
            break

        time.sleep(random.uniform(0.3, 1.0))

    score = _get_task_score(token, release_id, task_type)
    log(f"  完成，分数: {score}")

def _get_task_score(token, release_id, task_type="ClassTask"):
    status, body = api_get("ClassTask/List", token,
                           {"page_count": 1, "page_size": 100})
    try:
        for t in json.loads(body)["data"]["task_list"]:
            if t.get("release_id") == release_id:
                return t.get("score", 0)
    except:
        pass
    return 0

# ============ 主入口 ============

def main():
    import argparse
    p = argparse.ArgumentParser(description="词达人全自动刷题")
    p.add_argument("--check", action="store_true", help="检查 token")
    p.add_argument("--task-id", type=str, help="指定任务ID")
    p.add_argument("--auto", action="store_true", help="全自动模式")
    p.add_argument("--all", action="store_true", help="全自动+所有任务(含已完成)")
    args = p.parse_args()

    config = load_config()
    token = config.get("user_token", "")

    if not token:
        log("请先在 config.json 中设置 user_token")
        log("获取方法: 用 Fiddler 抓包, 见 README.md")
        return

    ok, user = check_token_valid(token)
    if not ok:
        log("Token 无效或已过期，请重新抓取")
        return

    if args.check:
        return

    config["user_token"] = token
    save_config(config)

    tasks = get_class_tasks(token)

    if not tasks:
        log("没有待做任务")
        return

    log(f"\n待做任务 ({len(tasks)} 个):")
    for i, t in enumerate(tasks):
        ttype = {1: "学习", 2: "测试"}.get(t.get("task_type", 1), "?")
        log(f"  [{i+1}] [{ttype}] {t['task_name']} ({t.get('score',0):.1f}分)")

    if args.auto or args.all:
        selected = tasks if args.all else [t for t in tasks if t.get('progress', 0) < 100 and t.get('score', 0) < 100]
        log(f"\n全自动模式: 运行 {len(selected)} 个任务\n")
        for i, t in enumerate(selected):
            log(f"[{i+1}/{len(selected)}] {t['task_name']}")
            try:
                do_task(token, t, config)
            except Exception as e:
                log(f"  !! 任务异常: {e}")
                time.sleep(5)
        log("\n===== 全部完成! =====")
        _print_final_scores(token)
        return

    if args.task_id:
        for t in tasks:
            if str(t.get("task_id")) == args.task_id or str(t.get("release_id")) == args.task_id:
                do_task(token, t, config)
                return
        log(f"未找到任务ID: {args.task_id}")
        return

    log("\n输入序号(空格分隔多个), 留空=全部, a=全自动: ", end="")
    try:
        choice = input().strip()
    except EOFError:
        choice = ""

    selected = tasks if not choice else []
    if choice and choice.lower() != 'a':
        for c in choice.split():
            try:
                idx = int(c) - 1
                if 0 <= idx < len(tasks):
                    selected.append(tasks[idx])
            except:
                pass

    for t in selected:
        do_task(token, t, config)

    if not choice or choice.lower() == 'a':
        log("\n===== 全部完成! =====")
        _print_final_scores(token)

def _print_final_scores(token):
    status, body = api_get("ClassTask/List", token, {"page_count": 1, "page_size": 100})
    try:
        tasks = json.loads(body)["data"]["task_list"]
        total_score = sum(t.get('score', 0) for t in tasks)
        log(f"总得分: {total_score:.1f}")
        for t in tasks:
            if t.get('score', 0) > 0:
                log(f"  {t['task_name']}: {t['score']:.1f}分")
    except:
        pass

if __name__ == "__main__":
    main()
