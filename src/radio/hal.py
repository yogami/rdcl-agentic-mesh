import asyncio
import math
from typing import Dict, Tuple, List
from .packet import Packet

class SimulatedRadioEnvironment:
    def __init__(self, max_range_meters: float = 1000.0, base_tx_power: float = 14.0):
        self.nodes: Dict[str, Tuple[float, float]] = {} # node_id -> (x, y)
        self.inboxes: Dict[str, asyncio.Queue] = {}
        self.max_range = max_range_meters
        self.base_tx_power = base_tx_power # dBm
        self.stats = {"transmissions": 0, "collisions": 0, "dropped_out_of_range": 0}

    def register_node(self, node_id: str, x: float, y: float) -> asyncio.Queue:
        """Register a node in the physical space and return its receive queue."""
        self.nodes[node_id] = (x, y)
        self.inboxes[node_id] = asyncio.Queue()
        return self.inboxes[node_id]
        
    def _calculate_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
    def _calculate_rssi(self, distance: float) -> float:
        """Simple Free Space Path Loss (FSPL) approximation"""
        if distance < 1:
            return self.base_tx_power
        # L = 20 * log10(d) + 20 * log10(f) + 32.44
        # Assuming 868MHz
        path_loss = 20 * math.log10(distance) + 20 * math.log10(868) - 27.55
        rssi = self.base_tx_power - path_loss
        return rssi

    async def broadcast(self, sender_id: str, packet: Packet):
        """Simulate a radio broadcast from sender_id to all nodes in range."""
        self.stats["transmissions"] += 1
        if sender_id not in self.nodes:
            return

        sender_pos = self.nodes[sender_id]
        
        # In a real ALOHA network, we'd calculate collisions based on overlapping transmit times.
        # For this demo, we assume perfect reception if within range, but we will model 
        # congestion at the node queue level.
        
        for recipient_id, recipient_pos in self.nodes.items():
            if recipient_id == sender_id:
                continue
                
            distance = self._calculate_distance(sender_pos, recipient_pos)
            if distance <= self.max_range:
                # Add physical layer stats to the packet instance for this specific hop
                received_packet = packet.model_copy(deep=True)
                received_packet.rssi = self._calculate_rssi(distance)
                # Introduce slight randomness to SNR
                received_packet.snr = max(-20.0, min(10.0, 10.0 - (distance / self.max_range) * 20.0))
                
                # Check for queue overflow (simulating node buffer congestion)
                if self.inboxes[recipient_id].qsize() > 50:
                    self.stats["collisions"] += 1 # Treating overflow as collision for simplicity
                else:
                    await self.inboxes[recipient_id].put(received_packet)
            else:
                self.stats["dropped_out_of_range"] += 1
