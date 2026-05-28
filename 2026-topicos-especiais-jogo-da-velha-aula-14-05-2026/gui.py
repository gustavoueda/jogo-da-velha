import os
import sys
import tempfile
import threading
import urllib.request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pygame

from jogo_da_velha import criar_board, faz_movimento, verifica_ganhador, verica_movimento
from minimax import movimento_ia, movimentoIA_facil, movimentoIA_medio

# ── Dimensões e cores ────────────────────────────────────────────────────────
W, H          = 600, 600
BARRA_H       = 60
BOARD_H       = H - BARRA_H   # 540
CELL_W        = W // 3        # 200
CELL_H        = BOARD_H // 3  # 180

COR_FUNDO     = (0,   0,   0)
COR_BARRA     = (15,  15,  15)
COR_LINHA     = (200, 200, 200)
COR_BOTAO     = (255, 255, 255)
COR_HOVER     = (200, 225, 255)
COR_BORDA     = (80,  80,  80)
COR_DESTAQUE  = (255, 220, 0)
COR_X         = (210, 50,  50)
COR_O         = (80,  100, 240)
COR_GANHOU    = (60,  210, 80)
COR_PERDEU    = (220, 50,  50)
COR_EMPATE    = (210, 210, 210)
COR_BRANCO    = (255, 255, 255)
COR_AZUL_CLARO= (160, 195, 255)
COR_CAIXA     = (20,  30,  60)

DIR = os.path.dirname(os.path.abspath(__file__))


