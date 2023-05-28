import rpyc
import sys
from rpyc.utils.server import ThreadedServer
from threading import Thread
import numpy as np

class Server(rpyc.Service):
	'''Contem as funcionalidades que estejam relacionadas ao atendimento de requisições.'''
	
	global NO_LOCAL

	def on_connect(self, conx):
		print("Conexao estabelecida.")

	def on_disconnect(self, conx):
		print("Conexao encerrada.")
	
	def done_waiting_for_responses(self):
		'''Um nó precisa esperar pelas respostas dos probes realizados.
		Conta o número de echos recebidos, o número de acks recebidos e 
		soma 1 para contar o nó pai (caso não seja o nó raiz).'''
		if NO_LOCAL.is_root_node():
			if len(NO_LOCAL.attributes) + NO_LOCAL.acks_counter == len(NO_LOCAL.neighbourhood):
				return True
			return False
		else:
			if len(NO_LOCAL.attributes) + NO_LOCAL.acks_counter + 1 == len(NO_LOCAL.neighbourhood):
				return True
			return False	

	def exposed_echo(self, attribute_pair):
		'''Recebe atributos dos nós vizinhos.
		
		A cada echo recebido, checa se ainda deve esperar por mais um echo ou ack.
		Se não precisar decide o líder provisório entre os valores que o nó pode ver.
		Se for o nó raiz, termina a eleição. Se for um nó comum, envia o lider 
		provisório ao nó pai.'''
		
		NO_LOCAL.append_attribute(attribute_pair[0], attribute_pair[1])

		if self.done_waiting_for_responses():
			NO_LOCAL.decide_lider()
			if NO_LOCAL.is_root_node():
				print("\nEleição terminada. \nPara distribuir o líder pela rede deve-se digitar o comando 'enviar_lider'.")
			else:
				parent_port = int(NO_LOCAL.parentNode) + 10000
				parent_conn = NO_LOCAL.neighbourhood[str(parent_port)]
				parent_conn.root.echo(NO_LOCAL.lider_pair)	

	def manage_if_already_probed(self, port):
		'''Define o pai caso seja a primeira requisição.
		Caso contrário, envia ack para o nó que requisitou probe.
		Param port: porta utilizada pelo nó que requisitou probe.'''
		if NO_LOCAL.has_parent_node():
			conn = NO_LOCAL.neighbourhood[str(port)]
			conn.root.ack()
			return True
		else:
			parent_id = int(port)-10000
			NO_LOCAL.set_parent_node(str(parent_id))
			return False

	def probe_neighbours(self):
		'''Executa probe em todos os vizinhos excluindo o nó pai'''
		for port in NO_LOCAL.neighbourhood:
			if int(port) != int(NO_LOCAL.parentNode) + 10000:
				conn = NO_LOCAL.neighbourhood[port]
				conn.root.probe(NO_LOCAL.port)

	def exposed_probe(self, port):
		'''Não pode ser chamada na raiz ou em um nó que já tenha 
		sido alvo de um probe.'''

		if NO_LOCAL.is_root_node():
			conn = NO_LOCAL.neighbourhood[str(port)]
			conn.root.ack()
		else:
			if self.manage_if_already_probed(port):
				pass
			else:
				if NO_LOCAL.is_leaf_node():
					NO_LOCAL.lider_pair = [NO_LOCAL.identifier, NO_LOCAL.attribute]
					parent_connection = NO_LOCAL.neighbourhood[str(port)]
					parent_connection.root.echo(NO_LOCAL.lider_pair)
				else:
					self.probe_neighbours()

	def exposed_ack(self):
		'''A cada ack recebido, checa se ainda deve esperar por mais um echo ou ack.
		Se não precisar decide o líder provisório entre os valores que o nó pode ver.
		Se for o nó raiz, termina a eleição. Se for um nó comum, envia o líder 
		provisório ao nó pai.'''
		
		NO_LOCAL.acks_counter += 1

		if self.done_waiting_for_responses():
			NO_LOCAL.decide_lider()
			if NO_LOCAL.is_root_node():
				print("\nEleição terminada. \nPara distribuir o líder pela rede deve-se digitar o comando 'enviar_lider'.")
			else:
				parent_port = int(NO_LOCAL.parentNode) + 10000
				parent_conn = NO_LOCAL.neighbourhood[str(parent_port)]
				parent_conn.root.echo(NO_LOCAL.lider_pair)

	def exposed_lider(self, lider_pair):
		'''Recebe o identificador do nó eleito e chama a mesma função em seus 
		nós vizinhos para que recebam o identificador.
		Esse identificador não pode ser enviado ao nó pai ou a um nó que já o 
		tenha recebido.'''
		
		NO_LOCAL.lider_pair = lider_pair
		NO_LOCAL.set_lider(lider_pair[0])
		NO_LOCAL.received_lider = True
		
		print("Recebeu o líder eleito: " + str(lider_pair[0]) + ", com atributo: " + str(lider_pair[1]))
		
		for port in NO_LOCAL.neighbourhood:
			if int(port) != int(NO_LOCAL.parentNode) + 10000:
				conn = NO_LOCAL.neighbourhood[port]
				if not conn.root.already_received_lider():
					conn.root.lider(lider_pair)
	
	def exposed_already_received_lider(self):
		if NO_LOCAL.received_lider == True:
			return True
		return False

