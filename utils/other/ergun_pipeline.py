# -*- coding: utf-8 -*-
"""
Ergun River Narrative - SFL Transitivity Pipeline
- Extract narrative text from PDF (skip author bio via anchors)
- Chunk by paragraphs (fallback to sentences), ~3000-5000 Chinese chars
- Call OpenAI-compatible Chat Completions API (multiple independent tasks) with a stable coding manual
- Validate/repair JSON, retry failures, resume from cache
- Aggregate records, compute required stats, ask AI for final consistency + narrative synthesis
- Export final Excel to local disk

Dependencies:
  pip install pymupdf pandas openpyxl
"""

import os
import re
import json
import sys
import time
import math
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

import fitz  # PyMuPDF
import pandas as pd
import requests
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

# ====== OpenAI SDK (OpenAI-compatible base_url) ======
from openai import OpenAI

# -----------------------------
# CONFIG
# -----------------------------
PDF_PATH = input("请输入PDF文件路径：").strip()  # 输入PDF路径
if not os.path.isfile(PDF_PATH):
    raise FileNotFoundError(f"PDF文件未找到：{PDF_PATH}")
OUT_DIR = os.path.dirname(PDF_PATH)   # 输出目录

BASE_URL = "https://xiaoai.plus/v1/"
# BASE_URL = "http://127.0.0.1:23333/v1/"
# BASE_URL = "https://api.mttieeo.com/v1/"
API_KEY = input("请输入OpenAI API Key：").strip()  # 输入API Key
# API_KEY = "cs-sk-f0fd0228-4540-470f-8237-789684ac5f7e"
# MODEL = input("输入模型ID（如 gpt-4-turbo-0613）：").strip() or "gpt-4o"
# MODEL = "[满血]gemini-3.0-pro-preview"
MODEL = "gemini-2.5-pro-thinking"

# Narrative anchors
START_SENT = "我是雨和雪的老熟人了，我有九十岁了。"
END_SENT = "我落泪了，因为我已分不清天上人间了。"

# Chunk sizing (chars, after whitespace normalization; Chinese chars ~ tokens close to 1:1)
CHUNK_MIN_CHARS = 500
CHUNK_TARGET_CHARS = 1000
CHUNK_MAX_CHARS = 1500

# Retry policy
MAX_RETRIES = 4
RETRY_BACKOFF_SEC = 2.0

# Cache policy (resume)
USE_CACHE = True

# Excel sheet limits
EXCEL_MAX_ROWS = 1_000_000  # xlsx limit ~1,048,576

# -----------------------------
# CODING MANUAL / PROMPT
# -----------------------------
CODING_MANUAL = r"""
你是一个“系统功能语言学（SFL）及物性系统”标注员，需要对中文小说叙事文本进行可复核的结构化标注。
你必须在多次独立任务中保持一致口径：所有规则以本手册为准。

【统计范围】
- 输入文本已来自小说正文（不含作者简介）。无需再处理作者简介。

【计数单位】
- 每一个“过程实例”（process instance）计1条记录：以“小句（clause）”为主，包含嵌入小句/嵌入短语中的过程（embedded process）。
- 小句切分参考：逗号/分号/冒号等；但如果切出的是“纯环境片段”（只有时间/地点/方式等，没有过程核），不要单独成条，应并入后面最近的带过程核小句，作为其环境成分（circumstance）。

【过程类型（固定6类）】
- Material（物质过程）：做/发生/对具体客体的处置（例：披/拴/拉/宰杀/建造/击打/画等）
- Behavioural（行为过程）：身体化行为、介于物质与心理之间的感知/生理表现（本项目中“看/听（主动去看/去听）”通常归此类）
  - Subtype: physiological（生理型） / pathological（病理型）
- Mental（心理过程）：感知/认知/情感/意愿（本项目中“看见/见到/发现（感知结果）”通常归此类）
- Verbal（言语过程）：说/问/告诉/叫（命名可用 verbal:appellative 子类）
- Relational（关系过程）：是/像/成为/属性描写/占有
  - possessive relational：英语 he has X；中文多为“X有Y（描述X具备Y）”
  - 注意“有”的歧义：如为“（地点）有X/出现X”用于引入存在物，则是 Existential
- Existential（存在过程）：英语 there is X；中文多为“（地点）有/出现/存在X”
  - 注意：存在物（Existent）不计入主动参与者统计，但该过程仍计入“过程类型分布”

【关键判别（已确认）】
- “看老了我/把它们给看老了”：在本项目中按 Behavioural:physiological（动词核=看；老=结果补语）
- “（太阳）身上一片云彩都不披”：按 Material（对具体客体云彩的处置）
- 被字句：若主语是受事（X被…），则 ActiveCounted=0
- 存在过程：ActiveCounted=0（因为存在物不计主动参与者）

【主动参与者分类（ParticipantCategory）】
- Human：人类/人称代词/人物名
- HumanBodyPart：明确为“人类身体部位”作主语（如“我的手发抖”）
- Artifact：人造物（希楞柱、镜子、神鼓等）
- Nature：除 Human/HumanBodyPart/Artifact 之外一律归 Nature
  - NatureSubcategory：Animal / Plant / Environment / NatureOther

【动物部位归并（CanonicalFloraFauna）】
- 若主动参与者是动物部位/动物相关物（如鹿角/鹿皮/鹿铃），应归并到对应动物（如“驯鹿”）。
- 若主动参与者是植物或其部位，归并到植物名。

【参与者角色（Role）】
- Material -> Actor
- Behavioural -> Behaver
- Mental -> Senser
- Verbal -> Sayer
- Relational -> Carrier
- Existential -> Existent（但 ActiveCounted=0）

【环境成分 Circumstances 分类（type/subtype）】
- Extent: duration/distance/frequency
- Location: time/place
- Manner: means/quality/comparison/degree
- Cause: reason/purpose/behalf
- Contingency: condition/concession
- Accompaniment: comitative/additive
- Role: guise/product
- Matter
- Angle: source/viewpoint

【输出要求：只输出严格有效JSON，不要夹带任何解释文字】
- 你会收到带句子编号标记的文本：例如 “〔S000123〕……。”。每条记录必须包含 sent_id（整数）。
- clause_id 规则：对每个句子按出现顺序切分小句，编号为 “S000123.C1 / S000123.C2 …”
- 结果补语（如“老了/出/落/起/瘦了”）写入 notes 或单列 resultative 字段（可选）；不要因此拆成两个过程，除非它确实成独立小句。

【JSON Schema】
{
  "chunk_id": int,
  "records": [
    {
      "sent_id": int,
      "clause_id": str,
      "clause_text": str,
      "process_type": "Material|Behavioural|Mental|Verbal|Relational|Existential",
      "process_subtype": str|null,
      "process_lexeme": str,
      "active_participant": str,
      "participant_category": "Human|HumanBodyPart|Artifact|Nature",
      "nature_subcategory": "Animal|Plant|Environment|NatureOther"|null,
      "canonical_flora_fauna": str|null,
      "role": "Actor|Behaver|Senser|Sayer|Carrier|Existent",
      "circumstances": [
        {"type": str, "subtype": str|null, "text": str}
      ],
      "embedded_processes": [
        {"text": str, "process_type": str, "process_lexeme": str}
      ],
      "active_counted": 0|1,
      "notes": str|null
    }
  ],
  "unparsed": [
    {"sent_id": int, "text": str, "reason": str}
  ]
}
"""


