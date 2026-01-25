---
applyTo: '**'
description: This file contains mandatory instructions for handling user requests, including a skill index for debugging tasks.
---

# Instructions

## 🚨 MANDATORY: Check Skill Index Before Every Task

**STOP. Before ANY action, scan the user's message against this skill index.**

### Skill Index

| Skill | Trigger Words | Action |
|-------|---------------|--------|
| **python-debugger** | bug, debug, trace, error, exception, broken, not working, wrong, incorrect, failing, fails, investigate, unexpected, why doesn't, why does, crash, issue | Read `.github/skills/debugger/SKILL.md` then use debugger tools IMMEDIATELY |

### Quick Trigger Word Scan

> **bug** | **debug** | **trace** | **error** | **exception** | **broken** | **not working** | **wrong** | **incorrect** | **failing** | **fails** | **investigate** | **unexpected** | **why doesn't** | **why does** | **crash** | **issue**

⚠️ **If ANY word above appears in user's request → Load matching skill file FIRST, act SECOND**

### Enforcement Rules

1. **Scan** user message for trigger words from skill index
2. **If match found**: `read_file` the skill's SKILL.md IMMEDIATELY
3. **Follow skill instructions** BEFORE reading code or taking other actions
4. **If no match**: Proceed with normal task handling

### ❌ Common Violations to Avoid

- Reading source code files before consulting skill
- Saying "let me check the code first" when user reports a bug
- Analyzing code structure before using debugger
- Suggesting fixes based on code reading alone
- Stopping investigation after finding one bug (multi-source bugs exist!)

---

## Adding New Skills

To add a new skill:
1. Create `.github/skills/[skill-name]/SKILL.md`
2. Add entry to Skill Index table above
3. Add trigger words to Quick Scan list