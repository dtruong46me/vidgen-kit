# vidgen-kit — mọi lệnh đi qua đây.
#
#   make studio                      mở Remotion Studio để xem trước
#   make content DAY=2026-08-20      chỉ chuẩn bị nội dung (TTS + timeline)
#   make video   DAY=2026-08-20      dựng trọn: nội dung -> render MP4
#   make still   DAY=2026-08-20 FRAME=300   render 1 frame ra PNG
#   make all                         dựng mọi kịch bản chưa có MP4
#   make clean                       xoá file máy sinh
#
# Quy ước đường dẫn: mọi lệnh chạy từ gốc repo. Remotion cần chạy trong
# studio/ (nơi có package.json), nên đường dẫn truyền vào nó là tương đối
# so với studio/ — đó là lý do có tiền tố ../ ở PROPS và OUT.

SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSITION := Daily
STUDIO      := studio
CONTENT     := content
OUT         := out
FRAME       ?= 300

# Đường dẫn nhìn từ bên trong studio/
PROPS = ../$(CONTENT)/$(DAY).build.json
DEST  = ../$(OUT)/$(DAY).mp4
STILL = ../$(OUT)/$(DAY)-f$(FRAME).png

# Bắt lỗi thiếu DAY sớm, kèm gợi ý — thay vì để lệnh con báo lỗi khó hiểu.
define need_day
	@if [ -z "$(DAY)" ]; then \
		echo "Thiếu DAY. Ví dụ: make $@ DAY=2026-08-20"; \
		echo "Các kịch bản đang có:"; \
		ls $(CONTENT)/*.json 2>/dev/null \
			| grep -v '\.build\.json$$' | grep -v '_sample' \
			| xargs -n1 basename 2>/dev/null | sed 's/\.json$$/  /' | sed 's/^/  /' \
			|| echo "  (chưa có kịch bản nào)"; \
		exit 1; \
	fi
endef

.PHONY: help studio content video still all clean check new

help:
	@echo "vidgen-kit"
	@echo ""
	@echo "  make studio                       mở Remotion Studio"
	@echo "  make content DAY=2026-08-20       chuẩn bị nội dung (TTS + timeline)"
	@echo "  make video   DAY=2026-08-20       dựng trọn ra MP4"
	@echo "  make still   DAY=2026-08-20 FRAME=300"
	@echo "  make all                          dựng mọi kịch bản chưa có MP4"
	@echo "  make clean                        xoá file máy sinh"
	@echo ""
	@echo "  make check / make new             chưa có — xem BƯỚC 6 trong kế hoạch"

## Mở Studio bằng bản mẫu content/_sample.build.json
studio:
	cd $(STUDIO) && npx remotion studio

## Kịch bản -> giọng đọc -> content/<DAY>.build.json
content:
	$(need_day)
	@python3 scripts/legacy_build.py $(DAY)

## content/<DAY>.build.json -> out/<DAY>.mp4
video: content
	@mkdir -p $(OUT)
	cd $(STUDIO) && npx remotion render $(COMPOSITION) "$(DEST)" --props="$(PROPS)"
	@echo ""
	@echo "Xong: $(OUT)/$(DAY).mp4"
	@ffprobe -v error -show_entries format=duration -of csv=p=0 $(OUT)/$(DAY).mp4 \
		| xargs printf "  thời lượng %.2f giây\n"

## Render đúng 1 frame — cách nhanh nhất để bắt lỗi font và bố cục caption
still:
	$(need_day)
	@mkdir -p $(OUT)
	@test -f $(CONTENT)/$(DAY).build.json \
		|| { echo "Chưa có $(CONTENT)/$(DAY).build.json — chạy 'make content DAY=$(DAY)' trước."; exit 1; }
	cd $(STUDIO) && npx remotion still $(COMPOSITION) "$(STILL)" --frame=$(FRAME) --props="$(PROPS)"
	@echo "Xong: $(OUT)/$(DAY)-f$(FRAME).png"

## Dựng mọi kịch bản chưa có MP4 tương ứng
all:
	@for f in $(CONTENT)/*.json; do \
		case "$$f" in *.build.json|*_sample*) continue;; esac; \
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
	@# Bản mẫu là file cố định, phải dựng lại nếu lỡ xoá
	@git checkout -- $(CONTENT)/_sample.build.json 2>/dev/null || true
	@echo "Đã xoá file máy sinh. Kịch bản trong $(CONTENT)/ còn nguyên."

check new:
	@echo "'make $@' chưa có. Nó thuộc BƯỚC 6 trong kế hoạch triển khai."
	@exit 1
