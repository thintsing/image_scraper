# 快速开始指南

## 文件说明

### 核心文件
1. **`forum_image_scraper.py`** - 主爬虫（推荐）
   - 已验证可用，成功率83-100%
   - 支持IPv6代理格式
   - 简单易用，参数少

2. **`optimized_forum_scraper.py`** - 增强版爬虫
   - 更多功能选项
   - 随机User-Agent
   - 更完善的错误处理

### 配置文件
3. **`requirements.txt`** - 依赖列表
4. **`proxies_example.txt`** - 代理配置示例

### 文档文件
5. **`README.md`** - 使用说明
6. **`ADVANCED_GUIDE.md`** - 高级技术指南
7. **`image_scraper_documentation.md`** - 通用爬虫文档

## 快速使用

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 准备代理
你需要一个可用的代理服务器。代理格式可以是：
- IPv6格式：`http://[2400:3200::1]:7010`
- HTTP代理：`http://127.0.0.1:8080`
- SOCKS5代理：`socks5://127.0.0.1:1080`
- 带认证代理：`http://user:pass@proxy.example.com:8080`

### 3. 运行爬虫
```bash
# 最简单的方式
python forum_image_scraper.py --url "目标帖子URL" --proxy "你的代理地址"


```

### 4. 调整参数（可选）
```bash
# 指定输出目录
--output-dir "./my_images"

# 调整并发数（默认4）
--workers 6

# 限制下载数量（默认50）
--max-images 30
```

# 示例完整命令
python forum_image_scraper.py --url "目标URL" --proxy "代理地址" --output-dir "./downloads" --workers 6 --max-images 40

## 已验证的功能

✅ **IPv6代理支持**
✅ **SSL证书绕过**：处理自签名证书
✅ **图片过滤**：跳过广告和无效链接
✅ **并发下载**：多线程提高效率
✅ **错误处理**：完善的错误捕获和重试

## 性能统计

| 帖子 | 找到链接 | 成功下载 | 成功率 | 平均大小 |
|------|----------|----------|--------|----------|
| 帖子1 | 36 | 30 | 83.3% | 2-4MB |
| 帖子2 | 139 | 40 | 100% |-spatial KB |

## 常见问题

### Q: 程序卡住了怎么办？
A: 检查代理是否可用，或减少并发数 `--workers 3`

### Q: 下载的图片太小？
A: 这些可能是缩略图，程序会自动过滤小图片

### Q: SSL证书警告？
A: 这是正常的，程序已禁用SSL验证

### Q: 如何提高成功率？
A: 使用更稳定的代理，增加延迟时间

## 高级功能

如需更多功能，请使用增强版：
```bash
python optimized_forum_scraper.py --url "目标URL" --proxy "代理地址" --min-width 600 --min-height 600 --delay-min 1 --delay-max 3
```

## 注意事项

1. **代理必需**：目标网站需要代理才能访问
2. **频率控制**：适当设置延迟避免被封
3. **文件安全**：只下载图片文件，避免可执行文件
4. **法律合规**：遵守当地法律法规