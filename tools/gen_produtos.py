#!/usr/bin/env python3
"""Gera uma página por produto (p/REF.html + p/REF.jpg) para o WhatsApp mostrar foto e nome ao abrir o link.
Lê os produtos publicados no Firestore (leitura pública, a mesma que o site usa). Uso: python3 tools/gen_produtos.py [--teste docs.json]"""
import base64, html, io, json, os, sys, urllib.request
from PIL import Image

P, K = 'lafouch-2f6bd', 'AIzaSyAW-54tS1A_VL2EC9OJWFsw1EtboptpEvc'
BASE = 'https://firestore.googleapis.com/v1/projects/%s/databases/(default)/documents/' % P
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, 'p')

def get(path):
    with urllib.request.urlopen(BASE + path + ('&' if '?' in path else '?') + 'key=' + K, timeout=60) as r:
        return json.load(r)

def val(v):
    for k in ('stringValue', 'integerValue', 'doubleValue', 'booleanValue'):
        if k in v: return v[k]
    return None

def campos(d):
    return {k: val(v) for k, v in (d.get('fields') or {}).items()}

def pagina(ref, nome, esg):
    url = 'https://lafouch.com/p/%s.html' % ref
    img = 'https://lafouch.com/p/%s.jpg' % ref
    t = html.escape('%s (%s) · La Fouch' % (nome, ref))
    desc = html.escape(('Esgotado. Avise-me quando chegar. ' if esg else 'Reserve pelo WhatsApp e retire na loja. ') + 'La Fouch · Tudo em Óculos')
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><meta name="description" content="%s">'
            '<meta property="og:type" content="website"><meta property="og:site_name" content="La Fouch">'
            '<meta property="og:title" content="%s"><meta property="og:description" content="%s">'
            '<meta property="og:url" content="%s"><meta property="og:image" content="%s">'
            '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            '<meta name="twitter:card" content="summary_large_image">'
            '<script>location.replace("/?ref=%s")</script></head>'
            '<body><p><a href="/?ref=%s">Ver %s na La Fouch</a></p></body></html>') % (t, desc, t, desc, url, img, ref, ref, html.escape(nome))

def foto(dataurl, destino):
    im = Image.open(io.BytesIO(base64.b64decode(dataurl.split(',', 1)[1]))).convert('RGBA')
    fundo = Image.new('RGB', (1200, 630), (255, 255, 255))
    im.thumbnail((1100, 580))
    fundo.paste(im, ((1200 - im.width) // 2, (630 - im.height) // 2), im)
    fundo.save(destino, 'JPEG', quality=85, optimize=True)

def main():
    if len(sys.argv) > 2 and sys.argv[1] == '--teste':
        dados = json.load(open(sys.argv[2])); docs = dados['produtos']; fotos = dados['fotos']
    else:
        docs = get('produtos?pageSize=300').get('documents', []); fotos = None
    os.makedirs(SAIDA, exist_ok=True)
    vivos = set()
    for d in docs:
        f = campos(d); ref = f.get('ref') or d['name'].split('/')[-1]
        if f.get('oculto') or not ref.replace('-', '').replace('_', '').isalnum(): continue
        try:
            fd = fotos.get(ref) if fotos is not None else campos(get('fotos/' + ref)).get('d')
        except Exception:
            fd = None
        if not fd: continue
        vivos.add(ref)
        jpg = os.path.join(SAIDA, ref + '.jpg'); pg = os.path.join(SAIDA, ref + '.html')
        # só refaz a foto se o produto mudou de versão da foto (fv) ou ainda não existe
        marca = os.path.join(SAIDA, ref + '.fv')
        fv = str(f.get('fv') or '')
        if not os.path.exists(jpg) or not os.path.exists(marca) or open(marca).read() != fv:
            foto(fd, jpg); open(marca, 'w').write(fv)
        novo = pagina(ref, f.get('nome') or ref, f.get('aviso') == 'Esgotado')
        if not os.path.exists(pg) or open(pg, encoding='utf-8').read() != novo:
            open(pg, 'w', encoding='utf-8').write(novo)
    # produtos que já vêm dentro do próprio site (enquanto não foram publicados na vitrine)
    import re
    fs = {}
    for d in docs:
        c = campos(d); fs[c.get('ref') or d['name'].split('/')[-1]] = c
    src = open(os.path.join(RAIZ, 'index.html'), encoding='utf-8').read()
    for ch in src.split("{ref:'")[1:]:
        ch = ch.split("{ref:'")[0]
        m = re.match(r"([A-Za-z0-9_-]+)'", ch)
        n = re.search(r"nome:'([^']+)'", ch); f = re.search(r"foto:'(data:image/[^']+)'", ch); av = re.search(r"aviso:'([^']*)'", ch)
        if not (m and n and f) or m.group(1) in vivos: continue
        ref = m.group(1); c = fs.get(ref, {})
        if c.get('oculto'): continue
        jpg = os.path.join(SAIDA, ref + '.jpg'); pg = os.path.join(SAIDA, ref + '.html')
        vivos.add(ref)
        if not os.path.exists(jpg): foto(f.group(1), jpg)
        novo = pagina(ref, c.get('nome') or n.group(1), (c.get('aviso') if 'aviso' in c else (av.group(1) if av else '')) == 'Esgotado')
        if not os.path.exists(pg) or open(pg, encoding='utf-8').read() != novo: open(pg, 'w', encoding='utf-8').write(novo)
    for n in os.listdir(SAIDA):
        base = n.rsplit('.', 1)[0]
        if base not in vivos: os.remove(os.path.join(SAIDA, n))
    print('páginas:', len(vivos))

main()
