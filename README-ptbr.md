# CloneGram

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python 3.12">
  <img src="https://img.shields.io/badge/License-Apache_2.0-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Telegram-API-blue.svg" alt="Telegram API">
</p>
CloneGram é uma ferramenta poderosa e eficiente para clonar mensagens entre grupos do Telegram, desenvolvida com recursos avançados para evitar detecção e banimentos.

## 📋 Características

* **Clonagem Completa** : Transfira mensagens, mídias, documentos e grupos de mídia entre grupos
* **Sistema Anti-Ban** : Mecanismos avançados para simular comportamento humano e evitar limitações da API
* **Configuração Flexível** : Personalize limites de taxa, atrasos e configurações de atividade
* **Retomada de Progresso** : Continue de onde parou em caso de interrupções
* **Modo Noturno** : Reduz atividade durante horários específicos para comportamento mais natural
* **Modo Final de Semana** : Ajusta atividade durante os finais de semana

## 🚀 Instalação

### Pré-requisitos

* Python 3.12 ou superior
* Conta do Telegram
* Credenciais de API do Telegram (API ID e API Hash)

### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/clonegram.git
   cd clonegram
   ```
2. Instale as dependências:
   ```bash
   pip install -e .
   ```
3. Configure o arquivo de ambiente:
   ```bash
   cp .env.exemple .env
   # Edite o arquivo .env com suas credenciais e configurações
   ```

## ⚙️ Configuração

Edite o arquivo `.env` com suas configurações:

```
ACCOUNT_NAME=minha_conta
PHONE_NUMBER=+5511987654321
PASSWORD=sua_senha_do_telegram
API_ID=12345
API_HASH=abcdef1234567890abcdef

ORIGIN_GROUP=grupo_origem_id
DESTINY_GROUP=grupo_destino_id

# Configurações anti-ban (opcionais)
MIN_DELAY=3
MAX_DELAY=5
DAILY_LIMIT=1000
HOURLY_LIMIT=100
DAILY_MEDIA_LIMIT=500
MAX_BATCH_SIZE=50
BATCH_COOLDOWN=300
NIGHT_MODE=true
NIGHT_START=0
NIGHT_END=7
NIGHT_MULTIPLIER=2.0
WEEKEND_MODE=false
WEEKEND_MULTIPLIER=1.5
```

### Obter API ID e Hash

1. Visite https://my.telegram.org/auth
2. Faça login com sua conta do Telegram
3. Acesse "API development tools"
4. Crie um novo aplicativo e copie o API ID e API Hash

### IDs dos Grupos

Para obter o ID de um grupo:

* Adicione [@username_to_id_bot](https://t.me/username_to_id_bot) ao grupo
* Ou use o grupo pelo seu nome de usuário (se tiver um)

## 🔧 Uso

Execute o bot:

```bash
python -m bot.main
```

O bot começará a clonar mensagens do grupo de origem para o grupo de destino. O progresso é salvo automaticamente no arquivo `progress.json`.

### Opções de Configuração

| Configuração     | Descrição                                               | Padrão |
| ------------------ | --------------------------------------------------------- | ------- |
| MIN_DELAY          | Atraso mínimo entre mensagens (segundos)                 | 3       |
| MAX_DELAY          | Atraso máximo entre mensagens (segundos)                 | 5       |
| DAILY_LIMIT        | Limite máximo de mensagens por dia                       | 1000    |
| HOURLY_LIMIT       | Limite máximo de mensagens por hora                      | 100     |
| DAILY_MEDIA_LIMIT  | Limite máximo de mensagens de mídia por dia             | 500     |
| MAX_BATCH_SIZE     | Máximo de mensagens a processar antes de uma pausa maior | 50      |
| BATCH_COOLDOWN     | Tempo de pausa após atingir o tamanho do lote (segundos) | 300     |
| NIGHT_MODE         | Reduzir atividade durante a noite                         | true    |
| NIGHT_START        | Hora de início do modo noturno (formato 24h)             | 0       |
| NIGHT_END          | Hora de término do modo noturno (formato 24h)            | 7       |
| NIGHT_MULTIPLIER   | Multiplicador de atrasos durante a noite                  | 2.0     |
| WEEKEND_MODE       | Reduzir atividade nos finais de semana                    | false   |
| WEEKEND_MULTIPLIER | Multiplicador de atrasos nos finais de semana             | 1.5     |

## 🐳 Docker

O projeto inclui suporte a Docker para fácil implantação.

### Construindo a imagem

Primeiro, construa a imagem Docker do projeto:

```bash
# Defina variáveis de ambiente para o build
export DOCKER_USERNAME=seu_usuario
export IMAGE_TAG=latest

# Construa a imagem
docker build -t $DOCKER_USERNAME/clonegram:$IMAGE_TAG .
```

### Primeira execução (modo interativo)

Na primeira vez que você executar o bot, será necessário autorizar a conta do Telegram. Isso requer execução em modo interativo:

```bash
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/progress.json:/app/progress.json \
  -v $(pwd)/activity_counters.json:/app/activity_counters.json \
  $DOCKER_USERNAME/clonegram:$IMAGE_TAG
```

Durante essa primeira execução, você receberá um código de verificação no Telegram. Insira esse código no terminal para concluir a autenticação.

### Execução em segundo plano

Após a autenticação inicial estar completa (e o arquivo de sessão ter sido criado), você pode executar o bot em segundo plano:

```bash
# Executar em segundo plano
docker-compose up -d

# Ou, sem o docker-compose:
docker run -d \
  --name clonegram \
  --env-file .env \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/progress.json:/app/progress.json \
  -v $(pwd)/activity_counters.json:/app/activity_counters.json \
  $DOCKER_USERNAME/clonegram:$IMAGE_TAG
```

### Verificar logs

Para verificar os logs do contêiner em execução:

```bash
docker-compose logs -f

# Ou, sem o docker-compose:
docker logs -f clonegram
```

## 📝 Nota Importante

Este projeto destina-se apenas a fins educacionais e pessoais. O uso indevido para spam ou violação dos termos de serviço do Telegram é estritamente desencorajado. O autor não se responsabiliza pelo uso inadequado desta ferramenta.

## 🧩 Estrutura do Projeto

```
clonegram/
│
├── bot/
│   ├── main.py            # Ponto de entrada principal
│   ├── progress_tracker.py # Gerenciamento de progresso
│   ├── rate_limit.py      # Limitação de taxa
│   ├── safety.py          # Mecanismos anti-detecção
│   ├── settings.py        # Configurações
│   └── utils.py           # Utilitários diversos
│
├── sessions/              # Armazena sessões do Telegram
├── .env.exemple           # Exemplo de arquivo de configuração
├── Dockerfile             # Configuração do Docker
├── docker-compose.yml     # Configuração do Docker Compose
├── pyproject.toml         # Dependências e metadados do projeto
└── README.md              # Documentação
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

1. Faça um fork do projeto
2. Crie sua branch de feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adicionar nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença Apache 2.0 - veja o arquivo [LICENSE]() para detalhes.

## 👏 Agradecimentos

* [Telethon](https://github.com/LonamiWebs/Telethon) por fornecer a API Python para o Telegram
