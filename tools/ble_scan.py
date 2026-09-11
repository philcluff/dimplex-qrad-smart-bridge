import asyncio, sys, time
from bleak import BleakScanner

SECS = int(sys.argv[1]) if len(sys.argv) > 1 else 15

async def main():
    seen = {}
    def cb(d, adv):
        n = d.name or adv.local_name or ""
        if "dimplex" in n.lower():
            seen.setdefault(d.address, [n, adv.rssi, 0])
            seen[d.address][1] = adv.rssi
            seen[d.address][2] += 1
    print(f"Scanning {SECS}s for Dimplex adverts...")
    async with BleakScanner(cb):
        await asyncio.sleep(SECS)
    if not seen:
        print(time.strftime("%H:%M:%S"), "NOT advertising")
    for a, (n, r, c) in seen.items():
        print(time.strftime("%H:%M:%S"), f"advertising: {n} rssi={r} packets={c}")

asyncio.run(main())
