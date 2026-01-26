---
name: debugger
description: "MANDATORY for ANY Python bug, error, crash, wrong value, or 'not working' report. STOP - do NOT read code to guess. You MUST use this skill's debugger tools (add_breakpoint, run_vscode_command to start debugging, get_variables_values) to trace root cause. Trigger words: bug, debug, trace, error, broken, wrong, failing, investigate, not working, unexpected."
---

# Python Debugger

This skill enables comprehensive debugging of Python applications using MCPDebug automation.

---

## ⚠️ MANDATORY ENFORCEMENT

**STOP. Before reading ANY code to investigate a bug, you MUST use this skill.**

### When This Skill is REQUIRED (Non-Negotiable)

You MUST use this skill's debugger tools when the user mentions ANY of:

| Trigger Words | Examples |
|---------------|----------|
| `bug`, `debug` | "there's a bug", "debug this" |
| `error`, `exception` | "getting an error", "throws exception" |
| `broken`, `not working` | "it's broken", "code not working" |
| `wrong`, `incorrect` | "wrong result", "incorrect output" |
| `failing`, `fails` | "test failing", "function fails" |
| `trace`, `investigate` | "trace the issue", "investigate why" |
| `unexpected` | "unexpected behavior", "unexpected value" |
| `why does/doesn't` | "why doesn't this work" |

### What You MUST Do

```
1. STOP previous debug sessions with: mcp_debugmcp_stop_debugging (workspace-scoped, safe)
2. IMMEDIATELY call add_breakpoint() - set breakpoint at relevant location
3. Check for .vscode/launch.json and start debug with run_vscode_command() - NO manual intervention
4. Use get_variables_values() and evaluate_expression() - inspect actual runtime state
5. Use step_over/step_into - trace execution flow
6. Find ALL root causes - don't stop at the first bug found
```

### What You MUST NOT Do

❌ **NEVER** analyze code by just reading it when user reports a bug  
❌ **NEVER** guess the fix without running the debugger first  
❌ **NEVER** say "the bug might be..." without debugger evidence  
❌ **NEVER** provide a fix before confirming root cause via debugging  
❌ **NEVER** ask user to choose debug configuration - select autonomously  

---

**IMPORTANT**: When encountering ANY Python error, exception, bug, crash, wrong output, or user complaint about code not working—USE THIS SKILL. Do not attempt to guess the fix by reading code alone. Debug first, understand the root cause, then fix.

## When to Use This Skill

Use this skill when you need to:
- Debug Python exceptions (`TypeError`, `ValueError`, `AttributeError`, `KeyError`)
- Investigate wrong or unexpected variable values
- Understand why a function returns incorrect results
- Debug failing pytest or unittest tests
- Respond to user reports of "it doesn't work" or "something is broken"
- Trace the root cause of unexpected behavior

**Key principle**: If you cannot determine the root cause by reading the code, start debugging.

## Prerequisites

- VS Code with DebugMCP extension (`ozzafar.debugmcpextension`)
- Microsoft Python extension installed
- MCP server running on port 3001 (default)

## Core Capabilities

### 1. Breakpoint Management
- Set breakpoints using line content matching
- Remove breakpoints by line number
- List all active breakpoints
- Clear all breakpoints at once

### 2. Session Control
- Start debugging a Python file or test
- Stop, restart debugging sessions
- Navigate code with step over, step into, step out, continue

### 3. Variable Inspection
- Get local, global, or all variables at breakpoint
- Evaluate arbitrary Python expressions
- Inspect complex objects and their attributes

### 4. Root Cause Analysis
- Trace symptoms back to their origin
- Step through code to understand execution flow
- Verify fixes by re-running debug sessions

## Usage Examples

### Example 1: Set a Breakpoint
```json
// Set breakpoint at a specific line
{
  "tool": "mcp_debugmcp_add_breakpoint",
  "fileFullPath": "/workspaces/project/main.py",
  "lineContent": "result = calculate_total(items)"
}
```

