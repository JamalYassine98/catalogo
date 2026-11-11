#!/usr/bin/env python3
"""Troca a prévia do WhatsApp (og:image) do teste do Mochi conforme a temática do dia (S169, aprovado 11/11/2026).
Mesma regra do site: o evento manual do painel (config/site.evento) tem prioridade; sem ele, vale o calendário
(config/site.cal: 'auto'/'off'; Halloween desligado por padrão). Só mexe em descubra-o-grau.html e descubri-tu-graduacion.html."""
import json, re, sys, urllib.request, datetime as dt
P, K = 'lafouch-2f6bd', 'AIzaSyAW-54tS1A_VL2EC9OJWFsw1EtboptpEvc'
TZ = dt.timezone(dt.timedelta(hours=-3))  # Paraguai
TEMAS = {'natal', 'anonovo', 'maes', 'pais', 'bf', 'halloween'}
def val(v):
    if not isinstance(v, dict): return v
    for k in ('stringValue', 'integerValue', 'doubleValue', 'booleanValue'):
        if k in v: return float(v[k]) if k in ('integerValue', 'doubleValue') else v[k]
    if 'mapValue' in v: return {a: val(b) for a, b in (v['mapValue'].get('fields') or {}).items()}
    return None
def cfg():
    try:
        u = f'https://firestore.googleapis.com/v1/projects/{P}/databases/(default)/documents/config/site?key={K}'
        d = json.load(urllib.request.urlopen(u, timeout=20))
        return {a: val(b) for a, b in (d.get('fields') or {}).items()}
    except Exception as e:
        print('sem config/site:', e); return {}
def ms(y, m, d, fim=False):
    return dt.datetime(y, m, d, 23 if fim else 0, 59 if fim else 0, 59 if fim else 0, tzinfo=TZ).timestamp() * 1000
def cal(y):
    n1 = dt.date(y, 11, 1); bf = 1 + (4 - (n1.isoweekday() % 7) + 7) % 7 + 21 + 1
    cy = dt.date(y, 11, bf) + dt.timedelta(days=3)
    j1 = dt.date(y, 6, 1); p2 = 1 + (7 - (j1.isoweekday() % 7)) % 7 + 7
    L = []
    if y == 2026: L.append(('bfcde', 'bf', ms(y, 11, 19), ms(y, 11, 22, 1), 'auto'))
    L += [('bf', 'bf', ms(y, 11, bf), ms(y, 11, bf, 1), 'auto'),
          ('cyber', 'bf', ms(cy.year, cy.month, cy.day), ms(cy.year, cy.month, cy.day, 1), 'auto'),
          ('natal', 'natal', ms(y, 12, 1), ms(y, 12, 25, 1), 'auto'),
          ('anonovo', 'anonovo', ms(y, 12, 26), ms(y + 1, 1, 1, 1), 'auto'),
          ('maes', 'maes', ms(y, 5, 1), ms(y, 5, 15, 1), 'auto'),
          ('pais', 'pais', ms(y, 6, 1), ms(y, 6, p2, 1), 'auto'),
          ('halloween', 'halloween', ms(y, 10, 24), ms(y, 10, 31, 1), 'off')]
    return L
def tema(c, agora):
    e = c.get('evento')
    if isinstance(e, dict) and e.get('tema') in TEMAS:
        ini, fim = float(e.get('ini') or 0), float(e.get('fim') or 0)
        if not (ini > 0 and agora < ini) and not (fim > 0 and agora > fim): return e['tema']
    st = c.get('cal') if isinstance(c.get('cal'), dict) else {}
    y = dt.datetime.fromtimestamp(agora / 1000, TZ).year
    for yy in (y - 1, y):
        for i, t, a, b, pad in cal(yy):
            if a <= agora <= b and (st.get(i) if st.get(i) in ('auto', 'off') else pad) == 'auto': return t
    return ''
def main():
    agora = float(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now(TZ).timestamp() * 1000
    t = tema(cfg(), agora); mud = 0
    for arq, lg in (('descubra-o-grau.html', 'pt'), ('descubri-tu-graduacion.html', 'es')):
        h = open(arq, encoding='utf-8').read()
        img = f'https://lafouch.com/og/mochi-{t}-{lg}.jpg' if t else f'https://lafouch.com/og/mochi-{lg}.jpg'
        n = re.sub(r'(<meta property="og:image" content=")[^"]*(")', r'\g<1>' + img + r'\g<2>', h, count=1)
        if n != h: open(arq, 'w', encoding='utf-8').write(n); mud += 1
        print(arq, '->', img)
    print('tema:', t or '(nenhum)', '· arquivos mudados:', mud)
if __name__ == '__main__': main()
