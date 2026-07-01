#!/usr/bin/env python3
"""OFFLINE seed recovery for the 'tony-miner' coldkey. RUN DISCONNECTED.
Output = master coldkey seed (all TAO + stake). Paper only. Never paste/sync it."""
import os, json

WALLET = "tony-miner"
COLDKEY = os.path.expanduser(f"~/.bittensor/wallets/{WALLET}/coldkey")

def via_wallet_lib():
    from bittensor_wallet import Wallet
    w = Wallet(name=WALLET)
    try: w.unlock_coldkey()          # prompts for your PASSWORD
    except Exception: pass
    kp = w.coldkey
    return getattr(kp, "mnemonic", None), getattr(kp, "seed_hex", None)

def via_keyfile_json():
    from bittensor_wallet import Keyfile
    kf = Keyfile(path=COLDKEY)
    kf.decrypt()                     # prompts for your PASSWORD
    raw = kf.keyfile_data
    obj = json.loads(raw.decode() if isinstance(raw, (bytes, bytearray)) else raw)
    return obj.get("secretPhrase"), obj.get("secretSeed")

def via_sdk():
    import bittensor
    kp = bittensor.wallet(name=WALLET).coldkey   # prompts for your PASSWORD
    return getattr(kp, "mnemonic", None), getattr(kp, "seed_hex", None)

mnem = seed = None
for fn in (via_wallet_lib, via_keyfile_json, via_sdk):
    try:
        mnem, seed = fn()
        if mnem or seed:
            print(f"[ok via {fn.__name__}]"); break
    except Exception as e:
        print(f"[{fn.__name__} unavailable: {e}]")

print("\n=============== KEEP OFFLINE — TREAT AS CASH ===============")
print("MNEMONIC :", mnem or "(this version didn't expose words — use RAW SEED)")
print("RAW SEED :", seed or "(none — send me the [..unavailable..] lines, NOT this)")
print("Import into Talisman/SubWallet as 'mnemonic' (preferred) or 'raw seed'.")
print("===========================================================")