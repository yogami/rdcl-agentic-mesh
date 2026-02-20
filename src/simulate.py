import asyncio
import argparse
import random
from dotenv import load_dotenv

from src.radio.hal import SimulatedRadioEnvironment
from src.radio.packet import Packet
from src.mesh.node import Node
from src.mesh.policies.flood_routing import FloodPolicy
from src.mesh.policies.agentic_routing import AgenticRoutingPolicy

load_dotenv()

async def simulate(policy_name: str, num_nodes: int, duration_sec: int):
    print(f"Starting simulation with {policy_name} policy and {num_nodes} nodes.")
    env = SimulatedRadioEnvironment(max_range_meters=800)
    
    # Initialize Policy
    if policy_name == "agentic":
        policy = AgenticRoutingPolicy()
    else:
        policy = FloodPolicy()
        
    nodes = []
    
    # Create nodes in a grid / random cluster
    for i in range(num_nodes):
        x = random.uniform(0, 1500)
        y = random.uniform(0, 1500)
        node = Node(f"Node-{i}", env, x, y, policy)
        nodes.append(node)
        
    # Start all nodes
    for n in nodes:
        await n.start()
        
    print("Network initialized. Injecting traffic...")
    
    # Inject test traffic
    critical_messages = [
        "SOS: Need medical evac at coord 45.1, 9.2",
        "CRITICAL: Structural failure detected on bridge alpha",
        "URGENT: Riot police deploying on Main St"
    ]
    
    noise_messages = [
        "Telemetry: Temp 22C, Hum 45%",
        "Ping: ACK 33",
        "Telemetry: Battery 88%",
        "Telemetry: Heartbeat OK"
    ]
    
    async def traffic_generator():
        for _ in range(duration_sec * 5): # 5 messages per second across network
            sender = random.choice(nodes)
            
            # 80% noise, 20% critical (typical IoT/tactical split)
            if random.random() < 0.2:
                payload = random.choice(critical_messages)
            else:
                payload = random.choice(noise_messages)
                
            packet = Packet(
                sender_id=sender.node_id,
                original_sender=sender.node_id,
                destination_id="BROADCAST",
                payload=payload,
                ttl=5 # Allow multi-hop
            )
            
            await sender.transmit(packet)
            
            # Sync environment stats with dashboard
            from src.state import GlobalState
            GlobalState.stats = env.stats
            GlobalState.stats["policy"] = policy_name
            GlobalState.broadcast()
            
            await asyncio.sleep(0.2)
            
    try:
        # Run traffic generator for 'duration_sec' seconds
        await asyncio.wait_for(traffic_generator(), timeout=duration_sec)
    except asyncio.TimeoutError:
        pass
        
    # Let network settle
    await asyncio.sleep(2)
    
    print("\n--- SIMULATION COMPLETE ---")
    print("HAL Physical Stats:", env.stats)
    
    total_received = sum(n.stats["received"] for n in nodes)
    total_sent = sum(n.stats["sent"] for n in nodes)
    total_delivered = sum(n.stats["delivered_to_app"] for n in nodes)
    total_dropped = sum(n.stats["dropped"] for n in nodes)
    
    print(f"Total RF Transmissions (Sent): {total_sent}")
    print(f"Total Packets Processed by Nodes: {total_received}")
    print(f"Packets Delivered to Application Layers: {total_delivered}")
    print(f"Packets Dropped by Policy: {total_dropped}")
    
    # Stop nodes
    for n in nodes:
        await n.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic Mesh Sim")
    parser.add_argument("--policy", choices=["flood", "agentic"], default="flood")
    parser.add_argument("--nodes", type=int, default=15)
    parser.add_argument("--duration", type=int, default=10)
    args = parser.parse_args()
    
    asyncio.run(simulate(args.policy, args.nodes, args.duration))
