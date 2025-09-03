#!/usr/bin/env python3
"""
Template para Agentes Reais do Conductor
Mostra como implementar qualquer agente que lê arquivos + usa DeepSeek
"""

import json
import requests
import re
import time
from pathlib import Path
from typing import Dict, Optional, List
from abc import ABC, abstractmethod


class ConductorAgentBase(ABC):
    """Base class para todos os agentes do Conductor"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.model = "deepseek-coder-v2:16b"
        self.chat_url = "http://localhost:11434/api/chat"
        self.stats = {"executions": 0, "successes": 0, "deepseek_calls": 0}

    @abstractmethod
    def execute_task(self, task_params: Dict) -> Dict:
        """Executa a tarefa específica do agente"""
        pass

    def _call_deepseek(
        self, system_message: str, user_message: str, max_tokens: int = 20
    ) -> Dict:
        """Chama DeepSeek com configurações otimizadas"""

        self.stats["deepseek_calls"] += 1

        try:
            start_time = time.time()

            response = requests.post(
                self.chat_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "max_tokens": max_tokens,
                        "stop": ["\n", "```"],
                    },
                },
                timeout=20,
            )

            end_time = time.time()

            if response.status_code != 200:
                return {"status": "ERROR", "result": f"HTTP {response.status_code}"}

            result_data = response.json()
            raw_content = result_data["message"]["content"].strip()

            return {
                "status": "SUCCESS",
                "result": raw_content,
                "time_ms": int((end_time - start_time) * 1000),
                "tokens": result_data.get("eval_count", 0),
            }

        except Exception as e:
            return {"status": "ERROR", "result": str(e)}

    def _update_stats(self, success: bool):
        """Atualiza estatísticas do agente"""
        self.stats["executions"] += 1
        if success:
            self.stats["successes"] += 1

    def get_stats(self) -> Dict:
        """Retorna estatísticas do agente"""
        success_rate = (
            self.stats["successes"] / max(self.stats["executions"], 1)
        ) * 100
        return {**self.stats, "success_rate": f"{success_rate:.1f}%"}


class GradleVersionAgent(ConductorAgentBase):
    """Agente especializado em extrair versões do Gradle"""

    def __init__(self):
        super().__init__("gradle-version-extractor")

    def execute_task(self, task_params: Dict) -> Dict:
        """
        Extrai versão do Gradle de um projeto

        Args:
            task_params: {"project_path": "/path/to/project"}
        """

        project_path = task_params.get("project_path")
        if not project_path:
            return {"status": "ERROR", "message": "project_path é obrigatório"}

        # 1. LER ARQUIVOS DO FILESYSTEM
        gradle_files = self._find_gradle_files(project_path)

        if not gradle_files:
            self._update_stats(False)
            return {"status": "ERROR", "message": "Nenhum arquivo Gradle encontrado"}

        # 2. PROCESSAR CADA ARQUIVO (LOCAL + DEEPSEEK)
        best_version = "UNKNOWN"
        best_confidence = 0.0

        for file_path, content in gradle_files.items():
            # Tentar regex local primeiro
            local_result = self._extract_version_with_regex(content)

            if local_result["confidence"] >= 0.9:
                # Regex funcionou bem, não precisa do DeepSeek
                if local_result["confidence"] > best_confidence:
                    best_version = local_result["result"]
                    best_confidence = local_result["confidence"]
                continue

            # Usar DeepSeek como backup
            deepseek_result = self._extract_version_with_deepseek(content, file_path)

            if deepseek_result["status"] == "SUCCESS":
                clean_version = self._clean_version_response(deepseek_result["result"])
                confidence = 0.8 if clean_version != "UNKNOWN" else 0.1

                if confidence > best_confidence:
                    best_version = clean_version
                    best_confidence = confidence

        # 3. RESULTADO FINAL
        success = best_version != "UNKNOWN"
        self._update_stats(success)

        return {
            "agent_name": self.agent_name,
            "status": "SUCCESS" if success else "FAILED",
            "result": best_version,
            "confidence": best_confidence,
            "project_path": project_path,
            "files_analyzed": len(gradle_files),
            "cost": 0.00,  # GPU local
        }

    def _find_gradle_files(self, project_path: str) -> Dict[str, str]:
        """Encontra e lê arquivos Gradle"""
        gradle_files = {}
        project_dir = Path(project_path)

        if not project_dir.exists():
            return {}

        # Procurar arquivos importantes
        important_files = [
            "gradle/wrapper/gradle-wrapper.properties",
            "build.gradle",
            "build.gradle.kts",
        ]

        for file_pattern in important_files:
            file_path = project_dir / file_pattern
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    gradle_files[str(file_path)] = content
                except Exception:
                    continue

        return gradle_files

    def _extract_version_with_regex(self, content: str) -> Dict:
        """Extrai versão usando regex (rápido e confiável)"""

        patterns = [
            r"gradle-(\d+\.\d+(?:\.\d+)?)-(?:bin|all)\.zip",  # wrapper properties
            r'gradleVersion\s*=\s*["\'](\d+\.\d+(?:\.\d+)?)["\']',  # build.gradle
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return {"result": match.group(1), "confidence": 0.95, "method": "regex"}

        return {"result": "UNKNOWN", "confidence": 0.0, "method": "regex"}

    def _extract_version_with_deepseek(self, content: str, file_path: str) -> Dict:
        """Usa DeepSeek para extrair versão"""

        # Focar apenas nas linhas relevantes
        relevant_lines = []
        for line in content.split("\n")[:20]:  # Primeiras 20 linhas
            if any(
                keyword in line.lower()
                for keyword in ["gradle", "version", "distribution"]
            ):
                relevant_lines.append(line)

        relevant_content = "\n".join(relevant_lines[:10])  # Máximo 10 linhas

        system_message = """You are a Gradle version extractor. 
