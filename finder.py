# finder.py - FIXED VERSION
import requests
import re
import time
from pathlib import Path
from datetime import datetime
import os
import html

OUTPUT_DIR = Path("configs")
OUTPUT_DIR.mkdir(exist_ok=True)

PROVIDER = "Cherry Servers"
COUNTRY = "Lithuania"

SEARCH_QUERIES = [
    'vless "5.199.17"',
    'vmess "5.199.17"',
    '"protocol":"vless" "5.199.17"',
    '"protocol":"vmess" "5.199.17"',
    "fromblancwithlove",
    "vless lithuania extension:txt",
    "vmess lithuania extension:txt",
    'vless:// "5.199" extension:txt',
    'vmess:// "5.199" extension:txt',
]

V2RAY_REPOS = [
    "yebekhe/TelegramV2rayCollector",
    "barry-far/V2ray-Configs",
    "mfuu/v2ray",
    "mahdibland/V2RayAggregator",
    "peasoft/NoMoreWalls",
    "aiboboxx/v2rayfree",
    "itsyebekhe/HiN-VPN",
    "Pawdroid/Free-servers",
]

class GitHubSearcher:
    def __init__(self, token):
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_code(self, query, max_results=30):
        all_items = []
        page = 1
        
        while len(all_items) < max_results:
            url = f"https://api.github.com/search/code?q={query}&per_page=30&page={page}"
            
            try:
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 403:
                    print(f"  ⏳ Rate limited, waiting 60s...")
                    time.sleep(60)
                    continue
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break
                
                all_items.extend(items)
                print(f"  +{len(items)}", end=' ')
                
                page += 1
                time.sleep(2)
                
                if len(items) < 30:
                    break
                    
            except Exception as e:
                print(f"  ❌ {e}")
                break
        
        return all_items

def clean_config(config):
    """Clean config URL - decode HTML entities"""
    # Decode HTML entities like &amp; to &
    config = html.unescape(config)
    return config.strip()

def is_v2ray_config_file(content):
    """Check if file actually contains V2Ray configs"""
    if not content:
        return False
    
    v2ray_indicators = [
        'vless://',
        'vmess://',
        'trojan://',
        '"protocol":"vless"',
        '"protocol":"vmess"',
        '"protocol":"trojan"',
    ]
    
    return any(indicator in content for indicator in v2ray_indicators)

def is_cherry_ip(ip_or_domain):
    """Check if IP is Cherry Servers (5.199.160-175.*)"""
    match = re.search(r'\b5\.199\.1[6-7]\d\.\d+\b', str(ip_or_domain))
    return bool(match)

def extract_ip_from_config(config):
    """Extract IP/domain from config string"""
    try:
        if '://' in config:
            after_protocol = config.split('://', 1)[1]
            
            # For vmess (base64 encoded)
            if config.startswith('vmess://'):
                import base64
                try:
                    decoded = base64.b64decode(after_protocol.split('#')[0]).decode('utf-8')
                    import json
                    data = json.loads(decoded)
                    return data.get('add', '')
                except:
                    return ''
            
            # For vless, trojan, ss
            if '@' in after_protocol:
                after_at = after_protocol.split('@', 1)[1]
                ip_part = after_at.split(':')[0].split('?')[0]
                return ip_part
    except:
        pass
    
    return ''

def extract_configs(text):
    """Extract ONLY Cherry Servers configs"""
    if not text:
        return []
    
    all_configs = []
    
    # Extract all protocol links
    all_configs.extend(re.findall(r'vless://[^\s\n<>"\'\)\]]+', text))
    all_configs.extend(re.findall(r'vmess://[^\s\n<>"\'\)\]]+', text))
    all_configs.extend(re.findall(r'trojan://[^\s\n<>"\'\)\]]+', text))
    all_configs.extend(re.findall(r'ss://[^\s\n<>"\'\)\]]+', text))
    
    # Filter: Keep only Cherry Servers configs
    cherry_configs = []
    
    for config in all_configs:
        ip_or_domain = extract_ip_from_config(config)
        
        if is_cherry_ip(ip_or_domain):
            # Clean the config
            cleaned = clean_config(config)
            cherry_configs.append(cleaned)
    
    return cherry_configs

def extract_cherry_ips(text):
    """Extract Cherry Servers IPs from text"""
    return set(re.findall(r'5\.199\.1[6-7]\d\.\d+', text))

def download_file(url):
    """Download file from GitHub"""
    try:
        raw_url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        response = requests.get(raw_url, timeout=15)
        return response.text
    except:
        return None

