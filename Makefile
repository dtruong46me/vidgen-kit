# vidgen-kit — mọi lệnh đi qua đây.
#
# Bảng lệnh KHÔNG viết ở đây. Mỗi lệnh tự mang dòng mô tả `#.` ngay trên chính
# nó, và `make help` in ra từ đó. Một chỗ duy nhất, không có bản thứ hai để trôi
# lệch — cùng lý do khiến paths.py là chỗ duy nhất biết bố cục thư mục.
#
#   #:  tiêu đề một nhóm lệnh   (in ra)
#   #.  một dòng của bảng lệnh, dạng `cách gõ | mô tả`   (in ra)
#   ##  giải thích dài cho người mở file này ra đọc   (KHÔNG in ra)
#
# Dây chuyền một ngày — mỗi bước ghi ra file mở lên xem được:
#
#   make new       content/<ngày>/script.json      kịch bản, NGƯỜI viết
#   make build     mp3 + content/<ngày>/build.json nguyên liệu, MÁY soạn
#   make video     out/<ngày>/<ngày>.mp4 + ảnh bìa file hình, Remotion render
#   make check     out/<ngày>-check/               số đo + trang soát
#   make export    out/<ngày>/                     gói đăng
#   make release   video + check + export, một lệnh
#
# Sơ đồ đầy đủ, và nên gộp bước nào khi nào: README.md.
#
# TÊN LỆNH — ba luật, đoán được tên lệnh mà không phải tra:
#
#   <việc>        làm cho MỘT ngày hoặc một khoảng ngày    build, video, check, export…
#   <việc>-all    làm cho MỌI ngày còn thiếu, không nhận ngày  build-all, video-all, export-all
#   <sổ>-list     chỉ IN một cuốn sổ ra, không sinh file   shots-list, bank-list
#
# Tên lệnh là tên THÀNH PHẨM khi có thể: `build` ra build.json, `video` ra MP4.
#
# TỪ DÙNG TRONG FILE NÀY — mỗi từ đúng MỘT nghĩa, đừng dùng lẫn:
#
#   soạn         Python sinh ra nguyên liệu. Không bao giờ có nghĩa là render.
#   render       Remotion vẽ ra file hình (MP4, ảnh bìa, ảnh tĩnh).
#   kiểm         MÁY tự kết luận đạt/hỏng (số đo của `check`, đối chiếu của `shots-list`).
#   soát         MẮT NGƯỜI kết luận (trang soát, ảnh tĩnh, romaji).
#   gói          chép và viết ra out/<ngày>/. Chỉ `export` làm việc này.
#   nguyên liệu  giọng đọc mp3 + build.json. Sản phẩm của `make build`.
#   gói đăng     thư mục out/<ngày>/, đủ thứ để mở ra và đăng.
#   lời đăng     chữ ĐỂ ĐĂNG, đi ra out/<ngày>/caption.txt. Không hiện trong video.
#   caption      chữ TRÊN HÌNH, tức phụ đề. Không phải lời đăng.
#   màn chữ      một lần chữ đổi trên hình. Câu dài chia mảnh thì một cảnh có
#                nhiều màn chữ — nên `check` đếm theo màn chữ, không theo cảnh.
#   ngày         đơn vị đếm của MỌI lệnh (DAY=2026-08-20). Không gọi là "kịch bản".
#   sổ clip      library/shots.json: nguồn, tác giả, giấy phép, tag của clip VÀ nhạc nền.
#   thư viện     thư viện Python/Node mà `make setup` cài. KHÔNG phải kho clip.
#
# Quy ước đường dẫn: mọi lệnh chạy từ gốc repo. Remotion cần cwd là studio/ (nơi
# có package.json), nên đường dẫn truyền vào nó phải có tiền tố ../ — quy ước đó
# nằm gọn trong pipeline/render.py. Còn content/ và out/ bày ra sao thì chỉ
# pipeline/paths.py biết: Makefile HỎI nó (`python3 -m pipeline.paths --list
# --unrendered`…), không tự thử `[ -f out/$$day/$$day.mp4 ]`. Ngoại lệ duy nhất
# là `rm` trong `clean` — xoá thì phải gọi đúng tên thứ bị xoá.

