# COC Game Manager — Hermes Agent Skill

> 🎲 AI as Keeper, Python dice, structured scenario engine.

[中文](#coc-跑团助手)

## What

A **Hermes Agent skill** for running **Call of Cthulhu (CoC)** tabletop RPG sessions. You provide the scenario, the AI acts as Keeper, guiding your investigator through the story. **Dice are real Python `random.randint`, not AI hallucination.**

## Install

```bash
# Option 1: Hermes skill registry
hermes skills install coc-game-manager

# Option 2: Direct from GitHub
hermes skills install https://raw.githubusercontent.com/lzj124/hermes-coc-game-manager/main/SKILL.md

# Option 3: Manual clone
git clone https://github.com/lzj124/hermes-coc-game-manager.git ~/.hermes/skills/leisure/coc-game-manager
```

All data stored in `$HERMES_HOME/coc-data/`. Scripts are self-contained — zero external dependencies.

## Why

Generic AI GMing has two fatal flaws:

1. **No memory** — forgets clues from Act 1 by Act 3, NPC dialogue contradicts itself
2. **Fake dice** — "You rolled a 35 — success!" (AI made it up)

This system fixes both:

- A **structured scenario file** (JSON) defining every scene, NPC, clue, and check
- A **real dice roller** (Python `random.randint`) — success/failure is real

## Quick Start

```
You: Create a private investigator character
AI: Got it. What's your stat line? Let me file the character sheet.

You: *rolls stats*
AI: Recorded. Starting "The Short-Sighted" —

You: I knock on Professor Vaughan's door
AI: (reads the scene description, Vaughan's dialogue, available checks from the scenario...)
```

You just talk. The AI handles scenarios, dice, character state, and memory.

## What a Scenario Looks Like

Scenarios aren't natural language — they're structured data. What's behind a door, what an NPC knows, what happens on success vs. failure — all pre-written:

```json
"Vaughan's Doorstep": {
  "description": "17 Miller Street. Porch light on. A ring of copper coils in the yard.",
  "npcs": [{
    "name": "Vaughan",
    "opening": "Who are you? It's late.",
    "secret": "Running a dimensional experiment in the basement. Ritual at 3:17 AM Oct 25."
  }],
  "checks": [{
    "name": "Fast Talk to convince Vaughan",
    "skill": 55,
    "info": "Vaughan relents, lets you in — living room only",
    "on_failure": "He sees through you. Slams the door."
  }]
}
```

With this data the AI:
- Only speaks lines the NPC knows
- Only shows what the investigator can see
- Rolls real dice for the Fast Talk check
- Never reveals Vaughan's `secret` — the player must discover it

## Features

| Feature | Description |
|---------|-------------|
| **Character creation** | Track attributes, skills, inventory, HP/SAN/MP |
| **Scenario management** | Convert PDF/TXT/Markdown modules to structured JSON |
| **Real dice** | Python `random.randint(1,100)` with COC 7th edition critical rules |
| **Multi-session** | Close and continue tomorrow — `resume` injects full progress |
| **Scenario validation** | `validate` catches missing failure paths and clue gaps |
| **Campaign isolation** | Separate directories per campaign, no cross-contamination |
| **Multiple endings** | Branch to different endings based on player choices |
| **Campaign journal** | Auto-records key decisions, NPC state changes, foreshadowed events |
| **Free exploration** | Multi-location sandbox with no fixed order |

## vs. Generic AI GMing

| | Generic AI | This System |
|------|------|------|
| Dice | "You rolled 35 — success!" (maybe fake) | Python `random.randint(1,100)` real random |
| Memory | Forgets earlier scenes | `resume` auto-injects full session state |
| Scenario | AI improvises, goes off-rails | Structured JSON with success/failure for every check |
| NPCs | May leak others' secrets | Only speaks what they know |
| Persistence | Gone when you close the tab | Permanent storage in `$HERMES_HOME/coc-data/` |

## Design

Inspired by Claude Code's memory architecture. Four principles:

1. **Structured over free-form** — clues, checks, NPCs all have fixed schemas
2. **Index always loaded, content on demand** — compact summary injected at session start
3. **Never store derivable data** — don't duplicate what's already in the scenario
4. **Force injection at startup** — AI doesn't "remember" to check state; the system does

## Use Cases

- 🎲 Solo CoC player without a Keeper
- 📝 Module authors testing custom scenarios
- 🔧 Developers studying how structured data constrains AI agents

---

# COC 跑团助手

> 🎲 AI 当 KP，Python 掷真骰子，结构化剧本防剧透。

## 这是什么

**Hermes Agent skill**，帮你跑 COC 桌面角色扮演游戏。AI 当守秘人，骰子是 Python 真随机。

## 安装

```bash
hermes skills install coc-game-manager
# 或
hermes skills install https://raw.githubusercontent.com/lzj124/hermes-coc-game-manager/main/SKILL.md
# 或
git clone https://github.com/lzj124/hermes-coc-game-manager.git ~/.hermes/skills/leisure/coc-game-manager
```

数据存 `$HERMES_HOME/coc-data/`，脚本自包含零外部依赖。

## 为什么

普通 AI 跑团两大问题：没记性 + 假骰子。本系统用结构化 JSON 剧本 + Python 真随机骰子解决。

## 功能

| 功能 | 说明 |
|------|------|
| 创建角色 | 属性/技能/物品，跟踪 HP/SAN/MP |
| 结构化剧本 | PDF/TXT/Markdown 转 JSON |
| 真骰子 | `random.randint(1,100)`，COC 7版大成功大失败 |
| 跨天续跑 | `resume` 自动注入完整进度 |
| 战役隔离 | 多战役独立目录互不串 |
| 多结局 | 根据选择分叉 |
| 战役笔记 | 自动记录决策/NPC状态/伏笔 |
| 自由探索 | 多地点不限制顺序 |

## 设计理念

1. 结构化优于自由文本
2. 索引常驻 + 内容按需
3. 禁止存可推导数据
4. 启动时强制注入

---

*Scenario JSON schema: `references/scenario-schema.md`*
