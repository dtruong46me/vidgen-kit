/**
 * Note: When using the Node.JS APIs, the config file
 * doesn't apply. Instead, pass options directly to the APIs.
 *
 * All configuration options: https://remotion.dev/docs/config
 */

import { Config } from "@remotion/cli/config";
import { enableTailwind } from "@remotion/tailwind-v4";

Config.setRspack(true);
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.overrideBundlerConfig(enableTailwind);

/**
 * Ghì bộ nhớ lại — máy dựng chỉ có 2 nhân và khoảng 3 GB RAM trống, không swap.
 *
 * Clip nền là video dọc 1080×1920, mỗi frame giải nén ra khoảng 6 MB. Với thiết
 * lập mặc định, compositor (tiến trình Rust lo giải mã cho OffthreadVideo) bị
 * kernel giết bằng SIGTERM ở khoảng frame 251 — đúng lúc clip thứ hai được mở
 * và hai luồng cùng giữ frame đã giải nén.
 *
 * Hai số dưới đây đổi tốc độ lấy sự ổn định. Máy khoẻ hơn thì nâng lên hoặc
 * xoá hẳn; đây không phải giới hạn của code mà là giới hạn của phần cứng.
 */
Config.setConcurrency(1);
Config.setOffthreadVideoCacheSizeInBytes(256 * 1024 * 1024);
