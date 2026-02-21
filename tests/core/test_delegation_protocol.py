"""
Tests for the 4-step delegation protocol (DECOMPOSE → TRIAGE → EXECUTE → HANDOFF).

Validates that:
1. Delegation prompts contain the correct 4-step structure
2. Persona content does NOT leak into delegation instructions
3. Squad filtering works correctly (self excluded)
4. Chain depth limits are injected
5. Both XML and text formats are consistent

These are unit tests for prompt construction — they do NOT invoke an LLM.
For end-to-end delegation chain tests, see test_delegation_e2e.py (manual marker).
"""

import pytest
import tempfile
import yaml
import re
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.core.prompt_engine import PromptEngine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SQUAD_6_AGENTS = [
    {
        "agent_id": "DocumentationExpert_Agent",
        "instance_id": "instance-1000000000001-docexpert",
        "name": "Documentation Expert",
        "description": "Especialista em documentação de projetos, README, APIs e melhores práticas",
        "emoji": "📝",
        "squad": "documentation",
    },
    {
        "agent_id": "CodeReviewer_Agent",
        "instance_id": "instance-1000000000002-coderev",
        "name": "Code Reviewer",
        "description": "Especialista em revisão de código, análise de qualidade e melhores práticas",
        "emoji": "🔍",
        "squad": "development",
    },
    {
        "agent_id": "DevOpsEngineer_Agent",
        "instance_id": "instance-1000000000003-devops",
        "name": "DevOps Engineer",
        "description": "Consultor DevOps proativo que analisa aspectos aleatórios do ecossistema com reports didáticos",
        "emoji": "⚙️",
        "squad": "devops",
    },
    {
        "agent_id": "LinkedInContent_Agent",
        "instance_id": "instance-1000000000004-linkedin",
        "name": "LinkedIn Content",
        "description": "Especialista em criar posts para LinkedIn relacionando conteúdo com projetos Conductor",
        "emoji": "💼",
        "squad": "documentation",
    },
    {
        "agent_id": "LinkedInCritic_Agent",
        "instance_id": "instance-1000000000005-critic",
        "name": "LinkedIn Critic",
        "description": "Avaliador crítico de posts LinkedIn — pontua, compara e elege o melhor post",
        "emoji": "🎯",
        "squad": "content",
    },
    {
        "agent_id": "SeniorCodeExecutor_Agent",
        "instance_id": "instance-1000000000006-codeexec",
        "name": "Senior Code Executor",
        "description": "Executor de código sênior que analisa requisitos em Markdown, avalia viabilidade e implementa soluções robustas",
        "emoji": "💻",
        "squad": "orchestration",
    },
]


@pytest.fixture
def make_engine():
    """Factory fixture: creates a PromptEngine with delegation configured.

    Usage:
        engine = make_engine("DocumentationExpert_Agent")
        engine = make_engine("CodeReviewer_Agent", max_depth=5)
    """

    def _factory(active_agent_id: str, max_depth: int | None = None):
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_path = Path(tmp_dir)

            config = {
                "name": active_agent_id.replace("_Agent", "").replace("_", " "),
                "description": next(
                    (a["description"] for a in SQUAD_6_AGENTS if a["agent_id"] == active_agent_id),
                    "Test agent",
                ),
            }
            with open(agent_path / "definition.yaml", "w") as f:
                yaml.dump(config, f)

            # Use the real persona for DocumentationExpert to test persona influence
            if active_agent_id == "DocumentationExpert_Agent":
                persona = """# Persona: Documentation Expert

## Identidade
Você é um especialista em documentação de projetos de software.

## Expertise
- Análise e melhoria de README.md existentes
- Documentação de APIs (REST, GraphQL, etc.)
- Code comments e docstrings efetivos
- Documentação para diferentes audiências
"""
            elif active_agent_id == "CodeReviewer_Agent":
                persona = """# Persona: Code Reviewer

## Identidade
Você é um especialista em revisão de código e qualidade de software.

## Expertise
- Code review detalhado
- Análise de qualidade e complexidade
- Melhores práticas de engenharia
"""
            else:
                persona = f"# Persona: {config['name']}\nYou are a test agent."

            with open(agent_path / "persona.md", "w") as f:
                f.write(persona)

            engine = PromptEngine(agent_path)
            engine.load_context()

            # Inject delegation settings directly (bypass MongoDB)
            engine.agent_id = active_agent_id
            engine.conversation_delegation = {
                "auto_delegate": True,
                "max_chain_depth": max_depth,
                "squad": SQUAD_6_AGENTS,
            }

            return engine

    return _factory


