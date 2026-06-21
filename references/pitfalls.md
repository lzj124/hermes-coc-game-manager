# Pitfalls

### update 命令 MP/SAN 字段名大小写

`game.py update` 对某些属性字段名区分大小写。`san`（小写）有效，但 `mp`（小写）无效——穿越传送门消耗 MP 时 `update char_001 mp 7` 静默失败，MP 不变。

**正确：** `game.py update char_001 MP 7`（大写 MP），或直接用 Python 读/写 characters.json。
**验证：** update 后调 `game.py get char_001` 检查返回值确认字段已变更。

### 场景切换忘记调 `game.py node`

玩家说"去案发现场看看"，agent 直接叙事新场景但没调 `game.py node loc_death_site`——导致场景描述靠记忆编造，缺少当前节点的 NPC 台词和检定列表。

**规则：** 玩家离开当前节点去新地点 → **第一步就是 `game.py node <id>`**，拿到完整节点信息后再叙事。不能凭 resume 的 node_index 摘要就开讲。

### agent 不等玩家互动就自导自演 NPC 对话

agent 进新场景后常把 NPC 的开场白和后续对话一次性全部输出——没给玩家插话的机会。NPC 只能说玩家**实际触发**的对话。

**正确流程：**
1. `node` 切换到新场景 → 用 `description` 做环境描写
2. 提到 NPC 在场（如"一个老教授正在批改试卷"）→ **停止，等玩家行动**
3. 玩家说"跟他聊聊" → 才用 NPC 的 `opening` 做第一句
4. 玩家问具体问题 → 才查 `key_replies` 回答

**禁止：** 环境描写完就直接让 NPC 来一段长篇独白。

**⚠️ description 不是脚本：** node 返回的 `description` 字段常包含多段 NPC 对话片段（如"弗洛先生推荐的工人——泽地来的…""自从妻女出事后，弗洛就变了…"）——这些是 KP 内部素材库，**不能一次性全部输出**。正确做法：只拿 `description` 的第一段（环境/氛围描写）开场，NPC 对话片段按玩家实际提问逐条用。典型翻车：杰哥刚自我介绍完，agent 就把三个会员的五六段发言全倒出来。

### 描述场景里不存在的物品/动作

agent 在叙事时容易把别的场景的道具挪过来用——比如在火车站的出站口说 NPC「从抽屉里拿出笔记」，但火车站根本没有抽屉。
**对策：** 描述动作前先看节点 `location` 字段确认当前场景。车站出站口 = 公文包/木箱/长椅可用，办公楼 = 抽屉/文件柜/茶具可用。
**用户直接指出：** 「哪里的抽屉？我们不是在火车站嘛」

### agent 在冗长叙事中忘记调 state
三层防线：
1. **Skill 规则**：`resume` 已给全局索引 + 当前节点详情，正常叙事不需要每轮调 `state`。只在需要全部线索进度/角色库存/检定历史时才调
2. **用户一句拉回**："查下 state" 或 "我们在哪"
3. **新会话重启**：空白上下文 + skill 约束 = 偏离概率最低

### 把幕后信息（notes）当场景描述泄露给玩家
state 返回的 `node.notes` 字段是给 KP 的内部信息（仪式时间、NPC 行踪、幕后动机），**不是给玩家的场景描写**。
叙事时只用 `node.description` 和 `node.location`。
典型翻车：告诉玩家"今晚艾琳会去沃恩家送致幻剂"——这是 notes 里的，玩家此时还不知道。

### 检定提示显示剧本难度而非玩家技能值
检定提示括号里必须是玩家的实际技能值（从 characters.json 读取），不是 scenario.json 的难度值。
**正确：** `侦查 — 你的 70` | **错误：** `侦查(60)`
scenario 的 skill 值仅供 agent 内部判定难度等级。

### 线索太多导致 pending_clues 列表过长
探索阶段可能有 20+ clues，全部列在 pending 中会冗长。
解决：pending_clues 只显示当前节点可获取的线索。已移出当前节点范围的线索不显示。

### 检定技能值硬编码 vs 玩家角色
scenario.json 中的 `skill` 值是对抗难度，不是玩家技能值。
检定时必须用玩家角色的实际技能值做 `roll.py skill`，而非 scenario 中写的数值。

### 游戏中断做大量文件搜索
跑团过程中如果缺剧本文件或数据，不要在玩家等待时连续做 5+ 次 `search_files` / `session_search`。这样做会让玩家觉得游戏卡住了。
**对策：** 如果缺数据（如 scenario.json 不存在），立刻进无剧本模式继续推剧情——不要中断叙事去做大范围搜索。数据补齐是后台/会话结束后的事。

