import json
import requests
from bs4 import BeautifulSoup
import sentence_transformers
import chromadb
import numpy as np

# ==================== 配置 ====================
WIKI_URL = "https://en.wikipedia.org/wiki/List_of_theorems"
CACHE_FILE = "theorems_cache.json"
CHROMA_DB_DIR = "./chroma_theorem_db"
COLLECTION_NAME = "math_theorems"
MODEL_NAME = "intfloat/multilingual-e5-base"  # 数学友好，中英文通吃
# ==============================================

class TheoremKnowledgeBase:
    """定理知识库：收集、向量化、检索"""
    
    # 后备定理（网络不可用时使用）
    BACKUP_THEOREMS = [
        {"name": "Pythagorean theorem", 
         "statement": "In a right triangle, the square of the hypotenuse equals the sum of the squares of the other two sides.",
         "domain": "geometry"},
        {"name": "Fundamental theorem of arithmetic", 
         "statement": "Every integer greater than 1 can be uniquely factored into prime numbers.",
         "domain": "number theory"},
        {"name": "Prime number theorem", 
         "statement": "The number of primes less than x is approximately x / log(x).",
         "domain": "number theory"},
        {"name": "Fermat's Last Theorem", 
         "statement": "No three positive integers a, b, c satisfy a^n + b^n = c^n for any integer n > 2.",
         "domain": "number theory"},
        {"name": "Gödel's incompleteness theorems", 
         "statement": "Any consistent formal system rich enough to express arithmetic contains statements that cannot be proved or disproved within the system.",
         "domain": "logic"},
        {"name": "Four color theorem", 
         "statement": "Any planar map can be colored with at most four colors such that no adjacent regions share the same color.",
         "domain": "graph theory"},
        {"name": "Fundamental theorem of calculus", 
         "statement": "Differentiation and integration are inverse operations.",
         "domain": "calculus"},
        {"name": "Central limit theorem", 
         "statement": "The distribution of sample means approaches a normal distribution as sample size increases.",
         "domain": "probability"},
        {"name": "P vs NP", 
         "statement": "The class of problems solvable in polynomial time equals the class of problems verifiable in polynomial time?",
         "domain": "computational complexity"},
        {"name": "Riemann hypothesis", 
         "statement": "All non-trivial zeros of the Riemann zeta function have real part 1/2.",
         "domain": "number theory"},
    ]
    
    def __init__(self):
        self.model = None
        self.collection = None
        
    def fetch_wiki_theorems(self, url):
        """从维基百科抓取定理列表"""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            theorems = []
            content = soup.find('div', class_='mw-parser-output')
            if content:
                for ul in content.find_all('ul'):
                    for li in ul.find_all('li'):
                        a_tag = li.find('a')
                        if a_tag and a_tag.get('title'):
                            name = a_tag.get('title')
                            desc = li.get_text().strip()[:300]
                            theorems.append({"name": name, "statement": desc, "domain": "unknown"})
            # 去重
            seen = set()
            return [t for t in theorems if not (t['name'] in seen or seen.add(t['name']))]
        except:
            return None
    
    def load_theorems(self):
        """加载定理数据：缓存 > 网络 > 后备"""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        theorems = self.fetch_wiki_theorems(WIKI_URL)
        if theorems and len(theorems) > 10:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(theorems, f, ensure_ascii=False, indent=2)
            return theorems
        
        print("使用内置后备定理库")
        return self.BACKUP_THEOREMS
    
    def build_database(self):
        """构建向量数据库"""
        print(f"加载嵌入模型: {MODEL_NAME}")
        self.model = sentence_transformers.SentenceTransformer(MODEL_NAME)
        
        theorems = self.load_theorems()
        statements = [t['statement'] for t in theorems]
        
        print("生成嵌入向量...")
        embeddings = self.model.encode(statements, show_progress_bar=True)
        
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        try:
            client.delete_collection(COLLECTION_NAME)
        except:
            pass
        self.collection = client.create_collection(COLLECTION_NAME)
        
        self.collection.add(
            ids=[f"thm_{i}" for i in range(len(theorems))],
            embeddings=embeddings.tolist(),
            metadatas=[{"name": t["name"], "statement": t["statement"], 
                       "domain": t.get("domain", "unknown")} 
                      for t in theorems]
        )
        
        print(f"数据库就绪: {len(theorems)} 条定理")
        return self
    
    def search(self, query, top_k=10):
        """搜索最相似的定理"""
        query_emb = self.model.encode([f"query: {query}"], normalize_embeddings=True)
        results = self.collection.query(query_embeddings=query_emb.tolist(), n_results=top_k)
        return [
            {"name": meta["name"], "statement": meta["statement"], 
             "domain": meta.get("domain", "unknown"),
             "distance": dist}
            for meta, dist in zip(results['metadatas'][0], results['distances'][0])
        ]