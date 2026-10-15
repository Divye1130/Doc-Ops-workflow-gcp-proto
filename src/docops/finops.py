def estimate_cost(text_chars: int, classification_calls: int = 1) -> float:
    # Illustrative cost model only; not a Google price quote.
    doc_ai = 0.0015 + text_chars * 0.0000002
    vertex = 0.0008 * classification_calls + text_chars * 0.00000008
    run = 0.00015
    return round(doc_ai + vertex + run, 6)
