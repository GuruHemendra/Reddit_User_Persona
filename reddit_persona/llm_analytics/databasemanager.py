import chromadb
from sentence_transformers import SentenceTransformer
import os

class DatabaseManager:
    def __init__(self, path, collection_name="reddit_user_data", embedding_model_name="all-MiniLM-L6-v2"):
        # Initialize ChromaDB client and collection
        chroma_path = os.path.join(path,"./chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.chroma_client.get_or_create_collection(name=collection_name)
        # Load embedding model
        self.embedding_model = SentenceTransformer(embedding_model_name)

    def clean_metadata(self, metadata: dict) -> dict:
        return {k: ("" if v is None else v) for k, v in metadata.items()}

    def embed_text(self, text: str):
        # Returns embedding as list
        return self.embedding_model.encode(text).tolist()

    def upload_reddit_user_data(self, json_data):
        ids = []
        documents = []
        embeddings = []
        metadatas = []

        # Subreddits
        for subreddit_name, subreddit_data in json_data.get("subreddits_master", {}).items():
            doc_id = f"sub_{subreddit_name}"
            text = f"{subreddit_data.get('title', '')} {subreddit_data.get('public_description', '')}"
            vector = self.embed_text(text)

            ids.append(doc_id)
            documents.append(text)
            embeddings.append(vector)
            metadatas.append(self.clean_metadata({
                "type": "subreddit",
                "subreddit_name": subreddit_name,
                **subreddit_data
            }))

        # Posts
        for idx, post in enumerate(json_data.get("posts", [])):
            post_info = post["post_info"]
            subreddit_name = post["subreddit"]
            flair_text = post_info.get("flair", "")
            text = f"title: {post_info['title']} flair: {flair_text} subreddit:{subreddit_name} content: {post_info['body']}"
            vector = self.embed_text(text)

            post_payload = {
                "type": "post",
                "post_title": post_info["title"],
                "post_flair": flair_text,
                "post_url": post_info["reddit_url"],
                "post_created_at": post_info["created_at"],
                "subreddit_name": subreddit_name,
                "body": post_info["body"]
            }

            ids.append(f"post_{idx}")
            documents.append(text)
            embeddings.append(vector)
            metadatas.append(self.clean_metadata(post_payload))

        # Comments
        comment_counter = 0
        for comment_group in json_data.get("comments", []):
            post_info = comment_group["post_info"]
            subreddit_name = comment_group["subreddit"]

            for comment in comment_group["comments"]:
                text = f"content: {comment['body']} post_title: {post_info['title']} subreddit: {subreddit_name}"
                vector = self.embed_text(text)

                comment_payload = {
                    "type": "comment",
                    "comment_body": comment["body"],
                    "comment_created_at": comment["created_at"],
                    "comment_url": comment["url"],
                    "post_title": post_info["title"],
                    "post_url": post_info["reddit_url"],
                    "subreddit_name": subreddit_name
                }

                ids.append(f"comment_{comment_counter}")
                documents.append(text)
                embeddings.append(vector)
                metadatas.append(self.clean_metadata(comment_payload))
                comment_counter += 1

        # Upload all to ChromaDB
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        print(f"✅ Uploaded {len(ids)} records to ChromaDB.")
        return self.collection,self.embed_text

    def retrieve(self, query: str, n_results=5):
        """
        Retrieve the top `n_results` most similar records for the given query.
        Returns list of dictionaries with document and metadata.
        """
        query_embedding = self.embed_text(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        # results is a dict with keys like 'ids', 'documents', 'metadatas', 'distances'
        retrieved = []
        for i in range(len(results['documents'][0])):
            retrieved.append({
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i]
            })

        return retrieved
