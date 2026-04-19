#!/usr/bin/env python3
"""
Multi-Source Paper Monitor (arXiv + Semantic Scholar + Web of Science)
三源合一文献监控 - GitHub Actions 版本
支持：
  - arXiv: 预印本（免费，无需 API key）
  - Semantic Scholar: 全学科期刊（免费，可选 API key）
  - Web of Science: 核心期刊（需机构 API key）
"""

import os
import sys
import json
import time
import random
import hashlib
import requests
from datetime import date, datetime, timedelta
from pathlib import Path

# ==================== 配置 ====================
# arXiv 配置
ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_REQUEST_INTERVAL = 6  # 秒

# Semantic Scholar 配置
SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
SEMANTIC_SCHOLAR_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")  # 可选

# Web of Science 配置
WEB_OF_SCIENCE_URL = "https://api.clarivate.com/apis/wos-starter/v1/documents"
WEB_OF_SCIENCE_API_KEY = os.environ.get("WEB_OF_SCIENCE_API_KEY", "")  # 必需

# 通用配置
REQUEST_INTERVAL = 3  # 不同平台间请求间隔
MAX_RETRIES = 3
RETRY_DELAY = 10

PAPERS_DIR = Path("papers")
CRAWLED_IDS_FILE = Path("crawled_ids.txt")

# 飞书配置
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "")


def load_search_keywords():
    """读取搜索关键词"""
    keywords_file = Path("search_keywords.txt")
    if not keywords_file.exists():
        return "(all:oceanography)+AND+(all:deep+OR+all:neural+OR+all:transformer+OR+all:learning)"
    return keywords_file.read_text().strip()


def generate_paper_id(source: str, identifier: str) -> str:
    """生成唯一论文 ID（用于去重）"""
    return f"{source}:{identifier}"


def search_arxiv_papers(keywords: str, max_results: int = 20):
    """搜索 arXiv 论文（带重试）"""
    print(f"\n[arXiv] Searching: {keywords}")
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt > 0:
                delay = RETRY_DELAY * (2 ** (attempt - 1)) + random.uniform(0.5, 2.0)
                print(f"[arXiv] Retrying in {delay:.1f}s...")
                time.sleep(delay)
            elif attempt == 0:
                time.sleep(REQUEST_INTERVAL)
            
            params = {
                "search_query": keywords,
                "max_results": max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending"
            }
            
            response = requests.get(
                ARXIV_API_URL,
                params=params,
                timeout=60,
                headers={"User-Agent": "Hermes-MultiSource-Monitor/1.0"}
            )
            
            if response.status_code == 429:
                print(f"[arXiv] Rate limited (429), attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES:
                    continue
                raise Exception("arXiv rate limit exceeded")
            
            response.raise_for_status()
            
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
                abstract = summary_elem.text.strip().replace("\n", " ")[:500] if summary_elem is not None else "No abstract"
                
                published_elem = entry.find("atom:published", ns)
                published = published_elem.text[:10] if published_elem is not None else ""
                
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)
                
                papers.append({
                    "id": generate_paper_id("arxiv", arxiv_id),
                    "source": "arXiv",
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "abstract": abstract,
                    "published": published,
                    "authors": authors[:5],  # 最多 5 个作者
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                })
            
            print(f"[arXiv] Found {len(papers)} papers")
            return papers
            
        except Exception as e:
            print(f"[arXiv] Error: {e}")
            if attempt >= MAX_RETRIES:
                return []
    
    return []


