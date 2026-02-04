# finder.py - FIXED VERSION - Only Cherry Servers configs
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

SEARCH_QUERIES = [
    "5.199.172", "5.199.171", "5.199.170", "5.199.169",
    "5.199.168", "5.199.167", "5.199.166", "5.199.165",
    "5.199.164", "5.199.163", "5.199.162", "5.199.161", "5.199.160",
    "cherryservers vless", "fromblancwithlove",
]

POPULAR_REPOS = [
    "yebekhe/TelegramV2rayCollector",
    "barry-far/V2ray-Configs",
    "mfuu/v2ray",
    "mahdibland/V2RayAggregator",
]

class GitHubSearcher:
    def __init__(self, token):
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_code(self, query, max_results=50):
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
                print(f"  Error: {e}")
                break
        
        return all_items

def is_cherry_ip(ip_or_domain):
    """Check if IP is Cherry Servers (5.199.160-175.*)"""
    # Extract IP if it's in the string
    match = re.search(r'\b5\.199\.1[6-7]\d\.\d+\b', ip_or_domain)
    return bool(match)

def extract_ip_from_config(config):
    """Extract IP/domain from config string"""
    try:
        # For vless://, vmess://, trojan://, ss://
        if '://' in config:
            # Remove protocol
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
            
            # For vless, trojan, ss - format: protocol://uuid@IP:port
            if '@' in after_protocol:
                # Get part after @
                after_at = after_protocol.split('@', 1)[1]
                # Get IP before :
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
    
    # Filter: Keep only configs that use Cherry Servers IPs
    cherry_configs = []
    
    for config in all_configs:
        ip_or_domain = extract_ip_from_config(config)
        
        if is_cherry_ip(ip_or_domain):
            cherry_configs.append(config)
            print(f"    ✓ Cherry: {ip_or_domain}")
    
    return cherry_configs

def extract_cherry_ips(text):
    """Extract Cherry Servers IPs"""
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
    print("\n🔍 Searching...\n")
    
    for query in SEARCH_QUERIES:
        print(f"🔎 {query[:40]}", end=' ')
        items = searcher.search_code(query, max_results=50)
        for item in items:
            all_urls.add(item['html_url'])
        print(f"✓")
        time.sleep(2)
    
    for repo in POPULAR_REPOS:
        print(f"📦 {repo}", end=' ')
        items = searcher.search_code(f"repo:{repo} 5.199.17", max_results=30)
        for item in items:
            all_urls.add(item['html_url'])
        print(f"✓")
        time.sleep(2)
    
    print(f"\n✓ Found {len(all_urls)} files to check")
    
    # Download and extract
    print(f"\n📥 Filtering for Cherry Servers configs...\n")
    
    for i, url in enumerate(list(all_urls)[:100], 1):
        print(f"[{i:3d}] {url.split('/')[-1][:35]:35s}")
        
        content = download_file(url)
        
        if content and '5.199.1' in content:  # Quick pre-check
            configs = extract_configs(content)  # Only returns Cherry configs
            ips = extract_cherry_ips(content)
            
            if configs:
                all_configs.update(configs)
                all_ips.update(ips)
                print(f"      → Found {len(configs)} Cherry configs")
        
        time.sleep(1)
    
    # Save results
    print("\n" + "=" * 60)
    print("💾 Saving...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save configs
    config_file = OUTPUT_DIR / f"cherry_servers_configs_{timestamp}.txt"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(f"# Cherry Servers V2Ray Configs - {COUNTRY}\n")
        f.write(f"# Provider: {PROVIDER}\n")
        f.write(f"# IP Range: 5.199.160.0 - 5.199.175.255 ONLY\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"# Total: {len(all_configs)} configs\n")
        f.write(f"#" + "=" * 58 + "\n\n")
        
        for config in sorted(all_configs):
            f.write(f"{config}\n")
    
    # Save IPs
    ip_file = OUTPUT_DIR / f"cherry_servers_ips_{timestamp}.txt"
    with open(ip_file, 'w') as f:
        f.write(f"# Cherry Servers IPs - {COUNTRY}\n")
        f.write(f"# Range: 5.199.160.0 - 5.199.175.255\n")
        f.write(f"# Total: {len(all_ips)} IPs\n\n")
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
        f.write(f"Results:\n")
        f.write(f"  Files checked:       {len(all_urls)}\n")
        f.write(f"  Cherry configs:      {len(all_configs)}\n")
        f.write(f"  Unique Cherry IPs:   {len(all_ips)}\n\n")
        
        if all_ips:
            f.write(f"Cherry Servers IPs:\n")
            for ip in sorted(all_ips):
                f.write(f"  • {ip}\n")
        
        if all_configs:
            f.write(f"\nSample configs:\n")
            for config in list(sorted(all_configs))[:5]:
                protocol = config.split('://')[0]
                ip = extract_ip_from_config(config)
                f.write(f"  • {protocol}:// → {ip}\n")
    
    # Create latest
    import shutil
    shutil.copy(config_file, OUTPUT_DIR / "latest_configs.txt")
    shutil.copy(ip_file, OUTPUT_DIR / "latest_ips.txt")
    shutil.copy(summary_file, OUTPUT_DIR / "latest_summary.txt")
    
    # Print summary
    print("=" * 60)
    print("✅ DONE!")
    print("=" * 60)
    print(f"📄 Cherry Configs:  {len(all_configs)}")
    print(f"📍 Cherry IPs:      {len(all_ips)}")
    
    if all_ips:
        print(f"\n📍 Cherry Servers IPs found:")
        for ip in sorted(all_ips):
            print(f"  • {ip}")
    
    if all_configs:
        print(f"\n📋 Sample configs:")
        for config in list(sorted(all_configs))[:3]:
            ip = extract_ip_from_config(config)
            print(f"  {config[:60]}... → {ip}")

if __name__ == "__main__":
    main()
