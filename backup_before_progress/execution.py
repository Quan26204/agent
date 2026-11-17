"""Small, approval-gated execution engine for ATO jobs.

Only explicitly implemented handlers can run. Never execute LLM-generated code.
"""
from datetime import datetime, timezone
import requests
from threading import Lock

from .models import ATOPlan, ATOJob

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen3:8b"
_EXECUTION_LOCK = Lock()


def utc_now():
    return datetime.now(timezone.utc)


def _summarize(job, dependency_outputs):
    payload = job.payload or {}
    source_text = payload.get("text") or payload.get("content") or payload.get("input")
    if not source_text and dependency_outputs:
        source_text = "\n\n".join(dependency_outputs)
    if not source_text:
        raise ValueError(
            "Summarization requires payload.text/content/input or output from a dependency."
        )

    prompt = (
        "Summarize the following material accurately. Do not invent facts. "
        "Use clear headings and concise bullet points where useful.\n\n"
        f"MATERIAL:\n{source_text}"
    )
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL_NAME, "prompt": prompt, "stream": False, "think": False},
        timeout=180,
    )
    response.raise_for_status()
    result = response.json().get("response", "").strip()
    if not result:
        raise RuntimeError("Ollama returned an empty summary.")
    return result


def _chatbot_summarize_document(job, dependency_outputs):
    """
    Summarize every indexed chunk belonging to one uploaded PDF.

    The normal /chat endpoint intentionally retrieves only top-k relevant
    chunks. This agent instead performs an exact metadata lookup by filename
    and uses a map-reduce process so the whole document is covered.
    """
    import json
    import os

    from backend.rag.vector_store import collection
    from backend.rag.llm import generate_answer

    payload = job.payload or {}
    source = (
        payload.get("source")
        or payload.get("filename")
        or payload.get("document_name")
    )

    if not isinstance(source, str) or not source.strip():
        raise ValueError(
            "Document summarization requires payload.source with the exact "
            "uploaded PDF filename (for example, attention.pdf)."
        )

    source = source.strip()

    # The Chroma metadata stores only the basename, never an arbitrary path.
    if os.path.basename(source) != source or not source.lower().endswith(".pdf"):
        raise ValueError(
            "payload.source must be an exact PDF filename, not a path."
        )

    stored = collection.get(
        where={"source": source},
        include=["documents", "metadatas"],
    )

    ids = stored.get("ids") or []
    texts = stored.get("documents") or []
    metadatas = stored.get("metadatas") or []

    if not ids or not texts:
        raise ValueError(
            f"No indexed chunks were found for '{source}'. "
            "Check the filename and make sure PDF ingestion has completed."
        )

    chunks = []
    for index, chunk_id in enumerate(ids):
        text = texts[index] if index < len(texts) else ""
        if not text or not text.strip():
            continue

        metadata = metadatas[index] if index < len(metadatas) else {}
        metadata = metadata or {}
        page = metadata.get("page")

        # Current ingestion IDs are chunk_<number>; this preserves the
        # original ingestion order, with page as a useful secondary key.
        suffix = str(chunk_id).rsplit("_", 1)[-1]
        try:
            sequence = int(suffix)
        except ValueError:
            sequence = index

        try:
            page_order = int(page) if page is not None else 0
        except (TypeError, ValueError):
            page_order = 0

        chunks.append({
            "id": str(chunk_id),
            "text": text.strip(),
            "page": page_order if page_order > 0 else None,
            "sequence": sequence,
        })

    if not chunks:
        raise ValueError(f"'{source}' has no readable text chunks.")

    chunks.sort(key=lambda item: (item["sequence"], item["page"] or 0))

    # Map stage: summarize small groups of chunks, keeping prompts bounded.
    group_size = 4
    partial_summaries = []
    for start in range(0, len(chunks), group_size):
        group = chunks[start:start + group_size]
        material = "\n\n".join(
            (
                f"[Page {item['page']}]\n{item['text']}"
                if item["page"] is not None
                else item["text"]
            )
            for item in group
        )
        prompt = (
            "You are summarizing part of a PDF document. Summarize all "
            "important claims, definitions, explanations, examples, and "
            "conclusions in this section. Preserve technical terms and "
            "important numbers. Do not add outside information. Do not "
            "omit a major point merely to be brief.\\n\\n"
            f"DOCUMENT: {source}\\n"
            f"SECTION {len(partial_summaries) + 1}\\n\\n"
            f"{material}\\n\\nSECTION SUMMARY:"
        )
        partial = generate_answer(prompt).strip()
        if not partial:
            raise RuntimeError(
                f"Qwen returned an empty summary for section "
                f"{len(partial_summaries) + 1}."
            )
        partial_summaries.append(partial)

    # Reduce stage: recursively merge section summaries until a bounded
    # number remains, then produce the final document summary.
    while len(partial_summaries) > 4:
        reduced = []
        for start in range(0, len(partial_summaries), 4):
            batch = partial_summaries[start:start + 4]
            prompt = (
                "Merge these section summaries into one accurate summary. "
                "Remove repetition but retain distinct key information, "
                "technical details, examples and conclusions. Do not add "
                "outside facts.\\n\\n"
                + "\n\n".join(batch)
                + "\\n\\nMERGED SUMMARY:"
            )
            merged = generate_answer(prompt).strip()
            if not merged:
                raise RuntimeError("Qwen returned an empty intermediate summary.")
            reduced.append(merged)
        partial_summaries = reduced

    final_prompt = (
        "Create a coherent, well-structured summary of the entire PDF using "
        "the section summaries below. Include an overview, key concepts and "
        "findings, important details/examples, and conclusions where present. "
        "Avoid repetition. Do not invent information or use outside knowledge. "
        "If the document does not contain a type of information, do not fabricate it.\\n\\n"
        f"DOCUMENT: {source}\\n\\n"
        + "\n\n".join(partial_summaries)
        + "\\n\\nFULL DOCUMENT SUMMARY:"
    )
    final_summary = generate_answer(final_prompt).strip()

    if not final_summary:
        raise RuntimeError("Qwen returned an empty final document summary.")

    pages = sorted({
        item["page"] for item in chunks if item["page"] is not None
    })

    return json.dumps(
        {
            "source": source,
            "chunks_processed": len(chunks),
            "pages": pages,
            "summary": final_summary,
        },
        ensure_ascii=False,
    )


