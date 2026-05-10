import os; os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import sys
import importlib.util

def import_module_from_file(filepath, module_name):
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

step1 = import_module_from_file("1.py", "step1")
step3 = import_module_from_file("3.py", "step3")

TheoremKnowledgeBase = step1.TheoremKnowledgeBase
LeanVerifier = step3.LeanVerifier
GeneTreeEvolver = step3.GeneTreeEvolver

class DeepEchoOracle:
    def __init__(self):
        print("🔮 初始化 Deep Echo 数学神谕...")
        print("[1/3] 构建知识库...")
        self.kb = TheoremKnowledgeBase().build_database()
        print("[2/3] 跳过推理器（简化版）...")
        print("[3/3] 初始化语法树进化引擎...")
        self.verifier = LeanVerifier(lean_path=r"C:\Users\Administrator\.elan\toolchains\leanprover--lean4---v4.29.1\bin\lean.exe")
        self.evolver = GeneTreeEvolver(verifier=self.verifier, pop_size=200, max_depth=5)
        print("✅ 系统就绪\n")

    def consult(self, statement):
        print("=" * 70)
        print(f"📝 目标: {statement}")
        print("=" * 70)
        print(f"\n🔬 启动语法树进化搜索...")
        lean_stmt = f"example : {statement} := by"
        best = self.evolver.run(lean_stmt, max_generations=100)
        
        if best and isinstance(best, tuple) and len(best) >= 3:
            best_gene, best_fitness, best_verif = best[0], best[1], best[2]
            proof_found = best_verif.get("success", False) if isinstance(best_verif, dict) else False
        else:
            best_fitness = 0
            proof_found = False
        
        print(f"\n📊 搜索结果:\n   证明找到: {'是 🎉' if proof_found else '否'}\n   最佳适应度: {best_fitness:.1f}\n   进化代数: {self.evolver.generation}")
        return best

if __name__ == "__main__":
    oracle = DeepEchoOracle()
    print("\n" + "=" * 70 + "\nDeep Echo 数学神谕已就绪\n" + "=" * 70)
    while True:
        user_input = input("\n🧪 你的数学陈述: ").strip()
        if user_input.lower() in ('exit', 'quit', 'q'):
            break
        if user_input:
            oracle.consult(user_input)