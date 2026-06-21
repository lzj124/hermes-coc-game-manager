#!/usr/bin/env python3
"""
COC游戏数据管理器 + 剧本状态机 + 跨会话记忆
支持角色管理 + 剧本节点切换 + 线索追踪 + 战役笔记
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

IST = timezone(timedelta(hours=8))

# 数据文件路径
HERMES_HOME = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
DATA_DIR = Path(HERMES_HOME) / "coc-data"
CHARACTERS_FILE = DATA_DIR / "characters.json"        # 向后兼容：无活跃战役时使用

def get_characters_file():
    """获取当前战役的角色文件路径。有活跃战役则存到战役目录下。"""
    d = get_campaign_dir()
    if d:
        d.mkdir(parents=True, exist_ok=True)
        return d / "characters.json"
    return CHARACTERS_FILE  # 向后兼容
ITEMS_FILE = DATA_DIR / "items.json"                   # 共享
ACTIVE_CAMPAIGN_FILE = DATA_DIR / "active_campaign"    # 纯文本，内容为当前战役名

def get_campaign_dir(campaign_name=None):
    """获取战役目录。不传参则用当前活跃战役。"""
    if campaign_name is None:
        campaign_name = get_active_campaign()
    if not campaign_name:
        return None
    return DATA_DIR / campaign_name

def get_active_campaign():
    """读取当前活跃战役名"""
    if ACTIVE_CAMPAIGN_FILE.exists():
        return ACTIVE_CAMPAIGN_FILE.read_text(encoding="utf-8").strip()
    return None

def set_active_campaign(name):
    """设置当前活跃战役"""
    ACTIVE_CAMPAIGN_FILE.write_text(name, encoding="utf-8")

def get_campaign_path(filename, campaign_dir=None):
    """获取战役目录下的文件路径"""
    if campaign_dir is None:
        campaign_dir = get_campaign_dir()
    if campaign_dir is None:
        return None
    return campaign_dir / filename

# Note: scenario.json is a structured script parsed from the user's .docx/.pdf/.md.
# It follows the four-act structure (导入→探索→高潮→结局) with hub nodes
# for exploration phases. See references/scenario-schema.md for the full spec.

def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def _campaign_file(filename):
    """获取当前战役目录下的文件路径。如果无活跃战役，返回 None。"""
    d = get_campaign_dir()
    if d is None:
        return None
    d.mkdir(parents=True, exist_ok=True)
    return d / filename

def load_json(file_path):
    if file_path is None or not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file_path, data):
    ensure_data_dir()
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now():
    return datetime.now(IST).strftime("%H:%M:%S")

# ── Scenario State Machine ──

def load_state():
    f = _campaign_file("state.json")
    s = load_json(f)
    s.setdefault("current_node", None)
    s.setdefault("discovered_clues", [])
    s.setdefault("check_history", [])
    return s

def save_state(s):
    f = _campaign_file("state.json")
    if f:
        save_json(f, s)

def get_node_info(node_id):
    scenario = load_json(_campaign_file("scenario.json"))
    nodes = scenario.get("nodes", {})
    return nodes.get(node_id)

def state_command():
    """输出完整运行时状态：当前位置、可用线索、检定历史"""
    s = load_state()
    node_id = s.get("current_node")
    scenario = load_json(_campaign_file("scenario.json"))
    all_clues = scenario.get("clues", {})
    nodes = scenario.get("nodes", {})

    node_info = get_node_info(node_id) if node_id else None
    pending = []
    if node_info:
        for cid in node_info.get("clues_available", []):
            if cid not in s["discovered_clues"]:
                clue_text = all_clues.get(cid, cid)
                pending.append({"id": cid, "text": clue_text})

    characters = load_json(get_characters_file())

    return {
        "scenario": scenario.get("name", "未载入"),
        "current_node": node_id,
        "node": node_info,
        "discovered_clues": s["discovered_clues"],
        "pending_clues": pending,
        "check_history": s.get("check_history", []),
        "characters": {cid: {"name": c["name"], "occupation": c["occupation"],
                              "hp": c["hp"], "max_hp": c["max_hp"],
                              "san": c["san"], "max_san": c["max_san"],
                              "status": c.get("status", "正常"),
                              "inventory": [i["name"] for i in c.get("inventory", [])],
                              "clues": [cl["text"] for cl in c.get("clues", [])]}
                       for cid, c in characters.items()}
    }

def node_command(node_id):
    """切换到指定剧本节点，并返回完整节点信息供 agent 立即叙事。"""
    node_info = get_node_info(node_id)
    if not node_info:
        return {"error": f"节点 '{node_id}' 在 scenario.json 中不存在",
                "available_nodes": list((load_json(_campaign_file("scenario.json")).get("nodes", {})).keys())}

    s = load_state()
    s["current_node"] = node_id
    save_state(s)

    # 返回完整节点信息 + 当前节点的未发现线索
    all_clues = load_json(_campaign_file("scenario.json")).get("clues", {})
    discovered = s.get("discovered_clues", [])
    pending = [
        {"id": cid, "text": all_clues.get(cid, {}).get("text", cid) if isinstance(all_clues.get(cid), dict) else str(all_clues.get(cid, cid))}
        for cid in node_info.get("clues_available", [])
        if cid not in discovered
    ]

    return {
        "switched_to": node_id,
        "name": node_info["name"],
        "act": node_info.get("act", ""),
        "location": node_info.get("location", ""),
        "description": node_info.get("description", ""),
        "npcs": [
            {"name": n["name"], "role": n.get("role",""), "opening": n.get("opening",""),
             "key_replies": n.get("key_replies", {})}
            for n in node_info.get("npcs", [])
        ],
        "checks": node_info.get("checks", []),
        "clues_available": pending,
        "next": node_info.get("next"),
        "exits": node_info.get("exits", {}),
        "exit_rule": node_info.get("exit_rule", ""),
        "time_cost": node_info.get("time_cost", ""),
        "at": now()
    }

def found_command(clue_id):
    """标记线索为已发现"""
    scenario = load_json(_campaign_file("scenario.json"))
    all_clues = scenario.get("clues", {})
    if clue_id not in all_clues:
        return {"warning": f"线索 '{clue_id}' 不在 scenario.clues 中，但已记录", "clue": clue_id}

    s = load_state()
    if clue_id in s["discovered_clues"]:
        return {"info": f"线索 '{clue_id}' 已存在", "clue": all_clues[clue_id],
                "already_found": True}
    s["discovered_clues"].append(clue_id)
    save_state(s)
    return {"found": clue_id, "clue": all_clues[clue_id], "at": now()}

def log_command(char_id, check_name, roll, skill):
    """记录检定结果"""
    s = load_state()
    entry = {"char": char_id, "check": check_name, "roll": roll, "skill": skill,
             "at": now()}
    s.setdefault("check_history", []).append(entry)
    # 只保留最近 50 条
    s["check_history"] = s["check_history"][-50:]
    save_state(s)
    return {"logged": entry, "total_checks": len(s["check_history"])}

# ── Character Management (existing) ──

def create_character(name, occupation, hp, max_hp, san, max_san):
    data = load_json(get_characters_file())
    char_id = f"char_{len(data) + 1:03d}"
    data[char_id] = {
        "id": char_id, "name": name, "occupation": occupation,
        "attributes": {}, "skills": {},
        "san": san, "max_san": max_san,
        "hp": hp, "max_hp": max_hp,
        "mp": 15, "max_mp": 15,
        "db": "0", "build": 0, "mov": 8,
        "status": "正常", "inventory": [], "clues": [], "notes": ""
    }
    save_json(get_characters_file(), data)
    return data[char_id]

def update_character_status(char_id, **kwargs):
    data = load_json(get_characters_file())
    if char_id not in data:
        return {"error": f"角色ID {char_id} 不存在"}
    char = data[char_id]
    updatable = ["san", "hp", "status", "inventory", "clues", "notes"]
    for k, v in kwargs.items():
        if k in updatable:
            char[k] = v
    save_json(get_characters_file(), data)
    return char

def get_character(char_id):
    data = load_json(get_characters_file())
    return data.get(char_id, {"error": f"角色ID {char_id} 不存在"})

def list_characters():
    return list(load_json(get_characters_file()).values())

def query_characters(condition):
    data = load_json(get_characters_file())
    results = []
    for cid, char in data.items():
        match = True
        for k, v in condition.items():
            if "." in k:
                obj = char
                for part in k.split("."):
                    obj = obj.get(part, {}) if isinstance(obj, dict) else {}
                if obj != v:
                    match = False
            elif char.get(k) != v:
                match = False
        if match:
            results.append(char)
    return results

def add_item(char_id, item_name, item_type="道具", count=1):
    data = load_json(get_characters_file())
    if char_id not in data:
        return {"error": f"角色ID {char_id} 不存在"}
    for item in data[char_id]["inventory"]:
        if item["name"] == item_name:
            item["count"] += count
            save_json(get_characters_file(), data)
            return {"message": f"已更新 {item_name} 数量到 {item['count']}"}
    data[char_id]["inventory"].append({"name": item_name, "type": item_type, "count": count})
    save_json(get_characters_file(), data)
    return {"message": f"已添加道具：{item_name}"}

# ── Scenario Validation ──

def validate_scenario():
    """校验 scenario.json 完整性，返回 errors/warnings/oks 三级报告"""
    scenario = load_json(_campaign_file("scenario.json"))
    if not scenario:
        return {"errors": ["scenario.json 不存在或为空"], "warnings": [], "oks": []}

    errors, warnings, oks = [], [], []
    nodes = scenario.get("nodes", {})

    # Synopsis
    if not scenario.get("synopsis") or not scenario["synopsis"].strip():
        errors.append("🔴 缺少 synopsis（公开概要）或为空")
    if not scenario.get("keeper_notes") or not scenario["keeper_notes"].strip():
        errors.append("🔴 缺少 keeper_notes（守秘人笔记）或为空")

    # Check all clue references in nodes exist in clues dict
    all_clues = scenario.get("clues", {})
    # collect hub-ref'd sub-node IDs
    sub_location_ids = set()
    for nid, node in nodes.items():
        for loc_id in node.get("locations", []):
            sub_location_ids.add(loc_id)

    # ── 整体结构 ──
    for field in ["name", "meta", "act_order", "nodes"]:
        if field not in scenario:
            errors.append(f"缺少顶层字段: {field}")

    # ── 节点校验 ──
    node_ids = set()
    for nid, node in nodes.items():
        node_ids.add(nid)

        # 🔴 必填字段
        for field in ["id", "act", "name", "location", "description"]:
            if field not in node or not node[field]:
                errors.append(f"[{nid}] 缺少必填字段: {field}")

        # 🔴 线索引用
        for cid in node.get("clues_available", []):
            if cid not in all_clues:
                errors.append(f"[{nid}] 线索引用 '{cid}' 在 clues 字典中不存在")

        # 🔴 检定 on_failure
        for i, chk in enumerate(node.get("checks", [])):
            if "on_failure" not in chk:
                errors.append(f"[{nid}] 检定 #{i} '{chk.get('name', '?')}' 缺少 on_failure")
            if "name" not in chk:
                errors.append(f"[{nid}] 检定 #{i} 缺少 name")
            valid_skill = isinstance(chk.get("skill"), (int, float)) or \
                          chk.get("skill") in ("auto", "n/a", "多段检定", "灵感+意志 双检定")
            if "skill" not in chk or not valid_skill:
                errors.append(f"[{nid}] 检定 '{chk.get('name', '?')}' skill 不是数值（也不是已知语义标记）")

        # 🔴 线性节点必须有 next 或属于结局
        act = node.get("act", "")
        if "next" not in node and act not in ("结局",):
            if "locations" not in node and nid not in sub_location_ids:
                errors.append(f"[{nid}] 非结局节点缺少 next（也不是 hub 节点或子节点）")

        # 🟡 NPC opening
        for j, npc in enumerate(node.get("npcs", [])):
            if "opening" not in npc:
                warnings.append(f"[{nid}] NPC '{npc.get('name', '?')}' 缺少 opening（开场白）")

        # 🟢 通过项
        if node.get("description"):
            oks.append(f"[{nid}] description ✓")
        if node.get("exit_rule"):
            oks.append(f"[{nid}] exit_rule ✓")

    # ── 线索校验 ──
    for cid, clue in all_clues.items():
        if not isinstance(clue, dict):
            errors.append(f"[clue:{cid}] 不是对象格式（应为 {{text, delivery, ...}}）")
            continue
        if "text" not in clue or not clue["text"]:
            errors.append(f"[clue:{cid}] 缺少 text 字段")
        if "delivery" not in clue:
            errors.append(f"[clue:{cid}] 缺少 delivery 字段")
        valid_delivery = {"auto", "inspect", "document", "npc_dialogue"}
        if clue.get("delivery") not in valid_delivery:
            errors.append(f"[clue:{cid}] delivery 值无效: {clue.get('delivery')}（应为 {valid_delivery}）")

    # ── 引用完整性 ──
    # 检查 clue 引用: 所有 clues_available 中的 ID 必须在 clues 字典中
    for nid, node in nodes.items():
        for cid in node.get("clues_available", []):
            if cid not in all_clues and f"clue:{cid}" not in [e.split("]")[0].split(":")[-1] for e in errors]:
                pass  # 已在节点校验中处理

    # ── 时间追踪 ──
    if "time_tracking" not in scenario:
        warnings.append("缺少 time_tracking 字段（有时间压力的剧本建议填写）")
    else:
        tt = scenario["time_tracking"]
        if "start" not in tt:
            warnings.append("time_tracking 缺少 start")
        if "deadline" not in tt:
            warnings.append("time_tracking 缺少 deadline")
        if "default_cost_per_location" not in tt:
            warnings.append("time_tracking 缺少 default_cost_per_location")

    # ── 重复 ID ──
    if len(node_ids) != len(nodes):
        errors.append("存在重复的节点 ID")

    # ── 汇总 ──
    error_count = len(errors)
    warn_count = len(warnings)
    ok_count = len(oks)
    status = "❌ INVALID" if error_count > 0 else ("⚠️ PASS WITH WARNINGS" if warn_count > 0 else "✅ VALID")

    return {
        "status": status,
        "summary": f"{error_count} errors, {warn_count} warnings, {ok_count} checks passed",
        "errors": errors,
        "warnings": warnings,
        "oks": oks[:10]  # 限制输出
    }


# ── 跨会话战役记忆 ──

CAMPAIGN_MEMORY_TEMPLATE = """# 战役记忆 — {scenario_name}

