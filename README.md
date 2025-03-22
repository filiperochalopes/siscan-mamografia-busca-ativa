# Sistema de Proecssamento de laudos SISCAN

A Busca Ativa é um importante passo no processo da Jornada Digital do Câncer de Mama, pois garante uma maior cobertura da população no rastreio bianual, facilitando o diagnóstico precoce de câncer de mama (pode-se reduzir a mortalidade em até 25%, a sobrevida - mais de 5 anos; para pacientes que descobrem o câncer em estágio inicial 1 é de quase 100%, enquanto para estágios mais tardios - 4 - é de praticamente 30%). Dessa forma, a busca ativa, tem como objetivo não apenas ampliar a adesão ao rastreamento de imagem (mamografia)  mas também reduzir o tempo entre as etapas e priorizar no sistema, quando necessário, os casos em estágios mais tardios, por meio de alertas,. Além disso, busca-se garantir o acompanhamento das pacientes com resultados negativos, mesmo na ausência de uma consulta formal.

Na tentativa de usar dados que já estão disponível para aprimorar a busca, principalmente para os prestadores que não conseguem acesso à ferramenta de Seguimento interna do SISCAN, ou que não conseguem a praticidade necessária com ela, a Prisma Consultoria, em parceria com a Roche e com a Secretaria Municipal de Saúde de Curitiba, desenvolveu como parte das melhorias de processo para a Jornada DIgital da paciente com Câncer de Mama, esse serviço para otimizar a Busca Ativa com informações da Base de Dados.

Observação: Os dados processados não sao armazenados pelo serviço. O sistema de token para autenticação é mais para dificultar um grande volume de acesso do que para segurança em si.

[Live Demo](https://siscan.filipelopes.med.br)

## Regras de negócio

### Conjunto mínimo de dados

Conjunto mínimo de dados a ser disponibilizado vel na planilha final deve ser: Nome, data de nascimento, idade (calculado a partir da data de nascimento),  nome da mãe, CNS, data de realização/execução do exame, nome da unidade de saúde com CNES, BIRADS MD (mama direita), BIRADS ME, Mama densa MD (boleano), Mama densa ME, Alterado (boleano - indica necessidade de atenção)ou seja, necessita de atenção), USG (boleano - sugerido realizar USG por comentário ou por característica do laudo), Link para arquivo (JPG extraído do PDF para auditoria e mais detalhes), pendente (boleano), data de ação, resultado da ação, observações do avaliador (coluna em branco para controle do rastreio)

### Requisitos técnicos

Solução técnica para extração de dados: Realizar uso de Python com lib (ex.: PyMuPDF, pdf plumber, PyPDF) para extração de dados em formato de texto, reconhecimento de padrões, captura de posição de elementos fixos para facilitar leitura e uso de reconhecimento de padrões para a parte de texto variável. Para uma abordagem de MVP, visando reduzir custos de desenvolvimento,reduzindo o custo de desenvolvimento, será adotado o uso de sugiro realizar com RegEx ou um algum modelo simples de NER já treinado com tolerância a erros de grafia.