def search_semantic_scholar(keywords: str, max_results: int = 20):
    """搜索 Semantic Scholar 论文"""
    print(f"\n[Semantic Scholar] Searching: {keywords}")
    
    headers = {"Content-Type": "application/json"}
    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY
    
    # 转换关键词格式
    # 将 arXiv 格式转为自然语言关键词
    query_text = keywords.replace("(all:", "").replace(")", "").replace("+OR+", " OR ").replace("+AND+", " AND ")
    query_text = query_text.replace("all:", "").strip()
    
    params = {
        "query": query_text,
        "fields": "title,abstract,publicationDate,authors,url,publicationTypes,journal,venue,year,openAccessPdf",
        "year": f"{(datetime.now().year - 1)}-",  # 最近 1-2 年
    }
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt > 0:
                time.sleep(RETRY_DELAY * (2 ** (attempt - 1)))
            elif attempt == 0:
                time.sleep(REQUEST_INTERVAL)
            
            response = requests.get(
                SEMANTIC_SCHOLAR_URL,
                params=params,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 429:
                print(f"[Semantic Scholar] Rate limited (429), attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES:
                    continue
            
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for paper in data.get("data", []):
                paper_id = paper.get("paperId", "unknown")
                title = paper.get("title", "No title")
                abstract = paper.get("abstract", "No abstract")[:500] if paper.get("abstract") else "No abstract"
                pub_date = paper.get("publicationDate", "")[:10] if paper.get("publicationDate") else ""
                
                authors = []
                for author in paper.get("authors", [])[:5]:
                    if author.get("name"):
                        authors.append(author["name"])
                
                # 获取 PDF 链接或详情页链接
                pdf_url = None
                if paper.get("openAccessPdf"):
                    pdf_url = paper["openAccessPdf"].get("url")
                url = pdf_url if pdf_url else paper.get("url", f"https://www.semanticscholar.org/paper/{paper_id}")
                
                papers.append({
                    "id": generate_paper_id("semantic_scholar", paper_id),
                    "source": "Semantic Scholar",
                    "paper_id": paper_id,
                    "title": title,
                    "abstract": abstract,
                    "published": pub_date,
                    "authors": authors,
                    "url": url,
                    "venue": paper.get("venue", paper.get("journal", {}).get("name", "")),
                })
                
                if len(papers) >= max_results:
                    break
            
            print(f"[Semantic Scholar] Found {len(papers)} papers")
            return papers
            
        except Exception as e:
            print(f"[Semantic Scholar] Error: {e}")
            if attempt >= MAX_RETRIES:
                return []
    
    return []


def search_web_of_science(keywords: str, max_results: int = 20):
    """搜索 Web of Science 论文"""
    print(f"\n[Web of Science] Searching: {keywords}")
    
    if not WEB_OF_SCIENCE_API_KEY:
        print("[Web of Science] API key not configured, skipping")
        return []
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": WEB_OF_SCIENCE_API_KEY
    }
    
    # 转换关键词格式为 WoS 查询语法
    query_text = keywords.replace("(all:", "").replace(")", "").replace("+OR+", " OR ").replace("+AND+", " AND ")
    query_text = query_text.replace("all:", "").strip()
    
    params = {
        "q": f'TS=("{query_text}") AND PY=2024-2026',  # 主题搜索，最近 2-3 年
        "databaseId": "WOS",
        "lang": "en",
        "firstRecord": 1,
        "count": max_results,
        "orderBy": "PY.D",  # 按出版年份倒序
    }
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt > 0:
                time.sleep(RETRY_DELAY * (2 ** (attempt - 1)))
            elif attempt == 0:
                time.sleep(REQUEST_INTERVAL)
            
            response = requests.get(
                WEB_OF_SCIENCE_URL,
                params=params,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 401 or response.status_code == 403:
                print(f"[Web of Science] Authentication failed: {response.status_code}")
                return []
            
            if response.status_code == 429:
                print(f"[Web of Science] Rate limited (429), attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES:
                    continue
            
            response.raise_for_status()
            data = response.json()
            
            papers = []
            documents = data.get("Data", [])
            
            for doc in documents:
                doi = doc.get("DOI", "")
                title = doc.get("title", "No title")
                
                # 获取摘要
                abstract = ""
                if "abstracts" in doc and doc["abstracts"]:
                    abstract = doc["abstracts"][0].get("value", "No abstract")[:500]
                
                # 获取作者
                authors = []
                if "authors" in doc:
                    for author in doc["authors"][:5]:
                        if author.get("name"):
                            authors.append(author["name"])
                
                # 出版日期
                pub_date = ""
                if "publishedDate" in doc:
                    pub_date = doc["publishedDate"][:10]
                elif "source" in doc:
                    pub_date = doc["source"].get("publishedDate", "")[:10]
                
                # 链接
                url = f"https://www.webofscience.com/wos/woscc/full-record/{doc.get('ut', '')}" if doc.get('ut') else ""
                
                papers.append({
                    "id": generate_paper_id("wos", doi or doc.get("ut", "")),
                    "source": "Web of Science",
                    "doi": doi,
                    "ut": doc.get("ut", ""),
                    "title": title,
                    "abstract": abstract,
                    "published": pub_date,
                    "authors": authors,
                    "url": url,
                    "journal": doc.get("source", {}).get("title", ""),
                })
                
                if len(papers) >= max_results:
                    break
            
            print(f"[Web of Science] Found {len(papers)} papers")
            return papers
            
        except Exception as e:
            print(f"[Web of Science] Error: {e}")
            if attempt >= MAX_RETRIES:
                return []
    
    return []


def merge_and_deduplicate(all_papers_list: list) -> list:
    """合并多个来源的论文并去重"""
    seen_ids = set()
    merged = []
    
    for papers in all_papers_list:
        for paper in papers:
            if paper["id"] not in seen_ids:
                seen_ids.add(paper["id"])
                merged.append(paper)
    
    # 按出版日期排序（最新的在前）
    merged.sort(key=lambda x: x.get("published", ""), reverse=True)
    
    return merged


def load_crawled_ids() -> set:
    """加载已爬取的论文 ID"""
    if CRAWLED_IDS_FILE.exists():
        return set(line.strip() for line in CRAWLED_IDS_FILE.read_text().splitlines() if line.strip())
    return set()


def save_crawled_ids(crawled_ids: set):
    """保存已爬取的论文 ID"""
    CRAWLED_IDS_FILE.write_text("\n".join(sorted(crawled_ids)))


def get_feishu_access_token() -> str:
    """获取飞书访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    
    response = requests.post(url, json=payload, timeout=30)
    result = response.json()
    
    if result.get("code") != 0:
        raise Exception(f"Failed to get Feishu token: {result}")
    
    return result["tenant_access_token"]


def send_feishu_message(message: str):
    """发送飞书消息"""
    if not FEISHU_CHAT_ID:
        print("[WARNING] FEISHU_CHAT_ID not set, skipping message send")
        return
    
    token = get_feishu_access_token()
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    
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
        print(f"[INFO] Message sent to Feishu")


def build_message(new_papers: list, source_counts: dict) -> str:
    """构建飞书推送消息"""
    today = date.today().isoformat()
    
    message = f"🔬 **物理海洋学+AI 新论文推送**\n\n"
    message += f"📅 日期：{today}\n"
    message += f"📊 发现 {len(new_papers)} 篇新论文\n"
    message += f"   • arXiv: {source_counts.get('arXiv', 0)} 篇\n"
    message += f"   • Semantic Scholar: {source_counts.get('Semantic Scholar', 0)} 篇\n"
    message += f"   • Web of Science: {source_counts.get('Web of Science', 0)} 篇\n\n"
    
    message += "**最新论文列表：**\n\n"
    
    for i, paper in enumerate(new_papers[:10], 1):
        title = paper["title"][:60] + "..." if len(paper["title"]) > 60 else paper["title"]
        authors = ", ".join(paper.get("authors", [])[:3])
        if len(paper.get("authors", [])) > 3:
            authors += " et al."
        
        source_emoji = {"arXiv": "📄", "Semantic Scholar": "🎓", "Web of Science": "📚"}.get(paper["source"], "📝")
        
        message += f"{i}. {source_emoji} [{title}]({paper['url']})\n"
        message += f"   作者：{authors} | {paper.get('published', 'N/A')} | {paper['source']}\n\n"
    
    if len(new_papers) > 10:
        message += f"\n... 还有 {len(new_papers) - 10} 篇论文，请查看 GitHub Pages 获取完整列表。\n"
    
    message += f"\n📌 搜索策略：oceanography + AI/ML/数据同化"
    
    return message


def main():
    print("=" * 70)
    print(f"[START] Multi-Source Paper Monitor (arXiv + Semantic Scholar + WoS)")
    print(f"[INFO] Date: {date.today().isoformat()}")
    print("=" * 70)
    
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载关键词
    keywords = load_search_keywords()
    print(f"[INFO] Search keywords: {keywords}")
    
    # 加载已爬取 ID
    crawled_ids = load_crawled_ids()
    print(f"[INFO] Loaded {len(crawled_ids)} crawled IDs")
    
    # 搜索三个来源
    all_papers = []
    source_counts = {}
    
    # 1. arXiv
    arxiv_papers = search_arxiv_papers(keywords, max_results=20)
    all_papers.append(arxiv_papers)
    source_counts["arXiv"] = len(arxiv_papers)
    
    # 2. Semantic Scholar
    ss_papers = search_semantic_scholar(keywords, max_results=20)
    all_papers.append(ss_papers)
    source_counts["Semantic Scholar"] = len(ss_papers)
    
    # 3. Web of Science
    wos_papers = search_web_of_science(keywords, max_results=20)
    all_papers.append(wos_papers)
    source_counts["Web of Science"] = len(wos_papers)
    
    # 合并去重
    all_unique_papers = merge_and_deduplicate(all_papers)
    print(f"\n[INFO] Total unique papers: {len(all_unique_papers)}")
    
    # 查重
    new_papers = [p for p in all_unique_papers if p["id"] not in crawled_ids]
    print(f"[INFO] New papers: {len(new_papers)}")
    
    if not new_papers:
        message = f"✅ 今日（{date.today().isoformat()}）未发现新的物理海洋学+AI 相关论文。\n\n"
        message += f"搜索来源：arXiv, Semantic Scholar, Web of Science\n"
        message += f"关键词：oceanography + AI/ML/数据同化"
        send_feishu_message(message)
        print("[INFO] No new papers. Notification sent.")
        return
    
    # 构建并发送消息
    message = build_message(new_papers, source_counts)
    send_feishu_message(message)
    
    # 更新已爬取 ID
    new_ids = {p["id"] for p in new_papers}
    crawled_ids.update(new_ids)
    save_crawled_ids(crawled_ids)
    print(f"[INFO] Updated crawled_ids.txt with {len(new_ids)} new IDs")
    
    print("\n" + "=" * 70)
    print("[DONE] Multi-source monitor completed successfully")
    print("=" * 70)


if __name__ == "__main__":
    main()