SHELL := /bin/bash
.DEFAULT_GOAL := help

STUDIO  := studio
CONTENT := content
OUT     := out

# --------------------------------------------------------------------------
# THAM SỐ — gõ kèm lệnh, dạng TÊN=giá trị
# --------------------------------------------------------------------------

# CHỌN NGÀY. Mọi lệnh nhận DAY=. Riêng `export` và `release` nhận thêm cả khoảng
# (FROM/TO/MONTH). Muốn làm MỌI ngày thì không phải là tham số nữa, mà là lệnh
# đuôi `-all`: `build-all`, `video-all`, `export-all`.
DAY      ?=
FROM     ?=
TO       ?=
MONTH    ?=

# Ghép bốn thứ trên thành MỘT chuỗi mà pipeline/paths.py hiểu, ví dụ
# `2026-09-12..2026-09-30`. Đọc chuỗi đó là việc của paths.py; Makefile không tự
# so ngày, không tự đoán tháng có bao nhiêu ngày. Bỏ TO thì ra `2026-09-12..`
# (tới ngày cuối cùng), bỏ FROM thì ra `..2026-09-30` (từ ngày đầu tiên).
DAYS := $(strip $(if $(DAY),$(DAY),$(if $(MONTH),$(MONTH),$(if $(FROM)$(TO),$(FROM)..$(TO)))))

# Của `make still`: frame nào. Có mặc định, nên gõ thiếu vẫn chạy — ra frame 300.
FRAME    ?= 300

# Của `make reading`: cutlet hay pykakasi. Để trống thì kịch bản tự quyết.
PROVIDER ?=

# Của `make shots-find` và `make shots-get`: lấy clip ở đâu (pexels/pixabay).
# Tên khác PROVIDER là cố ý — gộp một tên thì `make reading` sẽ đi tìm provider
# tên "pexels".
SOURCE   ?= pexels

# Của `make new`: để trống = có ANTHROPIC_API_KEY thì nhờ Claude viết, không thì
# lấy ngân hàng. `bank` ép lấy ngân hàng; `opus`/`sonnet`/`haiku` ép gọi Claude.
MODEL    ?=

# Của họ `make shots-*`, không có mặc định — thiếu thì lệnh tự nhắc:
#   Q=       chuỗi tìm kiếm            (shots-find)
#   ID=      id clip trên nguồn        (shots-get)
#   NAME=    tên đặt cho clip          (shots-get, shots-add)
#   TAGS=    tag, ngăn bằng dấu phẩy   (shots-get, shots-add)
#   FILE= URL= AUTHOR= LICENSE=        (shots-add)

# --------------------------------------------------------------------------
# Bắt lỗi thiếu tham số SỚM, kèm gợi ý — thay vì để lệnh con báo lỗi khó hiểu
# --------------------------------------------------------------------------

## Cho lệnh chỉ nhận đúng MỘT ngày.
define need_day
	@if [ -z "$(DAY)" ]; then \
		echo "Thiếu DAY. Ví dụ: make $@ DAY=2026-08-20"; \
		echo ""; \
		days=$$(python3 -m pipeline.paths --list 2>/dev/null); \
		n=$$(echo "$$days" | grep -c . ); \
		if [ "$$n" -eq 0 ]; then \
			echo "Chưa có ngày nào. Tạo một ngày: make new DAY=2026-09-10"; \
		elif [ "$$n" -le 8 ]; then \
			echo "Các ngày đang có kịch bản:"; \
			echo "$$days" | sed 's/^/  /'; \
		else \
			echo "Có $$n ngày. 8 ngày gần nhất:"; \
			echo "$$days" | tail -8 | sed 's/^/  /'; \
			echo "  (đủ danh sách: python3 -m pipeline.paths --list)"; \
		fi; \
		exit 1; \
	fi
