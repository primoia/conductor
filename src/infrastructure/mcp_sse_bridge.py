import sys
import json
import requests
import threading
import logging
import argparse

# Configure logging to stderr so it doesn't interfere with stdout (MCP protocol)
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='[MCP-BRIDGE] %(message)s')
logger = logging.getLogger(__name__)

def read_sse(url, session_id_event):
    """Reads SSE stream and prints events to stdout."""
    try:
        logger.info(f"Connecting to SSE: {url}")
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("event: endpoint"):
                        # Endpoint event, usually contains the session ID URL or similar
                        pass
                    elif decoded_line.startswith("data:"):
                        data_str = decoded_line[5:].strip()
                        try:
                            data = json.loads(data_str)
                            # If this is the initial connection, we might get a session_id
                            # But usually MCP SSE returns the endpoint in the 'endpoint' event
                            # or we just get JSON-RPC messages in 'message' event
                            
                            # For MCP, we expect 'message' events containing JSON-RPC
                            # But first we might get the endpoint
                            pass
                        except:
                            pass
                            
                    # We need to handle the specific MCP SSE protocol details
                    # According to spec:
                    # event: endpoint
                    # data: /messages?session_id=...
                    
                    if decoded_line.startswith("event: endpoint"):
                        # Read the next line which should be data
                        continue
                        
                    if decoded_line.startswith("data:"):
                        data_str = decoded_line[5:].strip()
                        # Check if it's a URL (endpoint) or JSON-RPC
                        if data_str.startswith("/"):
                            # It's the session endpoint
                            session_id_event.set_endpoint(data_str)
                            logger.info(f"Session endpoint received: {data_str}")
                        else:
                            # Assume it's a JSON-RPC message
                            print(data_str)
                            sys.stdout.flush()
                            
    except Exception as e:
        logger.error(f"SSE Error: {e}")
        sys.exit(1)

class SessionInfo:
    def __init__(self):
        self.endpoint = None
        self.event = threading.Event()
        
    def set_endpoint(self, endpoint):
        self.endpoint = endpoint
        self.event.set()
        
    def wait_for_endpoint(self):
        self.event.wait()
        return self.endpoint

def main():
    parser = argparse.ArgumentParser(description="MCP SSE Bridge")
    parser.add_argument("url", help="Base URL of the MCP server (e.g. http://localhost:9000)")
    args = parser.parse_args()
    
    base_url = args.url.rstrip("/")
    sse_url = f"{base_url}/sse"
    
    session_info = SessionInfo()
    
    # Start SSE reader thread
    t = threading.Thread(target=read_sse, args=(sse_url, session_info), daemon=True)
    t.start()
    
    # Wait for session endpoint
    endpoint = session_info.wait_for_endpoint()
    post_url = f"{base_url}{endpoint}"
    
    # Read stdin loop
    for line in sys.stdin:
        try:
            # Parse just to validate, but we forward raw string mostly
            # Actually, we should forward the JSON object
            msg = json.loads(line)
            
            # Post to the session endpoint
            response = requests.post(post_url, json=msg)
            response.raise_for_status()
            
            # Note: The response to the POST is usually "Accepted", 
            # the actual result comes via SSE.
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON received on stdin")
        except Exception as e:
            logger.error(f"Error posting message: {e}")

if __name__ == "__main__":
    main()
