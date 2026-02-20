from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from src.radio.packet import Packet

if TYPE_CHECKING:
    from src.mesh.node import Node

class RoutingPolicy(ABC):
    @abstractmethod
    async def process_packet(self, packet: Packet, node: 'Node') -> None:
        """
        Process an incoming packet.
        The policy decides whether to drop it, forward it, or consume it.
        """
        pass
