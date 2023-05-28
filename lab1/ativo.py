# Exemplo basico socket (lado ativo)

import socket

HOST = 'localhost'  # maquina onde esta o par passivo
PORTA = 9090        # porta que o par passivo esta escutando

# cria socket
sock = socket.socket() # default: socket.AF_INET, socket.SOCK_STREAM 

# conecta-se com o par passivo
sock.connect((HOST, PORTA)) 

while True:
    print('Digite a mensagem a ser enviada. Caso não deseje enviar nenhuma mensagem, aperte ENTER')
    msg = input()
    # a mensagem vazia indica o término da comunicação
    if not msg: break
    # converte a mensagem em bytes e a envia ao passivo
    msgBytes = bytes(msg, encoding='utf-8')
    sock.send(msgBytes)
    # recebe a mensagem do passivo. A mensagem deve ser igual a mensagem enviada acima
    msgRecv = sock.recv(1024) # argumento indica a qtde maxima de bytes da mensagem
    print(str(msgRecv,  encoding='utf-8'))

print('Término da comunicação')

# encerra a conexao
sock.close() 
