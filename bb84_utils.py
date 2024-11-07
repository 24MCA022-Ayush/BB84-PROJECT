import random
import cirq

def format_binary(bits):
    binary_str = ''.join(str(bit) for bit in bits)
    return ' '.join(binary_str[i:i+8] for i in range(0, len(binary_str), 8))

def message_to_bits(message):
    bits = []
    for char in message:
        char_bits = format(ord(char), '08b')
        bits.extend(int(bit) for bit in char_bits)
    return bits

def prepare_qubits_using_bb84(len_key):
    alice_bits = [random.randint(0, 1) for _ in range(len_key)]
    alice_bases = [random.choice(['+', 'x']) for _ in range(len_key)]
    bob_bases = [random.choice(['+', 'x']) for _ in range(len_key)]
    
    qubits = [cirq.LineQubit(i) for i in range(len_key)]
    circuit = cirq.Circuit()
    
    for i, (bit, base) in enumerate(zip(alice_bits, alice_bases)):
        if bit == 1:
            circuit.append(cirq.X(qubits[i]))
        if base == 'x':
            circuit.append(cirq.H(qubits[i]))
    
    for i, base in enumerate(bob_bases):
        if base == 'x':
            circuit.append(cirq.H(qubits[i]))
        circuit.append(cirq.measure(qubits[i], key=str(i)))
    
    return circuit, alice_bits, alice_bases, bob_bases, qubits

def simulate_bb84(circuit):
    simulator = cirq.Simulator()
    results = simulator.run(circuit, repetitions=1)
    return results

def reconcile_key(alice_bits, alice_bases, bob_bases, measurement_results):
    sifted_key = []
    
    for i, (a_base, b_base) in enumerate(zip(alice_bases, bob_bases)):
        if a_base == b_base:
            if hasattr(measurement_results, 'data'):
                measured_bit = int(measurement_results.data[str(i)].iloc[0])
            else:
                measured_bit = int(measurement_results[str(i)][0][0])
            
            sifted_key.append(measured_bit)
    
    return sifted_key

def privacy_amplification(key):
    if len(key) < 2:
        return key
    
    amplified = []
    for i in range(0, len(key) - 1, 2):
        amplified.append(key[i] ^ key[i + 1])
    return amplified

def bits_to_bytes(bits):
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) == 8:
            byte = 0
            for bit in byte_bits:
                byte = (byte << 1) | bit
            bytes_list.append(byte)
    return bytes_list

def encrypt_message(key, message):
    message_bits = message_to_bits(message)
    encrypted_bits = []
    
    for i, bit in enumerate(message_bits):
        key_bit = key[i % len(key)]
        encrypted_bits.append(bit ^ key_bit)
    
    return encrypted_bits

def decrypt_message(key, encrypted_bits):
    decrypted_bits = []
    
    for i, bit in enumerate(encrypted_bits):
        key_bit = key[i % len(key)]
        decrypted_bits.append(bit ^ key_bit)
    
    decrypted_bytes = bits_to_bytes(decrypted_bits)
    decrypted_message = ''.join(chr(byte) for byte in decrypted_bytes)
    
    return decrypted_message
