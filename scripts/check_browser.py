"""Check the bilingual local preview with Playwright; save review screenshots.

Start `python3 scripts/serve_preview.py` in the repository first.
Requires the Python Playwright package and its Chromium browser.
"""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:9879')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=['--no-sandbox'])
        for language, filename in [('zh', 'index.html'), ('en', 'en.html')]:
            for device, width in [('desktop', 1440), ('mobile', 390)]:
                page = browser.new_page(viewport={'width': width, 'height': 1000 if device == 'desktop' else 844}, reduced_motion='reduce')
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('response', lambda response: errors.append(f'{response.status} {response.url}') if response.status >= 400 else None)
                page.goto(f'{args.url}/{filename}', wait_until='networkidle')
                page.add_style_tag(content='html{scroll-behavior:auto!important}')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (language, device, 'page overflow')
                assert page.eval_on_selector_all('.positive-case .table-scroll', 'tables=>tables.every(t=>t.scrollWidth<=t.clientWidth)'), (language, device, 'positive score table overflow')
                page.eval_on_selector_all('img', "images => images.forEach(image => image.loading = 'eager')")
                assert page.eval_on_selector_all('img:not([src])', 'images => images.map(i=>i.id)') == ['expanded-figure']
                page.wait_for_function("[...document.images].filter(i=>i.getAttribute('src')).every(image => image.complete && image.naturalWidth > 0)")
                page.locator('[data-zoom]').first.click()
                page.wait_for_function("document.getElementById('expanded-figure').naturalWidth > 0")
                assert page.locator('#figure-modal').evaluate('d => d.open')
                page.locator('#close-figure').click()
                # All 29 video resources must load metadata; source elements and direct src are both covered.
                media = page.eval_on_selector_all('video', '''videos => Promise.all(videos.map(video => new Promise((resolve, reject) => {
                    video.addEventListener('loadedmetadata', () => resolve({src:video.currentSrc, duration:video.duration, width:video.videoWidth, height:video.videoHeight}), {once:true});
                    video.addEventListener('error', () => reject(new Error(video.currentSrc)), {once:true});
                    video.load();
                })))''')
                assert len(media) == 29 and all(m['duration'] > 0 and m['width'] > 0 for m in media)
                assert all(abs(m['duration'] - 8) < .05 for m in media if any(s in m['src'] for s in ['ranking-drawer', 'ranking-banana', 'preference-button', 'preference-red-bin']))
                # Play each new replay briefly, then seek its final sampled image and capture the card.
                for case in page.locator('.positive-case').all():
                    slug = case.get_attribute('data-positive-case')
                    for video in case.locator('video').all():
                        video.evaluate('async v => {v.muted=true; await v.play()}')
                        page.wait_for_function('(v) => v.currentTime > 0', arg=video.element_handle())
                        video.evaluate('v => {v.pause(); v.currentTime=7.25}')
                        page.wait_for_function('(v) => !v.seeking && v.readyState>=2', arg=video.element_handle())
                    case.locator('summary').click()
                    assert case.locator('details').evaluate('d => d.open')
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (slug, 'expanded overflow')
                    case.locator('summary').click()
                    case.screenshot(path=str(args.output / f'{language}-{device}-{slug}.png'),
                                    style='.header,.toc,#reading-progress{visibility:hidden!important}')
                # Exercise all exact samples after metadata has loaded.
                seek_checks = []
                for panel in page.locator('[data-progress-compare]').all():
                    video = panel.locator('video')
                    indices = list(map(int, panel.get_attribute('data-progress-indices').split(',')))
                    values = list(map(float, panel.get_attribute('data-progress-values').split(',')))
                    fps = float(panel.get_attribute('data-progress-fps'))
                    for index, value in zip(indices, values):
                        panel.locator(f'[data-progress-seek="{index}"]').click()
                        page.wait_for_function('(args) => Math.abs(args.v.currentTime-args.time)<0.01 && !args.v.seeking', arg={'v':video.element_handle(), 'time':index / fps})
                        button = panel.locator(f'[data-progress-seek="{index}"]')
                        assert button.get_attribute('aria-pressed') == 'true'
                        assert panel.locator(f'[data-progress-point="{index}"]').evaluate("e => e.classList.contains('is-active')")
                        cursor = float(panel.locator('[data-progress-cursor]').get_attribute('x1'))
                        assert abs(cursor - (48 + index / 31 * 348)) < .001
                        status = panel.locator('[data-progress-status]').inner_text()
                        assert f'{value:.2f}' in status
                        assert (('协议起点' if language == 'zh' else 'Protocol initial value') in status) == (index == 0)
                        seek_checks.append({'index': index, 'value': value, 'time': video.evaluate('v => v.currentTime')})
                    panel.locator('[data-progress-seek="23"]').focus()
                    page.keyboard.press('Enter')
                    page.wait_for_function('(v) => Math.abs(v.currentTime-5.75)<.01 && !v.seeking', arg=video.element_handle())
                    video.evaluate('v => {v.currentTime=v.duration}')
                    page.wait_for_function('(p) => p.querySelector("[data-progress-seek=\\"31\\"]").getAttribute("aria-pressed")==="true"', arg=panel.element_handle())
                    assert float(panel.locator('[data-progress-cursor]').get_attribute('x1')) == 396
                page.locator('[data-progress-compare]').first.screenshot(path=str(args.output / f'{language}-{device}-progress.png'))
                # Protocol expansion and language navigation preserve the Results location.
                page.locator('#positive-case-protocol summary').click()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.locator('#positive-case-protocol summary').click()
                page.locator('#quality-results').scroll_into_view_if_needed()
                page.evaluate("document.getElementById('quality-results').scrollIntoView()")
                page.wait_for_function("document.querySelector('[data-language-link]').hash === '#quality-results'")
                link = page.locator('[data-language-link]').first.get_attribute('href')
                assert '#quality-results' in link
                # Also check the minimum supported 320 px width with all details open.
                if device == 'mobile':
                    page.evaluate("window.scrollTo(0,document.getElementById('ranking-drawer-case').getBoundingClientRect().top+scrollY-140)")
                    page.screenshot(path=str(args.output / f'{language}-mobile-viewport.png'))
                    page.set_viewport_size({'width':320,'height':844})
                    page.eval_on_selector_all('.positive-case details', 'items => items.forEach(d => d.open=true)')
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (language, '320px overflow')
                    assert page.eval_on_selector_all('.positive-case .table-scroll', 'tables=>tables.every(t=>t.scrollWidth<=t.clientWidth)'), (language, '320px score table overflow')
                assert not errors, errors
                results.append({'language': language, 'device': device, 'width': width, 'videos_loaded': len(media),
                                'new_videos_played': 8, 'sample_seek_checks': len(seek_checks), 'seek_results': seek_checks,
                                'page_overflow': False, 'expanded_quotes_checked': 4, 'keyboard_seek_and_end_clamp': True,
                                'language_anchor': link, 'console_or_http_errors': errors})
                page.close()
        # Test clicks before metadata exists, not just the readyState >= 1 branch.
        page = browser.new_page()
        page.goto(f'{args.url}/index.html', wait_until='networkidle')
        for panel in page.locator('[data-progress-compare]').all():
            video = panel.locator('video')
            assert video.evaluate('v=>v.readyState') == 0
            panel.locator('[data-progress-seek="15"]').click()
            page.wait_for_function('(v)=>v.readyState>=2 && !v.seeking && Math.abs(v.currentTime-3.75)<.01',arg=video.element_handle())
        browser.close()
    report = {'passed': True, 'pages': results, 'sample_seek_checks': sum(r['sample_seek_checks'] for r in results),
              'cold_metadata_seek_checks': 4, 'screenshots': sorted(p.name for p in args.output.glob('*.png'))}
    (args.output / 'browser-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':True,'language_viewports':len(results),'sample_seek_checks':report['sample_seek_checks'],
                      'cold_metadata_seek_checks':4,'screenshots':len(report['screenshots'])},indent=2))


if __name__ == '__main__':
    main()
