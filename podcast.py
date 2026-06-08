"""
Podcast generation — turns generated lecture notes into a two-host audio
podcast, chapter by chapter, using OpenAI TTS.

Uses the synchronous OpenAI SDK (chat + audio) so it doesn't touch the app's
async layer. Cheap: gpt-4o-mini for the dialogue script + tts-1 for audio.
"""
import json
import logging
import re
from typing import Callable, Dict, List, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

# The 6 built-in OpenAI TTS voices.
OPENAI_TTS_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

_HEADING_RE = re.compile(r'^\s{0,3}#{1,3}\s+(.+?)\s*#*\s*$', re.MULTILINE)


def split_into_chapters(text: str, max_chapters: int = 5) -> List[Dict[str, str]]:
    """Split lecture markdown into (title, body) chapters by headings."""
    text = (text or "").strip()
    if not text:
        return []
    matches = list(_HEADING_RE.finditer(text))
    chapters: List[Dict[str, str]] = []
    if matches:
        for i, m in enumerate(matches):
            title = m.group(1).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            if len(body) > 40:  # skip tiny/empty sections
                chapters.append({"title": title, "body": body})
    if not chapters:
        chapters = [{"title": "Full Lecture", "body": text}]
    return chapters[:max_chapters]


def _generate_dialogue(client: OpenAI, model: str, course_name: str,
                       chapter_title: str, chapter_body: str,
                       host_a: str, host_b: str) -> List[Dict[str, str]]:
    """Ask the LLM for a grounded two-host dialogue as JSON turns."""
    system = (
        "You write lively but factually accurate two-host educational podcast scripts. "
        "Ground the conversation ONLY in the provided lecture content — never invent "
        "statistics, studies, or facts that aren't in the source."
    )
    user = f"""Turn this lecture chapter from "{course_name}" into a natural two-host podcast dialogue.

Hosts: "{host_a}" and "{host_b}" (curious co-hosts explaining the material to learners).
Chapter: {chapter_title}

CONTENT:
{chapter_body[:4000]}

Return ONLY a JSON array of 6-10 turns, alternating speakers, like:
[{{"speaker": "A", "text": "..."}}, {{"speaker": "B", "text": "..."}}]
"A" = {host_a}, "B" = {host_b}. Keep each turn 1-3 sentences, conversational, accurate."""

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0.7,
    )
    raw = resp.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1].lstrip("json").strip() if "```json" in raw else raw.split("```")[1].strip()
    try:
        turns = json.loads(raw)
        return [t for t in turns if t.get("text")]
    except Exception as e:
        logger.warning(f"Dialogue JSON parse failed for '{chapter_title}': {e}")
        return [{"speaker": "A", "text": chapter_body[:600]}]


def _synthesize(client: OpenAI, turns: List[Dict[str, str]],
                voice_a: str, voice_b: str) -> bytes:
    """TTS each turn with the speaker's voice; concatenate to one MP3."""
    chunks: List[bytes] = []
    for t in turns:
        voice = voice_a if str(t.get("speaker", "A")).upper().startswith("A") else voice_b
        text = (t.get("text") or "").strip()
        if not text:
            continue
        resp = client.audio.speech.create(model="tts-1", voice=voice, input=text)
        chunks.append(resp.content)
    return b"".join(chunks)


def build_podcast(api_key: str, course_name: str, lecture_text: str,
                  voice_a: str, voice_b: str, model: str = "gpt-4o-mini",
                  max_chapters: int = 5,
                  progress: Optional[Callable[[str], None]] = None) -> List[Dict]:
    """Build chapter-wise podcast episodes from lecture notes.

    Returns a list of {title, script (turns), audio (mp3 bytes)} per chapter.
    """
    client = OpenAI(api_key=api_key)
    chapters = split_into_chapters(lecture_text, max_chapters=max_chapters)
    episodes: List[Dict] = []
    for i, ch in enumerate(chapters, 1):
        if progress:
            progress(f"🎙️ Chapter {i}/{len(chapters)}: {ch['title']}")
        turns = _generate_dialogue(client, model, course_name, ch["title"], ch["body"], voice_a, voice_b)
        audio = _synthesize(client, turns, voice_a, voice_b)
        episodes.append({"title": ch["title"], "script": turns, "audio": audio})
    return episodes