### NPC 说了他不可能知道的事（NPC 背面信息泄露）
一个 NPC 只能透露他**自己亲眼见过、亲身经历过**的信息。
典型翻车：让马库斯说"艾琳的已故丈夫被学术界否定，所以她参与实验是为了证明丈夫是对的"——这是艾琳自己埋在心底的秘密，马库斯不可能知道，只有去诊所跟她本人对峙时才可能被挖出来。
**场景 A 的 NPC 不能替场景 B 的 NPC 交代背景故事。**
**对策：** 写 NPC 对话前，问自己"这个人是从哪知道这件事的？"——如果答案不成立，不说。

### 跑团中用了 clawd 旧路径而非 Hermes 路径

### resume 注入太稀疏，agent 对其他节点/NPC 一无所知

resume 最初只返回当前节点信息（NPC 开场白 + 检定列表）。agent 不知道还有其他地点和 NPC，无法做铺垫、无法让 NPC 引用其他角色、无法暗示其他调查方向——像守秘人只读了当前场景那一页。

**教训：** resume 必须包含三层信息，对标 Claude Code 的代码索引：
- **全局索引** — node_index（所有节点名/幕/位置/摘要/clue_ids）、key_npcs（所有 NPC 身份+态度）、timeline、synopsis
- **当前节点** — NPC 台词、检定列表（展开的详细信息）
- **运行时状态** — 线索进度、角色 HP/SAN、检定历史

这样 agent 始终知道"还有哪些地方可去、还有哪些 NPC 存在"，但只在玩家实际到达时用 `read_file` 加载对应节点的完整描述/NPC 台词/检定 on_failure。

**具体实现见 `game.py` 的 `resume_command()`。**
coc-dice 和 coc-game-manager 已迁移到 Hermes（`$HERMES_HOME/skills/leisure/`）。
**错误：** `python3 <user_home>/clawd/skills/public/coc-dice/scripts/roll.py`  
**正确：** `python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/roll.py`

agent 加载 skill 后必须用 Hermes 绝对路径，不要凭记忆走 clawd 旧工作区。

### 搜索剧本数据时漏掉了 .hermes/coc-data 目录
agent 在 `clawd/`、`hermes-agent/`、`$HERMES_HOME/skills/` 里搜了几圈没找到 scenario.json，
就下结论"剧本不存在"进无剧本模式——但实际上 `$HERMES_HOME/coc-data/` 里三个文件全在
（`scenario.json` / `state.json` / `characters.json`）。

**教训：** 搜索 COC 数据时，第一个应该搜的目录就是 SKILL.md 开头写的
**数据目录 `$HERMES_HOME/coc-data/`**。从 `<user_home>` 出发的全局搜索有结果上限，
小目录容易被淹没。

**正确搜索顺序：**
1. `search_files path=$HERMES_HOME/coc-data pattern=scenario`
2. 确认 `state.json` 和 `characters.json` 也在同目录
3. 如果都不存在，再进无剧本模式

**禁止行为：** 搜了几个不对的目录后就说"scenario 不存在/没找到"——先确认搜了
正确目录再下结论。

### create_character 不生成属性/技能，需后续手动填充

`game.py create <名> <职业> <HP> <MHP> <SAN> <MSAN>` 只创建角色框架：
`attributes` 和 `skills` 字段初始化为空 `{}`，`db`/`build`/`mov` 等战斗属性为占位值。

**必须后续操作：**
1. 用 `game.py update char_xxx 字段 值` 逐项填充技能（如 `update char_001 skills '{"侦查":70}'`）
2. 或直接用 Python 读取 characters.json、修改后写回

**新建角色后不填充技能直接跑团 → 所有检定都是 0，全失败。**

### 手写 scenario.json 时 JSON 转义错误

agent 用 `write_file` 直接写 JSON 时，`description` 字段里的原文引号常被漏转义。

**典型翻车：**
```json
"description": "他低声说："你不能进去。"——门锁了。"
```
上面这个 JSON 是非法的。内层双引号破坏了字符串边界。

**正确做法：**
```json
"description": "他低声说：'你不能进去。'——门锁了。"
```
或
```json
"description": "他低声说：\"你不能进去。\"——门锁了。"
```

**预防：** 写完 scenario.json 后立即 `game.py validate`，JSON 语法错误会被 Python 直接报出来。

### 漏调 game.py init 导致写到平面目录

新剧本应该走 `game.py init "剧本名"` 创建战役目录，scenario.json 写入 `$HERMES_HOME/coc-data/<战役名>/`。agent 常跳过 init 直接写 `$HERMES_HOME/coc-data/scenario.json`（平面目录），多战役混在一起。

