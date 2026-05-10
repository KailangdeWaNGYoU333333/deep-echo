"""
突变建议器：通过 DeepSeek API 对语法树提出改进建议
"""
import requests
import json
import random


class MutationAdvisor:
    """用 DeepSeek 模型充当突变顾问"""

    def __init__(self, api_key="your-api-key-here"):
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_key = api_key
        self.conversation_history = []  # 记录历史建议，避免重复

    def suggest_mutations(self, gene_tree, target, n=4):
        """
        给定当前最好的语法树和目标命题，返回 n 个突变建议
        每个建议是 (新子树, 理由) 的元组
        """
        prompt = self._build_prompt(gene_tree, target, n)

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "你是一个数学证明突变顾问。你会看到当前最好的证明语法树，请提出具体的、可操作的改进建议。每个建议必须包含新的子树代码。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 2000
                },
                timeout=30
            )

            result = response.json()
            suggestions = self._parse_response(result["choices"][0]["message"]["content"])

            # 避免重复建议
            unique = []
            for s in suggestions:
                if s not in self.conversation_history[-20:]:
                    unique.append(s)
                    self.conversation_history.append(s)

            return unique[:n]

        except Exception as e:
            print(f"   突变顾问调用失败: {e}")
            return []  # 失败时返回空，进化器会用随机突变兜底

    def _build_prompt(self, gene_tree, target, n):
        """构建给 DeepSeek 的提示"""
        return f"""
当前证明目标: {target}

当前最好的证明语法树（S-表达式格式）:
{repr(gene_tree)}

翻译为 Lean 代码后:
{gene_tree.to_lean(target)}

请提出 {n} 个具体的改进建议，每个建议必须:
1. 指出当前证明的问题
2. 给出修改后的新子树（也用 S-表达式格式，如 (I (Q x y) (P x y))）
3. 解释为什么这个修改更可能通过 Lean 编译器

格式:
问题1: <问题描述>
新子树1: <S-表达式>
理由1: <理由>

问题2: <问题描述>
新子树2: <S-表达式>
理由2: <理由>
"""

    def _parse_response(self, text):
        """从 DeepSeek 的回复中提取建议"""
        suggestions = []

        import re
        # 匹配 "新子树N: <S-表达式>"
        pattern = r"新子树\d+:\s*(\(.+?\))"
        matches = re.findall(pattern, text)

        # 也匹配 "理由N: <理由>"
        reasons = re.findall(r"理由\d+:\s*(.+)", text)

        for i, subtree_str in enumerate(matches):
            reason = reasons[i] if i < len(reasons) else "模型建议"
            suggestions.append((subtree_str, reason))

        return suggestions