# ── Clipboard via PowerShell ─────────────────────────────────────────────────
def get_clipboard():
    try:
        import subprocess
        result = subprocess.run(
            ['powershell', '-noprofile', '-command', 'Get-Clipboard'],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


# ── Download de áudio por link direto ────────────────────────────────────────
def baixar_url(url):
    try:
        suffix = '.mp3'
        url_limpa = url.split('?')[0].lower()
        for ext in ['.ogg', '.wav', '.mp3', '.m4a']:
            if url_limpa.endswith(ext):
                suffix = ext
                break
        caminho = os.path.join(tempfile.gettempdir(), f'jv_musica{suffix}')
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'audio/mpeg,audio/*;q=0.9,*/*;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(caminho, 'wb') as f:
                f.write(resp.read())
        return caminho, None
    except Exception as e:
        return None, str(e)


# ── Classe Botão ─────────────────────────────────────────────────────────────
class Botao:
    def __init__(self, x, y, w, h, texto, fonte,
                 cor=COR_BOTAO, hover=COR_HOVER, cor_texto=(20, 20, 20)):
        self.rect      = pygame.Rect(x, y, w, h)
        self.texto     = texto
        self.fonte     = fonte
        self.cor       = cor
        self.hover     = hover
        self.cor_texto = cor_texto

    def draw(self, win, mouse_pos):
        c = self.hover if self.rect.collidepoint(mouse_pos) else self.cor
        pygame.draw.rect(win, c,         self.rect, border_radius=10)
        pygame.draw.rect(win, COR_BORDA, self.rect, 2, border_radius=10)
        surf = self.fonte.render(self.texto, True, self.cor_texto)
        win.blit(surf, (
            self.rect.x + (self.rect.w - surf.get_width())  // 2,
            self.rect.y + (self.rect.h - surf.get_height()) // 2,
        ))

    def clicado(self, event, mouse_pos):
        return (event.type == pygame.MOUSEBUTTONUP
                and event.button == 1
                and self.rect.collidepoint(mouse_pos))


# ── Utilitários de desenho ───────────────────────────────────────────────────
def centralizar(win, texto, fonte, cor, y):
    surf = fonte.render(texto, True, cor)
    win.blit(surf, ((W - surf.get_width()) // 2, y))

def fundo(win):
    win.fill(COR_FUNDO)


# ── Música ───────────────────────────────────────────────────────────────────
def listar_musicas():
    arquivos = sorted(
        f for f in os.listdir(DIR)
        if f.lower().endswith(('.mp3', '.ogg', '.wav'))
    )
    return ["Sem musica"] + arquivos

def tocar_musica(nome):
    pygame.mixer.music.stop()
    if nome == "Sem musica":
        return False
    caminho = nome if os.path.isabs(nome) else os.path.join(DIR, nome)
    try:
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.play(-1)
        return True
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════════════════
# TELA: Digitação de link
# ════════════════════════════════════════════════════════════════════════════
def tela_input_url(win, fontes):
    texto = ""
    clock = pygame.time.Clock()

    btn_colar  = Botao(50,  380, 230, 48, "Colar  Ctrl+V", fontes['btn'])
    btn_ok     = Botao(320, 380, 100, 48, "OK",            fontes['btn'])
    btn_limpar = Botao(430, 380, 120, 48, "Limpar",        fontes['btn'])
    btn_voltar = Botao(20,  545, 150, 40, "< Voltar",      fontes['btn'])

    input_rect = pygame.Rect(30, 290, 540, 52)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        fundo(win)

        centralizar(win, "Link da Musica",                               fontes['titulo'],  COR_DESTAQUE,    60)
        centralizar(win, "Cole o link direto do audio (.mp3 / .ogg / .wav)", fontes['pequeno'], COR_AZUL_CLARO, 135)
        centralizar(win, "Clique em 'Colar' ou pressione Ctrl+V",        fontes['pequeno'], (80, 100, 140),  165)

        pygame.draw.rect(win, COR_CAIXA,    input_rect, border_radius=8)
        pygame.draw.rect(win, COR_DESTAQUE, input_rect, 2, border_radius=8)

        exibir = texto
        surf   = fontes['pequeno'].render(exibir, True, COR_BRANCO)
        while surf.get_width() > input_rect.w - 16:
            exibir = exibir[1:]
            surf   = fontes['pequeno'].render(exibir, True, COR_BRANCO)

        if texto:
            win.blit(surf, (input_rect.x + 8,
                            input_rect.y + (input_rect.h - surf.get_height()) // 2))
        else:
            ph = fontes['pequeno'].render("https://...", True, (70, 90, 130))
            win.blit(ph,   (input_rect.x + 8,
                            input_rect.y + (input_rect.h - ph.get_height()) // 2))

        btn_colar.draw(win, mouse_pos)
        btn_ok.draw(win, mouse_pos)
        btn_limpar.draw(win, mouse_pos)
        btn_voltar.draw(win, mouse_pos)

        pygame.display.update()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if event.key == pygame.K_BACKSPACE:
                    texto = texto[:-1]
                elif event.key == pygame.K_DELETE:
                    texto = ""
                elif event.key == pygame.K_v and (mods & pygame.KMOD_CTRL):
                    texto = get_clipboard()
                elif event.key not in (pygame.K_RETURN, pygame.K_ESCAPE,
                                       pygame.K_LCTRL, pygame.K_RCTRL,
                                       pygame.K_LSHIFT, pygame.K_RSHIFT,
                                       pygame.K_LALT, pygame.K_RALT):
                    if event.unicode.isprintable():
                        texto += event.unicode

            if btn_colar.clicado(event, mouse_pos):
                texto = get_clipboard()
            elif btn_ok.clicado(event, mouse_pos):
                return texto.strip() or None
            elif btn_limpar.clicado(event, mouse_pos):
                texto = ""
            elif btn_voltar.clicado(event, mouse_pos):
                return None


# ════════════════════════════════════════════════════════════════════════════
# TELA: Seleção de música
# ════════════════════════════════════════════════════════════════════════════
def tela_musica(win, fontes, musica_atual):
    musicas      = listar_musicas()
    idx          = musicas.index(musica_atual) if musica_atual in musicas else 0
    clock        = pygame.time.Clock()
    url_status   = ""
    url_caminho  = None
    download_res = [None]
    thread_dl    = [None]

    btn_ant    = Botao(60,  188, 50,  44, "<<",         fontes['btn'])
    btn_prox   = Botao(490, 188, 50,  44, ">>",         fontes['btn'])
    btn_link   = Botao(150, 330, 300, 50, "Colar Link", fontes['btn'])
    btn_ok     = Botao(175, 460, 250, 52, "Confirmar",  fontes['btn'])
    btn_voltar = Botao(20,  545, 150, 40, "< Voltar",   fontes['btn'])

    tocar_musica(musicas[idx])

    while True:
        mouse_pos = pygame.mouse.get_pos()
        fundo(win)

        centralizar(win, "Escolha a Musica", fontes['titulo'], COR_DESTAQUE, 22)

        lbl = fontes['pequeno'].render("Arquivos locais:", True, COR_AZUL_CLARO)
        win.blit(lbl, (60, 95))

        caixa = pygame.Rect(120, 115, 360, 56)
        pygame.draw.rect(win, COR_CAIXA,    caixa, border_radius=10)
        pygame.draw.rect(win, COR_DESTAQUE, caixa, 2, border_radius=10)
        nome = musicas[idx]
        if len(nome) > 26:
            nome = nome[:23] + "..."
        centralizar(win, nome,                             fontes['medio'],   COR_BRANCO,    128)
        centralizar(win, f"{idx + 1}  /  {len(musicas)}", fontes['pequeno'], COR_AZUL_CLARO, 180)

        btn_ant.draw(win, mouse_pos)
        btn_prox.draw(win, mouse_pos)

        pygame.draw.line(win, (50, 55, 80), (40, 248), (560, 248), 1)
        sep = fontes['pequeno'].render("ou baixe por link direto (.mp3 / .ogg / .wav):", True, (100, 120, 160))
        win.blit(sep, ((W - sep.get_width()) // 2, 262))

        btn_link.draw(win, mouse_pos)

        if url_status:
            cor_s = COR_GANHOU if url_status.startswith("ok") else \
                    COR_PERDEU if url_status.startswith("erro") else COR_DESTAQUE
            s = fontes['pequeno'].render(url_status, True, cor_s)
            win.blit(s, ((W - s.get_width()) // 2, 395))

        btn_ok.draw(win, mouse_pos)
        btn_voltar.draw(win, mouse_pos)

        pygame.display.update()
        clock.tick(60)

        # Checa resultado do download
        if thread_dl[0] and not thread_dl[0].is_alive():
            thread_dl[0] = None
            if download_res[0] is not None:
                caminho, erro = download_res[0]
                download_res[0] = None
                if caminho:
                    if tocar_musica(caminho):
                        url_caminho = caminho
                        url_status  = "ok - musica carregada!"
                    else:
                        url_status = "erro: link nao e um audio valido"
                else:
                    url_status = f"erro: {str(erro)[:45]}"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_UP):
                    idx = (idx - 1) % len(musicas)
                    tocar_musica(musicas[idx])
                    url_caminho = None; url_status = ""
                elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                    idx = (idx + 1) % len(musicas)
                    tocar_musica(musicas[idx])
                    url_caminho = None; url_status = ""
                elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    return url_caminho if url_caminho else musicas[idx]

            if btn_ant.clicado(event, mouse_pos):
                idx = (idx - 1) % len(musicas)
                tocar_musica(musicas[idx])
                url_caminho = None; url_status = ""

            elif btn_prox.clicado(event, mouse_pos):
                idx = (idx + 1) % len(musicas)
                tocar_musica(musicas[idx])
                url_caminho = None; url_status = ""

            elif btn_link.clicado(event, mouse_pos):
                if thread_dl[0] is None:
                    url = tela_input_url(win, fontes)
                    if url:
                        url_status      = "carregando..."
                        download_res[0] = None
                        def _baixar(u=url):
                            download_res[0] = baixar_url(u)
                        thread_dl[0] = threading.Thread(target=_baixar, daemon=True)
                        thread_dl[0].start()

            elif btn_ok.clicado(event, mouse_pos):
                return url_caminho if url_caminho else musicas[idx]

            elif btn_voltar.clicado(event, mouse_pos):
                return url_caminho if url_caminho else musicas[idx]


# ════════════════════════════════════════════════════════════════════════════
# TELA: Menu principal
# ════════════════════════════════════════════════════════════════════════════
def tela_menu(win, fontes, musica_atual):
    clock = pygame.time.Clock()

    btn_facil   = Botao(175, 190, 250, 55, "1  -  Facil",   fontes['btn'])
    btn_medio   = Botao(175, 268, 250, 55, "2  -  Medio",   fontes['btn'])
    btn_dificil = Botao(175, 346, 250, 55, "3  -  Dificil", fontes['btn'])
    btn_musica  = Botao(175, 450, 250, 46, "Musica",        fontes['btn'])

    while True:
        mouse_pos = pygame.mouse.get_pos()
        fundo(win)

        centralizar(win, "Jogo da Velha",        fontes['titulo'], COR_DESTAQUE,    65)
        centralizar(win, "Escolha a dificuldade:", fontes['medio'], COR_AZUL_CLARO, 145)

        nome_m = os.path.basename(musica_atual)
        if len(nome_m) > 24:
            nome_m = nome_m[:21] + "..."
        centralizar(win, f"Musica: {nome_m}", fontes['pequeno'], (80, 100, 140), 522)

        btn_facil.draw(win, mouse_pos)
        btn_medio.draw(win, mouse_pos)
        btn_dificil.draw(win, mouse_pos)
        btn_musica.draw(win, mouse_pos)

        pygame.display.update()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 1, False
                elif event.key == pygame.K_2:
                    return 2, False
                elif event.key == pygame.K_3:
                    return 3, False

            if btn_facil.clicado(event, mouse_pos):
                return 1, False
            elif btn_medio.clicado(event, mouse_pos):
                return 2, False
            elif btn_dificil.clicado(event, mouse_pos):
                return 3, False
            elif btn_musica.clicado(event, mouse_pos):
                return None, True


# ════════════════════════════════════════════════════════════════════════════
# TELA: Jogo
# ════════════════════════════════════════════════════════════════════════════
def draw_tabuleiro(win, board, fontes):
    for k in range(1, 3):
        pygame.draw.line(win, COR_LINHA, (0, k * CELL_H), (W, k * CELL_H), 3)
        pygame.draw.line(win, COR_LINHA, (k * CELL_W, 0), (k * CELL_W, BOARD_H), 3)

    for i in range(3):
        for j in range(3):
            peca = board[i][j]
            if peca == " ":
                continue
            cor  = COR_X if peca == "X" else COR_O
            surf = fontes['peca'].render(peca, True, cor)
            x = j * CELL_W + (CELL_W - surf.get_width())  // 2
            y = i * CELL_H + (CELL_H - surf.get_height()) // 2
            win.blit(surf, (x, y))

def draw_jogo(win, board, dificuldade, fontes, mouse_pos, btn_voltar, vez_humano):
    nomes = {1: "Facil", 2: "Medio", 3: "Dificil"}
    fundo(win)
    draw_tabuleiro(win, board, fontes)

    pygame.draw.rect(win, COR_BARRA, (0, BOARD_H, W, BARRA_H))
    dif = fontes['pequeno'].render(f"Dificuldade: {nomes[dificuldade]}", True, COR_AZUL_CLARO)
    win.blit(dif, (12, BOARD_H + 8))

    vez_txt = "Sua vez" if vez_humano else "IA jogando..."
    cor_vez = COR_GANHOU if vez_humano else COR_DESTAQUE
    vez = fontes['pequeno'].render(vez_txt, True, cor_vez)
    win.blit(vez, (12, BOARD_H + 34))

    btn_voltar.draw(win, mouse_pos)


def jogar(win, fontes, dificuldade):
    board    = criar_board()
    jogador  = 0
    ganhador = False
    clock    = pygame.time.Clock()

    btn_voltar = Botao(430, BOARD_H + 10, 158, 40, "< Menu", fontes['btn'])

    while not ganhador:
        vez_humano = (jogador == 0)
        mouse_pos  = pygame.mouse.get_pos()

        draw_jogo(win, board, dificuldade, fontes, mouse_pos, btn_voltar, vez_humano)
        pygame.display.update()
        clock.tick(60)

        if jogador == 0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "sair"
                if btn_voltar.clicado(event, mouse_pos):
                    return "menu"
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    px, py = event.pos
                    if py < BOARD_H:
                        i = py // CELL_H
                        j = px // CELL_W
                        if verica_movimento(board, i, j):
                            faz_movimento(board, i, j, jogador)
                            jogador = 1
        else:
            pygame.time.wait(350)
            if dificuldade == 1:
                i, j = movimentoIA_facil(board, jogador)
            elif dificuldade == 2:
                i, j = movimentoIA_medio(board, jogador)
            else:
                i, j = movimento_ia(board, jogador)

            faz_movimento(board, i, j, jogador)
            jogador = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "sair"
                if btn_voltar.clicado(event, mouse_pos):
                    return "menu"

        ganhador = verifica_ganhador(board)

    mouse_pos = pygame.mouse.get_pos()
    draw_jogo(win, board, dificuldade, fontes, mouse_pos, btn_voltar, False)
    pygame.display.update()

    return tela_fim(win, ganhador, fontes)


# ════════════════════════════════════════════════════════════════════════════
# TELA: Fim de jogo
# ════════════════════════════════════════════════════════════════════════════
def tela_fim(win, ganhador, fontes):
    if ganhador == "X":
        msg, sub, cor_msg = "VC GANHOU!",  "Parabens! Voce venceu a IA.", COR_GANHOU
    elif ganhador == "O":
        msg, sub, cor_msg = "VC PERDEU!",  "A IA foi melhor dessa vez.",   COR_PERDEU
    else:
        msg, sub, cor_msg = "VELHA!",      "Empate! Ninguem venceu.",       COR_EMPATE

    btn_novamente = Botao(60,  390, 210, 55, "Jogar Novamente", fontes['btn'])
    btn_menu      = Botao(330, 390, 210, 55, "Menu Principal",  fontes['btn'])
    clock         = pygame.time.Clock()

    while True:
        mouse_pos = pygame.mouse.get_pos()

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        win.blit(overlay, (0, 0))

        caixa = pygame.Rect(80, 180, 440, 240)
        pygame.draw.rect(win, (10, 15, 40), caixa, border_radius=18)
        pygame.draw.rect(win, cor_msg,      caixa, 3,  border_radius=18)

        centralizar(win, msg, fontes['titulo_grande'], cor_msg,    210)
        centralizar(win, sub, fontes['pequeno'],       COR_BRANCO, 310)

        btn_novamente.draw(win, mouse_pos)
        btn_menu.draw(win, mouse_pos)

        pygame.display.update()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "sair"
            if btn_novamente.clicado(event, mouse_pos):
                return "novamente"
            if btn_menu.clicado(event, mouse_pos):
                return "menu"


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    pygame.init()
    pygame.mixer.init()

    win = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Jogo da Velha")

    fontes = {
        'titulo':         pygame.font.SysFont('comicsans', 52, bold=True),
        'titulo_grande':  pygame.font.SysFont('comicsans', 72, bold=True),
        'medio':          pygame.font.SysFont('comicsans', 30),
        'btn':            pygame.font.SysFont('comicsans', 26),
        'pequeno':        pygame.font.SysFont('comicsans', 20),
        'peca':           pygame.font.SysFont('comicsans', 110, bold=True),
    }

    musica_atual = "musica.mp3"
    tocar_musica(musica_atual)

    while True:
        dificuldade, ir_musica = tela_menu(win, fontes, musica_atual)

        if dificuldade is None and not ir_musica:
            break

        if ir_musica:
            resultado = tela_musica(win, fontes, musica_atual)
            if resultado is None:
                break
            musica_atual = resultado
            tocar_musica(musica_atual)
            continue

        while True:
            resultado = jogar(win, fontes, dificuldade)
            if resultado == "sair":
                pygame.quit()
                return
            elif resultado == "menu":
                break
            elif resultado == "novamente":
                continue

    pygame.quit()


main()
