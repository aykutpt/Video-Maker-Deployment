"""Simple video generator from a single image using moviepy.

Produces a Ken Burns-style pan & zoom video sized for Etsy previews (HD default).

Requirements: moviepy and a system ffmpeg binary installed and on PATH.
"""
import math
import os
from moviepy.editor import ImageClip, ColorClip, CompositeVideoClip, AudioFileClip
from moviepy.video.fx.all import fadein, fadeout


def create_video_from_image(input_image_path: str,
                            output_video_path: str,
                            duration: float = 12.0,
                            fps: int = 30,
                            resolution=(1920, 1080),
                            zoom_scale: float = 1.15):
    """Create a high-quality MP4 from a single image.

    - input_image_path: path to source image
    - output_video_path: path to write mp4
    - duration: seconds (10-15 recommended)
    - fps: frames per second
    - resolution: (w,h) of output video
    - zoom_scale: how much larger the image is scaled to allow pan/zoom (1.0 = no extra room)
    """
    res_w, res_h = resolution

    img = ImageClip(input_image_path)
    # Ensure image is large enough to fill the frame; scale up if necessary
    scale_fit = max(res_w / img.w, res_h / img.h)
    base_scale = scale_fit * zoom_scale
    img = img.resize(base_scale)

    # Smooth pan: move image within the frame over time
    max_dx = max(0, img.w - res_w)
    max_dy = max(0, img.h - res_h)

    def pos(t):
        # Use a smooth sinusoidal easing to move between 0 and max (halfway and back)
        # start near top-left, move toward bottom-right slightly
        progress = t / max(duration, 1e-6)
        ease = 0.5 * (1 - math.cos(math.pi * progress))  # 0 -> 1
        x = - (0.2 * max_dx) - (0.6 * max_dx) * ease  # shift a bit
        y = - (0.2 * max_dy) - (0.6 * max_dy) * ease
        return (x, y)

    moving = img.set_position(pos).set_duration(duration)

    # Background (black) to pad if image doesn't perfectly fit
    bg = ColorClip(size=resolution, color=(0, 0, 0)).set_duration(duration)

    clip = CompositeVideoClip([bg, moving], size=resolution)

    # add short fade in/out for polish
    clip = fadein(clip, 0.6)
    clip = fadeout(clip, 0.6)

    # Write high-quality mp4 (libx264). Square format for Etsy - OPTIMIZED
    codec = 'libx264'
    bitrate = "2500k"  # Çok düşük bitrate (hızlı encoding)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_video_path) or '.', exist_ok=True)

    clip.write_videofile(output_video_path,
                         fps=15,  # Daha düşük FPS (çoğu device'de 15 fps yeterli)
                         codec=codec,
                         bitrate=bitrate,
                         audio=False,
                         threads=4,
                         preset='ultrafast',  # Maksimum hız
                         verbose=False,
                         logger=None)

    clip.close()
    img.close()
    bg.close()
    moving.close()
    return output_video_path
