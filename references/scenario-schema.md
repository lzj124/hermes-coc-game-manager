# scenario.json 结构规范

## 🔴🟡 字段标记约定

- 🔴 = **必填** — 缺了 agent 无法独立运行该场景
- 🟡 = **推荐** — 缺了 agent 可以临时填充，但质量会下降
- 无标记 = **可选**

---

## 整体结构

```json
{
  "name": "剧本名",                                                  // 🔴
  "synopsis": "公开概要 — 只写调查员开局时已知的事。谁死了、谁请了调查员、来干什么。不含任何守秘人才知道的真相。",  // 🔴 resume 注入此项
  "keeper_notes": "守秘人笔记 — 完整的幕后真相。教派内幕、NPC 真实身份、仪式时间地点、结局走向。此字段仅供守秘人查阅，不注入 resume。",  // 🔴 必须存在但不注入 agent 上下文
  "meta": {                                                         // 🔴
    "difficulty": "简单|中等|困难",                                    // 🔴
    "estimated_time": "预计时长",                                     // 🟡
    "players": "推荐人数",                                            // 🟡
    "era": "背景时代",                                                // 🔴 用于 agent 确定时代细节
    "rules": "COC 7th"                                              // 🔴
  },
  "act_order": ["导入", "探索", "高潮", "结局"],                       // 🔴
  "time_tracking": { ... },                                         // 🟡 有时间限制的剧本必填
  "nodes": { ... },                                                 // 🔴
  "clues": { ... },                                                 // 🔴
  "npcs": { ... },                                                  // 🔴
  "san_checks": [ ... ],                                            // 🟡
  "combat": { ... }                                                 // 🟡
}
```

### 时间追踪 (time_tracking) — 🟡 有时间限制必填

```json
"time_tracking": {
  "start": "10月21日 18:00",              // 🔴 游戏起始时间
  "deadline": "10月25日 03:17",           // 🔴 最终截止时间
  "default_cost_per_location": "2小时",    // 🔴 探索一个地点默认耗时
  "time_sensitive_npcs": {                // 🟡 只在特定时间出现的 NPC
    "艾琳·陈": "周二/周四晚",
    "弗兰克": "周一至周五 22:00-06:00"
  }
}
```

agent 每轮回复后追踪当前日期时间，在玩家切换地点时推进时间。接近 deadline 时应通过环境描述（天色、NPC 催促）提示紧迫感。

## 节点类型

### 线性节点（标准四幕）

```json
"scene_1": {
  "id": "scene_1",                                                  // 🔴
  "act": "开场|发展|高潮|结局",                                       // 🔴
  "name": "场景名",                                                  // 🔴
  "location": "地点",                                                // 🔴
  "description": "环境氛围描述（agent 直接叙述给玩家的文本）",           // 🔴
  "time_cost": "30分钟",                                             // 🟡 探索此地点的耗时
  "npcs": [{                                                        // 🟡 在场 NPC
    "name": "NPC名",
    "role": "身份",
    "opening": "开场白（NPC 见到调查员说的第一句话）",                  // 🟡 agent 必用
    "key_replies": {                                                // 🟡 对话钩子
      "被问到X": "NPC的回答",
      "被问到Y": "NPC的回答"
    }
  }],
  "clues_available": ["clue_id"],                                   // 🟡
  "checks": [{                                                      // 🟡
    "name": "检定名",                                                // 🔴
    "skill": 难度值,                                                 // 🔴
    "info": "成功后的信息（agent 叙述用）",                            // 🔴
    "on_failure": "失败后的结果（agent 叙述用）"                       // 🔴 防止 agent 现场编造
  }],
  "next": "scene_2",                                                // 🔴
  "exit_rule": "退出条件描述"                                         // 🔴 agent 判断何时推进
}
```

**关键变更：**
- `checks[].on_failure` 🔴 必填 — 每个检定必须有失败路径，agent 不能现场拍"失败了怎么办"
- NPC 的 `opening` 🟡 推荐 — agent 不知道 NPC 该说什么时用的第一句
- NPC 的 `key_replies` 🟡 推荐 — 关键问题的预设回答，防止 agent 让 NPC 说不该说的话
- `time_cost` 🟡 推荐 — 有时间压力时必须填，否则 agent 无法推进时钟

### 分支结局节点
```json
"scene_4a": {
  "id": "scene_4a",
  "act": "结局",
  "name": "好结局 - 名称",
  "description": "结局叙事",
  "effects": {"san_change": "+1d6"},
  "next": null
}
```

### Hub 节点（自由探索阶段）
```json
"scene_1": {
  "id": "scene_1",
  "act": "探索",
  "name": "自由探索·区域名",
  "location": "区域描述",
  "locations": ["loc_a", "loc_b", "loc_c"],
  "notes": "探索线索引导 / 时间线提醒",
  "next": "scene_2",
  "exit_rule": "推进条件"
}
```
每个 `loc_*` 是独立的可探索子节点，结构与线性节点相同但不设 `next`（探索无固定顺序）。

