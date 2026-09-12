# vidgen-kit — mọi lệnh đi qua đây.
#
#   make setup                       cài phụ thuộc Python (ĐÚNG python3 này) + Node cho studio/
#   make studio [DAY=2026-08-20]     mở Remotion Studio bằng dữ liệu thật
#   make content DAY=2026-08-20      chỉ chuẩn bị nội dung (TTS + timeline)
#   make video   DAY=2026-08-20      dựng trọn: nội dung -> render MP4 + ảnh bìa
#   make release DAY=2026-08-20      trọn gói để đăng: video + ảnh bìa + check
#   make still   DAY=2026-08-20 FRAME=300   render 1 frame ra PNG
#   make thumbnail DAY=2026-08-20    render ảnh bìa: tiêu đề ngày đã hiện, câu 1 chưa đọc
#   make shots                       soi sổ tài sản: nguồn, giấy phép, tag, ai dùng
#   make shots-find / shots-get / shots-add   thêm clip vào thư viện
#   make new     DAY=2026-09-10      tạo kịch bản mới (ngân hàng, hoặc Claude nếu có khoá)
#   make bank                        in ngân hàng kịch bản kèm ước lượng thời lượng
#   make check   DAY=2026-08-20      kiểm MP4: số đo + trang duyệt từng cảnh
#   make export  DAY=2026-08-20      gói ra out/<ngày>/: caption, lời, audio, metadata
#   make export-all                  gói mọi ngày đã dựng nội dung
#   make content-all                 chuẩn bị nội dung cho MỌI kịch bản chưa có
#   make all                         dựng mọi kịch bản chưa có MP4
#   make clean                       xoá file máy sinh
#
# Quy ước đường dẫn: mọi lệnh chạy từ gốc repo. Remotion cần chạy trong
# studio/ (nơi có package.json), nên đường dẫn truyền vào nó phải có tiền tố
# ../ — quy ước đó nằm gọn trong pipeline/render.py, Makefile không lo nữa.

SHELL := /bin/bash
.DEFAULT_GOAL := help

STUDIO      := studio
CONTENT     := content
OUT         := out
FRAME       ?= 300
# PROVIDER là của `make reading` (cutlet/pykakasi) — để trống thì kịch bản tự
# quyết. SOURCE là của `make shots-*` (pexels/pixabay). Hai thứ khác hẳn nhau,
# nên hai tên khác nhau: gộp lại là `make reading` đi tìm provider tên "pexels".
PROVIDER    ?=
SOURCE      ?= pexels
# MODEL là của `make new`: để trống = có ANTHROPIC_API_KEY thì gọi Claude, không
# thì lấy ngân hàng. `bank` ép lấy ngân hàng; `opus`/`sonnet`/`haiku` ép gọi Claude.
MODEL       ?=

