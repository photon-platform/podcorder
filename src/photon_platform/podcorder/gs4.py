import subprocess
import gi
import os
import datetime
import re
from post_process import *
import threading
import time


gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# Initialize GStreamer
Gst.init(None)


def display_elapsed_time(start_time, stop_event):
    while not stop_event.is_set():
        elapsed_time = time.time() - start_time
        elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
        print(f'\rElapsed Time: {elapsed_str}', end='')
        time.sleep(1)  # Update every second
    print()  # Ensure the next print statement is on a new line


def main():

    # Prompt for clip name and create directory
    title = input("Title for the clip: ")
    slug = slugify(title)
    ts = datetime.datetime.now().strftime("%y.%j.%H%M%S")
    folder_name = f"{ts}_{slug}"
    os.makedirs(folder_name, exist_ok=True)

    screen_file = os.path.join(folder_name, "screen.mkv")
    mic_file = os.path.join(folder_name, "mic.ogg")
    system_file = os.path.join(folder_name, "system.ogg")

    screen_pipeline = Gst.parse_launch(
        f"ximagesrc use-damage=0 startx=0 starty=768 endx=1919 endy=1847 ! "
        f"videoconvert ! vp8enc cpu-used=4 target-bitrate=2000000 ! matroskamux ! "
        f"filesink location={screen_file}")

    mic = "alsa_input.usb-BLUE_MICROPHONE_Blue_Snowball_201305-00.analog-stereo"
    mic_pipeline = Gst.parse_launch(
        f"pulsesrc device={mic} ! "
        f"volume volume=1.8 ! "
        f"audioconvert ! opusenc ! oggmux ! "
        f"filesink location={mic_file}")

    system = "alsa_output.pci-0000_0a_00.6.analog-stereo.monitor"
    system_audio_pipeline = Gst.parse_launch(
        f"pulsesrc device={system} ! "
        f"volume volume=0.7 ! "
        f"audioconvert ! opusenc ! oggmux ! "
        f"filesink location={system_file}")

    # Create the main loop
    loop = GLib.MainLoop()
    stop_event = threading.Event()

    # Start the elapsed time display thread
    start_time = time.time()
    elapsed_thread = threading.Thread(target=display_elapsed_time, args=(start_time, stop_event))
    elapsed_thread.start()
    

    try:
        # Start the pipelines
        screen_pipeline.set_state(Gst.State.PLAYING)
        mic_pipeline.set_state(Gst.State.PLAYING)
        system_audio_pipeline.set_state(Gst.State.PLAYING)
        loop.run()
    except KeyboardInterrupt:
        # Send EOS to each pipeline
        screen_pipeline.send_event(Gst.Event.new_eos())
        mic_pipeline.send_event(Gst.Event.new_eos())
        system_audio_pipeline.send_event(Gst.Event.new_eos())

        # Stop the pipelines on interrupt
        screen_pipeline.set_state(Gst.State.NULL)
        mic_pipeline.set_state(Gst.State.NULL)
        system_audio_pipeline.set_state(Gst.State.NULL)
        loop.quit()

        stop_event.set()
        elapsed_thread.join()


    mic_clean_file = clean_mic_audio(mic_file)

    screen_system_file = combine_screen_system(folder_name, screen_file, system_file)

    all_file = combine_all(folder_name, screen_system_file, mic_clean_file)

    mic_wave = generate_waveform(mic_clean_file, "Green")
    system_wave = generate_waveform(system_file, "Orange")

    screen_waves_file = combine_screen_waves(folder_name, screen_file, mic_wave, system_wave)

if __name__ == "__main__":
    main()

