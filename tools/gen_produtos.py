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

def pagina(ref, nome, esg, temfoto=True):
    url = 'https://lafouch.com/p/%s.html' % ref
    img = ('https://lafouch.com/p/%s.jpg' % ref) if temfoto else 'https://lafouch.com/icon-512.png'
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
    # foto embutida (data:) ou arquivo do próprio site (/media/i/…: o site deixou de embutir as imagens)
    # Desenho (SVG) ou foto que não abre: devolve False e a página sai sem imagem própria (não derruba o robô).
    try:
        if dataurl.startswith('/'):
            im = Image.open(os.path.join(RAIZ, dataurl.lstrip('/'))).convert('RGBA')
        else:
            cab, dado = dataurl.split(',', 1)
            if 'svg' in cab or ';base64' not in cab:
                return False
            dado += '=' * (-len(dado) % 4)
            im = Image.open(io.BytesIO(base64.b64decode(dado))).convert('RGBA')
    except Exception as e:
        print('foto ignorada:', destino, e)
        return False
    fundo = Image.new('RGB', (1200, 630), (255, 255, 255))
    im.thumbnail((1100, 580))
    fundo.paste(im, ((1200 - im.width) // 2, (630 - im.height) // 2), im)
    fundo.save(destino, 'JPEG', quality=85, optimize=True)
    return True

# ===== v453: endereços por página, com prévia no idioma do endereço =====
# Espelho da tabela RT do index.html. A página do robô só tem a prévia (título, texto, foto) e manda para /?r=<endereço>.
RT = {
  'pt': {'home': 'oculos', 'vitrine': 'catalogo', 'rosto': 'formato', 'atacado': 'atacado', 'como': 'como-comprar', 'duvidas': 'duvidas', 'p': 'p',
         't': {'solar': 'sol', 'grau': 'grau', 'armacao': 'armacoes', 'of': 'ofertas'}, 'g': {'f': 'feminino', 'm': 'masculino', 'u': 'unissex'}},
  'es': {'home': 'lentes', 'vitrine': 'tienda', 'rosto': 'tu-forma', 'atacado': 'mayorista', 'como': 'como-compro', 'duvidas': 'dudas', 'p': 'modelo',
         't': {'solar': 'lentes-de-sol', 'grau': 'lectura', 'armacao': 'armazones', 'of': 'descuentos'}, 'g': {'f': 'mujer', 'm': 'hombre', 'u': 'unisex'}},
}
TIT = {
  'pt': {'home': 'La Fouch · Tudo em Óculos', 'vitrine': 'Catálogo', 'solar': 'Óculos de sol', 'grau': 'Óculos de grau', 'armacao': 'Armações', 'of': 'Ofertas',
         'g': {'f': 'Óculos femininos', 'm': 'Óculos masculinos', 'u': 'Óculos unissex'},
         'gm': {'f': 'femininos', 'm': 'masculinos', 'u': 'unissex'}, 'gf': {'f': 'femininas', 'm': 'masculinas', 'u': 'unissex'},
         'rosto': 'Descubra o seu formato', 'atacado': 'Atacado', 'como': 'Como comprar', 'duvidas': 'Dúvidas'},
  'es': {'home': 'La Fouch · Todo en Lentes', 'vitrine': 'Catálogo', 'solar': 'Lentes de sol', 'grau': 'Lentes recetados', 'armacao': 'Armazones', 'of': 'Descuentos',
         'g': {'f': 'Lentes para mujer', 'm': 'Lentes para hombre', 'u': 'Lentes unisex'},
         'gm': {'f': 'para mujer', 'm': 'para hombre', 'u': 'unisex'}, 'gf': {'f': 'para mujer', 'm': 'para hombre', 'u': 'unisex'},
         'rosto': 'Descubrí tu forma', 'atacado': 'Mayorista', 'como': 'Cómo comprar', 'duvidas': 'Dudas'},
}
TXT = {
  'pt': {'ent': 'Retirada em CDE ou delivery', 'desde': '{n} {m} a partir de Gs. {v}', 'of': '{n} {m} com até {x}% OFF', 'vazio': 'Novidades em breve',
         'home': '{n} modelos de sol e de grau', 'mod': ('modelo', 'modelos'),
         'rosto': 'Descubra qual óculos combina com o formato do seu rosto.', 'atacado': 'Preços especiais para revenda. Fale com a gente pelo WhatsApp.',
         'como': 'Escolha, reserve pelo WhatsApp e retire em CDE ou receba por delivery.', 'duvidas': 'Perguntas frequentes sobre compras, retirada e delivery.',
         'peca': 'Reserve pelo WhatsApp e retire na loja. La Fouch · Tudo em Óculos', 'esg': 'Esgotado. Avise-me quando chegar. La Fouch · Tudo em Óculos'},
  'es': {'ent': 'Retiro en CDE o delivery', 'desde': '{n} {m} desde Gs. {v}', 'of': '{n} {m} con hasta {x}% OFF', 'vazio': 'Novedades muy pronto',
         'home': '{n} modelos de sol y recetados', 'mod': ('modelo', 'modelos'),
         'rosto': 'Descubrí qué lentes combinan con la forma de tu rostro.', 'atacado': 'Precios especiales para reventa. Escribinos por WhatsApp.',
         'como': 'Elegí, reservá por WhatsApp y retirá en CDE o recibí por delivery.', 'duvidas': 'Preguntas frecuentes sobre compras, retiro y delivery.',
         'peca': 'Reservá por WhatsApp y retirá en la tienda. La Fouch · Todo en Lentes', 'esg': 'Agotado. Avisame cuando llegue. La Fouch · Todo en Lentes'},
}
OG = os.path.join(RAIZ, 'og')

def mil(v):
    return '{:,}'.format(int(round(float(v or 0)))).replace(',', '.')

def num(v):
    try: return float(v or 0)
    except Exception: return 0.0

def gen_ok(p, g):
    if not g: return True
    pg = p.get('gen') or 'u'
    return pg == 'u' if g == 'u' else pg in (g, 'u')

def is_of(p):
    return num(p.get('de')) > num(p.get('n')) > 0 and p.get('aviso') != 'Esgotado'

def pct(p):
    de, n = num(p.get('de')), num(p.get('n'))
    return int(round((de - n) / de * 100)) if de > n > 0 else 0

def pg_html(lang, url, titulo, desc, img, destino):
    t = html.escape(titulo); d = html.escape(desc)
    return ('<!doctype html><html lang="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><meta name="description" content="%s">'
            '<meta property="og:type" content="website"><meta property="og:site_name" content="La Fouch"><meta property="og:locale" content="%s">'
            '<meta property="og:title" content="%s"><meta property="og:description" content="%s">'
            '<meta property="og:url" content="%s"><meta property="og:image" content="%s">'
            '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            '<meta name="twitter:card" content="summary_large_image"><link rel="canonical" href="%s">'
            '<script>location.replace(%s+(location.search?"&"+location.search.slice(1):""))</script></head>'
            '<body><p><a href="%s">La Fouch</a></p></body></html>') % (
        'es' if lang == 'es' else 'pt-BR', t, d, 'es_PY' if lang == 'es' else 'pt_BR', t, d, url, img, url, json.dumps(destino), destino)

def grava(caminho, txt):
    if not os.path.exists(caminho) or open(caminho, encoding='utf-8').read() != txt:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        open(caminho, 'w', encoding='utf-8').write(txt)

def fonte(nomes, tam):
    from PIL import ImageFont
    for n in nomes:
        for d in ('/usr/share/fonts/truetype/dejavu/', '/usr/share/fonts/truetype/liberation/', ''):
            try: return ImageFont.truetype(d + n, tam)
            except Exception: pass
    try: return ImageFont.load_default(size=tam)
    except Exception: return ImageFont.load_default()

def og_foto(ref, destino, tag):
    """1 foto grande no centro, faixa roxa LA FOUCH embaixo; nas ofertas, etiqueta -X% no canto."""
    from PIL import ImageDraw
    try:
        im = Image.open(os.path.join(SAIDA, ref + '.jpg')).convert('RGB')
    except Exception as e:
        print('og ignorada:', ref, e); return False
    W, H, F = 1200, 630, 92
    bb = Image.eval(im.convert('L'), lambda x: 255 if x < 245 else 0).getbbox()
    if bb: im = im.crop(bb)
    im.thumbnail((900, 420))
    bg = Image.new('RGB', (W, H), (255, 255, 255)); bg.paste(im, ((W - im.width) // 2, (H - F - im.height) // 2))
    d = ImageDraw.Draw(bg); d.rectangle([0, H - F, W, H], fill=(139, 58, 107))
    f = fonte(['DejaVuSerif.ttf', 'LiberationSerif-Regular.ttf'], 40); t = 'LA FOUCH'
    d.text(((W - d.textlength(t, font=f)) / 2, H - 70), t, fill=(255, 255, 255), font=f)
    if tag:
        ft = fonte(['DejaVuSans-Bold.ttf', 'LiberationSans-Bold.ttf'], 44); w = d.textlength(tag, font=ft)
        d.rounded_rectangle([50, 40, 50 + w + 50, 110], 18, fill=(192, 57, 43)); d.text((75, 50), tag, fill=(255, 255, 255), font=ft)
    os.makedirs(OG, exist_ok=True); bg.save(destino, 'JPEG', quality=86, optimize=True)
    return True

def escolhe(lst, g, of):
    """a peça da foto: mais vendida (mv 1..8), depois a mais nova; no filtro de gênero, o gênero exato antes do unissex; nas ofertas, o maior desconto."""
    com = [p for p in lst if os.path.exists(os.path.join(SAIDA, p['ref'] + '.jpg'))]
    if not com: return None
    def k(p):
        mv = int(num(p.get('mv'))) or 99
        return (-pct(p) if of else 0, 0 if (not g or (p.get('gen') or 'u') == g) else 1, mv, -num(p.get('cad')))
    return sorted(com, key=k)[0]

def paginas(prods, foto_ok):
    """prods: produtos visíveis (dict de campos, com 'ref'). Gera <endereço>.html na raiz, og/*.jpg e modelo/REF.html."""
    vis = [p for p in prods if p.get('tipo') != 'acessorio']
    disp = [p for p in vis if p.get('aviso') != 'Esgotado']
    feitos = []
    def lista(t, g):
        r = []
        for p in disp:
            if t == 'of':
                if not is_of(p): continue
            elif t and p.get('tipo') != t: continue
            if not gen_ok(p, g): continue
            r.append(p)
        return r
    def imagem(t, g):
        chave = (t or 'todos') + ('-' + g if g else '')
        lst = lista(t, g); p = escolhe(lst, g, t == 'of')
        if not p: return None, lst
        tag = ('-%d%%' % pct(p)) if t == 'of' and pct(p) else ''
        sig = '%s|%s|%s' % (p['ref'], p.get('fv') or '', tag)
        jpg = os.path.join(OG, chave + '.jpg'); mk = os.path.join(OG, chave + '.sig')
        if not os.path.exists(jpg) or not os.path.exists(mk) or open(mk).read() != sig:
            if not og_foto(p['ref'], jpg, tag): return None, lst
            open(mk, 'w').write(sig)
        v = ''.join(c for c in sig if c.isalnum())[:24]
        return 'https://lafouch.com/og/%s.jpg?v=%s' % (chave, v), lst
    def desc(lang, t, lst):
        T = TXT[lang]
        if not lst: return T['vazio'] + ' · ' + T['ent']
        m = T['mod'][0 if len(lst) == 1 else 1]
        if t == 'of':
            return T['of'].format(n=len(lst), m=m, x=max(pct(p) for p in lst)) + ' · ' + T['ent']
        return T['desde'].format(n=len(lst), m=m, v=mil(min(num(p.get('n')) for p in lst))) + ' · ' + T['ent']
    def titulo(lang, t, g):
        X = TIT[lang]
        if t and g: return X[t] + ' ' + (X['gf'] if t in ('armacao', 'of') else X['gm'])[g]
        if t: return X[t]
        if g: return X['g'][g]
        return X['vitrine']
    def sai(lang, slug, tit, ds, img):
        url = 'https://lafouch.com/' + slug
        grava(os.path.join(RAIZ, slug + '.html'), pg_html(lang, url, tit + ' · La Fouch' if not tit.startswith('La Fouch') else tit, ds, img, '/?r=' + slug))
        feitos.append(slug + '.html')
    casa = {'pt': 'https://lafouch.com/og/inicio-pt.jpg', 'es': 'https://lafouch.com/og/inicio-es.jpg'}
    combos = [(t, g) for t in ['', 'solar', 'grau', 'armacao', 'of'] for g in ['', 'f', 'm', 'u']]
    for t, g in combos:
        img, lst = imagem(t, g)
        for lang in ('pt', 'es'):
            R = RT[lang]
            slug = (R['t'][t] + ('-' + R['g'][g] if g else '')) if t else (R['g'][g] if g else R['vitrine'])
            sai(lang, slug, titulo(lang, t, g), desc(lang, t, lst), img or casa[lang])
    for lang in ('pt', 'es'):
        R, X, T = RT[lang], TIT[lang], TXT[lang]
        sai(lang, R['home'], X['home'], T['home'].format(n=len(disp)) + ' · ' + T['ent'], casa[lang])
        for pan in ('rosto', 'atacado', 'como', 'duvidas'):
            sai(lang, R[pan], X[pan], T[pan], casa[lang])
    # peças em espanhol: /modelo/REF (as de português continuam em /p/REF)
    md = os.path.join(RAIZ, 'modelo'); os.makedirs(md, exist_ok=True); vivas = set()
    for p in vis:
        ref = p['ref']
        if not foto_ok(ref): continue
        vivas.add(ref)
        esg = p.get('aviso') == 'Esgotado'
        tem = os.path.exists(os.path.join(SAIDA, ref + '.jpg'))
        img = ('https://lafouch.com/p/%s.jpg' % ref) if tem else 'https://lafouch.com/icon-512.png'
        tit = '%s (%s) · La Fouch' % (p.get('nome') or ref, ref)
        url = 'https://lafouch.com/modelo/' + ref
        grava(os.path.join(md, ref + '.html'), pg_html('es', url, tit, TXT['es']['esg' if esg else 'peca'], img, '/?ref=' + ref).replace('+(location.search?"&"+location.search.slice(1):"")', ''))
    for n in os.listdir(md):
        if n.rsplit('.', 1)[0] not in vivas: os.remove(os.path.join(md, n))
    return feitos

def main():
    if len(sys.argv) > 2 and sys.argv[1] == '--teste':
        dados = json.load(open(sys.argv[2])); docs = dados['produtos']; fotos = dados['fotos']
    else:
        docs = get('produtos?pageSize=300').get('documents', []); fotos = None
    os.makedirs(SAIDA, exist_ok=True)
    vivos = set(); prods = []
    for d in docs:
        f = campos(d); ref = f.get('ref') or d['name'].split('/')[-1]
        if f.get('oculto') or not ref.replace('-', '').replace('_', '').isalnum(): continue
        f['ref'] = ref
        if f.get('cat') in ('grau', 'armacao') and f.get('tipo') != 'solar': f['tipo'] = f['cat']  # categoria escolhida no painel
        prods.append(f)
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
            if foto(fd, jpg) or os.path.exists(jpg):
                open(marca, 'w').write(fv)
        novo = pagina(ref, f.get('nome') or ref, f.get('aviso') == 'Esgotado', os.path.exists(jpg))
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
        n = re.search(r"nome:'([^']+)'", ch); f = re.search(r"foto:'(data:image/[^']+|/media/i/[^']+)'", ch); av = re.search(r"aviso:'([^']*)'", ch)
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
    feitos = paginas(prods, lambda r: r in vivos)
    print('endereços:', len(feitos))
    if '--teste' not in sys.argv:
        # o workflow só faz "git add -A p": o próprio robô acrescenta os arquivos novos
        import subprocess
        subprocess.run(['git', 'add', '-A', 'modelo', 'og'] + feitos, cwd=RAIZ, check=False)

main()
