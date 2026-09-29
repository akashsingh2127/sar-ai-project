import pandas as pd
import networkx as nx
from typing import Dict, List, Any

class NetworkAnalyzer:
    """
    Lightweight transaction relationship analysis representing:
    Customer -> Account -> Transaction -> Counterparty
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        
    def build_graph(self, df: pd.DataFrame) -> None:
        """
        Build a directed graph from transactions.
        Nodes: Send/Receive Entities.
        Edges: Transactions with amounts.
        """
        self.graph.clear()
        if df.empty or 'sender' not in df.columns or 'receiver' not in df.columns:
            return
            
        for _, row in df.iterrows():
            sender = row.get('sender')
            receiver = row.get('receiver')
            amount = row.get('amount', 0.0)
            txn_id = row.get('transaction_id', 'unknown')
            
            if pd.notnull(sender) and pd.notnull(receiver):
                self.graph.add_node(sender, type='entity')
                self.graph.add_node(receiver, type='entity')
                self.graph.add_edge(sender, receiver, transaction_id=txn_id, amount=amount)

    def detect_circular_patterns(self) -> List[List[str]]:
        """
        Detects simple circular flow patterns (cycles in the directed graph).
        Returns list of cycles (list of nodes).
        """
        if self.graph.number_of_nodes() == 0:
            return []
        
        try:
            return list(nx.simple_cycles(self.graph))
        except nx.NetworkXNoCycle:
            return []
            
    def analyze_entity(self, entity_id: str) -> Dict[str, Any]:
        """
        Extract network intelligence for a specific entity.
        """
        if entity_id not in self.graph:
            return {
                "in_degree": 0,
                "out_degree": 0,
                "unique_counterparties": 0,
                "is_hub": False
            }
            
        in_deg = self.graph.in_degree(entity_id)
        out_deg = self.graph.out_degree(entity_id)
        
        counterparties = set(self.graph.successors(entity_id)).union(set(self.graph.predecessors(entity_id)))
        is_hub = len(counterparties) > 5
        
        return {
            "in_degree": in_deg,
            "out_degree": out_deg,
            "unique_counterparties": len(counterparties),
            "is_hub": is_hub
        }
