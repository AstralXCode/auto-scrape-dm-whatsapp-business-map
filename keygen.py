#!/usr/bin/env python3
"""ASTRAL License Key Generator - FOR SELLER ONLY"""
import hashlib, sys, os

SECRET = "ASTRAL_X7K9M2"

def get_device_id(prefix="/data/data/com.termux/files/usr"):
    return hashlib.md5(prefix.encode()).hexdigest()[:12]

def gen_key(device_id, days=365):
    raw = f"{device_id}:{SECRET}:{days}"
    key = hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
    return f"ASTRAL-{key[:4]}-{key[4:8]}-{key[8:12]}-{key[12:]}"

def verify(key, device_id):
    for days in [365, 180, 90, 60, 30, 14, 7, 3, 1]:
        raw = f"{device_id}:{SECRET}:{days}"
        expected = hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
        expected_fmt = f"ASTRAL-{expected[:4]}-{expected[4:8]}-{expected[8:12]}-{expected[12:]}"
        if key.upper() == expected_fmt:
            return True
    return False

if __name__ == "__main__":
    print("=" * 50)
    print("  ASTRAL LICENSE KEY GENERATOR")
    print("  FOR SELLER ONLY - JANGAN DIBAGIKAN!")
    print("=" * 50)
    print()

    while True:
        print("[1] Generate key dari Device ID")
        print("[2] Verify key")
        print("[0] Exit")
        print()
        ch = input("▸ Pilih: ").strip()

        if ch == "1":
            did = input("▸ Device ID pembeli: ").strip()
            days = input("▸ Hari (default 365): ").strip()
            days = int(days) if days.isdigit() else 365
            key = gen_key(did, days)
            print(f"\n  ✓ License Key: {key}")
            print(f"  ✓ Device ID: {did}")
            print(f"  ✓ Expired: {days} hari")
            print()
            input("Tekan Enter...")
        elif ch == "2":
            did = input("▸ Device ID: ").strip()
            key = input("▸ License Key: ").strip()
            if verify(key, did):
                print("\n  ✓ VALID!")
            else:
                print("\n  ✗ INVALID!")
            input("\nTekan Enter...")
        elif ch == "0":
            break
