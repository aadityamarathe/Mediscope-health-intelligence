def calculate_disease_severity(total_cases, occurrences):
    case_score = total_cases / 5000   # reduce impact
    occurrence_score = occurrences * 1.5

    score = case_score + occurrence_score

    if score < 5:
        return "low"
    elif score < 12:
        return "medium"
    else:
        return "high"


def calculate_outbreak_severity(case_count):
    if case_count > 8000:
        return "high"
    if case_count > 3000:
        return "medium"
    return "low"
