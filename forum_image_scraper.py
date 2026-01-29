#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版IPv6代理爬虫
修复了过滤逻辑和SSL警告
"""

import os
import re
import time
import random
import hashlib
import argparse
from urllib.parse import urljoin, urlparse, unquote

# 完全禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


class FixedIPv6Scraper:
    def __init__(self, output_dir='./images', proxy=None, max_workers=4):
        self.output_dir = output_dir
        self.proxy = proxy
        self.max_workers = max_workers
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 配置代理
        self.proxies = None
        if proxy:
            # 处理各种代理格式
            if '[' in proxy and ']' in proxy:
                # IPv6地址格式: [240e:74c:110:a01::2000]:7010
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
        
        # 请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.t66y.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def extract_images(self, html: str, base_url: str):
        """提取图片链接"""
        print("提取图片链接...")
        
        all_urls = []
        
        # 方法1: 正则匹配所有图片URL
        img_pattern = r'https?://[^\s"\']+\.(?:jpg|jpeg|png|gif|webp|bmp)[^\s"\']*'
        all_urls.extend(re.findall(img_pattern, html, re.IGNORECASE))
        
        # 方法2: 查找img标签的各种属性
        img_attrs = ['src', 'data-src', 'ess-data', 'data-original', 'file']
        for attr in img_attrs:
            pattern = f'{attr}=["\']([^"\']+)["\']'
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match.startswith('http'):
                    all_urls.append(match)
                else:
                    full_url = urljoin(base_url, match)
                    all_urls.append(full_url)
        
        # 过滤和去重
        filtered_urls = []
        seen_urls = set()
        
        for url in all_urls:
            # 清理URL
            clean_url = url.split('?')[0].strip('\'"')
            
            # 跳过base64和无效URL
            if clean_url.startswith('data:') or not clean_url.startswith('http'):
                continue
            
            # 过滤广告、缩略图和无效链接
            skip_words = ['adblock', 'adblo_ck', 'thumb', 'avatar', 'icon']
            if any(word in clean_url.lower() for word in skip_words):
                continue
            
            # 特殊过滤：23img.com的/l/路径是HTML页面
            if '23img.com/l/' in clean_url:
                continue
            
            if clean_url not in seen_urls:
                seen_urls.add(clean_url)
                filtered_urls.append(clean_url)
        
        print(f"找到 {len(filtered_urls)} 个图片链接")
        
        # 按域名统计
        domains = {}
        for url in filtered_urls:
            try:
                domain = urlparse(url).netloc
                domains[domain] = domains.get(domain, 0) + 1
            except:
                pass
        
        if domains:
            print("域名分布:")
            for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {domain}: {count}")
        
        return filtered_urls
    
    def download_image(self, url: str, referer: str):
        """下载单个图片"""
        try:
            # 简单延迟
            time.sleep(random.uniform(0.5, 1.5))
            
            # 截断长URL显示
            display_url = url[:60] + "..." if len(url) > 60 else url
            print(f"下载: {display_url}")
            
            # 请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': referer,
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            }
            
            # 下载
            response = self.session.get(
                url, 
                headers=headers,
                timeout=10,
                stream=True,
                proxies=self.proxies,
                verify=False  # 重要：禁用SSL验证
            )
            
            if response.status_code != 200:
                print(f"  失败: HTTP {response.status_code}")
                return None
            
            # 检查内容类型
            content_type = response.headers.get('Content-Type', '')
            if not any(img_type in content_type.lower() for img_type in 
                      ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']):
                print(f"  失败: 不是图片 ({content_type})")
                return None
            
            # 读取数据
            img_data = response.content
            
            if len(img_data) < 1024:  # 太小可能不是图片
                print(f"  失败: 文件太小 ({len(img_data)} bytes)")
                return None
            
            # 生成文件名
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename or '.' not in filename:
                # 生成哈希文件名
                filename_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
                # 尝试猜测扩展名
                if 'gif' in content_type.lower():
                    filename = f"{filename_hash}.gif"
                elif 'png' in content_type.lower():
                    filename = f"{filename_hash}.png"
                elif 'jpeg' in content_type.lower() or 'jpg' in content_type.lower():
                    filename = f"{filename_hash}.jpg"
                else:
                    filename = f"{filename_hash}.jpg"
            else:
                # 清理文件名
                filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
                if not filename:
                    filename_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
                    filename = f"{filename_hash}.jpg"
            
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
            if file_size_kb > 1024:
                size_display = f"{file_size_kb/1024:.1f}MB"
            else:
                size_display = f"{file_size_kb}KB"
            
            print(f"  成功: {filename} ({size_display})")
            return filepath
            
        except Exception as e:
            print(f"  错误: {type(e).__name__}")
            return None
    
    def scrape(self, url: str, max_images=50):
        """主抓取函数"""
        print(f"目标: {url}")
        
        if self.proxy:
            print(f"代理: {self.proxy}")
        
        try:
            # 1. 获取页面
            print("获取页面...")
            response = self.session.get(
                url,
                timeout=20,
                proxies=self.proxies,
                verify=False
            )
            
            if response.status_code != 200:
                print(f"页面访问失败: HTTP {response.status_code}")
                return []
            
            response.encoding = 'utf-8'
            html_content = response.text
            
            # 保存HTML调试
            debug_file = os.path.join(self.output_dir, 'debug.html')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"页面已保存: {debug_file}")
            
            # 2. 提取图片链接
            image_urls = self.extract_images(html_content, url)
            
            if not image_urls:
                print("没有找到图片链接")
                return []
            
            # 3. 下载图片
            downloaded_files = []
            download_count = min(len(image_urls), max_images)
            print(f"\n开始下载 {download_count} 张图片...")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_url = {
                    executor.submit(self.download_image, img_url, url): img_url 
                    for img_url in image_urls[:download_count]
                }
                
                completed = 0
                for future in as_completed(future_to_url):
                    completed += 1
                    img_url = future_to_url[future]
                    try:
                        result = future.result(timeout=30)
                        if result:
                            downloaded_files.append(result)
                    except Exception as e:
                        print(f"下载失败: {e}")
                    
                    # 进度显示
                    if completed % 5 == 0:
                        print(f"进度: {completed}/{len(future_to_url)}")
            
            # 4. 生成报告
            print(f"\n下载完成!")
            print(f"成功: {len(downloaded_files)}/{download_count}")
            
            report_file = os.path.join(self.output_dir, 'report.txt')
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"报告时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"目标URL: {url}\n")
                f.write(f"代理: {self.proxy}\n")
                f.write(f"找到链接: {len(image_urls)}\n")
                f.write(f"尝试下载: {download_count}\n")
                f.write(f"成功下载: {len(downloaded_files)}\n")
                f.write(f"成功率: {len(downloaded_files)/download_count*100:.1f}%\n")
            
            print(f"报告已保存: {report_file}")
            
            return downloaded_files
            
        except Exception as e:
            print(f"抓取失败: {e}")
            import traceback
            traceback.print_exc()
            return []


def main():
    parser = argparse.ArgumentParser(description='修复IPv6代理爬虫')
    parser.add_argument('--url', required=True, help='目标网页URL')
    parser.add_argument('--output-dir', default='./images', help='输出目录')
    parser.add_argument('--proxy', required=True, help='代理服务器地址')
    parser.add_argument('--workers', type=int, default=4, help='并发线程数')
    parser.add_argument('--max-images', type=int, default=50, help='最大下载数量')
    
    args = parser.parse_args()
    
    # 创建爬虫
    scraper = FixedIPv6Scraper(
        output_dir=args.output_dir,
        proxy=args.proxy,
        max_workers=args.workers
    )
    
    # 开始抓取
    scraper.scrape(args.url, args.max_images)


if __name__ == '__main__':
    main()