# Referencias:
# https://www.tutorialkart.com/python/python-read-file-as-string/
# https://www.delftstack.com/howto/python/python-counter-most-common/

import socket
from collections import Counter
import select
import sys
import threading

HOST = ''       # '' possibilita acessar qualquer endereco alcancavel da maquina local
PORTA = 9090    # porta onde chegarao as mensagens para essa aplicacao

#define a lista de I/O de interesse (jah inclui a entrada padrao)
entradas = [sys.stdin]
#armazena as conexoes ativas
conexoes = {}
#lock para acesso do dicionario 'conexoes'
lock = threading.Lock()

# Conta as 5 palavras mais comuns no arquivo e retorna esses termos ordenados
# Parametros:
#   conteudoDoArquivo (string): arquivo de texto em string única
#   numeroDePalavras (int): numero de palavras mais comuns buscadas
def contaPalavrasMaisComuns(conteudoDoArquivo, numeroDePalavras = 5):
    conteudoEmPalavras = conteudoDoArquivo.split() # separa a string em uma lista de palavras
    c = Counter(conteudoEmPalavras)
    palavrasMaisComuns = str(c.most_common(numeroDePalavras))
    return palavrasMaisComuns

# abre o arquivo e o converte para string. caso haja alguma falha, lança uma exceção e envia uma mensagem de erro
def abreArquivo(nomeArquivo, socket):
    try:
        arquivoAberto = open(nomeArquivo)
        return arquivoAberto.read()
    except FileNotFoundError:
        msgErroBytes = bytes("Erro: um arquivo com o nome especificado não foi encontrado.", encoding='utf-8')
        socket.send(msgErroBytes)
        return ""

def iniciaServidor():
	'''Cria um socket de servidor e o coloca em modo de espera por conexoes
	Saida: o socket criado'''
	# cria o socket 
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Internet( IPv4 + TCP) 
	# vincula a localizacao do servidor
	sock.bind((HOST, PORTA))
	# coloca-se em modo de espera por conexoes
	sock.listen(5) 
	# configura o socket para o modo nao-bloqueante
	sock.setblocking(False)
	# inclui o socket principal na lista de entradas de interesse
	entradas.append(sock)
	return sock

def aceitaConexao(sock):
	'''Aceita o pedido de conexao de um cliente
	Entrada: o socket do servidor
	Saida: o novo socket da conexao e o endereco do cliente'''
	# estabelece conexao com o proximo cliente
	clisock, endr = sock.accept()
	# registra a nova conexao
	lock.acquire()
	conexoes[clisock] = endr 
	lock.release()
	return clisock, endr

def atendeRequisicoes(clisock, endr):
	'''Recebe mensagens e as envia de volta para o cliente (ate o cliente finalizar)
	Entrada: socket da conexao e endereco do cliente
	Saida: '''
	while True:
		#recebe dados do cliente
		data = clisock.recv(1024) 
		if not data: # dados vazios: cliente encerrou
			print(str(endr) + '-> encerrou')
			lock.acquire()
			del conexoes[clisock] #retira o cliente da lista de conexoes ativas
			lock.release()
			clisock.close() # encerra a conexao com o cliente
			return
		
		#pega o conteudo do arquivo, conta as palavras mais comuns e as envia ao cliente
		conteudoDoArquivo = abreArquivo(data, clisock)
		if conteudoDoArquivo != "":
			palavrasMaisComuns = contaPalavrasMaisComuns(conteudoDoArquivo)
			clisock.send(bytes(palavrasMaisComuns, encoding='utf-8'))

def main():
	'''Inicializa e implementa o loop principal (infinito) do servidor'''
	fluxosExecucao = [] # lista das threads criadas pelo fluxo principal
	sock = iniciaServidor()
	print("Pronto para receber conexoes...")
	while True:
		#espera por qualquer entrada de interesse
		leitura, escrita, excecao = select.select(entradas, [], [])
		#tratar todas as entradas prontas
		for pronto in leitura:
			if pronto == sock:  #pedido novo de conexao
				clisock, endr = aceitaConexao(sock)
				print ('Conectado com: ', endr)
				#cria nova thread para atender o cliente
				cliente = threading.Thread(target=atendeRequisicoes, args=(clisock,endr))
				cliente.start()
				fluxosExecucao.append(cliente)
			elif pronto == sys.stdin: #entrada padrao
				cmd = input()
				if cmd == 'fim': #solicitacao de finalizacao do servidor
					for thread in fluxosExecucao:
						thread.join()
					sock.close()
					sys.exit()
				elif cmd == 'hist': #outro exemplo de comando para o servidor
					print(str(conexoes.values()))

main()
