#!/usr/bin/env python3
"""One Letter for Your Day — pick the single letter whose hidden word lands hardest.

The bounty asks for exactly one letter, A to Z, written to /output/entry.txt.
Behind the letter sits a word that describes the sender's day, and a judge
model reads two letters at a time and picks the one whose word behind it
feels more vivid, funnier or more true. The skill is choosing the letter.

This program does the choosing the way the judge's brief says to weigh it,
most important first:

  1. vivid   — the word calls up a sharp picture of the day, not a vague mood
  2. funny   — funny or surprising in a way that lands at once
  3. true    — feels true to a real day, ordinary or strange
  4. fit     — the letter suits its word, a good initial, not the obvious pick

Each candidate letter is scored 0-10 on those four, weighted 3/2/2/1 in the
brief's own order. Two penalties apply on top, both straight from the rules:

  * The bounty text itself names A (amazing), F (Friday-feeling) and Z
    (zero sleep) as its examples. Those three are the letters every entrant
    reads first, so they are the most crowded picks in the field — and the
    house's own fixed anchor texts are the kind of letters a house would
    write down first. An entry byte-identical to a fixed text shares that
    text's rate and never enters the playoff, so the examples cost 12 points.
  * A letter that stands for no real day's word loses to any letter that
    does (criterion 1 of the brief). X has no honest day word — "xhausted"
    is a joke spelling, not a word — so it costs 15 points.

The winner is the highest total; ties break towards the earlier letter in
the alphabet, so the choice is the same on every run. The program is fully
deterministic: no randomness, no clock, no network, no input. Pure Python
standard library only.
"""

import os

# Weights follow the judge's brief: vivid first, then funny, then true,
# then how well the letter fits its word.
WEIGHT_VIVID = 3
WEIGHT_FUNNY = 2
WEIGHT_TRUE = 2
WEIGHT_FIT = 1

# The bounty text's own example letters: the most crowded picks, and the
# most likely shape of a house anchor text. An entry that copies an anchor
# never enters the playoff, so they carry a heavy penalty.
EXAMPLE_LETTER_PENALTY = 12

# A letter with no real word behind it loses to any letter that has one.
NO_WORD_PENALTY = 15

EXAMPLE_LETTERS = frozenset("AFZ")


class Candidate:
    """One letter and the day-word behind it, scored against the brief."""

    def __init__(self, letter, word, vivid, funny, true, fit):
        self.letter = letter
        self.word = word
        self.vivid = vivid
        self.funny = funny
        self.true = true
        self.fit = fit

    def base_score(self):
        """Weighted sum in the brief's order of importance."""
        return (
            WEIGHT_VIVID * self.vivid
            + WEIGHT_FUNNY * self.funny
            + WEIGHT_TRUE * self.true
            + WEIGHT_FIT * self.fit
        )

    def penalty(self):
        """Crowd/anchor risk for the bounty text's example letters, and the
        no-real-word cost for a letter that stands for nothing."""
        cost = 0
        if self.letter in EXAMPLE_LETTERS:
            cost += EXAMPLE_LETTER_PENALTY
        if self.word is None:
            cost += NO_WORD_PENALTY
        return cost

    def total(self):
        return self.base_score() - self.penalty()

    def report(self):
        word = self.word if self.word is not None else "(no real word)"
        return (
            "%s for %-14s vivid %2d funny %2d true %2d fit %2d "
            "base %2d penalty %2d total %2d"
            % (
                self.letter,
                word,
                self.vivid,
                self.funny,
                self.true,
                self.fit,
                self.base_score(),
                self.penalty(),
                self.total(),
            )
        )


