import os
import tempfile
import numpy as np
import random
import torch
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer

@dataclass
class ProofCandidate:
    seed: np.ndarray
    proof_code: str
    fitness: float
    verification_result: Dict
    generation: int

class QuantumStrategyDecoder:
    def __init__(self, model_name="Qwen/Qwen2.5-Math-1.5B-Instruct"):
        print(f"加载证明生成模型: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            offload_folder="./offload",
        )
        self.model.eval()

    def generate_proof(self, theorem_statement, seed_vector, max_length=512):
        prompt = f"/-- Theorem to prove in Lean 4 -/\n{theorem_statement}\n\nProof:"
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        seed_int = int(np.abs(seed_vector).sum() * 1e6) % (2**31 - 1)
        torch.manual_seed(seed_int)
        temperature = 0.7 + 0.3 * float(np.clip(np.std(seed_vector), 0, 1))

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=temperature,
                do_sample=True,
                top_p=0.92,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

class LeanVerifier:
    """Lean 4 形式化验证器"""

    def __init__(self, lean_path="lean"):
        self.lean_path = lean_path

    def verify(self, lean_code, timeout=30):
        import subprocess, tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lean", delete=False, encoding="utf-8") as f:
            f.write(lean_code)
            fname = f.name
        try:
            result = subprocess.run(
                [self.lean_path, fname],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore"
            )
            success = result.returncode == 0
            errors = []
            if not success:
                for line in result.stderr.split("\n"):
                    if "error" in line.lower():
                        if "unknown identifier" in line.lower(): errors.append({"type": "unknown_identifier"})
                        elif "type mismatch" in line.lower(): errors.append({"type": "type_mismatch"})
                        elif "unsolved goals" in line.lower(): errors.append({"type": "unsolved_goals"})
                        else: errors.append({"type": "other", "detail": line[:100]})
            return {"success": success, "errors": errors, "error_count": len(errors), "output": result.stdout[:300] if success else "", "error_output": result.stderr[:300] if not success else ""}
        except subprocess.TimeoutExpired:
            return {"success": False, "errors": [{"type": "timeout"}], "error_count": 1}
        finally:
            os.unlink(fname)

    def estimate_progress(self, lean_code):
        score = 0.0
        if "theorem" in lean_code: score += 0.2
        if "by" in lean_code or "begin" in lean_code: score += 0.1
        tactics = ["apply", "have", "cases", "induction", "rw", "simp", "refine", "intro", "exact", "calc", "ring", "linarith", "assumption"]
        score += min(0.4, sum(lean_code.count(t) for t in tactics) * 0.05)
        if "qed" in lean_code.lower() or "done" in lean_code.lower(): score += 0.3
        return min(1.0, score)

class LeanlessVerifier:
    def __init__(self):
        self.proof_keywords = ["proof", "theorem", "lemma", "assume", "therefore", "hence", "thus", "implies", "let", "then", "since", "qed", "□", "■"]
        self.lean_tactics = ["apply", "have", "cases", "induction", "rw", "simp", "refine", "intro", "exact", "calc", "ring", "linarith", "assumption", "refl", "trivial", "admit", "sorry"]
        self.math_symbols = ["=", "≠", "≤", "≥", "→", "←", "⇒", "⇐", "⇔", "∀", "∃", "∈", "∉", "⊆", "⊇", "∪", "∩", "ℕ", "ℤ", "ℚ", "ℝ", "∧", "∨"]

    def verify(self, text: str, timeout=None):
        core = self._extract_proof_body(text)
        errors = []
        
        has_proof_start = any(kw in core.lower() for kw in ["proof", "theorem", "by"])
        if not has_proof_start: errors.append({"type": "no_proof_start"})
        
        has_proof_end = any(kw in core.lower() for kw in ["qed", "□", "■", "therefore", "hence"])
        if not has_proof_end: errors.append({"type": "no_conclusion"})
        
        logical_markers = len(re.findall(r"(?:then|therefore|hence|thus|so|implies|follows)", core, re.I))
        if logical_markers < 1: errors.append({"type": "no_logical_chain"})
        
        declarations = len(re.findall(r"(?:let|suppose|assume|denote|define|set)\s+\w+", core, re.I))
        if declarations < 1: errors.append({"type": "no_variable_declaration"})
        
        if core.count("(") != core.count(")"): errors.append({"type": "parenthesis_mismatch"})
        if core.count("{") != core.count("}"): errors.append({"type": "brace_mismatch"})
        
        if any(kw in core.lower() for kw in ["sorry", "admit"]): errors.append({"type": "incomplete_admission"})
        
        return {"success": len(errors) == 0, "errors": errors, "error_count": len(errors), "output": core[:300] if not errors else "", "error_output": "; ".join(e["type"] for e in errors)}

    def estimate_progress(self, text: str):
        core = self._extract_proof_body(text)
        score = 0.0
        if any(kw in core.lower() for kw in ["proof", "theorem", "by", "let"]): score += 0.25
        tactic_count = sum(core.lower().count(t) for t in self.lean_tactics)
        score += min(0.3, tactic_count * 0.03)
        logical_count = len(re.findall(r"(?:then|therefore|hence|thus|so|implies)", core, re.I))
        score += min(0.2, logical_count * 0.04)
        if any(kw in core.lower() for kw in ["qed", "□", "■", "therefore", "hence"]): score += 0.15
        if len(core) > 200: score += 0.1
        return min(1.0, score)

    def _extract_proof_body(self, text: str):
        for marker in [":= by", ":= \nby", "Proof:", "-- Proof:", "/--"]:
            idx = text.find(marker)
            if idx != -1: return text[idx + len(marker):].strip()
        return text.strip()

