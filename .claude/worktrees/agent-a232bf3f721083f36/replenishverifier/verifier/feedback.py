FEEDBACK_TEMPLATES = {
    "inventory_balance": "你的模型缺少或仅弱支持库存平衡约束。应加入类似 I[t] = I[t-1] + Q[t] - demand[t] 的约束；若允许缺货，可使用 I[t] - B[t] = I[t-1] - B[t-1] + Q[t] - demand[t]。仅有 inventory_balance 名称不能证明代数关系正确。",
    "order_variable": "你的模型缺少订货决策变量。应加入非负订货变量 Q[t] 或 Q[i,t]。",
    "inventory_variable": "你的模型缺少库存状态变量。应加入非负库存变量 I[t] 或 I[i,t]。",
    "shortage_variable": "题目允许缺货或包含缺货惩罚，但你的模型没有可用的缺货变量。应加入 B[t] 或 B[i,t]，并让其参与目标函数或库存/需求约束。",
    "capacity_constraint": "题目包含容量限制，但你的模型没有足够证据支持容量约束。应加入类似 sum_i volume[i] * I[i,t] <= capacity 的不等式约束。",
    "binary_order_variable": "题目包含固定订货成本，但你的模型没有 binary 订货触发变量 Y[t]。应加入 Y[t] ∈ {0,1}。",
    "big_m_constraint": "你的模型有固定订货成本或订货触发逻辑，但没有足够证据支持 Big-M 连接约束。应加入 Q[t] <= M * Y[t]，并检查 M 的数值合理性。",
    "lead_time": "题目包含提前期 lead time，但你的模型没有体现提前期。库存平衡中应使用延迟到货的订货量，例如 Q[t-L]。",
    "holding_cost": "你的目标函数缺少持有成本项。应加入 holding_cost * I[t]。",
    "shortage_cost": "你的目标函数缺少缺货惩罚项。应加入 shortage_cost * B[t]。",
    "fixed_order_cost": "你的目标函数缺少固定订货成本项。应加入 fixed_order_cost * Y[t]；仅声明 Y 变量不足以证明 fixed cost 存在。",
}


def _certificates_by_rule(check_result):
    return {cert.get("rule_name"): cert for cert in check_result.get("certificates", [])}


def generate_feedback(check_result):
    if hasattr(check_result, "to_dict"):
        check_result = check_result.to_dict()

    missing = check_result.get("missing", [])
    if not missing:
        return "结构验证通过：模型包含题目所需的关键库存补货结构。"

    certs = _certificates_by_rule(check_result)
    lines = ["结构验证发现以下问题："]
    for key in missing:
        cert = certs.get(key, {})
        score = cert.get("score")
        evidence_strength = cert.get("evidence_strength", "none")
        prefix = f"- [{key}] evidence_strength={evidence_strength}"
        if score is not None:
            prefix += f", rule_score={float(score):.3f}"
        lines.append(f"{prefix}: {FEEDBACK_TEMPLATES.get(key, '缺少结构：' + key)}")
        if cert.get("repair_hint"):
            lines.append(f"  Repair hint: {cert['repair_hint']}")
        if cert.get("index_consistency", {}).get("warnings"):
            lines.append(f"  Index warnings: {cert['index_consistency']['warnings']}")
        if cert.get("magnitude_check", {}).get("warning"):
            lines.append(f"  Magnitude warning: {cert['magnitude_check']['warning']}")

    score = check_result.get("structure_score")
    if score is not None:
        lines.append(f"当前结构完整性分数为 {score:.3f}。请优先修复上述低证据强度结构。")

    return "\n".join(lines)
