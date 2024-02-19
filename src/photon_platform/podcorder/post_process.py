import subprocess
import os
import re

def slugify(value):
    """
    Converts to lowercase, removes non-word characters (alphanumerics and underscores)
    and converts spaces to hyphens. Also strips leading and trailing whitespace.
    """
    value = str(value)
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value

def clean_mic_audio(input_audio):
    # Apply noise reduction
    output_audio = input_audio.replace(".ogg", "_clean.ogg")
    command = [
        'ffmpeg', '-y', '-i', input_audio,
        '-af', 'afftdn=nr=40:nt=w',  # Adjust noise reduction settings as needed
        output_audio
    ]
    subprocess.run(command)
    return output_audio



def combine_screen_system(folder_name, screen_file, system_file):
    output_file = os.path.join(folder_name, f"screen_system.mp4")
    command = [
        'ffmpeg',
        '-i', screen_file,
        '-i', system_file,
        '-c:v', 'libx264',
        '-crf', '23',
        '-preset', 'veryfast',
        '-c:a', 'copy',
        '-shortest', output_file
    ]
    subprocess.run(command)
    return output_file


def combine_all(folder_name, screen_system_file, mic_file):
    output_file = os.path.join(folder_name, f"all.mp4")
    command = [
        'ffmpeg',
        '-i', screen_system_file,  # Input file with system audio
        '-i', mic_file,  # Input file with microphone audio
        '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=shortest,volume=2.0[a]',  # Mix audio streams
        '-map', '0:v',  # Map video from first input
        '-map', '[a]',  # Map mixed audio
        '-c:v', 'copy',  # Copy the video stream as is
        '-c:a', 'aac',  # Re-encode audio to AAC
        '-b:a', '128k',  # Bitrate for the audio
        output_file  # Output file
    ]
    subprocess.run(command)
    return output_file

def generate_waveform(input_audio, color="Blue"):
    output = input_audio.replace(".ogg", "_waves.mp4")
    subprocess.run([
        'ffmpeg', '-y', '-i', input_audio,
        #  '-filter_complex', f'showwaves=s=400x400:mode=cline:colors={color}',
        '-filter_complex', f'showwaves=s=200x400:mode=cline:colors={color},crop=200:200',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        output
    ])
    return output


def combine_screen_waves(folder_name, screen_file, mic_waves, system_waves):
    margin = 30
    wave_size = 100
    output_file = os.path.join(folder_name, "all_waves.mp4")

    # Calculate new height for the screen video
    output_resolution=(1920, 1080)
    new_height = output_resolution[1] - 3 * margin - wave_size
    # Calculate new width while maintaining the aspect ratio
    # Assuming the aspect ratio of the original video is 16:9
    aspect_ratio = 16 / 9
    new_width = int(new_height * aspect_ratio)

    subprocess.run([
        'ffmpeg', '-y',
        '-i', str(screen_file),
        '-i', str(mic_waves),
        '-i', str(system_waves),
        '-i', 'circle_mask.png',
        '-filter_complex',
        f'[1:v]scale={wave_size}x{wave_size},format=yuva420p[mic_waves];' +
        f'[2:v]scale={wave_size}x{wave_size},format=yuva420p[sys_waves];' +
        '[mic_waves][3:v]alphamerge[mic_masked];' +
        '[sys_waves][3:v]alphamerge[sys_masked];' +
        f'[0:v]scale={new_width}x{new_height}[scaled_screen];' +
        f'color=c=black:s={output_resolution[0]}x{output_resolution[1]}[bg];' +
        f'[bg][scaled_screen]overlay=(W-w)/2:{margin}[screen_on_bg];' +
        f'[screen_on_bg][mic_masked]overlay=shortest=1:x={margin}:y=main_h-overlay_h-{margin}[with_mic];' +
        f'[with_mic][sys_masked]overlay=shortest=1:x=W-w-{margin}:y=main_h-overlay_h-{margin},format=yuv420p[v];' +
        '[1:a][2:a]amix=inputs=2:duration=shortest:normalize=0,volume=2.0[a]',
        '-map', '[v]', '-map', '[a]',
        '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '128k',
        str(output_file)
    ])
    return output_file

