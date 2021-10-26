# Module to centralize Cryptopals Crypto Challenge functions
from base64 import b64decode, b64encode


class Cryptopals:

    def __init__(self):
        self.description = "Cryptopals Crypto Challenge Functions"

    def char_frequency(str):
        freq = {}
        for c in set(str):
            freq[c] = str.count(c)
        return freq


    def highest_frequency(self, str):
        freq = self.char_frequency(str)
        max_value = max(list(freq.values()))
        return list(freq.keys())[list(freq.values()).index(max_value)]


    def hex_to_byte(self, hexstr):
        return bytes.fromhex(hex_string)


    def hex_to_base64(self, hexstr):
        return b64encode(bytes.fromhex(hexstr)).decode()


    def base64_to_hex(self, b64str):
        return b64decode(b64str.encode()).hex()


    def xor_strings(self, s, t):
        sb = bytes.fromhex(s)
        tb = bytes.fromhex(t)
        return bytes([a ^ b for a, b in zip(sb, tb)]).hex()


    def single_char_xor(self, input, char):
        output = b''
        for byte in input:
            output += bytes([byte ^ char])
        return output, char
