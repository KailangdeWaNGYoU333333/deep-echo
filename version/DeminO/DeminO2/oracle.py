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
step2 = import_module_from_file("2.py", "step2")
step3 = import_module_from_file("3.py", "step3")

TheoremKnowledgeBase = step1.TheoremKnowledgeBase
MathematicalReasoner = step2.MathematicalReasoner
QuantumStrategyDecoder = step3.QuantumStrategyDecoder
LeanVerifier = step3.LeanVerifier
QuantumProofEvolver = step3.QuantumProofEvolver

class DeepEchoOracle:
    def __init__(self, model_name="Qwen/Qwen2.5-Math-1.5B-Instruct"):
        print("🔮 初始化 Deep Echo 数学神谕...")
        print("[1/3] 构建知识库...")
        self.kb = TheoremKnowledgeBase().build_database()
        print("[2/3] 初始化推理器...")
        self.reasoner = MathematicalReasoner(self.kb)
        print("[3/3] 初始化量子进化引擎...")
        self.decoder = QuantumStrategyDecoder(model_name=model_name)
        self.verifier = LeanVerifier(lean_path="lean")
        self.evolver = QuantumProofEvolver(decoder=self.decoder, verifier=self.verifier, pop_size=50, seed_dim=1536)
        print("✅ 系统就绪\n")

    def consult(self, statement):
        print("=" * 70)
        print(f"📝 咨询: {statement[:60]}...")
        analysis = self.reasoner.analyze_statement(statement)
        print(f"\n📊 分析结果:\n   领域: {analysis['domain']}\n   难度: {analysis['difficulty']:.1f} / 10\n   已知定理: {'是' if analysis['is_known'] else '否'}")
        if analysis['is_known']:
            print(f"   等价于: {analysis['equivalent_to']}")
            return {"status": "known", "analysis": analysis}
        print(f"\n🔬 未知陈述，启动量子进化搜索...")
        best = self.evolver.run(f"example : {statement} := by", max_generations=100)
        print(f"\n📊 搜索结果:\n   证明找到: {'是 🎉' if best and best.verification_result['success'] else '否'}\n   最佳适应度: {best.fitness if best else 0:.1f}\n   进化代数: {self.evolver.generation}")
        return best

if __name__ == "__main__":
    oracle = DeepEchoOracle()
    print("\n" + "=" * 70 + "\nDeep Echo 数学神谕已就绪\n" + "=" * 70)
    while True:
        user_input = input("\n🧪 你的数学陈述: ").strip()
        if user_input.lower() in ('exit', 'quit', 'q'): break
        if user_input: oracle.consult(user_input)