endef

## Cho lệnh nhận được cả khoảng ngày (`export`, `release`).
define need_days
	@if [ -z "$(DAYS)" ]; then \
		echo "Thiếu ngày. Ví dụ:"; \
		echo "  make $@ DAY=2026-09-12                    một ngày"; \
		echo "  make $@ FROM=2026-09-12 TO=2026-09-30     từ ngày tới ngày"; \
		echo "  make $@ FROM=2026-09-12                   tới ngày cuối cùng"; \
		echo "  make $@ TO=2026-09-30                     từ ngày đầu tiên"; \
		echo "  make $@ MONTH=2026-09                     cả tháng"; \
		exit 1; \
	fi
endef

## Tên cũ của một lệnh đã đổi tên: in một dòng nhắc rồi chạy tên mới, cùng mọi
## tham số (DAY=, FROM=… đi theo qua MAKEFLAGS). Giữ một thời gian cho quen tay,
## rồi xoá hẳn — hai tên cho một việc là đúng cái lộn xộn vừa dọn.
define renamed
	@echo "[tên cũ] 'make $@' giờ là 'make $(1)'. Lần này vẫn chạy; lần sau gõ tên mới."
	@$(MAKE) --no-print-directory $(1)
endef

.PHONY: help setup new bank-list build video check export release studio still \
        thumbnail reading shots-list shots-find shots-get shots-add \
        build-all video-all export-all clean clean-all \
        content content-all bank shots assets all

## In bảng lệnh, đọc thẳng từ các dòng `#:` và `#.` trong chính file này.
## Sửa mô tả ở cạnh lệnh là bảng này đổi theo — không có bản thứ hai để quên.
help:
	@awk ' \
	  function row(t,   i, a, b) { \
	    i = index(t, " | "); \
	    if (i == 0) { printf "  %s\n", t; return } \
	    a = substr(t, 1, i - 1); b = substr(t, i + 3); \
	    sub(/[ \t]+$$/, "", a); \
	    printf "  %-44s %s\n", a, b; \
	  } \
	  /^#: / { printf "\n%s\n", substr($$0, 4) } \
	  /^#\. / { row(substr($$0, 4)) } \
	  END { print "" } \
	' $(MAKEFILE_LIST)

#: MỘT NGÀY — từ kịch bản tới lúc đăng

## Viết content/<DAY>/script.json. Không có khoá thì lấy ngân hàng, không gọi
## mạng. KHÔNG BAO GIỜ đè kịch bản đã có — file trong content/ là file người viết.
#. make new DAY=2026-09-10 | viết kịch bản mới [MODEL=bank|opus|sonnet|haiku]
new:
	$(need_day)
	@python3 -m pipeline.new $(DAY) $(MODEL)

## Mỗi mục: bao nhiêu câu, ước lượng bao nhiêu giây, đã dùng cho ngày nào.
#. make bank-list | in ngân hàng kịch bản viết sẵn
bank-list:
	@python3 -m pipeline.new --bank

## Kịch bản -> content/<DAY>/build.json, qua năm việc: kiểm kịch bản, đọc TTS
## từng câu, sinh romaji, chọn clip cho cảnh bỏ trống, đổi giây ra frame.
## Tên là `build` vì thành phẩm là build.json — KHÔNG phải `tts`: TTS chỉ là
## một trong năm việc, gọi `tts` thì tưởng nó không đụng clip hay timeline.
## Chỉ soạn, không render: đây là lúc rẻ để sửa chữ, vì chưa tốn CPU nào.
#. make build DAY=2026-08-20 | soạn nguyên liệu: giọng đọc + chọn clip + build.json
build:
	$(need_day)
	@python3 -m pipeline.run $(DAY)

