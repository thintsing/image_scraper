#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版论坛图片爬虫
针对成人论坛网站优化，包含完整的反爬策略
"""

import os
import re
import time
import random
import hashlib
import argparse
from io import BytesIO
from urllib.parse import urljoin, urlparse, unquote

# 完全禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    from PIL import Image
    from fake_useragent import UserAgent  # 用于生成随机User-Agent
except ImportError as e:
    print(f"缺少依赖库: {e}")
    print("请运行: pip install fake-useragent pillow")
    exit(1)


class OptimizedForumScraper:
    def __init__(self, output_dir='./forum_images', min_width=600, min_height=600,
                 max_workers=6, delay_range=(1, 3), proxy=None, use_cookies=False):
        """
        初始化爬虫
        
        Args:
            output_dir: 输出目录
            min_width: 最小宽度
            min_height: 最小高度
            max_workers: 最大工作线程数
            delay_range: 延迟范围（秒）
            proxy: 代理服务器
            use_cookies: 是否使用cookies
        """
        self.output_dir = output_dir
        self.min_width = min_width
        self.min_height = min_height
        self.max_workers = max_workers
        self.delay_range = delay_range
        self.proxy = proxy
        self.use_cookies = use_cookies
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化User-Agent生成器
        try:
            self.ua = UserAgent()
        except:
            self.ua = None
        
        # 请求会话
        self.session = requests.Session()
        
        # 配置代理
        self.proxies = None
        if proxy:
            # 处理IPv6地址格式 [ipv6]:port
            if '[' in proxy and ']' in proxy:
                # IPv6地址，直接使用
                if proxy.startswith('http://') or proxy.startswith('https://'):
                    self.proxies = {'http': proxy, 'https': proxy}
                else:
                    self.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
            elif proxy.startswith('http://') or proxy.startswith('https://'):
                self.proxies = {'http': proxy, 'https': proxy}
            elif proxy.startswith('socks'):
                self.proxies = {'http': proxy, 'https': proxy}
            else:
                self.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        
        # 配置Cookies（如果需要）
        if use_cookies:
            # 这里可以加载预配置的cookies
            self.load_cookies()
    
    def load_cookies(self):
        """加载cookies"""
        # 可以从文件加载或手动设置
        # 示例：self.session.cookies.update({'key': 'value'})
        pass
    
    def get_random_headers(self, referer=None):
        """生成随机请求头"""
        if self.ua:
            user_agent = self.ua.random
        else:
            # 备用User-Agent列表
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT ' + str(random.randint(6, 11)) + '; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/' + str(random.randint(90, 120)) + '.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            user_agent = random.choice(user_agents)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        if referer:
            headers['Referer'] = referer
        
        return headers
    
    def random_delay(self):
        """随机延迟"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def extract_forum_images(self, html: str, base_url: str):
        """
        提取论坛图片链接
        针对Discuz!等论坛系统优化
        """
        print("正在分析页面结构...")
        
        all_urls = []
        
        # 1. 查找帖子内容区域
        # Discuz!常见的内容容器
        content_patterns = [
            r'<div[^>]*class="[^"]*tpc_content[^"]*"[^>]*>(.*?)</div>',
            r'<td[^>]*class="[^"]*t_f[^"]*"[^>]*>(.*?)</td>',
            r'<div[^>]*id="postmessage_[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*postmessage[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*pcb[^"]*"[^>]*>(.*?)</div>',
        ]
        
        # 2. 常见图床域名模式
        hosting_domains = [
            '66img.cc', 'qpic.ws', 'imgbox.com', 'imgur.com', 'postimg.cc',
            'tinypic.com', 'imgbb.com', 'freeimage.host', 'imagebam.com',
            'pixhost.org', 'imgsrc.ru', 'img.yt', 'imagevenue.com',
            'pimpandhost.com', 'imgchili.net', 'imgtaxi.com', 'imgserve.net',
            'imgspice.com', 'imgmoon.com', 'imgflare.com', 'imgdino.com'
        ]
        
        # 3. 提取所有可能的图片链接
        # 方法1: 正则匹配所有图片URL
        img_pattern = r'https?://[^\s"\']+\.(?:jpg|jpeg|png|gif|webp|bmp)[^\s"\']*'
        direct_urls = re.findall(img_pattern, html, re.IGNORECASE)
        all_urls.extend(direct_urls)
        
        # 方法2: 查找img标签的各种属性
        img_tag_patterns = [
            r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>',
            r'<img[^>]+data-src=["\']([^"\']+)["\'][^>]*>',
            r'<img[^>]+ess-data=["\']([^"\']+)["\'][^>]*>',
            r'<img[^>]+data-original=["\']([^"\']+)["\'][^>]*>',
            r'<img[^>]+file=["\']([^"\']+)["\'][^>]*>',
            r'<img[^>]+srcs=["\']([^"\']+)["\'][^>]*>',
        ]
        
        for pattern in img_tag_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match.startswith('http'):
                    all_urls.append(match)
                else:
                    full_url = urljoin(base_url, match)
                    all_urls.append(full_url)
        
        # 方法3: 在内容区域内查找
        for pattern in content_patterns:
            content_matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for content in content_matches:
                # 在内容中查找图片链接
                content_urls = re.findall(img_pattern, content, re.IGNORECASE)
                all_urls.extend(content_urls)
                
                # 查找img标签
                for img_pattern_tag in img_tag_patterns:
                    tag_matches = re.findall(img_pattern_tag, content, re.IGNORECASE)
                    for match in tag_matches:
                        if match.startswith('http'):
                            all_urls.append(match)
                        else:
                            full_url = urljoin(base_url, match)
                            all_urls.append(full_url)
        
        # 4. 过滤和清理
        filtered_urls = []
        seen_urls = set()
        
        for url in all_urls:
            # 清理URL
            clean_url = url.split('?')[0].strip('\'"')
            
            # 跳过base64
            if clean_url.startswith('data:'):
                continue
            
            # 跳过缩略图和小图标
            skip_keywords = ['thumb', 'avatar', 'icon', 'logo', 'smiley', 'attach']
            if any(keyword in clean_url.lower() for keyword in skip_keywords):
                continue
            
            # 确保是有效URL
            if clean_url.startswith('http') and clean_url not in seen_urls:
                seen_urls.add(clean_url)
                filtered_urls.append(clean_url)
        
        # 5. 按域名分组统计
        domain_count = {}
        for url in filtered_urls:
            try:
                domain = urlparse(url).netloc
                domain_count[domain] = domain_count.get(domain, 0) + 1
            except:
                pass
        
        print(f"找到 {len(filtered_urls)} 个图片链接")
        
        if domain_count:
            print("链接域名分布:")
            for domain, count in sorted(domain_count.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {domain}: {count} 个链接")
        
        return filtered_urls
    
    def download_image_with_retry(self, url: str, referer: str, max_retries=3):
        """带重试机制的图片下载"""
        for attempt in range(max_retries):
            try:
                # 随机延迟
                self.random_delay()
                
                print(f"下载 ({attempt+1}/{max_retries}): {url[:80]}...")
                
                # 生成请求头
                headers = self.get_random_headers(referer)
                
                # 添加图片特定的请求头
                headers.update({
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Sec-Fetch-Dest': 'image',
                    'Sec-Fetch-Mode': 'no-cors',
                    'Sec-Fetch-Site': 'cross-site',
                })
                
                # 发送请求
                response = self.session.get(
                    url, 
                    headers=headers,
                    timeout=15,
                    stream=True,
                    proxies=self.proxies,
                    verify=False  # 禁用SSL验证
                )
                
                if response.status_code != 200:
                    print(f"  失败: 状态码 {response.status_code}")
                    if response.status_code in [403, 429]:
                        # 被禁止或限速，等待更长时间
                        time.sleep(random.uniform(5, 10))
                    continue
                
                # 检查内容类型
                content_type = response.headers.get('Content-Type', '')
                if not any(img_type in content_type.lower() for img_type in 
                          ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']):
                    print(f"  失败: 非图片内容")
                    continue
                
                # 读取数据
                img_data = response.content
                
                if len(img_data) < 4096:  # 小于4KB的可能不是有效图片
                    print(f"  失败: 文件太小 ({len(img_data)} bytes)")
                    continue
                
                # 验证图片尺寸
                try:
                    img = Image.open(BytesIO(img_data))
                    width, height = img.size
                    
                    if width < self.min_width or height < self.min_height:
                        print(f"  失败: 图片尺寸太小 ({width}x{height})")
                        continue
                    
                    # 获取图片格式
                    img_format = img.format.lower() if img.format else 'jpg'
                    
                except Exception as e:
                    print(f"  失败: 无法读取图片尺寸 ({e})")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return None
                
                # 生成安全文件名
                parsed_url = urlparse(url)
                original_filename = os.path.basename(parsed_url.path)
                
                if not original_filename or '.' not in original_filename:
                    filename_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
                    filename = f"{filename_hash}.{img_format}"
                else:
                    # 清理文件名
                    safe_chars = r'[a-zA-Z0-9_\-\.]'
                    safe_name = ''.join(re.findall(safe_chars, original_filename))
                    if not safe_name:
                        filename_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
                        filename = f"{filename_hash}.{img_format}"
                    else:
                        # 确保有正确的扩展名
                        name_parts = safe_name.rsplit('.', 1)
                        if len(name_parts) < 2 or name_parts[1] not in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                            filename = f"{safe_name}.{img_format}"
                        else:
                            filename = safe_name
                
                # 保存文件
                filepath = os.path.join(self.output_dir, filename)
                
                # 避免重名
                counter = 1
                while os.path.exists(filepath):
                    name, ext = os.path.splitext(filename)
                    filepath = os.path.join(self.output_dir, f"{name}_{counter}{ext}")
                    counter += 1
                
                with open(filepath, 'wb') as f:
                    f.write(img_data)
                
                file_size_kb = len(img_data) // 1024
                print(f"  成功: {filename} ({width}x{height}, {file_size_kb}KB)")
                return filepath
                
            except requests.exceptions.RequestException as e:
                print(f"  网络错误: {type(e).__name__}")
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)  # 指数退避
                    time.sleep(wait_time)
                    continue
            except Exception as e:
                print(f"  未知错误: {type(e).__name__}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
        
        return None
    
    def scrape(self, url: str):
        """主抓取函数"""
        print(f"开始抓取: {url}")
        
        if self.proxy:
            print(f"使用代理: {self.proxy}")
        
        if self.use_cookies:
            print("使用Cookies进行访问")
        
        try:
            # 1. 获取页面
            print("正在获取页面内容...")
            headers = self.get_random_headers()
            
            self.random_delay()  # 初始延迟
            
            response = self.session.get(
                url, 
                headers=headers,
                timeout=30,
                proxies=self.proxies,
                verify=False
            )
            
            if response.status_code != 200:
                print(f"无法访问页面: 状态码 {response.status_code}")
                print(f"响应头: {dict(response.headers)}")
                return []
            
            response.encoding = 'utf-8'
            html_content = response.text
            
            # 保存HTML用于调试
            debug_file = os.path.join(self.output_dir, 'page_debug.html')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"页面已保存到: {debug_file}")
            
            # 2. 提取图片链接
            image_urls = self.extract_forum_images(html_content, url)
            
            if not image_urls:
                print("未找到图片链接")
                return []
            
            # 3. 并发下载
            downloaded_files = []
            print(f"\n开始下载 {len(image_urls)} 张图片...")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_url = {
                    executor.submit(self.download_image_with_retry, img_url, url): img_url 
                    for img_url in image_urls[:50]  # 限制最多50张
                }
                
                completed = 0
                for future in as_completed(future_to_url):
                    completed += 1
                    img_url = future_to_url[future]
                    try:
                        result = future.result(timeout=60)
                        if result:
                            downloaded_files.append(result)
                    except Exception as e:
                        print(f"下载出错 {img_url}: {e}")
                    
                    # 进度显示
                    if completed % 5 == 0:
                        print(f"进度: {completed}/{len(future_to_url)}")
            
            # 4. 生成报告
            report_file = os.path.join(self.output_dir, 'download_report.txt')
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"抓取报告 - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"目标URL: {url}\n")
                f.write(f"找到链接: {len(image_urls)}\n")
                f.write(f"成功下载: {len(downloaded_files)}\n")
                f.write(f"成功率: {len(downloaded_files)/len(image_urls)*100:.1f}%\n\n")
                f.write("下载的文件:\n")
                for i, filepath in enumerate(downloaded_files, 1):
                    f.write(f"{i}. {os.path.basename(filepath)}\n")
            
            print(f"\n抓取完成!")
            print(f"成功下载 {len(downloaded_files)}/{len(image_urls)} 张图片")
            print(f"成功率: {len(downloaded_files)/len(image_urls)*100:.1f}%")
            print(f"报告已保存到: {report_file}")
            
            return downloaded_files
            
        except Exception as e:
            print(f"抓取失败: {e}")
            import traceback
            traceback.print_exc()
            return []


def main():
    parser = argparse.ArgumentParser(description='优化论坛图片抓取工具')
    parser.add_argument('--url', required=True, help='目标网页URL')
    parser.add_argument('--output-dir', default='./forum_images', help='输出目录')
    parser.add_argument('--min-width', type=int, default=600, help='最小宽度')
    parser.add_argument('--min-height', type=int, default=600, help='最小高度')
    parser.add_argument('--workers', type=int, default=6, help='并发线程数')
    parser.add_argument('--delay-min', type=float, default=1.0, help='最小延迟(秒)')
    parser.add_argument('--delay-max', type=float, default=3.0, help='最大延迟(秒)')
    parser.add_argument('--max-images', type=int, default=50, help='最大下载数量')
    parser.add_argument('--proxy', help='代理服务器地址')
    parser.add_argument('--use-cookies', action='store_true', help='使用Cookies')
    parser.add_argument('--retries', type=int, default=3, help='重试次数')
    
    args = parser.parse_args()
    
    # 创建抓取器
    scraper = OptimizedForumScraper(
        output_dir=args.output_dir,
        min_width=args.min_width,
        min_height=args.min_height,
        max_workers=args.workers,
        delay_range=(args.delay_min, args.delay_max),
        proxy=args.proxy,
        use_cookies=args.use_cookies
    )
    
    # 开始抓取
    scraper.scrape(args.url)


if __name__ == '__main__':
    main()