# Getting Started — Full Walkthrough

> From scenario document to rolling dice. ~5 minutes.

## Step 1: Install the Skill

```bash
hermes skills install https://raw.githubusercontent.com/lzj124/hermes-coc-game-manager/main/SKILL.md
```

Verify:
```bash
hermes skills list | grep coc
```

---

## Step 2: Send Your Scenario

Start a chat with your Hermes agent and send the scenario document:

```
你：我有一份剧本，帮我跑

[attach: 短视的人.pdf]
```

The agent will:
1. Load the `coc-game-manager` skill
2. Create a campaign: `game.py init "短视的人"`
3. Read your document and convert it to structured JSON
4. Write `scenario.json`, validate it with `game.py save-scenario`
5. Report: "剧本已结构化，X 个节点，Y 条线索，校验通过"

**Supported formats:** `.docx`, `.pdf`, `.md`, `.txt`, or pasted text.

---

## Step 3: Create Your Investigator

The agent will prompt you. You can either:

**Option A — Let the agent roll:**
```
agent：需要我帮你掷属性吗？职业是什么？
你：私家侦探。帮我掷。
agent：[rolls STR/CON/DEX/…] 展示全卡，确认？
你：侦查换成70，其他OK。
```

**Option B — Roll yourself:**
```
你：STR 50 CON 55 DEX 60 APP 70 POW 50 SIZ 55 INT 65 EDU 60 LUK 50
    职业客户经理，技能：说服60 信用55 心理学45 话术50 英语60 驾驶45 图书馆40 侦查40 射击30 闪避35 斗殴35
```

The agent MUST show the full character sheet for your confirmation before proceeding.

---

## Step 4: Start Playing

The agent calls `game.py resume`, describes the opening scene, and waits.

```
agent：1920年2月21日。好友马里格尼从新奥尔良发来急件——记者盖文在调查
      庆典团体时离奇死亡，手里攥着一张黄色符号的纸片。

      火车驶入新奥尔良站。一个瘦高、神情疲惫的男人在出站口等你——
      查尔斯·尚斯特拉姆，《新奥尔良公报》主编。

      "阿什顿教授？感谢你能来。皮特是我手下最好的记者——他不可能是自杀。"
```

From here, just talk. Say what you do:

```
你：我问他盖文发现了什么
agent："他说其中一个庆典团体跟神秘事件扯上了关系。一周后他就死了。"
你：我要去盖文死的地方看看
agent：[calls game.py node loc_death_site] 图兰大学物理楼前…
```

---

## Step 5: Continuing a Campaign

Next session, just say:

```
你：继续跑团
```

The agent calls `resume` and auto-injects everything — your character sheet, discovered clues, NPC states, campaign journal, and the current scene.

---

## What the Agent Handles

| Task | How |
|------|-----|
| Dice rolls | `roll.py skill 70` → real Python random |
| Clue tracking | `game.py found clue_xxx` |
| Scene switching | `game.py node loc_xxx` |
| HP/SAN tracking | `game.py update char_001 san 45` |
| Decision logging | `game.py note decision "chose to..."` |
| Campaign memory | `campaign-memory.md` auto-maintained |

---

## Troubleshooting

**"scenario.json not found"**
→ Make sure you sent the scenario document to the agent. The agent creates the JSON from your doc.

**"No active campaign"**
→ Say "新开一个团" and send the scenario again, or check campaigns with `game.py campaigns`.

**Character has no skills**
→ The agent may have skipped filling in skills after `create`. Say "帮我补全角色技能" or provide them yourself.

**Dice rolls look fake**
→ All rolls go through `scripts/roll.py` with `random.randint(1,100)`. You can verify: `python3 ~/.hermes/skills/leisure/coc-game-manager/scripts/roll.py skill 70`

**Can't continue from last session**
→ Say "继续跑团". If the wrong campaign is active, check: `game.py campaigns` then `game.py switch "战役名"`.