## Soạn nguyên liệu (như `make build`) rồi render thẳng vào out/<DAY>/.
## Ảnh bìa render liền sau MP4, ở frame mà build.json đã ghi sẵn (thumbnailFrame).
#. make video DAY=2026-08-20 | soạn nguyên liệu rồi render MP4 + ảnh bìa
video:
	$(need_day)
	@python3 -m pipeline.run $(DAY) --render

## Hai phần, hai người kết luận khác nhau:
##   SỐ ĐO   — máy tự kết luận đạt/hỏng. Đếm frame trên chính MP4, không tin
##             `duration × fps` (độ dài container tính cả luồng tiếng).
##   TRANG SOÁT — mắt người kết luận. MỘT ảnh cho MỖI MÀN CHỮ, không phải mỗi
##             cảnh: câu dài chia mảnh thì lấy giữa cảnh là mảnh đầu không ai
##             nhìn thấy, mà trang này sinh ra chính để soi chữ.
#. make check DAY=2026-08-20 | kiểm số đo MP4 + trang soát từng màn chữ
check:
	$(need_day)
	@python3 -m pipeline.check $(DAY)

## Gói out/<ngày>/ thành thư mục đăng được: lời đăng, lời Nhật–Việt, giọng đọc
## từng câu, metadata và ghi công tài sản.
##
## Lệnh này CHỈ ĐỌC build.json và MP4 đã có — nó không gọi TTS, không chọn clip,
## không tính frame, nên chạy lại bao nhiêu lần cũng ra thư mục giống hệt nhau.
## Ngoại lệ DUY NHẤT: thiếu ảnh bìa hoặc ảnh bìa cũ hơn build.json thì nó gọi
## Remotion render lại đúng một frame — gói không có ảnh bìa là gói chưa đăng được.
#. make export DAY=2026-08-20 | gói out/<ngày>/ để đăng — chỉ đọc, không render lại
#. make export FROM=2026-09-12 TO=2026-09-30 | gói cả khoảng ngày — xem CHỌN NHIỀU NGÀY
export:
	$(need_days)
	@python3 -m pipeline.export $(DAYS)

## Ba bước một lệnh: video (soạn + render) -> check (kiểm + trang soát) -> export (gói).
##
## Trong MỘT ngày thì dừng ở bước hỏng: render hỏng thì không kiểm, kiểm FAIL thì
## không gói — không đóng gói một file dở dang.
##
## Nhưng một ngày hỏng KHÔNG chặn các ngày sau: render cả tháng mất hàng giờ,
## dừng giữa chừng vì một ngày thì sáng ra chẳng còn gì. Cuối lệnh in ra ngày nào
## hỏng, và thoát bằng mã lỗi nếu có.
#. make release DAY=2026-08-20 | video -> check -> export, một lệnh
#. make release FROM=2026-09-12 TO=2026-09-30 | cả khoảng ngày — xem CHỌN NHIỀU NGÀY
release:
	$(need_days)
	@days=$$(python3 -m pipeline.paths $(DAYS)) || exit 1; \
	failed=""; \
	for day in $$days; do \
		echo ""; \
		echo "==> $$day"; \
		python3 -m pipeline.run $$day --render \
			&& python3 -m pipeline.check $$day \
			&& python3 -m pipeline.export $$day \
			|| failed="$$failed $$day"; \
	done; \
	echo ""; \
	if [ -n "$$failed" ]; then \
		echo "Hỏng:$$failed — cuộn lên xem lỗi của từng ngày."; \
		exit 1; \
	fi; \
	echo "Xong. Mỗi ngày một thư mục $(OUT)/<ngày>/: <ngày>.mp4, <ngày>-thumbnail.png,"; \
	echo "caption.txt, description.txt, script.txt, credits.txt, metadata.json, audio/."; \
	echo "Trang soát: $(OUT)/<ngày>-check/index.html"

