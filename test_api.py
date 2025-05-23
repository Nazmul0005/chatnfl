import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        response = await client.get('https://api.sportradar.com/nfl/official/trial/v7/en/league/hierarchy.json?api_key=EQLJam968WSEZ8ASHS3ICejYya2AxcPkKGP1DVZ9')
        print(f'Status: {response.status_code}')
        print(response.text[:500] if response.status_code == 200 else 'Error')

if __name__ == "__main__":
    asyncio.run(test())
