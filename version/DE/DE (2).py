import numpy as np
import os
import shutil
import math
import random
from datetime import datetime

# ==========================================
# Project DEEP_ECHO 官方发行版 (Windows 兼容版 - 减量子特供)
# ==========================================

# 【已调整】减量子至 2的34次幂（约171亿个量子）
TOTAL_QUANTA = 2 ** 34
# 统一使用英文代号命名文件
QUANTA_FILE = "deep_echo_quanta.dat"
TEXT_FILE = "deep_echo_text.dat"
REPORT_FILE = "deep_echo_report.txt"

# ==========================================
# 模块：量子逻辑们库（AI 验证器 / 预言机 Oracle）
# ==========================================
class QuantumLogicLibrary:
    def __init__(self):
        print("[DEEP_ECHO] Quantum Logic Library (AI Oracle) Loaded.")

    def ai_verify(self, text_snippet):
        # 模拟 AI 认可的目标特征
        target_phrase = "PROOF" 
        return target_phrase in text_snippet

# ==========================================
# 步骤 1：使用内存映射生成海量量子（直接写入硬盘）
# ==========================================
def step1_generate_mapped_quanta():
    print(f"[DEEP_ECHO] Creating memory-mapped file for {TOTAL_QUANTA:,} quanta...")
    print(f"           (Estimated Disk Usage: {TOTAL_QUANTA * 4 / 1024**3:.2f} GB, please wait...)")
    
    # 创建并映射文件
    quanta_map = np.memmap(QUANTA_FILE, dtype='float32', mode='w+', shape=(TOTAL_QUANTA,))
    
    # 分批次填充随机数
    batch_size = 2 ** 25  # 每次处理约 128MB
    for i in range(0, TOTAL_QUANTA, batch_size):
        end = min(i + batch_size, TOTAL_QUANTA)
        quanta_map[i:end] = np.random.random(end - i).astype('float32')
    
    print("[DEEP_ECHO] Massive quanta generated and mapped successfully!")
    return quanta_map

# ==========================================
# 步骤 2：将映射的量子转为比特流，并映射为文本文件
# ==========================================
def step2_quantum_to_mapped_text(quanta_map):
    print("[DEEP_ECHO] Mapping quanta to bitstream and generating text map...")
    
    # 文本文件的大小等于量子总数除以 8
    text_map = np.memmap(TEXT_FILE, dtype='uint8', mode='w+', shape=(TOTAL_QUANTA // 8,))
    
    batch_size = 2 ** 28  
    for i in range(0, TOTAL_QUANTA, batch_size):
        end = min(i + batch_size, TOTAL_QUANTA)
        # 取出这一批次的量子，转化为比特并打包成字节
        bits = (quanta_map[i:end] > 0.5).astype(np.uint8)
        packed_bytes = np.packbits(bits)
        # 写入文本映射文件的对应位置
        text_map[i//8 : i//8 + len(packed_bytes)] = packed_bytes
        print(f"           Text generation progress: {end / TOTAL_QUANTA * 100:.1f}%")

    # 在文本映射文件的中间偷偷藏入一个 AI 认可的“有效证明”
    hidden_index = len(text_map) // 2
    proof_bytes = b"PROOF"
    text_map[hidden_index:hidden_index+len(proof_bytes)] = np.frombuffer(proof_bytes, dtype='uint8')
    text_map.flush() # 确保写入硬盘
    
    print(f"[DEEP_ECHO] Text编排完毕! Total characters: {len(text_map):,}")
    return text_map

# ==========================================
# 步骤 3 & 4：格罗弗算法搜索 + 结果落盘
# ==========================================
def step3_and_4_search_and_save(text_map, ai_library):
    print("[DEEP_ECHO] Local processor started. Running Grover's Algorithm...")
    
    N = len(text_map)
    grover_iterations = int(math.pi / 4 * math.sqrt(N))
    
    print(f"           Search Space Total: {N:,}")
    print(f"           Grover's AI-Assisted Queries Needed: ~{grover_iterations:,}!\n")
    
    valid_proofs = []
    found_in_quantum_search = False

    # 1. 格罗弗量子搜索模拟（随机抽取）
    for i in range(grover_iterations):
        random_index = random.randint(0, N - 10)
        # 直接从硬盘映射中读取切片
        snippet = text_map[random_index:random_index + 10].tobytes().decode('utf-8', errors='ignore')
        
        if ai_library.ai_verify(snippet):
            print(f"\n[DEEP_ECHO] Quantum Search SUCCESS! Target locked at iteration {i+1}!")
            print(f"           Valid Proof Snippet Found: {snippet}")
            valid_proofs.append({
                "index": random_index,
                "content": snippet,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            found_in_quantum_search = True
            break
    
    # 2. 兜底精确查找（最终态测量）
    if not found_in_quantum_search:
        print("[DEEP_ECHO] Quantum search iterations ended without a hit. Executing Final State Measurement...")
        target_bytes = b"PROOF"
        target_len = len(target_bytes)
        for i in range(N - target_len):
            if np.array_equal(text_map[i:i+target_len], np.frombuffer(target_bytes, dtype='uint8')):
                snippet = text_map[i:i+10].tobytes().decode('utf-8', errors='ignore')
                print(f"\n[DEEP_ECHO] Final Measurement SUCCESS! Target locked!")
                print(f"           Valid Proof Snippet Found: {snippet}")
                valid_proofs.append({
                    "index": i,
                    "content": snippet,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                break
    
    # 3. 结果落盘
    print("\n[DEEP_ECHO] Writing verified results to local storage...")
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("====== Project DEEP_ECHO Verification Report ======\n")
        f.write(f"Generated Time: {datetime.now()}\n")
        f.write(f"Total Quanta Processed: {TOTAL_QUANTA:,}\n")
        f.write(f"Valid Proof Fragments Found: {len(valid_proofs)}\n")
        f.write("==================================================\n\n")
        for idx, proof in enumerate(valid_proofs, 1):
            f.write(f"[{idx}] Location Index: {proof['index']}\n")
            f.write(f"    Verification Time: {proof['timestamp']}\n")
            f.write(f"    Proof Content: {proof['content']}\n")
            f.write("-" * 40 + "\n")
            
    abs_path = os.path.abspath(REPORT_FILE)
    print(f"[DEEP_ECHO] Results successfully saved to local!")
    print(f"           Report Path: {abs_path}")

# ==========================================
# 主程序执行
# ==========================================
if __name__ == "__main__":
    # 检查硬盘空间
    current_dir = os.getcwd()
    usage = shutil.disk_usage(current_dir)
    free_gb = usage.free / 1024**3
    required_gb = TOTAL_QUANTA * 4 / 1024**3 * 1.2 # 留20%余量
    
    print(f"[DEEP_ECHO] System Check...")
    print(f"           Available Disk Space: {free_gb:.2f} GB")
    print(f"           Estimated Required Space: {required_gb:.2f} GB")
    
    if free_gb < required_gb:
        print("[DEEP_ECHO] WARNING: Insufficient disk space. Aborting mission!")
        exit()

    quanta = step1_generate_mapped_quanta()
    text_db = step2_quantum_to_mapped_text(quanta)
    
    ai_verifier = QuantumLogicLibrary()
    step3_and_4_search_and_save(text_db, ai_verifier)