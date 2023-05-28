import socket
import select
import sys

'''
Premissas:

Existem 5 comandos disponíveis ao usuário:
- ler: imprime o valor local da variável X;
- escrever: modifica o valor local da variável X;
- historico: imprime o histórico de mudancas a variável X;
- fim: termina o programa;
- imprime_infos: imprime algumas variáveis do programa (auxílio para debug).

Um usuário que não possui a cópia primária faz uma requisição a ela ao tentar modificar a variável X.
Esse usuário deve continuar tentando modificar a variável por meio deste comando até que a cópia 
primária seja dada a ele. Ao obter a cópia primária, deve novamente digitar o comando 'escrever', 
que agora o permitirá modificar o valor de X.

Um usuário pode modificar o valor de X quantas vezes desejar, até que digite 'termino', indicando 
que não possui outras modificações a realizar.
'''

INT_SIZE_IN_BYTES = 4

HOST = 'localhost'
PORT = 10000

#define a lista de I/O de interesse (jah inclui a entrada padrao)
entradas = [sys.stdin]

# ID da copia local
local_copy_identifier = None
# Key: id da copia, Value: porta da copia
REPLICAS = [[1, 10001], [2, 10002], [3, 10003], [4, 10004]]

N = 4 # numero de replicas permanentes
X = 0 # valor local da copia

changes_history = []

# indica o id de quem possui a copia primaria
# replica de id 1 comeca com a copia primaria
primary_copy_identifier = 1
holds_primary_copy = False
can_give_primary_away = False

header_primary_request = "primary_request"
header_primary_update = "primary_update"
header_history_update = "history_update"
header_ack = "ack"

previous_X_value = None

def inicia_servidor():
	'''Cria um socket de servidor e o coloca em modo de espera por conexões
	Saida: o socket criado'''
	# cria o socket 
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Internet( IPv4 + TCP) 
	# vincula a localizacao do servidor
	sock.bind((HOST, PORT))
	# coloca-se em modo de espera por conexoes
	sock.listen(4) 
	# configura o socket para o modo nao-bloqueante
	sock.setblocking(False)
	# inclui o socket principal na lista de entradas de interesse
	entradas.append(sock)

	return sock

def recebe(sock):
	'''Recebe uma mensagem em bytes. O header da mensagem contém o tamanho do resto.'''
	# primeiro recebe o tamanho do resto da mensagem
	# assume que um int tem 4 bytes
	tamanho_bytes = sock.recv(INT_SIZE_IN_BYTES)
	if not tamanho_bytes:
		return None
	tamanho = int.from_bytes(tamanho_bytes, "big") # assumindo big-endian
	msg_bytes = sock.recv(tamanho)
	msg = str(msg_bytes, encoding="utf-8")
	
	print("Mensagem recebida: " + msg)
	
	return msg

def envia(sock, msg):
	'''Manda uma mensagem pelo socket. Parâmetro 'msg' deve ser string. Adiciona um header contendo o tamanho da mensagem.'''
	msg_bytes = bytes(msg, encoding="utf-8")
	tamanho = len(msg)
	tamanho_bytes = tamanho.to_bytes(4, "big")
	sock.sendall(tamanho_bytes)
	sock.sendall(msg_bytes)

def new_message(header, lista):
	'''Cria uma mensagem na qual as seções sao delimitadas por "|".
	Usada para poder recuperar informações, como o ID de uma réplica pedindo a cópia primária, mais facilmente.'''
	msg = str(header)
	for item in lista:
		msg = msg + "|" + str(item)

	return msg

def indicate_new_primary_copy_holder(new_holder_id):
	'''Usada após passar a cópia primária para outra réplica.'''
	global primary_copy_identifier
	
	primary_copy_identifier = new_holder_id
	reset_variables()

def reset_variables():
	'''Modifica variáveis relacionadas a posse da cópia primária.'''
	global holds_primary_copy, can_give_primary_away
	
	holds_primary_copy = False
	can_give_primary_away = False

def broadcast(msg):
	for replica in REPLICAS:
		if int(replica[0]) != int(local_copy_identifier):
			sock = socket.socket()
			sock.connect((HOST, replica[1]))
			envia(sock, msg)
			sock.close()

def atende_requisicao_copia_primaria(sock, comando):
	'''Requisição de posse da cópia primária.'''
	split_comand = comando.split("|")
	requester_id = split_comand[1]
	
	if holds_primary_copy and can_give_primary_away:
		primary_msg = new_message(header_primary_update, requester_id)
		indicate_new_primary_copy_holder(requester_id)
		broadcast(primary_msg)
	else:
		sock.send(bytes(header_ack, encoding="utf-8"))
		