## 线索系统

```json
"clues": {
  "clue_xxx": {
    "text": "玩家实际看到/听到/读到的完整文本",                      // 🔴 agent 直接念给玩家的
    "delivery": "npc_dialogue | inspect | document | auto",        // 🔴 交付方式
    "source": "NPC名 / 地点 / 物品",                                 // 🟡 从哪获得
    "check_required": true | false                                  // 🟡 是否需要检定（默认 false）
  }
}
```

**delivery 类型说明：**

| delivery | 含义 | agent 行为 |
|----------|------|-----------|
| `auto` | NPC 或场景自动告知 | 玩家进入场景/对话后直接 `found`，不走检定 |
| `inspect` | 需要观察/侦查 | 提示玩家可检定，成功后 `found` |
| `document` | 读到的文档/笔记 | 检定成功后展示 `text` 全文 |
| `npc_dialogue` | NPC 口中说出 | NPC 在对话中自动给出，或检定成功后说出 |

- `clue_id` 全局唯一，命名建议 `clue_<loc>_<num>` 或 `clue_<phase>_<num>`
- `text` 🔴 **必须包含 agent 能逐字念给玩家的内容** — 不能只是一行摘要
- 场景节点的 `clues_available` 列出当前场景可获取的线索 ID
- `delivery: "auto"` 的线索在玩家接触来源后立即 `found`，不需要玩家主动问

## NPC 系统

完整 NPC 结构：
```json
"npc_xxx": {
  "name": "全名",
  "role": "身份/分支",
  "stats": "HP/关键技能",
  "attitude": "态度",
  "secrets": ["秘密1"],
  "flip_condition": "倒戈条件",
  "weakness": "弱点",
  "defeat_condition": "击败条件"
}
```

## SAN 检定

```json
"san_checks": [
  {"scene": "节点ID", "trigger": "触发事件", "check": "成功/失败扣除(如 1d3/1d6)"}
]
```

## 战斗

```json
"combat": {
  "monster_id": {
    "name": "怪物名",
    "stats": "HP/STR/SIZ...",
    "armor": 护甲值,
    "attacks": ["攻击名 概率, 伤害"],
    "abilities": ["特殊技能"],
    "weaknesses": ["弱点"],
    "san_loss": "SAN扣除"
  }
}
```

## 注意事项

- `checks[].skill` 是对抗难度，不是玩家技能值。检定必须用玩家角色的实际技能。
- 自由探索阶段每个 `loc_*` 节点独立，agent 不需要为每次进入调 `node`——用 state 获取当前位置即可。
- 剧本解析由 LLM 完成，game.py 不涉及剧本内容理解。

---

## 校验命令

```bash
python3 scripts/game.py validate
```

检查 scenario.json 完整性并输出报告。分成三档：

| 级别 | 含义 | 示例 |
|------|------|------|
| 🔴 ERROR | 缺了 agent 无法运行的字段 | `clue 无 text`、`check 无 on_failure` |
| 🟡 WARNING | 缺了会降低质量 | `NPC 无 opening`、`无 time_tracking` |
| 🟢 OK | 检查通过 | — |

**校验项：**

| 检查项 | 级别 | 说明 |
|--------|------|------|
| `synopsis` 字段存在且非空 | 🔴 | 新守秘人需要故事概述 |
| 所有 `clue_id` 在 `clues` 字典中有定义 | 🔴 | 引用不能悬空 |
| 所有 `clue` 有 `text` 字段且非空 | 🔴 | agent 需要念的内容 |
| 所有 `check` 有 `on_failure` 字段 | 🔴 | 防止 agent 现场编失败后果 |
| 所有线性节点有 `next` 或为结局节点 | 🔴 | 不能断链 |
| 所有节点有 `description` 且非空 | 🔴 | agent 需要场景叙述文本 |
| NPC 有 `opening` 字段 | 🟡 | 建议 |
| 有时间压力的剧本有 `time_tracking` | 🟡 | 建议 |
| `checks[].skill` 是数值类型 | 🔴 | 不能是字符串 |
| 无重复 `clue_id` / `node_id` / `npc_id` | 🔴 | 全局唯一 |

---

## 数据存储约定

所有 COC 数据统一放在 `$HERMES_HOME/coc-data/`：

```
$HERMES_HOME/coc-data/
├── scenario.json      ← 剧本（唯一写入点）
├── state.json         ← 运行时状态（只由 game.py 写入）
├── characters.json    ← 调查员数据
├── npcs.json          ← NPC（从 scenario.json 提取或脚本生成）
└── items.json         ← 物品
```

**搜索规则（强制）：**
搜 COC 数据时第一步**必须** `search_files path=$HERMES_HOME/coc-data pattern=*`。
找到文件后直接读取，不要从 `/Users/jackbot` 全盘搜索——小目录容易被结果淹没。
