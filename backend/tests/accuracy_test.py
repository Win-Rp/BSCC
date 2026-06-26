from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.similarity import compare_documents, find_keyword_hits


def block(block_id: str, text: str, paragraph: int = 1, sentence: int = 1) -> dict:
    return {
        "block_id": block_id,
        "page": 1,
        "paragraph": paragraph,
        "sentence": sentence,
        "text": text,
        "char_count": len(text),
    }


def doc(blocks: list[dict]) -> dict:
    return {
        "text": "\n".join(item["text"] for item in blocks),
        "blocks": blocks,
        "metadata": {"author": "tester", "software": "DOCX"},
        "page_count": None,
        "word_count": sum(item["char_count"] for item in blocks),
        "sentence_count": len(blocks),
        "paragraph_count": len({item["paragraph"] for item in blocks}),
    }


def run() -> None:
    a_doc = doc(
        [
            block("p1-s1", "本项目建设智慧园区综合管理平台，采用统一数据底座。", 1, 1),
            block("p2-s1", "技术方案采用微服务架构，支持身份认证、权限管理和日志审计。", 2, 1),
            block("p3-s1", "售后服务需在接到问题后及时响应并形成处理记录。", 3, 1),
        ]
    )
    b_doc = doc(
        [
            block("p1-s1", "本项目建设智慧园区综合管理平台，采用统一数据底座。", 1, 1),
            block("p2-s1", "技术方案采用服务化架构，支持统一认证、权限控制和审计日志。", 2, 1),
            block("p3-s1", "服务团队将在收到故障反馈后快速响应，并保留处置记录。", 3, 1),
        ]
    )
    result = compare_documents(1, 2, a_doc, b_doc, ["微服务", "响应"], preview_limit=5)
    matches = result["matches"]
    match_types = {match["match_type"] for match in matches}

    assert result["summary"]["matched_sentence_count"] == 3, matches
    assert "exact" in match_types, matches
    assert "rewrite" in match_types, matches
    assert "semantic" in match_types, matches
    assert result["summary"]["total_similarity"] > 0.75, result["summary"]

    hits = find_keyword_hits(1, a_doc["blocks"], ["微服务", "响应"])
    assert len(hits) == 2, hits
    exact_sequence_doc = doc(
        [
            block("p1-s1", "本项目建设智慧园区综合管理平台，采用统一数据底座。", 1, 1),
            block("p1-s2", "技术方案采用微服务架构，支持身份认证、权限管理和日志审计。", 1, 2),
            block("p2-s1", "实施团队将提供培训、验收和运维支持。", 2, 1),
        ]
    )
    copied_doc = doc(
        [
            block("p1-s1", "本项目建设智慧园区综合管理平台，采用统一数据底座。", 1, 1),
            block("p1-s2", "技术方案采用微服务架构，支持身份认证、权限管理和日志审计。", 1, 2),
            block("p2-s1", "售后团队将提供培训、验收和运维支持。", 2, 1),
        ]
    )
    exact_result = compare_documents(3, 4, exact_sequence_doc, copied_doc, [], preview_limit=5)
    continuous_exact = [
        match for match in exact_result["matches"]
        if match["match_type"] == "exact" and match.get("reason") == "continuous_exact"
    ]

    assert continuous_exact, exact_result["matches"]
    assert continuous_exact[0]["a_char_count"] > len("本项目建设智慧园区综合管理平台，采用统一数据底座。")
    print(
        {
            "matches": len(matches),
            "types": sorted(match_types),
            "keyword_hits": len(hits),
            "continuous_exact": len(continuous_exact),
        }
    )


if __name__ == "__main__":
    run()
