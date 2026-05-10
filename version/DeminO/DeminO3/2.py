import subprocess
import tempfile
import os
import re

class MathematicalReasoner:
    def __init__(self, kb):
        self.kb = kb

    def convert_to_tptp(self, statement, use_llm=True):
        if use_llm:
            try:
                import ollama
                prompt = f"""Convert the following mathematical statement into TPTP first-order logic format.
Rules:
- Use fof(name, type, formula).
- type can be 'conjecture', 'axiom', or 'theorem'.
- For universal quantification use ! [X] : ...
- For existential quantification use ? [X] : ...

Statement: {statement}

TPTP:"""
                response = ollama.generate(model='deepseek-math:7b', prompt=prompt)
                return response['response'].strip()
            except:
                pass
        return f"fof(statement, conjecture, true)."

    def check_implication(self, premise_tptp, conjecture_tptp, timeout=10):
        content = premise_tptp + "\n" + conjecture_tptp
        with tempfile.NamedTemporaryFile(mode='w', suffix='.p', delete=False) as f:
            f.write(content)
            fname = f.name
        
        try:
            result = subprocess.run(['eprover', '-s', '--cpu-limit=' + str(timeout), fname], capture_output=True, text=True, timeout=timeout + 5)
            output = result.stdout + result.stderr
            if "Theorem" in output or "Unsatisfiable" in output: return True
            if "Satisfiable" in output or "CounterSatisfiable" in output: return False
            return None
        except:
            return None
        finally:
            os.unlink(fname)

    def detect_relationship(self, statement_a, statement_b):
        tptp_a = self.convert_to_tptp(statement_a)
        tptp_b = self.convert_to_tptp(statement_b)
        
        a_implies_b = self.check_implication(tptp_a, tptp_b)
        b_implies_a = self.check_implication(tptp_b, tptp_a)
        
        if a_implies_b and b_implies_a: return "equivalent"
        elif a_implies_b: return "a_implies_b"
        elif b_implies_a: return "b_implies_a"
        elif a_implies_b is False and b_implies_a is False: return "independent"
        else: return "unknown"

    def estimate_difficulty(self, statement):
        try:
            import ollama
            response = ollama.generate(model='deepseek-math:7b', prompt=f"""Rate the difficulty of proving this mathematical statement on a scale of 1-10.
Reference scale:
1-3: Undergraduate exercise
4-6: Graduate level or IMO problem
7-8: Major theorem (e.g., Prime Number Theorem)
9: Fields Medal level
10: Millennium Prize problem

Statement: {statement}

Difficulty (1-10):""")
            numbers = re.findall(r'\d+', response['response'])
            if numbers: return float(numbers[0])
        except:
            pass
        return 5.0

    def classify_domain(self, statement):
        similar = self.kb.search(statement, top_k=10)
        domains = {}
        for t in similar:
            d = t.get('domain', 'unknown')
            domains[d] = domains.get(d, 0) + 1
        return max(domains, key=domains.get) if domains else "unknown"

    def analyze_statement(self, statement):
        domain = self.classify_domain(statement)
        difficulty = self.estimate_difficulty(statement)
        similar = self.kb.search(statement, top_k=10)
        
        relations = []
        is_known = False
        equivalent_to = None
        
        for t in similar:
            rel = self.detect_relationship(statement, t['statement'])
            relations.append({"theorem": t['name'], "relationship": rel, "distance": t['distance']})
            if rel == "equivalent":
                is_known = True
                equivalent_to = t['name']
        
        return {
            "statement": statement,
            "domain": domain,
            "difficulty": difficulty,
            "is_known": is_known,
            "equivalent_to": equivalent_to,
            "related_theorems": similar,
            "logical_relations": relations
        }