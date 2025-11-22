# Claude Agent Spec

Each `.md` file in `.claude-code/agents/` represents:
- A unique Claude Code agent
- One Git branch task
- Zero conflict with others

Claude reads the agent spec → creates branch → builds feature → pushes code

Agents must:
- Use the branch name provided
- Only touch listed files or folders
- Report success/failure in commit message