### Example 2: Start Debugging Automatically
```json
// Start debug session automatically using VS Code command
// First, check if .vscode/launch.json exists and read it to find config names
{
  "tool": "run_vscode_command",
  "commandId": "workbench.action.debug.start",
  "name": "Start debug session",
  "args": ["Config Name from launch.json"]
}

// Alternative: Start without specific config (may require manual selection)
{
  "tool": "mcp_debugmcp_start_debugging",
  "fileFullPath": "/workspaces/project/main.py",
  "workingDirectory": "/workspaces/project"
}
```

### Example 3: Debug a Specific Test
```json
// Debug a pytest test
{
  "tool": "mcp_debugmcp_start_debugging",
  "fileFullPath": "/workspaces/project/test_calculator.py",
  "workingDirectory": "/workspaces/project",
  "testName": "test_calculate_total"
}
```

### Example 4: Inspect Variables
```json
// Get local variables at current breakpoint
{
  "tool": "mcp_debugmcp_get_variables_values",
  "scope": "local"
}
```

### Example 5: Evaluate Expression
```json
// CRITICAL: Always check current frame first with get_variables_values!
// Variables are only accessible in their defining scope.

// Check length of a list
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "len(items)" }

// Inspect object attribute
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "user.name" }

// Check dictionary keys
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "list(data.keys())" }

// Get object type
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "type(variable).__name__" }
```

**⚠️ Common Mistake:** Trying to evaluate variables from parent frames
```json
// ❌ WRONG: Breakpoint is in nested function, trying to access parent variable
// Debug output shows: Frame: _calc_runtime_offset
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "food_check_pos" }
// Result: NameError: name 'food_check_pos' is not defined

// ✅ RIGHT: First check what's available in current scope
{ "tool": "mcp_debugmcp_get_variables_values", "scope": "local" }
// Then evaluate only variables that exist in this frame
```

### Example 6: Navigate Code
```json
// Step to next line (skip function internals)
{ "tool": "mcp_debugmcp_step_over" }

// Enter into a function call
{ "tool": "mcp_debugmcp_step_into" }

// Exit current function
{ "tool": "mcp_debugmcp_step_out" }

// Continue to next breakpoint
{ "tool": "mcp_debugmcp_continue_execution" }
```

### Example 7: Cleanup
```json
// Remove all breakpoints
{ "tool": "mcp_debugmcp_clear_all_breakpoints" }

// Stop debugging session
{ "tool": "mcp_debugmcp_stop_debugging" }
```

## Critical: Debug Session Management

### Auto-Select Debug Method
**NEVER prompt the user to choose a debugging method.** Automatically determine the appropriate approach:
- For standalone Python scripts → use `mcp_debugmcp_start_debugging` with the script file
- For pytest tests → use `mcp_debugmcp_start_debugging` with `testName` parameter
- For unittest tests → use `mcp_debugmcp_start_debugging` with `testName` parameter
- For modules → debug the entry point file directly

### Monitor Debug Terminal for User Input
**CRITICAL**: Some programs require user input (e.g., `input()`, `stdin` reads). If the debug session appears stuck or unresponsive:
1. Check the **Debug Console** or **Terminal** for pending input prompts
2. Use `get_terminal_output` to check if the program is waiting for input
3. If input is needed, provide it via the terminal or inform the user
4. Watch for prompts like "Enter value:", ">>>", or any input-waiting state

**Signs of a stuck session waiting for input:**
- Breakpoint not being hit despite correct placement
- Debug session running but no progress
- No error, no output, session just hangs

When this happens, check the debug terminal immediately before assuming the breakpoint wasn't hit.

## ⚡ EFFICIENCY GUIDELINES - Minimize Tool Calls

**CRITICAL**: Debugging can be expensive. Follow these rules to minimize iterations:

### 1. Search First, Debug Second
Before setting any breakpoints, use `grep_search` to find ALL modification sites:
```
grep_search: "variable_name|related_function|global_state"
```
This single search often reveals multiple bug sources across files, saving many debug iterations.

### 2. Set Breakpoints INSIDE Conditional Blocks
❌ **Wrong** (causes repeated continue loops):
```python
if condition:  # ← Breakpoint here hits EVERY iteration
    do_something()
```
✅ **Right** (hits only when relevant):
```python
if condition:
    do_something()  # ← Breakpoint here hits only when condition is true
```