# Bắt lỗi thiếu DAY sớm, kèm gợi ý — thay vì để lệnh con báo lỗi khó hiểu.
define need_day
	@if [ -z "$(DAY)" ]; then \
		echo "Thiếu DAY. Ví dụ: make $@ DAY=2026-08-20"; \
		echo "Các kịch bản đang có:"; \
		ls -d $(CONTENT)/*/ 2>/dev/null \
			| xargs -n1 basename 2>/dev/null | sed 's/^/  /' \
			|| echo "  (chưa có kịch bản nào)"; \
		exit 1; \
	fi
endef

.PHONY: help setup studio content video release still thumbnail reading shots assets \
        shots-find shots-get shots-add all clean check new bank export export-all \n        content-all

help:
	@echo "vidgen-kit"
	@echo ""
	@echo "  make setup                        cài phụ thuộc Python + Node"
	@echo "  make studio [DAY=2026-08-20]      mở Remotion Studio bằng dữ liệu thật"
	@echo "  make content DAY=2026-08-20       chuẩn bị nội dung (TTS + timeline)"
	@echo "  make video   DAY=2026-08-20       dựng trọn ra MP4 + ảnh bìa"
	@echo "  make release DAY=2026-08-20       trọn gói: MP4 + ảnh bìa + check"
	@echo "  make still   DAY=2026-08-20 FRAME=300"
	@echo "  make thumbnail DAY=2026-08-20     chỉ render ảnh bìa ra out/<ngày>-thumbnail.png"
	@echo "  make reading DAY=2026-08-20       in romaji + hiragana máy sinh"
	@echo "  make shots                        soi sổ tài sản (nguồn, giấy phép, tag)"
	@echo "  make shots-find SOURCE=pexels Q=\"tea ceremony\""
	@echo "  make shots-get  SOURCE=pexels ID=8507912 NAME=matcha-whisk TAGS=tea"
	@echo "  make shots-add  FILE=... NAME=... URL=... AUTHOR=... LICENSE=..."
	@echo "  make new     DAY=2026-09-10       tạo kịch bản mới [MODEL=bank|opus|sonnet|haiku]"
	@echo "  make bank                         in ngân hàng kịch bản viết sẵn"
	@echo "  make check   DAY=2026-08-20       kiểm MP4 + trang duyệt từng cảnh"
	@echo "  make export  DAY=2026-08-20       gói ra out/<ngày>/ để đăng"
	@echo "  make export-all                   gói mọi ngày đã dựng nội dung"
	@echo "  make content-all                  chuẩn bị nội dung mọi kịch bản chưa có"
	@echo "  make all                          dựng mọi kịch bản chưa có MP4"
	@echo "  make clean                        xoá file máy sinh"

## Cài phụ thuộc Python vào ĐÚNG trình thông dịch mà Makefile sẽ gọi.
##
## Dùng `python3 -m pip` chứ không dùng `pip` trần, và đây không phải chuyện
## câu nệ: máy này có hai Python (conda base và python của codespace). `pip`
## trần trỏ vào cái nào là tuỳ PATH, nên rất dễ cài xong một chỗ rồi `make`
## chạy ở chỗ kia và báo thiếu thư viện.
##
## Node cũng cùng bẫy đó, theo kiểu WSL: PATH của Windows lọt vào nên `npm` có
## thể là bản Windows. studio/node_modules không vào git, thiếu nó thì `npx
## remotion` chỉ báo "could not determine executable to run".
setup:
	@echo "Python:  $$(python3 -c 'import sys; print(sys.executable)')"
	@echo "Node:    $$(command -v node || echo '(không có)')"
	@echo "npm:     $$(command -v npm || echo '(không có)')"
	@if ! command -v node >/dev/null 2>&1; then \
		echo ""; \
		echo "[lỗi] Không có node. Remotion cần Node 18 trở lên."; \
		echo "      Cài bản Linux bằng nvm — xem docs/cai-dat.md."; \
		exit 1; \
	fi
	@case "$$(command -v npm)" in /mnt/*) \
		echo ""; \
		echo "[lỗi] npm đang trỏ sang bản Windows: $$(command -v npm)"; \
		echo "      Đó là PATH của Windows lọt vào WSL, không phải Node của WSL."; \
		echo "      Cài bằng nó thì Remotion tải nhị phân win32, render sẽ chết."; \
		echo "      Cài Node bản Linux bằng nvm — xem docs/cai-dat.md."; \
		exit 1;; \
	esac
	@major=$$(node -p 'process.versions.node.split(".")[0]'); \
	if [ "$$major" -lt 18 ]; then \
		echo ""; \
		echo "[lỗi] Node $$(node -v) quá cũ. Remotion cần Node 18 trở lên."; \
		exit 1; \
	fi
	@echo ""
	@python3 -m pip install -r requirements.txt
	@echo ""
	@cd $(STUDIO) && if [ -f package-lock.json ]; then npm ci; else npm install; fi
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ""; \
		echo "Đã tạo .env từ .env.example."; \
		echo "Mở .env ra điền khoá API nếu muốn dùng 'make shots-find/shots-get'."; \
		echo "Không điền cũng chạy được mọi lệnh dựng video."; \
	else \
		echo ""; \
		echo "Đã có .env, giữ nguyên (không đè lên khoá bạn đã điền)."; \
	fi
	@echo ""
	@echo "Xong. Kiểm nhanh: make reading DAY=2026-08-20"

## Mở Studio bằng dữ liệu THẬT của một ngày.
##   make studio                 -> nạp ngày mới nhất đã dựng
##   make studio DAY=2026-08-20  -> nạp đúng ngày đó
## Chưa dựng ngày nào thì Studio rơi về props mặc định trong Composition.tsx —
## một câu, nền gradient, không tiếng. Đó là bản dự phòng, không phải video thật.
studio:
	@if [ ! -x $(STUDIO)/node_modules/.bin/remotion ]; then \
		echo "Chưa cài Remotion ($(STUDIO)/node_modules trống). Chạy 'make setup' trước."; \
		exit 1; \
	fi
	@day="$(DAY)"; \
	if [ -z "$$day" ]; then \
		newest=$$(ls -t $(CONTENT)/*/build.json 2>/dev/null | head -1); \
		[ -n "$$newest" ] && day=$$(basename $$(dirname "$$newest")); \
	fi; \
	if [ -n "$$day" ] && [ -f "$(CONTENT)/$$day/build.json" ]; then \
		echo "Studio nạp $(CONTENT)/$$day/build.json"; \
		cd $(STUDIO) && npx remotion studio --props="../$(CONTENT)/$$day/build.json"; \
	else \
		echo "Chưa có content/*/build.json nào, Studio mở bằng props mặc định."; \
		echo "Chạy 'make content DAY=2026-08-20' trước để xem video thật."; \
		cd $(STUDIO) && npx remotion studio; \
	fi