# -----------------------------
# Utilities
# -----------------------------
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def normalize_text_keep_para(text: str) -> str:
    """
    Keep paragraph boundaries, but normalize intra-line wraps and whitespace.
    Strategy:
      - Convert fullwidth spaces to normal removal
      - Keep blank lines as paragraph breaks
      - Remove spaces/tabs; merge wrapped lines within a paragraph
    """
    text = text.replace("\u3000", "")
    # unify newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # remove trailing spaces per line
    lines = [re.sub(r"[ \t]+", "", ln) for ln in text.split("\n")]
    # rebuild paragraphs: blank line separates paragraphs
    paras = []
    buf = []
    for ln in lines:
        if ln == "":
            if buf:
                paras.append("".join(buf))
                buf = []
        else:
            buf.append(ln)
    if buf:
        paras.append("".join(buf))
    # remove empty paras
    paras = [p for p in paras if p.strip()]
    return "\n\n".join(paras)


def extract_pdf_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    pages = [doc.load_page(i).get_text("text") for i in range(doc.page_count)]
    return "\n".join(pages)


def slice_narrative_scope(full_text: str, start_sent: str, end_sent: str) -> str:
    """
    Use anchors to slice narrative正文，避开作者简介。
    End anchor may have whitespace breaks; we use regex with loose spaces removal.
    """
    # For robust matching, remove spaces/newlines but keep punctuation for anchor-finding
    compact = re.sub(r"[ \t\r\n\u3000]+", "", full_text)

    start_idx = compact.find(re.sub(r"[ \t\r\n\u3000]+", "", start_sent))
    if start_idx < 0:
        raise ValueError("未找到正文起点锚点（START_SENT）。请核对锚点句是否与PDF文本一致。")

    # For end, build tolerant regex on compact text
    end_compact = re.sub(r"[ \t\r\n\u3000]+", "", end_sent)
    end_idx = compact.find(end_compact)
    if end_idx < 0:
        # fallback: regex around key phrase “我落泪了...天上人间了。”
        m = re.search(r"我落泪了，?因为我已.*?分不清.*?天上人间了。", compact)
        if not m:
            raise ValueError("未找到正文终点锚点（END_SENT）。请核对终止句。")
        end_idx = m.end()
    else:
        end_idx += len(end_compact)

    scope_compact = compact[start_idx:end_idx]

    # Now we need a paragraph-preserving scope. Best effort:
    # We locate start/end in the original text by searching start/end in compact, then map back is hard.
    # Practical solution: extract text again paragraph-preserving, then locate using compact find within compact version and just use compact scope.
    # We will re-inject paragraph boundaries later by sentence markers, so compact scope is acceptable for analysis.
    return scope_compact


def sentence_split(text: str) -> List[str]:
    """
    Split by sentence-ending punctuation. Keep punctuation at end.
    """
    sents = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in "。！？；":
            t = buf.strip()
            if t:
                sents.append(t)
            buf = ""
    if buf.strip():
        sents.append(buf.strip())
    return sents


def paragraph_split_from_sentences(sentences: List[str]) -> List[str]:
    """
    Recreate paragraphs roughly: since compact text loses original paras,
    we group sentences into paragraphs by heuristics:
      - If a sentence ends with '。' keep grouping; start new paragraph at dialogue markers or scene breaks.
    For chunking, paragraph boundaries are "soft"; we can just group every N sentences.
    """
    # Heuristic: new paragraph if sentence contains "——" or starts with "“" and previous ended with "。"
    paras = []
    buf = []
    for s in sentences:
        if buf and (("——" in s) or s.startswith("“") or s.startswith("『") or s.startswith("《")):
            paras.append("".join(buf))
            buf = [s]
        else:
            buf.append(s)
    if buf:
        paras.append("".join(buf))
    return [p for p in paras if p.strip()]


@dataclass
class Chunk:
    chunk_id: int
    start_sent_id: int
    end_sent_id: int
    char_count: int
    text_with_markers: str
    sha1: str


