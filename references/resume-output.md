# resume 命令输出格式

会话启动时 `game.py resume` 返回三层信息。agent 基于此直接叙事，无需再调 `state`。

## 第一层：全局索引（agent 始终持有）

```json
{
  "scenario": "剧本名",
  "synopsis": "3-5句故事概要",
  "act_order": ["导入","探索","高潮","结局"],
  "node_index": {
    "scene_0a": {
      "act": "导入",
      "name": "场景名",
      "location": "地点",
      "summary": "描述前80字...",
      "clue_ids": ["clue_xxx"],
      "next": "scene_0b",
      "exit_rule": "退出条件"
    }
    // hub 节点有 "hub_of": ["loc_a", "loc_b", ...]
  },
  "key_npcs": {
    "npc_id": {
      "name": "NPC名",
      "role": "身份",
      "attitude": "态度",
      "hint": "秘密/关键信息（60字内）"
    }
  },
  "timeline": {
    "start": "起始时间",
    "deadline": "截止时间",
    "per_location": "每个地点耗时"
  }
}
```

## 第二层：当前节点详情

```json
"node": {
  "location": "当前地点",
  "npcs": [
    {"name": "NPC", "role": "身份", "opening": "开场白"}
  ],
  "checks": [
    {"name": "检定名", "skill": 难度, "info": "成功叙事", "on_failure": "失败叙事"}
  ]
}
```

## 第三层：运行时状态

```json
"clue_progress": "3/26",
"pending_in_current": ["clue_id"],  // 当前节点尚未发现的线索
"recent_checks": [...],              // 最近5次检定
"characters": {                      // 角色HP/SAN/状态
  "char_001": {"name": "...", "hp": "11/11", "san": "40/99", "status": "正常"}
},
"campaign_notes": "..."              // 战役记忆最后1500字
```

## agent 行为规则

- `node_index` 和 `key_npcs` 是守秘人内部参考工具——被问到时快速回答，**不主动报菜名、不主动透露 NPC 秘密**
- 玩家切换场景时调 `game.py node <id>`（返回完整节点，不需再调 state）
- **场景切换后：** 用 `description` 做环境描写，提到 NPC 在场 → **停止，等玩家行动** → 玩家互动后才用 `opening`/`key_replies`
- **禁止自导自演 NPC 对话** — NPC 只能说玩家实际触发的内容，不能一次性输出全部台词
- **一个回合只推进一个场景** — 禁止「两小时后」「第二天」等自主快进。玩家不主动说去下一个地点就停在当前场景
- 需要完整线索文本或 NPC key_replies 时 `read_file scenario.json` 定位读
- `game.py state` 仅需完整运行时数据时才调，不是每轮

## 场景切换（node 命令）

`game.py node <id>` 一次性返回：
- description（可直接念的场景叙述）
- npcs[]（opening + key_replies）
- checks[]（含 on_failure）
- clues_available（ID + 文本，已过滤已发现）
- time_cost, next, exits, exit_rule

agent 拿到后直接叙事，不需要再调任何命令。
