import asyncio, json, sys, time
from bleak import BleakScanner, BleakClient

NAME = "Dimplex"
OUT = sys.argv[1] if len(sys.argv) > 1 else "qrad_gatt.json"

async def main():
    print("Scanning 10s for", NAME)
    found = {}
    def cb(d, adv):
        if NAME.lower() in (d.name or adv.local_name or "").lower():
            found[d.address] = (d, adv)
    async with BleakScanner(cb):
        await asyncio.sleep(10)
    if not found:
        print("No Dimplex device seen. Is Comms > Bluetooth enabled?"); return
    for a, (d, adv) in found.items():
        print(f"  {a}  name={d.name!r} rssi={adv.rssi} mfg={ {k: v.hex() for k, v in adv.manufacturer_data.items()} } svc={adv.service_uuids}")
    addr = max(found, key=lambda a: found[a][1].rssi)
    d, adv = found[addr]
    print("Connecting to", addr)
    dump = {"address": addr, "name": d.name, "rssi": adv.rssi,
            "manufacturer_data": {str(k): v.hex() for k, v in adv.manufacturer_data.items()},
            "adv_service_uuids": adv.service_uuids, "services": []}
    async with BleakClient(addr, timeout=30) as c:
        print("Connected. Enumerating (a pairing prompt may appear)...")
        for s in c.services:
            sd = {"uuid": s.uuid, "description": s.description, "characteristics": []}
            for ch in s.characteristics:
                cd = {"uuid": ch.uuid, "handle": ch.handle, "description": ch.description,
                      "properties": ch.properties, "descriptors": [(x.uuid, x.description) for x in ch.descriptors]}
                if "read" in ch.properties:
                    try:
                        v = await c.read_gatt_char(ch)
                        cd["value_hex"] = v.hex()
                        try: cd["value_ascii"] = v.decode("ascii")
                        except Exception: pass
                    except Exception as e:
                        cd["read_error"] = str(e)
                sd["characteristics"].append(cd)
                print(f"  {s.uuid[:8]} {ch.uuid[:8]} h={ch.handle:4d} {','.join(ch.properties):28s} {cd.get('value_hex', cd.get('read_error',''))}")
            dump["services"].append(sd)
    json.dump(dump, open(OUT, "w"), indent=2)
    nchar = sum(len(s["characteristics"]) for s in dump["services"])
    print(f"\nWrote {OUT}: {len(dump['services'])} services, {nchar} characteristics")

asyncio.run(main())
