#!/usr/bin/env python3
"""
Test script: Stream-based watcher PoC.

Runs Claude CLI with --output-format stream-json and processes events in real-time.
Simulates how the real watcher could stream tool calls and reasoning to the BFF.

Usage:
    # Single agent, no MCP
    python test-stream-watcher.py -p "What is 2+2?"

    # Single agent with MCP
    python test-stream-watcher.py --mcp '{"mcpServers":{"tasks":{"type":"sse","url":"http://localhost:13144/sse"}}}' -p "Liste os projetos"

    # 3 concurrent agents with MCP
    python test-stream-watcher.py --workers 3 --mcp '{"mcpServers":{"tasks":{"type":"sse","url":"http://localhost:13144/sse"}}}' \\
        -p "Liste projetos" -p "Quantas tasks abertas?" -p "Quais materiais existem?"

    # With BFF event emission (sends to gateway websocket)
    python test-stream-watcher.py --emit-to http://localhost:14199 -p "Liste projetos" \\
        --mcp '{"mcpServers":{"tasks":{"type":"sse","url":"http://localhost:13144/sse"}}}'
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

# ANSI colors for per-agent output
COLORS = [
    "\033[36m",   # cyan
    "\033[33m",   # yellow
    "\033[35m",   # magenta
    "\033[32m",   # green
    "\033[34m",   # blue
    "\033[91m",   # bright red
    "\033[92m",   # bright green
    "\033[93m",   # bright yellow
    "\033[94m",   # bright blue
    "\033[95m",   # bright magenta
]
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Stats per agent
agent_stats = {}
stats_lock = threading.Lock()


def open_bff_websocket(gateway_url: str, task_context: dict):
    """Open WebSocket to BFF for real-time streaming."""
    try:
        import websocket
        ws_url = gateway_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url += "/ws/agent-stream"
        ws = websocket.WebSocket()
        ws.connect(ws_url, timeout=5)
        ws.send(json.dumps({"type": "stream_start", "data": task_context}))
        print(f"  {DIM}(connected to BFF WebSocket: {ws_url}){RESET}")
        return ws
    except Exception as e:
        print(f"  {DIM}(BFF WebSocket unavailable: {e}){RESET}")
        return None


def close_bff_websocket(ws, task_context: dict, stats: dict = None):
    """Close BFF WebSocket gracefully."""
    if not ws:
        return
    try:
        ws.send(json.dumps({"type": "stream_end", "data": {**task_context, "stats": stats or {}}}))
        ws.close()
    except Exception:
        pass


def process_stream_event(raw_event: dict, agent_id: str, color: str, ws=None, task_context: dict = None):
    """
    Process a Claude CLI stream-json event, display it, and forward to BFF via WebSocket.

    Claude CLI stream-json format (3 event types):
    - {"type": "system", "subtype": "init", "tools": [...], "mcp_servers": [...], ...}
    - {"type": "assistant", "message": {"content": [{"type": "text", "text": "..."}, {"type": "tool_use", ...}], ...}}
    - {"type": "result", "subtype": "success|error", "duration_ms": N, "total_cost_usd": N, "usage": {...}, ...}
    """
    now = datetime.now().strftime("%H:%M:%S")
    prefix = f"{color}[{agent_id}]{RESET} {DIM}{now}{RESET}"

    event_type = raw_event.get("type", "unknown")

    # Track stats
    with stats_lock:
        stats = agent_stats.setdefault(agent_id, {
            "messages": 0, "tool_calls": 0, "text_blocks": 0,
            "tokens_in": 0, "tokens_out": 0, "cost_usd": 0, "start": time.time()
        })

    # Forward to BFF via WebSocket (real-time)
    if ws and task_context:
        try:
            ws.send(json.dumps({
                "type": "agent_stream",
                "data": {**task_context, "event_type": event_type, "event": raw_event}
            }))
        except Exception:
            pass

    if event_type == "system":
        subtype = raw_event.get("subtype", "")
        if subtype == "init":
            tools = raw_event.get("tools", [])
            mcp_servers = raw_event.get("mcp_servers", [])
            session_id = raw_event.get("session_id", "?")[:8]
            mcp_names = [s.get("name", "?") for s in mcp_servers if s.get("status") == "connected"]
            print(f"{prefix} {BOLD}--- INIT ---{RESET} session={session_id} tools={len(tools)} mcps={mcp_names or 'none'}")

    elif event_type == "assistant":
        message = raw_event.get("message", {})
        content = message.get("content", [])
        usage = message.get("usage", {})
        stats["messages"] += 1
        stats["tokens_in"] += usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
        stats["tokens_out"] += usage.get("output_tokens", 0)

        for block in content:
            block_type = block.get("type", "")

            if block_type == "text":
                text = block.get("text", "")
                stats["text_blocks"] += 1
                # Show text, truncated per line
                for line in text.split("\n")[:10]:
                    if line.strip():
                        display = line[:120]
                        print(f"{prefix} {display}")
                if text.count("\n") > 10:
                    print(f"{prefix} {DIM}... ({text.count(chr(10))} lines total){RESET}")

            elif block_type == "tool_use":
                tool_name = block.get("name", "?")
                tool_id = block.get("id", "?")[:12]
                tool_input = block.get("input", {})
                stats["tool_calls"] += 1
                # Show tool call with compact input
                input_preview = json.dumps(tool_input, ensure_ascii=False)[:80]
                print(f"{prefix} {color}{BOLD}tool_use{RESET} {tool_name} ({tool_id}) {DIM}{input_preview}{RESET}")

            elif block_type == "tool_result":
                tool_id = block.get("tool_use_id", "?")[:12]
                content_blocks = block.get("content", [])
                for cb in content_blocks:
                    if cb.get("type") == "text":
                        result_text = cb.get("text", "")[:100]
                        print(f"{prefix} {DIM}  result ({tool_id}): {result_text}{RESET}")

            elif block_type == "thinking":
                thinking = block.get("thinking", "")
                if thinking.strip():
                    display = thinking.replace("\n", " ")[:80]
                    print(f"{prefix} {DIM}think: {display}{RESET}")

    elif event_type == "result":
        subtype = raw_event.get("subtype", "?")
        duration = raw_event.get("duration_ms", 0)
        cost = raw_event.get("total_cost_usd", 0)
        usage = raw_event.get("usage", {})
        num_turns = raw_event.get("num_turns", 0)
        stats["cost_usd"] = cost
        stats["tokens_in"] = usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
        stats["tokens_out"] = usage.get("output_tokens", 0)

        status_icon = "✅" if subtype == "success" else "❌"
        print(f"{prefix} {status_icon} {BOLD}RESULT{RESET} ({subtype}) turns={num_turns} duration={duration}ms cost=${cost:.4f}")


def run_agent(agent_idx: int, prompt: str, mcp_config_path: str = None,
              cwd: str = ".", timeout: int = 300, gateway_url: str = None):
    """Run a single Claude CLI agent with stream-json output."""
    agent_id = f"Agent-{agent_idx}"
    color = COLORS[agent_idx % len(COLORS)]
    now = datetime.now().strftime("%H:%M:%S")

    print(f"{color}[{agent_id}]{RESET} {now} Starting... prompt='{prompt[:60]}...'")

    command = [
        "claude", "--print", "--verbose",
        "--output-format", "stream-json",
        "--dangerously-skip-permissions",
    ]

    if mcp_config_path:
        command.extend(["--mcp-config", mcp_config_path])

    start_time = time.time()
    task_context = {"task_id": f"test-{agent_idx}", "agent_id": agent_id}

    # Open WebSocket to BFF if gateway_url provided
    ws = None
    if gateway_url:
        ws = open_bff_websocket(gateway_url, task_context)

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            env=os.environ.copy()
        )

        # Send prompt via stdin and close
        process.stdin.write(prompt)
        process.stdin.close()

        # Read stdout line by line (stream-json = NDJSON)
        for line in iter(process.stdout.readline, ""):
            line = line.strip()
            if not line:
                continue

            try:
                event_wrapper = json.loads(line)
            except json.JSONDecodeError:
                print(f"{color}[{agent_id}]{RESET} {DIM}(non-json: {line[:80]}){RESET}")
                continue

            # stream-json wraps events: {"type": "stream_event", "event": {...}}
            if event_wrapper.get("type") == "stream_event":
                raw_event = event_wrapper.get("event", {})
            else:
                raw_event = event_wrapper

            process_stream_event(raw_event, agent_id, color, ws, task_context)

        process.wait(timeout=30)
        duration = time.time() - start_time

        # Print summary
        with stats_lock:
            stats = agent_stats.get(agent_id, {})

        stderr_out = process.stderr.read()
        if stderr_out and process.returncode != 0:
            print(f"{color}[{agent_id}]{RESET} stderr: {stderr_out[:200]}")

        print(f"\n{color}[{agent_id}]{RESET} {BOLD}=== DONE ==={RESET}")
        print(f"  Duration: {duration:.1f}s | Exit: {process.returncode}")
        print(f"  Messages: {stats.get('messages', 0)} | Tool calls: {stats.get('tool_calls', 0)}")
        print(f"  Tokens in: {stats.get('tokens_in', 0)} | Tokens out: {stats.get('tokens_out', 0)}")
        print()

    except subprocess.TimeoutExpired:
        process.kill()
        print(f"{color}[{agent_id}]{RESET} TIMEOUT after {timeout}s")
    except FileNotFoundError:
        print(f"{color}[{agent_id}]{RESET} ERROR: 'claude' not found in PATH")
    except Exception as e:
        print(f"{color}[{agent_id}]{RESET} ERROR: {e}")
    finally:
        # Close WebSocket
        with stats_lock:
            final_stats = agent_stats.get(agent_id, {})
        close_bff_websocket(ws, task_context, final_stats)


def main():
    parser = argparse.ArgumentParser(description="Stream-based watcher PoC")
    parser.add_argument("-p", "--prompt", action="append", required=True,
                        help="Prompt(s) to send. Use multiple -p for concurrent agents")
    parser.add_argument("--mcp", type=str, default=None,
                        help="MCP config JSON string or file path")
    parser.add_argument("--workers", type=int, default=None,
                        help="Max concurrent workers (default: number of prompts)")
    parser.add_argument("--cwd", type=str, default=".",
                        help="Working directory for Claude CLI")
    parser.add_argument("--timeout", type=int, default=300,
                        help="Timeout per agent in seconds")
    parser.add_argument("--emit-to", type=str, default=None,
                        help="Gateway URL to emit events to (e.g., http://localhost:14199)")
    args = parser.parse_args()

    # Handle MCP config
    mcp_config_path = None
    if args.mcp:
        if os.path.isfile(args.mcp):
            mcp_config_path = args.mcp
        else:
            # Assume JSON string, write to temp file
            try:
                config = json.loads(args.mcp)
                fd, mcp_config_path = tempfile.mkstemp(suffix=".json", prefix="test_mcp_")
                with os.fdopen(fd, 'w') as f:
                    json.dump(config, f)
                print(f"MCP config written to {mcp_config_path}")
            except json.JSONDecodeError:
                print(f"ERROR: Invalid MCP JSON: {args.mcp}")
                sys.exit(1)

    prompts = args.prompt
    workers = args.workers or len(prompts)

    print(f"\n{BOLD}=== Stream Watcher PoC ==={RESET}")
    print(f"Agents: {len(prompts)} | Workers: {workers} | Timeout: {args.timeout}s")
    if mcp_config_path:
        print(f"MCP: {mcp_config_path}")
    if args.emit_to:
        print(f"Emit to: {args.emit_to}")
    print()

    try:
        if len(prompts) == 1:
            # Single agent - run directly
            run_agent(0, prompts[0], mcp_config_path, args.cwd, args.timeout, args.emit_to)
        else:
            # Multiple agents - run concurrently
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = []
                for i, prompt in enumerate(prompts):
                    f = pool.submit(run_agent, i, prompt, mcp_config_path,
                                    args.cwd, args.timeout, args.emit_to)
                    futures.append(f)
                    time.sleep(0.5)  # Stagger starts slightly

                for f in futures:
                    f.result()  # Wait for all

        # Final summary
        print(f"\n{BOLD}=== Summary ==={RESET}")
        with stats_lock:
            total_tools = sum(s.get("tool_calls", 0) for s in agent_stats.values())
            total_msgs = sum(s.get("messages", 0) for s in agent_stats.values())
            total_tokens_in = sum(s.get("tokens_in", 0) for s in agent_stats.values())
            total_tokens_out = sum(s.get("tokens_out", 0) for s in agent_stats.values())

        print(f"Total agents: {len(prompts)}")
        print(f"Total messages: {total_msgs} | Total tool calls: {total_tools}")
        print(f"Total tokens: {total_tokens_in} in / {total_tokens_out} out")

    finally:
        # Cleanup temp MCP config
        if mcp_config_path and mcp_config_path.startswith(tempfile.gettempdir()):
            try:
                os.unlink(mcp_config_path)
            except OSError:
                pass


if __name__ == "__main__":
    main()
