import random

from jogo_da_velha import branco, token, verifica_ganhador

score = {
    "EMPATE": 0,
    "X": 1,
    "O": -1
}

#função de posições
def get_posicoes(board):
    posicoes = []

    for i in range(3):
        for j in range(3):
            if (board[i][j] == branco):
                posicoes.append([i, j])
    
    return posicoes

#função de movimento da I.A.
def movimento_ia(board, jogador):
    possibilidades = get_posicoes(board)
    melhor_valor = None
    melhor_movimento = None

    for possibilidade in possibilidades:
        board[possibilidade[0]][possibilidade[1]] = token[jogador]
        valor = minimax(board, jogador)
        board[possibilidade[0]][possibilidade[1]] = branco

        if melhor_valor is None:
            melhor_valor = valor
            melhor_movimento = possibilidade
        elif jogador == 0:
            if (valor > melhor_valor):
                melhor_valor = valor
                melhor_movimento = possibilidade
        elif jogador == 1:
            if (valor < melhor_valor):
                melhor_valor = valor
                melhor_movimento = possibilidade

    return melhor_movimento[0], melhor_movimento[1]

def minimax(board, jogador):
    ganhador = verifica_ganhador(board)

    if (ganhador):
        return score[ganhador]
    
    jogador = (jogador + 1) % 2

    possibilidades = get_posicoes(board)
    melhor_valor = None

    for possibilidade in possibilidades:
        board[possibilidade[0]][possibilidade[1]] = token[jogador]
        valor = minimax(board, jogador)
        board[possibilidade[0]][possibilidade[1]] = branco
        
        if melhor_valor is None:
            melhor_valor = valor
        elif jogador == 0:
            if (valor > melhor_valor):
                melhor_valor = valor
        elif jogador == 1:
            if (valor < melhor_valor):
                melhor_valor = valor
    
    return melhor_valor

def movimentoIA_facil(board, jogador):
    posicoes = get_posicoes(board)
    escolha = random.choice(posicoes)
    return escolha[0], escolha[1]

def movimentoIA_medio(board, jogador):
    if random.random() < 0.5:
        return movimento_ia(board, jogador)
    else:
        return movimentoIA_facil(board, jogador)