class QuantumProofEvolver:
    def __init__(self, decoder, verifier, pop_size=100, seed_dim=1536):
        self.decoder = decoder
        self.verifier = verifier
        self.pop_size = pop_size
        self.seed_dim = seed_dim
        self.population = []
        self.best: Optional[ProofCandidate] = None
        self.generation = 0

    def initialize(self):
        self.population = [np.random.normal(0, 1, self.seed_dim) / np.linalg.norm(np.random.normal(0, 1, self.seed_dim)) for _ in range(self.pop_size)]
        self.best = None
        self.generation = 0

    def fitness(self, proof_code, verification, theorem):
        if verification["success"]: return 100.0 + max(0, 20 - len(proof_code) / 100)
        score = 30 - verification.get("error_count", 1) * 5
        for err in verification.get("errors", []):
            if err["type"] == "unsolved_goals": score += 15
            elif err["type"] == "type_mismatch": score += 5
        score += self.verifier.estimate_progress(proof_code) * 20
        return max(0, score)

    def quantum_crossover(self, p1, p2, mutation_rate=0.1):
        mask = np.random.rand(self.seed_dim) > 0.5
        child = np.where(mask, p1, p2) + np.random.normal(0, mutation_rate, self.seed_dim)
        return child / np.linalg.norm(child)

    def evaluate_population(self, theorem):
        candidates = []
        for i, seed in enumerate(self.population):
            proof = self.decoder.generate_proof(theorem, seed)
            verif = self.verifier.verify(proof)
            fit = self.fitness(proof, verif, theorem)
            candidates.append(ProofCandidate(seed.copy(), proof, fit, verif, self.generation))
            if (i + 1) % 20 == 0: print(f"  评估进度: {i+1}/{self.pop_size}")
        candidates.sort(key=lambda c: c.fitness, reverse=True)
        return candidates

    def evolve_generation(self, theorem):
        print(f"\n🌊 第 {self.generation} 代进化中...")
        candidates = self.evaluate_population(theorem)
        if self.best is None or candidates[0].fitness > self.best.fitness: self.best = candidates[0]
        elite_count = max(2, self.pop_size // 5)
        elites = candidates[:elite_count]
        new_pop = [e.seed.copy() for e in elites]
        while len(new_pop) < self.pop_size:
            p1, p2 = random.choice(elites[:5]).seed, random.choice(elites[:5]).seed
            new_pop.append(self.quantum_crossover(p1, p2))
        self.population = new_pop
        self.generation += 1
        avg = np.mean([c.fitness for c in candidates])
        print(f"  最佳: {candidates[0].fitness:.1f} | 平均: {avg:.1f} | 精英: {elite_count}")
        if candidates[0].verification_result["success"]: print(f"  🎯 发现有效证明！")
        return candidates[0].verification_result["success"]

    def run(self, theorem, max_generations=300):
        self.initialize()
        print(f"🚀 开始量子进化搜索\n   种群: {self.pop_size} | 最大代数: {max_generations}\n   目标: {theorem[:80]}...")
        for gen in range(max_generations):
            if self.evolve_generation(theorem):
                print(f"\n✨ 第 {gen} 代进化成功！")
                break
            if gen % 25 == 0 and self.best:
                print(f"\n📜 当前最佳证明片段 (Gen {gen}):\n{self.best.proof_code[:200]}")
        return self.best