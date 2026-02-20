import asyncio
from typing import List, Dict

class GlobalState:
    stats = {
        "transmissions": 0,
        "collisions": 0,
        "dropped_out_of_range": 0,
        "policy": "None"
    }
    nodes: Dict = {}
    logs: List[Dict] = []
    
    _queues: List[asyncio.Queue] = []
    
    @classmethod
    def get_state(cls):
        return {
            "type": "state_update",
            "stats": cls.stats,
            "nodes": cls.nodes,
            "logs": cls.logs[-100:]
        }
    
    @classmethod
    def register_client(cls) -> asyncio.Queue:
        q = asyncio.Queue()
        cls._queues.append(q)
        return q
        
    @classmethod
    def unregister_client(cls, q: asyncio.Queue):
        if q in cls._queues:
            cls._queues.remove(q)
            
    @classmethod
    def broadcast(cls):
        state = cls.get_state()
        for q in cls._queues:
            if q.qsize() < 10:
                q.put_nowait(state)

    @classmethod
    def log_event(cls, node_id: str, action: str, payload: str, congestion: str):
        entry = {"node_id": node_id, "action": action, "payload": payload, "congestion": congestion}
        cls.logs.append(entry)
        cls.broadcast()
        
    @classmethod
    def update_node(cls, node_id: str, x: float, y: float, inbox_size: int, stats: dict):
        cls.nodes[node_id] = {
            "id": node_id,
            "x": x,
            "y": y,
            "inbox_size": inbox_size,
            "stats": stats
        }
        cls.broadcast()
