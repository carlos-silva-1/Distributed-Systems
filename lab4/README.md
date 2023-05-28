A aplicação:

Implementa o algoritmo probe/echo para realizar eleições em uma rede distribuída.

Cada nó foi dividido em duas partes: uma classe servidor e uma classe cliente.
A primeira tem as responsabilidades de lidar com as requisições feita a um nó, enquanto 
que a segunda pode iniciar eleições e distribuir o ID do nó elegido ao resto da rede, além 
de funcionalidades para o gerenciamento do nó (adicionar vizinhos, entre outras).

Não foi utilizado rpyc de forma assíncrona pois não impacta a corretude do programa.

-----

Uso da aplicação:

O programa pode ser iniciado da seguinte forma:
	python3 eleicao.py <arquivo>
Onde "arquivo" é o nome do arquivo contendo uma descrição da rede. [1]

Isso irá abrir uma janela que corresponde ao nó da rede.
Será solicitado do usuário o número identificador do nó para que aquele nó possa ser 
controlado por aquela janela. 
Serão impressas as informações do nó retiradas do arquivo descrição, 
além do atributo que indica a adequação do nó como líder (gerado aleatoriamente).
O usuário deve utilizar uma janela para cada nó.

O usuário deve então esperar até que os nós com os quais irá se conectar estejam 
prontos para receber conexões, e então apertar a tecla 'enter'. [2][3]

A eleição deve ser iniciada pela linha de comando. A eleição não foi escrita como uma 
parte da API do servidor.
O identificador do eleito não é automaticamente enviado após o termino de uma eleição, 
um comando (enviar_lider) deve ser digitado para que seja distribuído pela rede. 
Para o funcionamento correto do programa, o comando "enviar_lider" deve ser chamado 
pelo mesmo no que chamou o comando "iniciar_eleicao".

Além desses dois comandos, existem três outros: "imprimir_no_pai", "imprimir_lider" e 
"reiniciar_no".
O primeiro imprime o id do nó pai do nó local.
O segundo imprime qual nó é o líder de acordo com o nó local. Após uma eleição e distribuição 
do líder, todos os nós devem imprimir o mesmo valor para esse comando.
O terceiro reinicia os campos do nó que são modificados ao decorrer de uma eleição e o 
impediriam de participar de uma nova eleição. [4]

-----

Observações:

[1]: Exemplos que foram utilizados para testar a aplicação estão nos arquivos 
"lider.txt", "lider2.txt" e "lider3.txt". Qualquer nova rede na qual utilizar 
essa aplicação deve ser descrita da mesma forma.

[2]: Não é necessário que todos os nós descritos no arquivo de entrada estejam na rede:
os outros nos simplesmente não irão se conectar ao nó que não está presente. 

[3]: Um nó não pode ser conectado ao resto da rede após essa etapa. Essa é a única 
parte do programa onde a conexão entre nós é possível. Caso algum nó tente se 
conectar a rede, será ignorado. Caso algum nó caia da rede, algum erro pode ocorrer 
durante a execução.

[4]: Caso queira realizar uma segunda eleição, é necessário primeiramente digitar 
o comando "reiniciar_no" em todos os nós. 
