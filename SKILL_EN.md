---
name: coc-game-manager
description: COC TRPG Keeper — single entry point. Manage characters, clues, scene progression, dice checks, cross-session memory, multi-campaign isolation. Built-in real dice, zero external deps.
triggers: 跑团, COC, 克苏鲁, 守秘人, KP, 创建角色, 调查员, 车卡, 剧本大纲, 开始游戏, 继续跑团, 检定, SAN, HP, NPC, 线索, 道具, 模组, 剧本, scenario, cthulhu, call of cthulhu, keeper, investigator, rpg, tabletop
---
[中文版](SKILL.md)

# COC Game Manager — Single Entry Point for CoC Sessions

> ⚠️ **This is the ONLY skill you need for CoC sessions.** Dice are built-in via `scripts/roll.py`. Zero external dependencies.

## Design Philosophy

**Inspired by Claude Code's memory architecture:**

1. **Structured over free-form** — clues, checks, NPCs all have fixed schemas
2. **Index always loaded, content on demand** — compact summary injected at session start, details expanded when needed
3. **Never store derivable data** — don't duplicate scenario.json content in state
4. **Force injection at startup** — the agent doesn't "remember" to check state; `resume` auto-injects

---

## Architecture

```
$HERMES_HOME/coc-data/
├── active_campaign          ← currently active campaign name
├── <CampaignA>/
│   ├── scenario.json
│   ├── state.json
│   ├── characters.json      ← campaign-isolated character roster
│   └── campaign-memory.md
└── <CampaignB>/
    ├── scenario.json
    ├── characters.json
    └── ...
```

**Static layer** — `scenario.json` (scenario structure), `characters.json` (campaign roster)
**Dynamic layer** — `state.json` (runtime progress), `campaign-memory.md` (cross-session notes)
**Validation** — `game.py validate`

---

## New Session Startup (MOST IMPORTANT)

```bash
python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/game.py resume
```

**The agent MUST call `resume` as the very first action in every new session, before the first reply.**

`resume` returns three layers:
- **Global index** — `node_index` (all node names/acts/locations, **no content summaries**), `key_npcs` (all NPC names/roles/attitudes, **no secrets**), `timeline`, `synopsis`, `act_order`
- **Current node** — NPC openings, available checks, pending clues
- **Runtime state** — clue progress, character HP/SAN, recent checks, campaign notes

The agent uses the global index to answer "what else is there?" and "who is that?" — but **doesn't know what's inside each location or what NPC secrets are**. Only when the player goes to a location and calls `node` does the agent get full scene descriptions and NPC dialogue. **The index is a map, not a walkthrough.**

### New Scenario — Full Workflow

```bash
# 1. Create campaign
game.py init "Scenario Name"

# 2. Agent writes JSON → validates and imports via save-scenario
game.py save-scenario /path/to/written/scenario.json

# 3. Create character (new campaign = new character)
game.py create "Name" "Occupation" HP MHP SAN MSAN
# Then use execute_code to edit characters.json and fill in attributes/skills

# 4. After validation, start
game.py node scene_0a
```

**⚠️ After creating a character, MUST show the full character sheet to the player before proceeding.** Call `game.py get <id>` and display it for player confirmation.

**⚠️ Never write JSON directly to the campaign directory — use write_file to a temp path first, then save-scenario to validate and import.**

### Switching Campaigns

```bash
game.py campaigns                  # list all campaigns
game.py switch "CampaignName"      # switch active
```

---

## Game Loop

```
New session
  │
  ▼
game.py resume          ← global index + current node details (REQUIRED first step)
  │                     resume provides: node_index/key_npcs/timeline/synopsis
  │                     current node: NPC lines + check list
  ▼
Scene description        ← use current node's description, mention NPCs present
  │                     ⚠️ After mentioning NPCs, STOP and wait for player action
  │                     ⚠️ NEVER monologue NPC dialogue unprompted
  ▼
Player action ──→ Scene change?
  │               ├─ Yes → game.py node <new_node>
  │               │        Returns full node: description/NPCs/checks/clues
  │               │        → describe environment → wait for player
  │               └─ No → continue
  │
  ▼
Player action ──→ Check needed?
  │               ├─ Yes → roll.py skill <value from characters.json>
  │               │        → game.py log → narrate result
  │               └─ No → narrate directly
  │
  ▼
Clue discovered? ──→ game.py found <clue_id>
  │
  ▼
Key decision? ──→ game.py note <type> <text>
  │
  ▼
Continue loop
```

> `game.py state` is only called when you need the FULL runtime state (all clue progress, character inventory, etc.). Not needed every turn.

---

## Command Reference

### State Machine (Core)

| Command | Purpose | When |
|---------|---------|------|
| `resume` | Session startup summary | **REQUIRED first step every new session** |
| `state` | Full runtime state | When you need all clue progress / inventory / check history |
| `node <id>` | Switch to scenario node | Scene change — **returns complete node info**, no need to call state afterward |
| `found <clue_id>` | Mark clue discovered | Immediately after player obtains a clue |
| `log <char> <check> <roll> <skill>` | Record a check | After every dice roll |
| `note <type> <text>` | Write campaign note | **REQUIRED** after every key decision |
| `validate` | Validate scenario.json | After writing/editing scenario |
| `reset` | Clear campaign runtime | Re-run same scenario |

### Campaign Management

| Command | Purpose |
|---------|---------|
| `init <name>` | Create new campaign directory, set active |
| `switch <name>` | Switch active campaign |
| `campaigns` | List all campaigns |

### Character Management

