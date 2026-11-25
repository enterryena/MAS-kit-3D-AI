# -*- coding: utf-8 -*-
"""Build the browser edition (v3.6) from the desktop screen, so both always share one screen and one engine.

  app/MASKIT_Desktop.html  +  browser_demo/src/browser_site.js  ->  browser_demo/MAS-kit_브라우저_v3_6.html

What changes for the browser: the virtual site / built-in main server / kit link run in JavaScript (ported from
the Python app, checked job-for-job by src/parity_test.js), records go to this browser's IndexedDB, and the
AI-only buttons are hidden. The physics, estimators and results are unchanged.
Opening the page shows the 3D stacking sim first (#calc = alignment screen, #yard = 3D AI yard).
usage: python build_browser_v36.py
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / 'app' / 'MASKIT_Desktop.html'
SITE_JS = HERE / 'src' / 'browser_site.js'
OUT = HERE / 'MAS-kit_브라우저_v3_6.html'

GLUE = r"""
/* Browser edition: built-in main server + kit run here; records stay in this browser. */
(function(root){'use strict';
 const S=root.MASKIT_BROWSER_SITE;let M=null;
 const site=new S.Site(()=>M||(M=root.MASKIT.buildModel(DATA)),{approachMs:1000,moveMs:800});
 const bank=root.MASKIT_CASE_BANK;bank.mode='browser_indexeddb';
 bank.gateBank=async q=>S.gateBankFrom(await bank.all(),q);
 const st=async()=>site.linkStatus();
 root.MASKIT_LINK={status:st,selfTest:st,machineReady:st,round:st,senseFailed:st,abort:async(sid,reason)=>{site.abort(reason);return site.linkStatus();}};
 root.MASKIT_SIM={start:async p=>site.start(p),state:async()=>site.state()};
})(window);
"""

DESKTOP_ONLY_START = '<script>\n/* Desktop distribution: a direct file open MUST NOT create a second, misleading browser database. */'

PAIRS = [
    ('<h1>MAS-kit 컨테이너 정렬 시뮬레이터 v3.6</h1>', '<h1>MAS-kit 컨테이너 정렬 시뮬레이터 v3.6 · 브라우저판</h1>'),
    ('<title>MAS-kit Matrix5 · 3D 보정 시뮬레이터</title>', '<title>MAS-kit 정렬 시뮬레이터 v3.6 (브라우저판)</title>'),
    ('if(BANK.mode!==\'desktop_sqlite\'||!LINK){', 'if(!LINK){'),
    ('if(BANK.mode!==\'desktop_sqlite\'){alert(', 'if(false){alert('),
    ("'자동 누적 활성화 · 브라우저 IndexedDB (다른 파일 위치·브라우저와 분리)'", "'자동 저장 중 · 기록은 이 브라우저에만 남습니다 (다른 기기·브라우저와 공유 안 됨)'"),
    ("'메인 서버 미설정 · PC에만 보관 · 내장 시뮬 서버가 지시 (설정 후 재시작하면 쌓인 기록부터 전송)'",
     "'브라우저판 · 내장 메인 서버가 지시 · 기록은 이 브라우저에만 저장'"),
    ('PC 저장소 연결 상태를 확인할 수 없습니다. 저장 위치 확인 후 다시 실행하세요.', '브라우저 저장소를 열 수 없습니다. 시크릿 창이 아닌 일반 창에서 다시 열어 주세요.'),
    ('PC 저장소 기록에 실패했습니다.', '브라우저 저장에 실패했습니다.'),
    ('PC 누적 기록 저장에 실패했습니다.', '브라우저 저장에 실패했습니다.'),
    (' · 마지막 결과 JSON을 저장하고 관리자 창의 저장 폴더 상태를 확인하세요.', ' · "성공·실패 기록 JSON 저장"으로 백업하세요.'),
]
REMOVE = [  # AI / desktop-only parts
    '<a href="/3d" style="display:inline-block;margin-bottom:8px;padding:8px 14px;border-radius:9px;background:#2f7df6;color:#fff;font-weight:700;text-decoration:none">🎮 3D AI 야드로 가기 (트럭·장애물·사례 유도)</a>',
]
REPLACE_BLOCKS = [
    ('<div class="buttons"><button id="open3d" class="secondary">', '<div class="buttons" style="display:none"><button id="open3d" class="secondary">'),
]


START_VIEW = r"""
<style>
#mkView{position:fixed;inset:0;z-index:9999;background:#0d1a24;display:flex;flex-direction:column}
#mkView[hidden]{display:none}
#mkViewBar{display:flex;gap:6px;flex-wrap:wrap;align-items:center;padding:6px 8px;background:#0d1a24;color:#e9f1f6;font:600 13px "Malgun Gothic","Apple SD Gothic Neo","Noto Sans KR",system-ui,sans-serif}
#mkViewBar b{margin-right:auto;font-size:13px}
#mkViewBar button{border:0;border-radius:8px;padding:7px 10px;font:inherit;cursor:pointer;background:#24384a;color:#e9f1f6}
#mkViewBar button.on{background:#2f7df6;color:#fff}
#mkViewFrame{flex:1;width:100%;border:0;background:#b7c9d5}
#mkBackTo3d{position:fixed;right:12px;bottom:12px;z-index:9998;border:0;border-radius:10px;padding:10px 14px;background:#2f7df6;color:#fff;font-weight:700;cursor:pointer}
</style>
<div id="mkView" hidden><div id="mkViewBar"><b>MAS-kit 시뮬레이터</b>
<button data-v="stack">3D 적재 시뮬</button><button data-v="yard">3D AI 야드</button><button data-v="calc">정렬 계산 화면</button></div>
<iframe id="mkViewFrame" title="MAS-kit 3D 시뮬레이션" allow="fullscreen"></iframe></div>
<button id="mkBackTo3d" hidden>3D 적재 시뮬로 돌아가기</button>
<script>
/* QR로 열면 3D 적재 시뮬을 먼저 띄운다. 주소 끝 #calc = 정렬 계산 화면, #yard = 3D AI 야드. */
(function(){
 var PAGES={stack:'MAS-kit_3D_%EC%BB%A8%ED%85%8C%EC%9D%B4%EB%84%88%EC%98%AE%EA%B8%B0%EA%B8%B0.html',
            yard:'MAS-kit_3D_AI%EC%95%BC%EB%93%9C_%EB%B8%8C%EB%9D%BC%EC%9A%B0%EC%A0%80.html'};
 var box=document.getElementById('mkView'),fr=document.getElementById('mkViewFrame'),back=document.getElementById('mkBackTo3d');
 function show(v){
  if(!PAGES[v]&&v!=='calc')v='stack';
  [].forEach.call(box.querySelectorAll('button'),function(b){b.className=b.getAttribute('data-v')===v?'on':'';});
  if(v==='calc'){box.hidden=true;back.hidden=false;fr.removeAttribute('src');document.body.style.overflow='';return;}
  back.hidden=true;box.hidden=false;document.body.style.overflow='hidden';
  var url=new URL(PAGES[v],location.href).href;if(fr.getAttribute('src')!==url)fr.setAttribute('src',url);
 }
 function fromHash(){show((location.hash||'').replace('#',''));}
 box.addEventListener('click',function(e){var v=e.target.getAttribute&&e.target.getAttribute('data-v');if(v)location.hash=v;});
 back.addEventListener('click',function(){location.hash='stack';});
 window.addEventListener('hashchange',fromHash);fromHash();
})();
</script>
"""


def build():
    html = SRC.read_text(encoding='utf-8')
    for old, new in PAIRS + REPLACE_BLOCKS + [(r, '') for r in REMOVE]:
        n = html.count(old)
        if n < 1:
            raise SystemExit('not found: %r' % old)
        html = html.replace(old, new)
    # storage / link notes written for the desktop
    import re
    html, n1 = re.subn(r'<p class="small">보관 위치: .*?</p>',
                       '<p class="small">보관 위치: <b>이 브라우저 안</b>(IndexedDB). 브라우저 기록을 지우면 사라지니 '
                       '"누적 전체 JSON 내보내기"로 백업하세요. 저장한 기록은 정렬 계산에 쓰지 않고 검토용으로만 남깁니다.</p>', html, count=1)
    html, n2 = re.subn(r'<p class="small">메인 서버 주소와 장치 번호는.*?</p>',
                       '<p class="small">브라우저판은 메인 서버도 이 화면 안에서 가상으로 돌립니다. 키트는 재고 보고만 하고, '
                       '움직이고 내릴지는 메인 서버가 정합니다. 실제 서버 연결·PC 영구 저장은 설치판(v3.6)에서 됩니다.</p>', html, count=1)
    if not (n1 and n2):
        raise SystemExit('desktop note not found')
    i = html.find(DESKTOP_ONLY_START)
    j = html.find('</script>', i)
    if i < 0 or j < 0:
        raise SystemExit('desktop-only block not found')
    site = SITE_JS.read_text(encoding='utf-8')
    html = html[:i] + '<script>\n' + site + '\n' + GLUE + '</script>' + html[j + len('</script>'):]
    k = html.rfind('</body>')
    if k < 0:
        raise SystemExit('</body> not found')
    html = html[:k] + START_VIEW + html[k:]
    OUT.write_text(html, encoding='utf-8')
    print('wrote', OUT.name, len(html), 'bytes')


if __name__ == '__main__':
    build()
