# 从模组文档构建 scenario.json

## 输入来源

用户发来 `.doc` / `.docx` / `.pdf` / `.md` 格式的 COC 模组原文。

## 步骤

1. **提取文本** — 用 `textutil -convert txt -stdout`（macOS）或相应工具读取全文
2. **识别结构** — 按四幕结构（导入→发展→高潮→结局）拆解场景节点
3. **提取机械要素**：
   - SAN 检定：触发条件 + 成功/失败扣除值（如 `1/1d10`）
   - 技能检定：技能名 + 难度值 + 成功/失败后果
   - 战斗数据：怪物属性（STR/CON/SIZ/HP/护甲）、攻击方式（命中率/伤害）、特殊能力
   - 线索：文本内容 + 交付方式（auto/inspect/document/npc_dialogue）
4. **编写 nodes** — 每个场景含 `description`（agent 直接叙述）、`checks`（含 `on_failure`）、`exit_rule`
5. **编写 combat** — 怪物属性转换：原文 STR 14 → `"STR 80"`（原始值×5+10），CON/SIZ 同理
6. **编写 san_checks** — 集中列出所有 SAN 检定点
7. **校验** — `python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/game.py validate`
8. **重置状态** — `python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/game.py node scene_1a`

## 常见模组特性处理

### 无传统线索的遭遇型剧本
像《惊惧坠落》这类纯遭遇模组，没有侦探式线索。`clues` 只记录关键事件标记（如 "星之精出现"），作为 `found` 追踪用。

### 梦境/幻觉结局
如果结局揭示一切是梦境：将结局节点的 `effects.san_change` 设为扣除值，`description` 写清楚回归现实的叙事转折。

### 单人模组的 NPC 处理
如果模组说"其他调查员应当表现得…"但只有1个PC，直接忽略多人设定。

## 校验通过标准

- ✅ 0 errors
- ⚠️ warnings 可接受（如缺少 time_tracking，短剧本不需要）