# We need to keep the temp dir alive for the engine, so use a class-based approach
@pytest.fixture
def engine_with_dir():
    """Factory that keeps the temp dir alive."""
    dirs = []

    def _factory(active_agent_id: str, max_depth: int | None = None):
        tmp_dir = tempfile.mkdtemp()
        dirs.append(tmp_dir)
        agent_path = Path(tmp_dir)

        config = {
            "name": active_agent_id.replace("_Agent", "").replace("_", " "),
            "description": next(
                (a["description"] for a in SQUAD_6_AGENTS if a["agent_id"] == active_agent_id),
                "Test agent",
            ),
        }
        with open(agent_path / "definition.yaml", "w") as f:
            yaml.dump(config, f)

        if active_agent_id == "DocumentationExpert_Agent":
            persona = """# Persona: Documentation Expert

## Identidade
Você é um especialista em documentação de projetos de software.

## Expertise
- Análise e melhoria de README.md existentes
- Documentação de APIs (REST, GraphQL, etc.)
- Code comments e docstrings efetivos
- Documentação para diferentes audiências
"""
        elif active_agent_id == "CodeReviewer_Agent":
            persona = """# Persona: Code Reviewer

## Identidade
Você é um especialista em revisão de código e qualidade de software.

## Expertise
- Code review detalhado
- Análise de qualidade e complexidade
- Melhores práticas de engenharia
"""
        elif active_agent_id == "LinkedInContent_Agent":
            persona = """# Persona: LinkedIn Content Creator

## Identidade
Você cria posts profissionais para LinkedIn.

## Expertise
- Copywriting para LinkedIn
- Storytelling técnico
- Engagement e gatilhos mentais
"""
        elif active_agent_id == "LinkedInCritic_Agent":
            persona = """# Persona: LinkedIn Critic

## Identidade
Você avalia e pontua posts de LinkedIn.

## Expertise
- Análise de engagement
- Scoring de qualidade
- Comparação de versões
"""
        else:
            persona = f"# Persona: {config['name']}\nYou are a test agent."

        with open(agent_path / "persona.md", "w") as f:
            f.write(persona)

        engine = PromptEngine(agent_path)
        engine.load_context()
        engine.agent_id = active_agent_id
        engine.conversation_delegation = {
            "auto_delegate": True,
            "max_chain_depth": max_depth,
            "squad": SQUAD_6_AGENTS,
        }
        return engine

    yield _factory

    # Cleanup
    import shutil
    for d in dirs:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FOUR_STEPS = ["DECOMPOSE", "TRIAGE", "EXECUTE", "HANDOFF"]
OLD_STEPS_ONLY = ["TRIAGE", "EXECUTE", "HANDOFF"]  # Old 3-step protocol


def _extract_delegation_block(prompt: str) -> str:
    """Extract the delegation section from a full prompt."""
    # XML format
    m = re.search(r"<delegation>.*?</delegation>", prompt, re.DOTALL)
    if m:
        return m.group(0)
    # Text format
    m = re.search(r"### DELEGATION.*?(?=###|\Z)", prompt, re.DOTALL)
    if m:
        return m.group(0)
    return ""


