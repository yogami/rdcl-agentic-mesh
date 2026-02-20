from pydantic import BaseModel, Field
import uuid
from typing import Optional

class Packet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    destination_id: str # "BROADCAST" or a specific node ID
    payload: str
    ttl: int = 3 # Hop limit
    rssi: Optional[float] = None
    snr: Optional[float] = None
    
    # Internal tracking for simulation analysis (not transmitted physically)
    original_sender: str
    hops: int = 0
