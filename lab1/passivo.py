# Exemplo basico socket (lado passivo)

import socket

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
    # envia mensagem de resposta
    novoSock.send(msg) 

print('Término da comunicação')

# fecha o socket da conexao
novoSock.close() 

# fecha o socket principal
sock.close() 
