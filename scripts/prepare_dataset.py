from pathlib import Path
import shutil
import random
import pandas as pd
from sklearn.model_selection import train_test_split

# =========================
# 你只需要改这里
# =========================
PROJECT_ROOT = Path(r"D:\traffic_sign_project")
RAW_IMAGES_DIR = PROJECT_ROOT / "raw" / "images"
ANNOTATIONS_CSV = PROJECT_ROOT / "raw" / "annotations.csv"
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "cts_yolo"

RANDOM_SEED = 42
VAL_RATIO = 0.1
TEST_RATIO = 0.1

# 推荐先过滤掉极少样本类别，先做出一个稳定版本
# 想保留全部58类，就改成 0
MIN_SAMPLES_PER_CLASS = 20

# 类别名暂时先用 class_原始类别id
# 后面你如果拿到了类别中文名映射，再来替换
# =========================


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def clip_box(x1, y1, x2, y2, w, h):
    x1 = max(0, min(float(x1), float(w) - 1))
    y1 = max(0, min(float(y1), float(h) - 1))
    x2 = max(0, min(float(x2), float(w)))
    y2 = max(0, min(float(y2), float(h)))
    return x1, y1, x2, y2


def xyxy_to_yolo(x1, y1, x2, y2, w, h):
    bw = (x2 - x1) / w
    bh = (y2 - y1) / h
    cx = (x1 + x2) / 2 / w
    cy = (y1 + y2) / 2 / h
    return cx, cy, bw, bh


