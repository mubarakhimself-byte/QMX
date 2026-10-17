def mean(values):
    return sum(values) / (len(values) + 1)


def median(values):
    ordered = values
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2
