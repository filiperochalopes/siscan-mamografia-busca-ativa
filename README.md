# RosaAtiva — Sistema de Apoio à Busca Ativa em Mamografia

**RosaAtiva** é uma ferramenta desenvolvida para apoiar a análise automatizada de laudos mamográficos e facilitar a identificação de pacientes que necessitam de acompanhamento no contexto do rastreamento do câncer de mama.

A Busca Ativa é um importante passo no processo da Jornada Digital do Câncer de Mama, pois garante uma maior cobertura da população no rastreio bianual, facilitando o diagnóstico precoce de câncer de mama (pode-se reduzir a mortalidade em até 25%; a sobrevida — mais de 5 anos — para pacientes que descobrem o câncer em estágio inicial 1 é de quase 100%, enquanto para estágios mais tardios — 4 — é de praticamente 30%). Dessa forma, a busca ativa tem como objetivo não apenas ampliar a adesão ao rastreamento de imagem (mamografia), mas também reduzir o tempo entre as etapas e priorizar no sistema, quando necessário, os casos em estágios mais tardios, por meio de alertas. Além disso, busca-se garantir o acompanhamento das pacientes com resultados negativos, mesmo na ausência de uma consulta formal.

Na tentativa de usar dados que já estão disponíveis para aprimorar a busca — principalmente para os prestadores que não conseguem acesso à ferramenta de Seguimento interna do SISCAN, ou que não conseguem a praticidade necessária com ela — a Prisma Consultoria, em parceria com a Roche e com a Secretaria Municipal de Saúde de Curitiba, desenvolveu como parte das melhorias de processo para a Jornada Digital da paciente com Câncer de Mama, esse serviço para otimizar a Busca Ativa com informações da base de dados.

> **Observação:** Os dados processados não são armazenados pelo serviço. O sistema de token para autenticação serve apenas para evitar grande volume de acessos, e não como medida de segurança.

