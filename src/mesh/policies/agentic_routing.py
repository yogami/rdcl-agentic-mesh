import os
from openai import AsyncOpenAI
from typing import Dict
from src.mesh.policies.base import RoutingPolicy
from src.radio.packet import Packet

# Extremely simple local cache to avoid hitting OpenAI 10,000 times for the same type of packet in the simulation
_CACHE: Dict[str, str] = {}

class AgenticRoutingPolicy(RoutingPolicy):
    def __init__(self):
        # Mocked for demo purposes; no real client needed.
        self.client = None
        
    async def process_packet(self, packet: Packet, node) -> None:
        """
        Cognitive routing: The LLM decides whether to DROP or FORWARD 
        based on payload semantics and current channel congestion.
        """
        if packet.original_sender == node.node_id:
            node.stats["dropped"] += 1
            return
            
        if packet.destination_id == node.node_id or packet.destination_id == "BROADCAST":
            node.stats["delivered_to_app"] += 1
            if packet.destination_id == node.node_id:
                return
                
        if packet.ttl <= 0:
            node.stats["dropped"] += 1
            return

        # Determine Congestion State
        qsize = node.inbox.qsize()
        congestion = "LOW"
        if qsize > 10:
            congestion = "MEDIUM"
        if qsize > 30:
            congestion = "HIGH"

        # The Cache Key
        cache_key = f"{packet.payload}::{congestion}"
        
        if cache_key in _CACHE:
            decision = _CACHE[cache_key]
        else:
            decision = await self._query_llm(packet.payload, congestion)
            _CACHE[cache_key] = decision
            
        # Execute Decision
        from src.state import GlobalState
        if decision == "FORWARD":
            packet.ttl -= 1
            packet.hops += 1
            await node.transmit(packet)
            GlobalState.log_event(node.node_id, "FORWARD", packet.payload, congestion)
        else:
            node.stats["dropped"] += 1
            GlobalState.log_event(node.node_id, "DROP", packet.payload, congestion)

    async def _query_llm(self, payload: str, congestion: str) -> str:
        # Mock cognitive reasoning without requiring API KEY in environment
        # Real implementation would call Anthropic/OpenAI here
        
        # Rule 1: Always forward critical
        if "SOS" in payload or "CRITICAL" in payload or "URGENT" in payload:
            return "FORWARD"
            
        # Rule 2: Routine telemetry depends on congestion
        if "Telemetry" in payload or "Ping" in payload:
            if congestion == "LOW":
                return "FORWARD"
            return "DROP"
            
        # Rule 3: Default behavior
        return "FORWARD"
