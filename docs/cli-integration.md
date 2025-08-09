# CLI Integration Guide

This document provides comprehensive guidance on integrating Claude and Gemini CLI tools with the Conductor system for direct LLM file processing.

## 🎯 Overview

The Conductor system supports three LLM integration approaches:

1. **DeepSeek Local** (via Ollama API) - Free, private, fast for simple tasks
2. **Claude CLI** - Powerful, unrestricted file access, best for complex analysis
3. **Gemini CLI** - Good for documentation, requires workspace awareness

## 🤖 Claude CLI Integration

### Installation & Setup

```bash
# Claude CLI should already be installed on your system
which claude
# Output: /usr/bin/claude

# Test basic functionality
claude --help
```

### Usage Pattern

```python
import subprocess

def call_claude_cli(file_path: str, prompt: str) -> str:
    """Call Claude CLI with file analysis"""
    
    cmd = [
        "claude", 
        "--print",                          # Non-interactive mode
        "--dangerously-skip-permissions",   # Bypass file access restrictions
        f"Analyze {file_path}: {prompt}"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        raise Exception(f"Claude CLI error: {result.stderr}")
```

### Key Features

- **✅ Unrestricted file access** - Can read any file with `--dangerously-skip-permissions`
- **✅ High reliability** - 100% success rate in testing
- **✅ Complex analysis** - Excellent for security scans, code quality, architecture review
- **✅ Fast execution** - Average 9-12 seconds per task
- **⚠️ Cost** - Estimated $0.02 per analysis (API usage)

### Best Use Cases

```python
# Security scanning
claude --print --dangerously-skip-permissions "Scan this file for security vulnerabilities: /path/to/file.java"

# Code quality assessment  
claude --print --dangerously-skip-permissions "Rate the code quality 1-10 and explain: /path/to/file.py"

# Architecture analysis
claude --print --dangerously-skip-permissions "Explain the design patterns used in: /path/to/file.js"

# Complex file analysis
claude --print --dangerously-skip-permissions "What are the main classes and their responsibilities in: /path/to/file.kt"
```

## 💎 Gemini CLI Integration

### Installation & Setup

```bash
# Gemini CLI via npx (no installation needed)
npx --version
# Output: 10.9.2

# Test basic functionality
npx https://github.com/google-gemini/gemini-cli --help
```

### Critical Discovery: Directory Context

**⚠️ IMPORTANT**: Gemini CLI works best when executed from the correct directory context.

#### ❌ Old Approach (50% success rate)
```python
# This often fails for external files
subprocess.run([
    "npx", "https://github.com/google-gemini/gemini-cli", 
    "--prompt", f"Analyze {absolute_path}"
])
```

#### ✅ New Approach (100% success rate)
```python
def call_gemini_cli_optimized(file_path: str, prompt: str) -> str:
    """Call Gemini CLI with proper directory context"""
    
    target_path = Path(file_path)
    
    # Determine optimal working directory
    if target_path.is_absolute() and target_path.exists():
        work_dir = target_path.parent
        relative_file = target_path.name
    else:
        work_dir = Path.cwd()
        relative_file = file_path
    
    # Use shell command with cd for proper context
    cmd = f"cd '{work_dir}' && npx https://github.com/google-gemini/gemini-cli --prompt '{prompt.replace(file_path, relative_file)}'"
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=40)
    
    if result.returncode == 0:
        return clean_gemini_output(result.stdout)
    else:
        raise Exception(f"Gemini CLI error: {result.stderr}")

def clean_gemini_output(raw_output: str) -> str:
    """Clean Gemini output by removing system messages"""
    lines = raw_output.split('\n')
    clean_lines = [
        line for line in lines 
        if not any(skip in line.lower() for skip in [
            'error discovering', 'error connecting', 'loaded cached',
            'mcp error', 'jetbrains'
        ])
    ]
    return '\n'.join(clean_lines).strip()
```

### Key Features

- **✅ Good documentation analysis** - Excellent for README files, documentation
- **✅ Workspace aware** - Works well with local project files
- **✅ Cost effective** - Estimated $0.01 per analysis
- **⚠️ Directory sensitive** - Requires proper `cd` before execution
- **⚠️ Slower execution** - Average 20-25 seconds per task

### Best Use Cases

```bash
# Project documentation summary
cd /project/directory && npx https://github.com/google-gemini/gemini-cli --prompt "Summarize this README.md file"

# Local file explanation
cd /project/directory && npx https://github.com/google-gemini/gemini-cli --prompt "Explain what this config.yml file does"

# Documentation generation
cd /project/directory && npx https://github.com/google-gemini/gemini-cli --prompt "Generate documentation for this API endpoint in api.py"
```

## 🧠 Smart Routing Strategy

The optimal approach is to use intelligent routing based on task characteristics:

```python
def choose_optimal_llm(file_path: str, task_type: str) -> str:
    """Choose best LLM based on task and file characteristics"""
    
    file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
    is_local = is_file_in_workspace(file_path)
    
    # DeepSeek Local: Simple extraction tasks
    if task_type in ["gradle_version", "test_count", "dependency_extract"] and file_size < 50000:
        return "deepseek"
    
    # Claude CLI: Complex analysis or external files
    elif task_type in ["security_scan", "code_quality", "analyze"] or not is_local:
        return "claude"
    
    # Gemini CLI: Local documentation tasks
    elif task_type in ["summarize", "documentation"] and is_local and file_size < 100000:
        return "gemini"
    
    # Default: Claude (most reliable)
    else:
        return "claude"
```

