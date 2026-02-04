# finder.py
import requests
import json
import time
import re
from pathlib import Path
from datetime import datetime

# Configuration
GITHUB_TOKEN = ""  # Will be set from GitHub Secrets
OUTPUT_DIR = Path("configs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Target: Cherry Servers Lithuania
PROVIDER = "Cherry Servers"
IP_RANGES = [(5, 199, 160, 175)]  # 5.199.160.0 - 5.199.175.255
COUNTRY = "Lithuania"

SEARCH_QUERIES = [
    "5.199.172",
    "5.199.171",
    "5.199.170",
    "5.199.169",
    "5.199.168",
    "5.199.167",
    "5.199.166",
    "5.199.165",
    "5.199.164",
    "5.199.163",
    "5.199.162",
    "5.199.161",
    "5.199.160",
    "cherryservers vless",
    "cherry servers vmess",
    "fromblancwithlove",
    "vless lithuania",
    "vmess lithuania",
]

POPULAR_REPOS = [
    "yebekhe/TelegramV2rayCollector",
    "barry-far/V2ray-Configs",
    "mfuu/v2ray",
    "mahdibland/V2RayAggregator",
    "peasoft/NoMoreWalls",
    "itsyebekhe/HiN-VPN",
    "Pawdroid/Free-servers",
    "aiboboxx/v2rayfree",
]

class GitHubSearcher:
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def check_rate_limit(self):
        """Check remaining API calls"""
        try:
            r = self.session.get("https://api.github.com/rate_limit", timeout=10)
            data = r.json()
            remaining = data['resources']['search']['remaining']
            reset = data['resources']['search']['reset']
            return remaining, reset
        except:
            return 0, 0
    
    def search_code(self, query, max_results=100):
        """Search GitHub code"""
        all_items = []
        page = 1
        
        while len(all_items) < max_results:
            remaining, reset = self.check_rate_limit()
            
            if remaining < 2:
                wait_time = reset - time.time() + 5
                print(f"  ⏳ Rate limit reached. Waiting {int(wait_time/60)} minutes...")
                if wait_time > 300:  # More than 5 minutes
                    print(f"  ⏭️  Skipping this query to save time")
                    break
                time.sleep(min(wait_time, 60))
            
            url = f"https://api.github.com/search/code?q={query}&per_page=30&page={page}"
            
            try:
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    print(f"  ❌ Status: {response.status_code}")
                    break
                
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break
                
                all_items.extend(items)
                print(f"  📄 Page {page}: +{len(items)} files (total: {len(all_items)})")
                
                page += 1
                time.sleep(2)  # Be nice to GitHub
                
                if len(items) < 30:  # Last page
                    break
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                break
        
        return all_items

def is_cherry_servers(text):
    """Check if content contains Cherry Servers IPs"""
    if not text:
        return False
    
    # Check for IP range 5.199.160-175
    pattern = r'5\.199\.1[6-7]\d\.\d+'
    return bool(re.search(pattern, text))

def extract_cherry_ips(text):
    """Extract all Cherry Servers IPs"""
    pattern = r'5\.199\.1[6-7]\d\.\d+'
    return set(re.findall(pattern, text))

def extract_configs(text):
    """Extract V2Ray/VLESS/VMess configs"""
    configs = []
    
    # Extract vless:// and vmess:// links
    vless = re.findall(r'vless://[^\s\n<>"\'\)]+', text)
    vmess = re.findall(r'vmess://[^\s\n<>"\'\)]+', text)
    
    configs.extend(vless)
    configs.extend(vmess)
    
    # Try to extract JSON configs
    try:
        # Look for JSON objects with "protocol" field
        json_pattern = r'\{[^{}]*"protocol"[^{}]*\}'
        potential_jsons = re.findall(json_pattern, text)
        
        for pj in potential_jsons:
            try:
                obj = json.loads(pj)
                if obj.get('protocol') in ['vless', 'vmess', 'trojan']:
                    configs.append(json.dumps(obj, ensure_ascii=False))
            except:
                pass
    except:
        pass
    
    return configs

def download_file(url):
    """Download file content"""
    try:
        # Convert to raw URL
        raw_url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        response = requests.get(raw_url, timeout=15)
        return response.text
    except:
        return None

def main():
    global GITHUB_TOKEN
    
    print("=" * 60)
    print("🔍 V2Ray Config Finder - Cherry Servers Edition")
    print("=" * 60)
    print(f"Provider: {PROVIDER}")
    print(f"IP Range: 5.199.160.0 - 5.199.175.255")
    print(f"Country: {COUNTRY}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    # Get token from environment or parameter
    import os
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', GITHUB_TOKEN)
    
    if not GITHUB_TOKEN:
        print("❌ GitHub token not found!")
        return
    
    searcher = GitHubSearcher(GITHUB_TOKEN)
    
    all_urls = set()
    all_ips = set()
    all_configs = []
    
    # Search GitHub
    print("\n🔍 Phase 1: Searching GitHub...\n")
    
    for i, query in enumerate(SEARCH_QUERIES, 1):
        print(f"[{i}/{len(SEARCH_QUERIES)}] Query: {query}")
        items = searcher.search_code(query, max_results=50)
        
        for item in items:
            all_urls.add(item['html_url'])
        
        time.sleep(2)
    
    # Search popular repos
    print(f"\n🔍 Phase 2: Searching popular repositories...\n")
    
    for i, repo in enumerate(POPULAR_REPOS, 1):
        print(f"[{i}/{len(POPULAR_REPOS)}] Repo: {repo}")
        
        query = f"repo:{repo} 5.199.17"
        items = searcher.search_code(query, max_results=30)
        
        for item in items:
            all_urls.add(item['html_url'])
        
        time.sleep(2)
    
    print(f"\n✓ Found {len(all_urls)} unique files")
    
    # Download and filter
    print(f"\n📥 Phase 3: Downloading and filtering...\n")
    
    cherry_files = []
    
    for i, url in enumerate(list(all_urls)[:100], 1):  # Limit to 100
        print(f"[{i}/100] {url.split('/')[-1][:40]}", end=' ')
        
        content = download_file(url)
        
        if is_cherry_servers(content):
            print("✓ Cherry Servers!")
            
            # Extract IPs
            ips = extract_cherry_ips(content)
            all_ips.update(ips)
            
            # Extract configs
            configs = extract_configs(content)
            all_configs.extend(configs)
            
            cherry_files.append({
                'url': url,
                'ips': list(ips),
                'config_count': len(configs)
            })
        else:
            print("○")
        
        if i >= 100:
            break
        
        time.sleep(1)
    
    # Save results
    print("\n" + "=" * 60)
    print("💾 Saving results...")
    print("=" * 60)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. Save Cherry Servers IPs
    ip_file = OUTPUT_DIR / f"cherry_servers_ips_{timestamp}.txt"
    with open(ip_file, 'w') as f:
        f.write(f"# Cherry Servers IPs - {COUNTRY}\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"# Total IPs: {len(all_ips)}\n\n")
        for ip in sorted(all_ips):
            f.write(f"{ip}\n")
    
    print(f"✓ Saved {len(all_ips)} IPs to {ip_file.name}")
    
    # 2. Save configs
    config_file = OUTPUT_DIR / f"cherry_servers_configs_{timestamp}.txt"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(f"# Cherry Servers V2Ray Configs - {COUNTRY}\n")
        f.write(f"# Provider: {PROVIDER}\n")
        f.write(f"# IP Range: 5.199.160.0 - 5.199.175.255\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"# Total configs: {len(all_configs)}\n\n")
        
        for config in all_configs:
            f.write(f"{config}\n")
    
    print(f"✓ Saved {len(all_configs)} configs to {config_file.name}")
    
    # 3. Save summary JSON
    summary = {
        "provider": PROVIDER,
        "country": COUNTRY,
        "ip_range": "5.199.160.0 - 5.199.175.255",
        "generated_at": datetime.now().isoformat(),
        "stats": {
            "files_searched": len(all_urls),
            "cherry_files_found": len(cherry_files),
            "unique_ips": len(all_ips),
            "configs_found": len(all_configs)
        },
        "ips": sorted(list(all_ips)),
        "files": cherry_files
    }
    
    summary_file = OUTPUT_DIR / f"summary_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved summary to {summary_file.name}")
    
    # 4. Update latest symlinks
    latest_ip = OUTPUT_DIR / "latest_ips.txt"
    latest_config = OUTPUT_DIR / "latest_configs.txt"
    latest_summary = OUTPUT_DIR / "latest_summary.json"
    
    if latest_ip.exists():
        latest_ip.unlink()
    if latest_config.exists():
        latest_config.unlink()
    if latest_summary.exists():
        latest_summary.unlink()
    
    # Copy as latest
    import shutil
    shutil.copy(ip_file, latest_ip)
    shutil.copy(config_file, latest_config)
    shutil.copy(summary_file, latest_summary)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    print(f"Provider: {PROVIDER}")
    print(f"Country: {COUNTRY}")
    print(f"IP Range: 5.199.160.0 - 5.199.175.255")
    print(f"\nResults:")
    print(f"  • Files searched: {len(all_urls)}")
    print(f"  • Cherry Servers files: {len(cherry_files)}")
    print(f"  • Unique IPs found: {len(all_ips)}")
    print(f"  • Configs extracted: {len(all_configs)}")
    
    if all_ips:
        print(f"\n📍 Cherry Servers IPs found:")
        for ip in sorted(list(all_ips)[:20]):
            print(f"   • {ip}")
        if len(all_ips) > 20:
            print(f"   ... and {len(all_ips) - 20} more")
    
    print("\n" + "=" * 60)
    print("✅ Done!")

if __name__ == "__main__":
    main()
