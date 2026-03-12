# We don't let AI hallucinate numbers blindly.

def calculate_cost(duration_months, expected_users):
    # Base development cost
    base_dev_cost = 20000 * duration_months

    # Infrastructure cost based on users
    infra_cost = expected_users * 0.5

    # Contingency buffer
    contingency = base_dev_cost * 0.1

    # Total cost
    total = base_dev_cost + infra_cost + contingency

    return {
        "development_cost": base_dev_cost,
        "infrastructure_cost": infra_cost,
        "contingency": contingency,
        "total_estimated_cost": total
    }
