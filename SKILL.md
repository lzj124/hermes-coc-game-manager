---
name: coc-game-manager
description: COC TRPG 跑团主控台 — 唯一入口。管理角色、线索、场景推进、骰子检定、跨会话记忆、多战役隔离。内置真随机骰子，零外部依赖。
triggers: 跑团, COC, 克苏鲁, 守秘人, KP, 创建角色, 调查员, 车卡, 剧本大纲, 开始游戏, 继续跑团, 上次跑到哪了, 检定, SAN, HP, NPC, 线索, 道具, 模组, 剧本, 新剧本, scenario
---

# COC 游戏管理器 — 跑团唯一入口

> ⚠️ **这是 COC 跑团唯一需要加载的 skill。** 加载这个就够，骰子走内置 `scripts/roll.py`。零外部依赖。

## 设计哲学

**受 Claude Code 记忆机制启发：**

1. **结构化优于自由文本** — 线索、检定、NPC 全有固定 schema，不做"自由描述"
2. **索引常驻 + 内容按需** — 会话启动时注入紧凑摘要，完整内容用时再展开
3. **禁止存能推出来的** — 不把 scenario.json 已有的内容再记到 state 里
4. **启动时强制注入** — agent 不需要"记住"调 state；`resume` 命令在会话开局自动完成注入

---

## 架构

```
$HERMES_HOME/coc-data/
├── active_campaign          ← 当前活跃战役名
├── <战役名A>/
│   ├── scenario.json
│   ├── state.json
│   ├── characters.json      ← 战役隔离：每个战役独立角色库
│   └── campaign-memory.md
└── <战役名B>/
    ├── scenario.json
    ├── characters.json
    └── ...
```

**静态层** — `scenario.json`（剧本结构）、`characters.json`（本战役角色库）
**动态层** — `state.json`（运行时进度）、`campaign-memory.md`（跨会话笔记）
**校验** — `game.py validate`

---

## 新会话启动（最重要）

```bash
python3 scripts/game.py resume
```

**agent 在每段新会话的第一个回复前，必须先调 `resume`。**

`resume` 返回三层信息：
- **全局索引** — `node_index`（所有节点名/幕/位置，**不含内容摘要**）、`key_npcs`（所有 NPC 姓名/角色/态度，**不含秘密**）、`timeline`、`synopsis`、`act_order`
- **当前节点** — NPC 开场白、可用检定、待发现线索
- **运行时状态** — 线索进度、角色 HP/SAN、最近检定、战役笔记

agent 用全局索引回答「还有哪些地方」「那是谁」——但**不知道每个地点里有什么、NPC 的秘密是什么**。只有玩家去到那个地点、调了 `node`，agent 才能拿到完整的场景描述和 NPC 台词。**索引是地图，不是攻略。**

### 全新剧本完整流程

```bash
# 1. 创建战役
game.py init "剧本名"

# 2. agent 用 write_file 写 JSON → 用 save-scenario 校验入库
game.py save-scenario /path/to/written/scenario.json

# 3. 车卡（新战役必须新建角色，旧时代角色不能跨剧本）
game.py create "角色名" "职业" HP MHP SAN MSAN
# 然后用 execute_code 编辑 characters.json 补全属性和技能

# 4. 校验通过后初始化
game.py node scene_0a
```

**⚠️ 新角色创建后必须展示完整角色卡给玩家再推进剧情。** 玩家不知道你替他车了什么卡——先 `game.py get <id>` 展示全卡，让玩家确认，再切场景。不要像胖绅士跑团那样跳步骤导致玩家问「我是谁」。

**⚠️ agent 不要直接手写 JSON 到 campaign 目录 — 先用 write_file 写临时文件，再用 save-scenario 校验入库。这样 JSON 语法错误会被拦截。**

### 切换已有战役

```bash
game.py campaigns                  # 列出所有战役
game.py switch "战役名"            # 切换
```

---

## 游戏循环

```
新会话启动
  │
  ▼
game.py resume          ← 全局索引 + 当前节点详情（必须第一步）
  │                     resume 已给：node_index/key_npcs/timeline/synopsis
  │                     当前节点的 NPC 台词 + 检定列表
  ▼
环境描写                 ← 用当前节点 description，提到 NPC 在场
  │                     ⚠️ 提到 NPC 后必须停止，等玩家行动
  │                     ⚠️ 禁止自导自演 NPC 长篇对话
  ▼
玩家行动 ──→ 切换场景?
  │           ├─ 是 → game.py node <new_node>
  │           │       返回完整节点：description/NPC/检定/线索
  │           │       → 环境描写 → 等玩家行动
  │           └─ 否 → 继续
  │
  ▼
玩家行动 ──→ 需要检定?
  │           ├─ 是 → roll.py skill <从 characters.json 读取的值>
  │           │       → game.py log 记录 → 叙事结果
  │           └─ 否 → 直接叙事
  │
  ▼
发现线索? ──→ game.py found <clue_id>
  │
  ▼
关键决策? ──→ game.py note <type> <text>
  │
  ▼
继续循环
```

