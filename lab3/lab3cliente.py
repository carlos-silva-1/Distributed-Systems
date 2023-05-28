import socket

HOST = 'localhost'  # maquina onde esta o par passivo
PORTA = 9090        # porta que o par passivo esta escutando

# cria socket
sock = socket.socket() # default: socket.AF_INET, socket.SOCK_STREAM 

# conecta-se com o par passivo
sock.connect((HOST, PORTA)) 

while True:
    print("Digite o nome do arquivo a ser processado. \nEx: candidatos.txt, para processar um arquivo de nome \"candidatos\". \nSe deseja terminar a comunicação, não digite nenhuma mensagem e aperte ENTER.")
    msg = input()
    # a mensagem vazia indica o término da comunicação
    if not msg: break
    # converte a mensagem em bytes e a envia ao servidor
    msgBytes = bytes(msg, encoding='utf-8')
    sock.send(msgBytes)
    # recebe a mensagem do servidor. A mensagem pode indicar um erro ou é a lista de palavras ordenada
    msgRecv = sock.recv(1024) # argumento indica a qtde maxima de bytes da mensagem
    print("Resultado do processamento:")
    print(str(msgRecv,  encoding='utf-8'))

print('Término da comunicação')

# encerra a conexao
sock.close() 