def atende_atualizacao_historico(clisock, comando):
	'''Requisição para a cópia local atualizar seu histórico.'''
	global X, changes_history

	split_comand = comando.split("|")
	requester_id = split_comand[1]
	new_value = split_comand[2]
	X = new_value
	changes_history.append([requester_id, new_value])

def atende_atualizacao_copia_primaria(clisock, comando):
	'''Requisição para atualizar os indicadores de posse da cópia primária.'''
	global primary_copy_identifier, holds_primary_copy, can_give_primary_away
	
	split_comand = comando.split("|")
	new_holder_id = split_comand[1]
	primary_copy_identifier = new_holder_id
	
	if primary_copy_identifier == local_copy_identifier:
		holds_primary_copy = True
		can_give_primary_away = True

def processa_comando_sock(clisock, comando):
	'''Trata o comando recebido pelo socket.'''
	if comando.startswith( header_primary_request ):
		atende_requisicao_copia_primaria( clisock, comando )
		
	elif comando.startswith( header_history_update ):
		atende_atualizacao_historico( clisock, comando )
	
	elif comando.startswith( header_primary_update ):
		atende_atualizacao_copia_primaria( clisock, comando )
		
	elif comando.startswith( header_ack ):
		print("Ack.")
		
	else:
		clisock.send(bytes("Comando invalido", encoding="utf-8"))

def atende_requisicoes():
	'''Recebe mensagens e as envia para processamento.'''
	global sock
	
	clisock, endr = sock.accept()
	print ('Conectado com: ', endr)
	
	while True:
		data = recebe(clisock)
		if not data:
			print("Desconectado de: " + str(endr))
			clisock.close()
			return
		
		processa_comando_sock(clisock, data)

"""
INTERFACE
"""

LISTA_COMANDOS = ["ler", "escrever", "historico", "fim", "imprime_infos"]

def ler_x():
	print("Valor local de X: " + str(X))

def ler_historico():
	print("Historico de mudancas: " + str(changes_history))

def escrever_x():
	global X, changes_history
		
	if holds_primary_copy:
		writing()
		while True:
			new_value = input("Digite o novo valor para X ou 'termino' se nao quiser alterar seu valor:")
			if new_value == "termino":
				break
			else:
				X = new_value
				changes_history.append([local_copy_identifier, X])
		done_writing()
	else:
		msg = new_message(header_primary_request, local_copy_identifier)
		broadcast(msg)
		print("Esta replica nao possui a copia primaria, mas fez uma requisicao. Tente novamente.")

def terminar_programa():
	global sock
	
	try:
		sock.close()
	except:
		print("ERRO: O programa nao foi terminado.")

def processa_comando_stdin(comando):
	'''Implementa a interface.'''

	if comando == "ler":
		ler_x()
	elif comando == "escrever":
		escrever_x()
	elif comando == "historico":
		ler_historico()
	elif comando == "fim":
		terminar_programa()
	elif comando == "imprime_infos":
		imprime_infos()
	else:
		print("Comando nao reconhecido. Comandos disponiveis:")
		for comando_valido in LISTA_COMANDOS:
			print(comando_valido)

'''
AUX FUNC
'''

def writing():
	'''Indica que a replica local esta escrevendo. 
	"previous_X_value eh usada para indicar se o valor de X realmente foi modificado."'''
	global previous_X_value, can_give_primary_away
	
	previous_X_value = X
	can_give_primary_away = False

def done_writing():
	'''Indica que a replica terminou de escrever.
	Se X foi modificado, atualiza o valor de X e historico de outras replicas.'''
	global previous_X_value, can_give_primary_away

	if previous_X_value != X:
		history_msg = new_message(header_history_update, changes_history[-1])
		broadcast(history_msg)
	can_give_primary_away = True

def imprime_infos():
	'''Imprime algumas informacoes para auxiliar no debug.'''
	print("\nlocal_copy_identifier: " + str(local_copy_identifier))
	print("PORT: " + str(PORT))
	print("primary_copy_identifier: " + str(primary_copy_identifier))
	print("holds_primary_copy: " + str(holds_primary_copy))
	print("can_give_primary_away: " + str(can_give_primary_away))

"""
MAIN
"""

local_copy_identifier = input("Insira o numero identificador desta replica:\n")
PORT += int(local_copy_identifier)

if int(local_copy_identifier) == int(primary_copy_identifier):
	holds_primary_copy = True
	can_give_primary_away = True

print("Replica com a copia primaria: " + str(primary_copy_identifier))

sock = inicia_servidor()

while True:
	print("\nComandos disponiveis: "+ str(LISTA_COMANDOS) + "\n")
	leitura, escrita, excecao = select.select(entradas, [], [])
	for pronto in leitura:
		if pronto == sock:
			atende_requisicoes()
		elif pronto == sys.stdin:
			comando = input()
			processa_comando_stdin(comando)
