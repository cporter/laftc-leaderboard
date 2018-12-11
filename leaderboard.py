import sqlite3
import sys
from collections import defaultdict
import numpy as np

iltmap = (('F1', 'B'), ('F2', 'O'), ('C2', 'A1'), ('C1', 'E'), ('D', 'V'), ('I', 'A2'))

def ilt(league):
    for x in iltmap:
        if league in x:
            return '/'.join(sorted(x))
    return '??'

highs = defaultdict(list)
team_oprs = defaultdict(list)
leagues = {}

for dbname in sorted(sys.argv[1:]):
    league = dbname.split()[0]
    db = sqlite3.connect(dbname)
    cur = db.cursor()
    
    cur.execute('select number from teams')
    teams = []
    for row in cur.fetchall():
        teams.append(row[0])
    
    teamind = {}
    for i, tn in enumerate(teams):
        teamind[tn] = i
        leagues[tn] = league
    
    scores = np.array([0 for x in teams])
    games = np.matrix([[0 for x in teams] for x in teams])
    
    cur.execute('''
    select
            q.red1 as "r1",
            q.red2 as "r2",
            q.red1S as "ru",
            q.blue1 as "b1",
            q.blue2 as "b2",
            q.blue1S as "bu",
            r.redScore as "rs",
            r.redPenaltyCommitted as "rp",
            r.blueScore as "bs",
            r.bluePenaltyCommitted as "bp"
    from
            quals q,
            qualsResults r
    where
            q.match = r.match
    
    ''')

    
    for row in cur.fetchall():
        (r1, r2, ru, b1, b2, bu, rs, rp, bs, bp) = row
        rnp = rs
        bnp = bs
        if (rs + bp) > (bs + rp):
            rr, br = 2, 0
            tp = bnp
        elif (bs + rp) > (rs + bp):
            rr, br = 0, 2
            tp = rnp
        else:
            rr, br = 1, 1
            tp = min(rnp, bnp)

        if ru > 0:
            print('%s %d %d %d %d' % (league, r1, r2, b1, b2), file = sys.stderr)
            
        if ru == 0:
            highs[r1].append((rr, tp))

        if bu == 0:
            highs[b1].append((br, tp))

        highs[r2].append((rr, tp))
        highs[b2].append((br, tp))
    
        scores[teamind[r1]] += rnp
        scores[teamind[r2]] += rnp
        scores[teamind[b1]] += bnp
        scores[teamind[b2]] += bnp
        
        games[teamind[r1], teamind[r2]] += 1
        games[teamind[r2], teamind[r1]] += 1
        games[teamind[b1], teamind[b2]] += 1
        games[teamind[b2], teamind[b1]] += 1
    
        games[teamind[r1], teamind[r1]] += 1
        games[teamind[r2], teamind[r2]] += 1
        games[teamind[b1], teamind[b1]] += 1
        games[teamind[b2], teamind[b2]] += 1
    
    
    opr_raw = scores * games.I
    opr = dict(zip(teams, (opr_raw[0,i] for i in range(len(teams)))))

    for team in teams:
        team_oprs[team].append(opr[team])

def take(n, it):
    for x, _ in zip(it, range(n)):
        yield x

data = []
        
for team in highs.keys():
    trp, ttp = 0, 0
    for rp, tp in take(10, reversed(sorted(highs[team]))):
        trp += rp
        ttp += tp

    oprs = team_oprs[team]
    oprstr = '\t'.join('%.2f' % x for x in oprs)
    print('%s\t%s\t%d\t%d\t%d\t%s' % (ilt(leagues[team]), leagues[team], team, trp, ttp, oprstr))
        