**正确流程：**
```
game.py init "剧本名"                         # 创建隔离目录
write_file → $HERMES_HOME/coc-data/剧本名/scenario.json
game.py validate                              # 检查
```

### 幻觉加载 coc-keeper skill

system prompt 的 `available_skills` 列表里有两个 COC 相关 skill（`coc-game-manager` 和 `coc-dice`），agent 容易自己推断"还缺一个 coc-keeper"并幻觉加载。coc-dice 已改 triggers 为空防止独立加载，但 agent 仍可能编造。

**识别：** 如果看到 `skill_view(name="coc-keeper")`，立即停止——这个 skill 不存在。跑团只需 `coc-game-manager` 一个。

**对策：** 如果 agent 提了 coc-keeper，忽略它，继续用 coc-game-manager。

### 建骨架剧本而非完整结构化（用户反弹最高的错误）

用户提供 .docx 源剧本后，agent 容易偷懒：只建 2-3 个节点骨架（导入 + 空 hub）、写几条线索、搁置探索地点的子节点。结果是 `scene_1` 的 `locations` 数组为空，9 个探索地点全丢。

**用户原话：** "你是不是还是要完整拉下剧本下来结构化？而不是做了个大概要" "源剧本转的scenario，是不是应该足够完整呢？其实就是源剧本的结构化展示"

**正确做法：** scenario.json 就是源剧本的完整结构化等价物——所有节点（包括每个探索子节点）、所有线索、所有 NPC 定义、时间追踪、战斗数据，一个不能少。

**自检清单（写完 scenario.json 后）：**
1. `game.py validate` 是否 0 errors？
2. 源剧本里的每个可到达地点都有对应节点？
3. 每条线索都在 `clues` 字典中定义？
4. 每个 NPC 都有顶层定义（`npcs` 字段）？
5. `synopsis` 是否存在？（🔴 必填）
6. 有时间压力的剧本是否有 `time_tracking`？
7. 探索 hub 的 `locations` 数组是否非空？

**对比：**
- ❌ 骨架：3 个节点、4 条线索、hub 无子节点
- ✅ 完整：18 个节点（含所有探索子节点）、26 条线索、7 个 NPC 顶层定义、完整时间追踪、战斗数据

### 角色库全局共享导致跨战役串角色

原本 `characters.json` 存在 `$HERMES_HOME/coc-data/` 根目录，所有战役共享同一份角色数据。跑完 A 战役切到 B 战役，角色 HP/SAN/道具全部带过去——上个战役的角色强行出现在下个故事里。

**修复：** `game.py` 新增 `get_characters_file()` 函数，有活跃战役时角色文件写入战役目录（`$HERMES_HOME/coc-data/<战役>/characters.json`）。**切换战役后必须先确认角色列表——新战役默认无角色。**

### 提到玩家角色不可能知道的地点（剧透未发现区域）

在描述完当前场景后，顺嘴提到同一建筑内其他未探索的房间、子区域、或者暗示某些地点藏有线索——这些都是剧透。玩家的角色（非玩家本人）只知道自己亲眼见过、或 NPC 明确告知的地方。

**典型翻车：** 从弗洛宅邸储藏室穿越传送门前，agent 说「楼上还有埃斯特尔的房间（弗洛已故女儿的祭坛），其中也藏有线索」——亨利根本没上过楼，弗洛也没提过任何女儿的房间或祭坛。他不知道楼上有这个房间。

**用户直接指出（2026-06-20 克鲁办公室）：** 「一次性公布所有信息破坏了探索节奏」
**用户直接指出（2026-06-21 弗洛宅邸）：** 「同时我怎么会知道楼上有祭坛？你又剧透了」——亨利刚从储藏室传送门回来，只在一层活动过，不可能知道二楼的房间或祭坛。哪怕 exits 字段里有 `loc_flowe_locked_room`，只要玩家没上去就不能提。

**规则：**
- `exits` 字段里的子节点（如 `loc_flowe_locked_room`、`loc_flowe_storage`）只能在玩家**亲自发现**或**NPC 明确告知**后才能提及
- 描述当前场景时不要把同一建筑内的其他房间当「已知信息」列出来
- 不要在切换场景时附带「你也可以去看看 X」——让玩家自己决定去哪
- **闭嘴规则：** 如果你不确定角色知不知道这件事，那就不要说。

### 战役结束后忘记清理 campaign-memory.md 的未解决事件

