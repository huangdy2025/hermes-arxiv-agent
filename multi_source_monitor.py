#!/usr/bin/env python3
"""
Multi-Source Paper Monitor (arXiv + Semantic Scholar + Scopus)
三源合一文献监控 - GitHub Actions 版本
支持：
  - arXiv: 预印本（免费，无需 API key）
  - Semantic Scholar: 全学科期刊（免费，可选 API key）
  - Scopus: 核心期刊（免费，需注册 API key）
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

# Scopus 配置
SCOPUS_API_URL = "https://api.elsevier.com/content/search/scopus"
SCOPUS_API_KEY = os.environ.get("SCOPUS_API_KEY", "")  # 必需

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


def load_search_config():
    """加载分数据源的搜索配置"""
    config_file = Path("search_config.json")
    if not config_file.exists():
        # 默认配置
        return {
            "arxiv": "oceanography AND (deep learning OR neural network OR transformer OR AI OR machine learning)",
            "semantic_scholar": "oceanography AND machine learning OR deep learning OR AI",
            "scopus": "TITLE-ABS-KEY(oceanography AND (deep learning OR neural network OR AI OR machine learning))"
        }
    
    config = json.loads(config_file.read_text())
    return config


def generate_paper_id(source: str, identifier: str) -> str:
    """生成唯一论文 ID（用于去重）"""
    return f"{source}:{identifier}"


def search_arxiv_papers(ocean_keywords: str, ai_keywords: str, max_results: int = 20):
    """搜索 arXiv 论文（带重试）
    
    arXiv 使用 AND 连接两个查询条件
    """
    # 构建 arXiv 查询：(海洋学关键词) AND (AI 关键词)
    search_query = f"({ocean_keywords}) AND ({ai_keywords})"
    print(f"\n[arXiv] Searching: {search_query}")
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt > 0:
                delay = RETRY_DELAY * (2 ** (attempt - 1)) + random.uniform(0.5, 2.0)
                print(f"[arXiv] Retrying in {delay:.1f}s...")
                time.sleep(delay)
            elif attempt == 0:
                time.sleep(REQUEST_INTERVAL)
            
            params = {
                "search_query": search_query,
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
                    "authors": authors[:5],
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
    """搜索 Semantic Scholar 论文
    
    Semantic Scholar 使用自然语言查询，支持 OR/AND 逻辑
    """
    print(f"\n[Semantic Scholar] Searching: {keywords}")
    
    headers = {"Content-Type": "application/json"}
    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY
    
    # Semantic Scholar 直接使用自然语言查询
    query_text = keywords
    
    params = {
        "query": query_text,
        "fields": "title,abstract,publicationDate,authors,url,publicationTypes,journal,venue,year,openAccessPdf",
        "year": f"{(datetime.now().year - 2)}-",  # 最近 2-3 年
        "limit": max_results
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
                
                pdf_url = paper.get("openAccessPdf", {}).get("url") if paper.get("openAccessPdf") else None
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


def search_scopus(keywords: str, max_results: int = 20):
    """搜索 Scopus 论文
    
    Scopus 使用专门的查询语法：
    - TITLE-ABS-KEY(): 搜索标题、摘要、关键词
    - AND/OR/NOT: 逻辑运算符
    - PUBYEAR >: 出版年份过滤
    """
    print(f"\n[Scopus] Searching: {keywords}")
    
    if not SCOPUS_API_KEY:
        print("[Scopus] API key not configured, skipping")
        return []
    
    headers = {
        "X-ELS-APIKey": SCOPUS_API_KEY,
        "Accept": "application/json"
    }
    
    # Scopus 查询已经是指定的语法，直接使用
    # 添加出版年份过滤（最近 3 年）
    scopus_query = f"{keywords} AND PUBYEAR > {datetime.now().year - 3}"
    
    params = {
        "query": scopus_query,
        "count": max_results,
        "start": 0,
        "sortBy": "prism_coverdate",
        "sortDirection": "desc",
        "view": "COMPLETE",  # 获取完整信息
    }
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            if attempt > 0:
                time.sleep(RETRY_DELAY * (2 ** (attempt - 1)))
            elif attempt == 0:
                time.sleep(REQUEST_INTERVAL)
            
            response = requests.get(
                SCOPUS_API_URL,
                params=params,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 401 or response.status_code == 403:
                print(f"[Scopus] Authentication failed: {response.status_code}")
                print(f"[Scopus] Please check your API key at https://dev.elsevier.com")
                return []
            
            if response.status_code == 429:
                print(f"[Scopus] Rate limited (429), attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES:
                    continue
            
            response.raise_for_status()
            data = response.json()
            
            papers = []
            
            # Scopus API 返回结构：search-results -> entry
            entries = data.get("search-results", {}).get("entry", [])
            
            for entry in entries:
                # 获取 DOI 或 Scopus ID
                doi = entry.get("prism_doi", "")
                scopus_id = entry.get("dc:identifier", "").replace("SCOPUS_ID:", "")
                paper_id = doi or scopus_id
                
                if not paper_id:
                    continue
                
                title = entry.get("dc:title", "No title")
                
                # 获取摘要
                abstract = entry.get("dc:description", "No abstract")
                if not abstract or abstract == "No abstract":
                    abstract = "No abstract available"
                abstract = abstract[:500]
                
                # 获取作者
                authors = []
                if "authkeywords" in entry:
                    # authkeywords 可能是一个列表或字典
                    auth_list = entry["authkeywords"]
                    if isinstance(auth_list, dict):
                        auth_list = auth_list.get("$text", "").split("|")
                    elif isinstance(auth_list, list):
                        auth_list = [item.get("$text", "") if isinstance(item, dict) else str(item) for item in auth_list]
                    else:
                        auth_list = str(auth_list).split("|")
                    
                    for i, kw in enumerate(auth_list[:5]):
                        authors.append(kw.strip())
                
                # 出版日期
                pub_date = entry.get("prism_coverdate", "")[:10] if entry.get("prism_coverdate") else ""
                
                # 链接
                url = entry.get("link", [{}])[0].get("@href", "") if entry.get("link") else ""
                if not url and doi:
                    url = f"https://doi.org/{doi}"
                elif not url and scopus_id:
                    url = f"https://www.scopus.com/record/display.uri?eid={scopus_id}"
                
                # 期刊信息
                journal = entry.get("prism_publicationName", "")
                
                papers.append({
                    "id": generate_paper_id("scopus", paper_id),
                    "source": "Scopus",
                    "doi": doi,
                    "scopus_id": scopus_id,
                    "title": title,
                    "abstract": abstract,
                    "published": pub_date,
                    "authors": authors,
                    "url": url,
                    "journal": journal,
                })
                
                if len(papers) >= max_results:
                    break
            
            print(f"[Scopus] Found {len(papers)} papers")
            return papers
            
        except json.JSONDecodeError as e:
            print(f"[Scopus] JSON parse error: {e}")
            print(f"[Scopus] Response: {response.text[:500]}")
            if attempt >= MAX_RETRIES:
                return []
        except Exception as e:
            print(f"[Scopus] Error: {e}")
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
    
    # 按出版日期排序
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
    message += f"   • Scopus: {source_counts.get('Scopus', 0)} 篇\n\n"
    
    message += "**最新论文列表：**\n\n"
    
    for i, paper in enumerate(new_papers[:10], 1):
        title = paper["title"][:60] + "..." if len(paper["title"]) > 60 else paper["title"]
        authors = ", ".join(paper.get("authors", [])[:3]) if paper.get("authors") else "Unknown"
        if len(paper.get("authors", [])) > 3:
            authors += " et al."
        
        source_emoji = {"arXiv": "📄", "Semantic Scholar": "🎓", "Scopus": "📚"}.get(paper["source"], "📝")
        
        message += f"{i}. {source_emoji} [{title}]({paper['url']})\n"
        message += f"   作者：{authors} | {paper.get('published', 'N/A')} | {paper['source']}\n\n"
    
    if len(new_papers) > 10:
        message += f"\n... 还有 {len(new_papers) - 10} 篇论文，请查看 GitHub Pages 获取完整列表。\n"
    
    message += f"\n📌 搜索策略：oceanography + AI/ML/数据同化"
    
    return message


def main():
    print("=" * 70)
    print(f"[START] Multi-Source Paper Monitor (arXiv + Semantic Scholar + Scopus)")
    print(f"[INFO] Date: {date.today().isoformat()}")
    print("=" * 70)
    
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载分数据源的搜索配置
    search_config = load_search_config()
    arxiv_ocean = search_config.get("arxiv", "")
    arxiv_ai = search_config.get("arxiv_ai", "")
    semantic_scholar_query = search_config.get("semantic_scholar", "")
    scopus_query = search_config.get("scopus", "")
    
    print(f"[INFO] arXiv 海洋学关键词：{arxiv_ocean}")
    print(f"[INFO] arXiv AI 关键词：{arxiv_ai}")
    print(f"[INFO] Semantic Scholar 查询：{semantic_scholar_query}")
    print(f"[INFO] Scopus 查询：{scopus_query}")
    
    # 加载已爬取 ID
    crawled_ids = load_crawled_ids()
    print(f"[INFO] Loaded {len(crawled_ids)} crawled IDs")
    
    # 搜索三个来源
    all_papers = []
    source_counts = {}
    
    # 1. arXiv - 使用分离的海洋学和 AI 关键词
    arxiv_papers = search_arxiv_papers(arxiv_ocean, arxiv_ai, max_results=20)
    all_papers.append(arxiv_papers)
    source_counts["arXiv"] = len(arxiv_papers)
    
    # 2. Semantic Scholar - 使用完整的自然语言查询
    ss_papers = search_semantic_scholar(semantic_scholar_query, max_results=20)
    all_papers.append(ss_papers)
    source_counts["Semantic Scholar"] = len(ss_papers)
    
    # 3. Scopus - 使用 Scopus 专用语法
    scopus_papers = search_scopus(scopus_query, max_results=20)
    all_papers.append(scopus_papers)
    source_counts["Scopus"] = len(scopus_papers)
    
    # 合并去重
    all_unique_papers = merge_and_deduplicate(all_papers)
    print(f"\n[INFO] Total unique papers: {len(all_unique_papers)}")
    
    # 查重
    new_papers = [p for p in all_unique_papers if p["id"] not in crawled_ids]
    print(f"[INFO] New papers: {len(new_papers)}")
    
    if not new_papers:
        message = f"✅ 今日（{date.today().isoformat()}）未发现新的物理海洋学+AI 相关论文。\n\n"
        message += f"搜索来源：arXiv, Semantic Scholar, Scopus\n"
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
