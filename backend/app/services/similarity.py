import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


PUNCT_RE = re.compile(r"[\s，。、《》？?！!；;：:,.()\[\]【】“”\"'`~\-_/\\]+")
SYNONYM_GROUPS = [
    ("售后服务", "售后团队", "服务团队", "运维团队", "服务保障"),
    ("及时响应", "快速响应", "及时处理", "立即响应", "响应处理"),
    ("问题", "故障", "异常", "反馈"),
    ("处理记录", "处置记录", "服务记录", "响应记录"),
    ("项目实施", "实施过程", "实施周期", "项目周期"),
    ("准备", "前期准备", "启动准备"),
    ("部署", "系统部署", "上线部署"),
    ("联调", "联合调试", "系统联调"),
    ("验收", "最终验收", "交付验收"),
    ("微服务架构", "微服务", "服务化架构"),
    ("身份认证", "用户认证", "统一认证"),
    ("权限管理", "权限控制", "授权管理"),
    ("日志审计", "审计日志", "日志留痕"),
    ("统一数据底座", "数据底座", "统一数据基础"),
]
DOMAIN_TERMS = {
    "售后",
    "服务",
    "响应",
    "故障",
    "问题",
    "记录",
    "实施",
    "准备",
    "部署",
    "联调",
    "验收",
    "微服务",
    "认证",
    "权限",
    "日志",
    "审计",
    "数据",
    "平台",
    "运维",
}
MIN_CONTINUOUS_EXACT_CHARS = 24
MIN_CONTINUOUS_EXACT_BLOCKS = 2
MAX_CONTINUOUS_EXACT_BLOCKS = 6


def compare_documents(
    a_file_id: int,
    b_file_id: int,
    a_doc: dict[str, Any],
    b_doc: dict[str, Any],
    keywords: list[str],
    preview_limit: int,
) -> dict[str, Any]:
    a_blocks = a_doc["blocks"]
    b_blocks = b_doc["blocks"]
    matches = _match_sentences(a_blocks, b_blocks)
    a_total_chars = max(1, sum(len(_norm(block["text"])) for block in a_blocks))
    char_totals = {"exact": 0, "rewrite": 0, "semantic": 0}
    for match in matches:
        char_totals[match["match_type"]] += len(_norm(match["a_text"]))
    total_chars = sum(char_totals.values())
    keyword_hits = find_keyword_hits(a_file_id, a_blocks, keywords) + find_keyword_hits(b_file_id, b_blocks, keywords)
    format_results = compare_format(a_doc, b_doc)
    metadata_results = compare_metadata(a_doc.get("metadata", {}), b_doc.get("metadata", {}))
    return {
        "summary": {
            "total_similarity": round(total_chars / a_total_chars, 4),
            "exact_similarity": round(char_totals["exact"] / a_total_chars, 4),
            "rewrite_similarity": round(char_totals["rewrite"] / a_total_chars, 4),
            "semantic_similarity": round(char_totals["semantic"] / a_total_chars, 4),
            "sentence_similarity": round(len(matches) / max(1, len(a_blocks)), 4),
            "paragraph_similarity": round(
                len({m["a_position"]["paragraph"] for m in matches}) / max(1, a_doc.get("paragraph_count") or 1),
                4,
            ),
            "format_similarity": round(_average([item["similarity"] for item in format_results]), 4),
            "metadata_similarity": round(_metadata_score(metadata_results), 4),
            "keyword_hit_count": len(keyword_hits),
            "matched_sentence_count": len(matches),
            "matched_paragraph_count": len({m["a_position"]["paragraph"] for m in matches}),
        },
        "matches": matches,
        "preview_segments": matches[:preview_limit],
        "keyword_hits": keyword_hits,
        "format_results": format_results,
        "metadata_results": metadata_results,
    }


