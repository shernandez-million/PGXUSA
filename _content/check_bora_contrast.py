#!/usr/bin/env python3
"""
Detect false-contrast claims about the Board of Rules and Appeals.

VERIFIED FACT: BOTH Miami-Dade and Broward have a Board of Rules and Appeals.
Miami-Dade's exists under Chapter 8, Sec. 8-4 of the Miami-Dade County Code: it is the
board of appeals for building-official decisions countywide (incorporated and
unincorporated), it issues code interpretations, and it is the local construction
regulation board for contractor permitting authority county-wide.

Any content claiming Broward has a board / county layer / code authority that
Miami-Dade lacks is FALSE. This script walks every string value in every *.json in
_content (skipping site_plan.json) and reports remaining false-contrast claims,
in English or Spanish.
"""
import json, glob, os, re, sys, collections

CONTENT = os.path.dirname(os.path.abspath(__file__))
SKIP = {'site_plan.json'}

BOARD = re.compile(r'Board of Rules|Rules and Appeals|\bBORA\b|Reglas y Apelaciones|Junta de Reglas', re.I)
MD    = re.compile(r'Miami[- ]Dade', re.I)
BRO   = re.compile(r'\bBroward\b', re.I)

# A. explicit denial that Miami-Dade has the thing
EXPLICIT = re.compile(
    r'(en\s+Miami[- ]Dade\s+no\s+(existe|hay|tiene)'
    r'|que\s+Miami[- ]Dade\s+no\s+(tiene|existe|usa|aplica|conoce)'
    r'|Miami[- ]Dade\s+no\s+(tiene|cuenta\s+con|posee|dispone)'
    r'|unlike\s+Miami[- ]Dade'
    r'|a\s+diferencia\s+de\s+Miami[- ]Dade'
    r'|Miami[- ]Dade\s+(does\s+not|doesn.t|has\s+no|lacks)'
    r'|(which|that)\s+Miami[- ]Dade\s+(does\s+not|doesn.t|has\s+no|lacks)'
    r'|no\s+equivalent\s+in\s+Miami[- ]Dade'
    r'|sin\s+equivalente\s+en\s+Miami[- ]Dade)', re.I)

# B. contrast connectors that split a two-county sentence into clauses
SPLIT = re.compile(r'\s*(?:,\s*while\s+|\bwhile\s+|\bwhereas\s+|\bmientras\s+que\s+|\bmientras\s+|;\s*|\ben\s+cambio\b)', re.I)

# C. additive framing that gives Broward an extra tier
ADDITIVE = re.compile(
    r'(Broward\s+(also|then)?\s*(adds|layers|runs|adds\s+its\s+own|stacks)'
    r'|Broward\s+(suma|agrega|añade|anade)(\s+(adem[aá]s|tambi[eé]n|luego|despu[eé]s))?'
    r'|Broward\s+(adem[aá]s|tambi[eé]n)\s+(suma|agrega|a[nñ]ade)'
    r'|layers\s+a\s+county\s+Board'
    r'|its\s+own\s+layer|su\s+propia\s+capa|una\s+capa\s+m[aá]s|otra\s+capa)', re.I)

# true jurisdiction statements: Miami-Dade's building department genuinely has no role in
# Broward and vice versa. That is not a claim about which county has a board.
JURISDICTION = re.compile(
    r'(building\s+department\s+has\s+no\s+role'
    r'|departamento\s+de\s+construcci[oó]n\s+de\s+Miami[- ]Dade\s+no\s+tiene\s+ninguna\s+injerencia'
    r'|no\s+tiene\s+(ninguna\s+)?(injerencia|jurisdicci[oó]n|competencia)'
    r'|has\s+no\s+(role|jurisdiction|say)\s+(on|in)\s+this\s+side)', re.I)

# symmetric wording that explicitly gives BOTH counties a board -> never a false contrast
SYMMETRIC = re.compile(
    r'(each\s+county|both\s+counties|every\s+county'
    r'|cada\s+condado|ambos\s+condados|los\s+dos\s+condados'
    r'|each\s+has\s+its\s+own|cada\s+uno\s+tiene\s+(el\s+)?suyo|cada\s+uno\s+tiene\s+su\s+propio)', re.I)


def walk(o, path=''):
    if isinstance(o, str):
        yield path, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, path + '/' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, path + '/' + str(i))


def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|(?<=—)\s+', text) if s.strip()]


def judge(sent, para):
    """Return a reason string if this sentence draws a false contrast, else None."""
    para_is_about_board = bool(BOARD.search(para))
    if not BOARD.search(sent) and not para_is_about_board:
        return None
    if SYMMETRIC.search(sent):
        return None

    # A. explicit denial, in the sentence itself or elsewhere in a board paragraph
    if EXPLICIT.search(sent) and not JURISDICTION.search(sent):
        return 'EXPLICIT: denies Miami-Dade has what Broward has'
    if not BOARD.search(sent):
        return None

    # B. two-county sentence where the board sits only on the Broward side of a contrast
    if MD.search(sent) and BRO.search(sent):
        clauses = SPLIT.split(sent)
        if len(clauses) > 1:
            bro_board = [c for c in clauses if BOARD.search(c) and BRO.search(c) and not MD.search(c)]
            md_noboard = [c for c in clauses if MD.search(c) and not BOARD.search(c)]
            if bro_board and md_noboard:
                return 'ASYMMETRIC: county-vs-county contrast puts the board only on the Broward side'

    # C. additive framing inside a paragraph that also names Miami-Dade
    if ADDITIVE.search(sent) and MD.search(para) and not SYMMETRIC.search(para):
        # only when the paragraph never credits Miami-Dade with a board of its own
        md_board = any(BOARD.search(s) and MD.search(s) and not BRO.search(s) for s in sentences(para))
        if not md_board:
            return 'ADDITIVE: frames the board as an extra tier Broward alone has, in a two-county paragraph'
    return None


def main():
    files = sorted(f for f in glob.glob(os.path.join(CONTENT, '*.json'))
                   if os.path.basename(f) not in SKIP)
    findings = []
    board_sentences = 0
    for f in files:
        with open(f, encoding='utf-8') as fh:
            data = json.load(fh)
        for path, text in walk(data):
            sents = sentences(text)
            for sent in sents:
                if BOARD.search(sent):
                    board_sentences += 1
                reason = judge(sent, text)
                if reason:
                    findings.append((os.path.basename(f), path, reason, sent))

    print('files scanned            : %d' % len(files))
    print('sentences naming the board: %d' % board_sentences)
    print('false-contrast claims     : %d' % len(findings))
    for fname, path, reason, sent in findings:
        print('-' * 88)
        print('%s  %s' % (fname, path))
        print('  [%s]' % reason)
        print('  %s' % sent)
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
