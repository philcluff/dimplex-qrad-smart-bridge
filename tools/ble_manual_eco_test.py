import asyncio
from bleak import BleakScanner, BleakClient

BASE = "0000{:04x}-0000-1000-8000-00805f9b34fb"
MODE, SETPOINT = BASE.format(0x1001), BASE.format(0x1023)
NAMES = {1: "Timer", 2: "Manual", 3: "Eco", 4: "Frost"}

async def state(c, label):
    m = await c.read_gatt_char(MODE); sp = await c.read_gatt_char(SETPOINT)
    print(f"{label:28s} mode={m.hex()} ({NAMES.get(m[0],'?')}) setpoint={sp[0]}C")
    return m, sp

async def step(c, label, uuid, payload):
    await c.write_gatt_char(uuid, payload, response=True)
    await asyncio.sleep(2)
    return await state(c, label)

async def main():
    found = {}
    async with BleakScanner(lambda d, a: found.__setitem__(d.address, a.rssi) if "dimplex" in (d.name or a.local_name or "").lower() else None):
        await asyncio.sleep(8)
    async with BleakClient(max(found, key=found.get), timeout=30) as c:
        m0, sp0 = await state(c, "start")
        await step(c, "write mode 2 (Manual)", MODE, bytes([2, 0, 0, 0, 0, 0]))
        await step(c, "write setpoint 15", SETPOINT, bytes([15, 0]))
        await step(c, "write setpoint 21", SETPOINT, bytes([21, 0]))
        await step(c, "write setpoint 18", SETPOINT, bytes([18, 0]))
        await step(c, "write setpoint 19", SETPOINT, bytes([19, 0]))
        await step(c, "write mode 3 (Eco)", MODE, bytes([3, 0, 0, 0, 0, 0]))
        await step(c, "write setpoint 22 in Eco", SETPOINT, bytes([22, 0]))
        input("Check the display, then press Enter to restore... ")
        await step(c, "restore mode", MODE, bytes(m0))
        await step(c, "restore setpoint", SETPOINT, bytes(sp0))

asyncio.run(main())
