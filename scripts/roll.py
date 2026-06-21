#!/usr/bin/env python3
"""
COC 7th Edition Dice Roller
支持D100检定、大成功、大失败、成功等级判定
"""

import random
import sys
import json

def roll_d100():
    """投掷D100（1-100）"""
    return random.randint(1, 100)

def check_success(roll_value, skill_value):
    """检定成功等级"""
    critical_success = roll_value == 1 or (skill_value >= 50 and roll_value <= 5)

    critical_failure = (
        roll_value == 100 or
        (skill_value < 50 and roll_value >= 96) or
        (skill_value < 50 and roll_value >= skill_value * 2)
    )

    if critical_success:
        return {"level": "critical_success", "name": "大成功", "description": "极好的结果，可能带来额外奖励"}
    elif critical_failure:
        return {"level": "critical_failure", "name": "大失败", "description": "灾难性的失败"}
    elif roll_value <= skill_value // 2:
        return {"level": "hard_success", "name": "极难成功", "description": "出色的表现"}
    elif roll_value <= skill_value:
        return {"level": "success", "name": "成功", "description": "达成目标"}
    else:
        return {"level": "failure", "name": "失败", "description": "未达成目标"}

def roll_skill(skill_value):
    """技能检定（D100）"""
    roll = roll_d100()
    success = check_success(roll, skill_value)
    return {
        "roll": roll,
        "skill": skill_value,
        "success_level": success["level"],
        "success_name": success["name"],
        "success_desc": success["description"]
    }

def roll_die(sides, count=1):
    """投掷指定面数的骰子"""
    rolls = [random.randint(1, sides) for _ in range(count)]
    return {"sides": sides, "count": count, "rolls": rolls, "total": sum(rolls)}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: roll.py <command> [args]"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    command = sys.argv[1]

    if command == "skill":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Usage: roll.py skill <skill_value>"}, ensure_ascii=False))
            sys.exit(1)
        skill_value = int(sys.argv[2])
        result = roll_skill(skill_value)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == "d100":
        result = {"roll": roll_d100()}
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == "die":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Usage: roll.py die <sides> [count]"}, ensure_ascii=False))
            sys.exit(1)
        sides = int(sys.argv[2])
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        result = roll_die(sides, count)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        print(json.dumps({"error": f"Unknown command: {command}"}, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()