def build_chunks(sentences: List[str]) -> List[Chunk]:
    """
    Chunk by paragraphs (heuristic), fallback to sentence boundaries.
    Add sentence markers to stabilize AI output: 〔S000123〕
    """
    paras = paragraph_split_from_sentences(sentences)

    # Build a mapping: paragraph -> sentence id range by reconstructing from concatenation
    # We'll just chunk by sentences directly but try to cut at para boundaries by using paras list
    # and tracking sentence pointers.
    chunks: List[Chunk] = []
    sent_idx = 1
    chunk_id = 1
    # Build para sentence lists: distribute sentences into paras in same order
    # Since paras were built from sentences sequentially, we can reconstruct by re-splitting paras (not needed).
    # We'll instead chunk via sentences with target sizes and allow "soft" paragraph breaks at para ends.
    # Precompute para boundaries in sentence indices:
    para_boundaries = []
    acc = 0
    # We reconstruct by iterating paras and counting how many sentences were in each by greedy matching
    # because paras were built from sentences with join, we can store counts during paragraph_split, but we didn't.
    # We'll re-do paragraph_split with counts:
    para_sent_counts = []
    buf = []
    for s in sentences:
        if buf and (("——" in s) or s.startswith("“") or s.startswith("『") or s.startswith("《")):
            para_sent_counts.append(len(buf))
            buf = [s]
        else:
            buf.append(s)
    if buf:
        para_sent_counts.append(len(buf))

    # Build para end indices
    end = 0
    for c in para_sent_counts:
        end += c
        para_boundaries.append(end)  # sentence index (1-based) where a paragraph ends

    def is_para_end(sid: int) -> bool:
        return sid in para_boundaries

    cur_sents = []
    cur_chars = 0
    chunk_start_sid = 1

    def flush_chunk(end_sid: int):
        nonlocal chunk_id, chunk_start_sid, cur_sents, cur_chars
        if not cur_sents:
            return
        # build text with sentence markers
        lines = []
        sid = chunk_start_sid
        for s in cur_sents:
            lines.append(f"〔S{sid:06d}〕{s}")
            sid += 1
        text_with_markers = "\n".join(lines)
        ch = Chunk(
            chunk_id=chunk_id,
            start_sent_id=chunk_start_sid,
            end_sent_id=end_sid,
            char_count=cur_chars,
            text_with_markers=text_with_markers,
            sha1=sha1_text(text_with_markers),
        )
        chunks.append(ch)
        chunk_id += 1
        chunk_start_sid = end_sid + 1
        cur_sents = []
        cur_chars = 0

    for sid, s in enumerate(sentences, start=1):
        s_len = len(s)
        # if adding would exceed max, flush before adding (ensure non-empty)
        if cur_sents and (cur_chars + s_len > CHUNK_MAX_CHARS):
            flush_chunk(sid - 1)

        cur_sents.append(s)
        cur_chars += s_len

        # flush when reaching target AND at paragraph end (preferred)
        if cur_chars >= CHUNK_TARGET_CHARS and is_para_end(sid):
            flush_chunk(sid)
        # or if very large, flush anyway at sentence end
        elif cur_chars >= CHUNK_MAX_CHARS:
            flush_chunk(sid)

    # remainder
    if cur_sents:
        flush_chunk(len(sentences))

    return chunks


# -----------------------------
# AI Call + JSON Validation
# -----------------------------
def make_client() -> OpenAI:
    # 显著增加 timeout，标注任务建议至少 120s，如果是慢速模型建议 300s
    # 同时增加 httpx 限制，防止连接过快断开
    import httpx
    http_client = httpx.Client(
        limits=httpx.Limits(max_connections=5, max_keepalive_connections=2),
        timeout=httpx.Timeout(300.0, read=240.0, connect=20.0)
    )
    client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        http_client=http_client
    )
    return client


