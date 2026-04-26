"""
Linguistic patterns for Say-Do tagging.

SAY patterns capture habitual, normative, or aspirational claims.
DO patterns capture actual, episodic, or past-behaviour reports.
"""

# ---------------------------------------------------------------------------
# SAY patterns — what participants *claim* they do habitually
# ---------------------------------------------------------------------------
SAY_PATTERNS = [
    # Frequency/habit markers
    r"\bI always\b",
    r"\bI usually\b",
    r"\bI typically\b",
    r"\bI generally\b",
    r"\bI regularly\b",
    r"\bI consistently\b",
    r"\bI routinely\b",
    r"\bI often\b",
    # Intent / preference
    r"\bI tend to\b",
    r"\bI try to\b",
    r"\bI try not to\b",
    r"\bI like to\b",
    r"\bI prefer to\b",
    r"\bI prefer\b",
    r"\bI make sure to\b",
    r"\bI make a point\b",
    r"\bI make it a habit\b",
    r"\bI aim to\b",
    r"\bI strive to\b",
    r"\bI prioritize\b",
    r"\bI prioritise\b",
    # Normative / self-concept
    r"\bI never\b",
    r"\bI would never\b",
    r"\bI wouldn't\b",
    r"\bI'm good about\b",
    r"\bI'm careful to\b",
    r"\bI'm diligent\b",
    r"\bI'm supposed to\b",
    r"\bI should\b",
    r"\bI need to\b",
    r"\bI want to\b",
    r"\bI plan to\b",
    r"\bI always try\b",
    r"\bI'm the kind of person\b",
    r"\bI believe in\b",
    r"\bI value\b",
    r"\bI commit to\b",
]

# ---------------------------------------------------------------------------
# DO patterns — what participants *actually* report doing (past / episodic)
# ---------------------------------------------------------------------------
DO_PATTERNS = [
    # Direct past-tense anchors
    r"\bI actually\b",
    r"\bI ended up\b",
    r"\bI found myself\b",
    r"\bI realized\b",
    r"\bI realised\b",
    r"\bI noticed\b",
    r"\bI forgot\b",
    r"\bI skipped\b",
    r"\bI missed\b",
    r"\bI gave up\b",
    r"\bI stopped\b",
    r"\bI started\b",
    r"\bI ignored\b",
    r"\bI clicked\b",
    r"\bI opened\b",
    r"\bI closed\b",
    r"\bI scrolled\b",
    r"\bI downloaded\b",
    r"\bI bought\b",
    r"\bI tried\b",
    r"\bI used\b",
    r"\bI went\b",
    r"\bI checked\b",
    r"\bI sent\b",
    r"\bI got distracted\b",
    r"\bI couldn't\b",
    r"\bI didn't\b",
    r"\bI hadn't\b",
    r"\bI wasn't\b",
    r"\bI don't\b",
    # Time anchors (strong episodic signals)
    r"\blast time I\b",
    r"\byesterday I\b",
    r"\blast week I\b",
    r"\blast month I\b",
    r"\bthat day I\b",
    r"\bone time I\b",
    r"\bonce I\b",
    r"\bthat morning\b",
    r"\bthat evening\b",
    r"\bthat meeting\b",
    r"\bin the end\b",
    r"\bin practice\b",
    r"\bin reality\b",
]

# ---------------------------------------------------------------------------
# Polarity markers
# ---------------------------------------------------------------------------
NEGATIVE_MARKERS = {
    "didn't", "don't", "never", "not", "no", "without", "forgot",
    "skipped", "missed", "ignored", "avoided", "stopped", "quit",
    "gave up", "failed", "couldn't", "wouldn't", "wasn't", "hadn't",
    "barely", "rarely", "seldom", "hardly", "can't", "won't",
    "distracted", "delayed", "late", "overslept", "ignored",
}

POSITIVE_MARKERS = {
    "always", "usually", "typically", "regularly", "every", "consistently",
    "checked", "completed", "finished", "managed", "remembered", "made sure",
    "succeeded", "accomplished", "did", "built", "created", "sent",
    "reviewed", "confirmed", "organised", "organized", "scheduled",
}

# ---------------------------------------------------------------------------
# Stopwords to exclude from keyword extraction
# ---------------------------------------------------------------------------
STOPWORDS = {
    "i", "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "that",
    "this", "it", "its", "my", "your", "our", "their", "his", "her",
    "we", "they", "he", "she", "you", "me", "him", "us", "them",
    "so", "if", "when", "what", "how", "why", "which", "who", "whom",
    "just", "like", "really", "very", "also", "even", "still", "already",
    "then", "there", "here", "where", "about", "up", "out", "get", "got",
    "as", "than", "into", "through", "during", "before", "after", "some",
    "know", "think", "feel", "want", "need", "let", "make", "thing",
    "kind", "sort", "bit", "lot", "way", "time", "day", "week", "much",
    "every", "each", "both", "any", "all", "these", "those", "such",
}
