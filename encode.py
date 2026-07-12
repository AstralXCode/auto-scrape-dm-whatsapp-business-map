#!/usr/bin/env python3
"""ASTRAL Script Encoder - Encode scrape.py agar tidak mudah di-copy"""
import base64, zlib, sys, os

def encode_script(input_file, output_file):
    """Encode script with base64 + zlib"""
    with open(input_file, 'r') as f:
        code = f.read()

    # Compress + encode
    compressed = zlib.compress(code.encode('utf-8'))
    encoded = base64.b64encode(compressed).decode('ascii')

    # Create decoder stub
    decoder = f'''#!/usr/bin/env python3
import base64, zlib, sys
_data = "{encoded}"
_code = zlib.decompress(base64.b64decode(_data)).decode('utf-8')
exec(compile(_code, __file__, 'exec'))
'''
    with open(output_file, 'w') as f:
        f.write(decoder)

    # Set permissions
    os.chmod(output_file, 0o755)

    orig_size = os.path.getsize(input_file)
    enc_size = os.path.getsize(output_file)
    print(f"✓ Encoded: {input_file} → {output_file}")
    print(f"  Original: {orig_size:,} bytes")
    print(f"  Encoded:  {enc_size:,} bytes")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 encode.py <input.py> [output.py]")
        print("Default output: <input>_enc.py")
        sys.exit(1)

    input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base = os.path.splitext(input_file)[0]
        output_file = f"{base}_enc.py"

    encode_script(input_file, output_file)