## Kịch bản -> giọng đọc -> content/<DAY>.build.json
content:
	$(need_day)
	@python3 -m pipeline.run $(DAY)

## Kịch bản -> giọng đọc -> timeline -> out/<DAY>.mp4 + out/<DAY>-thumbnail.png, một lượt
video:
	$(need_day)
	@python3 -m pipeline.run $(DAY) --render

## Trọn gói một ngày, đủ thứ để đăng: video (nội dung + MP4 + ảnh bìa) rồi check
## (số đo + trang duyệt). Check chạy trên MP4 VỪA dựng, nên không có chuyện kiểm
## nhầm bản cũ. Render hỏng thì dừng luôn, không check một file dở dang.
release:
	$(need_day)
	@python3 -m pipeline.run $(DAY) --render
	@echo ""
	@echo "==> Kiểm MP4 vừa dựng"
	@python3 -m pipeline.check $(DAY)
	@echo ""
	@echo "==> Gói thư mục đăng"
	@python3 -m pipeline.export $(DAY)
	@echo ""
	@echo "Đủ bộ cho $(DAY):"
	@echo "  thư mục đăng $(OUT)/$(DAY)/  (caption.txt, script.txt, audio/, metadata.json)"
	@echo "  video        $(OUT)/$(DAY).mp4"
	@echo "  ảnh bìa      $(OUT)/$(DAY)-thumbnail.png"
	@echo "  trang duyệt  $(OUT)/$(DAY)-check/index.html"
	@echo "  ảnh ghép     $(OUT)/$(DAY)-check/sheet.jpg"

## Render đúng 1 frame — cách nhanh nhất để bắt lỗi font và bố cục caption
still:
	$(need_day)
	@python3 -m pipeline.run $(DAY) --still $(FRAME)

## Ảnh bìa: frame mà ngày và chủ đề vừa hiện đủ, caption câu 1 chưa vào, chưa có
## tiếng đọc. Frame đó do timeline.py chọn (thumbnailFrame trong build.json).
## Như `still`, chỉ vẽ từ build.json đã có — sửa kịch bản thì `make content` trước.
thumbnail:
	$(need_day)
	@python3 -m pipeline.run $(DAY) --thumbnail

## In romaji và hiragana máy sinh, để đọc đối chiếu trước khi tin nó
reading:
	$(need_day)
	@python3 -m pipeline.reading $(CONTENT)/$(DAY)/script.json $(PROVIDER)

## Soi sổ tài sản: file thật, nguồn, tác giả, giấy phép, tag, ai đang dùng
shots assets:
	@python3 -m pipeline.library

## Tìm clip trên Pexels/Pixabay. Cần khoá API — xem pipeline/fetch.py
shots-find:
	@if [ -z "$(Q)" ]; then echo 'Thiếu Q. Ví dụ: make shots-find SOURCE=pexels Q="tea ceremony"'; exit 1; fi
	@python3 -m pipeline.fetch find $(SOURCE) "$(Q)"

