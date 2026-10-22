"""Audit saved RBM judgments and build exact-input replays, entirely offline.

No model client is instantiated. Request hashes are reconstructed from the original
NPZ frames, recorded prompts, and recorded API settings before media is written.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RUNS = {
    'astra': 'outputs/astra/gpt6_astra_ca_low_ood_full_ca_20260916',
    'deepseek': 'outputs/astra/deepseek_v41_flash_max_ood_zero_shot_chat_20260920/ranking_preference_w128',
}
SELECTION = [
    ('ranking-drawer', 'policy_ranking', ['1d035ec5-5127-4af9-9cca-fe214830d670', '9726c08b-3b48-495a-9aae-f90cebd83330']),
    ('ranking-banana', 'policy_ranking', ['503f40f8-85e6-4b77-9d30-db39c92de0d8', '2a17c406-2c21-49e0-9014-47bca47e93a6']),
    ('preference-button', 'quality_preference', ['e46b4860-568f-4d5c-8e41-832010b82c73', 'c1fec2fd-7a48-43e1-ac2e-0e10e4813fc4']),
    ('preference-red-bin', 'quality_preference', ['d6ae8dbb-e361-4c65-9845-9d869c21324f', 'd028b5d8-702f-4f0f-b7f5-7c2273b9c9c3']),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def digest(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())


def request_hash(config, prompt, videos):
    """Reproduce the frozen client's serialization, without importing its API code."""
    parts = [{'type': 'text', 'text': prompt}]
    for name, frames in zip('AB', videos):
        parts.append({'type': 'text', 'text': f'Video {name}: frames follow in chronological order.'})
        for i, frame in enumerate(frames):
            parts.extend([{'type': 'text', 'text': f'{name}, frame {i + 1}'},
                          {'type': 'image', 'url': 'data:image/jpeg;base64,' + base64.b64encode(frame).decode('ascii')}])
    if config['api_format'] == 'responses':
        content = [({'type': 'input_text', 'text': p['text']} if p['type'] == 'text' else
                    {'type': 'input_image', 'image_url': p['url'], 'detail': config['image_detail']}) for p in parts]
        payload = {'model': config['model'], 'input': [{'role': 'user', 'content': content}],
                   'max_output_tokens': config['max_output_tokens'], 'store': False,
                   'text': {'format': {'type': config['json_mode']}}, 'reasoning': {'effort': config['reasoning_effort']}}
    else:
        content = [({'type': 'text', 'text': p['text']} if p['type'] == 'text' else
                    {'type': 'image_url', 'image_url': {'url': p['url'], 'detail': config['image_detail']}}) for p in parts]
        payload = {'model': config['model'], 'messages': [{'role': 'user', 'content': content}],
                   'max_tokens': config['max_output_tokens'], 'response_format': {'type': config['json_mode']},
                   'reasoning_effort': config['reasoning_effort']}
    return digest({'url': config['base_url'], 'format': config['api_format'], 'payload': payload})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--openwvm', type=Path, default=ROOT.parent / 'OpenWVM')
    parser.add_argument('--check', action='store_true', help='Verify saved evidence and media without writing them')
    args = parser.parse_args()
    base = args.openwvm.resolve()
    source_files = {}

    def source(path):
        name = str(path.relative_to(base)) if path.is_relative_to(base) else str(path)
        source_files[name] = sha(path.read_bytes())
        return name

    index_path = base / 'outputs/astra/zero_shot_kendall_failure_report_20260919/trajectories.json'
    index = read(index_path)
    source(index_path)
    assert len(index) == 567
    lookup = {r['id']: r for r in index}
    configs, statuses, records, manifests = {}, {}, {}, []
    for model, run in RUNS.items():
        root = base / run
        configs[model] = read(root / 'run_config.json')
        source(root / 'run_config.json')
        summary = read(root / 'summary.json')
        source(root / 'summary.json')
        assert summary['status'] == 'complete'
        assert all(s['status'] == 'complete' and s['completed_samples'] == s['expected_samples'] for s in summary['stages'].values())
        statuses[model] = {'status': summary['status'], 'stages': len(summary['stages']),
                           'completed_samples': sum(s['completed_samples'] for s in summary['stages'].values())}
        records[model] = {}
        for stage in ['policy_ranking', 'quality_preference']:
            records[model][stage] = []
            for path in sorted((root / stage).glob('*/predictions.jsonl')):
                name = source(path)
                for line, text in enumerate(path.read_text().splitlines(), 1):
                    records[model][stage].append((path.parent.name, line, name, json.loads(text)))
            assert len(records[model][stage]) == (567 if stage == 'policy_ranking' else 1192)
    assert configs['astra']['reference'] == configs['deepseek']['reference']
    for stage in ['policy_ranking', 'quality_preference']:
        for path in sorted((base / RUNS['astra'] / stage).glob('*/sample_indices.json')):
            other = base / RUNS['deepseek'] / path.relative_to(base / RUNS['astra'])
            assert path.read_bytes() == other.read_bytes()
            manifests.append({'astra': source(path), 'deepseek': source(other), 'identical': True})
    assert len(manifests) == 12
    evidence = {'schema_version': 1, 'selection': 'Post-hoc illustrative cases; no new evaluations or aggregate metrics.',
                'source_root': str(base), 'runs': RUNS, 'completion': statuses,
                'protocol': {'max_frames': 8, 'stored_frame_indices': [0, 4, 9, 13, 18, 22, 27, 31],
                             'jpeg_quality': 90, 'max_image_side': 512, 'seed': 44,
                             'icl': False, 'labels_sent_to_model': False,
                             'reference_quality_order': ['failure', 'suboptimal', 'successful'],
                             'reference_code': configs['astra']['reference'],
                             'matching_scope': 'Task, trajectories, reference labels, prompts, encoded input images, sample selection, A/B display order, and metric implementation.',
                             'configuration_differences': {m: {k: c[k] for k in ['model', 'api_format', 'reasoning_effort', 'max_output_tokens', 'workers', 'answer_retries']} for m, c in configs.items()},
                             'caveat': 'Compute budgets and API transports are not matched; returned model names are provider-reported, not independently authenticated. No swapped-order rerun is available.'},
                'sample_manifests': manifests, 'missing': ['No matched per-example Robometer output was used.'], 'cases': []}
    dimensions_path = ROOT / 'data/media-dimensions.json'
    dimensions = read(dimensions_path)
    for slug, stage, ids in SELECTION:
        case = {'slug': slug, 'stage': stage, 'task': lookup[ids[0]]['task'], 'source': lookup[ids[0]]['source'],
                'source_name': lookup[ids[0]]['source_name'], 'trajectories': [], 'judgments': {}}
        videos = []
        for ident, label in zip(ids, 'AB'):
            row = lookup[ident]
            assert row['task'] == case['task'] and row['source'] == case['source']
            assert row['frame_indices'] == [0, 4, 9, 13, 18, 22, 27, 31]
            path = Path(row['npz_path'])
            source(path)
            with np.load(path) as archive:
                frames = archive['frames']
            assert len(frames) == 32
            encoded = []
            for i in row['frame_indices']:
                image = Image.fromarray(frames[i]).convert('RGB')
                image.thumbnail((512, 512))
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=90)
                encoded.append(buffer.getvalue())
            videos.append(encoded)
            directory = ROOT / 'assets/case-studies' / f'{slug}-{label.lower()}-frames'
            if not args.check:
                directory.mkdir(parents=True, exist_ok=True)
            input_frames = []
            for i, data in enumerate(encoded):
                target = directory / f'frame-{i:02}.jpg'
                if args.check:
                    assert target.read_bytes() == data
                else:
                    target.write_bytes(data)
                input_frames.append({'path': str(target.relative_to(ROOT)), 'stored_index': row['frame_indices'][i], 'sha256': sha(data)})
            poster = directory.with_name(f'{slug}-{label.lower()}.jpg')
            video = directory.with_name(f'{slug}-{label.lower()}.mp4')
            if not args.check:
                shutil.copyfile(directory / 'frame-07.jpg', poster)
                subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', '1', '-i', str(directory / 'frame-%02d.jpg'),
                                '-an', '-c:v', 'libx264', '-threads', '2', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '24', '-movflags', '+faststart', str(video)], check=True)
            assert poster.read_bytes() == encoded[-1]
            size = list(Image.open(poster).size)
            if args.check:
                assert dimensions[str(poster.relative_to(ROOT))] == size
            else:
                dimensions[str(poster.relative_to(ROOT))] = size
                for item in input_frames:
                    dimensions[item['path']] = size
            case['trajectories'].append({'display': label, 'id': ident, 'audit_key': row['key'], 'quality_label': row['quality'],
                                         'npz_path': str(path), 'npz_sha256': sha(path.read_bytes()), 'input_frames': input_frames,
                                         'poster': str(poster.relative_to(ROOT)), 'poster_sha256': sha(poster.read_bytes()),
                                         'video': str(video.relative_to(ROOT)), 'video_sha256': sha(video.read_bytes()),
                                         'replay': {'input_frames': 8, 'seconds_per_input_frame': 1, 'duration_seconds': 8, 'encoded_fps': 24, 'continuous_original_video': False}})
        for model in RUNS:
            picked = [r for r in records[model][stage] if r[0] == case['source'] and
                      (r[3].get('id') in ids if stage == 'policy_ranking' else r[3]['display_order'] == dict(zip('AB', ids)))]
            if stage == 'policy_ranking':
                picked.sort(key=lambda r: ids.index(r[3]['id']))
            assert len(picked) == (2 if stage == 'policy_ranking' else 1)
            judgments = []
            for _, line, prediction_file, prediction in picked:
                if stage == 'policy_ranking':
                    trajectory = case['trajectories'][ids.index(prediction['id'])]
                    assert prediction['quality_label'] == trajectory['quality_label']
                response_path = base / RUNS[model] / 'responses' / (prediction['request_sha256'] + '.json')
                response = read(response_path)
                raw = response['response']
                if response['api_format'] == 'responses':
                    assert raw['status'] == 'completed'
                    output = ''.join(p['text'] for item in raw['output'] if item['type'] == 'message' for p in item['content'] if p['type'] == 'output_text')
                else:
                    assert raw['choices'][0]['finish_reason'] == 'stop'
                    output = raw['choices'][0]['message']['content']
                assert json.loads(output) == prediction['model_answer']
                actual_videos = [videos[ids.index(prediction['id'])]] if stage == 'policy_ranking' else videos
                assert response['video_frame_counts'] == list(map(len, actual_videos))
                reconstructed = request_hash(configs[model], response['prompt'], actual_videos)
                assert reconstructed == prediction['request_sha256'] == response['request_sha256'], (slug, model, reconstructed)
                judgments.append({'prediction_file': prediction_file, 'line': line, 'prediction': prediction,
                                  'response_file': source(response_path), 'response_id': raw['id'],
                                  'requested_model': response['requested_model'], 'returned_model': raw['model'],
                                  'requested_effort': configs[model]['reasoning_effort'], 'returned_reasoning': raw.get('reasoning'),
                                  'prompt': response['prompt'], 'prompt_sha256': sha(response['prompt'].encode()),
                                  'original_final_output': output, 'request_sha256_reconstructed': reconstructed})
            case['judgments'][model] = judgments
        a, d = case['judgments']['astra'], case['judgments']['deepseek']
        for x, y in zip(a, d):
            assert x['prompt'] == y['prompt']
            for key in (['id', 'task', 'quality_label', 'metadata'] if stage == 'policy_ranking' else ['task', 'metadata', 'display_order', 'preference_labels']):
                assert x['prediction'][key] == y['prediction'][key]
        if stage == 'policy_ranking':
            order = evidence['protocol']['reference_quality_order']
            assert order.index(case['trajectories'][0]['quality_label']) > order.index(case['trajectories'][1]['quality_label'])
            assert a[0]['prediction']['model_answer']['score'] > a[1]['prediction']['model_answer']['score']
            assert d[0]['prediction']['model_answer']['score'] < d[1]['prediction']['model_answer']['score']
            case['reference_order'] = ['A', 'B']
            case['display_note'] = 'A/B are article labels only; each independent scoring request contains one video named A.'
        else:
            p = a[0]['prediction']
            chosen = p['metadata']['chosen_metadata']['id']
            rejected = p['metadata']['rejected_metadata']['id']
            swapped = bool(int(digest([44, chosen, rejected])[:8], 16) % 2)
            assert p['display_order'] == dict(zip('AB', [rejected, chosen] if swapped else [chosen, rejected]))
            for trajectory in case['trajectories']:
                meta = p['metadata']['chosen_metadata'] if trajectory['id'] == chosen else p['metadata']['rejected_metadata']
                assert trajectory['quality_label'] == meta['quality_label']
            case['reference_winner'] = 'B' if swapped else 'A'
            assert p['model_answer']['winner'] == case['reference_winner'] and p['preference_pred'] == 1.0
            assert d[0]['prediction']['model_answer']['winner'] != case['reference_winner'] and d[0]['prediction']['preference_pred'] == 0.0
            case['display_note'] = 'A/B are the actual recorded input order for both models, checked against seed 44; no swapped-order repeat.'
        evidence['cases'].append(case)
    evidence['source_files_sha256'] = source_files
    target = ROOT / 'data/rbm-positive-cases.json'
    if args.check:
        assert read(target) == evidence, 'Saved positive-case evidence differs from original records'
    else:
        target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
        dimensions_path.write_text(json.dumps(dimensions, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'cases': len(evidence['cases']), 'reconstructed_requests': 12, 'exact_input_images': 64,
                      'matching_sample_manifests': len(manifests), 'paid_model_calls': 0, 'mode': 'check' if args.check else 'build'}, indent=2))


if __name__ == '__main__':
    main()
