#!/usr/bin/env python3
"""
Daily ArXiv Paper Monitor - GitHub Actions Version
直接推送飞书消息，不需要 Hermes agent
带重试机制和限流处理
"""

import os
import sys
import json
import time
import random
import requests
from datetime import date, datetime
from pathlib import Path

# ==================== 配置 ====================
ARXIV_API_URL = "https://export.arxiv.org/api/query"
REQUEST_INTERVAL = 6  # arXiv API 请求间隔（秒）- 增加到 6 秒降低触发限流概率
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 10  # 初始重试延迟（秒）

PAPERS_DIR = Path("papers")
EXCEL_FILE = Path("papers_record.xlsx")
OUTPUT_JSON = Path("new_papers.json")

# 飞书配置
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "")


def load_search_keywords():
    """读取搜索关键词"""
    keywords_file = Path("search_keywords.txt")
    if not keywords_file.exists():
        # 默认关键词：海洋学 + AI
        return "(all:ocean+OR+all:oceanography)+AND+(all:deep+OR+all:neural+OR+all:transformer+OR+all:learning+OR+all:LSTM)"
    return keywords_file.read_text().strip()


def search_arxiv_papers_with_retry(keywords: str, max_results: int = 20):
    """搜索 arXiv 论文，带重试机制"""
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            print(f"[INFO] Searching arXiv (attempt {attempt + 1}/{MAX_RETRIES + 1}): {keywords}")
            
            params = {
                "search_query": keywords,
                "max_results": max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending"
            }
            
            # 添加随机延迟避免多实例同时请求
            if attempt > 0:
                jitter = random.uniform(0.5, 2.0)
                delay = RETRY_DELAY * (2 ** (attempt - 1)) + jitter
                print(f"[INFO] Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
            elif attempt == 0 and REQUEST_INTERVAL > 0:
                time.sleep(REQUEST_INTERVAL)
            
            response = requests.get(
                ARXIV_API_URL, 
                params=params, 
                timeout=60,
                headers={"User-Agent": "Hermes-Arxiv-Monitor/1.0"}
            )
            
            # 检查是否被限流
            if response.status_code == 429:
                print(f"[WARNING] arXiv API rate limited (429). Retry {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES:
                    continue  # 重试
                else:
                    raise Exception("arXiv API rate limit exceeded after all retries")
            
            # 其他 HTTP 错误
            response.raise_for_status()
            
            # 解析 Atom XML 响应
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
            
            papers = []
            for entry in root.findall("atom:entry", ns):
                title_elem = entry.find("atom:title", ns)
                title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else "No title"
                
                id_elem = entry.find("atom:id", ns)
                arxiv_id = id_elem.text.split("/")[-1] if id_elem is not None else "unknown"
                
                summary_elem = entry.find("atom:summary", ns)
                abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else "No abstract"
                
                published_elem = entry.find("atom:published", ns)
                published = published_elem.text if published_elem is not None else ""
                
                # 获取作者
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)
                
                papers.append({
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "abstract": abstract,
                    "published": published,
                    "authors": authors,
                })
            
            print(f"[INFO] Successfully retrieved {len(papers)} papers")
            return papers
            
        except requests.exceptions.Timeout:
            print(f"[WARNING] Request timeout (attempt {attempt + 1}/{MAX_RETRIES + 1})")
            if attempt >= MAX_RETRIES:
                raise Exception("arXiv API timeout after all retries")
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Request failed: {e} (attempt {attempt + 1}/{MAX_RETRIES + 1})")
            if attempt >= MAX_RETRIES:
                raise
    
    raise Exception("Failed to search arXiv after all retries")


def get_feishu_access_token_with_retry():
    """获取飞书访问令牌，带重试机制"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if result.get("code") == 0:
                return result["tenant_access_token"]
            
            # 429 限流
            if response.status_code == 429 or result.get("code") == 13004:
                print(f"[WARNING] Feishu rate limited, retrying ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY * (2 ** attempt))
                continue
            
            # 其他错误不重试
            raise Exception(f"Failed to get Feishu token: {result}")
            
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Feishu token request failed: {e} (attempt {attempt + 1}/{MAX_RETRIES + 1})")
            if attempt >= MAX_RETRIES:
                raise
    
    raise Exception("Failed to get Feishu token after all retries")


def send_feishu_message(message: str):
    """发送飞书消息"""
    if not FEISHU_CHAT_ID:
        print("[WARNING] FEISHU_CHAT_ID not set, skipping message send")
        return
    
    token = get_feishu_access_token_with_retry()
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "receive_id": FEISHU_CHAT_ID,
        "msg_type": "text",
        "content": json.dumps({"text": message})
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    result = response.json()
    
    if result.get("code") != 0:
        print(f"[ERROR] Failed to send Feishu message: {result}")
    else:
        print(f"[INFO] Message sent to Feishu chat {FEISHU_CHAT_ID}")
    
    return result


def main():
    print("=" * 60)
    print(f"[START] ArXiv Daily Monitor (GitHub Actions) - With Retry Logic")
    print(f"[INFO] Date: {date.today().isoformat()}")
    print(f"[INFO] Config: Max retries={MAX_RETRIES}, Initial delay=10s, Request interval={REQUEST_INTERVAL}s")
    print("=" * 60)
    
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载已爬取 ID
    crawled_ids_file = Path("crawled_ids.txt")
    crawled_ids = set()
    if crawled_ids_file.exists():
        crawled_ids = set(line.strip() for line in crawled_ids_file.read_text().splitlines() if line.strip())
    print(f"[INFO] Loaded {len(crawled_ids)} crawled IDs")
    
    # 搜索
    keywords = load_search_keywords()
    try:
        all_papers = search_arxiv_papers_with_retry(keywords, max_results=20)
    except Exception as e:
        error_msg = f"❌ arXiv API 错误：{str(e)}\n\n可能是临时限流，请稍后重试。GitHub Actions 会在明天 9:00 自动再次运行。"
        send_feishu_message(error_msg)
        sys.exit(1)
    
    print(f"[INFO] Retrieved {len(all_papers)} papers from arXiv")
    
    # 查重
    new_papers = [p for p in all_papers if p["arxiv_id"] not in crawled_ids]
    print(f"[INFO] {len(new_papers)} NEW papers")
    
    if not new_papers:
        # 无新论文
        message = f"✅ 今日（{date.today().isoformat()}）未发现新的物理海洋学+AI 相关论文。\n\n搜索关键词：海洋学 (ocean/oceanography) + AI (deep learning, neural network, transformer, LSTM)"
        send_feishu_message(message)
        print("[INFO] No new papers. Notification sent.")
        return
    
    # 构建推送消息
    paper_links = []
    for i, paper in enumerate(new_papers[:10], 1):  # 最多推送 10 篇
        title = paper["title"][:80] + "..." if len(paper["title"]) > 80 else paper["title"]
        authors = ", ".join(paper["authors"][:3])  # 最多 3 个作者
        if len(paper["authors"]) > 3:
            authors += " et al."
        pdf_url = f"https://arxiv.org/abs/{paper['arxiv_id']}"
        paper_links.append(f"{i}. [{title}]({pdf_url})\n   作者：{authors}")
    
    message = f"🔬 **物理海洋学+AI 新论文推送**\n\n"
    message += f"📅 日期：{date.today().isoformat()}\n"
    message += f"📊 发现 {len(new_papers)} 篇新论文\n\n"
    message += "**最新论文列表：**\n" + "\n\n".join(paper_links)
    
    if len(new_papers) > 10:
        message += f"\n\n... 还有 {len(new_papers) - 10} 篇论文，请查看 GitHub Pages 获取完整列表。"
    
    message += f"\n\n📌 搜索关键词：海洋学 (ocean/oceanography) + AI (deep learning, neural network, transformer, LSTM)"
    
    # 发送飞书消息
    send_feishu_message(message)
    
    # 更新 crawled_ids
    new_ids = {p["arxiv_id"] for p in new_papers}
    crawled_ids.update(new_ids)
    crawled_ids_file.write_text("\n".join(sorted(crawled_ids)))
    print(f"[INFO] Updated crawled_ids.txt with {len(new_ids)} new IDs")
    
    print("=" * 60)
    print("[DONE] Daily monitor completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
