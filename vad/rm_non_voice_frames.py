# -*- coding: utf-8 -*-
"""
Description : Remove non-voice frames in audios.
Authors     : lihp
CreateDate  : 2022/1/24
Notes       :
    1) You need to install `webrtcvad` and `pydub`.
    2) For `webrtcvad` only accepts 16-bit (sample_width=2) mono (channels=1) PCM audio sampled at 8000, 16000,
    32000 or 48000 Hz, audios that do not meet these conditions will be modified before VAD.
"""
import os
import sys
import time
import webrtcvad

sys.path.insert(0, os.getcwd())
from tqdm import tqdm
from pydub import AudioSegment
from argparse import ArgumentParser
from vad.vad import frame_generator


def rm_blank(vad, audio_path, out_path, frame_dur_ms=30):
    """Remove non-voice frames of an audio.
    Args:
        vad: An instance of webrtcvad.Vad()
        audio_path: The path to an audio.
        out_path: The path to output the result audio.
        frame_dur_ms: Milliseconds per frame.
    Returns:
        rmd: The number of removed frames.
    """
    audio = AudioSegment.from_file(audio_path)
    sample_rate = audio.frame_rate
    sample_width = audio.sample_width
    channels = audio.channels

    # The WebRTC VAD only accepts 16-bit (sample_width=2) mono (channels=1) audio,
    # sampled at 8000, 16000, 32000 or 48000 Hz.
    # assert sample_rate in [8000, 16000, 32000, 48000]
    # assert sample_width == 2
    # assert channels == 1
    reset_audio = False
    if sample_rate not in [8000, 16000, 32000, 48000]:
        sample_rate = 16000
        reset_audio = True
    if sample_width != 2:
        sample_width = 2
        reset_audio = True
    if channels != 2:
        channels = 1
        reset_audio = True
    if reset_audio:
        audio = audio.set_frame_rate(sample_rate)
        audio = audio.set_sample_width(sample_width)
        audio = audio.set_channels(channels)

    raw = audio.raw_data
    frames = frame_generator(frame_dur_ms, raw, sample_rate)
    frames = list(frames)
    labels = [vad.is_speech(frame.bytes, sample_rate) for frame in frames]
    rmd = 0
    if sum(labels) == labels.__len__():
        audio.export(out_path)
        return rmd
    else:
        results = [frame.bytes for label, frame in zip(labels, frames) if label]
        out_raw = b''.join(results)
        out_audio = AudioSegment(out_raw,
                                 sample_width=sample_width,
                                 frame_rate=sample_rate,
                                 channels=channels)
        out_audio.export(out_path)
        rmd = frames.__len__() - results.__len__()
        return rmd


def rm_blank_batch(vad, in_dir, out_dir, postfixes: list):
    """Remove non-voice frames of audios in the given directory.
    Args:
        vad: An instance of webrtcvad.Vad()
        in_dir: The directory contains audios to be reset.
        out_dir: The directory to output the reset audios.
        postfixes: The program will list audios to be reset by the provided `postfixes`.
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
        out_path = os.path.join(out_dir, name)
        out_audios.append(out_path)

    # Remove non-voice frames of audios
    os.makedirs(out_dir, exist_ok=True)

    st = time.time()
    fail = 0
    changed = 0
    for ap, oap in zip(tqdm(audios), out_audios):
        try:
            rmd = rm_blank(vad, ap, oap)
            if rmd > 0:
                # print(ap, '-->', oap)
                changed += 1
        except Exception as e:
            print(f"[WARNING] {e} {ap}")
            fail += 1
    print(f"[INFO] Took {round(time.time() - st, 3)} seconds processing {len(audios) - fail} audios. "
          f"{changed} audios were changed.")
    if fail > 0:
        print(f"[WARNING] {fail} audios cannot be processed.")


if __name__ == '__main__':
    """Notes:
    1) You can process one audio (provide --audio_path and --out_path) or a batch of audios (provide --audio_dir, --out_dir and --audio_postfixes).
    2) --audio_postfixes is a list. You can input one or more postfixes, like `--audio_postfixes mp3,wav`.
    """
    parser = ArgumentParser()
    parser.add_argument("--audio_path", "-ap", type=str, help="The path to the audio to be reset.")
    parser.add_argument("--out_path", "-op", type=str, help="Where to output the reset audio.")
    parser.add_argument("--audio_dir", "-ad", type=str, help="The directory contains audios to be reset.")
    parser.add_argument("--out_dir", "-od", type=str, help="The directory to output the reset audios.")
    parser.add_argument('--audio_postfixes', '-pf', type=str, nargs='+', help='Postfixes of the audios.')

    args = parser.parse_args()

    # mode, an integer between 0 and 3.
    # 0 is the least aggressive about filtering out non-speech, 3 is the most aggressive.
    vad = webrtcvad.Vad(mode=1)

    if args.audio_path:  # Process one audio
        assert args.out_path, "--out_path must be provided."
        rm_blank(vad, args.audio_path, args.out_path)
    elif args.audio_dir:  # Process a batch of audios
        assert args.out_dir, "--out_dir must be provided."
        assert args.audio_postfixes, "--audio_postfixes (.mp3, .wav, etc.)must be provided."
        rm_blank_batch(vad, args.audio_dir, args.out_dir, args.audio_postfixes)