Find the Gradle version number from the file content.
Respond with ONLY the version number (e.g., 7.4) or UNKNOWN."""

        user_message = f"Extract Gradle version from:\n{relevant_content}\nVersion:"

        return self._call_deepseek(system_message, user_message, max_tokens=10)

    def _clean_version_response(self, response: str) -> str:
        """Limpa resposta e extrai versão"""

        # Procurar padrão de versão
        version_match = re.search(r"\d+\.\d+(?:\.\d+)?", response)
        if version_match:
            return version_match.group()

        return "UNKNOWN"


class TestExecutorAgent(ConductorAgentBase):
    """Agente especializado em executar testes"""

    def __init__(self):
        super().__init__("test-executor")

    def execute_task(self, task_params: Dict) -> Dict:
        """
        Executa teste específico

        Args:
            task_params: {
                "test_command": "mvn test -Dtest=TestUserService#shouldValidateEmail",
                "expected_result": "PASS"
            }
        """

        test_command = task_params.get("test_command")
        if not test_command:
            return {"status": "ERROR", "message": "test_command é obrigatório"}

        # Para o protótipo, simular execução do teste
        # Em produção, executaria: subprocess.run(test_command)

        system_message = """You are a test executor. 
Based on the test command, determine if it would PASS or FAIL.
Respond with only PASS or FAIL."""

        user_message = f"Execute test command: {test_command}"

        deepseek_result = self._call_deepseek(
            system_message, user_message, max_tokens=5
        )

        if deepseek_result["status"] == "SUCCESS":
            result = "PASS" if "PASS" in deepseek_result["result"].upper() else "FAIL"
            confidence = 0.85
            success = True
        else:
            result = "ERROR"
            confidence = 0.0
            success = False

        self._update_stats(success)

        return {
            "agent_name": self.agent_name,
            "status": "SUCCESS" if success else "ERROR",
            "result": result,
            "confidence": confidence,
            "test_command": test_command,
            "time_ms": deepseek_result.get("time_ms", 0),
            "cost": 0.00,
        }


def demo_agent_templates():
    """Demonstra como usar os templates de agentes"""

    print("🤖 DEMO: TEMPLATES DE AGENTES REAIS")
    print("=" * 50)

    # Teste Gradle Agent
    print("\n1️⃣ GRADLE VERSION AGENT:")
    gradle_agent = GradleVersionAgent()
    gradle_result = gradle_agent.execute_task(
        {"project_path": "/mnt/ramdisk/primoia-main/codenoob-social-profile"}
    )

    print(f"   Versão: {gradle_result['result']}")
    print(f"   Confiança: {gradle_result['confidence']:.0%}")
    print(f"   Arquivos: {gradle_result['files_analyzed']}")

    # Teste Test Executor Agent
    print("\n2️⃣ TEST EXECUTOR AGENT:")
    test_agent = TestExecutorAgent()
    test_result = test_agent.execute_task(
        {"test_command": "mvn test -Dtest=TestUserService#shouldValidateEmail"}
    )

    print(f"   Resultado: {test_result['result']}")
    print(f"   Confiança: {test_result['confidence']:.0%}")
    print(f"   Tempo: {test_result.get('time_ms', 0)}ms")

    # Estatísticas
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"   Gradle Agent: {gradle_agent.get_stats()}")
    print(f"   Test Agent: {test_agent.get_stats()}")


if __name__ == "__main__":
    demo_agent_templates()