| Command | Purpose |
|---------|---------|
| `create <name> <occupation> <HP> <MHP> <SAN> <MSAN>` | Create character |
| `get <char_id>` | View character |
| `list` | List all characters |
| `update <char_id> <field> <value>` | Update HP/SAN/status |
| `add-item <char_id> <item> [type] [count]` | Add inventory item |
| `add-clue <char_id> <clue_text>` | Add personal clue to character |

### Campaign Note Types

| type | Meaning | Example |
|------|---------|---------|
| `decision` | Major player choice | "Chose to kick the old man as bait for time" |
| `npc_state` | NPC current state | "Vaughan has been taken by police" |
| `event` | Triggered but unresolved event | "Star Spawn not destroyed, may reappear" |
| `kp_preference` | Keeper style preference | "Player prefers fast pace, less exploration" |

**Discipline:** Call `note` after every key decision. Don't rely on mental memory.

---

## Keeper Boundaries (MUST FOLLOW)

**NEVER reveal to players:** `node.notes`, NPC `secret`, full `pending_clues` text, `san_checks`/`combat` data, `exit_rule` text.

**NPC discipline:** An NPC can only speak what they themselves know.

**Check display discipline:** Show the PLAYER'S skill value in parentheses, NOT the scenario difficulty. ✅ "Spot Hidden — your 70" ❌ "Spot Hidden (55)"

**Player preference discipline:** Style choices (showing dice numbers, narration detail level) are NOT hardcoded in the skill. Every group/player is different — agree on preferences with the player at campaign start. The skill governs process rules, not style.

**Pacing discipline:**
- Push forward on player action, don't double-confirm. Don't ask "are you sure?" twice
- Failed check ≠ dead end — provide alternative paths (cost, detour, new discovery)
- Combat: declare actions → roll → resolve damage → narrate
- **Critical failures MUST deal damage:** combat skill crit fails (Brawl, Dodge, Firearms) need both narrative AND mechanical consequences. Fall damage 1D3, weapon break, or free counter-attack for the enemy. Narrative alone is insufficient.
- **description is not a script:** The `description` field often contains multiple embedded NPC dialogue snippets. These are the Keeper's material library — don't dump them all at once. Use only the environment/atmosphere portion to open the scene. NPC dialogue comes one piece at a time, matching what the player actually asks about.

**Narrative pacing (anti-info-dump):**

Four iron rules — resume gives the agent the full scenario index, but that's the Keeper's internal reference, not the player's travel guide:
1. **Don't list destinations** — never say "you can go to A/B/C/D". At most, naturally mention 1-2 nearby locations in environment description. Unless the player explicitly asks "what's around here"
2. **NPCs only answer what's asked** — key_replies is a preset answer bank, not a dialogue script. Player asks A, answer A. Don't append B/C/D
3. **Index is a tool, not a script** — use node_index/key_npcs to answer questions quickly when asked, don't fish for opportunities to dump info
4. **One scene per turn** — forbid "two hours later..." / "the next day..." auto-fast-forward. If the player doesn't say they're going somewhere, stay in the current scene. The agent does NOT decide the player's schedule

**Tool discipline:** Check existing tools/skills before suggesting new installs. Don't default to complex solutions.

**exits field handling:** The `exits` field from `node` contains sub-node entrances within the same building/scene. These sub-nodes can ONLY be mentioned after the player character **sees the entrance with their own eyes** or an **NPC explicitly tells them about it**. Doors/rooms/passages the current NPC hasn't mentioned and the player hasn't discovered — the Keeper must not list them. When switching scenes via an exit, just `node <that_sub_node>` — don't add "or you could also go to X".

---

## Dice Checks

**Don't load coc-dice skill. Use the built-in roll.py:**

```bash
python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/roll.py skill <player_skill_value>
python3 $HERMES_HOME/skills/leisure/coc-game-manager/scripts/roll.py d100
```

**⚠️ roll.py doesn't support multi-dice syntax (`2d6`, `3d6` will throw `Unknown command`).** For damage rolls, use `execute_code` with Python's `random.randint(1,6)`.

---

## Post-Campaign Review

When the player says "campaign's over", "we're done", or the story reaches the ending node, the agent MUST do these five steps:

**1. Read final state** → `game.py resume`

**2. Update character stats** → Based on ending effects (SAN recovery, HP changes, items), sync with `game.py update`:
```bash
game.py update char_001 san <final_value>
game.py update char_001 hp <final_value>
```

**3. Record NPC states** → `game.py note npc_state` for each key NPC: who survived, who died, who escaped, attitude changes.

**4. Clean up unresolved events** → `game.py note event "Resolved: ..."` for every item in the "triggered but unresolved" list in campaign-memory.md.

**5. Fill KP preferences** → If the KP preferences section is empty, add at least one observed player style from this campaign.

Full review checklist → `references/post-campaign-review.md`

---

## References

| File | Content |
|------|---------|
| `references/scenario-schema.md` | Scenario JSON field specification |
| `references/scenario-design.md` | Four-act structure, clue system, NPC design |
| `references/scenario-from-document.md` | Building full scenario.json from .doc/.docx source modules |
| `references/resume-output.md` | Resume command output format |
| `references/pitfalls.md` | Fatal error checklist — **read before every session** |
| `references/post-campaign-review.md` | Campaign review checklist |
| `references/data-structure.md` | Character/NPC/item/clue JSON schemas |
| `references/story-outline-template.md` | Story outline template |
| `scripts/game.py` | Main program (no external deps) |
| `scripts/roll.py` | COC 7th edition real dice (critical success/failure) |