def _assert_four_steps(text: str):
    """Assert all 4 steps appear in the correct order."""
    positions = []
    for step in FOUR_STEPS:
        pos = text.find(f"STEP")
        step_match = re.search(rf"STEP\s+\d+\s*[—–-]\s*{step}", text)
        assert step_match, f"Missing STEP '{step}' in delegation instructions"
        positions.append(step_match.start())
    # Verify ordering
    assert positions == sorted(positions), (
        f"Steps are out of order. Positions: {dict(zip(FOUR_STEPS, positions))}"
    )


def _assert_no_old_protocol(text: str):
    """Assert the old 3-step protocol is NOT present (no STEP without DECOMPOSE)."""
    # The old protocol had only TRIAGE, EXECUTE, HANDOFF (3 steps).
    # The new protocol has DECOMPOSE as STEP 1. Verify DECOMPOSE is STEP 1.
    match = re.search(r"STEP\s+1\s*[—–-]\s*(\w+)", text)
    assert match, "No STEP 1 found"
    assert match.group(1) == "DECOMPOSE", (
        f"STEP 1 should be DECOMPOSE, got '{match.group(1)}' (old protocol?)"
    )


# ===========================================================================
# TEST CLASS: Protocol Structure
# ===========================================================================

class TestDelegationProtocolStructure:
    """Verify the 4-step protocol is correctly generated in both formats."""

    def test_xml_contains_four_steps(self, engine_with_dir):
        """XML delegation must have DECOMPOSE → TRIAGE → EXECUTE → HANDOFF."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()

        _assert_four_steps(xml)
        _assert_no_old_protocol(xml)

    def test_text_contains_four_steps(self, engine_with_dir):
        """Text delegation must have DECOMPOSE → TRIAGE → EXECUTE → HANDOFF."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        text = engine._build_delegation_text()

        _assert_four_steps(text)
        _assert_no_old_protocol(text)

    def test_xml_and_text_steps_are_consistent(self, engine_with_dir):
        """Both formats must contain the same 4 steps with same semantics."""
        engine = engine_with_dir("CodeReviewer_Agent")
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        for step in FOUR_STEPS:
            assert step in xml, f"XML missing step: {step}"
            assert step in text, f"Text missing step: {step}"

    def test_decompose_instructs_numbered_list(self, engine_with_dir):
        """DECOMPOSE step must instruct agent to create a numbered list of sub-tasks."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        for fmt, content in [("XML", xml), ("Text", text)]:
            assert "sub-task" in content.lower(), f"{fmt}: DECOMPOSE should mention sub-tasks"
            assert "numbered" in content.lower() or "list" in content.lower(), (
                f"{fmt}: DECOMPOSE should instruct agent to create a numbered list"
            )

    def test_execute_scoped_to_own_subtask(self, engine_with_dir):
        """EXECUTE step must say ONLY your sub-task, not the whole request."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        for fmt, content in [("XML", xml), ("Text", text)]:
            assert "ONLY" in content, f"{fmt}: EXECUTE must stress ONLY your sub-task"
            assert "Do NOT proceed" in content or "do NOT proceed" in content, (
                f"{fmt}: EXECUTE must prohibit proceeding to other agents' sub-tasks"
            )

    def test_handoff_includes_remaining_pipeline(self, engine_with_dir):
        """HANDOFF step must instruct passing the remaining pipeline."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        for fmt, content in [("XML", xml), ("Text", text)]:
            assert "remaining pipeline" in content.lower() or "remaining" in content.lower(), (
                f"{fmt}: HANDOFF must mention remaining pipeline"
            )

    def test_rules_include_decompose_mandate(self, engine_with_dir):
        """Rules must include 'ALWAYS decompose multi-part requests'."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        for fmt, content in [("XML", xml), ("Text", text)]:
            assert "ALWAYS decompose" in content, (
                f"{fmt}: Rules must mandate decomposition of multi-part requests"
            )

    def test_rules_prohibit_doing_other_agents_job(self, engine_with_dir):
        """Rules must say 'Never do another agent's job'."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        for fmt, content in [("XML", xml), ("Text", text)]:
            assert "another agent" in content.lower() and "job" in content.lower(), (
                f"{fmt}: Rules must prohibit doing another agent's job"
            )

    def test_scope_boundary_rule_present(self, engine_with_dir):
        """Rules must include SCOPE BOUNDARY preventing agents from overstepping."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        for fmt, content in [("XML", xml), ("Text", text)]:
            assert "SCOPE BOUNDARY" in content, (
                f"{fmt}: Missing SCOPE BOUNDARY rule"
            )
            # Must mention git operations as an example of scope violation
            assert "git" in content.lower() or "Git" in content, (
                f"{fmt}: SCOPE BOUNDARY should mention Git as example"
            )
            # Must say "even if you technically could"
            assert "even if you technically could" in content.lower(), (
                f"{fmt}: SCOPE BOUNDARY should say 'even if you technically could do it'"
            )

    def test_delegate_block_format_preserved(self, engine_with_dir):
        """The [DELEGATE]...[/DELEGATE] block format must be present."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        for fmt, content in [("XML", xml), ("Text", text)]:
            assert "[DELEGATE]" in content, f"{fmt}: Missing [DELEGATE] block"
            assert "[/DELEGATE]" in content, f"{fmt}: Missing [/DELEGATE] block"
            assert "target_agent_id:" in content, f"{fmt}: Missing target_agent_id field"
            assert "input:" in content, f"{fmt}: Missing input field"


# ===========================================================================
# TEST CLASS: Squad Filtering
# ===========================================================================

class TestSquadFiltering:
    """Verify agents are correctly listed and self is excluded."""

    def test_self_excluded_from_xml(self, engine_with_dir):
        """Active agent must NOT appear in available_agents XML."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()

        assert "DocumentationExpert_Agent" not in xml, (
            "Self (DocumentationExpert_Agent) should be excluded from squad listing"
        )
        # But the other 5 should be present
        for agent in SQUAD_6_AGENTS:
            if agent["agent_id"] != "DocumentationExpert_Agent":
                assert agent["agent_id"] in xml, f"Missing agent: {agent['agent_id']}"

    def test_self_excluded_from_text(self, engine_with_dir):
        """Active agent must NOT appear in delegation text."""
        engine = engine_with_dir("CodeReviewer_Agent")
        text = engine._build_delegation_text()

        assert "CodeReviewer_Agent" not in text
        for agent in SQUAD_6_AGENTS:
            if agent["agent_id"] != "CodeReviewer_Agent":
                assert agent["agent_id"] in text, f"Missing agent: {agent['agent_id']}"

    def test_empty_squad_returns_empty(self, engine_with_dir):
        """If only self in squad, delegation section should be empty."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        engine.conversation_delegation["squad"] = [SQUAD_6_AGENTS[0]]  # Only self
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        assert xml == ""
        assert text == ""

    def test_chain_depth_injected(self, engine_with_dir):
        """Chain depth limit must appear when set."""
        engine = engine_with_dir("DocumentationExpert_Agent", max_depth=10)
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        assert "10" in xml, "XML should contain chain depth limit"
        assert "10" in text, "Text should contain chain depth limit"

    def test_chain_depth_absent_when_none(self, engine_with_dir):
        """Chain depth should NOT appear when not set."""
        engine = engine_with_dir("DocumentationExpert_Agent", max_depth=None)
        xml = engine._build_delegation_xml()

        assert "Chain depth" not in xml


# ===========================================================================
# TEST CLASS: Persona Isolation (the key concern)
# ===========================================================================

class TestPersonaIsolation:
    """Verify that persona content does NOT contaminate delegation decisions.

    The concern: a Documentation Expert persona that mentions "Code comments",
    "API docs", etc. might cause the LLM to think it can handle code review
    or LinkedIn posts. These tests verify structural isolation.
    """

    def test_persona_not_in_delegation_xml(self, engine_with_dir):
        """Persona content must NOT appear inside <delegation> block."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()

        # Persona keywords that should NOT be in the delegation section
        persona_leaks = [
            "documentação de projetos",
            "README",
            "Code comments",
            "docstrings",
            "Identidade",
            "Expertise",
        ]
        for keyword in persona_leaks:
            assert keyword not in xml, (
                f"Persona content leaked into delegation XML: '{keyword}'"
            )

    def test_persona_not_in_delegation_text(self, engine_with_dir):
        """Persona content must NOT appear inside delegation text block."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        text = engine._build_delegation_text()

        persona_leaks = [
            "documentação de projetos",
            "README",
            "Code comments",
            "docstrings",
        ]
        for keyword in persona_leaks:
            assert keyword not in text, (
                f"Persona content leaked into delegation text: '{keyword}'"
            )

    def test_delegation_xml_only_contains_agent_descriptions(self, engine_with_dir):
        """The only agent-specific text in delegation should be from squad descriptions."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()

        # Squad descriptions that SHOULD be present
        for agent in SQUAD_6_AGENTS:
            if agent["agent_id"] != "DocumentationExpert_Agent":
                assert agent["description"] in xml, (
                    f"Squad agent description missing: {agent['agent_id']}"
                )

    def test_full_xml_prompt_persona_and_delegation_are_separate(self, engine_with_dir):
        """In the full XML prompt, <persona> and <delegation> must be separate blocks."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        engine.prompt_format = "xml"

        # Build full prompt (need to mock MongoDB-dependent parts)
        with patch.object(engine, '_load_conversation_history'):
            with patch.object(engine, '_load_conversation_context'):
                prompt = engine.build_prompt_with_format([], "test input")

        # Find both blocks
        persona_match = re.search(r"<persona>.*?</persona>", prompt, re.DOTALL)
        delegation_match = re.search(r"<delegation>.*?</delegation>", prompt, re.DOTALL)

        assert persona_match, "Missing <persona> block in full prompt"
        assert delegation_match, "Missing <delegation> block in full prompt"

        # Verify no overlap
        persona_end = persona_match.end()
        delegation_start = delegation_match.start()
        assert delegation_start > persona_end, (
            "Delegation block should come after persona block"
        )

        # Verify persona keywords are NOT inside delegation
        delegation_text = delegation_match.group(0)
        assert "documentação de projetos" not in delegation_text
        assert "README" not in delegation_text

    def test_full_text_prompt_persona_and_delegation_are_separate(self, engine_with_dir):
        """In text prompt, persona and delegation sections must be separate."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        engine.prompt_format = "text"

        prompt = engine.build_prompt([], "test input")

        # Delegation section should exist
        assert "### DELEGATION" in prompt, "Missing delegation section in text prompt"

        # Extract delegation section
        delegation_start = prompt.index("### DELEGATION")
        delegation_section = prompt[delegation_start:]

        # Persona keywords should not be in delegation section
        assert "documentação de projetos" not in delegation_section
        assert "README" not in delegation_section