def extract_visible_text_from_choice_message(msg) -> str:
    """
    Compatible with normal models (message.content) and reasoning models
    (message.reasoning_content). Return the best-effort visible text.
    """
    content = getattr(msg, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()

    # some reasoning models put output here
    rc = getattr(msg, "reasoning_content", None)
    if isinstance(rc, str) and rc.strip():
        return rc.strip()

    # fallback: stringify
    try:
        s = str(msg)
        return s.strip()
    except Exception:
        return ""


def check_ai_connectivity_or_exit():
    """
    使用原生 requests 检查连接
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "say ok"}],
        "max_tokens": 5
    }
    try:
        # 使用较短的 timeout 进行测试
        response = requests.post(f"{BASE_URL.rstrip('/')}/chat/completions",
                                 headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        print("  [Connect] API 连接成功")
    except Exception as e:
        print(f"\n[ERROR] 接口访问失败: {e}")
        if response := getattr(e, 'response', None):
            print(f"状态码: {response.status_code}, 返回内容: {response.text}")
        raise SystemExit(1)


ALLOWED_PROCESS_TYPES = {"Material", "Behavioural", "Mental", "Verbal", "Relational", "Existential"}
ALLOWED_PARTICIPANT_CATS = {"Human", "HumanBodyPart", "Artifact", "Nature"}
ALLOWED_ROLES = {"Actor", "Behaver", "Senser", "Sayer", "Carrier", "Existent"}


def basic_validate_payload(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errs = []
    if not isinstance(payload, dict):
        return False, ["payload_not_dict"]
    if "chunk_id" not in payload or not isinstance(payload["chunk_id"], int):
        errs.append("missing_or_bad_chunk_id")
    if "records" not in payload or not isinstance(payload["records"], list):
        errs.append("missing_or_bad_records")
    if "unparsed" not in payload or not isinstance(payload["unparsed"], list):
        errs.append("missing_or_bad_unparsed")

    # validate records fields lightly
    for i, r in enumerate(payload.get("records", [])):
        if not isinstance(r, dict):
            errs.append(f"record_{i}_not_dict")
            continue
        for k in ["sent_id", "clause_id", "clause_text", "process_type", "process_lexeme", "active_participant",
                  "participant_category", "role", "circumstances", "embedded_processes", "active_counted"]:
            if k not in r:
                errs.append(f"record_{i}_missing_{k}")
        pt = r.get("process_type")
        if pt and pt not in ALLOWED_PROCESS_TYPES:
            errs.append(f"record_{i}_bad_process_type:{pt}")
        pc = r.get("participant_category")
        if pc and pc not in ALLOWED_PARTICIPANT_CATS:
            errs.append(f"record_{i}_bad_participant_category:{pc}")
        role = r.get("role")
        if role and role not in ALLOWED_ROLES:
            errs.append(f"record_{i}_bad_role:{role}")
        ac = r.get("active_counted")
        if ac not in (0, 1):
            errs.append(f"record_{i}_bad_active_counted:{ac}")

        # circumstances & embedded_processes must be list
        if "circumstances" in r and not isinstance(r["circumstances"], list):
            errs.append(f"record_{i}_circumstances_not_list")
        if "embedded_processes" in r and not isinstance(r["embedded_processes"], list):
            errs.append(f"record_{i}_embedded_not_list")
    return (len(errs) == 0), errs


def is_cloudflare_524_or_timeout(err: Exception) -> bool:
    """
    Best-effort detection for Cloudflare 524 / timeouts from OpenAI-compatible SDKs.
    """
    s = str(err).lower()
    status = getattr(err, "status_code", None)
    if status == 524:
        return True
    if "error code 524" in s or "cloudflare" in s and "524" in s:
        return True
    if "timeout" in s or "timed out" in s or "readtimeout" in s:
        return True
    return False


def split_marked_text_by_lines(marked_text: str, sub_max_chars: int = 1800) -> List[str]:
    """
    marked_text is multiple lines like: 〔S000123〕....
    Split into smaller parts without breaking a line.
    """
    lines = [ln for ln in marked_text.split("\n") if ln.strip()]
    parts = []
    buf = []
    cur = 0
    for ln in lines:
        ln_len = len(ln)
        if buf and (cur + ln_len > sub_max_chars):
            parts.append("\n".join(buf))
            buf = [ln]
            cur = ln_len
        else:
            buf.append(ln)
            cur += ln_len
    if buf:
        parts.append("\n".join(buf))
    return parts


def call_ai_for_chunk(chunk: Chunk, cache_dir: str) -> Dict[str, Any]:
    """
    改进版：
    1. 修复 list index out of range (增加流式解析的健壮性)
    2. 增加控制台实时进度反馈 (打印 . )
    3. 保持 requests 流式调用以规避 524 超时
    """
    ensure_dir(cache_dir)
    cache_path = os.path.join(cache_dir, f"chunk_{chunk.chunk_id:03d}_{chunk.sha1}.json")

    # 缓存命中检查
    if USE_CACHE and os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            print(f"  [chunk {chunk.chunk_id}] 读取缓存: {os.path.basename(cache_path)}")
            return json.load(f)

    def _one_call(marked_text: str, current_chunk_id: int, sub_idx: int = 0) -> Dict[str, Any]:
        # 模拟浏览器 Header
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/event-stream",
        }

        system_prompt = "You are a rigorous SFL transitivity annotator. Follow the coding manual exactly. Output ONLY valid JSON."
        user_content = (
            f"{CODING_MANUAL}\n\n"
            f"【Task Info: chunk_id={current_chunk_id}】\n"
            f"Please annotate the following text:\n{marked_text}\n\n"
            f"Output ONLY JSON."
        )

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0,
            "stream": True,  # 必须开启流式
            "response_format": {"type": "json_object"}
        }

        last_err = None

        # 打印开始提示（不换行）
        sub_mark = f" (分片-{sub_idx})" if sub_idx > 0 else ""
        print(f"    处理 chunk {current_chunk_id}{sub_mark} ", end="", flush=True)

        for attempt in range(1, MAX_RETRIES + 1):
            full_content = []
            try:
                if attempt > 1:
                    print(f"\n    重试 {attempt}/{MAX_RETRIES}... ", end="", flush=True)

                response = requests.post(
                    f"{BASE_URL.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=(15, 600),  # (连接超时, 读取超时)
                    stream=True
                )

                if response.status_code != 200:
                    try:
                        err_msg = response.text[:100]
                    except:
                        err_msg = "Unknown"
                    raise RuntimeError(f"HTTP {response.status_code}: {err_msg}")

                # --- 核心修复：流式解析与进度条 ---
                char_counter = 0
                for line in response.iter_lines():
                    if not line:
                        continue

                    line_text = line.decode("utf-8")
                    if line_text.startswith("data: "):
                        data_str = line_text[6:]
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            data_json = json.loads(data_str)

                            # 1. 安全检查：防止 list index out of range
                            if not data_json.get("choices"):
                                continue

                            choice = data_json["choices"][0]
                            delta = choice.get("delta", {})

                            # 2. 获取内容
                            content_piece = delta.get("content", "")

                            if content_piece:
                                full_content.append(content_piece)
                                # 3. 交互改进：打印进度点
                                char_counter += len(content_piece)
                                if char_counter > 20:  # 每接收约20个字符打印一个点
                                    sys.stdout.write(".")
                                    sys.stdout.flush()
                                    char_counter = 0

                        except (json.JSONDecodeError, IndexError, AttributeError):
                            # 忽略单行解析错误，保证整体不崩溃
                            continue

                print(" 完成")  # 进度条结束换行

                raw_content = "".join(full_content).strip()
                if not raw_content:
                    raise RuntimeError("流式响应内容为空")

                # JSON 清洗
                clean_content = re.sub(r"^```json\s*", "", raw_content)
                clean_content = re.sub(r"\s*```$", "", clean_content)
                # 掐头去尾修复（防止首尾字符丢失）
                s = clean_content.find('{')
                e = clean_content.rfind('}')
                if s != -1 and e != -1:
                    clean_content = clean_content[s: e + 1]

                # 解析与验证
                try:
                    parsed = json.loads(clean_content)
                except json.JSONDecodeError as je:
                    raise ValueError(f"JSON解析失败: {str(je)[:50]}")

                ok, errs = basic_validate_payload(parsed)
                if not ok:
                    raise ValueError(f"Schema校验失败: {errs[:3]}")

                return parsed

            except Exception as e:
                last_err = e
                print(f" [错误: {str(e)[:50]}]", end="", flush=True)
                time.sleep(RETRY_BACKOFF_SEC * attempt)

        print("")  # 彻底失败后换行
        raise RuntimeError(f"重试耗尽，最后错误: {last_err}")

    # 主逻辑：先尝试整体，失败则拆分
    try:
        result = _one_call(chunk.text_with_markers, chunk.chunk_id)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return result

    except Exception as e:
        print(f"\n    [chunk {chunk.chunk_id}] 整体失败，切换为子分片模式...")
        # 失败后切分重试（使用更小的粒度）
        sub_texts = split_marked_text_by_lines(chunk.text_with_markers, sub_max_chars=600)
        all_records = []
        all_unparsed = []

        for i, sub_text in enumerate(sub_texts, start=1):
            try:
                sub_res = _one_call(sub_text, chunk.chunk_id, sub_idx=i)
                all_records.extend(sub_res.get("records", []))
                all_unparsed.extend(sub_res.get("unparsed", []))
            except Exception as sub_e:
                print(f"\n    [分片 {i} 失败] {sub_e}")
                # 记录失败但不中断整个流程
                all_unparsed.append({"sent_id": -1, "text": "SUB_CHUNK_FAILED", "reason": str(sub_e)})

        merged = {
            "chunk_id": chunk.chunk_id,
            "records": all_records,
            "unparsed": all_unparsed
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        return merged



def repair_json_via_ai(client: OpenAI, bad_text: str, errs: List[str]) -> Dict[str, Any]:
    """
    Ask AI to output valid JSON only, repairing prior output.
    """
    system_msg = "You are a strict JSON repair tool. Output ONLY valid JSON."
    user_msg = (
        "The previous output is not valid per schema. "
        f"Errors: {errs[:20]}\n"
        "Rewrite it into a STRICTLY valid JSON matching the schema. "
        "Do not add extra commentary.\n\n"
        f"Previous output:\n{bad_text}"
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
    )
    content = resp.choices[0].message.content.strip()
    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    return json.loads(content)


# -----------------------------
# Aggregation & Stats
# -----------------------------
def flatten_records(all_payloads: List[Dict[str, Any]], chunk_map: Dict[int, Chunk]) -> Tuple[
    pd.DataFrame, pd.DataFrame]:
    """
    Return:
      - records_df: parsed records
      - unparsed_df: unparsed items (not counted)
    """
    recs = []
    unparsed = []
    for payload in all_payloads:
        cid = payload["chunk_id"]
        ch = chunk_map.get(cid)
        for r in payload.get("records", []):
            rec = dict(r)
            rec["chunk_id"] = cid
            rec["chunk_start_sent_id"] = ch.start_sent_id if ch else None
            rec["chunk_end_sent_id"] = ch.end_sent_id if ch else None
            recs.append(rec)
        for u in payload.get("unparsed", []):
            item = dict(u)
            item["chunk_id"] = cid
            unparsed.append(item)
    records_df = pd.DataFrame(recs)
    unparsed_df = pd.DataFrame(unparsed)
    return records_df, unparsed_df


def safe_pct(n: int, d: int) -> float:
    return (n / d) if d else 0.0


def compute_required_tables(records_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Compute the required summary tables based ONLY on parsed records.
    unparsed_unknown is excluded by design (not in records_df).

    Added tables:
      - FloraFauna_ByRole: canonical_flora_fauna × role (counts + row-wise pct)
      - TopN_Animals_ByRole: (Animal only) top-N canonical_flora_fauna × role (counts + row-wise pct)
    """
    # ---- guard ----
    if records_df.empty:
        raise ValueError("records_df is empty; no parsed records to summarize.")

    # Ensure columns exist
    for col in [
        "process_type", "participant_category", "nature_subcategory",
        "canonical_flora_fauna", "role", "active_counted"
    ]:
        if col not in records_df.columns:
            records_df[col] = None

    # ---- 1) Process type distribution (include Existential) ----
    proc = (
        records_df.groupby("process_type")
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
    )
    proc["pct"] = proc["n"] / proc["n"].sum()

    # ---- ActiveCounted filter ----
    active_df = records_df[records_df["active_counted"] == 1].copy()
    n_active = len(active_df)

    # ---- 2) Human/HumanBodyPart active ----
    human_df = active_df[active_df["participant_category"].isin(["Human", "HumanBodyPart"])]
    human_sum = human_df.groupby("participant_category").size().reset_index(name="n")
    human_sum["pct_of_active"] = human_sum["n"] / n_active if n_active else 0.0

    # ---- 3) Nature vs Human+BodyPart vs Artifact active ----
    nature_n = len(active_df[active_df["participant_category"] == "Nature"])
    artifact_n = len(active_df[active_df["participant_category"] == "Artifact"])
    human_n = len(human_df)
    nature_sum = pd.DataFrame(
        {"Category": ["Nature", "Human+BodyPart", "Artifact"], "n": [nature_n, human_n, artifact_n]}
    )
    nature_sum["pct_of_active"] = nature_sum["n"] / n_active if n_active else 0.0

    # ---- 4) Nature active role distribution ----
    nature_active = active_df[active_df["participant_category"] == "Nature"]
    role_sum = (
        nature_active.groupby("role")
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
    )
    role_sum["pct_of_nature_active"] = role_sum["n"] / len(nature_active) if len(nature_active) else 0.0

    # ---- 5) Nature active process type distribution ----
    nature_proc = (
        nature_active.groupby("process_type")
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
    )
    nature_proc["pct_of_nature_active"] = nature_proc["n"] / len(nature_active) if len(nature_active) else 0.0

    # ---- 6) Top10 flora/fauna active (canonical_flora_fauna among Nature active) ----
    ff = nature_active[nature_active["canonical_flora_fauna"].notna()].copy()
    top10 = (
        ff.groupby("canonical_flora_fauna")
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
        .head(10)
    )
    denom_ff = len(ff)
    top10["pct_of_flora_fauna_active"] = top10["n"] / denom_ff if denom_ff else 0.0

    # ---- 7) Role breakdown for each top flora/fauna (long form) ----
    if not top10.empty:
        top_names = set(top10["canonical_flora_fauna"].tolist())
        top_ff = ff[ff["canonical_flora_fauna"].isin(top_names)]
        top_role = (
            top_ff.groupby(["canonical_flora_fauna", "role"])
            .size()
            .reset_index(name="n")
            .sort_values(["canonical_flora_fauna", "n"], ascending=[True, False])
        )
    else:
        top_role = pd.DataFrame(columns=["canonical_flora_fauna", "role", "n"])

    # =========================
    # NEW TABLE A: FloraFauna_ByRole (canonical_flora_fauna × role)
    # =========================
    # Use all flora/fauna active (ff), pivot to wide, add row totals & row-wise pct
    if not ff.empty:
        flora_role_counts = (
            ff.pivot_table(
                index="canonical_flora_fauna",
                columns="role",
                values="sent_id",   # any column, we just count rows
                aggfunc="count",
                fill_value=0,
            )
            .reset_index()
        )
        # ensure consistent role columns order
        role_cols = [c for c in ["Actor", "Behaver", "Senser", "Sayer", "Carrier"] if c in flora_role_counts.columns]
        # add missing role cols as 0
        for rc in ["Actor", "Behaver", "Senser", "Sayer", "Carrier"]:
            if rc not in flora_role_counts.columns:
                flora_role_counts[rc] = 0
        role_cols = ["Actor", "Behaver", "Senser", "Sayer", "Carrier"]

        flora_role_counts["Total"] = flora_role_counts[role_cols].sum(axis=1)

        # row-wise pct (per species)
        flora_role_pct = flora_role_counts.copy()
        for rc in role_cols:
            flora_role_pct[rc] = flora_role_pct.apply(
                lambda r: (r[rc] / r["Total"]) if r["Total"] else 0.0, axis=1
            )
        flora_role_pct = flora_role_pct.rename(columns={rc: f"{rc}_pct" for rc in role_cols})

        # merge counts + pct
        FloraFauna_ByRole = flora_role_counts.merge(
            flora_role_pct[["canonical_flora_fauna"] + [f"{rc}_pct" for rc in role_cols]],
            on="canonical_flora_fauna",
            how="left",
        ).sort_values("Total", ascending=False)
    else:
        FloraFauna_ByRole = pd.DataFrame(
            columns=[
                "canonical_flora_fauna", "Actor", "Behaver", "Senser", "Sayer", "Carrier",
                "Total", "Actor_pct", "Behaver_pct", "Senser_pct", "Sayer_pct", "Carrier_pct"
            ]
        )

    # =========================
    # NEW TABLE B: TopN_Animals_ByRole (Animal only)
    # =========================
    TOPN_ANIMALS = 10  # 你可在这里改成 15/20
    animal_ff = ff[ff["nature_subcategory"] == "Animal"].copy()

    if not animal_ff.empty:
        animal_totals = (
            animal_ff.groupby("canonical_flora_fauna")
            .size()
            .reset_index(name="Total")
            .sort_values("Total", ascending=False)
        )
        top_animals = animal_totals.head(TOPN_ANIMALS)["canonical_flora_fauna"].tolist()

        animal_top = animal_ff[animal_ff["canonical_flora_fauna"].isin(top_animals)]
        animal_role_counts = (
            animal_top.pivot_table(
                index="canonical_flora_fauna",
                columns="role",
                values="sent_id",
                aggfunc="count",
                fill_value=0,
            )
            .reset_index()
        )
        # ensure consistent role columns order
        for rc in ["Actor", "Behaver", "Senser", "Sayer", "Carrier"]:
            if rc not in animal_role_counts.columns:
                animal_role_counts[rc] = 0
        role_cols = ["Actor", "Behaver", "Senser", "Sayer", "Carrier"]
        animal_role_counts["Total"] = animal_role_counts[role_cols].sum(axis=1)

        # row-wise pct
        animal_role_pct = animal_role_counts.copy()
        for rc in role_cols:
            animal_role_pct[rc] = animal_role_pct.apply(
                lambda r: (r[rc] / r["Total"]) if r["Total"] else 0.0, axis=1
            )
        animal_role_pct = animal_role_pct.rename(columns={rc: f"{rc}_pct" for rc in role_cols})

        TopN_Animals_ByRole = animal_role_counts.merge(
            animal_role_pct[["canonical_flora_fauna"] + [f"{rc}_pct" for rc in role_cols]],
            on="canonical_flora_fauna",
            how="left",
        ).sort_values("Total", ascending=False)

        # Optional: attach overall totals rank (helps reporting)
        TopN_Animals_ByRole = TopN_Animals_ByRole.merge(
            animal_totals.rename(columns={"Total": "Total_all_animals"}),
            on="canonical_flora_fauna",
            how="left",
        )
    else:
        TopN_Animals_ByRole = pd.DataFrame(
            columns=[
                "canonical_flora_fauna", "Actor", "Behaver", "Senser", "Sayer", "Carrier",
                "Total", "Actor_pct", "Behaver_pct", "Senser_pct", "Sayer_pct", "Carrier_pct",
                "Total_all_animals"
            ]
        )

    return {
        "Summary_ProcessTypes": proc,
        "Summary_HumanActive": human_sum,
        "Summary_NatureActive": nature_sum,
        "NatureActive_RoleDist": role_sum,
        "NatureActive_ProcessDist": nature_proc,
        "Top10_FloraFaunaActive": top10,
        "Top10_FloraFauna_RoleBreakdown": top_role,
        # NEW
        "FloraFauna_ByRole": FloraFauna_ByRole,
        "TopN_Animals_ByRole": TopN_Animals_ByRole,
    }



# -----------------------------
# Final AI synthesis (optional but requested)
# -----------------------------
def call_ai_for_final_synthesis(client: OpenAI, tables: Dict[str, pd.DataFrame], out_dir: str) -> Dict[str, Any]:
    """
    Send summarized tables (not full records) back to AI for:
      - consistency check suggestions
      - narrative ecological linguistics insight
    Output JSON and save.
    """

    def df_to_markdown(df: pd.DataFrame, max_rows=50) -> str:
        return df.head(max_rows).to_markdown(index=False)

    payload_md = []
    for name, df in tables.items():
        payload_md.append(f"## {name}\n{df_to_markdown(df)}\n")
    summary_blob = "\n".join(payload_md)

    system_msg = "You are a senior SFL + ecolinguistics reviewer. Output ONLY JSON."
    user_msg = (
        "You will receive aggregated statistics from a clause-level SFL transitivity annotation of a Chinese eco-narrative.\n"
        "Tasks:\n"
        "1) Check internal consistency and flag likely coding inconsistencies to audit (e.g., 有 existential vs possessive; 看/看见; 被字句 active_counted).\n"
        "2) Provide a concise narrative synthesis (Chinese) of what the distributions imply for 'nature agency' in the text.\n"
        "3) Provide concrete next-step QA suggestions (what to spot-check).\n"
        "Return STRICT JSON with keys:\n"
        "{\n"
        '  "consistency_flags": [ {"issue": str, "why_it_matters": str, "how_to_audit": str} ],\n'
        '  "narrative_summary_cn": str,\n'
        '  "qa_plan": [str]\n'
        "}\n\n"
        "Aggregated tables:\n"
        f"{summary_blob}"
    )

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
    )
    content = resp.choices[0].message.content.strip()
    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    data = json.loads(content)

    out_path = os.path.join(out_dir, "final_ai_synthesis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


# -----------------------------
# Excel Writer
# -----------------------------
def add_sheet_from_df(wb: Workbook, name: str, df: pd.DataFrame, percent_cols: Optional[List[str]] = None,
                      freeze: str = "A2"):
    ws = wb.create_sheet(title=name)
    for r_i, row in enumerate(dataframe_to_rows(df, index=False, header=True), start=1):
        ws.append(row)
        if r_i == 1:
            for c in range(1, len(row) + 1):
                cell = ws.cell(row=1, column=c)
                cell.font = Font(bold=True)
                cell.fill = PatternFill("solid", fgColor="F2F2F2")
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = freeze

    # widths + wrap
    for col_i, col_name in enumerate(df.columns, start=1):
        sample = df[col_name].astype(str).head(200).tolist()
        max_len = max([len(str(col_name))] + [len(x) for x in sample]) if sample else len(str(col_name))
        ws.column_dimensions[get_column_letter(col_i)].width = min(max(10, max_len + 2), 90)
        if col_name.lower() in {"clause_text", "sentence", "notes", "active_participant"}:
            ws.column_dimensions[get_column_letter(col_i)].width = 90
            for r in range(2, min(ws.max_row, 500) + 1):
                ws.cell(row=r, column=col_i).alignment = Alignment(wrap_text=True, vertical="top")

    if percent_cols:
        for pc in percent_cols:
            if pc in df.columns:
                cidx = list(df.columns).index(pc) + 1
                for r in range(2, ws.max_row + 1):
                    ws.cell(row=r, column=cidx).number_format = "0.00%"


def write_final_excel(
        out_path: str,
        chunks: List[Chunk],
        records_df: pd.DataFrame,
        unparsed_df: pd.DataFrame,
        tables: Dict[str, pd.DataFrame],
        final_ai: Optional[Dict[str, Any]] = None
):
    print("正在写入 Excel，并在写入前将复杂对象转换为字符串...")

    # === 核心修复开始：创建副本并将 List/Dict 转换为 JSON 字符串 ===
    # 防止影响后续分析，操作副本
    export_records = records_df.copy()
    export_unparsed = unparsed_df.copy()

    def serialize_complex_columns(df: pd.DataFrame):
        if df.empty:
            return df
        for col in df.columns:
            # 检查第一行非空值，或者直接转换特定列
            # 为了保险，检查每一列，如果是 list 或 dict 就转 json
            # 这里使用 apply 逐个检查最稳妥
            df[col] = df[col].apply(
                lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x
            )
        return df

    # 对主要的数据表进行清洗
    export_records = serialize_complex_columns(export_records)
    export_unparsed = serialize_complex_columns(export_unparsed)
    # === 核心修复结束 ===

    wb = Workbook()
    wb.remove(wb.active)

    # README
    ws = wb.create_sheet("README")
    lines = [
        "统计范围：小说正文（作者简介剔除）。",
        f"起点句：{START_SENT}",
        f"终点句：{END_SENT}",
        "规则：动物部位计入动物能动性；存在物不计入主动参与者（active_counted=0），但存在过程计入过程类型分布。",
        "规则：he has X=占有型关系过程；there is X=存在过程。",
        "规则：看老了=生理型行为过程；身上一片云彩都不披=物质过程。",
        "规则：unparsed_unknown 不计入统计。",
        f"总chunks：{len(chunks)}",
        f"总records（已解析）：{len(records_df)}",
        f"总unparsed（未解析，未计入统计）：{len(unparsed_df)}",
    ]
    for i, line in enumerate(lines, start=1):
        ws.cell(row=i, column=1, value=line)
    ws.column_dimensions["A"].width = 120
    ws["A1"].font = Font(bold=True)

    # Chunk index
    chunk_df = pd.DataFrame([asdict(c) for c in chunks])
    # Drop huge marker text from chunk sheet (keep metadata)
    if "text_with_markers" in chunk_df.columns:
        chunk_df = chunk_df.drop(columns=["text_with_markers"])
    add_sheet_from_df(wb, "Chunks_Index", chunk_df)

    # Records
    # Ensure not exceed Excel limit; if exceed, split sheets
    if len(export_records) <= EXCEL_MAX_ROWS:
        add_sheet_from_df(wb, "Annotations_All", export_records)
    else:
        # split into multiple sheets
        n_parts = math.ceil(len(export_records) / EXCEL_MAX_ROWS)
        for i in range(n_parts):
            sub = export_records.iloc[i * EXCEL_MAX_ROWS:(i + 1) * EXCEL_MAX_ROWS].copy()
            add_sheet_from_df(wb, f"Annotations_{i + 1}", sub)

    # Unparsed (optional)
    if not export_unparsed.empty:
        add_sheet_from_df(wb, "Unparsed_Unknown", export_unparsed)

    # Summary tables
    percent_map = {
        "Summary_ProcessTypes": ["pct"],
        "Summary_HumanActive": ["pct_of_active"],
        "Summary_NatureActive": ["pct_of_active"],
        "NatureActive_RoleDist": ["pct_of_nature_active"],
        "NatureActive_ProcessDist": ["pct_of_nature_active"],
        "Top10_FloraFaunaActive": ["pct_of_flora_fauna_active"],
    }
    # Summary tables 通常是聚合后的数字，不需要序列化，但为了保险起见也可以检查
    for name, df in tables.items():
        # 大部分 summary table 是纯数字或字符串，直接写入即可
        # 如果 summary table 里有复杂对象（比如 FloraFauna_ByRole 如果有未展开项），也可以清洗一下
        # 但根据代码逻辑，tables 应该都是扁平的，直接写入：
        add_sheet_from_df(wb, name, df, percent_cols=percent_map.get(name))

    # Final AI synthesis (text)
    if final_ai:
        ws2 = wb.create_sheet("AI_Synthesis")
        ws2.column_dimensions["A"].width = 120
        ws2["A1"].font = Font(bold=True)
        ws2["A1"] = "narrative_summary_cn"
        ws2["A2"] = final_ai.get("narrative_summary_cn", "")

        ws2["A4"].font = Font(bold=True)
        ws2["A4"] = "consistency_flags"
        row = 5
        for item in final_ai.get("consistency_flags", []):
            ws2[f"A{row}"] = f"- issue: {item.get('issue', '')}"
            row += 1
            ws2[f"A{row}"] = f"  why: {item.get('why_it_matters', '')}"
            row += 1
            ws2[f"A{row}"] = f"  audit: {item.get('how_to_audit', '')}"
            row += 2

        ws2[f"A{row}"].font = Font(bold=True)
        ws2[f"A{row}"] = "qa_plan"
        row += 1
        for s in final_ai.get("qa_plan", []):
            ws2[f"A{row}"] = f"- {s}"
            row += 1

    wb.save(out_path)


# -----------------------------
# MAIN
# -----------------------------
def main():
    if not API_KEY:
        raise ValueError("API_KEY 为空。请在脚本顶部填入你的 key。")

    ensure_dir(OUT_DIR)
    cache_dir = os.path.join(OUT_DIR, "cache_chunks")
    ensure_dir(cache_dir)

    print("[1] Extract PDF text...")
    full_text = extract_pdf_text(PDF_PATH)

    print("[2] Slice narrative scope (skip author bio)...")
    scope_compact = slice_narrative_scope(full_text, START_SENT, END_SENT)

    print("[3] Sentence split...")
    sentences = sentence_split(scope_compact)
    # Safety: ensure first/last anchor presence
    if not sentences or (START_SENT.replace(" ", "") not in sentences[0].replace(" ", "")):
        print("WARN: 第一条句子未包含起点锚点，可能是PDF抽取差异，但仍继续。")
    if END_SENT.replace(" ", "") not in sentences[-1].replace(" ", ""):
        print("WARN: 最后一条句子未包含终点锚点，可能是PDF抽取差异，但仍继续。")

    print(f"Total sentences: {len(sentences)}")

    print("[4] Build chunks (paragraph-preferred, sentence-safe)...")
    chunks = build_chunks(sentences)
    print(f"Total chunks: {len(chunks)}")
    chunk_map = {c.chunk_id: c for c in chunks}

    print("[5] Call AI per chunk (with cache/resume)...")
    # client = make_client()
    check_ai_connectivity_or_exit()

    payloads = []
    failed_chunks = []
    for ch in chunks:
        try:
            payload = call_ai_for_chunk(ch, cache_dir)
            payloads.append(payload)
            print(
                f"  chunk {ch.chunk_id}: ok, records={len(payload.get('records', []))}, unparsed={len(payload.get('unparsed', []))}")
        except Exception as e:
            failed_chunks.append({"chunk_id": ch.chunk_id, "error": str(e)})
            print(f"  chunk {ch.chunk_id}: FAILED: {e}")

    # Save failures
    if failed_chunks:
        fail_path = os.path.join(OUT_DIR, "failed_chunks.json")
        with open(fail_path, "w", encoding="utf-8") as f:
            json.dump(failed_chunks, f, ensure_ascii=False, indent=2)
        print(f"WARN: some chunks failed. See: {fail_path}")

    if not payloads:
        raise RuntimeError("No successful chunk payloads; abort.")

    print("[6] Flatten records + compute tables...")
    records_df, unparsed_df = flatten_records(payloads, chunk_map)

    # Minimal normalization: ensure required columns exist
    for col in [
        "sent_id", "clause_id", "clause_text", "process_type", "process_subtype", "process_lexeme",
        "active_participant", "participant_category", "nature_subcategory", "canonical_flora_fauna",
        "role", "circumstances", "embedded_processes", "active_counted", "notes", "chunk_id"
    ]:
        if col not in records_df.columns:
            records_df[col] = None

    # Drop unparsed from stats by design (they are in unparsed_df)
    tables = compute_required_tables(records_df)

    print("[7] Final AI synthesis (optional but requested)...")
    final_ai = None
    # try:
    #     final_ai = call_ai_for_final_synthesis(client, tables, OUT_DIR)
    #     print("  final synthesis: ok")
    # except Exception as e:
    #     print(f"WARN: final synthesis failed: {e}")

    print("[8] Write Excel...")
    out_xlsx = os.path.join(OUT_DIR, "Ergun_FullNovel_SFL_Transitivity.xlsx")
    write_final_excel(out_xlsx, chunks, records_df, unparsed_df, tables, final_ai=final_ai)

    print("DONE.")
    print(f"Excel saved to: {out_xlsx}")


if __name__ == "__main__":
    main()
