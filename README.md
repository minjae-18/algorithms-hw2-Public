# 과제2 · 에이전트와 함께 만드는 URL 단축기

2026-2 **고급알고리즘**(SIT2001-01) 과제2의 **시작 저장소**입니다.
채팅창에 묻고 복사·붙여넣기 하던 방식에서 벗어나, Codespace 안의 에이전트가
저장소를 읽고, 파일을 고치고, 테스트를 직접 돌리게 하는 방법을 익힙니다.

- 과제 안내: [lec-algorithm.github.io/lecture/article/hw2-2026](https://lec-algorithm.github.io/lecture/article/hw2-2026/)
- 수업 슬라이드: [lec-algorithm.github.io/lecture/slides/hw2-2026](https://lec-algorithm.github.io/lecture/slides/hw2-2026/)
- 해시 테이블 복습: [주제 08 해시 테이블](https://lec-algorithm.github.io/lecture/course/topic-08-hashing/)

## 시작하기

1. 이 저장소 상단의 **Use this template** → **Create a new repository**
2. 저장소 이름은 `algorithms-hw2`처럼 정합니다. 공개(Public)로 만듭니다.
3. 만들어진 **내 저장소**에서 **Code** → **Codespaces** 탭 → **Create codespace on main**
4. 왼쪽 막대의 Copilot 아이콘을 눌러 채팅 창을 열고, 창 아래쪽에서 **Agent** 모드를 고릅니다.

## 들어 있는 것

| 파일 | 하는 일 |
| --- | --- |
| `SPEC.md` | 명세 틀. 에이전트가 초안을 쓰고 **본인이 고칩니다** |
| `src/` · `tests/` · `experiments/` | URL 단축기, 테스트, 해시 테이블 실험 |
| `tools/catchup.sh` | 수업 중 놓친 단계를 따라잡는 스크립트 |
| `Makefile` | `make test` · `make serve` · `make experiment` · `make compare` |

정답 코드는 들어 있지 않습니다. 에이전트는 작업 공간의 파일을 읽으므로, 정답이
옆에 있으면 그대로 베껴 와서 연습이 되지 않습니다.

## 명령

컨테이너 안(Codespaces 터미널)에서 실행합니다.

| 하고 싶은 것 | 명령 |
| --- | --- |
| 테스트 | `make test` |
| 웹 서버 (포트 8000) | `make serve` |
| 충돌 실험 | `make experiment` |
| 체이닝 vs Python `dict` 비교 | `make compare` |
| 놓친 단계 따라잡기 | `sh tools/catchup.sh <단계 번호>` |

외부 라이브러리는 쓰지 않습니다. Python 표준 모듈만으로 충분합니다.

## 웹 화면과 해시 테이블 확인

`make serve`를 실행하면 URL 입력 화면이 열립니다. URL을 제출하면 짧은 링크가
표시되고, `/table`에서는 현재 URL-to-ID 체이닝 테이블의 각 버킷, 연결 리스트,
Horner 해시 계산 단계를 확인할 수 있습니다. 서버는 메모리 기반이므로 종료하면
저장한 링크가 사라집니다.

Codespaces에서 휴대폰으로 확인하려면 실행 중인 서버의 **Ports** 탭에서 8000번
포트의 Visibility를 **Public**으로 바꾸고, 표시된 HTTPS 주소를 엽니다. 확인이
끝나면 터미널에서 `Ctrl+C`로 서버를 종료하고 포트 Visibility를 **Private**으로
되돌립니다.

## 실험

`make experiment`는 체이닝 해시 테이블의 적재율과 평균 탐색 횟수를 측정합니다.
`make compare`는 직접 구현한 체이닝 테이블과 Python 내장 `dict`의 삽입, 성공
검색, 실패 검색 시간을 같은 키 집합으로 비교하고 결과를
[`experiments/comparison_experiment.md`](experiments/comparison_experiment.md)에
기록합니다. 내장 `dict`는 이 비교 실험 스크립트에서만 사용하며, 실제 단축기와
직접 구현한 해시 테이블은 사용하지 않습니다.

## 로컬에서 하기

```sh
git clone https://github.com/<본인 계정>/<내 저장소>.git
cd <내 저장소>
docker compose up -d
docker compose exec lab bash
```

**이후 모든 `docker compose` 명령은 이 폴더에서 칩니다.**
