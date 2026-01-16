import pyaudio

p = pyaudio.PyAudio()

print("\n--- Available Audio Input Devices ---")
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

found_mic = False
for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        found_mic = True
        name = p.get_device_info_by_host_api_device_index(0, i).get('name')
        print(f"Device ID {i}: {name}")

if not found_mic:
    print("❌ No microphones found!")

p.terminate()