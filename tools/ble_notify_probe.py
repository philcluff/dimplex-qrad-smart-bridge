import asyncio, sys, time
from bleak import BleakScanner, BleakClient

SECS = int(sys.argv[1]) if len(sys.argv) > 1 else 90

async def main():
    found = {}
    async with BleakScanner(lambda d, a: found.__setitem__(d.address, a.rssi) if "dimplex" in (d.name or a.local_name or "").lower() else None):
        await asyncio.sleep(8)
    if not found: print("No Dimplex device"); return
    addr = max(found, key=found.get)
    async with BleakClient(addr, timeout=30) as c:
        subscribed = []
        for s in c.services:
            if s.uuid.startswith("00060000-f8ce"): continue
            for ch in s.characteristics:
                def cb(sender, data, ch=ch):
                    print(f"{time.strftime('%H:%M:%S')} NOTIFY {ch.uuid[:8]} h={ch.handle} {data.hex()}", flush=True)
                try:
                    await c.start_notify(ch, cb)
                    subscribed.append(ch.uuid[:8])
                except Exception as e:
                    if ch.uuid[4:8] in ("2006","2007","2008","200f"):
                        print(f"  {ch.uuid[:8]} h={ch.handle} props={ch.properties} notify refused: {e}")
        print(f"Subscribed to {len(subscribed)}: {subscribed}")
        print(f"Listening {SECS}s...")
        await asyncio.sleep(SECS)

asyncio.run(main())