#: SOÁT BẰNG MẮT — bốn lệnh này không sinh ra thứ gì để đăng

## Mở Studio bằng dữ liệu THẬT của một ngày.
##   make studio                 -> ngày vừa soạn gần đây nhất (theo thời gian sửa build.json)
##   make studio DAY=2026-08-20  -> đúng ngày đó
## Chưa soạn ngày nào thì Studio rơi về props mặc định viết thẳng trong
## Composition.tsx — một câu, nền gradient, không tiếng. Đó là bản dự phòng để
## Studio có gì đó mà mở, không phải video thật.
## Chọn ngày, dựng đường dẫn ../ và kiểm node_modules đều nằm trong
## pipeline/render.py — cùng chỗ với render video.
#. make studio [DAY=2026-08-20] | mở Remotion Studio bằng build.json thật
studio:
	@python3 -m pipeline.render studio $(DAY)

## Cách nhanh nhất để bắt lỗi font và bố cục caption: render đúng một frame.
## Bỏ FRAME thì ra frame 300. Ảnh nằm NGOÀI thư mục đăng (out/<ngày>-f<N>.png)
## vì nó là đồ soát, không phải đồ để đăng.
#. make still DAY=2026-08-20 [FRAME=300] | render 1 frame ra PNG để soát
still:
	$(need_day)
	@python3 -m pipeline.run $(DAY) --still $(FRAME)

## Ảnh bìa: frame mà tiêu đề ngày VÀ câu chào おはようございます cùng hiện đủ.
## Frame đó do timeline.py chọn và ghi sẵn vào build.json (thumbnailFrame) —
## lệnh này không tự tính. Như `still`, nó chỉ vẽ từ build.json đã có, nên sửa
## kịch bản thì phải `make build` trước.
## Thường không phải gõ: `make video` render kèm, `make export` render nốt nếu thiếu.
#. make thumbnail DAY=2026-08-20 | render riêng ảnh bìa ra out/<ngày>/
thumbnail:
	$(need_day)
	@python3 -m pipeline.run $(DAY) --thumbnail

## Romaji và hiragana đều do máy sinh, không gõ tay. Lệnh này in ra để đọc đối
## chiếu trước khi tin nó. Máy đọc sai chữ nào thì thêm cách đọc vào
## library/readings.json — bảng đó áp cho mọi ngày.
#. make reading DAY=2026-08-20 | in romaji + hiragana để soát [PROVIDER=cutlet]
reading:
	$(need_day)
	@python3 -m pipeline.reading $(DAY) $(PROVIDER)

#: SỔ CLIP VÀ NHẠC NỀN

## In cả sổ, và kiểm: file có thật không, khổ hình và fps thật là bao nhiêu, ngày
## nào đang dùng clip nào, dòng nào thiếu nguồn hoặc giấy phép.
## Thứ gì ffprobe đo được thì KHÔNG chép vào sổ — sổ chỉ giữ thứ không đo được.
#. make shots-list | in sổ clip + nhạc nền, kiểm file thật
shots-list:
	@python3 -m pipeline.library

## Cần khoá API trong .env. Không có khoá thì dùng `shots-add` — làm được mọi
## thứ đường API làm, chỉ tốn công tìm clip bằng tay.
#. make shots-find Q="tea ceremony" | tìm clip trên Pexels/Pixabay [SOURCE=pexels]
shots-find:
	@if [ -z "$(Q)" ]; then echo 'Thiếu Q. Ví dụ: make shots-find SOURCE=pexels Q="tea ceremony"'; exit 1; fi
	@python3 -m pipeline.fetch find $(SOURCE) "$(Q)"

