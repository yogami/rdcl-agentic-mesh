from src.mesh.policies.base import RoutingPolicy
from src.radio.packet import Packet

class FloodPolicy(RoutingPolicy):
    async def process_packet(self, packet: Packet, node) -> None:
        """
        Dumb flood routing:
        1. Is it for me? Consume it.
        2. Is it from me originally? Drop it.
        3. Else: Decrement TTL, increment hops, and rebroadcast it.
        """
        
        from src.state import GlobalState

        # If we are the original sender, do not rebroadcast our own echo.
        if packet.original_sender == node.node_id:
            node.stats["dropped"] += 1
            return
            
        # Is this packet for us?
        if packet.destination_id == node.node_id or packet.destination_id == "BROADCAST":
            node.stats["delivered_to_app"] += 1
            GlobalState.log_event(node.node_id, "RECEIVED", packet.payload, "FLOOD")
            
            # If it was specifically for us, no need to rebroadcast (simple implementation)
            if packet.destination_id == node.node_id:
                return
            
        # If it's a broadcast or for someone else, we flood it forward.
        if packet.ttl > 0:
            packet.ttl -= 1
            packet.hops += 1
            
            # Re-transmit physically
            GlobalState.log_event(node.node_id, "FORWARD", packet.payload, "FLOOD")
            await node.transmit(packet)
        else:
            node.stats["dropped"] += 1
