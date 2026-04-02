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
    parser = argparse.ArgumentParser(description='Edit Lark Doc with Markdown')
    parser.add_argument('doc_id', help='ID of the Lark document or URL')
    parser.add_argument('markdown_file', help='Path to the markdown file')
    parser.add_argument('--mode', choices=['overwrite', 'append', 'replace_range', 'replace_all', 'insert_before', 'insert_after', 'delete_range'], default='overwrite', help='Update mode')
    parser.add_argument('--new_title', help='New title for the document (optional)')
    parser.add_argument('--selection_by_title', help='Select section by title (e.g. "## Title")')
    parser.add_argument('--selection_with_ellipsis', help='Select section by content (e.g. "Start...End")')
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
    
    arguments = {
        "doc_id": args.doc_id,
        "markdown": content,
        "mode": args.mode
    }
    
    if args.new_title:
        arguments['new_title'] = args.new_title
    if args.selection_by_title:
        arguments['selection_by_title'] = args.selection_by_title
    if args.selection_with_ellipsis:
        arguments['selection_with_ellipsis'] = args.selection_with_ellipsis

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "update_lark_doc",
            "arguments": arguments
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
