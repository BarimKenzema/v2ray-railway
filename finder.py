# finder.py - SIMPLIFIED TXT VERSION
import requests
import re
import time
from pathlib import Path
from datetime import datetime
import os

OUTPUT_DIR = Path("configs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Target: Cherry Servers Lithuania
PROVIDER = "Cherry Servers"
COUNTRY = "Lithuania"

SEARCH_QUERIES = [
    "5.199.172", "5.199.171", "5.199.170", "5.199.169",
    "5.199.168", "5.199.167", "5.199.166", "5.199.165",
    "cherryservers vless", "fromblancwithlove",
    "vless lithuania", "vmess lithuania",
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
                print(f"  +{len(items)} files", end=' ')
                
                page += 1
                time.sleep(2)
                
                if len(items) < 30:
                    break
                    
            except Exception as e:
                print(f"  Error: {e}")
                break
        
        return all_items

def extract_configs(text):
    """Extract all V2Ray config formats from text"""
    if not text:
        return []
    
    configs = []
    
    # 1. Extract vless:// links
    vless = re.findall(r'vless://[^\s\n<>"\'\)\]]+', text)
    configs.extend(vless)
    
    # 2. Extract vmess:// links
    vmess = re.findall(r'vmess://[^\s\n<>"\'\)\]]+', text)
    configs.extend(vmess)
    
    # 3. Extract trojan:// links
    trojan = re.findall(r'trojan://[^\s\n<>"\'\)\]]+', text)
    configs.extend(trojan)
    
    # 4. Extract ss:// links (Shadowsocks)
    ss = re.findall(r'ss://[^\s\n<>"\'\)\]]+', text)
    configs.extend(ss)
    
    return configs

def is_cherry_servers(text):
    """Check if content contains Cherry Servers IPs (5.199.160-175)"""
    if not text:
        return False
    return bool(re.search(r'5\.199\.1[6-7]\d', text))

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
    print("🔍 V2Ray Config Finder - Cherry Servers")
    print("=" * 60)
    
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN not found!")
        return
    
    searcher = GitHubSearcher(token)
    
    all_urls = set()
    all_configs = set()  # Use set to auto-deduplicate
    all_ips = set()
    
    # Search
    print("\n🔍 Searching GitHub...\n")
    
    for query in SEARCH_QUERIES:
        print(f"🔎 {query[:40]}", end=' ')
        items = searcher.search_code(query, max_results=50)
        for item in items:
            all_urls.add(item['html_url'])
        print(f"✓")
        time.sleep(2)
    
    print(f"\n🔍 Checking repos...\n")
    
    for repo in POPULAR_REPOS:
        print(f"📦 {repo}", end=' ')
        items = searcher.search_code(f"repo:{repo} 5.199.17", max_results=30)
        for item in items:
            all_urls.add(item['html_url'])
        print(f"✓")
        time.sleep(2)
    
    print(f"\n✓ Found {len(all_urls)} files")
    
    # Download and extract
    print(f"\n📥 Downloading...\n")
    
    for i, url in enumerate(list(all_urls)[:100], 1):
        print(f"[{i:3d}] {url.split('/')[-1][:35]:35s}", end=' ')
        
        content = download_file(url)
        
        if is_cherry_servers(content):
            configs = extract_configs(content)
            ips = extract_cherry_ips(content)
            
            all_configs.update(configs)
            all_ips.update(ips)
            
            print(f"✓ {len(configs):3d} configs, {len(ips):2d} IPs")
        else:
            print("○")
        
        time.sleep(1)
    
    # Save results
    print("\n" + "=" * 60)
    print("💾 Saving results...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. Save all configs (deduplicated)
    config_file = OUTPUT_DIR / f"cherry_servers_configs_{timestamp}.txt"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(f"# Cherry Servers V2Ray Configs - {COUNTRY}\n")
        f.write(f"# Provider: {PROVIDER}\n")
        f.write(f"# IP Range: 5.199.160.0 - 5.199.175.255\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"# Total: {len(all_configs)} unique configs\n")
        f.write(f"#\n")
        f.write(f"# Usage: Copy any line below to your V2Ray client\n")
        f.write(f"#" + "=" * 58 + "\n\n")
        
        for config in sorted(all_configs):
            f.write(f"{config}\n")
    
    # 2. Save IPs
    ip_file = OUTPUT_DIR / f"cherry_servers_ips_{timestamp}.txt"
    with open(ip_file, 'w') as f:
        f.write(f"# Cherry Servers IPs - {COUNTRY}\n")
        f.write(f"# Total: {len(all_ips)} unique IPs\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        for ip in sorted(all_ips):
            f.write(f"{ip}\n")
    
    # 3. Save summary (simple text)
    summary_file = OUTPUT_DIR / f"summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("V2Ray Config Finder - Summary\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Provider:     {PROVIDER}\n")
        f.write(f"Country:      {COUNTRY}\n")
        f.write(f"IP Range:     5.199.160.0 - 5.199.175.255\n")
        f.write(f"Generated:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write(f"Results:\n")
        f.write(f"  Files searched:      {len(all_urls)}\n")
        f.write(f"  Unique configs:      {len(all_configs)}\n")
        f.write(f"  Unique IPs:          {len(all_ips)}\n\n")
        
        if all_ips:
            f.write(f"Cherry Servers IPs Found:\n")
            for ip in sorted(all_ips):
                f.write(f"  • {ip}\n")
    
    # 4. Create "latest" copies
    import shutil
    shutil.copy(config_file, OUTPUT_DIR / "latest_configs.txt")
    shutil.copy(ip_file, OUTPUT_DIR / "latest_ips.txt")
    shutil.copy(summary_file, OUTPUT_DIR / "latest_summary.txt")
    
    # Print summary
    print("=" * 60)
    print("✅ DONE!")
    print("=" * 60)
    print(f"📄 Configs:  {len(all_configs)} unique")
    print(f"📍 IPs:      {len(all_ips)} unique")
    print(f"\nFiles saved:")
    print(f"  • {config_file.name}")
    print(f"  • {ip_file.name}")
    print(f"  • latest_configs.txt (always updated)")
    print(f"  • latest_ips.txt (always updated)")
    
    if all_configs:
        print(f"\n📋 Sample configs (first 3):")
        for config in list(sorted(all_configs))[:3]:
            protocol = config.split('://')[0]
            print(f"  {protocol}:// {config[len(protocol)+3:50]}...")

if __name__ == "__main__":
    main()
