import ast
from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError

from .models import CalculationRule, CalculationRuleDependency


class _SafeDecimalEvaluator(ast.NodeVisitor):
    def __init__(self, values):
        self.values = values

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValidationError("Calculation expressions only support numeric constants.")
        return Decimal(str(node.value))

    def visit_Name(self, node):
        if node.id not in self.values:
            raise ValidationError(f"Missing calculation input: {node.id}")
        try:
            return Decimal(str(self.values[node.id]))
        except (TypeError, ValueError):
            raise ValidationError(f"Calculation input must be numeric: {node.id}")

    def visit_UnaryOp(self, node):
        value = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return value
        raise ValidationError("Unsupported unary operator in calculation expression.")

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ValidationError("Calculation expression cannot divide by zero.")
            return left / right
        if isinstance(node.op, ast.Pow):
            if right != right.to_integral_value():
                raise ValidationError("Calculation powers must use an integer exponent.")
            return left ** int(right)
        raise ValidationError("Unsupported binary operator in calculation expression.")

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name) or node.func.id not in {"abs", "min", "max"}:
            raise ValidationError("Only abs, min, and max are allowed in calculations.")
        if node.keywords:
            raise ValidationError("Calculation functions do not accept keyword arguments.")
        values = [self.visit(argument) for argument in node.args]
        if node.func.id == "abs" and len(values) == 1:
            return abs(values[0])
        if node.func.id == "min" and values:
            return min(values)
        if node.func.id == "max" and values:
            return max(values)
        raise ValidationError("Calculation function arguments are invalid.")

    def generic_visit(self, node):
        raise ValidationError(
            f"Unsupported syntax in calculation expression: {node.__class__.__name__}"
        )


def evaluate_calculation_rule(rule, values):
    """Evaluate one rule without executing arbitrary Python code."""
    input_keys = rule.input_keys or []
    if not isinstance(input_keys, list) or any(not isinstance(key, str) for key in input_keys):
        raise ValidationError("Calculation rule input_keys must be a list of names.")
    missing_keys = [key for key in input_keys if key not in values]
    if missing_keys:
        raise ValidationError(f"Missing calculation inputs: {', '.join(missing_keys)}")
    try:
        tree = ast.parse(rule.expression, mode="eval")
    except SyntaxError as exc:
        raise ValidationError("Calculation expression is not valid.") from exc
    result = _SafeDecimalEvaluator(values).visit(tree)
    return result.quantize(Decimal("0.000001"))


def _rule_order(rules):
    rules = list(rules)
    rule_by_id = {rule.id: rule for rule in rules}
    graph = defaultdict(set)
    for rule_id, depends_on_id in CalculationRuleDependency.objects.filter(
        rule_id__in=rule_by_id
    ).values_list("rule_id", "depends_on_id"):
        if depends_on_id in rule_by_id:
            graph[rule_id].add(depends_on_id)

    ordered = []
    visiting = set()
    visited = set()

    def visit(rule_id):
        if rule_id in visiting:
            raise ValidationError("Calculation rule dependency cycle detected.")
        if rule_id in visited:
            return
        visiting.add(rule_id)
        for dependency_id in graph[rule_id]:
            visit(dependency_id)
        visiting.remove(rule_id)
        visited.add(rule_id)
        ordered.append(rule_by_id[rule_id])

    for rule in sorted(rules, key=lambda item: (item.priority, item.id)):
        visit(rule.id)
    return ordered


def evaluate_calculation_rules(rules, values):
    """Evaluate rules in dependency order and return outputs by rule code."""
    outputs = {}
    for rule in _rule_order(rules):
        rule_values = {**values, **outputs}
        outputs[rule.code] = evaluate_calculation_rule(rule, rule_values)
    return outputs
