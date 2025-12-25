import subprocess
import logging
import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DiscoveredSidecar:
    name: str
    port: int
    url: str
    container_id: str

class DiscoveryService:
    """
    Service responsible for discovering MCP sidecars running in the Docker environment.
    """

    def scan_network(self) -> List[DiscoveredSidecar]:
        """
        Scans the Docker network for containers that look like MCP sidecars.
        
        Returns:
            List[DiscoveredSidecar]: A list of discovered sidecars.
        """
        sidecars = []
        try:
            # Run docker ps to get container info
            # Format: Names|Ports|ID
            cmd = ["docker", "ps", "--format", "{{.Names}}|{{.Ports}}|{{.ID}}"]
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8")
            
            for line in result.splitlines():
                if not line.strip():
                    continue
                
                parts = line.split("|")
                if len(parts) < 3:
                    continue
                    
                name, ports_str, container_id = parts[0], parts[1], parts[2]
                
                # Filter by name convention (must contain 'sidecar' or be a known mcp service)
                # The master plan says they are named '*sidecar*'
                if "sidecar" not in name.lower() and "mcp" not in name.lower():
                    continue
                
                # Extract port mapped to 9000
                # Example port string: "0.0.0.0:9001->9000/tcp, :::9001->9000/tcp"
                port = self._extract_port(ports_str)
                
                if port:
                    url = f"http://localhost:{port}/sse"
                    sidecars.append(DiscoveredSidecar(
                        name=name,
                        port=port,
                        url=url,
                        container_id=container_id
                    ))
                    logger.info(f"Discovered MCP Sidecar: {name} at {url}")
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to execute docker command: {e.output.decode('utf-8')}")
        except Exception as e:
            logger.error(f"Error during discovery scan: {e}")
            
        return sidecars

    def generate_mcp_config(self, output_path: str = "/tmp/mcp_config.json", whitelist: List[str] = None) -> str:
        """
        Scans for sidecars and generates an MCP configuration file for Claude CLI.
        
        Args:
            output_path: Path to save the generated JSON config.
            whitelist: Optional list of sidecar names to include. If None, include all.
            
        Returns:
            str: The path to the generated config file.
        """
        sidecars = self.scan_network()
        
        mcp_servers = {}
        bridge_script = os.path.join(os.path.dirname(__file__), "mcp_sse_bridge.py")
        
        for sidecar in sidecars:
            # Use the sidecar name as the server name
            # Clean up name if needed (e.g. remove /)
            server_name = sidecar.name.strip("/")
            
            # Filter by whitelist if provided
            if whitelist is not None:
                # Check if server_name matches any item in whitelist (exact or partial match?)
                # Let's assume exact match or simple substring for now
                if server_name not in whitelist:
                    continue
            
            mcp_servers[server_name] = {
                "command": "python3",
                "args": [bridge_script, f"http://localhost:{sidecar.port}"],
                "env": {}
            }
            
        config = {"mcpServers": mcp_servers}
        
        try:
            with open(output_path, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Generated MCP config at {output_path} with {len(sidecars)} servers")
        except Exception as e:
            logger.error(f"Failed to write MCP config: {e}")
            
        return output_path

    def _extract_port(self, ports_str: str) -> Optional[int]:
        """
        Extracts the host port that maps to container port 9000.
        """
        try:
            # Look for pattern like "0.0.0.0:PORT->9000"
            # We can use regex or simple string parsing
            import re
            # Regex to find port mapping to 9000
            # Matches 0.0.0.0:1234->9000 or 1234->9000
            match = re.search(r'(?:0\.0\.0\.0:|:)?(\d+)->9000', ports_str)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return None
