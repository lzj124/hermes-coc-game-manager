# COC游戏数据结构

## 数据文件位置
所有数据存储在 `$HERMES_HOME/coc-data/` 目录下：

**战役目录（隔离）：**
```
$HERMES_HOME/coc-data/<战役名>/
├── scenario.json       ← 剧本结构（静态）
├── state.json          ← 运行时进度（动态）
├── characters.json     ← 本战役调查员（战役隔离）
└── campaign-memory.md  ← 跨会话笔记
```

**共享数据（跨战役）：**
- `$HERMES_HOME/coc-data/characters.json` — 向后兼容：无活跃战役时的角色存储
- `$HERMES_HOME/coc-data/items.json` — 通用道具

## 调查员角色结构 (characters.json)

```json
{
  "char_001": {
    "id": "char_001",
    "name": "张伟",
    "occupation": "私家侦探",
    "attributes": {
      "str": 60, "con": 55, "siz": 50, "dex": 70,
      "app": 45, "int": 75, "pow": 50, "edu": 65
    },
    "skills": {
      "侦查": 65, "聆听": 55, "图书馆": 50,
      "心理学": 45, "格斗": 30, "射击": 25
    },
    "san": 80, "max_san": 99,
    "hp": 10, "max_hp": 12,
    "mp": 15, "max_mp": 15,
    "db": "0", "build": 0, "mov": 8,
    "status": "正常",
    "inventory": [
      {"name": ".38左轮手枪", "type": "武器", "count": 1, "damage": "1d10"},
      {"name": "笔记本", "type": "道具", "count": 1}
    ],
    "clues": [
      {"text": "老宅地下室有奇怪的气味", "acquired": "2026-02-14T10:30:00"}
    ],
    "notes": "对这个案件感到不安"
  }
}
```

## NPC结构 (npcs.json)

```json
{
  "npc_001": {
    "id": "npc_001",
    "name": "王警官",
    "role": "警察",
    "location": "警察局",
    "attitude": "友好",
    "description": "中年警察，经验丰富",
    "important": true,
    "secrets": ["三年前这起案件被秘密结案"],
    "relations": {"char_001": "认识"}
  }
}
```

## 道具结构 (items.json)

```json
{
  "item_001": {
    "id": "item_001",
    "name": ".38左轮手枪",
    "type": "武器",
    "damage": "1d10",
    "range": "15",
    "attacks": 1,
    "value": 150,
    "description": "标准的警用手枪"
  }
}
```

## 线索结构 (clues.json)

```json
{
  "clue_001": {
    "id": "clue_001",
    "text": "地下室墙壁上有古怪的符文",
    "location": "老宅地下室",
    "related_npc": "npc_001",
    "importance": "高",
    "solved": false
  }
}
```

## 状态标记

角色状态可选值：
- `正常` - 无异常
- `受伤` - HP低于最大值
- `重伤` - HP低于最大值的一半
- `濒死` - HP为0或1
- `疯狂` - 进入临时疯狂状态
- `不定型疯狂` - 长期疯狂
- `被束缚` - 无法行动
- `中毒` - 特殊状态