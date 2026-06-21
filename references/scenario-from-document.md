# 从原始文档构建 scenario.json

用户提供 .doc/.docx 剧本文件时，必须构建完整 scenario.json。不能因为剧本复杂就跳过。

## 核心原则

**scenario.json 就是源剧本的完整结构化等价物。** 不是摘要、不是骨架、不是"先做几个节点后面再补"。源剧本里的每个可到达地点、每条线索、每个 NPC、每段对话、每个检定、每个战斗数据——都必须出现在 JSON 中。信息丢失 = 错误。

**用户原话：** "源剧本转的scenario，是不是应该足够完整呢？其实就是源剧本的结构化展示"

自检：写完 scenario.json 后问自己——"如果我只拿着这个 JSON，不看源文档，能跑完整场团吗？" 不能 = 不合格。

## 流程

### 1. 提取文本

```bash
textutil -convert txt -stdout '/path/to/document.docx'
```

### 2. 分析剧本结构

通读全文，提取：

| 要素 | 映射到 JSON |
|------|-------------|
| 故事概要 | `synopsis`（🔴必填 — 读完后用自己的话写3-5句） |
| 时间线/截止日期 | `time_tracking` |
| 可到达地点 | `nodes`（hub 的 `locations` 数组） |
| 地点内的 NPC + 对话 | 节点 `npcs[]` |
| 需要检定的点 | 节点 `checks[]` |
| 可获取的线索/信息 | `clues` 字典 |
| SAN 检定触发 | `san_checks[]` |
| 战斗数据 | `combat` 字典 |
| 关键 NPC | `npcs` 字典 |

### 3. 节点设计

- **线性剧本**：每个场景一个独立节点，`next` 指向下一节点
- **探索型剧本**（多个地点可自由选择）：使用 **hub 节点**
  - hub 的 `locations` 数组列出所有子节点 ID
  - 每个子节点 `next: null`（探索无固定顺序）
  - hub 的 `exit_rule` 定义何时推进到高潮

### 4. JSON 陷阱

**中文引号问题**：描述文本中的 ASCII 双引号 `"` 会破坏 JSON 解析。修复方式：
1. 将中文语境的内引号替换为全角引号 `「」`
2. 或者确保所有内引号正确转义为 `\"`

**验证修复**：
```bash
python3 -c "import json; json.load(open('scenario.json'))"
```

### 5. 校验 + 重置状态

```bash
# 先自检完整性
python3 -c "
import json; s=json.load(open('scenario.json'))
print(f'nodes: {len(s.get(\"nodes\",{}))} | clues: {len(s.get(\"clues\",{}))} | npcs: {len(s.get(\"npcs\",{}))}')
print(f'synopsis: {\"✅\" if s.get(\"synopsis\") else \"❌ 缺失\"}  ')
print(f'time_tracking: {\"✅\" if s.get(\"time_tracking\") else \"⚠️ 缺失\"}  ')
hub = [nid for nid,nd in s['nodes'].items() if 'locations' in nd]
for h in hub:
    locs = s['nodes'][h]['locations']
    missing = [l for l in locs if l not in s['nodes']]
    if missing: print(f'❌ {h}: 引用不存在的子节点: {missing}')
    elif not locs: print(f'❌ {h}: locations 为空')
    else: print(f'✅ {h}: {len(locs)} 个子节点全部存在')
"

# 正式校验
python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/game.py validate

# 通过后重置状态（可选）
python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/game.py reset
```

### 校验必须通过

- 0 errors 才算可用
- warnings（如缺少 time_tracking）可接受但不理想
- **特别关注：** hub 节点的 `locations` 数组是否为空？所有子节点引用是否存在于 `nodes` 中？

## 写 JSON 时的纪律（每条都必须遵守）

- **每个场景必须有完整的 `description`** — 不是一句话摘要，而是 agent 可以直接念给玩家的环境氛围描述
- **每个检定必须有 `on_failure`** — 不能只写成功结果，agent 不能在失败时现场编
- **每条线索必须有 `text`** — agent 需要念给玩家的完整文本，不是"关于XX的信息"
- **NPC 的 `opening` 必填** — NPC 见到调查员说的第一句话
- **`synopsis` 用自己的话写** — 不是复制源剧本的"导入简介"，而是守秘人读完整个模组后的概括
- **线索 delivery 准确** — `auto`(场景自动获得)、`inspect`(需侦查/检定)、`document`(读到的文件)、`npc_dialogue`(NPC口中说出)
- **中文引号** — 描述文本中的双引号全部替换为全角「」，避免破坏 JSON

## 🔴 常见错误：骨架式 scenario

**最常见也最致命的错误：** 建了个只有 2-3 个节点的骨架，hub 的 `locations` 数组为空，线索只写了几条。

**自查方法（建完 scenario.json 后必须过）：**

| 检查项 | 方法 |
|--------|------|
| 源文档所有地点都对应一个 node | grep 源文档中地点名 → 对照 nodes 列表 |
| hub 的 `locations` 不为空 | 直接看 JSON，不能是 `[]` |
| 所有提及的线索都在 clues 字典中 | `grep -c clue_ scenario.json` 对照源文档线索数 |
| 所有 NPC 有顶层定义 | `npcs` 字典不为 `{}` |
| 每个检定有 on_failure | `grep -c on_failure scenario.json` 对照 checks 数 |
| validate 0 errors | `game.py validate` |

**记住：** scenario.json 是源剧本的完整结构化等价物。源剧本里有 10 个地点，scenario.json 里就有 10+ 个节点。源剧本里 20+ 条可发现信息，clues 里就有 20+ 条。不能偷懒做成大概。

## 参考案例

本 session 从「1920黄衣之王改 .docx」构建了 565 行的 scenario.json：
- 1 个导入节点 → 1 个探索 hub（11 个子节点） → 1 个高潮节点 → 1 个结局节点
- 21 条线索，5 个 NPC
- 时间追踪：2月21日 → 2月23日23:00 截止
