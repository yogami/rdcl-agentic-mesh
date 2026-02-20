import asyncio
from typing import Optional, Set
from src.radio.hal import SimulatedRadioEnvironment
from src.radio.packet import Packet
from src.mesh.policies.base import RoutingPolicy

class Node:
    def __init__(self, node_id: str, env: SimulatedRadioEnvironment, x: float, y: float, policy: RoutingPolicy):
        self.node_id = node_id
        self.env = env
        self.policy = policy
        self.x = x
        self.y = y
        self.stats = {"received": 0, "sent": 0, "dropped": 0, "delivered_to_app": 0}
        
        # Registration with Physical Environment (HAL)
        self.inbox = self.env.register_node(node_id, x, y)
        
        # Duplicate packet detection (standard mesh technique)
        self.seen_packets: Set[str] = set()
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the node's main listening loop."""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        
    async def stop(self):
        """Stop the node's loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            
    async def _run_loop(self):
        while self._running:
            try:
                # Wait for a packet from the physical layer (HAL)
                packet: Packet = await self.inbox.get()
                self.stats["received"] += 1
                
                # Deduplication: Ignore packets we've already processed
                if packet.id in self.seen_packets:
                    self.inbox.task_done()
                    continue
                    
                self.seen_packets.add(packet.id)
                self.inbox.task_done()
                
                # Pass the packet to the routing policy engine
                await self.policy.process_packet(packet, self)
                
            except asyncio.CancelledError:
                break
            
            # Update web dashboard
            from src.state import GlobalState
            GlobalState.update_node(self.node_id, self.x, self.y, self.inbox.qsize(), self.stats)
                
    async def transmit(self, packet: Packet):
        """Send a packet to the HAL for physical broadcast."""
        # Simulated radio processing delay (Time-On-Air) before the next action
        await asyncio.sleep(0.05)
        self.stats["sent"] += 1
        await self.env.broadcast(self.node_id, packet)
