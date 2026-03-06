import os
from typing import List, Dict, Any, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models
import psycopg2
from psycopg2 import sql
from minio import Minio
from minio.error import S3Error

class QdrantConnector:
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)

    def create_user_collection(self, user_id: str, vector_size: int = 1536):
        collection_name = f"user_{user_id}_vectors"
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
            print(f"Collection {collection_name} created.")
        else:
            print(f"Collection {collection_name} already exists.")

    def push(self, user_id: str, vectors: List[List[float]], payloads: List[Dict[str, Any]], ids: Optional[List[Union[str, int]]] = None):
        collection_name = f"user_{user_id}_vectors"
        self.client.upsert(
            collection_name=collection_name,
            points=models.Batch(
                ids=ids,
                vectors=vectors,
                payloads=payloads
            )
        )
        print(f"Data pushed to {collection_name}.")

    def pull(self, user_id: str, query_vector: List[float], top_k: int = 5) -> List[models.ScoredPoint]:
        collection_name = f"user_{user_id}_vectors"
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k
        )

    def delete(self, user_id: str, points_selector: models.Filter):
        collection_name = f"user_{user_id}_vectors"
        self.client.delete(
            collection_name=collection_name,
            points_selector=points_selector
        )
        print(f"Points deleted from {collection_name}.")

    def update(self, user_id: str, points: models.Batch):
        # Qdrant upsert handles update as well
        collection_name = f"user_{user_id}_vectors"
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"Points updated in {collection_name}.")
    
    # New methods for text and image collections
    def create_text_collection(self, user_id: str, vector_size: int = 384):
        """Create collection for text embeddings."""
        collection_name = f"{user_id}_text_embeddings"
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
            print(f"Text collection {collection_name} created.")
        else:
            print(f"Text collection {collection_name} already exists.")
        return collection_name
    
    def create_image_collection(self, user_id: str, vector_size: int = 512):
        """Create collection for image embeddings."""
        collection_name = f"{user_id}_image_embeddings"
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
            print(f"Image collection {collection_name} created.")
        else:
            print(f"Image collection {collection_name} already exists.")
        return collection_name
    
    def push_text_embeddings(self, user_id: str, vectors: List[List[float]], payloads: List[Dict[str, Any]], ids: Optional[List[Union[str, int]]] = None):
        """Push text embeddings to text collection."""
        collection_name = f"{user_id}_text_embeddings"
        
        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
        
        self.client.upsert(
            collection_name=collection_name,
            points=models.Batch(
                ids=ids,
                vectors=vectors,
                payloads=payloads
            )
        )
        print(f"Pushed {len(vectors)} text embeddings to {collection_name}.")
        return ids
    
    def push_image_embeddings(self, user_id: str, vectors: List[List[float]], payloads: List[Dict[str, Any]], ids: Optional[List[Union[str, int]]] = None):
        """Push image embeddings to image collection."""
        collection_name = f"{user_id}_image_embeddings"
        
        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
        
        self.client.upsert(
            collection_name=collection_name,
            points=models.Batch(
                ids=ids,
                vectors=vectors,
                payloads=payloads
            )
        )
        print(f"Pushed {len(vectors)} image embeddings to {collection_name}.")
        return ids
    
    def search_text(self, user_id: str, query_vector: List[float], top_k: int = 5, filter_conditions: Optional[models.Filter] = None) -> List[models.ScoredPoint]:
        """Search text embeddings."""
        collection_name = f"{user_id}_text_embeddings"
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filter_conditions
        )
    
    def search_images(self, user_id: str, query_vector: List[float], top_k: int = 5, filter_conditions: Optional[models.Filter] = None) -> List[models.ScoredPoint]:
        """Search image embeddings."""
        collection_name = f"{user_id}_image_embeddings"
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filter_conditions
        )

    def search_keyword(self, user_id: str, query_text: str, top_k: int = 5) -> List[models.ScoredPoint]:
        """
        Simulate keyword search using Qdrant's scroll/filter or text matching if available.
        For now, we will use a simple scroll with a filter if we had payload indexing, 
        but since we don't have a dedicated keyword engine, we'll try to use Qdrant's recommendation 
        or just rely on the vector search if keyword isn't strictly supported without a plugin.
        
        However, to strictly follow the "word search" requirement, we might need to assume 
        the payload contains the text and we do a filter. 
        
        Let's assume we can filter by a 'text' field in payload containing the query words.
        This is a naive implementation of "keyword search" in a vector DB without an inverted index.
        """
        collection_name = f"{user_id}_text_embeddings"
        
        # This is a placeholder for a real BM25 or keyword search.
        # Qdrant supports full-text search on payload fields if configured.
        # We will assume the 'content' field is indexed for text.
        
        try:
            # Try to use Qdrant's text filter if available, otherwise just return empty or fallback
            # For this implementation, we'll return an empty list if we can't do true keyword search,
            # or we can rely on the hybrid retriever to handle the logic.
            # Let's try to use a Match filter on the 'content' field.
            
            # Note: This requires the 'content' field to be indexed as 'text'.
            
            return self.client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="content",
                            match=models.MatchText(text=query_text)
                        )
                    ]
                ),
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )[0] # scroll returns (points, next_page_offset)
        except Exception as e:
            print(f"Keyword search failed or not supported: {e}")
            return []


