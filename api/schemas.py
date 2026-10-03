from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class FleetStatusResponse(BaseModel):
    data_class: str = "synthetic"
    total_tails: int
    mc_count: int
    pmc_count: int
    nmc_count: int
    current_mc_rate: float
    tail_states: Dict[str, str]

class ForecastResponse(BaseModel):
    data_class: str = "synthetic"
    mc_forecast: List[float]
    unfilled_sorties: List[int]

class WhatIfRequest(BaseModel):
    lever: Dict[str, Any]

class WhatIfResponse(BaseModel):
    data_class: str = "synthetic"
    latency_ms: float
    before_mc_rate: float
    after_mc_rate: float
    mc_forecast: List[float]
    unfilled_sorties: List[int]

class CannibalRequest(BaseModel):
    donor_tail: str
    recipient_tail: str
    comp_class: str

class CannibalResponse(BaseModel):
    data_class: str = "synthetic"
    approved: bool
    message: str
    details: Dict[str, Any]
