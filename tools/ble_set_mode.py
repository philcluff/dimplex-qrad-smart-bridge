import asyncio, sys
from bleak import BleakScanner, BleakClient

BASE = "0000{:04x}-0000-1000-8000-00805f9b34fb"
MODE, SETPOINT, ADVANCE, BOOSTMIN = BASE.format(0x1001), BASE.format(0x1023), BASE.format(0x100d), BASE.format(0x1027)
NAMES = {1: "Timer", 2: "Manual", 3: "Eco", 4: "Frost"}
SUBS = {1: "Out All Day", 2: "Home All Day", 3: "User Timer", 5: "Away"}

async def state(c, label):
    m = await c.read_gatt_char(MODE); sp = await c.read_gatt_char(SETPOINT); adv = await c.read_gatt_char(ADVANCE); bm = await c.read_gatt_char(BOOSTMIN)
    desc = NAMES.get(m[0], "?") + (f"/{SUBS.get(m[1], '?')}" if m[0] == 1 else "") + (" +boost" if m[3] else "")
    print(f"{label:10s} mode={m.hex()} ({desc}) setpoint={sp[0]}C advance={adv[0]} boostmin={bm[0]}")
    return m

async def write(c, uuid, payload):
    try:
        await c.write_gatt_char(uuid, payload, response=True); print(f"  write {uuid[4:8]} <- {payload.hex()} accepted"); return True
    except Exception as e:
        print(f"  write {uuid[4:8]} <- {payload.hex()} rejected: {e}"); return False

async def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("mode", "boost"):
        print("usage: ble_set_mode.py mode <1-4> [submode]   |   ble_set_mode.py boost <minutes>"); return
    found = {}
    async with BleakScanner(lambda d, a: found.__setitem__(d.address, a.rssi) if "dimplex" in (d.name or a.local_name or "").lower() else None):
        await asyncio.sleep(8)
    if not found: print("No Dimplex device"); return
    async with BleakClient(max(found, key=found.get), timeout=30) as c:
        orig = await state(c, "before")
        if sys.argv[1] == "mode":
            mode = int(sys.argv[2]); sub = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            payload = bytes([mode, sub, 0, 0, 0, 0])
            print(f"Setting mode {NAMES.get(mode)} sub {sub}")
            if not await write(c, MODE, payload): return
        else:
            mins = int(sys.argv[2])
            print(f"Starting boost for {mins} min")
            if not await write(c, MODE, bytes([2, 0, 0, 1, 0, 0])): return
            await asyncio.sleep(0.5)
            await write(c, BOOSTMIN, bytes([mins, 0]))
        await asyncio.sleep(2)
        await state(c, "after")
        input("Check the display, then press Enter to restore the original mode... ")
        await write(c, MODE, bytes(orig))
        if sys.argv[1] == "boost": await write(c, BOOSTMIN, bytes([0, 0]))
        await asyncio.sleep(2)
        await state(c, "restored")

asyncio.run(main())
