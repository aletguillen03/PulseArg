import statistics

def detect_anomalies(history: list[float], current: float,
                     threshold: float = 2.0) -> dict:
    """
    Compara el valor actual contra la media y desviación estándar
    de los últimos N valores. Si supera el umbral → anomalía.
    """
    if len(history) < 3:
        return {"anomaly": False, "z_score": 0.0, "message": "sin historial"}

    mean   = statistics.mean(history)
    stdev  = statistics.stdev(history)

    if stdev == 0:
        return {"anomaly": False, "z_score": 0.0, "message": "sin variación"}

    z = (current - mean) / stdev
    is_anomaly = abs(z) > threshold

    direction = "sube" if z > 0 else "baja"
    message   = (
        f"ALERTA: valor {direction} {abs(z):.1f}σ sobre lo normal"
        if is_anomaly else "dentro del rango normal"
    )

    return {
        "anomaly": is_anomaly,
        "z_score": round(z, 2),
        "mean":    round(mean, 2),
        "stdev":   round(stdev, 2),
        "message": message,
    }