### 3. Batch Parallel Operations
Read multiple files and set multiple breakpoints in ONE tool call batch:
```xml
<!-- Do this - parallel calls -->
<invoke name="read_file">file1.py</invoke>
<invoke name="read_file">file2.py</invoke>
<invoke name="grep_search">pattern</invoke>

<!-- NOT this - sequential calls -->
<invoke name="read_file">file1.py</invoke>
<!-- wait -->
<invoke name="read_file">file2.py</invoke>
<!-- wait -->
```

### 4. Batch Expression Evaluations
When paused at breakpoint, evaluate ALL relevant expressions in one batch:
```xml
<invoke name="evaluate_expression">var1</invoke>
<invoke name="evaluate_expression">var2</invoke>
<invoke name="evaluate_expression">module.global_state</invoke>
<invoke name="evaluate_expression">function_result()</invoke>
```

### 5. Avoid the "Continue and Check" Anti-Pattern
❌ **Wrong** (extremely wasteful):
```
continue_execution → evaluate_expression → "not yet" → 
continue_execution → evaluate_expression → "not yet" → 
... repeat 20 times
```
✅ **Right**: Set breakpoint at the SUCCESS path, not before the check

### 6. Use get_variables_values First
Call `get_variables_values(scope="local")` once to see ALL local variables, instead of multiple `evaluate_expression` calls for individual variables.

### 7. Strategic Breakpoint Placement for Progressive Bugs
For bugs that manifest after repeated operations:
- Set breakpoint in the STATE MODIFICATION code (e.g., where counter increments)
- NOT in the check that uses the state (fires every frame)

---

## Guidelines

1. **Always set a breakpoint before starting** - Never call `start_debugging` without first setting at least one breakpoint with `add_breakpoint`

2. **Set breakpoints on executable lines** - Break inside function bodies, not on `def`, `class`, or decorator lines

3. **Wait for breakpoint hit before inspecting** - `get_variables_values` and `evaluate_expression` only work when execution is paused at a breakpoint

4. **Check frame before evaluating expressions** - Always examine the "Frame:" output from debug state and use `get_variables_values` first to see what's available. Variables are only accessible in their defining scope - if paused in a nested function call, parent frame variables will cause NameError

4. **Trace to root cause, not symptoms** - If a variable is `None`, don't stop there—find WHY it's `None`

5. **Use strategic breakpoint placement**:
   - First line inside function body → inspect parameters
   - Before conditionals → check condition values
   - Before loops → inspect iterables
   - Before return → verify return value

6. **Clean up after debugging** - Call `mcp_debugmcp_clear_all_breakpoints` and `mcp_debugmcp_stop_debugging` when done

7. **Restart to re-verify** - After understanding the issue, use `restart_debugging` to confirm your analysis

8. **Never prompt user for debug method** - Automatically infer the correct debugging approach from context (script vs test, pytest vs unittest)

9. **Monitor debug terminal actively** - After starting debug, check terminal output for input prompts that may block execution. Use `get_terminal_output` if session seems stuck

10. **Trace ALL contributors to a bad value** - When you find a wrong value (e.g., offset is `(1, -1)` instead of `(0, 0)`), do NOT stop at the first source. This is where most debugging fails. Investigate ALL functions/modules that contribute to that value. Use `grep_search` to find all callers and all places where the variable is modified. **MANDATORY: Check EVERY contribution before concluding.**

11. **Investigate global state across ALL modules** - Bugs often span multiple files and are triggered by import-time code. When you find global state being modified, search the entire codebase for ALL places that modify it. Use `evaluate_expression` to check module-level variables like `module._global_var`. **MANDATORY: Search for ALL modifications, not just one file.** This is the #1 reason debugging fails.

12. **Verify the complete data flow** - If a function computes a result from multiple sources (e.g., `result = a + b + c`), inspect EACH source individually at runtime. One source being correct does NOT mean all sources are correct. This is not optional. **MANDATORY: Check all components separately before concluding.**

## Autonomous Debugging

### Start Debug Sessions Automatically (No Manual Clicks!)

**CRITICAL: Use `run_vscode_command` to start debugging automatically without user intervention.**