HANDLERS = {
    ("summarization_agent", "summarize"): _summarize,
    ("chatbot_agent", "summarize_document"): _chatbot_summarize_document,
}


def execute_plan(db, plan_id: str):
    """Execute an approved plan in dependency order; persist every transition."""
    if not _EXECUTION_LOCK.acquire(blocking=False):
        raise ValueError("Another plan is currently executing in this backend process. Try again shortly.")
    try:
        return _execute_plan_locked(db, plan_id)
    finally:
        _EXECUTION_LOCK.release()


def _execute_plan_locked(db, plan_id: str):
    plan = db.query(ATOPlan).filter(ATOPlan.id == plan_id).with_for_update().first()
    if plan is None:
        raise LookupError("Plan not found")
    if plan.status != "approved":
        raise ValueError(f"Plan must be approved before execution (current: {plan.status}).")
    if not plan.jobs:
        raise ValueError("Plan has no jobs to execute.")

    plan.status = "executing"
    db.commit()
    db.refresh(plan)

    jobs = list(plan.jobs)
    by_id = {job.id: job for job in jobs}
    remaining = {job.id for job in jobs if job.status not in ("completed", "failed", "cancelled")}
    outputs = {job.id: job.output for job in jobs if job.output}

    while remaining:
        progressed = False
        for job_id in list(remaining):
            job = by_id[job_id]
            dependencies = [by_id.get(dep_id) for dep_id in (job.depends_on or [])]
            if any(dep is None for dep in dependencies):
                job.status = "failed"
                job.error = "A dependency references a missing job."
            elif any(dep.status in ("failed", "cancelled", "blocked") for dep in dependencies):
                job.status = "blocked"
                job.error = "Blocked because a dependency did not complete successfully."
            elif any(dep.status != "completed" for dep in dependencies):
                continue
            else:
                handler = HANDLERS.get((job.target_agent, job.job_type))
                if handler is None:
                    job.status = "failed"
                    job.error = (
                        f"No execution handler is registered for "
                        f"{job.target_agent}/{job.job_type}. This agent is not executable yet."
                    )
                else:
                    job.status = "running"
                    job.started_at = utc_now()
                    job.error = None
                    db.commit()
                    try:
                        dependency_outputs = [dep.output for dep in dependencies if dep.output]
                        job.output = handler(job, dependency_outputs)
                        job.status = "completed"
                        job.completed_at = utc_now()
                        outputs[job.id] = job.output
                    except Exception as exc:
                        job.status = "failed"
                        job.error = str(exc)[:4000]
                        job.completed_at = utc_now()
            db.commit()
            remaining.remove(job_id)
            progressed = True

        if not progressed:
            # Remaining jobs are waiting on a cycle or an impossible dependency state.
            for job_id in remaining:
                by_id[job_id].status = "blocked"
                by_id[job_id].error = "Could not resolve job dependencies; check the dependency graph."
            db.commit()
            remaining.clear()

    statuses = [job.status for job in jobs]
    if all(status == "completed" for status in statuses):
        plan.status = "completed"
    elif any(status == "completed" for status in statuses):
        plan.status = "partially_completed"
    else:
        plan.status = "failed"
    db.commit()
    db.refresh(plan)
    return plan
