import numpy as np

def generate_health_curve(num_cycles: int, is_infant_mortality: bool = False, is_no_fault: bool = False, rng: np.random.Generator = None) -> np.ndarray:
    if rng is None:
        rng = np.random.default_rng()
    
    if is_no_fault:
        # Healthy component throughout
        return np.ones(num_cycles)
    
    if is_infant_mortality:
        # Early failure mode
        a = rng.uniform(0.05, 0.1)
        b = rng.uniform(0.03, 0.06)
    else:
        # Normal degradation curve
        a = rng.uniform(0.001, 0.005)
        b = rng.uniform(0.015, 0.025)
    
    t = np.arange(num_cycles)
    health = 1.0 - a * np.exp(b * t)
    health = np.clip(health, 0.0, 1.0)
    return health

def generate_sensors_for_health(health_curve: np.ndarray, rng: np.random.Generator = None) -> tuple[np.ndarray, np.ndarray]:
    if rng is None:
        rng = np.random.default_rng()
    
    num_cycles = len(health_curve)
    
    # 3 operating settings
    op_settings = np.zeros((num_cycles, 3))
    for i in range(num_cycles):
        setting_idx = rng.choice([0, 1, 2])
        if setting_idx == 0:
            op_settings[i] = [0.0, 0.0, 100.0]
        elif setting_idx == 1:
            op_settings[i] = [10.0, 0.8, 100.0]
        else:
            op_settings[i] = [20.0, 0.84, 100.0]
            
    # 12 sensors
    sensors = np.zeros((num_cycles, 12))
    base_degradation = 1.0 - health_curve  # 0 to 1 as it degrades
    
    for s in range(12):
        direction = 1.0 if s % 2 == 0 else -1.0
        scale = 10.0 + s * 5.0
        noise = rng.normal(0, 0.5, size=num_cycles)
        op_impact = op_settings[:, 0] * 0.1
        sensors[:, s] = 500.0 + direction * base_degradation * scale + noise + op_impact
        
    return op_settings, sensors
