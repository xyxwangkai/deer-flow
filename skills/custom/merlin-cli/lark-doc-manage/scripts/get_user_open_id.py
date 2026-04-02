import sys
import json
import urllib.request
import argparse

def main():
    parser = argparse.ArgumentParser(description='Get Lark User Open ID by Email Prefix')
    parser.add_argument('email_prefix', help='Email prefix or full email address')
    args = parser.parse_args()

    url = "https://f47ffxsv.fn.bytedance.net/mcp"
    headers = {
        "Accept": "application/json;text/event-stream",
        "Content-Type": "application/json"
    }
    
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_user_open_id_by_email",
            "arguments": {
                "email_prefix": args.email_prefix
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
