# 🔍 V2Ray Config Finder - Cherry Servers

Automated GitHub Actions workflow to find V2Ray/VLESS/VMess configs from Cherry Servers (Lithuania).

## 📊 Target Information

- **Provider:** Cherry Servers (UAB)
- **Country:** Lithuania 🇱🇹
- **IP Range:** 5.199.160.0 - 5.199.175.255
- **ASN:** AS16125

## 📁 Results

Latest configs are always available in:
- [`configs/latest_configs.txt`](configs/latest_configs.txt) - V2Ray configs
- [`configs/latest_ips.txt`](configs/latest_ips.txt) - IP addresses
- [`configs/latest_summary.json`](configs/latest_summary.json) - Full summary

## 🚀 Usage

### Automatic (Recommended)
The workflow runs automatically every 6 hours and commits results.

### Manual Run
1. Go to **Actions** tab
2. Click **Find V2Ray Configs**
3. Click **Run workflow**
4. Wait ~5-10 minutes
5. Check `configs/` folder for results

## 📥 Download Latest Results

```bash
# Download latest configs
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/v2ray-config-finder/main/configs/latest_configs.txt

# Download latest IPs
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/v2ray-config-finder/main/configs/latest_ips.txt
