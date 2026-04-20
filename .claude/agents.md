# Agents

Custom sub-agents available in this project.

## Available Agents

### reviewer
- **Purpose**: Review code changes for quality, security, and style
- **Trigger**: `/reviewer`

### debugger
- **Purpose**: Investigate and diagnose bugs or unexpected behavior
- **Trigger**: `/debugger`

### planner
- **Purpose**: Break down a feature or task into actionable steps
- **Trigger**: `/planner`

## Adding a New Agent

Create a new file under `.claude/agents/<agent-name>.md` with a system prompt describing the agent's role and behavior.
