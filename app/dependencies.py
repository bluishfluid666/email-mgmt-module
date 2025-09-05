from fastapi import HTTPException
from app.graph_service import GraphService

# Global Graph service instance
graph_service: GraphService = None

def set_graph_service(service: GraphService):
    """Set the global graph service instance"""
    global graph_service
    graph_service = service

def get_graph_service() -> GraphService:
    """Dependency to get the global graph service instance"""
    if graph_service is None:
        raise HTTPException(status_code=500, detail="Graph service not initialized")
    return graph_service
