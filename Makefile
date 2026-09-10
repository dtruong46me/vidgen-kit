# vidgen-kit — mọi lệnh đi qua đây.
#
#   make setup                       cài phụ thuộc Python + Node vào ĐÚNG máy này
#   make studio [DAY=2026-08-20]     mở Remotion Studio bằng dữ liệu thật
#   make content DAY=2026-08-20      chỉ chuẩn bị nội dung (TTS + timeline)
#   make video   DAY=2026-08-20      dựng trọn: nội dung -> render MP4
#   make still   DAY=2026-08-20 FRAME=300   render 1 frame ra PNG
#   make shots                       soi sổ tài sản: nguồn, giấy phép, tag, ai dùng
#   make shots-find / shots-get / shots-add   thêm clip vào thư viện
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

# Bắt lỗi thiếu DAY sớm, kèm gợi ý — thay vì để lệnh con báo lỗi khó hiểu.
define need_day
	@if [ -z "$(DAY)" ]; then \
		echo "Thiếu DAY. Ví dụ: make $@ DAY=2026-08-20"; \
		echo "Các kịch bản đang có:"; \
		ls $(CONTENT)/*.json 2>/dev/null \
			| grep -v '\.build\.json$$' \
			| xargs -n1 basename 2>/dev/null | sed 's/\.json$$/  /' | sed 's/^/  /' \
			|| echo "  (chưa có kịch bản nào)"; \
		exit 1; \
	fi
endef

# Thiếu node_modules thì npx chỉ nói "could not determine executable to run",
# câu đó không chỉ ra được thứ gì. Chặn sớm, trỏ thẳng vào `make setup`.
define need_node_modules
	@if [ ! -d "$(STUDIO)/node_modules/remotion" ]; then \
		echo "Chưa cài phụ thuộc Node trong $(STUDIO)/."; \
		echo "Chạy: make setup"; \
		exit 1; \
	fi
endef

.PHONY: help setup studio content video still reading shots assets \
        shots-find shots-get shots-add all clean check new

help:
	@echo "vidgen-kit"
	@echo ""
	@echo "  make setup                        cài phụ thuộc Python + Node"
	@echo "  make studio [DAY=2026-08-20]      mở Remotion Studio bằng dữ liệu thật"
	@echo "  make content DAY=2026-08-20       chuẩn bị nội dung (TTS + timeline)"
	@echo "  make video   DAY=2026-08-20       dựng trọn ra MP4"
	@echo "  make still   DAY=2026-08-20 FRAME=300"
	@echo "  make reading DAY=2026-08-20       in romaji + hiragana máy sinh"
	@echo "  make shots                        soi sổ tài sản (nguồn, giấy phép, tag)"
	@echo "  make shots-find SOURCE=pexels Q=\"tea ceremony\""
	@echo "  make shots-get  SOURCE=pexels ID=8507912 NAME=matcha-whisk TAGS=tea"
	@echo "  make shots-add  FILE=... NAME=... URL=... AUTHOR=... LICENSE=..."
	@echo "  make all                          dựng mọi kịch bản chưa có MP4"
	@echo "  make clean                        xoá file máy sinh"
	@echo ""
	@echo "  make check / make new             chưa có — xem BƯỚC 6 trong kế hoạch"

## Cài phụ thuộc vào ĐÚNG môi trường mà Makefile sẽ gọi — Python lẫn Node.
##
## Dùng `python3 -m pip` chứ không dùng `pip` trần, và đây không phải chuyện
## câu nệ: máy này có hai Python (conda base và python của codespace). `pip`
## trần trỏ vào cái nào là tuỳ PATH, nên rất dễ cài xong một chỗ rồi `make`
## chạy ở chỗ kia và báo thiếu thư viện.
##
## Node dính đúng cái bẫy đó, mà nặng hơn: WSL nối PATH của Windows vào cuối
## PATH của nó, nên `npm` gọi được bằng bản Windows trong khi `node` bản Linux
## thì không hề có. Cài bằng npm đó thì Remotion tải Chrome Headless Shell và
## esbuild bản win32 về, rồi render trong Linux mới chết — chết ở chỗ xa lỗi
## thật. Vì vậy in đường dẫn ra trước và chặn hẳn nếu npm nằm dưới /mnt.
##
## Soi cả ba đường dẫn TRƯỚC khi cài gì: thiếu Node mà vẫn chạy pip trước thì
## bạn ngồi chờ hết lượt cài Python rồi mới biết mình bị chặn.
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
	$(need_node_modules)
	@day="$(DAY)"; \
	if [ -z "$$day" ]; then \
		newest=$$(ls -t $(CONTENT)/*.build.json 2>/dev/null | head -1); \
		[ -n "$$newest" ] && day=$$(basename "$$newest" .build.json); \
	fi; \
	if [ -n "$$day" ] && [ -f "$(CONTENT)/$$day.build.json" ]; then \
		echo "Studio nạp $(CONTENT)/$$day.build.json"; \
		cd $(STUDIO) && npx remotion studio --props="../$(CONTENT)/$$day.build.json"; \
	else \
		echo "Chưa có content/*.build.json nào, Studio mở bằng props mặc định."; \
		echo "Chạy 'make content DAY=2026-08-20' trước để xem video thật."; \
		cd $(STUDIO) && npx remotion studio; \
	fi

## Kịch bản -> giọng đọc -> content/<DAY>.build.json
content:
	$(need_day)
	@python3 -m pipeline.run $(DAY)

## Kịch bản -> giọng đọc -> timeline -> out/<DAY>.mp4, một lượt
video:
	$(need_day)
	@python3 -m pipeline.run $(DAY) --render

## Render đúng 1 frame — cách nhanh nhất để bắt lỗi font và bố cục caption
still:
	$(need_day)
	@python3 -m pipeline.run $(DAY) --still $(FRAME)

## In romaji và hiragana máy sinh, để đọc đối chiếu trước khi tin nó
reading:
	$(need_day)
	@python3 -m pipeline.reading $(CONTENT)/$(DAY).json $(PROVIDER)

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

## Dựng mọi kịch bản chưa có MP4 tương ứng
all:
	@for f in $(CONTENT)/*.json; do \
		case "$$f" in *.build.json) continue;; esac; \
		day=$$(basename "$$f" .json); \
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
	rm -f $(CONTENT)/*.build.json $(CONTENT)/.*.cache.json
	rm -rf $(STUDIO)/public/audio/20*/
	@echo "Đã xoá file máy sinh."
	@echo "Kịch bản, nhạc nền và clip nền còn nguyên — chỉ giọng đọc bị xoá,"
	@echo "chạy lại 'make content' là edge-tts sinh lại."

check new:
	@echo "'make $@' chưa có. Nó thuộc BƯỚC 6 trong kế hoạch triển khai."
	@exit 1
