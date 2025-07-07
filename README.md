# Simulador_Camadas_Rede_TR1
 Simulador das camadas Física e de Enlace para a disciplina de Teleinformática e Redes 1 (TR1).

---

## 🧱 Requisitos

- Python **3.10 ou superior**
- Git (para clonar o projeto)
- Acesso à linha de comando (Linux/macOS: terminal | Windows: PowerShell, CMD ou GitBash)

---

## ⚙️ Etapas de Instalação

### 1. Clone o repositório

#### Clonar o repositório:

```bash
git clone https://github.com/guilhermerm99/Simulador_Camadas_Rede_TR1.git
```

#### Ir para o `path` do projeto clonado:
```bash
cd Simulador_Camadas_Rede_TR1
```

--- 

### 2. Crie um ambiente virtual (opcional, mas recomendado)

> O ambiente virtual **evita conflitos** de **dependências com outros projetos**.

#### Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows:

```cmd
python -m venv venv
.\venv\Scripts\activate
```

---

### 3. Instale as dependências

O projeto possui um arquivo `requirements.txt` com todas as bibliotecas utilizadas no projeto. Para instalá-las:

```bash
pip install -r requirements.txt
```

> Caso adicione uma nova biblioteca, o `requerements.txt` será atualizado automátiamente.

---

## ▶️ Executando o Simulador

Com o ambiente ativado e as dependências instaladas, execute:

```bash
python3 InterfaceGUI/interface_tkinter.py
```

Ou no Windows (caso use `python` em vez de `python3`):

```powershell
python InterfaceGUI/interface_tkinter.py
```

A interface gráfica será aberta, permitindo simular diferentes técnicas de enquadramento, modulação e controle de erros.

---

## 🙋‍♂️ Erros Frequentes

- **Não tenho o `venv` no Linux**
  Rode:
  ```bash
  sudo apt install python3-venv
  ```

- **Erro com o `tkinter`**
  No Linux, instale via:
  ```bash
  sudo apt install python3-tk
  ```

---

## 🧼 Arquivos ignorados

Este projeto já possui `.gitignore` configurado para ignorar:

- Ambientes virtuais (`venv/`)
- Arquivos temporários e de cache
- Arquivos de sistema específicos

---
