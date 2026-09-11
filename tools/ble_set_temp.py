import asyncio, sys
from bleak import BleakScanner, BleakClient

BASE = "0000{:04x}-0000-1000-8000-00805f9b34fb"
SETPOINT, EFFECTIVE, MODE = BASE.format(0x1023), BASE.format(0x1003), BASE.format(0x1001)
DELTA = int(sys.argv[1]) if len(sys.argv) > 1 else 2

async def read_state(c, label):
    sp = await c.read_gatt_char(SETPOINT); ef = await c.read_gatt_char(EFFECTIVE); md = await c.read_gatt_char(MODE)
    print(f"{label:12s} setpoint={sp.hex()} ({sp[0]}C) effective={ef.hex()} mode={md.hex()}")
    return sp

async def try_write(c, payload):
    try:
        await c.write_gatt_char(SETPOINT, payload, response=True)
        print(f"  write {payload.hex()} accepted")
        return True
    except Exception as e:
        print(f"  write {payload.hex()} rejected: {e}")
        return False

async def main():
    found = {}
    async with BleakScanner(lambda d, a: found.__setitem__(d.address, a.rssi) if "dimplex" in (d.name or a.local_name or "").lower() else None):
        await asyncio.sleep(8)
    if not found: print("No Dimplex device"); return
    addr = max(found, key=found.get)
    async with BleakClient(addr, timeout=30) as c:
        orig = await read_state(c, "before")
        target = orig[0] + DELTA
        print(f"Writing target {target}C")
        ok = await try_write(c, bytes([target, 0])) or await try_write(c, bytes([target]))
        if not ok: return
        await asyncio.sleep(2)
        after = await read_state(c, "after")
        if after[0] == target: print("  radiator reports the new setpoint")
        else: print("  setpoint did NOT change")
        input("Check the radiator display, then press Enter to restore the original... ")
        await try_write(c, bytes(orig))
        await asyncio.sleep(2)
        await read_state(c, "restored")

asyncio.run(main())
