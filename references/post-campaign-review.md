# 跑团审查清单

战役进行中或完结后，用户说"检查下流程""看看有没有问题"时执行。

## 中期检查（游戏进行中）

用户说"看看流程"但游戏还在跑时，聚焦五个必查项：

### 1. 读取状态
```bash
python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/game.py resume
```

### 2. 五个必查项

| 检查项 | 怎么查 | 红灯信号 |
|--------|--------|---------|
| auto 线索遗漏 | 对比已过节点的 `delivery: auto` 与 `discovered_clues` | scene_1 过了但 `clue_vacation_letter` 没标记 |
| 检定记录 | `check_history` 是否与经历场景匹配 | 过了 3 个节点 0 次检定 |
| campaign-memory | 文件是否存在 + 最后更新时间 | 跑了一阵还没生成 |
| note 调用 | 关键决策/场景切换后是否调了 note | NPC 加入/重要发现后没记 |
| inspect 线索 | 当前节点 `delivery: inspect` 的线索，玩家是否有观察机会 | NPC 有明显物品但没提示 |

### 3. 输出
简洁，只报红灯。黄灯（如 inspect 线索玩家没问）标注即可。

---

## 结案检查（战役完结后）

战役完结后（玩家说"完团了"、"结束了"、或剧情推进到结局节点后），执行完整审查。

## 审查步骤

### 1. 读取完整状态
```bash
python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/game.py resume
```

逐项检查三层信息。

### 2. 线索覆盖审计

对比 `state.json` 的 `discovered_clues` 与 `scenario.json` 的 `clues` 字典：

- 列出所有缺失的 clue_id
- 标注哪些是**剧情关键**（缺少会导致逻辑断裂）
- 标注哪些是**探索遗漏**（玩家没去该地点）
- 标注哪些是**KP内部信息**（如 `clue_carcosa_threat`，不该给玩家）
- 标注哪些是**通过其他渠道间接获取**（如从NPC处得知而非现场发现）

### 3. 场景覆盖审计

对比 `discovered_clues` 中的 `source` 字段与 `node_index`：

- 列出**完全未访问**的节点
- 判断是否玩家主动跳过（快节奏偏好）还是 agent 没提供机会

### 4. Campaign Memory 清理

检查 `campaign-memory.md` 的 "已触发但未解决的事件" 部分：

- 结局后所有遗留事件都应用 `game.py note event "已解决: ..."` 标记清掉
- 典型遗漏：NPC陪同状态、未处理的伏笔

```bash
# 清理示例
python3 scripts/game.py note event "查尔斯·尚斯特拉姆调查结束后回报社，头版报道警方清剿行动"
```

### 5. KP 偏好检查

检查 `campaign-memory.md` 的 "KP 偏好" 部分是否为空。

如果整个战役下来都没记过，说明 agent 没有在跑团过程中主动捕捉玩家风格。应补记：

- 探索偏好（地毯式 vs 快节奏直奔主线）
- 战斗偏好（正面硬刚 vs 迂回策略 vs 寻求NPC/警方协助）
- 对话偏好（深度盘问NPC vs 拿关键信息就走）
- 节奏偏好（喜欢长段叙事 vs 简洁推进）

```bash
python3 scripts/game.py note kp_preference "玩家偏好快节奏推进，倾向警方/NPC协助而非单打独斗"
```

### 6. 角色状态验证

- HP/SAN 是否与经过的场景匹配（传送门消耗、战斗伤害、SAN损失）
- MP 消耗是否被追踪（穿越传送门、法术使用）
- 道具增减是否记录

### 7. 结局分支追踪

- 确认走了哪个结局分支（A/B/C/D）
- 验证 SAN 恢复/奖励是否已结算
- 若有多分支可能，标注实际选中的路径

## 输出格式

审查报告分三档：

| 级别 | 含义 | 示例 |
|------|------|------|
| 🔴 流程缺陷 | 违反KP纪律、遗漏必要操作、系统错误 | 场景切换未调 node |
| 🟡 次要问题 | 遗漏但不影响剧情推进 | 可选地点未访问、MP追踪不准 |
| ✅ 做得好的 | 正确执行的操作 | 检定技能值无误、无剧透 |

每个问题附带：问题描述 + 影响评估 + 修复建议（如果还能修）。