> `game.py state` 仅当需要完整运行时状态（全部线索进度、角色库存等）时才调用，不是每轮必调。

---

## 命令参考

### 状态机（跑团核心）

| 命令 | 用途 | 调用时机 |
|------|------|---------|
| `resume` | 会话启动摘要 | **新会话第一步，必须** |
| `state` | 完整运行时状态 | 需要全部线索进度/角色库存/检定历史时（不每轮必调） |
| `node <id>` | 切换剧本节点 | 场景切换 — **返回完整节点信息**（描述/NPC/检定/线索），无需再调 state |
| `found <clue_id>` | 标记线索已发现 | 玩家获取线索后立即 |
| `log <char> <check> <roll> <skill>` | 记录检定 | 每次投骰后 |
| `note <type> <text>` | 写入战役笔记 | 关键决策后**必须** |
| `validate` | 校验 scenario.json | 剧本写完/修改后 |
| `reset` | 清空当前战役运行时 | 重跑同一剧本 |

### 剧本管理

| 命令 | 用途 |
|------|------|
| `save-scenario <json_path>` | 校验 JSON 并入库到当前战役目录。JSON 语法错误或 schema 不完整会拒绝。 |

### 战役管理

| 命令 | 用途 |
|------|------|
| `init <名>` | 创建新战役目录，设为活跃 |
| `switch <名>` | 切换活跃战役 |
| `campaigns` | 列出所有战役 |

### 角色管理

| 命令 | 用途 |
|------|------|
| `create <名> <职业> <HP> <MHP> <SAN> <MSAN>` | 创建角色 |
| `get <char_id>` | 查角色 |
| `list` | 列所有角色 |
| `update <char_id> <字段> <值>` | 更新 HP/SAN/状态 |
| `add-item <char_id> <道具名> [类型] [数量]` | 添加道具 |
| `add-clue <char_id> <线索文本>` | 给角色添加个人线索 |

### 战役笔记类型

| type | 含义 | 示例 |
|------|------|------|
| `decision` | 玩家重大选择 | "选择踢大叔当诱饵争取开伞时间" |
| `npc_state` | NPC 当前状态 | "沃恩已被警察带走" |
| `event` | 已触发未解决的事件 | "星之精未被消灭，可能再次出现" |
| `kp_preference` | KP 风格偏好 | "玩家偏好快节奏，少探索多推进" |

**纪律：** 关键决策后必须调 `note`，不能只在心里记。

---

## 如何写一份好剧本

1. agent 阅读用户提供的 .doc/.pdf/.md 剧本
2. agent 按 `references/scenario-schema.md` 规范生成 JSON
3. agent 用 `write_file` 写到临时路径（如 `/tmp/scenario.json`）
4. agent 调 `game.py save-scenario /tmp/scenario.json` 校验入库
5. 如果报错，修 JSON 后重试 `save-scenario`

### 🔴 必填
- 顶层必须有 `synopsis`（3-5句话故事概要）
- 每个节点有 `description`（agent 念给玩家的文本）
- 每条线索是 `{text, delivery}` 对象
- 每个检定有 `on_failure`
- 线性节点有 `next` + `exit_rule`

---

## KP 边界（必须遵守）

**以下严禁透露给玩家：** `node.notes`、NPC 的 `secret`、`pending_clues` 完整文本、`san_checks`/`combat` 数据、`exit_rule` 原文。

**NPC 纪律：** 一个 NPC 只能说他自己知道的事。

**检定提示纪律：** 括号里写玩家技能值，不是剧本难度。✅ "侦查 — 你的 70" ❌ "侦查 (55)"

**玩家偏好纪律：** KP风格选择（如检定是否显示骰子数值、叙事详细程度）不在 skill 中写死。每个团/玩家偏好不同，新战役开始时跟玩家当面定。skill 只管流程规则，不管风格选择。

