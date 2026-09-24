import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

async def inspect():
    mongodb_uri = "mongodb+srv://tiwaririshank242_db_user:CertiTrust2026@cluster0.4wegwkf.mongodb.net/certitrust?retryWrites=true&w=majority"
    client = AsyncIOMotorClient(mongodb_uri, tls=True, tlsAllowInvalidCertificates=True)
    db = client["certitrust"]
    
    users = await db.users.find({}).to_list(100)
    print("=== USERS IN MONGODB ATLAS ===")
    print(f"Total users: {len(users)}")
    for u in users:
        print(f"ID: {u.get('_id')} (type: {type(u.get('_id'))}), email: {u.get('email')}, role: {u.get('role')}, org: {u.get('organization')}")
        
    credentials = await db.credentials.find({}).to_list(100)
    print("\n=== CREDENTIALS IN MONGODB ATLAS ===")
    print(f"Total credentials: {len(credentials)}")
    for c in credentials:
        print(f"\nCredential ID: {c.get('_id')} (type: {type(c.get('_id'))})")
        print(f"  student_name: {c.get('student_name')}")
        print(f"  certificate_number: {c.get('certificate_number')}")
        print(f"  uploaded_by: {c.get('uploaded_by')} (type: {type(c.get('uploaded_by'))})")
        print(f"  institution_id: {c.get('institution_id')} (type: {type(c.get('institution_id'))})")
        print(f"  issuer_id: {c.get('issuer_id')} (type: {type(c.get('issuer_id'))})")
        print(f"  created_by: {c.get('created_by')} (type: {type(c.get('created_by'))})")
        print(f"  owner_id: {c.get('owner_id')} (type: {type(c.get('owner_id'))})")
        print(f"  status: {c.get('status')}")
        print(f"  all keys: {list(c.keys())}")

    certs_coll = await db.certificates.find({}).to_list(100)
    print("\n=== CERTIFICATES COLLECTION IN MONGODB ATLAS ===")
    print(f"Total documents in 'certificates': {len(certs_coll)}")
    for c in certs_coll:
        print(f"ID: {c.get('_id')}, keys: {list(c.keys())}")

if __name__ == "__main__":
    asyncio.run(inspect())
