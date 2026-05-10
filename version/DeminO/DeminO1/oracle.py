"""
Deep Echo Oracle - 主入口
串联 1.py (知识库) + 2.py (推理器) + 3.py (量子进化)
"""

# 导入你的三个模块
# 假设文件名为 1.py, 2.py, 3.py，放在同一目录
import importlib.util
import sys

def import_module_from_file(filepath, module_name):
    """从文件路径动态导入模块"""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# 导入三个步骤模块
step1 = import_module_from_file("1.py", "step1")
step2 = import_module_from_file("2.py", "step2")
step3 = import_module_from_file("3.py", "step3")

TheoremKnowledgeBase = step1.TheoremKnowledgeBase
MathematicalReasoner = step2.MathematicalReasoner
QuantumStrategyDecoder = step3.QuantumStrategyDecoder
LeanVerifier = step3.LeanVerifier
QuantumProofEvolver = step3.QuantumProofEvolver


class DeepEchoOracle:
    """
    完整三步系统：识别 → 推理 → 量子进化搜索
    """
    
    def __init__(self, lean_path="lean", model_name="deepseek-ai/deepseek-math-7b-instruct"):
        print("🔮 初始化 Deep Echo 数学神谕...")
        
        print("[1/3] 构建知识库...")
        self.kb = TheoremKnowledgeBase().build_database()
        
        print("[2/3] 初始化推理器...")
        self.reasoner = MathematicalReasoner(self.kb)
        
        print("[3/3] 初始化量子进化引擎...")
        self.decoder = QuantumStrategyDecoder(model_name=model_name)
        self.verifier = LeanVerifier(lean_path=lean_path)
        self.evolver = QuantumProofEvolver(
            decoder=self.decoder,
            verifier=self.verifier,
            pop_size=100,
            seed_dim=768
        )
        
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
        
        # 步骤 3: 未知 → 量子进化搜索
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
# 主程序
# ============================
if __name__ == "__main__":
    oracle = DeepEchoOracle()
    
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