# ===========================================================================
# TEST CLASS: Baton Scenarios (2, 3, 4 handoffs)
# ===========================================================================

class TestBatonScenarios:
    """Validate prompt structure for multi-handoff scenarios.

    These tests verify that the delegation prompt is correctly constructed
    for each agent in the chain, ensuring each agent sees the right squad
    and the protocol allows the chain to continue.

    Note: These are structural tests. They verify the PROMPT is correct,
    not that the LLM will actually delegate (that requires E2E tests).
    """

    # --- 2-baton: CodeReview → Commit (DevOps) ---

    def test_2_baton_first_agent_sees_handoff_target(self, engine_with_dir):
        """Baton 1→2: CodeReviewer must see DevOpsEngineer in squad."""
        engine = engine_with_dir("CodeReviewer_Agent")
        xml = engine._build_delegation_xml()

        assert "DevOpsEngineer_Agent" in xml
        assert "CodeReviewer_Agent" not in xml  # Self excluded

    def test_2_baton_second_agent_sees_first(self, engine_with_dir):
        """Baton 2→end: DevOps must see CodeReviewer (for potential back-delegation)."""
        engine = engine_with_dir("DevOpsEngineer_Agent")
        xml = engine._build_delegation_xml()

        assert "CodeReviewer_Agent" in xml
        assert "DevOpsEngineer_Agent" not in xml  # Self excluded

    # --- 3-baton: DocExpert → CodeReviewer → LinkedInContent ---

    def test_3_baton_chain_all_agents_see_next(self, engine_with_dir):
        """3-baton chain: each agent must see the next agent in its squad."""
        chain = [
            ("DocumentationExpert_Agent", "CodeReviewer_Agent"),
            ("CodeReviewer_Agent", "LinkedInContent_Agent"),
            ("LinkedInContent_Agent", "LinkedInCritic_Agent"),  # Natural next
        ]
        for current, expected_next in chain:
            engine = engine_with_dir(current)
            xml = engine._build_delegation_xml()
            assert expected_next in xml, (
                f"Agent '{current}' cannot see next target '{expected_next}'"
            )
            assert current not in xml, f"Agent '{current}' should not see itself"

    # --- 4-baton: DocExpert → CodeReviewer → LinkedInContent → LinkedInCritic ---

    def test_4_baton_full_pipeline_squad_visibility(self, engine_with_dir):
        """4-baton: full pipeline from docs → review → linkedin → critic.

        Each agent in the chain must:
        1. See all other agents (not just the next one)
        2. NOT see itself
        3. Have the 4-step protocol
        """
        pipeline = [
            "DocumentationExpert_Agent",
            "CodeReviewer_Agent",
            "LinkedInContent_Agent",
            "LinkedInCritic_Agent",
        ]
        for agent_id in pipeline:
            engine = engine_with_dir(agent_id)
            xml = engine._build_delegation_xml()

            # Must NOT see self
            assert agent_id not in xml, f"{agent_id} should not see itself"

            # Must see all OTHER pipeline members
            for other in pipeline:
                if other != agent_id:
                    assert other in xml, (
                        f"{agent_id} cannot see pipeline member {other}"
                    )

            # Must have 4-step protocol
            _assert_four_steps(xml)

    def test_4_baton_every_agent_has_execute_only_constraint(self, engine_with_dir):
        """Every agent in a 4-baton chain must have the ONLY constraint in EXECUTE."""
        pipeline = [
            "DocumentationExpert_Agent",
            "CodeReviewer_Agent",
            "LinkedInContent_Agent",
            "LinkedInCritic_Agent",
        ]
        for agent_id in pipeline:
            engine = engine_with_dir(agent_id)
            xml = engine._build_delegation_xml()

            assert "ONLY" in xml, f"{agent_id} missing ONLY constraint in EXECUTE"
            assert "remaining pipeline" in xml.lower() or "remaining" in xml.lower(), (
                f"{agent_id} missing remaining pipeline instruction in HANDOFF"
            )