class PostgresConnector:
    def __init__(self, host: str = "localhost", port: int = 5432, user: str = "postgres", password: str = "password", dbname: str = "nexus_db"):
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname
        )
        self.conn.autocommit = True

    def create_user_structure(self, user_id: str):
        schema_name = f"schema_user_{user_id}"
        with self.conn.cursor() as cur:
            # Create schema
            cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema_name)))
            
            # Create uploads table inside the schema
            # Example table structure, can be adjusted
            cur.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {}.uploads (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
            """).format(sql.Identifier(schema_name)))
            print(f"Schema {schema_name} and table uploads created.")

    def push(self, user_id: str, table_name: str, data: Dict[str, Any]):
        schema_name = f"schema_user_{user_id}"
        columns = data.keys()
        values = [data[column] for column in columns]
        
        insert_query = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
            sql.Identifier(schema_name),
            sql.Identifier(table_name),
            sql.SQL(', ').join(map(sql.Identifier, columns)),
            sql.SQL(', ').join(sql.Placeholder() * len(values))
        )
        
        with self.conn.cursor() as cur:
            cur.execute(insert_query, values)
        print(f"Data inserted into {schema_name}.{table_name}.")

    def pull(self, user_id: str, table_name: str, query_params: Dict[str, Any] = None) -> List[tuple]:
        schema_name = f"schema_user_{user_id}"
        query = sql.SQL("SELECT * FROM {}.{}").format(
            sql.Identifier(schema_name),
            sql.Identifier(table_name)
        )
        
        if query_params:
            conditions = []
            values = []
            for k, v in query_params.items():
                conditions.append(sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder()))
                values.append(v)
            
            query = sql.SQL(" WHERE ").join([query, sql.SQL(" AND ").join(conditions)])
            
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                return cur.fetchall()
        else:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()

    def delete(self, user_id: str, table_name: str, condition: Dict[str, Any]):
        schema_name = f"schema_user_{user_id}"
        if not condition:
            raise ValueError("Condition required for delete")
            
        conditions = []
        values = []
        for k, v in condition.items():
            conditions.append(sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder()))
            values.append(v)
            
        query = sql.SQL("DELETE FROM {}.{} WHERE {}").format(
            sql.Identifier(schema_name),
            sql.Identifier(table_name),
            sql.SQL(" AND ").join(conditions)
        )
        
        with self.conn.cursor() as cur:
            cur.execute(query, values)
        print(f"Data deleted from {schema_name}.{table_name}.")

    def execute_raw_sql(self, sql_query: str) -> List[tuple]:
        """
        Executes a raw SQL query and returns the results.
        WARNING: This is dangerous if not properly sanitized, but required for the SQL Agent.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql.SQL(sql_query))
                if cur.description: # Check if it's a SELECT query (returns rows)
                    return cur.fetchall()
                return [] # For INSERT/UPDATE/DELETE
        except Exception as e:
            print(f"Error executing raw SQL: {e}")
            raise e
        
    def close(self):
        self.conn.close()


class MinioConnector:
    def __init__(self, endpoint: str = "localhost:9000", access_key: str = "minioadmin", secret_key: str = "minioadmin123", secure: bool = False):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )

    def setup_user_dirs(self, org_id: str, user_id: str):
        # MinIO buckets are global, so we might use one bucket for the org or one global bucket
        # Let's assume one bucket per organization for better isolation, or one main bucket 'nexus-storage'
        # Based on request: "create two directory one for organisation and another for user"
        # We'll use a bucket named f"org-{org_id}"
        bucket_name = f"org-{org_id}"
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            print(f"Bucket {bucket_name} created.")
        else:
            print(f"Bucket {bucket_name} exists.")
            
        # Directories in S3 are virtual, so we don't strictly need to create them, 
        # but we can create an empty object to simulate a folder if needed.
        # For now, we just ensure the bucket exists.

    def push(self, org_id: str, user_id: str, category: str, file_path: str, object_name: str = None):
        bucket_name = f"org-{org_id}"
        if object_name is None:
            object_name = os.path.basename(file_path)
            
        # Path: user_{user_id}/{category}/{object_name}
        object_path = f"user_{user_id}/{category}/{object_name}"
        
        try:
            self.client.fput_object(
                bucket_name,
                object_path,
                file_path,
            )
            print(f"File {file_path} uploaded to {bucket_name}/{object_path}.")
        except S3Error as e:
            print(f"Error uploading file: {e}")

    def pull(self, org_id: str, user_id: str, category: str, object_name: str, file_path: str):
        bucket_name = f"org-{org_id}"
        object_path = f"user_{user_id}/{category}/{object_name}"
        
        try:
            self.client.fget_object(
                bucket_name,
                object_path,
                file_path
            )
            print(f"File {object_path} downloaded to {file_path}.")
        except S3Error as e:
            print(f"Error downloading file: {e}")

    def delete(self, org_id: str, user_id: str, category: str, object_name: str):
        bucket_name = f"org-{org_id}"
        object_path = f"user_{user_id}/{category}/{object_name}"
        
        try:
            self.client.remove_object(bucket_name, object_path)
            print(f"Object {object_path} removed from {bucket_name}.")
        except S3Error as e:
            print(f"Error deleting file: {e}")


class ConnectionManager:
    def __init__(self):
        self.qdrant = QdrantConnector()
        self.postgres = PostgresConnector()
        self.minio = MinioConnector()

    def onboard_new_user(self, user_id: str, org_id: str):
        print(f"Onboarding user {user_id} for org {org_id}...")
        self.postgres.create_user_structure(user_id)
        self.qdrant.create_user_collection(user_id)
        self.minio.setup_user_dirs(org_id, user_id)
        print("User onboarding complete.")

    def get_qdrant(self):
        return self.qdrant

    def get_postgres(self):
        return self.postgres

    def get_minio(self):
        return self.minio