> 最后更新: {timestamp}
> 自动生成，agent 每轮对话后更新。只记 scenario.json 里推不出来的东西。

## 关键决策
<!-- 玩家做的重大选择，按时间倒序 -->

## NPC 状态
<!-- 每个 NPC 的当前态度、是否存活、是否已知调查员身份 -->

## 已触发但未解决的事件
<!-- 被提及但尚未处理的伏笔/威胁 -->

## KP 偏好
<!-- 本战役中玩家表现出的风格偏好 -->

---
*此文件由 game.py note 命令写入。agent 不得手动编辑。*
"""

def resume_command():
    """会话启动摘要 — 类似 Claude Code 的索引注入。
    返回 agent 在新会话开始时最需要知道的紧凑摘要。"""
    s = load_state()
    scenario = load_json(_campaign_file("scenario.json"))
    characters = load_json(get_characters_file())

    node_id = s.get("current_node")
    node_info = get_node_info(node_id) if node_id else None

    # 最近 5 次检定
    recent_checks = s.get("check_history", [])[-5:]

    # 已发现线索数 / 总数
    found_count = len(s.get("discovered_clues", []))
    total_clues = len(scenario.get("clues", {}))
    pending = []
    if node_info:
        for cid in node_info.get("clues_available", []):
            if cid not in s.get("discovered_clues", []):
                pending.append(cid)

    # 角色一览
    char_summary = {}
    for cid, c in characters.items():
        char_summary[cid] = {
            "name": c["name"], "hp": f"{c['hp']}/{c['max_hp']}",
            "san": f"{c['san']}/{c['max_san']}", "status": c.get("status", "正常")
        }

    # 当前节点关键信息（NPC 开场白 + 可用检定摘要）
    node_key_info = {}
    if node_info:
        node_key_info["location"] = node_info.get("location", "")
        node_key_info["npcs"] = [
            {"name": n["name"], "role": n.get("role",""), "opening": n.get("opening","")}
            for n in node_info.get("npcs", [])
        ]
        node_key_info["checks"] = [
            {"name": c["name"], "skill": c.get("skill",""), "info": c.get("info","")}
            for c in node_info.get("checks", [])
        ]

    # ── 全剧本索引（最简 — 只给位置名，不给内容。防止 agent 看到摘要后忍不住快进剧情）──
    nodes = scenario.get("nodes", {})
    node_index = {}
    for nid, nd in nodes.items():
        entry = {
            "act": nd.get("act", ""),
            "name": nd.get("name", ""),
            "location": nd.get("location", "")
        }
        if "next" in nd:
            entry["next"] = nd["next"]
        if "locations" in nd:
            entry["hub_of"] = nd["locations"]
        node_index[nid] = entry

    # 关键 NPC 一览（最简 — 只给身份，不给秘密/定位。agent 需要和 NPC 互动才能了解）──
    key_npcs = {}
    for nid, npc in scenario.get("npcs", {}).items():
        key_npcs[nid] = {
            "name": npc.get("name", ""),
            "role": npc.get("role", ""),
            "attitude": npc.get("attitude", "")
        }

    # 时间线
    timeline = {}
    tt = scenario.get("time_tracking", {})
    if tt:
        timeline["start"] = tt.get("start", "")
        timeline["deadline"] = tt.get("deadline", "")
        timeline["per_location"] = tt.get("default_cost_per_location", "")

    # 读取战役记忆的最后一段（如果有）
    campaign_notes = ""
    cmf = _campaign_file("campaign-memory.md")
    if cmf and cmf.exists():
        raw = cmf.read_text(encoding="utf-8")
        # 只取最近 1500 字符 — 保持紧凑
        campaign_notes = raw[-1500:] if len(raw) > 1500 else raw

    return {
        "scenario": scenario.get("name", "未载入"),
        "synopsis": scenario.get("synopsis", ""),
        "act_order": scenario.get("act_order", []),
        "node_index": node_index,
        "key_npcs": key_npcs,
        "timeline": timeline,
        "current_node": node_id,
        "node_name": node_info.get("name", "") if node_info else "",
        "act": node_info.get("act", "") if node_info else "",
        "node": node_key_info,
        "clue_progress": f"{found_count}/{total_clues}",
        "pending_in_current": pending,
        "recent_checks": recent_checks,
        "characters": char_summary,
        "campaign_notes": campaign_notes,
        "instruction": (
            "以上是当前战役状态摘要。请基于此继续叙事，勿重复已发生的场景。"
            "如果 campaign_notes 中有 KP 偏好，请遵守。"
            "node_index 和 key_npcs 是守秘人的内部参考工具——用来在被问到时快速回答，不是给玩家的旅游手册。"
            "不主动报菜名（可去的地方），不主动透露 NPC 秘密，不让 NPC 一次性走完所有对话分支。"
            "玩家只应该看到眼前的场景。需要完整节点详情时，用 read_file 读 scenario.json 对应部分。"
        )
    }

def note_command(note_type, text):
    """写入战役记忆 — 类似 Claude Code 的 auto-memory 写入。
    note_type: decision | npc_state | event | kp_preference
    """
    if note_type not in ("decision", "npc_state", "event", "kp_preference"):
        return {"error": f"note_type 必须是 decision/npc_state/event/kp_preference，收到: {note_type}"}

    ts = datetime.now(IST).strftime("%Y-%m-%d %H:%M")
    cmf = _campaign_file("campaign-memory.md")
    if cmf is None:
        return {"error": "无活跃战役，请先 game.py init <战役名>"}

    # 确保文件存在
    if not cmf.exists():
        scenario = load_json(_campaign_file("scenario.json"))
        cmf.write_text(
            CAMPAIGN_MEMORY_TEMPLATE.format(
                scenario_name=scenario.get("name", "未命名"),
                timestamp=ts
            ),
            encoding="utf-8"
        )

    content = cmf.read_text(encoding="utf-8")

    # 按类型追加到对应 section
    section_map = {
        "decision": "## 关键决策",
        "npc_state": "## NPC 状态",
        "event": "## 已触发但未解决的事件",
        "kp_preference": "## KP 偏好"
    }
    section = section_map[note_type]

    # 在对应 section 下插入条目
    entry = f"- [{ts}] {text}\n"
    if section in content:
        # 在 section 标题后、下一个 ## 或 --- 前插入
        idx = content.index(section)
        next_section = content.find("\n## ", idx + len(section))
        insert_at = next_section if next_section != -1 else content.find("\n---", idx + len(section))
        if insert_at == -1:
            insert_at = len(content)
        # 找到 section 标题后的第一个换行后插入
        insert_at = content.index("\n", idx) + 1
        new_content = content[:insert_at] + entry + content[insert_at:]
        cmf.write_text(new_content, encoding="utf-8")

    # 更新最后修改时间
    final = cmf.read_text(encoding="utf-8")
    import re
    # 替换第一行 "> 最后更新:" 为当前时间
    final = re.sub(r'> 最后更新:.*', f'> 最后更新: {ts}', final, count=1)
    # 清理多余的 "> 自动生成" 行
    final = re.sub(r'> 自动生成\n(> 自动生成\n)+', '> 自动生成\n', final)
    # 只保留最近 5000 字符 — 防膨胀
    if len(final) > 5000:
        final = final[:1000] + "\n\n... (早期记录已截断) ...\n\n" + final[-4000:]
    cmf.write_text(final, encoding="utf-8")

    return {"recorded": entry.strip(), "type": note_type, "at": ts}

def add_clue(char_id, clue_text):
    data = load_json(get_characters_file())
    if char_id not in data:
        return {"error": f"角色ID {char_id} 不存在"}
    data[char_id]["clues"].append({"text": clue_text, "acquired": now()})
    save_json(get_characters_file(), data)
    return {"message": f"已添加线索：{clue_text}"}

# ── 战役管理 ──

def init_campaign(name):
    """创建新战役目录，设为活跃战役。"""
    camp_dir = DATA_DIR / name
    if camp_dir.exists():
        return {"error": f"战役 '{name}' 已存在", "path": str(camp_dir)}
    camp_dir.mkdir(parents=True)
    set_active_campaign(name)
    return {"init": name, "path": str(camp_dir), "message": f"战役 '{name}' 已创建并设为活跃。请放入 scenario.json。"}

def switch_campaign(name):
    """切换活跃战役"""
    camp_dir = DATA_DIR / name
    if not camp_dir.exists():
        available = [d.name for d in DATA_DIR.iterdir() if d.is_dir() and (d / "scenario.json").exists()]
        return {"error": f"战役 '{name}' 不存在", "available": available}
    set_active_campaign(name)
    scenario = load_json(camp_dir / "scenario.json")
    return {"switched": name, "scenario": scenario.get("name", "未命名")}

def list_campaigns():
    """列出所有战役"""
    campaigns = []
    for d in sorted(DATA_DIR.iterdir()):
        if d.is_dir() and (d / "scenario.json").exists():
            scenario = load_json(d / "scenario.json")
            campaigns.append({
                "name": d.name,
                "scenario": scenario.get("name", "未命名"),
                "active": get_active_campaign() == d.name
            })
    return {"campaigns": campaigns, "active": get_active_campaign()}

def save_scenario(json_path):
    """从 JSON 文件加载剧本到当前战役目录。校验通过后才写入。
    用法: game.py save-scenario /path/to/scenario.json"""
    import shutil
    src = Path(json_path)
    if not src.exists():
        return {"error": f"文件不存在: {json_path}"}
    # 先校验
    try:
        with open(src, "r", encoding="utf-8") as f:
            json.load(f)
    except json.JSONDecodeError as e:
        return {"error": f"JSON 语法错误: {e}"}
    # 复制到临时位置，用 validate_scenario 检查
    camp_dir = get_campaign_dir()
    if camp_dir is None:
        return {"error": "无活跃战役，请先 game.py init <战役名>"}
    dest = camp_dir / "scenario.json"
    if src.resolve() == dest.resolve():
        # 同文件，只校验
        result = validate_scenario()
        return {"saved": str(dest), "scenario": load_json(dest).get("name", "未命名"),
                "note": "源文件与目标相同，仅校验", "validation": result}
    shutil.copy(src, dest)
    # 校验
    result = validate_scenario()
    if result["status"] == "❌ INVALID":
        # 回滚
        dest.unlink()
        return {"error": "剧本校验未通过", "validation": result}
    return {"saved": str(dest), "scenario": load_json(dest).get("name", "未命名"), "validation": result}

def reset_command():
    """重置所有运行时状态 — 用于开启全新剧本或彻底重跑。"""
    s = {"current_node": None, "discovered_clues": [], "check_history": []}
    save_state(s)
    cmf = _campaign_file("campaign-memory.md")
    if cmf and cmf.exists():
        cmf.unlink()
    return {"reset": True, "message": "state.json + campaign-memory.md 已清除。角色和剧本保留。"}

# ── CLI ──

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: game.py <command> [args]"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        # ── 状态机命令 ──
        if cmd == "state":
            print(json.dumps(state_command(), ensure_ascii=False, indent=2))

        elif cmd == "resume":
            print(json.dumps(resume_command(), ensure_ascii=False, indent=2))

        elif cmd == "note":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Usage: game.py note <decision|npc_state|event|kp_preference> <text>"}, ensure_ascii=False))
                sys.exit(1)
            note_type = sys.argv[2]
            text = " ".join(sys.argv[3:])
            print(json.dumps(note_command(note_type, text), ensure_ascii=False, indent=2))

        elif cmd == "validate":
            print(json.dumps(validate_scenario(), ensure_ascii=False, indent=2))

        elif cmd == "reset":
            print(json.dumps(reset_command(), ensure_ascii=False, indent=2))

        # ── 战役管理 ──
        elif cmd == "init":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: game.py init <campaign_name>"}, ensure_ascii=False))
                sys.exit(1)
            print(json.dumps(init_campaign(sys.argv[2]), ensure_ascii=False, indent=2))

        elif cmd == "switch":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: game.py switch <campaign_name>"}, ensure_ascii=False))
                sys.exit(1)
            print(json.dumps(switch_campaign(sys.argv[2]), ensure_ascii=False, indent=2))

        elif cmd == "campaigns":
            print(json.dumps(list_campaigns(), ensure_ascii=False, indent=2))

        elif cmd == "save-scenario":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: game.py save-scenario <path/to/scenario.json>"}, ensure_ascii=False))
                sys.exit(1)
            print(json.dumps(save_scenario(sys.argv[2]), ensure_ascii=False, indent=2))

        elif cmd == "node":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: game.py node <node_id>"}, ensure_ascii=False))
                sys.exit(1)
            print(json.dumps(node_command(sys.argv[2]), ensure_ascii=False, indent=2))

        elif cmd == "found":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: game.py found <clue_id>"}, ensure_ascii=False))
                sys.exit(1)
            print(json.dumps(found_command(sys.argv[2]), ensure_ascii=False, indent=2))

        elif cmd == "log":
            if len(sys.argv) < 6:
                print(json.dumps({"error": "Usage: game.py log <char_id> <check_name> <roll> <skill>"}, ensure_ascii=False))
                sys.exit(1)
            print(json.dumps(log_command(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])), ensure_ascii=False, indent=2))

        # ── 角色管理 ──
        elif cmd == "create":
            name, occ = sys.argv[2], sys.argv[3]
            hp, mhp, san, msan = int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7])
            print(json.dumps(create_character(name, occ, hp, mhp, san, msan), ensure_ascii=False, indent=2))

        elif cmd == "get":
            print(json.dumps(get_character(sys.argv[2]), ensure_ascii=False, indent=2))

        elif cmd == "list":
            print(json.dumps(list_characters(), ensure_ascii=False, indent=2))

        elif cmd == "update":
            char_id, field, value = sys.argv[2], sys.argv[3], sys.argv[4]
            if value.isdigit():
                value = int(value)
            elif value in ("true", "false"):
                value = (value == "true")
            print(json.dumps(update_character_status(char_id, **{field: value}), ensure_ascii=False, indent=2))

        elif cmd == "add-item":
            char_id, item_name = sys.argv[2], sys.argv[3]
            item_type = sys.argv[4] if len(sys.argv) > 4 else "道具"
            count = int(sys.argv[5]) if len(sys.argv) > 5 else 1
            print(json.dumps(add_item(char_id, item_name, item_type, count), ensure_ascii=False, indent=2))

        elif cmd == "add-clue":
            print(json.dumps(add_clue(sys.argv[2], sys.argv[3]), ensure_ascii=False, indent=2))

        elif cmd == "query":
            field, value = sys.argv[2], sys.argv[3]
            if value.isdigit():
                value = int(value)
            print(json.dumps(query_characters({field: value}), ensure_ascii=False, indent=2))

        else:
            print(json.dumps({"error": f"Unknown command: {cmd}"}, ensure_ascii=False))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()