def write_result_files(result: dict[str, Any], preview_path: Path, detail_path: Path) -> None:
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    detail_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.write_text(
        json.dumps({"segments": result["preview_segments"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    detail_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def find_keyword_hits(file_id: int, blocks: list[dict[str, Any]], keywords: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for block in blocks:
        text = block["text"]
        for keyword in keywords:
            index = text.find(keyword)
            if index < 0:
                continue
            hits.append(
                {
                    "file_id": file_id,
                    "keyword": keyword,
                    "hit_text": text,
                    "position": {
                        "block_id": block["block_id"],
                        "page": block["page"],
                        "paragraph": block["paragraph"],
                        "sentence": block["sentence"],
                        "start": index,
                        "end": index + len(keyword),
                    },
                    "context_before": text[max(0, index - 20) : index],
                    "context_after": text[index + len(keyword) : index + len(keyword) + 20],
                }
            )
    return hits


def compare_format(a_doc: dict[str, Any], b_doc: dict[str, Any]) -> list[dict[str, Any]]:
    a_blocks = a_doc.get("blocks", [])
    b_blocks = b_doc.get("blocks", [])
    return [
        _format_item("段落数量", a_doc.get("paragraph_count"), b_doc.get("paragraph_count")),
        _format_item("句子数量", a_doc.get("sentence_count"), b_doc.get("sentence_count")),
        _format_item("页数", a_doc.get("page_count") or "无法判断", b_doc.get("page_count") or "无法判断"),
        _format_item("标题层级", _heading_count(a_blocks), _heading_count(b_blocks)),
        _format_item("目录结构", _toc_count(a_blocks), _toc_count(b_blocks)),
    ]


def compare_metadata(a_metadata: dict[str, Any], b_metadata: dict[str, Any]) -> list[dict[str, Any]]:
    fields = {
        "author": "作者",
        "created": "创建时间",
        "modified": "修改时间",
        "software": "软件",
        "template_source": "模板来源",
        "producer": "PDF 生成器",
    }
    results = []
    for key, label in fields.items():
        a_value = a_metadata.get(key)
        b_value = b_metadata.get(key)
        if not a_value or not b_value:
            similarity_type = "missing"
        elif str(a_value).strip() == str(b_value).strip():
            similarity_type = "same"
        elif str(a_value)[:10] == str(b_value)[:10]:
            similarity_type = "similar"
        else:
            similarity_type = "different"
        results.append(
            {
                "field_name": label,
                "a_value": a_value,
                "b_value": b_value,
                "similarity_type": similarity_type,
                "is_highlighted": similarity_type in {"same", "similar"},
            }
        )
    return results


def _match_sentences(a_blocks: list[dict[str, Any]], b_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exact_matches, used_a, used_b = _match_exact_sequences(a_blocks, b_blocks)
    matches: list[dict[str, Any]] = list(exact_matches)
    remaining_b = [
        (_sentence_features(block["text"]), block)
        for block in b_blocks
        if block["block_id"] not in used_b
    ]

    for a_block in a_blocks:
        if a_block["block_id"] in used_a:
            continue
        a_features = _sentence_features(a_block["text"])
        if len(a_features["norm"]) < 8:
            continue
        best_score = 0.0
        best_block = None
        best_reason = ""
        for b_features, b_block in remaining_b:
            if len(b_features["norm"]) < 8:
                continue
            score, reason = _hybrid_similarity(a_features, b_features)
            if score > best_score:
                best_score = score
                best_block = b_block
                best_reason = reason
        if best_block is None or best_score < 0.62:
            continue
        match_type = "exact" if best_score >= 0.995 and a_features["norm"] == _sentence_features(best_block["text"])["norm"] else "rewrite" if best_score >= 0.82 else "semantic"
        matches.append(
            {
                "match_type": match_type,
                "similarity": round(best_score, 4),
                "reason": best_reason,
                "a_text": a_block["text"],
                "b_text": best_block["text"],
                "a_position": _position(a_block),
                "b_position": _position(best_block),
                "a_char_count": len(a_features["norm"]),
            }
        )
    matches.sort(key=lambda item: item["similarity"], reverse=True)
    return matches


def _match_exact_sequences(
    a_blocks: list[dict[str, Any]],
    b_blocks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    matches: list[dict[str, Any]] = []
    used_a: set[str] = set()
    used_b: set[str] = set()
    b_candidates_by_norm: dict[str, list[dict[str, Any]]] = {}

    for candidate in _sequence_candidates(b_blocks):
        b_candidates_by_norm.setdefault(candidate["norm"], []).append(candidate)

    for candidate in _sequence_candidates(a_blocks):
        norm = candidate["norm"]
        if norm not in b_candidates_by_norm:
            continue
        if _candidate_is_used(candidate, used_a):
            continue
        for other in b_candidates_by_norm[norm]:
            if _candidate_is_used(other, used_b):
                continue
            matches.append(
                {
                    "match_type": "exact",
                    "similarity": 1.0,
                    "reason": "continuous_exact",
                    "a_text": candidate["text"],
                    "b_text": other["text"],
                    "a_position": _position(candidate["blocks"][0]),
                    "b_position": _position(other["blocks"][0]),
                    "a_char_count": len(norm),
                }
            )
            used_a.update(block["block_id"] for block in candidate["blocks"])
            used_b.update(block["block_id"] for block in other["blocks"])
            break

    return matches, used_a, used_b


def _sequence_candidates(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    total = len(blocks)

    for start in range(total):
        start_block = blocks[start]
        sequence: list[dict[str, Any]] = []

        for end in range(start, min(total, start + MAX_CONTINUOUS_EXACT_BLOCKS)):
            current = blocks[end]
            if current["paragraph"] != start_block["paragraph"]:
                break

            sequence.append(current)
            if len(sequence) < MIN_CONTINUOUS_EXACT_BLOCKS:
                continue

            text = "".join(block["text"] for block in sequence)
            norm = _norm(text)
            if len(norm) < MIN_CONTINUOUS_EXACT_CHARS:
                continue

            candidates.append(
                {
                    "blocks": list(sequence),
                    "text": text,
                    "norm": norm,
                    "block_count": len(sequence),
                }
            )

    candidates.sort(key=lambda item: (len(item["norm"]), item["block_count"]), reverse=True)
    return candidates


def _candidate_is_used(candidate: dict[str, Any], used_block_ids: set[str]) -> bool:
    return any(block["block_id"] in used_block_ids for block in candidate["blocks"])


def _position(block: dict[str, Any]) -> dict[str, Any]:
    return {
        "block_id": block["block_id"],
        "page": block["page"],
        "paragraph": block["paragraph"],
        "sentence": block["sentence"],
    }


def _norm(text: str) -> str:
    return PUNCT_RE.sub("", text).lower()


def _semantic_norm(text: str) -> str:
    normalized = _norm(text)
    for index, group in enumerate(SYNONYM_GROUPS):
        canonical = f"同义{index}"
        for phrase in group:
            normalized = normalized.replace(_norm(phrase), canonical)
    return normalized


def _sentence_features(text: str) -> dict[str, Any]:
    norm = _norm(text)
    semantic = _semantic_norm(text)
    return {
        "norm": norm,
        "semantic": semantic,
        "bigrams": _ngrams(norm, 2),
        "semantic_bigrams": _ngrams(semantic, 2),
        "terms": {term for term in DOMAIN_TERMS if term in text or _norm(term) in norm},
    }


def _hybrid_similarity(a_features: dict[str, Any], b_features: dict[str, Any]) -> tuple[float, str]:
    if a_features["norm"] == b_features["norm"]:
        return 1.0, "normalized_exact"
    sequence_score = SequenceMatcher(None, a_features["norm"], b_features["norm"]).ratio()
    semantic_sequence = SequenceMatcher(None, a_features["semantic"], b_features["semantic"]).ratio()
    gram_score = _dice(a_features["bigrams"], b_features["bigrams"])
    semantic_gram_score = _dice(a_features["semantic_bigrams"], b_features["semantic_bigrams"])
    term_score = _jaccard(a_features["terms"], b_features["terms"])
    score = max(
        sequence_score,
        gram_score,
        semantic_sequence * 0.96,
        semantic_gram_score * 0.96,
        (sequence_score * 0.45 + gram_score * 0.25 + term_score * 0.30),
        (semantic_sequence * 0.48 + semantic_gram_score * 0.32 + term_score * 0.20),
    )
    reason_scores = {
        "sequence": sequence_score,
        "ngram": gram_score,
        "semantic_sequence": semantic_sequence,
        "semantic_ngram": semantic_gram_score,
        "term_overlap": term_score,
    }
    reason = max(reason_scores, key=reason_scores.get)
    return min(1.0, score), reason


def _ngrams(text: str, size: int) -> set[str]:
    if len(text) <= size:
        return {text} if text else set()
    return {text[index : index + size] for index in range(len(text) - size + 1)}


def _dice(a_values: set[str], b_values: set[str]) -> float:
    if not a_values or not b_values:
        return 0.0
    return (2 * len(a_values & b_values)) / (len(a_values) + len(b_values))


def _jaccard(a_values: set[str], b_values: set[str]) -> float:
    if not a_values or not b_values:
        return 0.0
    return len(a_values & b_values) / len(a_values | b_values)


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _metadata_score(results: list[dict[str, Any]]) -> float:
    weights = {"same": 1.0, "similar": 0.7, "different": 0.0, "missing": 0.0}
    return _average([weights[item["similarity_type"]] for item in results])


def _format_item(name: str, a_value: Any, b_value: Any) -> dict[str, Any]:
    similarity = _numeric_similarity(a_value, b_value)
    return {
        "item_name": name,
        "a_value": str(a_value),
        "b_value": str(b_value),
        "similarity": similarity,
        "description": "相似" if similarity >= 0.8 else "差异较大" if similarity < 0.5 else "部分相似",
    }


def _numeric_similarity(a_value: Any, b_value: Any) -> float:
    if not isinstance(a_value, int) or not isinstance(b_value, int):
        return 0.0 if a_value == "无法判断" or b_value == "无法判断" else float(a_value == b_value)
    if max(a_value, b_value) == 0:
        return 1.0
    return round(min(a_value, b_value) / max(a_value, b_value), 4)


def _heading_count(blocks: list[dict[str, Any]]) -> int:
    return sum(1 for block in blocks if re.match(r"^第?[一二三四五六七八九十\d]+[章节、.．]", block["text"]))


def _toc_count(blocks: list[dict[str, Any]]) -> int:
    return sum(1 for block in blocks if "目录" in block["text"] or re.search(r"\.{3,}\s*\d+$", block["text"]))
