from pprint import pprint
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.models.models import CollectionInfo

def create_qd_collection(client_loc: str, coll_name: str, vector_size: int, distance: str = "COSINE") -> QdrantClient:
    """
    Create a Qdrant collection with the specified name and vector size.
    
    Args:
        client_loc (str): The location of the Qdrant client.
        coll_name (str): The name of the collection to create.
        vector_size (int): The size of the vectors in the collection.
        distance (str): The distance metric to use. Default is "COSINE".
        
    Returns:
        QdrantClient: The Qdrant client connected to the specified collection.
    """
    qd_client = QdrantClient(url=client_loc)
    qd_client.recreate_collection(
        collection_name=coll_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance[distance]),
    )
    return qd_client

def insert_qd_collection(qd_client: QdrantClient, coll_name: str, data: dict) -> None:
    """
    Insert points into the specified Qdrant collection.
    
    Args:
        qd_client (QdrantClient): The Qdrant client connected to the collection.
        coll_name (str): The name of the collection to insert points into.
        data (dict): The data to insert into the collection. Should contain 'vectors', and 'payload' keys.
    """
    operation_info = qd_client.upsert(
        collection_name=coll_name,
        points=[PointStruct(id=i, vector=vec, payload=payload) for i, (vec, payload) in enumerate(zip(data['vectors'], data['payload']))],
    )
    
    print(f"Upserted {len(data['vectors'])} points into collection '{coll_name}'")
    print(f"Operation info: {operation_info}")
    return operation_info.status

def search_qd_collection(client_loc: str, coll_name: str, query_vector: list[float], limit: int = 5) -> dict:
    """
    Search for similar points in the specified Qdrant collection.
    
    Args:
        client_loc (str): The location of the Qdrant client.
        coll_name (str): The name of the collection to search in.
        query_vector (list[float]): The vector to search for similar points.
        limit (int): The maximum number of results to return. Default is 5.
        
    Returns:
        dict: The search results containing the IDs and distances of the nearest points.
    """
    qd_client = QdrantClient(url=client_loc)
    search_result = qd_client.query_points(
        collection_name=coll_name,
        query_vector=query_vector,
        with_payload=True,
        limit=limit,
    ).points
    
    if not search_result:
        print("No results found.")
        return {}
    
    results = {
        "ids": [point.id for point in search_result],
        "distances": [point.distance for point in search_result],
        "payloads": [point.payload for point in search_result],
    }
    
    print(f"Search results:")
    pprint(results)
    return results

def get_collection_info(client_loc: str, coll_name: str) -> CollectionInfo:
    """
    Get information about the specified Qdrant collection.
    
    Args:
        client_loc (str): The location of the Qdrant client.
        coll_name (str): The name of the collection to get information about.
        
    Returns:
        dict: Information about the collection.
    """
    qd_client = QdrantClient(url=client_loc)
    collection_info = qd_client.get_collection(collection_name=coll_name)
    
    print(f"Collection info for '{coll_name}':")
    pprint(collection_info)
    return collection_info