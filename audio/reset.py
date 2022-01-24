# -*- coding: utf-8 -*-
"""
Description : Reset sample rate, sample width, etc of audios.
Authors     : wapping
CreateDate  : 2022/1/24
"""
import os
import sys
import time
import pydub
from tqdm import tqdm
from argparse import ArgumentParser


def reset(in_path, out_path, sample_rate, sample_width, channels, format):
    """Reset sample rate, sample width, the number of channels and format of an audio.
    Args:
        in_path: The audio path.
        out_path: Where to output the reset audio.
        sample_rate: The target sample rate.
        sample_width: The target sample width.
        channels: The number of channels.
        format: 'mp3', 'wav', 'raw', 'ogg' or other ffmpeg/avconv supported files
    """
    audio = pydub.AudioSegment.from_file(in_path)
    if sample_rate:
        audio.set_frame_rate(sample_rate)
    if sample_width:
        audio.set_sample_width(sample_width)
    if channels:
        audio.set_channels(channels)
    if format:
        audio.export(out_path, format)
    else:
        audio.export(out_path)


def reset_batch(in_dir, out_dir, postfixes: list, sample_rate, sample_width, channels, format):
    """Reset sample rate, sample width, the number of channels and format of an audio.
    Args:
        in_dir: The directory contains audios to be reset.
        out_dir: The directory to output the reset audios.
        postfixes: The program will list audios to be reset by the provided `postfixes`.
        sample_rate: The target sample rate.
        sample_width: The target sample width.
        channels: The number of channels.
        format: 'mp3', 'wav', 'raw', 'ogg' or other ffmpeg/avconv supported files
    """
    # List the audios
    files = os.listdir(in_dir)
    audios = []
    for f in files:
        for p in postfixes:
            if f.endswith(p):
                audios.append(os.path.join(in_dir, f))
                break
    if len(audios) == 0:
        print(f"[INFO] No audio was found.")
        sys.exit(0)
    print(f"[INFO] {len(audios)} audios were found.")

    # Create paths to output audios
    out_audios = []
    for fp in audios:
        name = os.path.split(fp)[1]
        end = name.rfind('.')
        prefix = name[:end] if end else name
        if format:
            out_path = os.path.join(out_dir, prefix + "." + format)
        else:
            out_path = os.path.join(out_dir, name)
        out_audios.append(out_path)

    # Reset audios
    os.makedirs(out_dir, exist_ok=True)

    st = time.time()
    fail = 0
    for ap, oap in zip(tqdm(audios), out_audios):
        try:
            reset(ap, oap, sample_rate, sample_width, channels, format)
        except Exception as e:
            print(f"[WARNING] {e} {ap}")
            fail += 1
    print(f"[INFO] Took {round(time.time() - st, 3)} seconds resetting {len(audios) - fail} audios.")
    if fail > 0:
        print(f"[WARNING] {fail} audios cannot be reset.")


if __name__ == '__main__':
    """Notes:
    1) You can reset one audio (provide --audio_path and --out_path) or a batch of audios (provide --audio_dir, --out_dir and --audio_postfixes).
    2) --audio_postfixes is a list. You can input one or more postfixes, like `--audio_postfixes mp3,wav`.
    """
    parser = ArgumentParser()
    parser.add_argument("--audio_path", "-ap", type=str, help="The path to the audio to be reset.")
    parser.add_argument("--out_path", "-op", type=str, help="Where to output the reset audio.")
    parser.add_argument("--audio_dir", "-ad", type=str, help="The directory contains audios to be reset.")
    parser.add_argument("--out_dir", "-od", type=str, help="The directory to output the reset audios.")
    parser.add_argument('--audio_postfixes', '-pf', type=str, nargs='+', help='Postfixes of the audios.')
    parser.add_argument("--sample_rate", "-sr", type=int, help="The target sample rate.")
    parser.add_argument("--sample_width", "-sw", type=int, help="The target sample width.")
    parser.add_argument("--channels", "-c", type=int, help="The number of channels.")
    parser.add_argument("--format", "-f", type=str, help="'mp3', 'wav', 'raw', 'ogg' or other ffmpeg/avconv supported files.")

    args = parser.parse_args()

    if args.audio_path:     # Reset one audio
        assert args.out_path, "--out_path must be provided."
        reset(args.audio_path, args.out_path, args.sample_rate, args.sample_width, args.channels, args.format)
    elif args.audio_dir:    # Reset a batch of audios
        assert args.out_dir, "--out_dir must be provided."
        assert args.audio_postfixes, "--audio_postfixes (.mp3, .wav, etc.)must be provided."
        reset_batch(args.audio_dir, args.out_dir, args.audio_postfixes, args.sample_rate, args.sample_width, args.channels, args.format)
