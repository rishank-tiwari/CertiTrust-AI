import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys

async def test_mongo():
    url = "mongodb+srv://gauravsharma45438_db_user:5HvDG5m1OLsgh7MY@certitrust.5jwu4po.mongodb.net/?appName=CertiTrust"
    print("Testing connection to default Atlas URL...")
    client = AsyncIOMotorClient(url)
    try:
        # Trigger connection check
        await client.admin.command('ping')
        print("Success! Connected to MongoDB Atlas.")
        return
    except Exception as e:
        print(f"Failed: {type(e).__name__}: {e}")

    # Test with tlsAllowInvalidCertificates
    url_tls = url + "&tlsAllowInvalidCertificates=true"
    print("\nTesting connection with tlsAllowInvalidCertificates=true...")
    client = AsyncIOMotorClient(url_tls)
    try:
        await client.admin.command('ping')
        print("Success with tlsAllowInvalidCertificates!")
        return
    except Exception as e:
        print(f"Failed: {type(e).__name__}: {e}")

    # Test with local mongodb fallback
    url_local = "mongodb://localhost:27017/certitrust"
    print("\nTesting connection to local MongoDB (mongodb://localhost:27017)...")
    client = AsyncIOMotorClient(url_local)
    try:
        await client.admin.command('ping')
        print("Success! Connected to local MongoDB.")
        print("We can fall back to local MongoDB in .env if Atlas connection fails.")
        return
    except Exception as e:
        print(f"Failed: {type(e).__name__}: {e}")

asyncio.run(test_mongo())
