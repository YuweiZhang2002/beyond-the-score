"""Reconstruct two saved preference requests and their exact input-frame replays.

This is an offline evidence export. It makes no model or network calls.
"""
import argparse
import io
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image
from build_positive_evidence import read, request_hash, sha

ROOT = Path(__file__).resolve().parents[1]
RUN = Path('outputs/astra/gpt6_astra_ca_low_ood_full_ca_20260916')
SELECTION = {
    'ambiguity-banana': ['2a17c406-2c21-49e0-9014-47bca47e93a6', 'a9c66932-a68f-4515-98f2-13f09dd14030'],
    'ambiguity-pebbles': ['7df7139d-3d6f-4720-9d1b-185e75dd9b41', 'd43b6193-eb56-4dd6-865e-3c60bcefaf6c'],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--openwvm', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    base = args.openwvm.resolve()
    run = base / RUN
    config = read(run / 'run_config.json')
    index = {row['id']: row for row in read(base / 'outputs/astra/zero_shot_kendall_failure_report_20260919/trajectories.json')}
    sizes_path = ROOT / 'data/media-dimensions.json'
    sizes = read(sizes_path)
    evidence = {'schema_version': 1, 'run': str(RUN), 'stage': 'quality_preference',
                'selection': 'Two existing zero-shot disagreements illustrating the boundary between suboptimal and failure labels.',
                'paid_model_calls': 0, 'cases': []}
    for slug, ids in SELECTION.items():
        rows = [index[ident] for ident in ids]
        assert rows[0]['task'] == rows[1]['task'] and rows[0]['source'] == rows[1]['source']
        predictions_path = run / 'quality_preference' / rows[0]['source'] / 'predictions.jsonl'
        matches = [(i, json.loads(line)) for i, line in enumerate(predictions_path.read_text().splitlines(), 1)
                   if json.loads(line)['display_order'] == dict(zip('AB', ids))]
        assert len(matches) == 1
        line, prediction = matches[0]
        assert prediction['preference_pred'] == 0
        response_path = run / 'responses' / (prediction['request_sha256'] + '.json')
        response = read(response_path)
        raw = response['response']
        assert response['api_format'] == 'responses' and raw['status'] == 'completed'
        original = ''.join(p['text'] for item in raw['output'] if item['type'] == 'message'
                           for p in item['content'] if p['type'] == 'output_text')
        assert json.loads(original) == prediction['model_answer']
        case = {'slug': slug, 'task': rows[0]['task'], 'source': rows[0]['source'],
                'prediction_file': str(predictions_path.relative_to(base)), 'prediction_file_sha256': sha(predictions_path.read_bytes()),
                'line': line, 'prediction': prediction, 'response_file': str(response_path.relative_to(base)),
                'response_file_sha256': sha(response_path.read_bytes()), 'original_final_output': original,
                'prompt': response['prompt'], 'trajectories': []}
        videos = []
        for display, row in zip('AB', rows):
            path = Path(row['npz_path'])
            with np.load(path) as archive:
                frames = archive['frames']
            assert len(frames) == 32 and row['frame_indices'] == [0, 4, 9, 13, 18, 22, 27, 31]
            directory = ROOT / 'assets/case-studies' / f'{slug}-{display.lower()}-frames'
            if not args.check:
                directory.mkdir(parents=True, exist_ok=True)
            encoded, entries = [], []
            for i, stored_index in enumerate(row['frame_indices']):
                image = Image.fromarray(frames[stored_index]).convert('RGB')
                image.thumbnail((512, 512))
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=90)
                data = buffer.getvalue()
                encoded.append(data)
                target = directory / f'frame-{i:02}.jpg'
                if args.check:
                    assert target.read_bytes() == data
                else:
                    target.write_bytes(data)
                entries.append({'path': str(target.relative_to(ROOT)), 'stored_index': stored_index, 'sha256': sha(data)})
            videos.append(encoded)
            poster = directory.with_name(f'{slug}-{display.lower()}.jpg')
            video = directory.with_name(f'{slug}-{display.lower()}.mp4')
            if not args.check:
                shutil.copyfile(directory / 'frame-07.jpg', poster)
                subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', '1', '-i', str(directory / 'frame-%02d.jpg'),
                                '-an', '-c:v', 'libx264', '-threads', '2', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '24', '-movflags', '+faststart', str(video)], check=True)
            assert poster.read_bytes() == encoded[-1]
            for item in [str(poster.relative_to(ROOT))] + [entry['path'] for entry in entries]:
                size = list(Image.open(ROOT / item).size)
                if args.check:
                    assert sizes[item] == size
                else:
                    sizes[item] = size
            case['trajectories'].append({'display': display, 'id': row['id'], 'quality_label': row['quality'],
                'npz_path': str(path), 'npz_sha256': sha(path.read_bytes()), 'input_frames': entries,
                'poster': str(poster.relative_to(ROOT)), 'poster_sha256': sha(poster.read_bytes()),
                'video': str(video.relative_to(ROOT)), 'video_sha256': sha(video.read_bytes())})
        reconstructed = request_hash(config, response['prompt'], videos)
        assert reconstructed == prediction['request_sha256'] == response['request_sha256']
        assert response['video_frame_counts'] == [8, 8]
        case['request_sha256_reconstructed'] = reconstructed
        chosen = prediction['metadata']['chosen_metadata']
        case['reference_winner'] = next(t['display'] for t in case['trajectories'] if t['id'] == chosen['id'])
        for trajectory in case['trajectories']:
            meta = next(m for m in prediction['metadata'].values() if m['id'] == trajectory['id'])
            assert trajectory['quality_label'] == meta['quality_label']
        assert prediction['model_answer']['winner'] != case['reference_winner']
        evidence['cases'].append(case)
    target = ROOT / 'data/rbm-quality-ambiguity-cases.json'
    if args.check:
        assert read(target) == evidence
    else:
        target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
        sizes_path.write_text(json.dumps(sizes, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'reconstructed_requests': 2, 'exact_input_images': 32, 'paid_model_calls': 0, 'mode': 'check' if args.check else 'build'}))


if __name__ == '__main__':
    main()