def main():
    print("=" * 60)
    print("🔍 V2Ray Config Finder - Cherry Servers")
    print("=" * 60)
    print("Target: 5.199.160.0 - 5.199.175.255")
    print("=" * 60)
    
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN not found!")
        return
    
    searcher = GitHubSearcher(token)
    
    all_urls = set()
    all_configs = set()
    all_ips = set()
    
    # Search
    print("\n🔍 Phase 1: V2Ray searches...\n")
    
    for query in SEARCH_QUERIES:
        print(f"🔎 {query[:50]}", end=' ')
        items = searcher.search_code(query, max_results=30)
        for item in items:
            all_urls.add(item['html_url'])
        print(f"✓")
        time.sleep(3)
    
    print(f"\n🔍 Phase 2: V2Ray repos...\n")
    
    for repo in V2RAY_REPOS:
        print(f"📦 {repo[:40]}", end=' ')
        items = searcher.search_code(f'repo:{repo} "5.199.17"', max_results=20)
        for item in items:
            all_urls.add(item['html_url'])
        print(f"✓")
        time.sleep(3)
    
    print(f"\n✓ Found {len(all_urls)} files")
    
    # Download and extract
    print(f"\n📥 Phase 3: Extracting...\n")
    
    for i, url in enumerate(list(all_urls)[:100], 1):
        filename = url.split('/')[-1][:40]
        print(f"[{i:3d}] {filename:40s}", end=' ')
        
        content = download_file(url)
        
        if not is_v2ray_config_file(content):
            print("○")
            continue
        
        configs = extract_configs(content)
        ips = extract_cherry_ips(content)
        
        if configs:
            all_configs.update(configs)
            all_ips.update(ips)
            print(f"✓ {len(configs)}")
        else:
            print("○")
        
        time.sleep(1)
    
    # Save results
    print("\n" + "=" * 60)
    print("💾 Saving...")
    print("=" * 60)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save configs (NO COMMENTS, just pure configs)
    config_file = OUTPUT_DIR / f"cherry_servers_configs_{timestamp}.txt"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(f"# Cherry Servers V2Ray Configs - {COUNTRY}\n")
        f.write(f"# Provider: {PROVIDER}\n")
        f.write(f"# IP Range: 5.199.160.0 - 5.199.175.255\n")
        f.write(f"# Total: {len(all_configs)} configs\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write(f"#\n")
        f.write(f"# Copy any line to V2rayNG\n")
        f.write(f"#" + "=" * 58 + "\n\n")
        
        # Just write the config, NO extra comments
        for config in sorted(all_configs):
            f.write(f"{config}\n")
    
    # Save IPs
    ip_file = OUTPUT_DIR / f"cherry_servers_ips_{timestamp}.txt"
    with open(ip_file, 'w') as f:
        f.write(f"# Cherry Servers IPs\n")
        f.write(f"# Total: {len(all_ips)}\n\n")
        for ip in sorted(all_ips):
            f.write(f"{ip}\n")
    
    # Save summary
    summary_file = OUTPUT_DIR / f"summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("Cherry Servers Configs - Summary\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Provider:     {PROVIDER}\n")
        f.write(f"Country:      {COUNTRY}\n")
        f.write(f"IP Range:     5.199.160.0 - 5.199.175.255\n")
        f.write(f"Generated:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write(f"Results:\n")
        f.write(f"  Configs:      {len(all_configs)}\n")
        f.write(f"  Unique IPs:   {len(all_ips)}\n\n")
        
        f.write(f"Cherry IPs:\n")
        for ip in sorted(all_ips):
            f.write(f"  • {ip}\n")
    
    # Create latest
    import shutil
    shutil.copy(config_file, OUTPUT_DIR / "latest_configs.txt")
    shutil.copy(ip_file, OUTPUT_DIR / "latest_ips.txt")
    shutil.copy(summary_file, OUTPUT_DIR / "latest_summary.txt")
    
    # Print summary
    print("\n✅ DONE!")
    print("=" * 60)
    print(f"📄 Configs:  {len(all_configs)}")
    print(f"📍 IPs:      {len(all_ips)}")
    
    if all_ips:
        print(f"\n📍 IPs found:")
        for ip in sorted(all_ips):
            print(f"  • {ip}")
    
    print(f"\n✅ Ready for V2rayNG!")
    print(f"📱 Import from: latest_configs.txt")

if __name__ == "__main__":
    main()
