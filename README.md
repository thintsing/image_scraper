# 优化版论坛图片抓取工具

## 功能说明
这是一个专门针对论坛网站的图片抓取工具，支持IPv6代理、完整反爬策略、并发下载等功能。已验证可在论坛网站上稳定工作。

## 安装依赖
```bash
pip install requests beautifulsoup4 pillow
```

## 使用方法

### 基本用法
```bash
python forum_image_scraper.py --url "目标URL" --proxy "代理地址"
```

### 带参数的用法
```bash
python forum_image_scraper.py --url "目标URL" --proxy "代理地址" --output-dir "./my_images" --workers 6 --max-images 50
```

### 代理使用示例

### 使用IPv6代理
```bash
python forum_image_scraper.py --url "https://目标网站.com/帖子.html" --proxy "http://[2400:3200::1]:7010"
```

### 使用HTTP代理
```bash
python forum_image_scraper.py --url "目标URL" --proxy "http://127.0.0.1:8080"
python forum_image_scraper.py --url "目标URL" --proxy "http://username:password@proxy.example.com:8080"
```

### 使用SOCKS5代理
```bash
python forum_image_scraper.py --url "目标URL" --proxy "socks5://127.0.0.1:1080"
python forum_image_scraper.py --url "目标URL" --proxy "socks5://user:pass@127.0.0.1:1080"
```

### 参数优化建议
```bash
# 保守设置（避免被封）
python forum_image_scraper.py --url "目标URL" --proxy "代理地址" --workers 3 --max-images 30

# 平衡设置（推荐）
python forum_image_scraper.py --url "目标URL" --proxy "代理地址" --workers 6 --max-images 50

# 快速设置（可能被封）
python forum_image_scraper.py --url "目标URL" --proxy "代理地址" --workers 10 --max-images 100
```

### 带参数的用法
```bash
python image_scraper.py --url "https://example.com/gallery.html" --output-dir "./my_images" --min-width 500 --min-height 500 --workers 8 --delay 1.0
```

### 参数说明
- `--url`: 目标网页URL（必需）
- `--output-dir`: 保存图片的目录（默认：`./images`）
- `--min-width`: 最小宽度（像素）（默认：300）
- `--min-height`: 最小高度（像素）（默认：300）
- `--workers`: 并发下载线程数（默认：4）
- `--delay`: 请求之间的延迟秒数（默认：0.5）
- `--max-images`: 最大下载图片数量（默认：50）
- `--proxy`: 代理服务器地址（格式：`http://host:port` 或 `socks5://host:port`）
- `--proxy-file`: 代理服务器列表文件路径（每行一个代理地址）
- `--proxy-type`: 代理类型（可选：`http`、`socks5`、`socks4`，默认：`http`）
- `--rotate-proxy`: 轮换使用多个代理（需要配合 `--proxy-file` 使用）

## 快速测试
```bash
python test_scraper.py
```

## 代理使用示例

### 使用HTTP代理
```bash
python image_scraper.py --url "https://example.com/gallery.html" --proxy "http://127.0.0.1:8080"
python image_scraper.py --url "https://example.com/gallery.html" --proxy "http://username:password@proxy.example.com:8080"
```

### 使用SOCKS5代理
```bash
python image_scraper.py --url "https://example.com/gallery.html" --proxy "socks5://127.0.0.1:1080"
python image_scraper.py --url "https://example.com/gallery.html" --proxy "socks5://user:pass@127.0.0.1:1080"
```

### 从文件读取代理列表
```bash
# 创建代理文件 proxies.txt
# 每行一个代理地址，例如:
# 127.0.0.1:8080
# user:pass@proxy.example.com:8080
# socks5://127.0.0.1:1080

python image_scraper.py --url "https://example.com/gallery.html" --proxy-file proxies.txt
python image_scraper.py --url "https://example.com/gallery.html" --proxy-file proxies.txt --rotate-proxy
```

### 自动补全代理协议
```bash
# 自动添加 http:// 前缀
python image_scraper.py --url "https://example.com/gallery.html" --proxy "127.0.0.1:8080" --proxy-type http

# 自动添加 socks5:// 前缀  
python image_scraper.py --url "https://example.com/gallery.html" --proxy "127.0.0.1:1080" --proxy-type socks5
```

### 代理功能测试
```bash
python proxy_test.py
```

### 主爬虫使用
```bash
# 使用主爬虫（推荐）
python forum_image_scraper.py --url "目标URL" --proxy "代理地址"

# 使用增强版爬虫
python optimized_forum_scraper.py --url "目标URL" --proxy "代理地址"
```

## 注意事项
1. 请尊重网站的 robots.txt 和使用条款
2. 适当设置延迟参数，避免对目标网站造成过大压力
3. 图片将自动过滤掉尺寸太小的图片
4. 支持 jpg、jpeg、png、gif、webp、bmp 格式

## 代码结构
### 核心爬虫文件
- `forum_image_scraper.py` - 主爬虫程序（推荐使用）
  - 专门针对论坛网站优化
  - 支持IPv6/HTTP/SOCKS5代理
  - 完整反爬策略
  - 已验证可用
  
- `optimized_forum_scraper.py` - 增强版爬虫
  - 更高级的反爬功能
  - 随机User-Agent生成
  - 更完善的错误处理

### 配置文件
- `requirements.txt` - 依赖列表
- `proxies_example.txt` - 代理配置示例

### 文档文件
- `README.md` - 使用说明（本文档）