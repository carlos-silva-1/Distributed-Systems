# Referencias:
# https://www.tutorialkart.com/python/python-read-file-as-string/
# https://www.delftstack.com/howto/python/python-counter-most-common/

import socket
from collections import Counter

# Conta as 5 palavras mais comuns no arquivo e retorna esses termos ordenados
# Parametros:
#   conteudoDoArquivo (string): arquivo de texto em string única
#   numeroDePalavras (int): numero de palavras mais comuns buscadas
def contaPalavrasMaisComuns(conteudoDoArquivo, numeroDePalavras = 5):
    conteudoEmPalavras = conteudoDoArquivo.split() # separa a string em uma lista de palavras
    c = Counter(conteudoEmPalavras)
    palavrasMaisComuns = str(c.most_common(numeroDePalavras))
    return palavrasMaisComuns

HOST = ''       # '' possibilita acessar qualquer endereco alcancavel da maquina local
PORTA = 9090    # porta onde chegarao as mensagens para essa aplicacao

# cria um socket para comunicacao
sock = socket.socket() # valores default: socket.AF_INET, socket.SOCK_STREAM  

# vincula a interface e porta para comunicacao
sock.bind((HOST, PORTA))

# define o limite maximo de conexoes pendentes e coloca-se em modo de espera por conexao
sock.listen(1) 

# aceita a primeira conexao da fila (chamada pode ser BLOQUEANTE)
novoSock, endereco = sock.accept() # retorna um novo socket e o endereco do par conectado
print ('Conectado com: ', endereco)

while True:
    # depois de conectar-se, espera uma mensagem (chamada pode ser BLOQUEANTE))
    msg = novoSock.recv(1024) # argumento indica a qtde maxima de dados
    # receber a mensagem vazia indica que nenhuma outra mensagem será enviada
    if not msg: break 
    # converte a mensagem de bytes para string
    fileName = str(msg, encoding='utf-8')

    # abre o arquivo e o converte para string. caso haja alguma falha, lança uma exceção e envia uma mensagem de erro
    conteudoDoArquivo = '' # armazena o arquivo como uma string, caso o arquivo seja encontrado
    try:
        arquivoAberto = open(fileName)
        conteudoDoArquivo = arquivoAberto.read()
    except FileNotFoundError:
        msgErroBytes = bytes("Erro: um arquivo com o nome especificado não foi encontrado.", encoding='utf-8')
        novoSock.send(msgErroBytes)

    palavrasMaisComuns = contaPalavrasMaisComuns(conteudoDoArquivo)
    novoSock.send(bytes(palavrasMaisComuns, encoding='utf-8'))

print('Término da comunicação')

# fecha o socket da conexao
novoSock.close() 

# fecha o socket principal
sock.close() 
