#!/usr/bin/env python3
"""
Hello World from Conductor!
This is an example project created by your {{team_name}}.

Project: {{project_name}}
Environment: {{environment}}
Generated: {{generated_at}}
"""


def main():
    print("🎼 Hello from Conductor!")
    print(f"Your {{team_name}} is ready to go!")
    print()
    print("Status: ✅ Active")
    print("Team: {{team_name}}")
    print("Project: {{project_name}}")
    print("Environment: {{environment}}")
    print("Agents: Configured Successfully")
    print()
    print("🚀 Next steps:")
    print(
        "1. Explore your agents in: {{project_root}}/projects/{{environment}}/{{project_name}}/agents/"
    )
    print("2. Start chatting with an agent:")
    print(
        "   python scripts/genesis_agent.py --embody [AGENT_NAME] --project-root {{project_root}} --repl"
    )
    print("3. Run automated workflows:")
    print(
        "   python scripts/run_conductor.py --projeto {{project_root}} workflows/[WORKFLOW].yaml"
    )


if __name__ == "__main__":
    main()
