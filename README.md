# Sistema Web de Gestão e Engajamento Comunitário

> **Projeto Integrador — UNIVESP**
> Plataforma web modular para gestão de mutirões, voluntários e indicadores de impacto ambiental de projetos de limpeza urbana comunitária.

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Configuração do Nome da Organização](#configuração-do-nome-da-organização)
3. [Funcionalidades](#funcionalidades)
4. [Arquitetura](#arquitetura)
5. [Pré-requisitos](#pré-requisitos)
6. [Instalação e Execução](#instalação-e-execução)
7. [Contas de Demonstração](#contas-de-demonstração)
8. [Estrutura do Projeto](#estrutura-do-projeto)
9. [Comandos Úteis](#comandos-úteis)
10. [Desenvolvimento Local](#desenvolvimento-local)
11. [Contribuindo](#contribuindo)

---

## 🎯 Visão Geral

Sistema web desenvolvido como Projeto Integrador da UNIVESP para digitalizar e organizar a gestão de projetos sociais de mobilização comunitária voltados à limpeza urbana.

O sistema possui duas áreas distintas:
- **Área Pública** (`/`) — site institucional aberto a qualquer visitante
- **Área da Equipe** (`/sistema/`) — plataforma interna para gestão de mutirões e voluntários

> ⚠️ **Ambiente Acadêmico:** Este sistema opera em ambiente simulado local via Podman, sem implantação em produção.

---

## 🏷️ Configuração do Nome da Organização

O nome e as informações da organização **não estão fixos no código**. Eles são controlados por variáveis em `config/settings.py` e podem ser sobrescritos por variáveis de ambiente.

### Opção 1 — Editando `config/settings.py`

Localize o bloco de variáveis institucionais e altere os valores:

```python
# config/settings.py

INSTITUICAO_NOME       = 'Nome da Sua Organização'
INSTITUICAO_SUBTITULO  = 'Subtítulo ou categoria'
INSTITUICAO_SLOGAN     = 'Slogan ou descrição curta da missão'
INSTITUICAO_EMAIL      = 'contato@suaorganizacao.org'
INSTITUICAO_FACEBOOK   = 'https://www.facebook.com/suaorganizacao/'
INSTITUICAO_ANO_FUNDACAO = '2020'
```

### Opção 2 — Via variáveis de ambiente (recomendado para produção)

Defina as variáveis antes de subir os containers:

```bash
export INSTITUICAO_NOME="Nome da Sua Organização"
export INSTITUICAO_SUBTITULO="Subtítulo"
export INSTITUICAO_SLOGAN="Descrição da missão"
export INSTITUICAO_EMAIL="contato@org.org"
export INSTITUICAO_FACEBOOK="https://facebook.com/suaorg"
export INSTITUICAO_ANO_FUNDACAO="2020"

podman-compose up --build
```

Ou adicione as variáveis diretamente no bloco `environment` do `docker-compose.yml`:

```yaml
environment:
  INSTITUICAO_NOME: "Nome da Sua Organização"
  INSTITUICAO_SUBTITULO: "Subtítulo"
  INSTITUICAO_SLOGAN: "Descrição da missão"
  INSTITUICAO_EMAIL: "contato@org.org"
  INSTITUICAO_FACEBOOK: "https://facebook.com/suaorg"
  INSTITUICAO_ANO_FUNDACAO: "2020"
```

### Como funciona tecnicamente

As variáveis são injetadas automaticamente em todos os templates Django via um **context processor** (`core/context_processors.py`). Nos templates, são usadas como:

```html
{{ INST_NOME }}        → Nome da organização
{{ INST_SUBTITULO }}   → Subtítulo
{{ INST_SLOGAN }}      → Slogan
{{ INST_EMAIL }}       → E-mail de contato
{{ INST_FACEBOOK }}    → Link do Facebook
{{ INST_ANO_FUNDACAO}} → Ano de fundação
```

---

## ✅ Funcionalidades

### Área Pública (sem login)
| Página | Conteúdo |
|---|---|
| **Home** | Métricas reais, últimas ações, próximos mutirões |
| **O Projeto** | História, pilares de atuação, reconhecimentos |
| **Ações** | Listagem de todos os mutirões com dados de impacto |
| **Participe** | Como ser voluntário, formas de contribuir, contato |

### Área da Equipe (com login)
| Módulo | Funcionalidades |
|---|---|
| **Dashboard** | Indicadores, gráfico mensal, mapa interativo |
| **Mutirões** | Criar, editar, inscrever-se, controle de presença |
| **Impacto** | Registrar kg de lixo, sacos, participantes |
| **Perfil** | Histórico de participações do voluntário |
| **Admin Django** | Painel administrativo completo |

---

## 🏗️ Arquitetura

```
Usuário (Navegador)
        ↓ HTTP
Django MTV (Gunicorn)
        ↓ ORM
PostgreSQL 15
```

**Stack tecnológica:**
- Backend: Python 3.11 + Django 4.2
- Frontend: Django Templates + Bootstrap 5 + Chart.js + Leaflet.js
- Banco de dados: PostgreSQL 15
- WSGI: Gunicorn
- Containerização: Podman + podman-compose

**Apps Django:**
```
config/    → Configurações centrais
users/     → Usuários e autenticação
events/    → Mutirões e inscrições
impact/    → Relatórios de impacto ambiental
dashboard/ → Métricas e visualizações (área interna)
public/    → Páginas institucionais públicas
core/      → Utilitários e context processors
```

---

## 🔧 Pré-requisitos

- Ubuntu 22.04+ (ou Linux compatível)
- Podman 4.0+
- podman-compose 1.0+

### Instalando no Ubuntu

```bash
# Instalar Podman
sudo apt update
sudo apt install -y podman

# Instalar podman-compose
pip install podman-compose
# ou
sudo apt install -y podman-compose

# Verificar
podman --version
podman-compose --version
```

---

## 🚀 Instalação e Execução

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio> sistema-comunitario
cd sistema-comunitario
```

### 2. (Opcional) Configurar o nome da organização

Edite `config/settings.py` ou defina variáveis de ambiente conforme descrito em
[Configuração do Nome da Organização](#configuração-do-nome-da-organização).

### 3. Subir o ambiente

```bash
podman-compose up --build
```

O sistema irá automaticamente:
- Construir a imagem da aplicação
- Subir o PostgreSQL
- Aplicar todas as migrations
- Carregar os dados de demonstração
- Iniciar o servidor Gunicorn

### 4. Acessar

Após a mensagem `Sistema pronto!` aparecer no terminal:

| Interface | URL |
|---|---|
| Site público | http://localhost:8000 |
| Sistema interno | http://localhost:8000/sistema/ |
| Painel administrativo | http://localhost:8000/admin/ |

### 5. Parar

```bash
podman-compose down          # para mantendo dados
podman-compose down -v       # para e apaga o banco
```

---

## 🔐 Contas de Demonstração

| Perfil | Usuário | Senha |
|---|---|---|
| Administrador | `admin` | `admin123` |
| Voluntário 1 | `voluntario1` | `voluntario123` |
| Voluntário 2 | `voluntario2` | `voluntario123` |
| Voluntário 3 | `voluntario3` | `voluntario123` |

---

## 📁 Estrutura do Projeto

```
/
├── config/                  # Configurações do Django
│   ├── settings.py          # ← variáveis institucionais aqui
│   ├── urls.py
│   └── wsgi.py
├── core/
│   └── context_processors.py  # injeta INST_* em todos os templates
├── users/                   # Módulo: Usuários
├── events/                  # Módulo: Mutirões
├── impact/                  # Módulo: Impacto ambiental
├── dashboard/               # Módulo: Dashboard interno
├── public/                  # Módulo: Páginas públicas
├── templates/
│   ├── base.html            # Layout interno
│   ├── public/              # Templates do site público
│   ├── users/
│   ├── events/
│   ├── impact/
│   └── dashboard/
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
└── requirements.txt
```

---

## 🛠️ Comandos Úteis

```bash
# Ver containers ativos
podman ps

# Logs em tempo real
podman-compose logs -f
podman-compose logs -f web

# Shell da aplicação
podman exec -it varrevila_web bash

# Shell Django
podman exec -it varrevila_web python manage.py shell

# Criar superusuário
podman exec -it varrevila_web python manage.py createsuperuser

# Gerar migrations após alterar models
podman exec -it varrevila_web python manage.py makemigrations

# Reiniciar do zero
podman-compose down -v && podman-compose up --build
```

---

## 💻 Desenvolvimento Local (sem container)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Para usar SQLite localmente, edite config/settings.py:
# DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}

python manage.py migrate
python manage.py runserver
```

---

## 🤝 Contribuindo

```bash
# Criar branch
git checkout -b funcionalidade/nome-da-feature

# Commitar em português
git commit -m "feat: descrição da mudança"

# Enviar
git push origin funcionalidade/nome-da-feature
```

### Convenção de commits (em português)

| Prefixo | Uso |
|---|---|
| `feat:` | Nova funcionalidade |
| `fix:` | Correção de bug |
| `docs:` | Documentação |
| `refactor:` | Refatoração |
| `test:` | Testes |
| `chore:` | Manutenção |

---

**UNIVESP — Universidade Virtual do Estado de São Paulo**
*Projeto Integrador — Engenharia da Computação*