## Tải một clip theo id rồi ghi thẳng vào sổ
shots-get:
	@if [ -z "$(ID)" ] || [ -z "$(NAME)" ]; then \
		echo 'Thiếu ID hoặc NAME.'; \
		echo 'Ví dụ: make shots-get SOURCE=pexels ID=8507912 NAME=matcha-whisk TAGS=tea,matcha'; \
		exit 1; \
	fi
	@python3 -m pipeline.fetch get $(SOURCE) $(ID) $(NAME) "$(TAGS)"

## Nhận một file đã tải sẵn vào thư viện. URL, AUTHOR, LICENSE là bắt buộc.
shots-add:
	@if [ -z "$(FILE)" ] || [ -z "$(NAME)" ]; then \
		echo 'Thiếu FILE hoặc NAME.'; \
		echo 'Ví dụ: make shots-add FILE=~/tai/san-vuon.mp4 NAME=zen-garden \'; \
		echo '                      URL=https://... AUTHOR="Tên" LICENSE="CC0" TAGS=garden,calm'; \
		exit 1; \
	fi
	@python3 -m pipeline.fetch add "$(FILE)" $(NAME) "$(URL)" "$(AUTHOR)" "$(LICENSE)" "$(TAGS)"

## Chuẩn bị NỘI DUNG (TTS + timeline) cho mọi kịch bản chưa có build.json.
## Khác `make all` ở chỗ không render: dùng khi muốn soạn cả tháng rồi mới
## `make export-all` lấy caption và lời ra soát, trước khi tốn CPU dựng video.
## Ngày nào đã có build.json thì bỏ qua — giọng đọc có cache nên chạy lại rẻ,
## nhưng bỏ qua vẫn nhanh hơn.
content-all:
	@for d in $(CONTENT)/*/; do \
		day=$$(basename "$$d"); \
		[ -f "$$d/script.json" ] || continue; \
		if [ -f "$$d/build.json" ]; then \
			echo "bỏ qua $$day (đã có build.json)"; \
		else \
			echo "==> $$day"; \
			python3 -m pipeline.run $$day || exit 1; \
		fi; \
	done

## Dựng mọi kịch bản chưa có MP4 tương ứng
all:
	@for d in $(CONTENT)/*/; do \
		day=$$(basename "$$d"); \
		[ -f "$$d/script.json" ] || continue; \
		if [ -f "$(OUT)/$$day.mp4" ]; then \
			echo "bỏ qua $$day (đã có MP4)"; \
		else \
			echo "==> $$day"; \
			$(MAKE) --no-print-directory video DAY=$$day; \
		fi; \
	done

## Xoá mọi thứ máy sinh ra. Kịch bản và thư viện shot không bị đụng tới.
clean:
	rm -rf $(OUT)
	rm -f $(CONTENT)/*/build.json $(CONTENT)/*/.cache.json
	rm -rf $(STUDIO)/public/audio/20*/
	@echo "Đã xoá file máy sinh."
	@echo "Kịch bản, nhạc nền và clip nền còn nguyên — chỉ giọng đọc bị xoá,"
	@echo "chạy lại 'make content' là edge-tts sinh lại."

## Tạo content/<DAY>.json. Không có khoá thì lấy ngân hàng, không gọi mạng.
## Không bao giờ đè kịch bản đã có.
new:
	$(need_day)
	@python3 -m pipeline.new $(DAY) $(MODEL)

## In ngân hàng: mỗi mục bao nhiêu câu, ước lượng bao nhiêu giây, đã dùng ngày nào
bank:
	@python3 -m pipeline.new --bank

## Gói một ngày thành thư mục đăng được: out/<ngày>/ có caption, lời Nhật–Việt,
## giọng đọc từng câu, metadata và ghi công tài sản. Chỉ đọc build.json và MP4
## đã có — không dựng lại gì, nên chạy lại bao nhiêu lần cũng được.
export:
	$(need_day)
	@python3 -m pipeline.export $(DAY)

## Gói MỌI ngày đã có content/<ngày>.build.json. Dùng khi đã dựng cả tháng.
export-all:
	@python3 -m pipeline.export --all

## Kiểm MP4 đã dựng: số đo tự kết luận + trang duyệt để mắt bắt tofu và chữ bị che
check:
	$(need_day)
	@python3 -m pipeline.check $(DAY)