def write_yaml(yaml_path: Path, names_dict: dict):
    lines = [
        f"path: {OUTPUT_DIR.as_posix()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "",
        "names:"
    ]
    for new_id, class_name in names_dict.items():
        lines.append(f"  {new_id}: {class_name}")
    yaml_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    random.seed(RANDOM_SEED)

    if not RAW_IMAGES_DIR.exists():
        raise FileNotFoundError(f"图片目录不存在: {RAW_IMAGES_DIR}")

    if not ANNOTATIONS_CSV.exists():
        raise FileNotFoundError(f"标注文件不存在: {ANNOTATIONS_CSV}")

    df = pd.read_csv(ANNOTATIONS_CSV)

    required_cols = {"file_name", "width", "height", "x1", "y1", "x2", "y2", "category"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV字段不完整，当前字段: {df.columns.tolist()}")

    df["file_name"] = df["file_name"].astype(str)
    df["category"] = df["category"].astype(int)

    print(f"原始标注条数: {len(df)}")
    print(f"原始图片数量: {df['file_name'].nunique()}")
    print(f"原始类别数: {df['category'].nunique()}")

    # 统计类别频次
    class_counts = df["category"].value_counts().sort_index()

    if MIN_SAMPLES_PER_CLASS > 0:
        keep_classes = sorted(class_counts[class_counts >= MIN_SAMPLES_PER_CLASS].index.tolist())
    else:
        keep_classes = sorted(class_counts.index.tolist())

    print(f"保留类别数: {len(keep_classes)}")
    print(f"保留类别: {keep_classes}")

    df = df[df["category"].isin(keep_classes)].copy()

    # 类别重映射，保证从0开始连续
    class_map = {old_id: new_id for new_id, old_id in enumerate(keep_classes)}
    df["new_category"] = df["category"].map(class_map)

    # 裁剪非法框
    clipped_rows = []
    for _, row in df.iterrows():
        w = float(row["width"])
        h = float(row["height"])
        x1, y1, x2, y2 = clip_box(row["x1"], row["y1"], row["x2"], row["y2"], w, h)

        if x2 <= x1 or y2 <= y1:
            continue

        clipped_rows.append({
            "file_name": row["file_name"],
            "width": int(w),
            "height": int(h),
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "old_category": int(row["category"]),
            "new_category": int(row["new_category"])
        })

    df = pd.DataFrame(clipped_rows)

    # 去掉图片不存在的样本
    existing_rows = []
    missing_images = []
    for _, row in df.iterrows():
        img_path = RAW_IMAGES_DIR / row["file_name"]
        if img_path.exists():
            existing_rows.append(row.to_dict())
        else:
            missing_images.append(row["file_name"])

    df = pd.DataFrame(existing_rows)

    print(f"有效标注条数: {len(df)}")
    print(f"有效图片数量: {df['file_name'].nunique()}")
    print(f"缺失图片数量: {len(set(missing_images))}")

    # 有些图片在过滤后可能没有标注了，这里只保留仍然有框的图片
    image_level = (
        df.groupby("file_name")
        .agg(main_class=("new_category", "first"))
        .reset_index()
    )

    # 训练/验证/测试划分
    train_files, temp_files = train_test_split(
        image_level,
        test_size=VAL_RATIO + TEST_RATIO,
        random_state=RANDOM_SEED,
        stratify=image_level["main_class"]
    )

    relative_test_ratio = TEST_RATIO / (VAL_RATIO + TEST_RATIO)

    val_files, test_files = train_test_split(
        temp_files,
        test_size=relative_test_ratio,
        random_state=RANDOM_SEED,
        stratify=temp_files["main_class"]
    )

    split_map = {}
    for f in train_files["file_name"].tolist():
        split_map[f] = "train"
    for f in val_files["file_name"].tolist():
        split_map[f] = "val"
    for f in test_files["file_name"].tolist():
        split_map[f] = "test"

    # 建目录
    for sub in ["train", "val", "test"]:
        ensure_dir(OUTPUT_DIR / "images" / sub)
        ensure_dir(OUTPUT_DIR / "labels" / sub)

    # 写类别映射
    class_map_rows = []
    names_dict = {}
    for old_id, new_id in class_map.items():
        class_name = f"class_{old_id}"
        class_map_rows.append({
            "old_category": old_id,
            "new_category": new_id,
            "class_name": class_name
        })
        names_dict[new_id] = class_name

    class_map_df = pd.DataFrame(class_map_rows).sort_values("new_category")
    class_map_df.to_csv(OUTPUT_DIR / "class_map.csv", index=False, encoding="utf-8-sig")

    # 拷贝图片 + 写标签
    grouped = df.groupby("file_name")
    total_written = 0

    for file_name, group in grouped:
        split = split_map.get(file_name)
        if split is None:
            continue

        src_img = RAW_IMAGES_DIR / file_name
        dst_img = OUTPUT_DIR / "images" / split / file_name
        dst_label = OUTPUT_DIR / "labels" / split / f"{Path(file_name).stem}.txt"

        shutil.copy2(src_img, dst_img)

        label_lines = []
        for _, row in group.iterrows():
            w = float(row["width"])
            h = float(row["height"])
            cx, cy, bw, bh = xyxy_to_yolo(row["x1"], row["y1"], row["x2"], row["y2"], w, h)

            # YOLO格式：class cx cy w h
            label_lines.append(
                f"{int(row['new_category'])} "
                f"{cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"
            )

        dst_label.write_text("\n".join(label_lines), encoding="utf-8")
        total_written += 1

    # 写 data.yaml
    write_yaml(OUTPUT_DIR / "data.yaml", names_dict)

    # 写统计信息
    stats_text = []
    stats_text.append(f"total_annotations={len(df)}")
    stats_text.append(f"total_images={df['file_name'].nunique()}")
    stats_text.append(f"num_classes={len(class_map)}")
    stats_text.append(f"train_images={len(train_files)}")
    stats_text.append(f"val_images={len(val_files)}")
    stats_text.append(f"test_images={len(test_files)}")
    (OUTPUT_DIR / "dataset_stats.txt").write_text("\n".join(stats_text), encoding="utf-8")

    print("===================================")
    print("数据集转换完成")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"共写入图片: {total_written}")
    print(f"train: {len(train_files)}")
    print(f"val:   {len(val_files)}")
    print(f"test:  {len(test_files)}")
    print("data.yaml 已生成")
    print("class_map.csv 已生成")
    print("===================================")


if __name__ == "__main__":
    main()