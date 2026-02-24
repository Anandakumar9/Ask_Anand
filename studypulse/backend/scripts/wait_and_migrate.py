"""
Wait for Railway deployment and run migration.
This script polls the production API until the migration endpoint is available.
"""
import asyncio
import aiohttp
import json

PRODUCTION_API_URL = "https://askanand-simba.up.railway.app"

async def wait_and_migrate():
    """Wait for Railway to deploy and then run migration."""
    
    print("=" * 60)
    print("Waiting for Railway deployment...")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Poll for migration endpoint
        for attempt in range(30):  # Try for 5 minutes (30 * 10 seconds)
            try:
                # Try the migration endpoint
                async with session.post(
                    f"{PRODUCTION_API_URL}/api/v1/migration/run",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"\n✅ Migration endpoint found!")
                        print(f"   Result: {json.dumps(result, indent=2)}")
                        return True
                    elif response.status != 404:
                        text = await response.text()
                        print(f"\n⚠️  Migration endpoint returned {response.status}: {text[:200]}")
                        
            except asyncio.TimeoutError:
                print(f"  [{attempt+1}/30] Timeout, retrying...")
            except Exception as e:
                print(f"  [{attempt+1}/30] Error: {e}")
            
            await asyncio.sleep(10)
        
        print("\n❌ Migration endpoint not found after 5 minutes")
        print("   Please check Railway dashboard for deployment status")
        return False

if __name__ == "__main__":
    asyncio.run(wait_and_migrate())