**Required workflow:**

1. **Kill all previous debug sessions**: Use terminal to kill any existing Python debug processes to avoid conflicts
2. **Check for `.vscode/launch.json`**: Read it to find available debug configuration names
3. **Select appropriate config**: Pick the right config based on context (auto-player, test, manual mode, etc.)
4. **Start automatically**: Use `run_vscode_command` with `workbench.action.debug.start` and config name

**Example:**
```json
// 1. Stop any existing debug sessions (workspace-scoped, prevents conflicts)
{
  "tool": "mcp_debugmcp_stop_debugging"
}

// 2. Set breakpoints FIRST (before starting debug)
{ "tool": "mcp_debugmcp_add_breakpoint", "fileFullPath": "/workspace/file.py", "lineContent": "suspicious_line" }

// 3. Read launch.json to get config names
{ "tool": "read_file", "filePath": "/workspace/.vscode/launch.json" }

// 4. Start debug with specific config name
{
  "tool": "run_vscode_command",
  "commandId": "workbench.action.debug.start",
  "name": "Start Auto-Player debug",
  "args": ["🤖 Snake: Auto-Player"]  // Exact name from launch.json
}

// 5. DO NOT call continue_execution immediately after starting!
// The debug session starts asynchronously and will automatically run to first breakpoint.
// Call continue_execution ONLY when you see debug output showing execution is paused.

// 6. Once paused at breakpoint, inspect variables
{ "tool": "mcp_debugmcp_get_variables_values", "scope": "local" }
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "variable_name" }
```

**CRITICAL: Never sleep or wait after starting debug!**
- The debug session runs asynchronously
- It will naturally pause at your breakpoint when code executes
- Calling `continue_execution` immediately will FAIL (session not ready)
- Instead: Set breakpoints first, start debug, then wait for natural pause
- For GUI programs (pygame, tkinter): The window must remain active for debug to work

**Why this approach?**
- ✅ No manual configuration selection needed
- ✅ Automatic execution without user clicks
- ✅ Selects specific debug config programmatically
- ❌ Avoid `mcp_debugmcp_start_debugging` - requires manual selection

### Fallback: When launch.json Doesn't Exist
If `.vscode/launch.json` doesn't exist, you can use `mcp_debugmcp_start_debugging`:
```json
{ 
  "tool": "mcp_debugmcp_start_debugging",
  "fileFullPath": "/path/file.py",
  "workingDirectory": "/path"
}
```
**Warning**: This may prompt the user to select a configuration manually.

### Auto-Recovery from Wrong Debug Configuration
If the debug session doesn't hit expected breakpoints:
1. Call `mcp_debugmcp_stop_debugging` immediately
2. Verify breakpoints are set with `mcp_debugmcp_list_breakpoints`
3. Re-examine the entry point file and `.vscode/launch.json`
4. Restart with correct configuration name using `run_vscode_command`

### Handling Interactive Programs
If the program has multiple modes (e.g., manual vs auto mode):
1. Read the main file to understand command-line arguments
2. Check for environment variables that control behavior
3. Determine the code path that exercises the bug
4. Set breakpoints along that specific path

### Troubleshooting Debug Session Issues

**Problem**: "Debug session is not ready" errors

