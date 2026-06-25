# FA

**맥락의 상실(Loss of Context)을 해결하는 풋볼 애널리틱스 프로젝트.**

선수의 스탯(골·도움·VAEP 등)에는 그 숫자가 나오게 된 배경 — 동료의 도움, 감독의 전술, 상대 수준, 리그 강도 — 이 담기지 않는다. 결과만 한 선수에게 귀속되어 영입 오판·저평가 사각지대·적응 실패를 낳는다. FA는 이 맥락을 분리·복원하는 것을 목표로 한다.

## 컨셉 노트 (원본)

프로젝트의 개념·도메인 지식은 Obsidian 보관함에 정리되어 있다. 도메인 관련 작업 전에 참고할 것:

- 폴더: `D:\Obsidian\Idea\축구`
- 핵심 문제: `이슈\맥락의 상실.md` — 폴더 전체를 관통하는 근본 문제
- 방법론: `세이버메트릭스.md` (풋볼 애널리틱스 개요), `선수 개인 스텟.md` (평가 층위)
- 보정 모델: `리그.md` (리그 변환), 동료 효과(RAPM/EPM), 전술 반사실 시뮬레이션
- 공급망: `데이터 공급사 생태계.md` (Opta / StatsBomb / SkillCorner / Impect)
- 이슈: `이슈\` 폴더 (감독교체, 리그 간 적응, 유망주문제, 이적료 등)

## 도메인 핵심 개념

- **맥락 분리** — 동료·감독·리그·상대 효과를 개인 기여에서 떼어내는 것이 프로젝트의 본질
- **포제션 밸류 모델** — xT(구역별 위협 증가), VAEP(행동의 득실 확률), EPV, OBV
- **보정 모델** — 동료→플러스마이너스(RAPM/EPM), 리그→리그 변환, 감독·전술→반사실 시뮬레이션
- **데이터 세대** — 1세대 이벤트(xG 표준화), 2세대 트래킹(off-ball, SkillCorner), 3세대 딥러닝/생성형
- **off-ball 공백** — 공 없을 때 기여가 데이터에 거의 안 잡힘 → 구조적 저평가의 원천

## 기술 스택

인터랙티브 웹 앱. **분석 레이어(Python)와 웹 레이어를 분리**한다.

- **프론트엔드**: Vite + React + TypeScript + **D3.js**(피치 시각화). 일반 차트는 visx/Recharts 병용. (SSR 필요해지면 Next.js로 이전)
- **백엔드 API**: **FastAPI** + Pydantic. 미리 계산된 분석 결과를 JSON으로 제공(조회 전용).
- **분석 코어**: **kloppy**(데이터 표준화) · **statsbombpy**(무료 데이터) · **socceraction**(xT·VAEP) · polars · scikit-learn · **xgboost**(수비 가치 추정) · mplsoccer(검증용 viz).
- **저장**: **DuckDB + parquet** (초기). 커지면 PostgreSQL.
- **원칙**: 무거운 모델 계산은 배치 파이프라인에서 미리 수행해 DuckDB에 적재. API는 매 요청마다 재계산하지 않는다.

### 폴더 구조 (monorepo)

```
analysis\   Python 분석 코어 + 파이프라인 (ingest\ models\ pipelines\)
api\        FastAPI 백엔드
web\        Vite + React + D3 프론트
data\       parquet/duckdb (git ignore)
```

## 개발 환경 / 실행

- Python 가상환경: `D:\FA\.venv` (Python 3.12). 실행은 `./.venv/Scripts/python.exe`.
- **Windows 콘솔 인코딩 주의**: 기본 cp949라 선수명(악센트)·한글 출력이 깨진다.
  - 스크립트 실행 시 `PYTHONUTF8=1` 환경변수를 붙이거나, 스크립트 상단에 `sys.stdout.reconfigure(encoding="utf-8")`.
  - matplotlib 한글은 `mpl.rcParams["font.family"] = "Malgun Gothic"` 설정.

### 현재까지 동작하는 것

**analysis/ (배치)**
- `xt_core.py` — xT 공통 로직(그리드 로드, 행동별 xT, 선수 랭킹). 시각화·API가 공유.
- `ingest/statsbomb_to_duckdb.py` — 한 대회/시즌(기본 분데스리가 2023/24 = 레버쿠젠 시즌 전체) 전 경기를 받아 `data/fa.duckdb`의 `matches`·`events`로 적재. 현재 34경기 137,765 이벤트.
- `models/xt_passmap.py` — 시즌 xT 누적(경기당, 5경기↑) 랭킹 + 1위 선수 패스맵(`data/xt_passmap.png`). 현 1위: Grimaldo.
- `models/vaep_rating.py` — socceraction VAEP. SPADL 변환→피처/라벨→XGBoost 2개(득점·실점확률)→행동가치→선수 90분당 랭킹(`data/vaep_rating.csv`). 현 1위: Wirtz. xT가 못 잡는 수비·빌드업까지 평가(Tapsoba 등 수비수 상위). ⚠️ 현재 train/test 미분리(낙관 편향) — 본격화 시 분리 필요.

**api/ (FastAPI, 조회 전용)**
- `main.py` — 시작 시 xT를 1회 계산해 메모리 캐시, VAEP는 CSV 로드. 엔드포인트: `/api/players/xt`, `/api/players/vaep`, `/api/players/{player}/xt-actions`.

**web/ (Vite + React)**
- Claude Design(`FA 분석 콘솔.dc.html`)을 React로 포팅한 **맥락 분석 콘솔**. 라이트/다크 테마, 사이드바(선수/구단/포지션 스코프), Newsreader/Archivo 폰트.
- 컴포넌트: `App`(셸·상태) · `Sidebar` · `Topbar` · `PlayerScope`(랭킹+상세: 기여도 분해 워터폴·피치·행동구성·백분위) · `ClubScope` · `PositionScope` · `Pitch`(SVG, 테마 변수) · `lib.js`(헬퍼+예시 모델).
- `/api`는 vite가 8000으로 프록시.
- ⚠️ **실데이터 vs 예시 경계**: 선수 랭킹(VAEP/90)·피치 패스맵·행동구성·포지션/구단 집계는 **실측**. **맥락 보정 분해(동료/리그/상대), 백분위, 경기별 추이, 포지션 차감%는 예시값**(`lib.js`) — 모델 미구축이라 UI에 `예시·미구축` 배지 표시. 보정 모델(RAPM/리그변환) 만들면 `lib.js`만 교체.

**주의**
- DuckDB 적재 시 중첩 list/dict 컬럼은 문자열로 직렬화됨. SPADL/VAEP처럼 원본 구조가 필요하면 DuckDB 대신 socceraction 로더로 재취득(vaep_rating.py가 그렇게 함).
- socceraction는 pandas<3·numpy<2·multimethod<2 를 요구 → 설치 순서 주의. 현재 venv는 맞춰져 있음.

### 실행 명령

```bash
# 1) 데이터 적재 (최초 1회, 수 분)
PYTHONUTF8=1 .venv/Scripts/python.exe analysis/ingest/statsbomb_to_duckdb.py
# 2) 모델 (선택)
PYTHONUTF8=1 .venv/Scripts/python.exe analysis/models/xt_passmap.py
PYTHONUTF8=1 .venv/Scripts/python.exe analysis/models/vaep_rating.py
# 3) 백엔드 (터미널 A)
PYTHONUTF8=1 .venv/Scripts/python.exe -m uvicorn api.main:app --reload --port 8000
# 4) 프론트 (터미널 B) → 브라우저 http://localhost:5173
cd web && npm install && npm run dev
```

- dev 서버 접속은 `127.0.0.1`이 아니라 `localhost`로 (vite/uvicorn IPv6 바인딩).

## 작업 규칙

- 응답·문서·주석은 한국어로 작성한다.
- 코드·git은 이 폴더(`D:\FA`)에서 관리한다. 컨셉/기획 노트는 Obsidian 보관함에 둔다.
