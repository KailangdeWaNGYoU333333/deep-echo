"""
基因语法树定义 + 编码/解码
用于将数学命题表示为可进化的语法树
"""
from typing import List, Union
import random

class GeneNode:
    """基因语法树节点"""
    def __init__(self, op: str, args: List[Union['GeneNode', str, int]]):
        self.op = op
        self.args = args
        self._hash = None

    def __repr__(self):
        if self.op in "0123456789" or isinstance(self.op, int):
            return str(self.op)
        if self.op in "abcdefghijklmnopqrstuvwxyz" and len(self.op) == 1:
            return self.op
        return f"({self.op} {' '.join(repr(a) for a in self.args)})"

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(repr(self))
        return self._hash

    def __eq__(self, other):
        return repr(self) == repr(other) if isinstance(other, GeneNode) else False

    def to_lean(self, target="1 + 0 = 1"):
        """将语法树翻译为 Lean 4 代码"""
        body = self._to_lean_body()
        return f"example : {target} := by\n{body}"

    def _to_lean_body(self):
        op = self.op
        if op == "F":   # forall
            var, body = self.args[0], self.args[1]
            return f"  intro {var}\n{body._to_lean_body()}"
        elif op == "E": # exists
            return f"  refine Exists.intro ?_ ?_"
        elif op == "I": # implies
            prem, conc = self.args[0], self.args[1]
            return f"  intro h\n{conc._to_lean_body()}"
        elif op == "N": # and
            return f"  refine And.intro ?_ ?_"
        elif op == "O": # or
            return f"  left"
        elif op == "X": # not
            return f"  intro h\n  exfalso"
        elif op == "Q": # equal
            return f"  rfl"
        elif op == "P": # plus
            return f"  ring"
        elif op == "M": # multiply
            return f"  ring"
        elif op == "G": # greater
            return f"  linarith"
        elif op == "L": # less
            return f"  linarith"
        elif op == "Z": # prime
            return f"  exact Nat.prime_def"
        elif op == "A": # apply theorem
            return f"  apply {self.args[0]}"
        elif str(op) in "0123456789" or (isinstance(op, int) and op <= 9):
            return f"  rfl"
        else:
            return f"  rfl"


# ==================== 随机生成 + 变异 ====================

OPS = ["F", "E", "I", "N", "O", "X", "Q", "P", "M", "G", "L", "Z", "A"]
VARS = ["n", "m", "p", "q", "x", "y", "k"]
NUMS = ["0", "1", "2", "3"]

def random_gene(depth=4):
    """随机生成一个语法树，depth 控制最大深度"""
    if depth <= 1:
        return random.choice([
            GeneNode(random.choice(VARS), []),
            GeneNode(random.choice(NUMS), []),
        ])

    op = random.choice(OPS)
    if op == "F":
        var = random.choice(VARS)
        body = random_gene(depth - 1)
        return GeneNode("F", [var, body])
    elif op == "E":
        var = random.choice(VARS)
        body = random_gene(depth - 1)
        return GeneNode("E", [var, body])
    elif op in ("I", "N", "O"):
        left = random_gene(depth - 1)
        right = random_gene(depth - 1)
        return GeneNode(op, [left, right])
    elif op == "X":
        body = random_gene(depth - 1)
        return GeneNode("X", [body])
    elif op in ("Q", "G", "L"):
        left = random_gene(depth - 1)
        right = random_gene(depth - 1)
        return GeneNode(op, [left, right])
    elif op in ("P", "M"):
        left = random_gene(depth - 1)
        right = random_gene(depth - 1)
        return GeneNode(op, [left, right])
    elif op == "Z":
        return GeneNode("Z", [random.choice(VARS)])
    elif op == "A":
        return GeneNode("A", [f"T{random.randint(1,10):03d}"])
    else:
        return GeneNode(random.choice(NUMS), [])


def mutate_gene(node, rate=0.3, depth=4):
    """变异语法树：随机替换子树"""
    if not isinstance(node, GeneNode):
        # 如果是字符串或数字，直接返回或随机替换
        if random.random() < rate:
            return random_gene(depth)
        return node
    
    if random.random() < rate:
        return random_gene(depth)
    
    if not node.args:
        return node
    
    new_args = []
    for a in node.args:
        if random.random() < rate:
            new_args.append(random_gene(depth))
        else:
            new_args.append(mutate_gene(a, rate, depth))
    
    return GeneNode(node.op, new_args)


def crossover_genes(n1, n2):
    """交叉两颗语法树：随机交换子树"""
    if not isinstance(n1, GeneNode) or not isinstance(n2, GeneNode):
        return n2 if random.random() < 0.5 else n1
    
    if random.random() < 0.5:
        return n2
    
    if not n1.args or not n2.args:
        return n1
    
    idx1 = random.randint(0, len(n1.args) - 1)
    idx2 = random.randint(0, len(n2.args) - 1)
    new_args = list(n1.args)
    new_args[idx1] = n2.args[idx2]
    return GeneNode(n1.op, new_args)