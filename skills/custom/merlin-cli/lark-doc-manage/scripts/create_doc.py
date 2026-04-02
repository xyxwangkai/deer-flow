import sys
import json
import urllib.request
import argparse
import subprocess
import os

def get_jwt_token():
    # Try to get token using merlin-cli
    try:
        result = subprocess.run(['merlin-cli', 'login', '--control-panel', 'cn', 'get-jwt'], capture_output=True, text=True)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get('success'):
                    return data.get('jwt_token')
            except json.JSONDecodeError:
                pass
    except FileNotFoundError:
        pass

    # Fallback: try reading from config file
    home = os.path.expanduser('~')
    config_paths = [
        os.path.join(home, '.merlin-cli', 'auth', 'cn.json'),
        os.path.join(home, '.merlin-cli', 'auth', 'cn-seed.json')
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    if 'jwt_token' in data:
                        return data['jwt_token']
            except:
                continue
                
    return None

def main():
    parser = argparse.ArgumentParser(description='Create Lark Doc from Markdown')
    parser.add_argument('title', help='Title of the document')
    parser.add_argument('markdown_file', help='Path to the markdown file')
    args = parser.parse_args()

    try:
        with open(args.markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    token = get_jwt_token()
    if not token:
        print("Warning: Failed to get JWT token from merlin-cli. Request might fail if authentication is required.")

    url = "https://f47ffxsv.fn.bytedance.net/mcp"
    headers = {
        "Accept": "application/json;text/event-stream",
        "Content-Type": "application/json"
    }
    if token:
        headers["X-Jwt-Token"] = token
    
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "create_lark_doc",
            "arguments": {
                "title": args.title,
                "markdown": content
            }
        }
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode('utf-8')
            try:
                json_data = None
                for line in response_body.split('\n'):
                    if line.startswith('data: '):
                        json_data = line[6:]
                        break
                
                if not json_data:
                    json_data = response_body
                
                resp_json = json.loads(json_data)
                content_text = resp_json.get('result', {}).get('content', [{}])[0].get('text', '')
                if content_text.strip().startswith('{'):
                   print(content_text)
                else:
                   print(content_text)
            except:
                print(response_body)
                
    except Exception as e:
        print(f"Error calling MCP: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
