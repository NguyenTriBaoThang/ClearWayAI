"""ClearWayAI Computer Vision Evaluation Metrics for Vietnamese Mixed Traffic.

Implements:
1. Intersection over Union (IoU).
2. All-point continuous Average Precision (AP) calculation (COCO / PASCAL standard).
3. Mean Average Precision (mAP@0.5 and mAP@0.5:0.95) across all 7 vehicle classes.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ai.detection.yolo_detector import CLASS_NAMES, Detection, compute_iou


def compute_ap(
    recalls: list[float] | np.ndarray,
    precisions: list[float] | np.ndarray,
    use_11_point: bool = False,
) -> float:
    """Compute Average Precision (AP) from recall and precision arrays.

    Uses either continuous envelope integration (modern COCO / VOC 2010+)
    or 11-point interpolated sampling (VOC 2007).
    """
    rec = np.array(recalls, dtype=float)
    prec = np.array(precisions, dtype=float)

    if len(rec) == 0 or len(prec) == 0:
        return 0.0

    if use_11_point:
        ap = 0.0
        for t in np.linspace(0.0, 1.0, 11):
            mask = rec >= t
            p = np.max(prec[mask]) if np.any(mask) else 0.0
            ap += p / 11.0
        return float(ap)

    # All-point continuous interpolation
    mrec = np.concatenate(([0.0], rec, [1.0]))
    mpre = np.concatenate(([0.0], prec, [0.0]))

    # Compute maximum precision envelope from right to left
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])

    # Find points where recall changes
    indices = np.where(mrec[1:] != mrec[:-1])[0]
    ap = float(np.sum((mrec[indices + 1] - mrec[indices]) * mpre[indices + 1]))
    return max(0.0, min(1.0, ap))


def evaluate_detections(
    ground_truths: list[list[Detection]],
    predictions: list[list[Detection]],
    iou_threshold: float = 0.5,
) -> dict[str, Any]:
    """Evaluate detector performance against ground truth over a set of frames.

    Args:
        ground_truths: Per-frame ground truth detections.
        predictions: Per-frame predicted detections.
        iou_threshold: IoU overlap threshold for true positive match.

    Returns:
        Dictionary containing overall mAP, per-class AP, precision, recall, and counts.
    """
    if len(ground_truths) != len(predictions):
        raise ValueError(
            f"Frame count mismatch: {len(ground_truths)} GT frames vs {len(predictions)} pred frames"
        )

    class_results: dict[str, dict[str, Any]] = {}
    total_tp = 0
    total_fp = 0
    total_fn = 0
    ap_list: list[float] = []

    for cls_id, cls_name in enumerate(CLASS_NAMES):
        # Collect all predictions and ground truths for this class
        all_pred_scores: list[float] = []
        all_pred_matches: list[int] = []  # 1 if TP, 0 if FP
        total_gt_class = 0

        for frame_idx in range(len(ground_truths)):
            gt_frame = [d for d in ground_truths[frame_idx] if d.class_id == cls_id]
            pred_frame = [d for d in predictions[frame_idx] if d.class_id == cls_id]

            total_gt_class += len(gt_frame)
            gt_matched = [False] * len(gt_frame)

            # Sort predictions in this frame by confidence descending
            sorted_preds = sorted(pred_frame, key=lambda d: d.confidence, reverse=True)

            for pred in sorted_preds:
                all_pred_scores.append(pred.confidence)

                best_iou = 0.0
                best_gt_idx = -1

                for gt_idx, gt in enumerate(gt_frame):
                    if not gt_matched[gt_idx]:
                        iou = compute_iou(pred.bbox, gt.bbox)
                        if iou > best_iou:
                            best_iou = iou
                            best_gt_idx = gt_idx

                if best_iou >= iou_threshold and best_gt_idx >= 0:
                    gt_matched[best_gt_idx] = True
                    all_pred_matches.append(1)  # TP
                else:
                    all_pred_matches.append(0)  # FP

        # Calculate AP, Precision, Recall for this class
        if total_gt_class == 0 and len(all_pred_scores) == 0:
            # Class not present in GT nor predicted
            class_results[cls_name] = {
                "tp": 0,
                "fp": 0,
                "fn": 0,
                "precision": 1.0,
                "recall": 1.0,
                "f1": 1.0,
                "ap": 1.0,
            }
            ap_list.append(1.0)
            continue

        if total_gt_class == 0 and len(all_pred_scores) > 0:
            # Ghost predictions for absent class
            fp_count = len(all_pred_scores)
            class_results[cls_name] = {
                "tp": 0,
                "fp": fp_count,
                "fn": 0,
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "ap": 0.0,
            }
            ap_list.append(0.0)
            total_fp += fp_count
            continue

        if len(all_pred_scores) == 0 and total_gt_class > 0:
            # Model missed all instances
            class_results[cls_name] = {
                "tp": 0,
                "fp": 0,
                "fn": total_gt_class,
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "ap": 0.0,
            }
            ap_list.append(0.0)
            total_fn += total_gt_class
            continue

        # Sort all dataset predictions for this class by confidence descending
        sorted_indices = np.argsort(all_pred_scores)[::-1]
        matches_sorted = np.array(all_pred_matches)[sorted_indices]

        tp_cumsum = np.cumsum(matches_sorted)
        fp_cumsum = np.cumsum(1 - matches_sorted)

        precisions = tp_cumsum / (tp_cumsum + fp_cumsum)
        recalls = tp_cumsum / total_gt_class

        ap = compute_ap(recalls, precisions)
        ap_list.append(ap)

        final_tp = int(tp_cumsum[-1]) if len(tp_cumsum) > 0 else 0
        final_fp = int(fp_cumsum[-1]) if len(fp_cumsum) > 0 else 0
        final_fn = max(0, total_gt_class - final_tp)

        prec_val = final_tp / max(1, final_tp + final_fp)
        rec_val = final_tp / max(1, total_gt_class)
        f1_val = 2 * (prec_val * rec_val) / max(1e-9, prec_val + rec_val)

        total_tp += final_tp
        total_fp += final_fp
        total_fn += final_fn

        class_results[cls_name] = {
            "tp": final_tp,
            "fp": final_fp,
            "fn": final_fn,
            "precision": round(float(prec_val), 4),
            "recall": round(float(rec_val), 4),
            "f1": round(float(f1_val), 4),
            "ap": round(float(ap), 4),
        }

    overall_map = float(np.mean(ap_list)) if ap_list else 0.0
    overall_prec = total_tp / max(1, total_tp + total_fp)
    overall_rec = total_tp / max(1, total_tp + total_fn)
    overall_f1 = 2 * (overall_prec * overall_rec) / max(1e-9, overall_prec + overall_rec)

    return {
        "map_50": round(overall_map, 4),
        "precision": round(float(overall_prec), 4),
        "recall": round(float(overall_rec), 4),
        "f1": round(float(overall_f1), 4),
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "classes": class_results,
    }


def evaluate_map_range(
    ground_truths: list[list[Detection]],
    predictions: list[list[Detection]],
    start_iou: float = 0.50,
    end_iou: float = 0.95,
    step: float = 0.05,
) -> float:
    """Calculate mAP@[start:end] (e.g. mAP@0.5:0.95 over 10 thresholds)."""
    thresholds = np.arange(start_iou, end_iou + 1e-4, step)
    maps: list[float] = []

    for t in thresholds:
        res = evaluate_detections(ground_truths, predictions, iou_threshold=float(t))
        maps.append(res["map_50"])

    return round(float(np.mean(maps)), 4)

