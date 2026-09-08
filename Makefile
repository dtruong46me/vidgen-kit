# vidgen-kit — mọi lệnh đi qua đây.
#
#   make setup                       cài phụ thuộc Python vào ĐÚNG python3 này
#   make studio [DAY=2026-08-20]     mở Remotion Studio bằng dữ liệu thật
#   make content DAY=2026-08-20      chỉ chuẩn bị nội dung (TTS + timeline)
#   make video   DAY=2026-08-20      dựng trọn: nội dung -> render MP4
#   make still   DAY=2026-08-20 FRAME=300   render 1 frame ra PNG
#   make assets                      soi nhạc nền và clip: thiếu gì, còn hàng mẫu gì
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
PROVIDER    ?=

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

.PHONY: help setup studio content video still reading assets all clean check new

help:
	@echo "vidgen-kit"
	@echo ""
	@echo "  make setup                        cài phụ thuộc Python"
	@echo "  make studio [DAY=2026-08-20]      mở Remotion Studio bằng dữ liệu thật"
	@echo "  make content DAY=2026-08-20       chuẩn bị nội dung (TTS + timeline)"
	@echo "  make video   DAY=2026-08-20       dựng trọn ra MP4"
	@echo "  make still   DAY=2026-08-20 FRAME=300"
	@echo "  make reading DAY=2026-08-20       in romaji + hiragana máy sinh"
	@echo "  make assets                       soi nhạc nền và clip nền"
	@echo "  make all                          dựng mọi kịch bản chưa có MP4"
	@echo "  make clean                        xoá file máy sinh"
	@echo ""
	@echo "  make check / make new             chưa có — xem BƯỚC 6 trong kế hoạch"

## Cài phụ thuộc Python vào ĐÚNG trình thông dịch mà Makefile sẽ gọi.
##
## Dùng `python3 -m pip` chứ không dùng `pip` trần, và đây không phải chuyện
## câu nệ: máy này có hai Python (conda base và python của codespace). `pip`
## trần trỏ vào cái nào là tuỳ PATH, nên rất dễ cài xong một chỗ rồi `make`
## chạy ở chỗ kia và báo thiếu thư viện.
setup:
	@echo "Cài vào: $$(python3 -c 'import sys; print(sys.executable)')"
	@python3 -m pip install -r requirements.txt
	@echo ""
	@echo "Xong. Kiểm nhanh: make reading DAY=2026-08-20"

## Mở Studio bằng dữ liệu THẬT của một ngày.
##   make studio                 -> nạp ngày mới nhất đã dựng
##   make studio DAY=2026-08-20  -> nạp đúng ngày đó
## Chưa dựng ngày nào thì Studio rơi về props mặc định trong Composition.tsx —
## một câu, nền gradient, không tiếng. Đó là bản dự phòng, không phải video thật.
studio:
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
	@ffprobe -v error -show_entries format=duration -of csv=p=0 $(OUT)/$(DAY).mp4 \
		| xargs printf "  thời lượng %.2f giây\n"

## Render đúng 1 frame — cách nhanh nhất để bắt lỗi font và bố cục caption
still:
	$(need_day)
	@python3 -m pipeline.run $(DAY) --still $(FRAME)

## In romaji và hiragana máy sinh, để đọc đối chiếu trước khi tin nó
reading:
	$(need_day)
	@python3 -m pipeline.reading $(CONTENT)/$(DAY).json $(PROVIDER)

## Soi tài sản media — file nào thiếu, file nào còn là hàng mẫu
assets:
	@python3 scripts/check_assets.py

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
