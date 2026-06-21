# COC scenario.json 设计原则

从「消失的邻居」和「短视的人」两个剧本的转换中提炼的设计规范。

## 四幕结构

所有剧本遵循 开场→发展(探索)→高潮→结局 四幕：

```
scene_0* (导入) → scene_1 (自由探索) → scene_2 (高潮) → scene_3* (结局分叉)
```

每幕在 `act` 字段标注：`"导入"` / `"探索"` / `"高潮"` / `"结局"`。

## 探索模式

简单剧本：线性节点推进（scene_1 → scene_2 → scene_3），直到高潮。

复杂剧本（如「短视的人」有 9 个可探索地点）：使用 hub 节点模式
```json
{
  "id": "scene_1",
  "act": "探索",
  "locations": ["loc_margaret", "loc_bookstore", "loc_clinic", ...],
  "exit_rule": "找到沃恩住处并确认仪式信息后推进"
}
```
每个 `loc_*` 节点独立包含完整的 description/checks/clues。

## 线索系统

- 每个节点指定 `clues_available`：此地点可发现的线索 ID 列表
- 全局 `clues` 字典存储完整线索文本
- 使用时：`game.py found clue_xxx` 标记已获取
- agent 通过 state 的 `pending_clues` 知道还有哪些未发现

## NPC 设计

每个 NPC 应包含：
```json
{
  "name": "角色名",
  "role": "身份（一句话）",
  "attitude": "对调查员的态度",
  "secret": "角色秘密/隐藏动机",
  "weakness": "弱点/突破口（可选，如'提及已故丈夫'）",
  "flip_condition": "倒戈条件（可选，如'展示专业性使其相信你比沃恩可靠'）",
  "stats": "HP和关键技能简写（可选）"
}
```

战斗 NPC 额外加 `combat` 块：
```json
{
  "name": "四维蠕虫",
  "stats": "HP15, STR70, DEX50, ...",
  "armor": 0,
  "attacks": ["攻击名 命中率% 伤害+特效"],
  "abilities": ["特殊能力列表"],
  "weaknesses": ["弱点列表"],
  "san_loss": "0/1d6"
}
```

## 分支结局

用独立节点处理多结局：
- scene_3a 好结局、scene_3b 普通、scene_3c 坏结局
- scene_final 统一尾声
- `effects` 字段写 SAN/HP 变化、道具得失等

## 准备阶段 checklist

1. 阅读完整剧本
2. 识别四幕边界（哪些段落是导入/探索/高潮/结局）
3. 提取每个场景的：location, description, NPCs, checks, clues
4. 提取全局线索字典（所有 clue_id → 文本）
5. 整理 SAN 检定点（scene + trigger + check 值）
6. 如有战斗：提取怪物数据和弱点
7. 写入 $HERMES_HOME/coc-data/scenario.json
8. `game.py node scene_0a` 初始化

## 参考实现

- `$HERMES_HOME/coc-data/scenario.json` — 当前剧本（「短视的人」完整示例）
- `references/data-structure.md` — JSON 数据 schema