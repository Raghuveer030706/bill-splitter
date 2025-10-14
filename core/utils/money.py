from __future__ import annotations

# Centralized epsilon & rounding helpers
EPS = 1e-6

def qround(x: float, ndigits: int = 2) -> float:
    """
    Quantized round for currency; keeps small negative zeros out.
    """
    v = round(float(x) + 0.0, ndigits)
    return 0.0 if abs(v) < EPS else v

def fmt(amount: float, symbol: str = "₹") -> str:
    """
    Format currency consistently.
    """
    return f"{symbol} {qround(amount):,.2f}"
