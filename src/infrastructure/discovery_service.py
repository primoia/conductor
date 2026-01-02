"""
DEPRECATED: Este módulo está sendo substituído pelo mcp_registry do Gateway.

O scan de containers Docker foi descontinuado em favor do sistema MCP On-Demand,
onde todos os MCPs são cadastrados no mcp_registry e gerenciados pelo Watcher.

Para obter a lista de MCPs disponíveis, use:
- GET /mcp/list do Gateway (retorna todos os MCPs do registry)
- MCPContainerService no Watcher (gerencia ciclo de vida dos containers)

Este arquivo será removido em versões futuras.
"""

import logging
import json
import os
import warnings
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# DEPRECATED: Docker scan está sendo substituído pelo mcp_registry
DOCKER_SCAN_DEPRECATED = True

# Try to import docker library, fall back gracefully if not available
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("Docker library not available. MCP sidecar discovery will be disabled.")

@dataclass
class DiscoveredSidecar:
    name: str
    port: int
    url: str
    container_id: str

class DiscoveryService:
    """
    Service responsible for discovering MCP sidecars running in the Docker environment.
    Uses the Python docker library to communicate with Docker daemon via socket.
    """

    def __init__(self):
        self._client = None

    def _get_docker_client(self):
        """Get or create Docker client instance."""
        if not DOCKER_AVAILABLE:
            return None
        if self._client is None:
            try:
                self._client = docker.from_env()
            except Exception as e:
                logger.error(f"Failed to create Docker client: {e}")
                return None
        return self._client

    def scan_network(self) -> List[DiscoveredSidecar]:
        """
        DEPRECATED: Use GET /mcp/list do Gateway em vez deste método.

        Scans the Docker network for containers that look like MCP sidecars.
        Este método está sendo descontinuado em favor do mcp_registry.

        Returns:
            List[DiscoveredSidecar]: A list of discovered sidecars.
        """
        warnings.warn(
            "scan_network() está deprecated. Use GET /mcp/list do Gateway.",
            DeprecationWarning,
            stacklevel=2
        )

        sidecars = []

        client = self._get_docker_client()
        if not client:
            logger.warning("Docker client not available, returning empty sidecar list")
            return sidecars

        try:
            # Get all running containers
            containers = client.containers.list()

            for container in containers:
                name = container.name
                container_id = container.short_id

                # Filter by name convention (must contain 'sidecar' or 'mcp')
                if "sidecar" not in name.lower() and "mcp" not in name.lower():
                    continue

                # Extract port mapped to container port 9000
                port = self._extract_port_from_container(container)

                if port:
                    url = f"http://localhost:{port}/sse"
                    sidecars.append(DiscoveredSidecar(
                        name=name,
                        port=port,
                        url=url,
                        container_id=container_id
                    ))
                    logger.info(f"Discovered MCP Sidecar: {name} at {url}")

        except Exception as e:
            logger.error(f"Error during discovery scan: {e}")

        return sidecars

    def _extract_port_from_container(self, container) -> Optional[int]:
        """
        Extract the host port that maps to container port 9000.

        Args:
            container: Docker container object

        Returns:
            Host port number or None if not found
        """
        try:
            ports = container.ports
            # ports is a dict like {'9000/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '9001'}]}
            port_bindings = ports.get('9000/tcp')
            if port_bindings and len(port_bindings) > 0:
                host_port = port_bindings[0].get('HostPort')
                if host_port:
                    return int(host_port)
        except Exception as e:
            logger.debug(f"Failed to extract port from container {container.name}: {e}")
        return None

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