**推进纪律：** 
- 玩家说做什么就推进，不反复确认。"确定要这样做吗？"不问第二遍
- 检定失败不等于剧情卡死 — 给替代路径（代价、绕路、新发现）
- 战斗轮：先宣言行动 → 投骰 → 结算伤害 → 叙事
- **大失败必须结算伤害：** 格斗/闪避/射击等战斗技能的大失败不能只给叙事惩罚——必须掷伤害骰。摔伤 1D3、武器损坏、或给对手一次免费反击。叙事+数值缺一不可。上次黄衣之王跑团中格斗大失败只丢了武器没掷伤害，被纠正。
- **description 不是台词本：** `node` 返回的 `description` 字段常内嵌多段 NPC 对话片段（如「"那些装饰品？生产商自己的创意…""弗洛先生推荐的工人…"」），这些是 KP 素材库，**不能一次性倒给玩家**。正确做法：只取 `description` 的环境/氛围部分开场，NPC 对话按玩家实际提问逐条从 `key_replies` 中取。典型翻车：进克鲁办公室一回合就把三个会员的五六段发言全抖出来

**叙事节奏（防信息倾泻）：**

四条铁律——resume 给了 agent 全剧本索引，但那是守秘人的内部参考，不是给玩家的旅游手册：
1. **不主动报菜名** — 不说「你可以去 A/B/C/D」。最多在环境描写中自然提及一两个临近地点，让玩家自己决定。除非玩家明确问「这附近有什么地方可去」
2. **NPC 只说被问到的** — key_replies 是预设答案库，不是对话脚本。玩家问 A 才答 A，不附带 B/C/D
3. **索引是工具，不是台词** — node_index/key_npcs 在被问到时快速回答，不找机会倒信息
4. **一个回合只推进一个场景** — 禁止「两小时后…」「第二天…」自主快进。玩家不主动说去下一个地点就停在当前场景。agent 不能替玩家决定日程

**工具纪律：** 先查现有工具/skill 再建议装新的，别上来就整复杂方案。

**exits 字段处理：** `node` 返回的 `exits` 字段包含同一建筑/场景内的子节点入口（如 `loc_flowe_locked_room`、`loc_flowe_storage`）。这些子节点**只能**在玩家角色**亲眼看见该入口**或**NPC 明确告知**后提及。当前节点 NPC 未提、玩家未发现的门/房间/密道，KP 不能替玩家列出来。切换场景时如玩家选了一个 exit，只需 `node <那个子节点>` 完成切换，不要说「或者你也可以去 X」。

---

## 骰子检定

**agent 不要加载 coc-dice skill，直接用内置 roll.py：**

```bash
python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/roll.py skill <玩家技能值>
python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/roll.py d100
```

**⚠️ roll.py 不支持多骰子语法（`2d6`、`3d6` 等会报 `Unknown command`）。** 需要掷伤害骰时，用 `execute_code` 写 Python 的 `random.randint(1,6)` 求和。

---

## 战役完结（Post-Campaign Review）

玩家说"完团了"、"结束了"、或剧情推进到结局节点后，agent 必须主动做以下五步：

**1. 读最终状态** → `game.py resume`

**2. 更新角色状态** → 根据结局效果（SAN 回复、HP 变化、道具增减），用 `game.py update` 同步角色卡：
```bash
game.py update char_001 san <最终值>
game.py update char_001 hp <最终值>
```

**3. 记录 NPC 状态** → `game.py note npc_state` 记下每个关键 NPC 的最终结果：谁存活、谁死亡、谁逃了、态度变化。

**4. 清理未解决事件** → `game.py note event "已解决: ..."` 把 campaign-memory.md 里所有"已触发但未解决"的事件逐一清掉。

**5. 补记 KP 偏好** → 如果 KP 偏好栏为空，补记至少一条本战役观察到的玩家风格。

完整审查清单 → `references/post-campaign-review.md`

---

## References

| 文件 | 内容 |
|------|------|
| `references/scenario-schema.md` | 剧本 JSON 完整字段规范（🔴🟡必填/推荐标记） |
| `references/scenario-design.md` | 四幕结构、线索系统、NPC 设计原则 |
| `references/scenario-from-document.md` | **从 .doc/.docx 源剧本完整构建 scenario.json — 不跳步、不偷懒、不骨架** |
| `references/resume-output.md` | resume 命令输出格式规范 — 三层索引设计 |
| `references/pitfalls.md` | 致命错误清单 — **每轮跑团前必读** |
| `references/custom-mechanics.md` | 自定义机制追踪 — 相信值等非标准 COC 数值的跨会话持久化 |
| `references/pitfalls.md` | 致命错误清单 — **每轮跑团前必读** |
| `references/custom-mechanics.md` | 自定义机制追踪 — 相信值等非标准 COC 数值的跨会话持久化 |
| `references/post-campaign-review.md` | 跑团审查清单 — **中期检查 + 结案审查** |
| `references/data-structure.md` | 角色/NPC/道具/线索 JSON schema |
| `references/story-outline-template.md` | 故事大纲模板 |
| `scripts/game.py` | 主程序（无外部依赖） |
| `scripts/roll.py` | COC 7版真随机骰子（大成功/大失败判定） |
