# finder.py - SMARTER SEARCH
import requests
import re
import time
from pathlib import Path
from datetime import datetime
import os

OUTPUT_DIR = Path("configs")
OUTPUT_DIR.mkdir(exist_ok=True)

PROVIDER = "Cherry Servers"
COUNTRY = "Lithuania"

# ⚠️ NEW STRATEGY: Search for V2Ray patterns + IPs, not just IPs
SEARCH_QUERIES = [
    # V2Ray specific searches with IPs
    'vless "5.199.17"',
    'vmess "5.199.17"',
    '"protocol":"vless" "5.199.17"',
    '"protocol":"vmess" "5.199.17"',
    
    # Domain-based (more reliable)
    "fromblancwithlove",
    
    # Protocol + Lithuania
    "vless lithuania extension:txt",
    "vmess lithuania extension:txt",
    
    # File type specific
    'vless:// "5.199" extension:txt',
    'vmess:// "5.199" extension:txt',
]

# Focus ONLY on known V2Ray repositories
V2RAY_REPOS = [
    "yebekhe/TelegramV2rayCollector",
    "barry-far/V2ray-Configs",
    "mfuu/v2ray",
    "mahdibland/V2RayAggregator",
    "peasoft/NoMoreWalls",
    "aiboboxx/v2rayfree",
    "itsyebekhe/HiN-VPN",
    "Pawdroid/Free-servers",
    "resasanian/Mirza",
    "Leon406/SubCrawler",
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

def is_v2ray_config_file(content):
    """Check if file actually contains V2Ray configs"""
    if not content:
        return False
    
    # Must contain V2Ray protocol indicators
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
                    decoded = base64.b64decode(after_protocol).decode('utf-8')
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
            cherry_configs.append(config)
    
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
    print("🔍 V2Ray Config Finder - Cherry Servers ONLY")
    print("=" * 60)
    print("Strategy: Search V2Ray repos for Cherry IPs")
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
    
    # Strategy 1: Search V2Ray-specific queries
    print("\n🔍 Phase 1: V2Ray-specific searches...\n")
    
    for query in SEARCH_QUERIES:
        print(f"🔎 {query[:50]}", end=' ')
        items = searcher.search_code(query, max_results=30)
        for item in items:
            all_urls.add(item['html_url'])
        print(f"✓ ({len(all_urls)} total)")
        time.sleep(3)
    
    # Strategy 2: Search known V2Ray repos
    print(f"\n🔍 Phase 2: Known V2Ray repositories...\n")
    
    for repo in V2RAY_REPOS:
        print(f"📦 {repo[:40]}", end=' ')
        
        # Search for Cherry IPs in this repo
        items = searcher.search_code(f'repo:{repo} "5.199.17"', max_results=20)
        for item in items:
            all_urls.add(item['html_url'])
        
        print(f"✓ ({len(all_urls)} total)")
        time.sleep(3)
    
    print(f"\n✓ Found {len(all_urls)} unique files")
    
    # Download and filter
    print(f"\n📥 Phase 3: Extracting Cherry configs...\n")
    
    for i, url in enumerate(list(all_urls)[:100], 1):
        filename = url.split('/')[-1][:40]
        print(f"[{i:3d}] {filename:40s}", end=' ')
        
        content = download_file(url)
        
        # Check if it's actually a V2Ray config file
        if not is_v2ray_config_file(content):
            print("○ Not V2Ray")
            continue
        
        # Extract Cherry configs
        configs = extract_configs(content)
        ips = extract_cherry_ips(content)
        
        if configs:
            all_configs.update(configs)
            all_ips.update(ips)
            print(f"✓ {len(configs)} Cherry configs!")
        else:
            print("○ No Cherry")
        
        time.sleep(1)
    
    # Save results
    print("\n" + "=" * 60)
    print("💾 Saving results...")
    print("=" * 60)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save configs
    config_file = OUTPUT_DIR / f"cherry_servers_configs_{timestamp}.txt"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(f"# Cherry Servers V2Ray Configs - {COUNTRY}\n")
        f.write(f"# Provider: {PROVIDER}\n")
        f.write(f"# IP Range: 5.199.160.0 - 5.199.175.255\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"# Total: {len(all_configs)} unique configs\n")
        f.write(f"#\n")
        f.write(f"# Copy any line to your V2Ray client\n")
        f.write(f"#" + "=" * 58 + "\n\n")
        
        for config in sorted(all_configs):
            ip = extract_ip_from_config(config)
            f.write(f"{config}  # IP: {ip}\n")
    
    # Save IPs
    ip_file = OUTPUT_DIR / f"cherry_servers_ips_{timestamp}.txt"
    with open(ip_file, 'w') as f:
        f.write(f"# Cherry Servers IPs\n")
        f.write(f"# Range: 5.199.160.0 - 5.199.175.255\n")
        f.write(f"# Total: {len(all_ips)}\n\n")
        for ip in sorted(all_ips):
            f.write(f"{ip}\n")
    
    # Save summary
    summary_file = OUTPUT_DIR / f"summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("Cherry Servers V2Ray Configs - Summary\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Provider:     {PROVIDER}\n")
        f.write(f"Country:      {COUNTRY}\n")
        f.write(f"IP Range:     5.199.160.0 - 5.199.175.255\n")
        f.write(f"Generated:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write(f"Search Strategy:\n")
        f.write(f"  1. V2Ray-specific queries with IPs\n")
        f.write(f"  2. Known V2Ray config repositories\n")
        f.write(f"  3. Filter out non-V2Ray files\n\n")
        f.write(f"Results:\n")
        f.write(f"  Files checked:       {len(all_urls)}\n")
        f.write(f"  Cherry configs:      {len(all_configs)}\n")
        f.write(f"  Unique Cherry IPs:   {len(all_ips)}\n\n")
        
        if all_ips:
            f.write(f"Cherry Servers IPs:\n")
            for ip in sorted(all_ips):
                f.write(f"  • {ip}\n")
        else:
            f.write("⚠️  No Cherry Servers configs found.\n")
            f.write("Possible reasons:\n")
            f.write("  - Configs may be temporary/deleted\n")
            f.write("  - IPs may not be in public repos\n")
            f.write("  - Try manual search on subscription sites\n")
    
    # Create latest
    import shutil
    shutil.copy(config_file, OUTPUT_DIR / "latest_configs.txt")
    shutil.copy(ip_file, OUTPUT_DIR / "latest_ips.txt")
    shutil.copy(summary_file, OUTPUT_DIR / "latest_summary.txt")
    
    # Print summary
    print("\n✅ DONE!")
    print("=" * 60)
    print(f"📄 Cherry Configs:  {len(all_configs)}")
    print(f"📍 Cherry IPs:      {len(all_ips)}")
    
    if all_ips:
        print(f"\n📍 IPs:")
        for ip in sorted(all_ips):
            print(f"  • {ip}")
    
    if all_configs:
        print(f"\n📋 Sample configs:")
        for config in list(sorted(all_configs))[:3]:
            ip = extract_ip_from_config(config)
            protocol = config.split('://')[0]
            print(f"  {protocol}:// → {ip}")
    else:
        print("\n⚠️  No Cherry Servers configs found in GitHub")
        print("💡 Try these alternatives:")
        print("  1. Check subscription sites directly")
        print("  2. Search Telegram channels")
        print("  3. Your working config might be private/deleted")

if __name__ == "__main__":
    main()
