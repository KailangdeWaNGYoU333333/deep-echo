import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import numpy as np
import random
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ProofCandidate:
    seed: np.ndarray
    proof_code: str
    fitness: float
    verification_result: Dict
    generation: int

class QuantumStrategyDecoder:
    """将量子种子解码为 Lean 4 证明策略"""
    
    def __init__(self, model_name="deepseek-ai/deepseek-math-7b-instruct"):
        print(f"加载证明生成模型: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        self.num_layers = len(self.model.model.layers)
    
    def inject_quantum_seed(self, seed_vector, strength=0.15):
        """将量子种子注入模型的所有层"""
        hooks = []
        # 为每层分配种子片段
        chunk_size = len(seed_vector) // self.num_layers
        
        for i, layer in enumerate(self.model.model.layers):
            start = i * chunk_size
            end = start + chunk_size
            layer_seed = seed_vector[start:end]
            
            def make_hook(layer_seed):
                def hook_fn(module, input, output):
                    noise = torch.tensor(
                        layer_seed, device=output.device
                    ).float().reshape(1, 1, -1)[:, :, :output.shape[-1]]
                    return output + strength * noise
                return hook_fn
            
            hooks.append(layer.self_attn.o_proj.register_forward_hook(make_hook(layer_seed)))
        
        return hooks
    
    def generate_proof(self, theorem_statement, seed_vector, max_length=512):
        """用量子种子生成 Lean 4 证明"""
        prompt = f"""-- Theorem to prove in Lean 4
{theorem_statement}

-- Proof:
theorem target : {theorem_statement} :=
by
"""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        hooks = self.inject_quantum_seed(seed_vector)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=0.85,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        for hook in hooks:
            hook.remove()
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

class LeanVerifier:
    """Lean 4 形式化验证器"""
    
    def __init__(self, lean_path="lean"):
        self.lean_path = lean_path
    
    def verify(self, lean_code, timeout=30):
        """验证 Lean 4 代码"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lean', delete=False) as f:
            f.write(lean_code)
            fname = f.name
        
        try:
            result = subprocess.run(
                [self.lean_path, fname],
                capture_output=True, text=True, timeout=timeout
            )
            
            success = result.returncode == 0
            errors = self.parse_errors(result.stderr) if not success else []
            
            return {
                "success": success,
                "errors": errors,
                "error_count": len(errors),
                "output": result.stdout[:300] if success else "",
                "error_output": result.stderr[:300] if not success else ""
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "errors": [{"type": "timeout"}], "error_count": 1}
        finally:
            os.unlink(fname)
    
    def parse_errors(self, text):
        """解析 Lean 错误信息"""
        errors = []
        for line in text.split('\n'):
            line_lower = line.lower()
            if 'error' in line_lower:
                if 'unknown identifier' in line_lower:
                    errors.append({"type": "unknown_identifier"})
                elif 'type mismatch' in line_lower:
                    errors.append({"type": "type_mismatch"})
                elif 'unsolved goals' in line_lower:
                    errors.append({"type": "unsolved_goals"})
                elif 'timeout' in line_lower:
                    errors.append({"type": "timeout"})
                else:
                    errors.append({"type": "other", "detail": line[:100]})
        return errors
    
    def estimate_progress(self, lean_code):
        """估计证明完成度"""
        score = 0.0
        if "theorem" in lean_code: score += 0.2
        if "by" in lean_code or "begin" in lean_code: score += 0.1
        
        tactics = ["apply", "have", "cases", "induction", "rw", "simp", 
                   "refine", "intro", "exact", "calc", "ring", "linarith", "assumption"]
        used = sum(lean_code.count(t) for t in tactics)
        score += min(0.4, used * 0.05)
        
        if "qed" in lean_code.lower() or "done" in lean_code.lower(): score += 0.3
        
        return min(1.0, score)

class QuantumProofEvolver:
    """量子进化证明搜索器"""
    
    def __init__(self, decoder, verifier, pop_size=100, seed_dim=768):
        self.decoder = decoder
        self.verifier = verifier
        self.pop_size = pop_size
        self.seed_dim = seed_dim
        self.population = []
        self.best: Optional[ProofCandidate] = None
        self.generation = 0
    
    def initialize(self):
        """用量子随机噪声初始化种群"""
        self.population = []
        for _ in range(self.pop_size):
            seed = np.random.normal(0, 1, self.seed_dim)
            seed = seed / np.linalg.norm(seed)
            self.population.append(seed)
        self.best = None
        self.generation = 0
    
    def fitness(self, proof_code, verification, theorem):
        """多维适应度计算"""
        score = 0.0
        
        if verification["success"]:
            score += 100.0
            # 简洁性加分
            score += max(0, 20 - len(proof_code) / 100)
            return score
        
        # 未成功时的渐进评分
        errors = verification.get("errors", [])
        error_count = verification.get("error_count", 1)
        
        score += max(0, 30 - error_count * 5)
        
        for err in errors:
            if err["type"] == "unsolved_goals":
                score += 15
            elif err["type"] == "type_mismatch":
                score += 5
        
        progress = self.verifier.estimate_progress(proof_code)
        score += progress * 20
        
        return score
    
    def quantum_crossover(self, p1, p2, mutation_rate=0.1):
        """量子干涉交叉 + 涨落变异"""
        mask = np.random.rand(self.seed_dim) > 0.5
        child = np.where(mask, p1, p2)
        
        # 量子涨落变异
        mutation = np.random.normal(0, mutation_rate, self.seed_dim)
        child = child + mutation
        
        return child / np.linalg.norm(child)
    
    def evaluate_population(self, theorem):
        """评估整个种群"""
        candidates = []
        for i, seed in enumerate(self.population):
            proof = self.decoder.generate_proof(theorem, seed)
            verif = self.verifier.verify(proof)
            fit = self.fitness(proof, verif, theorem)
            
            candidates.append(ProofCandidate(
                seed=seed.copy(),
                proof_code=proof,
                fitness=fit,
                verification_result=verif,
                generation=self.generation
            ))
            
            if (i + 1) % 20 == 0:
                print(f"  评估进度: {i+1}/{self.pop_size}")
        
        candidates.sort(key=lambda c: c.fitness, reverse=True)
        return candidates
    
    def evolve_generation(self, theorem):
        """执行一代进化"""
        print(f"\n🌊 第 {self.generation} 代进化中...")
        
        candidates = self.evaluate_population(theorem)
        
        # 更新最佳
        if self.best is None or candidates[0].fitness > self.best.fitness:
            self.best = candidates[0]
        
        # 精英保留 (20%)
        elite_count = max(2, self.pop_size // 5)
        elites = candidates[:elite_count]
        
        # 生成新种群
        new_pop = [e.seed.copy() for e in elites]
        
        while len(new_pop) < self.pop_size:
            p1 = random.choice(elites[:5]).seed
            p2 = random.choice(elites[:5]).seed
            child = self.quantum_crossover(p1, p2)
            new_pop.append(child)
        
        self.population = new_pop
        self.generation += 1
        
        # 统计
        avg = np.mean([c.fitness for c in candidates])
        print(f"  最佳: {candidates[0].fitness:.1f} | 平均: {avg:.1f} | 精英: {elite_count}")
        
        if candidates[0].verification_result["success"]:
            print(f"  🎯 发现有效证明！")
            return True
        
        return False
    
    def run(self, theorem, max_generations=500):
        """运行完整进化搜索"""
        self.initialize()
        
        print(f"🚀 开始量子进化搜索")
        print(f"   种群: {self.pop_size} | 最大代数: {max_generations}")
        print(f"   目标: {theorem[:80]}...")
        
        for gen in range(max_generations):
            success = self.evolve_generation(theorem)
            
            if success:
                print(f"\n✨ 第 {gen} 代进化成功！")
                break
            
            if gen % 50 == 0 and self.best:
                print(f"\n📜 当前最佳证明片段 (Gen {gen}):")
                print(self.best.proof_code[:200])
        
        return self.best

class DeepEchoOracle:
    """
    完整的三步系统：
    1. 语义检索识别
    2. 逻辑关系分析
    3. 量子进化搜索
    """
    
    def __init__(self):
        print("🔮 初始化 Deep Echo 数学神谕...")
        
        print("[1/3] 构建知识库...")
        self.kb = TheoremKnowledgeBase().build_database()
        
        print("[2/3] 初始化推理器...")
        self.reasoner = MathematicalReasoner(self.kb)
        
        print("[3/3] 初始化量子进化引擎...")
        self.decoder = QuantumStrategyDecoder()
        self.verifier = LeanVerifier()
        self.evolver = QuantumProofEvolver(self.decoder, self.verifier)
        
        print("✅ 系统就绪\n")
    
    def consult(self, statement):
        """
        咨询任何数学陈述
        """
        print("=" * 70)
        print(f"📝 咨询: {statement[:60]}...")
        print("=" * 70)
        
        # 步骤 1-2: 识别与分析
        analysis = self.reasoner.analyze_statement(statement)
        
        print(f"\n📊 分析结果:")
        print(f"   领域: {analysis['domain']}")
        print(f"   难度: {analysis['difficulty']:.1f}/10")
        print(f"   已知定理: {'是' if analysis['is_known'] else '否'}")
        
        if analysis['is_known']:
            print(f"   等价于: {analysis['equivalent_to']}")
            print(f"\n📚 相关定理:")
            for t in analysis['related_theorems'][:5]:
                print(f"   - {t['name']} (距离: {t['distance']:.3f})")
            return {"status": "known", "analysis": analysis}
        
        # 步骤 3: 未知陈述 → 量子进化搜索
        print(f"\n🔬 未知陈述，启动量子进化搜索...")
        
        lean_stmt = f"example : {statement} := by"
        best = self.evolver.run(lean_stmt, max_generations=300)
        
        result = {
            "status": "searched",
            "analysis": analysis,
            "proof_found": best.verification_result["success"] if best else False,
            "best_fitness": best.fitness if best else 0,
            "best_proof": best.proof_code if best else None,
            "generations": self.evolver.generation
        }
        
        print(f"\n📊 搜索结果:")
        print(f"   证明找到: {'是 🎉' if result['proof_found'] else '否'}")
        print(f"   最佳适应度: {result['best_fitness']:.1f}")
        print(f"   进化代数: {result['generations']}")
        
        return result

# ============================
# 主程序入口
# ============================
if __name__ == "__main__":
    oracle = DeepEchoOracle()
    
    # 交互式咨询
    print("\n" + "=" * 70)
    print("Deep Echo 数学神谕已就绪")
    print("输入任何数学陈述，我将识别它或尝试证明它")
    print("输入 'exit' 退出")
    print("=" * 70)
    
    while True:
        user_input = input("\n🧪 你的数学陈述: ").strip()
        if user_input.lower() in ('exit', 'quit', 'q'):
            print("再见。")
            break
        if not user_input:
            continue
        
        oracle.consult(user_input)