**Solutions**:
1. ✅ Set breakpoints BEFORE starting debug (not after)
2. ✅ Let program run naturally to breakpoint (don't force with continue_execution)
3. ✅ For GUI programs: Ensure window stays open (user might need to interact)
4. ❌ Don't call `continue_execution` immediately after `run_vscode_command`
5. ❌ Don't use sleep/wait - debug tools will indicate when paused

**Problem**: Breakpoint never hits

**Solutions**:
1. Verify breakpoint is on executable line (not on `def`, `class`, blank lines)
2. Check that code path actually executes (add print before breakpoint to test)
3. For conditional code: Set breakpoint INSIDE the condition block, not before
4. Use `mcp_debugmcp_list_breakpoints` to confirm breakpoints are set correctly

**Problem**: Debug session terminates immediately

**Solutions**:
1. Program might be crashing before reaching breakpoint
2. For GUI apps: Program might exit if no window interaction
3. Check debug console output for errors
4. Try running program without debugger first to verify it works

## Common Patterns

### Pattern: Debug AttributeError
```json
// 'NoneType' has no attribute 'x'
{ "tool": "mcp_debugmcp_add_breakpoint", "fileFullPath": "/path/file.py", "lineContent": "result = obj.x" }
// Read launch.json to get config name, then:
{ "tool": "run_vscode_command", "commandId": "workbench.action.debug.start", "name": "Start debug", "args": ["Python: Current File"] }
// When paused:
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "obj" }
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "type(obj)" }
```

### Pattern: Debug KeyError
```json
// KeyError: 'expected_key'
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "list(data.keys())" }
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "'expected_key' in data" }
```

### Pattern: Debug IndexError
```json
// list index out of range
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "len(items)" }
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "items" }
```

### Pattern: Inspect Complex Objects
```json
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "vars(obj)" }
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "obj.__dict__" }
{ "tool": "mcp_debugmcp_evaluate_expression", "expression": "[attr for attr in dir(obj) if not attr.startswith('_')]" }
```

### Pattern: Full Debug Workflow
```
1. mcp_debugmcp_stop_debugging → Stop previous debug sessions (workspace-scoped)
2. mcp_debugmcp_add_breakpoint → Set breakpoint at suspicious location
3. read .vscode/launch.json → Find available debug configurations
4. run_vscode_command       → Start debug automatically (runs to breakpoint naturally)
5. [WAIT] Debug pauses at breakpoint automatically - NO continue_execution needed!
6. mcp_debugmcp_get_variables_values → Inspect current state
7. mcp_debugmcp_evaluate_expression → Check specific values (run multiple in parallel)
8. mcp_debugmcp_step_over/step_into → Navigate through code
9. Repeat 6-8               → Until root cause found
10. Run COMPLETION CHECKLIST → Before concluding
11. mcp_debugmcp_clear_all_breakpoints → Clean up
12. mcp_debugmcp_stop_debugging → End session
```

**Common mistake**: Calling `continue_execution` immediately after starting debug
- ❌ WRONG: start debug → sleep → continue_execution (will fail!)
- ✅ RIGHT: start debug → [execution naturally pauses at breakpoint] → inspect variables

---

## 🛑 MANDATORY COMPLETION CHECKLIST - Before Concluding Investigation

**CRITICAL: This checklist is MANDATORY. You CANNOT stop debugging without completing ALL items. This is not optional.**

**STOP. HARD STOP. Before reporting "bug found", you MUST verify EVERY item below. Failing to complete this checklist will cause you to miss multi-source bugs.**

### ⚠️ GATE 1: Multi-Component Verification (MANDATORY)

**RED FLAG: If the buggy value is computed from multiple sources (e.g., `result = a + b + c`), you MUST complete ALL steps:**

**DO NOT PROCEED WITHOUT COMPLETING ALL:**

- ☑️ **Evaluated EACH component separately** using `evaluate_expression`
  - Not just the first component
  - Not just the most obvious component
  - EVERY component that contributes to the final value
- ☑️ **Checked ALL module-level globals** that could contribute
  - Search for ALL global variables that influence the value
  - Inspect their current values at runtime with `evaluate_expression`
- ☑️ **Used `grep_search`** to find ALL places that modify the value
  - Search the ENTIRE codebase
  - Include regex patterns to catch all variations
  - Document what you find
- ☑️ **Investigated ALL files** that import or modify related state
  - Don't stop at the first file
  - Check all files that touch the related state
  - Look for import-time side effects

### 🚩 GATE 2: Red Flag Detection (MANDATORY - STOP IF ANY PRESENT)

**If you see ANY of these patterns, you MUST continue investigating. Do NOT stop:**

- 🚩 **Arithmetic combinations**: `result = base + offset1 + offset2` — **MUST check EACH term separately**
  - Don't assume one term is correct
  - Don't assume all terms are the same
  - Evaluate each term at breakpoint
  - Example: If offset is (2, -2) and formula is base + runtime + calibration, check all three

- 🚩 **Function aggregation**: `get_total_offset()` that calls multiple sub-functions — **MUST check EACH sub-function**
  - Each function may have its own bug
  - Each function may contribute to the wrong value
  - Don't stop at the first function

- 🚩 **Accumulating operators**: `+=`, `.append()`, `|=` — **MUST search for ALL such operations**
  - Find every place the state accumulates
  - Not just one place
  - ALL places globally in the codebase
  - Use grep_search with patterns like `+=|\.append|modified global state`

- 🚩 **Module imports**: Files importing config/state modules — **MUST check for import-time side effects**
  - Import order matters
  - Calibrations may run at import time
  - Different modules may modify shared state at initialization
  - Search for all files that import the problematic module

- 🚩 **"Calibration" terminology**: Comments mentioning calibration, adjustment, compensation, optimization — **MANDATORY INVESTIGATION**
  - These often hide progressive bugs
  - Seemingly legitimate optimization code often contains corruption
  - grep_search for: calibration|optimization|compensation|adjustment
  - Check each occurrence manually

### 🛑 GATE 3: Completion Criteria (MANDATORY - VERIFY BEFORE STOPPING)

**You CANNOT stop debugging and report "bug found" until ALL of these are true:**

- ☑️ **Searched for ALL modification sources** — Use grep_search for the problematic variable
- ☑️ **Checked all contributing functions** — Not just the first one you found
- ☑️ **Evaluated all input components** — If result = a + b + c, checked all three at runtime
- ☑️ **Found every module that modifies state** — Check import-time code in all modules
- ☑️ **Documented the complete data flow** — Written down how each component contributes to the bug

**If you cannot check ALL boxes, keep debugging. You have missed bug sources.**

---

### Pattern: Multi-Source Bug Investigation
When a computed value is wrong (e.g., offset, coordinate, sum):
```
1. Set breakpoint where wrong value is USED (symptom location)
2. Identify the function that PRODUCES the wrong value
3. Set breakpoint inside that function
4. Inspect ALL inputs to the computation:
   - evaluate_expression for each variable/parameter
   - Check module-level globals with "module._variable"
5. For EACH input that seems wrong:
   - Use grep_search to find ALL places that modify it
   - Set breakpoints at EACH modification site
   - Trace the origin of EACH contributor
6. Don't stop at first bug found—continue checking other inputs
7. Document ALL sources contributing to the wrong value
```

### Pattern: Global State Corruption
When global/module state is unexpectedly modified:
```
1. Identify the corrupted global variable
2. Use grep_search: find ALL assignments to that variable
3. Set breakpoints at EACH assignment location
4. Check _who_ calls each assignment (caller info)
5. Trace back to find the ORIGINAL corruption source
6. Watch for:
   - Import-time side effects
   - Functions called at module load
   - Accumulated modifications (+=, append, etc.)
```

### Pattern: Progressive/Accumulating Bugs
When bugs manifest only after repeated operations:
```
1. Set breakpoint at the suspected accumulation point
2. Run until breakpoint hits multiple times
3. Track how values change across iterations:
   - First hit: value = X (correct?)
   - Second hit: value = Y (still correct?)
   - Third hit: value = Z (corruption starts?)
4. Identify the trigger condition for corruption
5. Search for ALL code paths that modify the accumulating state
```

## Tool Reference

| Tool | Parameters | Description |
|------|------------|-------------|
| `mcp_debugmcp_add_breakpoint` | `fileFullPath`, `lineContent` | Set breakpoint using content matching |
| `mcp_debugmcp_remove_breakpoint` | `fileFullPath`, `line` | Remove breakpoint by line number (1-based) |
| `mcp_debugmcp_list_breakpoints` | — | List all active breakpoints |
| `mcp_debugmcp_clear_all_breakpoints` | — | Remove all breakpoints |
| `mcp_debugmcp_start_debugging` | `fileFullPath`, `workingDirectory`, `testName`? | Start debug session |
| `mcp_debugmcp_stop_debugging` | — | Stop debug session |
| `mcp_debugmcp_restart_debugging` | — | Restart debug session |
| `mcp_debugmcp_step_over` | — | Execute line, skip into functions |
| `mcp_debugmcp_step_into` | — | Step into function calls |
| `mcp_debugmcp_step_out` | — | Step out of current function |
| `mcp_debugmcp_continue_execution` | — | Run to next breakpoint |
| `mcp_debugmcp_get_variables_values` | `scope`? | Get variables (`local`/`global`/`all`) |
| `mcp_debugmcp_evaluate_expression` | `expression` | Evaluate Python expression |

## Limitations

- Requires Python extension installed in VS Code
- Cannot debug without hitting a breakpoint first
- Expression evaluation requires an active stack frame (paused execution)
- Setting breakpoints on `def`/`class`/decorator lines will not work
- MCP server must be running and accessible on configured port
- Programs with `input()` calls may block—monitor debug terminal for input prompts
- Interactive programs require terminal attention during debug sessions

## Common Pitfalls to Avoid

### Pitfall 1: Stopping at First Bug Found ⚠️ THIS IS CRITICAL

❌ **WRONG** (This is what happened in the snake game debug):
1. Found `_advance_runtime_optimization()` called in snake.py ✓
2. Found `_calc_runtime_offset()` returns non-zero offset ✓
3. Concluded: "Bug found! Runtime offset is the problem"
4. **STOPPED DEBUGGING WITHOUT COMPLETING THE CHECKLIST**
5. **MISSED**: Auto-player.py calling `apply_axis_calibration()` which adds ANOTHER offset
6. **MISSED**: The bug has TWO independent sources that accumulate

✅ **RIGHT**:
1. Found `_advance_runtime_optimization()` called in snake.py ✓
2. Found `_calc_runtime_offset()` returns non-zero offset ✓
3. **CONTINUED INVESTIGATING** — Red flag: "calibration" terminology
4. Searched for `apply_axis_calibration` — Found it in auto_player.py
5. Searched for `_axis_compensation` — Found TWO modules modifying it
6. Evaluated EACH source separately at breakpoint
7. Found TWO independent bugs contributing to the same bad value
8. **ONLY THEN** reported bug found

**KEY LESSON**: Just because you found ONE bug source doesn't mean that's the ONLY bug. Keep digging until the COMPLETION CHECKLIST is 100% complete.

### Pitfall 2: Ignoring Cross-Module State
❌ **Wrong**: Only investigate the file where the symptom appears
✅ **Right**: Use `grep_search` to find ALL modules that touch the problematic state. Import-time code in other modules can corrupt state.

### Pitfall 3: Trusting Comments and Logs
❌ **Wrong**: Assume comments like "VERIFIED" or log output showing "correct" values are accurate
✅ **Right**: Only trust values seen in the debugger. Comments lie, logs can be misleading.

### Pitfall 4: Not Checking Accumulated State
❌ **Wrong**: Check a value once and assume it stays constant
✅ **Right**: For progressive bugs, check values across multiple iterations. State may accumulate or corrupt over time.

### Pitfall 5: Manual Debug Configuration Selection
❌ **Wrong**: Ask user "which debugger do you want to use?"
✅ **Right**: Autonomously select the appropriate debug configuration based on file type and context. If wrong config is selected, stop and restart with correct parameters.

### Pitfall 6: Partial Component Investigation
❌ **Wrong**: In `result = func1() + func2() + func3()`, only check `func1()` and assume others are fine
✅ **Right**: Use `evaluate_expression` on EACH function/component. Finding one correct doesn't mean all are correct.

### Pitfall 7: Missing Cross-Module Modifications
❌ **Wrong**: Find one place modifying state, stop searching
✅ **Right**: Use `grep_search` to find ALL modification sites. Multiple modules may modify same global state. This is NOT optional.

### Pitfall 8: Reading Code Before Debugging
❌ **Wrong**: Read source files first to "understand" the bug before setting breakpoints
✅ **Right**: Set breakpoints and start debugging IMMEDIATELY. Understanding comes from runtime inspection, not code reading.

### Pitfall 9: Skipping the Completion Checklist ⚠️ CRITICAL
❌ **Wrong**: Find one bug, report it, move on
✅ **Right**: ALWAYS run the COMPLETION CHECKLIST before concluding. Multi-source bugs are common. This is MANDATORY, not optional. You will miss bugs if you skip this.