class Client():
	'''Contém as funcionalidades de gerenciamento do nó,
	funcionalidades que estejam desacopladas do papel de servidor'''

	neighbourhood = {} # dicionario contendo as portas dos vizinhos e suas conexoes
	lider_pair = None # id e atributo do lider eleito na forma [id, atributo]
	lider_id = None # id do lider eleito
	parentNode = None # porta do no pai deste no
	attributes = [] # atributos dos nos vizinhos recebidos por echo
	acks_counter = 0 # conta quantas respostas 'ack' recebeu
	root = False # indica se o no iniciou a eleicao
	received_lider = False

	def __init__(self, identifier):
		self.identifier = identifier
		self.port = identifier+10000
		self.attribute = np.random.randint(1,20)

	def add_neighbour(self, port, conn):
		self.neighbourhood[str(port)] = conn

	def remove_neighbour(self, port):
		self.neighbourhood.pop(str(port))

	def set_parent_node(self, parent_id):
		self.parentNode = parent_id

	def has_parent_node(self):
		if self.parentNode != None:
			return True
		return False

	def is_leaf_node(self):
		if len(self.neighbourhood) == 1 and self.root == False:
			return True
		return False

	def is_root_node(self):
		if self.root == True:
			return True
		return False

	def start_election(self):
		self.root = True
		for port in self.neighbourhood:
			conn = self.neighbourhood[port]
			conn.root.probe(self.port)

	def publish_lider(self):
		self.received_lider = True
		self.set_lider(self.lider_pair[0])
		print("Distribuindo líder ao resto da rede. \nID do líder: " + str(self.lider_pair[0]) + ", atributo do líder: " + str(self.lider_pair[1]))
		for port in self.neighbourhood:
			conn = self.neighbourhood[port]
			conn.root.lider(self.lider_pair)
		print("\nLíder terminou de ser distribuído. \nPara conferir o resultado da eleição, digite o comando 'imprimir_lider'.")

	def append_attribute(self, index, value):
		self.attributes.append([index, value])

	def decide_lider(self):
		self.attributes.append([self.identifier, self.attribute])
		self.lider_pair = self.max_attribute()

	def max_attribute(self):
		'''Encontra o maior dos atributos e retorna ambos o 
		id do nó contendo o atributo e o próprio atributo.'''

		max_value = self.attributes[0][1]
		index = self.attributes[0][0]
		for pair in self.attributes:
			if pair[1] > max_value:
				max_value = pair[1]
				index = pair[0]
		return [index, max_value]
		
	def get_lider(self):
		return self.lider_id
		
	def set_lider(self, lider_id):
		self.lider_id = lider_id
	
	def restart_client(self):
		'''Quando se quer iniciar uma nova eleição, rastros da última 
		eleição podem gerar resultados incorretos.
		Essa função deve ser chamada em todos os nós antes de iniciar 
		uma nova eleição.'''
		self.root = False
		self.lider_pair = None
		self.lider_id = None
		self.parentNode = None
		self.attributes = []
		self.acks_counter = 0
		self.received_lider = False
		print("\nParâmetros do nó foram reiniciados. Este nó pode ser utilizado em uma nova eleição.\n")

def serverThread(port):
	'''Uma thread é criada com essa função, 
	criando um fluxo separado para atender requisições.'''
	srv = ThreadedServer(Server, port=port)
	srv.start()
	srv.close()

def read_data(lines):
	'''Pega os ids dos vizinhos do nó local.
	Parâmetro lines: strings das linhas do arquivo de texto 
	contendo a descrição da rede.'''
	
	processed_lines_counter = 0
	for line in lines:
		if line.find("node_id") != -1 and line.find(str(ID_LOCAL)) != -1:
			processed_lines_counter += 1
			continue
		if processed_lines_counter > 0:
			if line.find("neighbour_ids") != -1:
				NEIGHBOURS_IDS = line[line.find("[")+1 : line.find("]")]
				break
	
	return NEIGHBOURS_IDS

"""
MAIN
"""

# o nome do arquivo que descreve a rede eh passado na linha de comando
NOME_ARQUIVO = sys.argv[1]

# inicia o no local
ID_LOCAL = int(input("Digite o número identificador deste nó:"))
NO_LOCAL = Client(ID_LOCAL)

# inicia o servidor local
serverThread = Thread(target=serverThread, args = (10000+ID_LOCAL, ))
serverThread.start()

# le a rede do arquivo texto
NODES_DATA = open(NOME_ARQUIVO, 'r')
NODES_DATA_LINES = NODES_DATA.readlines()
NEIGHBOURS_IDS = read_data(NODES_DATA_LINES)
NEIGHBOURS_IDS = NEIGHBOURS_IDS.split(",")
NEIGHBOURS_IDS = [int(i) for i in NEIGHBOURS_IDS]

print("ID LOCAL")
print(ID_LOCAL)
print("ATTRIBUTE")
print(NO_LOCAL.attribute)
print("IDS DOS VIZINHOS")
print(NEIGHBOURS_IDS)

input("Aperte enter se todos os nós estão prontos\n")

for i in range(len(NEIGHBOURS_IDS)):
	try:
		port = NEIGHBOURS_IDS[i]+10000
		conn = rpyc.connect('localhost', port, config={"allow_all_attrs": True})
		NO_LOCAL.add_neighbour(port, conn)
	except:
		pass

# realiza comandos
while True:
	comando = input("\nComandos disponíveis: \niniciar_eleicao \nenviar_lider \nimprimir_no_pai \nimprimir_lider \nreiniciar_no\n\n")
	if comando == "enviar_lider":
		NO_LOCAL.publish_lider()
	elif comando == "iniciar_eleicao":
		NO_LOCAL.start_election()
	elif comando == "imprimir_no_pai":
		print("\nNo pai do no local: " + str(NO_LOCAL.parentNode))
	elif comando == "imprimir_lider":
		print("\nLider atual: " + str(NO_LOCAL.get_lider()))
	elif comando == "reiniciar_no":
		NO_LOCAL.restart_client()

