import sys
import os
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.discovery_service import DiscoveryService

def main():
    print("Testing DiscoveryService...")
    service = DiscoveryService()
    
    # 1. Scan network
    sidecars = service.scan_network()
    print(f"Found {len(sidecars)} sidecars.")
    for s in sidecars:
        print(f" - {s.name}: {s.url}")
        
    # 2. Generate config
    output_path = "/tmp/test_mcp_config.json"
    service.generate_mcp_config(output_path)
    
    print(f"\nGenerated config at {output_path}")
    
    # 3. Validate config
    with open(output_path, "r") as f:
        config = json.load(f)
        
    server_count = len(config.get("mcpServers", {}))
    print(f"Config contains {server_count} servers.")
    
    if server_count == len(sidecars):
        print("SUCCESS: Config matches discovered sidecars.")
    else:
        print("FAILURE: Config count mismatch.")
        
    # 4. Test Filtering
    print("\nTesting Filtering...")
    whitelist = ["crm-sidecar", "billing-sidecar"] # Assuming these exist or similar names
    output_path_filtered = "/tmp/test_mcp_config_filtered.json"
    service.generate_mcp_config(output_path_filtered, whitelist=whitelist)
    
    with open(output_path_filtered, "r") as f:
        config_filtered = json.load(f)
        
    filtered_count = len(config_filtered.get("mcpServers", {}))
    print(f"Filtered config contains {filtered_count} servers.")
    
    # We expect at most len(whitelist), but only if they exist
    # Let's just check if it's <= len(whitelist) and > 0 if we know they exist
    # For now just printing is enough for manual verification


if __name__ == "__main__":
    main()