## Tải và ghi sổ trong CÙNG một lệnh — đừng tách ra, tách ra là sẽ có ngày tải
## xong quên ghi, rồi không ai trả lời được "clip này ở đâu ra".
#. make shots-get ID=8507912 NAME=matcha-whisk | tải một clip rồi ghi sổ ngay [SOURCE= TAGS=]
shots-get:
	@if [ -z "$(ID)" ] || [ -z "$(NAME)" ]; then \
		echo 'Thiếu ID hoặc NAME.'; \
		echo 'Ví dụ: make shots-get SOURCE=pexels ID=8507912 NAME=matcha-whisk TAGS=tea,matcha'; \
		exit 1; \
	fi
	@python3 -m pipeline.fetch get $(SOURCE) $(ID) $(NAME) "$(TAGS)"

## Nhận một file đã tải sẵn vào sổ. URL, AUTHOR, LICENSE là bắt buộc — đó đúng
## là ba thứ ffprobe không đo được.
#. make shots-add FILE=... NAME=... | ghi file đã tải sẵn vào sổ (cần URL= AUTHOR= LICENSE=)
shots-add:
	@if [ -z "$(FILE)" ] || [ -z "$(NAME)" ]; then \
		echo 'Thiếu FILE hoặc NAME.'; \
		echo 'Ví dụ: make shots-add FILE=~/tai/san-vuon.mp4 NAME=zen-garden \'; \
		echo '                      URL=https://... AUTHOR="Tên" LICENSE="CC0" TAGS=garden,calm'; \
		exit 1; \
	fi
	@python3 -m pipeline.fetch add "$(FILE)" $(NAME) "$(URL)" "$(AUTHOR)" "$(LICENSE)" "$(TAGS)"

#: MỌI NGÀY MỘT LỆNH — đuôi `-all`, không nhận tham số ngày

## Soạn nguyên liệu cho mọi ngày chưa có build.json. Khác `video-all` ở chỗ
## KHÔNG render: dùng khi muốn soạn cả tháng rồi `make export-all` lấy lời đăng
## và lời Nhật–Việt ra soát, trước khi tốn CPU render.
## Ngày nào đã có build.json thì bỏ qua — giọng đọc có cache nên soạn lại rẻ,
## nhưng bỏ qua vẫn nhanh hơn. Soạn hỏng một ngày thì DỪNG: soạn chỉ mất vài
## giây, sửa kịch bản rồi chạy lại là tiếp đúng chỗ đó.
#. make build-all | soạn nguyên liệu mọi ngày chưa có build.json
build-all:
	@days=$$(python3 -m pipeline.paths --list --unbuilt) || exit 1; \
	if [ -z "$$days" ]; then \
		echo "Mọi ngày có kịch bản đều đã có build.json — không có gì để soạn."; \
		exit 0; \
	fi; \
	for day in $$days; do \
		echo "==> $$day"; \
		python3 -m pipeline.run $$day || exit 1; \
	done

## Render mọi ngày chưa có MP4. Không kiểm, không gói — muốn cả ba bước thì
## `make release FROM=… TO=…`.
## Render hỏng một ngày thì KHÔNG dừng, cùng lý do với `release`: render cả
## tháng mất hàng giờ. Cuối lệnh in ra ngày nào hỏng và thoát bằng mã lỗi.
#. make video-all | render mọi ngày chưa có MP4
video-all:
	@days=$$(python3 -m pipeline.paths --list --unrendered) || exit 1; \
	if [ -z "$$days" ]; then \
		echo "Mọi ngày có kịch bản đều đã có MP4 — không có gì để render."; \
		exit 0; \
	fi; \
	failed=""; \
	for day in $$days; do \
		echo ""; \
		echo "==> $$day"; \
		python3 -m pipeline.run $$day --render || failed="$$failed $$day"; \
	done; \
	echo ""; \
	if [ -n "$$failed" ]; then \
		echo "Hỏng:$$failed — cuộn lên xem lỗi của từng ngày."; \
		exit 1; \
	fi

## Gói MỌI ngày đã có build.json. Dùng sau khi đã soạn cả tháng.
#. make export-all | gói mọi ngày đã có build.json
export-all:
	@python3 -m pipeline.export --all