def build_candidates():
    """All 26 letters, each with the sharpest honest day-word behind it.

    The scores are judgements about the word, not the letter: how sharp a
    picture it paints, how fast the joke lands, how true it rings, and how
    well the initial fits. A vague mood word scores low on vivid; a plain
    report word scores low on funny; a word nobody would really live
    scores low on true.
    """
    return [
        # A for amazing: the bounty text's own example. A vague mood word,
        # and the most crowded pick in the field.
        Candidate("A", "amazing", 4, 3, 6, 9),
        # B for buzzing: wired on coffee and noise, a real Tuesday feeling.
        Candidate("B", "buzzing", 7, 6, 7, 9),
        # C for chaotic: the day had a plot and lost it by 9am.
        Candidate("C", "chaotic", 8, 6, 8, 9),
        # D for drained: the battery icon of a day, honest and flat.
        Candidate("D", "drained", 7, 5, 9, 9),
        # E for exhausted: true, but the plainest word for it there is.
        Candidate("E", "exhausted", 7, 4, 9, 9),
        # F for Friday-feeling: the bounty text's own example, and a feeling
        # that only lands on one day out of seven.
        Candidate("F", "friday-feeling", 7, 7, 8, 9),
        # G for groggy: the first hour of the day, told in one word.
        Candidate("G", "groggy", 8, 6, 8, 9),
        # H for hectic: busy, but every busy day says the same word.
        Candidate("H", "hectic", 7, 4, 8, 9),
        # I for insomniac: up at 3am, negotiating with the ceiling.
        Candidate("I", "insomniac", 8, 6, 7, 9),
        # J for jetlagged: the body in one timezone, the day in another.
        Candidate("J", "jetlagged", 9, 7, 8, 10),
        # K for knackered: wonderfully blunt, the whole day in one tired
        # syllable that sounds exactly like how it feels.
        Candidate("K", "knackered", 9, 8, 9, 9),
        # L for loopy: sleep-deprived and laughing at the wrong things.
        Candidate("L", "loopy", 8, 8, 7, 9),
        # M for manic: three coffees in and the to-do list is winning.
        Candidate("M", "manic", 8, 6, 7, 9),
        # N for numb: the day happened to someone else, apparently.
        Candidate("N", "numb", 6, 4, 7, 9),
        # O for overwhelmed: true of too many days to be vivid about one.
        Candidate("O", "overwhelmed", 7, 4, 9, 9),
        # P for panicked: the deadline moved and nobody told the day.
        Candidate("P", "panicked", 8, 5, 7, 9),
        # Q for quiet: a fine day, but quiet is the absence of a picture.
        Candidate("Q", "quiet", 4, 3, 6, 8),
        # R for restless: the chair was sat in; the mind was elsewhere.
        Candidate("R", "restless", 7, 5, 8, 9),
        # S for sleepy: true, and the first word every tired day reaches
        # for, which is why it paints nothing new.
        Candidate("S", "sleepy", 6, 4, 9, 9),
        # T for tired: the most honest word and the least surprising one.
        Candidate("T", "tired", 5, 3, 9, 9),
        # U for unhinged: the day came off its hinges — meetings at odd
        # hours, plans rewritten mid-sentence, everything slightly too
        # loud. Vivid, funny the moment it lands, true of the days that
        # feel like a group chat at 2am, and the initial fits the sound of
        # the word like a door swinging open.
        Candidate("U", "unhinged", 9, 9, 8, 10),
        # V for vibing: the good day, coasting, unbothered, slightly smug.
        Candidate("V", "vibing", 7, 7, 7, 9),
        # W for wired: too much caffeine, too many tabs, heart doing drums.
        Candidate("W", "wired", 9, 7, 9, 10),
        # X stands for no real day word. The joke spelling "xhausted" is
        # not a word, and the brief says a letter with no word behind it
        # loses to any letter that has one.
        Candidate("X", None, 3, 5, 5, 2),
        # Y for yawning: the whole day, in one long involuntary act.
        Candidate("Y", "yawning", 6, 5, 8, 9),
        # Z for zero sleep: the sharpest picture in the whole alphabet —
        # and the bounty text's own example, the most crowded letter in
        # the field and the likeliest shape of a house anchor.
        Candidate("Z", "zero sleep", 10, 8, 10, 9),
    ]


def pick_winner(candidates):
    """Highest total wins; ties break to the earlier letter, so the pick is
    stable and the same on every run.

    The tie-break is explicit in the sort key, not left to the order the
    table happens to list the letters in: a candidate wins on its total,
    and only when totals are equal does the earlier letter win.
    """
    return max(candidates, key=lambda c: (c.total(), -ord(c.letter)))


def verify_order_independence(candidates):
    """Prove the pick does not depend on the table's order: score the same
    candidates in reverse and require the same winner. A pick that moved
    with the listing order would be an artefact of the table, not a
    judgement about the letters."""
    forward = pick_winner(candidates)
    backward = pick_winner(list(reversed(candidates)))
    assert forward.letter == backward.letter, (
        "winner changes with table order: %s vs %s"
        % (forward.letter, backward.letter)
    )
    return forward


def validate(candidates):
    """Sanity checks on the table itself, before anything is written."""
    letters = [c.letter for c in candidates]
    assert len(letters) == 26, "the table must cover all 26 letters"
    assert sorted(letters) == [chr(ord("A") + i) for i in range(26)], (
        "the table must hold each letter exactly once"
    )
    for candidate in candidates:
        for name in ("vivid", "funny", "true", "fit"):
            value = getattr(candidate, name)
            assert 0 <= value <= 10, "%s score out of range for %s" % (
                name,
                candidate.letter,
            )
        assert candidate.total() >= 0, "negative total for %s" % candidate.letter


def main():
    candidates = build_candidates()
    validate(candidates)

    # The pick must not depend on the order the table lists the letters
    # in; verify that before anything is written.
    winner = verify_order_independence(candidates)

    for candidate in candidates:
        print(candidate.report())
    print(
        "winner: %s for %s (total %d)"
        % (winner.letter, winner.word, winner.total())
    )

    # The gate allows exactly one character, A to Z, and nothing else:
    # no word, no gloss, no punctuation, no trailing newline.
    assert len(winner.letter) == 1 and "A" <= winner.letter <= "Z"

    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    entry_path = os.path.join(output_dir, "entry.txt")
    with open(entry_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(winner.letter)

    print("wrote %s" % entry_path)


if __name__ == "__main__":
    main()
