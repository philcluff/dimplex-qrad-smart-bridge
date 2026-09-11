import asyncio, sys, time, threading
from bleak import BleakScanner, BleakClient

NAME = "dimplex"
SKIP_SERVICES = ("00060000-f8ce",)  # Cypress bootloader

async def main():
    found = {}
    def cb(d, adv):
        if NAME in (d.name or adv.local_name or "").lower():
            found[d.address] = adv.rssi
    async with BleakScanner(cb):
        await asyncio.sleep(8)
    if not found:
        print("No Dimplex device seen"); return
    addr = max(found, key=found.get)
    print("Connecting to", addr)
    async with BleakClient(addr, timeout=30) as c:
        chars = [ch for s in c.services if not s.uuid.startswith(SKIP_SERVICES)
                 for ch in s.characteristics if "read" in ch.properties]
        print(f"Watching {len(chars)} readable characteristics. Change things on the radiator. Ctrl-C to stop.")
        last = {}
        for ch in chars:
            try: last[ch.handle] = (await c.read_gatt_char(ch)).hex()
            except Exception as e: last[ch.handle] = f"ERR {e}"
        print("Baseline captured at", time.strftime("%H:%M:%S"))
        print("Type a note and press Enter at any time to stamp it into the log.")
        def stdin_marks():
            for line in sys.stdin:
                print(f"{time.strftime('%H:%M:%S')} MARK: {line.strip()}", flush=True)
        threading.Thread(target=stdin_marks, daemon=True).start()
        while True:
            for ch in chars:
                try: v = (await c.read_gatt_char(ch)).hex()
                except Exception as e: v = f"ERR {e}"
                if v != last[ch.handle]:
                    print(f"{time.strftime('%H:%M:%S')} h={ch.handle:4d} {ch.uuid[:8]}  {last[ch.handle]}  ->  {v}", flush=True)
                    last[ch.handle] = v
            await asyncio.sleep(0.5)

try: asyncio.run(main())
except KeyboardInterrupt: pass
