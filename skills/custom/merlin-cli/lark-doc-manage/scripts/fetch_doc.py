import sys
import json
import urllib.request
import argparse
import os
import subprocess

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
    parser = argparse.ArgumentParser(description='Fetch Lark Doc to Markdown')
    parser.add_argument('doc_id', help='Document ID or URL')
    parser.add_argument('output_path', help='Path to save the markdown file')
    args = parser.parse_args()

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
            "name": "fetch_lark_doc",
            "arguments": {
                "doc_id": args.doc_id
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
                content_list = resp_json.get('result', {}).get('content', [])
                if not content_list:
                     print(f"No content in response: {response_body}")
                     sys.exit(1)
                     
                content_text = content_list[0].get('text', '')
                
                try:
                    data = json.loads(content_text)
                    markdown_content = data.get('markdown', '')
                except json.JSONDecodeError:
                    print(f"Response is not valid JSON content: {content_text}")
                    sys.exit(1)

                output_dir = os.path.dirname(args.output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    
                with open(args.output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                print(f"Successfully saved document to {args.output_path}")
                
            except Exception as e:
                print(f"Error processing content: {e}")
                print(f"Raw response: {response_body[:500]}")
                sys.exit(1)
                
    except Exception as e:
        print(f"Error calling MCP: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