结局推进后，`campaign-memory.md` 的「已触发但未解决的事件」部分常残留旧条目（如「主编查尔斯·尚斯特拉姆加入调查，随亨利一同行动」）——这些事件在结局中已自然了结，但没人调 `note` 清理。

**规则：** 结局推进后，检查 campaign-memory.md 的所有未解决事件，逐条用 `game.py note event "已解决: ..."` 标记。不要让已完结的战役带着未清理的伏笔。

### KP 偏好栏全程为空

脑跑团全程没有调用 `game.py note kp_preference ...` 记录玩家风格，导致战役结束时偏好栏为空，跨会话复盘时丢失重要信息。

**规则：** 每 2-3 个场景后主动记一条。观察维度：探索偏好（地毯式/快节奏）、战斗偏好（硬刚/迂回/借力）、对话偏好（深度盘问/拿关键信息就走）、节奏偏好（长叙事/简洁推）。不用凑齐所有维度，有什么记什么。

### agent 一股脑把所有知道的东西都吐出来（信息倾泻）

resume 给了 agent 全剧本索引（18 节点、7 NPC、26 线索），agent 容易变成「导游模式」——恨不得把 node_index 和 key_npcs 全告诉玩家。

**症状：**
- 「你可以去书店、诊所、五金店、公园、沼泽、加油站……」
- NPC 对话一次性走完所有 key_replies 分支
- 主动透露 NPC 的 secrets/hint 字段
- 还没到高潮就暗示「仪式在 2 月 23 日晚上 11 点」

**根因：** agent 混淆了「守秘人的知识」和「玩家应该知道的事」。node_index 和 key_npcs 是给 agent 的**内部参考**，不是给玩家的**旅游手册**。

**三条铁律：**

1. **不主动报菜名** — 永远不说「你可以去 A/B/C/D」。最多在环境描写中自然提及一两个临近地点（如旅馆老板说「书店在隔壁那条街」），让玩家自己决定去哪。除非玩家明确问「这附近有什么地方可去」。

2. **NPC 只说被问到的** — key_replies 是预设答案库，不是对话脚本。玩家问 A 才答 A，不附带 B/C/D。NPC 不会主动把一生的故事讲给陌生人听。

3. **索引是工具，不是台词** — node_index/key_npcs 让 agent 在被问到时能快速回答「那是谁」「那里有什么」，而不是让 agent 找机会把这些信息倒出来。**守秘人知道整个模组，但玩家只应该看到眼前的场景。**

4. **一个回合只推进一个场景** — 禁止「两小时后…」「傍晚…」「第二天…」这种自主快进。玩家不主动说去下一个地点，agent 就停在当前场景。时间推进只在玩家完成当前场景探索后，由 `node` 命令的 `time_cost` 自然累加。agent 不能替玩家决定「去图书馆」「去找施旺森」「回报社」——这些是玩家的选择。

**典型症状：** agent 拿到 node_index 后，一回合内串起 4+ 个地点——图书馆→施旺森→回报社→克鲁办公室——全在一条消息里。「玩家一个字没说，一整天的调查走完了。」

`game.py node <id>` 最初只返回 `{switched_to, name, act}`，agent 切换场景后还得再调 `state` 才能拿到 NPC 台词和检定列表——两步操作才能开始叙事。

**修复：** `node_command()` 现在返回完整节点信息：`description`、`npcs[]`（含 opening + key_replies）、`checks[]`（含 on_failure）、`clues_available`（已筛选未发现线索，含完整 text）、`time_cost`、`next`、`exit_rule`、`exits`。agent 场景切换一步到位直接叙事。

### 战役完结后不清理 campaign-memory.md

玩家说「完团了」、「结束了」或剧情推进到结局节点后，agent 常常就此停手——但 `campaign-memory.md` 的「已触发但未解决的事件」里还挂着旧的未清理条目，KP 偏好栏也完全是空的。

**症状：** 结团审查发现 `campaign-memory.md` 里仍显示「查尔斯·尚斯特拉姆加入调查」（这是探索阶段的 NPC 状态，结局后应该清理），KP 偏好栏在整个战役期间从未被填写。

**正确做法（结团三步）：**

```bash
# 1. 清理遗留事件
python3 scripts/game.py note event "已解决: 查尔斯回报社，头版报道警方清剿"

# 2. 补记 KP 偏好
python3 scripts/game.py note kp_preference "玩家偏好快节奏，跳过次要地点直奔主线"

# 3. 最终审查
python3 scripts/game.py resume  # 确认一切干净
```

**纪律：** 不要在玩家说完团后就当没事了。主动调 `resume` 审查完整流程，参照 `references/post-campaign-review.md` 逐项检查。