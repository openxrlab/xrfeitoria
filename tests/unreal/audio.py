"""
>>> python -m tests.unreal.audio
"""

from pathlib import Path

from xrfeitoria.data_structure.models import RenderPass
from xrfeitoria.utils import setup_logger

from ..config import assets_path
from ..utils import __timer__, _init_unreal

root = Path(__file__).resolve().parents[2]
output_path = root / 'output' / Path(__file__).relative_to(root).with_suffix('')
seq_name = 'seq_audio'
wave_path = Path(assets_path['audio'])


def audio_test(debug: bool = False, background: bool = False):
    logger = setup_logger(level='DEBUG' if debug else 'INFO')
    with _init_unreal(background=background) as xf_runner:
        default_level = '/Game/Levels/Default'
        level_template = '/Game/Levels/Playground'
        level_path = '/Game/Levels/SequenceTestAudio'

        # duplicate level
        xf_runner.utils.open_level(default_level)
        xf_runner.utils.duplicate_asset(level_template, level_path, replace=True)

        with __timer__('create seq'):
            seq = xf_runner.sequence(level=level_path, seq_name=seq_name, seq_length=60, replace=True)
        with __timer__('importing audio'):
            audio_asset_path = xf_runner.utils.import_asset(path=wave_path, replace=True)
            audio_asset_path2 = xf_runner.utils.import_asset(path=wave_path.with_name('segment_1.WAV'), replace=True)
            seq.add_audio(audio_asset_path=audio_asset_path)
            seq.add_audio(audio_asset_path=audio_asset_path2, start_frame=30)
        with __timer__('add to renderer'):
            seq.spawn_camera()
            seq.add_to_renderer(
                output_path=output_path,
                resolution=(640, 360),
                render_passes=[RenderPass('img', 'png')],
                export_audio=True,
            )
        with __timer__('save seq'):
            seq.save()
            seq.close()
        with __timer__('render seq'):
            xf_runner.render()

    logger.info('🎉 [bold green]audio test passed!')


if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('--debug', action='store_true')
    args.add_argument('--background', '-b', action='store_true')
    args = args.parse_args()

    audio_test(debug=args.debug, background=args.background)
