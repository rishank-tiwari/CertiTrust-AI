import logging
import uuid
import re
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from config import get_settings

logger = logging.getLogger(__name__)

# --- In-Memory Mock Database Fallback for Hackathon Presentation Resilience ---
class InMemoryCollection:
    def __init__(self, name):
        self.name = name
        self.documents = []

    async def find_one(self, query):
        for doc in self.documents:
            if self._match_query(doc, query):
                # Return a copy to mimic real database document decoupling
                return doc.copy()
        return None

    async def insert_one(self, document):
        if "_id" not in document:
            document["_id"] = str(uuid.uuid4())
        doc_copy = document.copy()
        self.documents.append(doc_copy)
        
        class InsertResult:
            inserted_id = doc_copy["_id"]
            
        return InsertResult()

    async def insert_many(self, documents):
        inserted_ids = []
        for doc in documents:
            if "_id" not in doc:
                doc["_id"] = str(uuid.uuid4())
            doc_copy = doc.copy()
            self.documents.append(doc_copy)
            inserted_ids.append(doc_copy["_id"])
            
        class InsertManyResult:
            pass
        result_obj = InsertManyResult()
        result_obj.inserted_ids = inserted_ids
        return result_obj

    async def delete_many(self, query):
        if not query:
            self.documents = []
        else:
            self.documents = [d for d in self.documents if not self._match_query(d, query)]
        class DeleteResult:
            deleted_count = len(self.documents)
        return DeleteResult()

    async def update_one(self, query, update):
        doc = None
        # Locate the original document to mutate in-place in memory
        for d in self.documents:
            if self._match_query(d, query):
                doc = d
                break
        if doc and "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v
                
            class UpdateResult:
                modified_count = 1
                
            return UpdateResult()
            
        class UpdateResult:
            modified_count = 0
            
        return UpdateResult()

    async def count_documents(self, query):
        count = 0
        for doc in self.documents:
            if self._match_query(doc, query):
                count += 1
        return count

    def find(self, query=None, projection=None):
        query = query or {}
        matched_docs = [doc.copy() for doc in self.documents if self._match_query(doc, query)]
        
        class Cursor:
            def __init__(self, docs):
                self.docs = docs

            def sort(self, key, direction=None):
                reverse = True if direction == -1 else False
                try:
                    self.docs.sort(key=lambda x: x.get(key) or datetime.min.replace(tzinfo=timezone.utc), reverse=reverse)
                except Exception:
                    pass
                return self

            def limit(self, limit_val):
                self.docs = self.docs[:limit_val]
                return self

            async def to_list(self, length=None):
                if length:
                    return self.docs[:length]
                return self.docs

            # Async iterator support for "async for doc in cursor"
            def __aiter__(self):
                self._iter = iter(self.docs)
                return self

            async def __anext__(self):
                try:
                    return next(self._iter)
                except StopIteration:
                    raise StopAsyncIteration
        
        return Cursor(matched_docs)

    def _match_query(self, doc, query):
        for k, v in query.items():
            if k == "$or":
                match_any = False
                for subquery in v:
                    if self._match_query(doc, subquery):
                        match_any = True
                        break
                if not match_any:
                    return False
            elif k == "_id" and isinstance(v, dict) and "$in" in v:
                doc_id = str(doc.get("_id"))
                allowed_ids = [str(x) for x in v["$in"]]
                if doc_id not in allowed_ids:
                    return False
            elif isinstance(v, dict) and "$regex" in v:
                doc_val = str(doc.get(k, ""))
                regex_pat = v["$regex"]
                options = v.get("$options", "")
                flags = 0
                if "i" in options:
                    flags |= re.IGNORECASE
                if not re.search(regex_pat, doc_val, flags):
                    return False
            elif isinstance(v, dict) and "$in" in v:
                doc_val = doc.get(k)
                if doc_val not in v["$in"]:
                    return False
            else:
                # Direct comparison
                doc_val = doc.get(k)
                # Convert ObjectId to string if compared with a string
                if str(doc_val) != str(v):
                    return False
        return True


class InMemoryDatabase:
    def __init__(self):
        self.collections = {}

    def __getattr__(self, name):
        if name not in self.collections:
            self.collections[name] = InMemoryCollection(name)
        return self.collections[name]

    def __getitem__(self, name):
        return getattr(self, name)


class DatabaseClient:
    client: AsyncIOMotorClient = None
    db = None
    is_mock = False

db_client = DatabaseClient()

DEFAULT_MONGODB_URI = "mongodb+srv://tiwaririshank242_db_user:CertiTrust2026@cluster0.4wegwkf.mongodb.net/certitrust?retryWrites=true&w=majority"

async def connect_db():
    import os
    settings = get_settings()
    mongodb_uri = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL") or getattr(settings, "MONGODB_URI", "") or getattr(settings, "MONGODB_URL", "")
    if not mongodb_uri or mongodb_uri.strip() == "":
        mongodb_uri = DEFAULT_MONGODB_URI
    try:
        if not mongodb_uri:
            raise ValueError("Empty connection string")
        import certifi
        try:
            db_client.client = AsyncIOMotorClient(
                mongodb_uri,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            await db_client.client.admin.command('ping')
        except Exception:
            db_client.client = AsyncIOMotorClient(
                mongodb_uri,
                tls=True,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            await db_client.client.admin.command('ping')
        db_client.db = db_client.client[settings.DATABASE_NAME]
        db_client.is_mock = False
        logger.info("Connected to MongoDB Atlas database successfully.")
    except Exception as e:
        logger.warning(f"MongoDB Atlas connection failed or unconfigured: {e}")
        logger.warning(">>> Switching to thread-safe local In-Memory Database Fallback for development resilience! <<<")
        db_client.db = InMemoryDatabase()
        db_client.is_mock = True

async def close_db():
    if db_client.client and not db_client.is_mock:
        db_client.client.close()
        logger.info("Closed MongoDB connection.")

def get_database():
    if db_client.db is None:
        logger.info("Database instance was None, initializing default fallback in-memory database.")
        db_client.db = InMemoryDatabase()
        db_client.is_mock = True
    return db_client.db

def get_users_collection():
    return db_client.db["users"]

def get_credentials_collection():
    return db_client.db["credentials"]

def get_verification_records_collection():
    return db_client.db["verification_records"]

def get_resume_analysis_collection():
    return db_client.db["resume_analysis"]

async def check_db_connection() -> dict:
    try:
        import os
        settings = get_settings()
        mongodb_uri = os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL") or getattr(settings, "MONGODB_URI", "") or getattr(settings, "MONGODB_URL", "")
        
        if db_client.client and not db_client.is_mock:
            try:
                await db_client.client.admin.command('ping')
                return {
                    "status": "connected",
                    "database_name": settings.DATABASE_NAME,
                    "is_mock": False,
                    "message": "Connected to live MongoDB Atlas database."
                }
            except Exception as e:
                return {
                    "status": "in_memory_fallback",
                    "database_name": settings.DATABASE_NAME,
                    "is_mock": True,
                    "error": str(e),
                    "message": "MongoDB ping failed. Operating on in-memory fallback database."
                }
        else:
            return {
                "status": "in_memory_fallback",
                "database_name": settings.DATABASE_NAME,
                "is_mock": True,
                "uri_configured": bool(mongodb_uri),
                "message": "Operating on in-memory fallback database. Add a valid MONGODB_URI in Vercel settings to connect live MongoDB Atlas."
            }
    except Exception as e:
        return {
            "status": "in_memory_fallback",
            "database_name": "certitrust",
            "is_mock": True,
            "error": str(e)
        }
