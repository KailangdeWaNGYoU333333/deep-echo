"""
批量导入百度百科数学定理
运行一次即可生成 theorems_cache.json
国内网络直接运行，无需VPN
"""
import json
import requests
from bs4 import BeautifulSoup
import time
import os
import re

# 百度百科“数学定理列表”页面，列出了几百条常见定理
BAIKE_THEOREM_LIST_URL = "https://baike.baidu.com/item/%E6%95%B0%E5%AD%A6%E5%AE%9A%E7%90%86%E5%88%97%E8%A1%A8/5705999"

# 如果列表页失效，用这些高优先级定理兜底
FALLBACK_THEOREMS = [
    {"name": "勾股定理", "statement": "直角三角形两直角边的平方和等于斜边的平方。", "domain": "geometry"},
    {"name": "费马大定理", "statement": "当整数n大于2时，关于x,y,z的方程x^n+y^n=z^n没有正整数解。", "domain": "number theory"},
    {"name": "费马小定理", "statement": "如果p是一个质数，而a是任意一个不能被p整除的整数，那么a^(p-1)-1能被p整除。", "domain": "number theory"},
    {"name": "代数基本定理", "statement": "任何一个非零的一元n次复系数多项式，都正好有n个复数根。", "domain": "algebra"},
    {"name": "微积分基本定理", "statement": "描述了微分和积分运算之间的关系，是微积分学的核心定理。", "domain": "calculus"},
    {"name": "中心极限定理", "statement": "在适当的条件下，大量独立随机变量的均值经标准化后依分布收敛于标准正态分布。", "domain": "probability"},
    {"name": "哥德巴赫猜想", "statement": "任一大于2的偶数都可写成两个质数之和。", "domain": "number theory"},
    {"name": "四色定理", "statement": "任何一张地图只用四种颜色就能使具有共同边界的国家着上不同的颜色。", "domain": "graph theory"},
    {"name": "算术基本定理", "statement": "任何一个大于1的自然数，都可以唯一地分解成有限个质数的乘积。", "domain": "number theory"},
    {"name": "P vs NP", "statement": "P类问题是否等于NP类问题？", "domain": "computational complexity"},
]

def scrape_baidu_list(url):
    """从百度百科列表页抓取所有定理名称"""
    theorems = []
    try:
        print(f"正在访问: {url}")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DeepEcho/1.0"}
        resp = requests.get(url, timeout=15, headers=headers)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 百度百科列表页的定理通常在 class="para" 的段落里，或者在目录链接中
        # 方法1: 从目录中提取
        catalog = soup.find('div', class_='catalog')
        if not catalog:
            catalog = soup.find('div', class_='lemma-catalog')
        if catalog:
            for a_tag in catalog.find_all('a'):
                title = a_tag.get('title', '').strip()
                if title and len(title) > 1:
                    theorems.append({
                        "name": title,
                        "statement": title,
                        "domain": _guess_domain(title)
                    })
        
        # 方法2: 从正文段落中提取加粗的定理名称
        if len(theorems) < 20:
            para = soup.find('div', class_='para')
            if not para:
                para = soup.find('div', class_='lemma-content')
            if para:
                text = para.get_text()
                # 提取中文定理名（通常是连续的汉字+定理/定律/公式）
                found = re.findall(r'[\u4e00-\u9fff]{2,12}(?:定理|定律|公式|猜想|引理|法则|公理)', text)
                for name in found:
                    if name not in [t['name'] for t in theorems]:
                        theorems.append({
                            "name": name,
                            "statement": name,
                            "domain": _guess_domain(name)
                        })
        
        print(f"  从列表页提取到 {len(theorems)} 条定理")
    
    except Exception as e:
        print(f"  列表页抓取失败: {e}")
    
    return theorems

def _guess_domain(name):
    """根据定理的中文名猜测所属领域"""
    domain_keywords = {
        "number theory": ["数论", "质数", "素数", "整数", "同余", "整除", "费马", "哥德巴赫", "黎曼", "欧拉"],
        "geometry": ["几何", "三角形", "圆", "角", "弦", "面积", "体积", "勾股", "欧几里得"],
        "algebra": ["代数", "方程", "多项式", "群", "环", "域", "矩阵", "线性"],
        "calculus": ["微积分", "极限", "导数", "积分", "微分", "级数", "泰勒", "拉格朗日"],
        "probability": ["概率", "随机", "分布", "大数", "中心极限", "贝叶斯"],
        "logic": ["逻辑", "不完备", "哥德尔", "形式"],
        "graph theory": ["图论", "四色", "五色", "一笔画"],
        "computational complexity": ["P=NP", "P≠NP", "NP", "计算", "复杂度", "图灵"],
    }
    
    for domain, keywords in domain_keywords.items():
        for kw in keywords:
            if kw in name:
                return domain
    
    return "general"

def main():
    print("🧩 Deep Echo 定理导入器（百度百科版）")
    print(f"   目标: {BAIKE_THEOREM_LIST_URL}\n")
    
    # 从百度百科数学定理列表页抓取
    all_theorems = scrape_baidu_list(BAIKE_THEOREM_LIST_URL)
    
    # 如果抓太少，就用后备定理补充
    if len(all_theorems) < 10:
        print(f"  列表页提取不足（仅 {len(all_theorems)} 条），启用后备定理库补充")
        for t in FALLBACK_THEOREMS:
            if t['name'] not in [x['name'] for x in all_theorems]:
                all_theorems.append(t)
    
    # 去重
    seen = set()
    unique = []
    for t in all_theorems:
        if t['name'] not in seen:
            seen.add(t['name'])
            unique.append(t)
    
    print(f"\n✅ 总计: {len(unique)} 条不重复定理")
    
    # 保存
    output_file = "theorems_cache.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    
    print(f"   已保存到 {output_file}")
    print(f"   文件大小: {os.path.getsize(output_file) / 1024:.1f} KB")
    print(f"\n下一步:")
    print(f"   1. 删除旧向量库: rmdir /s chroma_theorem_db")
    print(f"   2. 重启 oracle.py，系统会自动加载新定理库")

if __name__ == "__main__":
    main()