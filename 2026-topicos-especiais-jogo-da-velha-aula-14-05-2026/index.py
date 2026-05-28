import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jogo_da_velha import criar_board, faz_movimento, get_input_valido, \
                            print_board, verifica_ganhador, verica_movimento

from minimax import movimento_ia

jogador = 0
board = criar_board()
ganhador = verifica_ganhador(board)

def imprime_barra():
    print("===================") #19 sinais de =

while(not ganhador):
    print_board(board)
    imprime_barra()

    if (jogador == 0):
        i, j = movimento_ia(board, jogador)
    else:
        i = get_input_valido("Digite a linha: ")
        j = get_input_valido("Digite a coluna: ")

    if (verica_movimento(board, i, j)):
        faz_movimento(board, i, j, jogador)
        jogador = (jogador + 1) % 2
    else:
        print("A posicição informada já esta ocupada")

    ganhador = verifica_ganhador(board)

imprime_barra()
print_board(board)
print("Ganhador = ", ganhador)
imprime_barra()