# ===========================================================================
# TEST CLASS: Edge Cases
# ===========================================================================

class TestDelegationEdgeCases:
    """Edge cases and regression guards."""

    def test_auto_delegate_false_produces_no_delegation(self, engine_with_dir):
        """When auto_delegate is false, no delegation section should be generated."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        engine.conversation_delegation["auto_delegate"] = False
        engine.prompt_format = "xml"

        xml = engine._build_delegation_xml()
        # _build_delegation_xml doesn't check auto_delegate directly,
        # but the callers (build_prompt_with_format / build_prompt) do.
        # So we test the caller behavior.
        with patch.object(engine, '_load_conversation_history'):
            with patch.object(engine, '_load_conversation_context'):
                prompt = engine.build_prompt_with_format([], "test")

        assert "<delegation>" not in prompt

    def test_single_agent_squad_no_delegation(self, engine_with_dir):
        """Squad with only 1 agent (self) should produce empty delegation."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        engine.conversation_delegation["squad"] = [
            s for s in SQUAD_6_AGENTS if s["agent_id"] == "DocumentationExpert_Agent"
        ]

        xml = engine._build_delegation_xml()
        assert xml == ""

    def test_two_agent_squad_shows_one(self, engine_with_dir):
        """Squad with 2 agents should list exactly 1 (excluding self)."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        engine.conversation_delegation["squad"] = [
            s for s in SQUAD_6_AGENTS
            if s["agent_id"] in ("DocumentationExpert_Agent", "CodeReviewer_Agent")
        ]

        xml = engine._build_delegation_xml()
        assert "CodeReviewer_Agent" in xml
        assert "DocumentationExpert_Agent" not in xml
        assert xml.count("<agent ") == 1

    def test_never_delegate_to_self_rule(self, engine_with_dir):
        """The 'never delegate back to yourself' rule must be present."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        assert "Never delegate back to yourself" in xml or "never delegate back to yourself" in xml.lower()
        assert "Never delegate back to yourself" in text or "never delegate back to yourself" in text.lower()

    def test_closed_squad_rule_xml(self, engine_with_dir):
        """CLOSED SQUAD rule must prohibit creating/adding new agents (XML)."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()

        assert "CLOSED SQUAD" in xml, "Missing CLOSED SQUAD rule in XML"
        assert "ONLY delegate to agents listed" in xml, (
            "CLOSED SQUAD must say ONLY delegate to listed agents"
        )
        assert "Do NOT create" in xml, "CLOSED SQUAD must prohibit creating agents"
        assert "agent creation tools" in xml.lower(), (
            "CLOSED SQUAD must explicitly mention agent creation tools"
        )

    def test_closed_squad_rule_text(self, engine_with_dir):
        """CLOSED SQUAD rule must prohibit creating/adding new agents (Text)."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        text = engine._build_delegation_text()

        assert "CLOSED SQUAD" in text, "Missing CLOSED SQUAD rule in text"
        assert "ONLY delegate to agents listed" in text, (
            "CLOSED SQUAD must say ONLY delegate to listed agents"
        )
        assert "Do NOT create" in text, "CLOSED SQUAD must prohibit creating agents"

    def test_closed_squad_says_fixed(self, engine_with_dir):
        """CLOSED SQUAD must emphasize the squad is FIXED."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        for fmt, content in [("XML", xml), ("Text", text)]:
            assert "fixed" in content.lower(), (
                f"{fmt}: CLOSED SQUAD must say the squad is fixed"
            )

    def test_instance_id_in_xml(self, engine_with_dir):
        """XML available_agents must include instance_id attribute for each agent."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()

        # Self excluded, so check the other 5
        for agent in SQUAD_6_AGENTS:
            if agent["agent_id"] != "DocumentationExpert_Agent":
                assert agent["instance_id"] in xml, (
                    f"Missing instance_id '{agent['instance_id']}' for {agent['agent_id']}"
                )
                assert f'instance_id="{agent["instance_id"]}"' in xml, (
                    f"instance_id should be an XML attribute for {agent['agent_id']}"
                )

    def test_instance_id_in_text(self, engine_with_dir):
        """Text delegation must include instance_id for each agent."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        text = engine._build_delegation_text()

        for agent in SQUAD_6_AGENTS:
            if agent["agent_id"] != "DocumentationExpert_Agent":
                assert agent["instance_id"] in text, (
                    f"Missing instance_id '{agent['instance_id']}' for {agent['agent_id']}"
                )

    def test_delegate_block_has_instance_id_field(self, engine_with_dir):
        """The [DELEGATE] block template must include instance_id field."""
        engine = engine_with_dir("DocumentationExpert_Agent")
        xml = engine._build_delegation_xml()
        text = engine._build_delegation_text()

        for fmt, content in [("XML", xml), ("Text", text)]:
            assert "instance_id:" in content, (
                f"{fmt}: [DELEGATE] block must include instance_id field"
            )