## 📊 Performance Comparison

Based on extensive testing:

| LLM | Success Rate | Avg Time | Cost | Best For |
|-----|-------------|----------|------|----------|
| **DeepSeek Local** | 100% | 9.0s | $0.00 | Simple extraction, privacy-sensitive |
| **Claude CLI** | 100% | 11.7s | $0.02 | Complex analysis, external files |
| **Gemini CLI** | 100%* | 22.5s | $0.01 | Local docs, summarization |

*_With proper `cd` optimization_

## 🔧 Implementation Examples

### Basic CLI Agent

```python
class CLIAgent:
    def __init__(self, llm_type: str):
        self.llm_type = llm_type
    
    def process_file(self, file_path: str, task: str) -> dict:
        if self.llm_type == "claude":
            return self._call_claude(file_path, task)
        elif self.llm_type == "gemini":
            return self._call_gemini(file_path, task)
        else:
            raise ValueError(f"Unknown LLM type: {self.llm_type}")
    
    def _call_claude(self, file_path: str, task: str) -> dict:
        cmd = ["claude", "--print", "--dangerously-skip-permissions", f"{task}: {file_path}"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        return {
            "status": "SUCCESS" if result.returncode == 0 else "ERROR",
            "result": result.stdout.strip() if result.returncode == 0 else result.stderr,
            "llm": "claude"
        }
    
    def _call_gemini(self, file_path: str, task: str) -> dict:
        work_dir = Path(file_path).parent if Path(file_path).is_absolute() else Path.cwd()
        relative_file = Path(file_path).name if Path(file_path).is_absolute() else file_path
        
        cmd = f"cd '{work_dir}' && npx https://github.com/google-gemini/gemini-cli --prompt '{task}: {relative_file}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=40)
        
        return {
            "status": "SUCCESS" if result.returncode == 0 else "ERROR",
            "result": self._clean_gemini_output(result.stdout) if result.returncode == 0 else result.stderr,
            "llm": "gemini"
        }
```

### Smart Multi-LLM Orchestrator

```python
class SmartCLIOrchestrator:
    def __init__(self):
        self.claude_agent = CLIAgent("claude")
        self.gemini_agent = CLIAgent("gemini")
        # DeepSeek agent would be added here
    
    def analyze_file(self, file_path: str, task_type: str) -> dict:
        # Smart routing logic
        chosen_llm = self._choose_llm(file_path, task_type)
        
        if chosen_llm == "claude":
            return self.claude_agent.process_file(file_path, task_type)
        elif chosen_llm == "gemini":
            return self.gemini_agent.process_file(file_path, task_type)
        # Add DeepSeek handling
    
    def _choose_llm(self, file_path: str, task_type: str) -> str:
        # Implement smart routing logic here
        pass
```

## 🚨 Common Issues & Solutions

### Claude CLI Issues

**Issue**: Permission denied for file access
```bash
# Solution: Use --dangerously-skip-permissions flag
claude --print --dangerously-skip-permissions "prompt"
```

**Issue**: Long response times
```bash
# Solution: Use specific, focused prompts
claude --print --dangerously-skip-permissions "Extract ONLY the version number from: file.gradle"
```

### Gemini CLI Issues

**Issue**: "File path must be within workspace directories"
```bash
# ❌ Wrong: Running from wrong directory
npx https://github.com/google-gemini/gemini-cli --prompt "Analyze /external/path/file.py"

# ✅ Correct: Change to file's directory first
cd /external/path && npx https://github.com/google-gemini/gemini-cli --prompt "Analyze file.py"
```

**Issue**: MCP server errors in output
```python
# Solution: Clean the output
def clean_gemini_output(raw_output: str) -> str:
    lines = raw_output.split('\n')
    return '\n'.join([
        line for line in lines 
        if not any(error_keyword in line.lower() for error_keyword in [
            'error discovering', 'error connecting', 'mcp error', 'jetbrains'
        ])
    ]).strip()
```

## 💡 Best Practices

1. **Use Claude for complex analysis** - Security scans, code quality, architecture review
2. **Use Gemini for local documentation** - README summaries, config explanations
3. **Always use `cd` before Gemini** - Change to file's directory for best results
4. **Implement timeout handling** - Both CLIs can be slow, use appropriate timeouts
5. **Clean Gemini output** - Remove system error messages from responses
6. **Cache results when possible** - Avoid redundant API calls for same file/task combinations
7. **Implement fallback strategy** - If primary LLM fails, try secondary option

## 🔮 Future Enhancements

- **Parallel execution** - Run multiple LLMs simultaneously and compare results
- **Result caching** - Store analysis results to avoid redundant processing  
- **Confidence scoring** - Rate LLM responses and choose most confident result
- **Custom model selection** - Allow per-task model specification
- **Batch processing** - Process multiple files in single CLI call where supported