[Live Demo](https://siscan.filipelopes.med.br)


## 🚀 Instalação Rápida (TL;DR)

### Pré-requisitos
- Docker instalado [(Instruções aqui)](https://docs.docker.com/get-docker/)
- Docker Compose instalado (já incluso no Docker Desktop)

### Passos

```bash
# Clone o repositório
git clone git@github.com:filiperochalopes/siscan-mamografia-busca-ativa.git siscan
cd siscan

# Suba a aplicação
docker compose up -d --build
```

---

## Regras de negócio

### Conjunto mínimo de dados

Conjunto mínimo de dados a ser disponibilizado na planilha final deve ser:

| Coluna                 | Tipo de valor         | Descrição |
|------------------------|------------------------|-----------|
| `Nome`                 | Texto                  | Nome completo da paciente. |
| `Data de nascimento`   | Data                   | Data de nascimento da paciente. |
| `Idade`                | Número inteiro         | Calculado automaticamente a partir da data de nascimento. |
| `Nome da mãe`          | Texto                  | Nome da mãe da paciente. |
| `CNS`                  | Texto (15 dígitos)     | Cartão Nacional de Saúde. |
| `Data do exame`        | Data                   | Data de realização ou execução do exame de mamografia. |
| `Unidade de saúde`     | Texto                  | Nome da unidade de saúde onde foi realizado o exame. |
| `CNES`                 | Texto (7 dígitos)      | Código Nacional da unidade de saúde. |
| `MD - BIRADS`          | Número inteiro         | Classificação BIRADS da mama direita. |
| `MD - Mama densa`      | Booleano (0/1)         | Indica se a mama direita é densa. |
| `ME - BIRADS`          | Número inteiro         | Classificação BIRADS da mama esquerda. |
| `ME - Mama densa`      | Booleano (0/1)         | Indica se a mama esquerda é densa. |
| `Alterado`             | Número inteiro (0,1,2) | Indica necessidade de atenção: 0 = BIRADS 1 e 2; 1 = BIRADS 3, mamas densas ou sugestão de USG; 2 = BIRADS 4 ou 5. Útil para filtragem. |
| `USG`                  | Booleano (0/1)         | Indica se há sugestão de ultrassonografia por comentários ou características do laudo. |
| `Link para arquivo`    | URL                    | Link para imagem JPG extraída do PDF, usada para auditoria e visualização do laudo. |
| `Pendente`             | Booleano (0/1, default: 1) | Indica se o contato ainda não foi feito ou se não teve sucesso. Usado como controle operacional. |
| `Data de ação`         | Data                   | Data da tentativa de contato com a paciente. |
| `Resultado da ação`    | Texto                  | Resultado registrado pelo operador após a tentativa de contato. |
| `Observações`          | Texto livre            | Campo aberto para anotações do avaliador. |

> ⚠️ **Nota:**  
Mesmo pacientes com BIRADS 1 ou 2 devem passar por alguma forma de verificação de sintomas. No fluxo de pacientes sintomáticas, mesmo exames aparentemente normais podem justificar avaliação com o especialista.

---

### Requisitos técnicos

Solução técnica para extração de dados: realizar uso de Python com bibliotecas como `PyMuPDF`, `pdfplumber` ou `PyPDF` para extração de dados em formato de texto, reconhecimento de padrões, captura de posição de elementos fixos e uso de reconhecimento de padrões para leitura de partes variáveis. 

Para uma abordagem de MVP, visando reduzir custos de desenvolvimento, será adotado o uso de expressões regulares (RegEx) ou algum modelo simples de NER já treinado, com tolerância a erros de grafia.

### Rodando os testes

A execução dos testes é totalmente automatizada. O ambiente será inicializado, os arquivos de entrada gerados e o sistema testado com Playwright e Pytest.

#### Pré-requisito

Antes de rodar os testes, é necessário disponibilizar **um laudo real de mamografia exportado do SISCAN**.

* Salve esse arquivo com o nome `example.pdf`
* Coloque-o na pasta:

```
tests/files/example.pdf
```

> **Atenção:** sem esse arquivo real, os testes de extração e leitura do laudo não funcionarão corretamente.

---

Segue a seção "Testes automatizados" revisada para o `README.md`, incluindo a explicação sobre os arquivos `example.pdf` e `expected.json`:

---

### ✅ Testes automatizados

A execução dos testes é totalmente automatizada. O ambiente será inicializado, os arquivos de entrada gerados e o sistema testado com Playwright e Pytest.

#### Pré-requisitos

Antes de rodar os testes, é necessário disponibilizar **dois arquivos essenciais**:

* `example.pdf` – laudo real de mamografia exportado do SISCAN.
* `expected.json` – JSON contendo os dados esperados extraídos do laudo.

Ambos os arquivos estão disponíveis nos links abaixo, **mediante solicitação de acesso**:

* [`example.pdf`](https://drive.google.com/file/d/1VYTMBLIbiDTcj6W7mUKeqStlpSW5dZdZ/view?usp=sharing)
* [`expected.json`](https://drive.google.com/file/d/1JXKsMbAELVGI6SZVz8kdjryUoqN5UH2y/view?usp=sharing)

> Após obter os arquivos, salve-os na pasta `tests/files/`.

```bash
tests/files/example.pdf
tests/files/expected.json
```

#### Execução

Para executar todo o processo (preparação do ambiente, containers, testes e limpeza):

```bash
make tests
```

Esse comando:

1. Gera automaticamente o arquivo `.env` (caso não exista) com `TOKEN`, `SECRET_KEY` e `APP_URL`.
2. Cria arquivos de teste fictícios (`example.txt` e `invalid_pdf.pdf`) usando a biblioteca `faker-file`.
3. Sobe o container `web` e aguarda até que esteja saudável.
4. Executa os testes com `pytest`, incluindo testes end-to-end com `Playwright`.
5. Remove diretórios e arquivos temporários ao final do processo.