#: MÁY VÀ DỌN DẸP

## Cài thư viện vào ĐÚNG trình thông dịch mà Makefile sẽ gọi.
##
## Dùng `python3 -m pip` chứ không dùng `pip` trần, và đây không phải chuyện câu
## nệ: máy này có hai Python (conda base và python của codespace). `pip` trần trỏ
## vào cái nào là tuỳ PATH, nên rất dễ cài xong một chỗ rồi `make` chạy ở chỗ kia
## và báo thiếu thư viện.
##
## Node cũng cùng bẫy đó, theo kiểu WSL: PATH của Windows lọt vào nên `npm` có
## thể là bản Windows. studio/node_modules không vào git, thiếu nó thì `npx
## remotion` chỉ báo "could not determine executable to run".
#. make setup | cài thư viện Python + Node, tạo .env nếu chưa có
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
		echo "Không điền cũng chạy được mọi lệnh soạn và render."; \
	else \
		echo ""; \
		echo "Đã có .env, giữ nguyên (không đè lên khoá bạn đã điền)."; \
	fi
	@echo ""
	@echo "Xong. Thử nhanh: make reading DAY=2026-08-20"

## Hai mức xoá, vì hai thứ đắt khác hẳn nhau:
##   clean      nguyên liệu — soạn lại mất VÀI GIÂY mỗi ngày.
##   clean-all  thêm cả out/ — render lại mất ~5 PHÚT mỗi ngày, cả tháng là
##              hàng giờ. Tách riêng để không ai mất video chỉ vì muốn xoá cache.
## Tách lệnh thay vì hỏi "gõ yes": hỏi thì script chạy tự động sẽ treo.
#. make clean | xoá nguyên liệu (build.json, cache, mp3) — MP4 còn nguyên
clean:
	rm -f $(CONTENT)/*/build.json $(CONTENT)/*/.cache.json
	rm -rf $(STUDIO)/public/audio/20*/
	@echo "Đã xoá nguyên liệu: build.json, .cache.json, giọng đọc mp3."
	@echo "Còn nguyên: kịch bản, nhạc nền, clip nền, sổ clip, và MỌI THỨ trong $(OUT)/."
	@echo "Soạn lại: 'make build DAY=…' hoặc 'make build-all' — vài giây mỗi ngày."
	@echo "(Chưa soạn lại thì 'make export' chưa gói được, vì nó đọc build.json.)"

#. make clean-all | xoá thêm out/: MP4, ảnh bìa, gói đăng — render lại mất hàng giờ
clean-all: clean
	rm -rf $(OUT)
	@echo "Đã xoá thêm $(OUT)/: MỌI MP4, ảnh bìa, gói đăng và trang soát."
	@echo "Render lại: 'make video-all' — khoảng 5 phút mỗi ngày."

#: TÊN CŨ — vẫn chạy, in một dòng nhắc; sẽ xoá khi đã quen tên mới
#. make content      | -> make build
#. make content-all  | -> make build-all
#. make all          | -> make video-all
#. make shots        | -> make shots-list   (make assets cũng vậy)
#. make bank         | -> make bank-list
content:
	$(call renamed,build)
content-all:
	$(call renamed,build-all)
all:
	$(call renamed,video-all)
shots assets:
	$(call renamed,shots-list)
bank:
	$(call renamed,bank-list)

#: CHỌN NHIỀU NGÀY — chỉ `export` và `release` nhận, thay cho DAY=
#. DAY=2026-09-12                | đúng một ngày
#. FROM=2026-09-12 TO=2026-09-30 | từ ngày tới ngày, TÍNH CẢ HAI ĐẦU
#. FROM=2026-09-12               | từ ngày đó tới ngày cuối cùng đang có
#. TO=2026-09-30                 | từ ngày đầu tiên tới ngày đó
#. MONTH=2026-09                 | cả tháng
